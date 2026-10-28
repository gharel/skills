#!/usr/bin/env python3
"""PPTX allégé pour Google Slides et pour un connecteur Google Drive.

Usage :
    python scripts/pptx_google_slides.py support.pptx [--sortie support.google-slides.pptx] [--base64]

Un connecteur Google Drive reçoit le fichier en base64 recopié dans l'appel : au-delà de 30 000 caractères
environ (22 Ko), la recopie dérive. Un PPTX vide de python-pptx en pèse déjà 27 Ko : 11 dispositions de
diapositive, une vignette et un thème complet. Le script retire ce qui ne sert pas, ramène chaque image au double
de sa taille d'affichage au plus (1 px de la slide de 1 920 px = 6 350 EMU), passe logo et icônes sur
la palette de leurs couleurs franches et recompresse le paquet. Photos et stickers gardent leur qualité. Il ne change rien à ce
qu'affichent PowerPoint et Google Slides.

rendre_support.py l'applique à chaque PPTX qu'il produit.
"""

from __future__ import annotations

import argparse
import base64
import io
import posixpath
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from charte import est_graphique, palette_transparente  # noqa: E402  (images transparentes : voir charte.py)

EMU_PAR_PX = 6350  # slide de 1 920 px = 12 192 000 EMU
QUALITE_JPEG = 85
ECHELLE_MAXI = 2  # images gardées jusqu'au double de leur taille d'affichage (écrans haute densité)
LARGEUR_MINI = 64  # px : une petite icône garde son dessin


def chemin_rels(partie: str) -> str:
    dossier, nom = posixpath.split(partie)
    return posixpath.join(dossier, "_rels", nom + ".rels")


def cibles(fichiers: dict, rels: str) -> dict[str, str]:
    """Identifiant de relation → partie visée (chemin dans le paquet), pour un fichier .rels."""
    source = posixpath.dirname(posixpath.dirname(rels))
    resultat = {}
    for rel in re.findall(r"<Relationship\b[^>]*>", fichiers.get(rels, b"").decode("utf-8")):
        ident, cible = re.search(r'Id="([^"]+)"', rel), re.search(r'Target="([^"]+)"', rel)
        if ident and cible and "External" not in rel:
            t = cible.group(1)
            resultat[ident.group(1)] = t.lstrip("/") if t.startswith("/") else posixpath.normpath(posixpath.join(source, t))
    return resultat


def retirer(fichiers: dict, partie: str) -> list[tuple[str, str]]:
    """Retire une partie, ses relations sortantes, les relations qui la visent et son type de contenu.
    Renvoie les relations retirées : (fichier .rels, identifiant)."""
    fichiers.pop(partie, None)
    fichiers.pop(chemin_rels(partie), None)
    retirees = []
    for rels in [n for n in fichiers if n.endswith(".rels")]:
        visees = {i for i, c in cibles(fichiers, rels).items() if c == partie}
        if visees:
            texte = fichiers[rels].decode("utf-8")
            texte = re.sub(r"<Relationship\b[^>]*>", lambda m: "" if re.search(r'Id="([^"]+)"', m.group(0)).group(1) in visees else m.group(0), texte)
            fichiers[rels] = texte.encode("utf-8")
            retirees += [(rels, i) for i in visees]
    types = fichiers["[Content_Types].xml"].decode("utf-8")
    fichiers["[Content_Types].xml"] = re.sub(r'<Override PartName="/{}"[^>]*/>'.format(re.escape(partie)), "", types).encode("utf-8")
    return retirees


def retirer_inutiles(fichiers: dict, messages: list[str]) -> None:
    """Vignette, propriétés du document, réglages d'impression et dispositions qu'aucune diapositive n'utilise."""
    retirees = [n for n in fichiers if re.match(r"docProps/(thumbnail\.jpeg|app\.xml|core\.xml)$|ppt/printerSettings/", n)]
    for n in retirees:
        retirer(fichiers, n)
    utilisees = set()
    for rels in [n for n in fichiers if re.match(r"ppt/slides/_rels/slide\d+\.xml\.rels$", n)]:
        utilisees |= {c for c in cibles(fichiers, rels).values() if "/slideLayouts/" in c}
    dispositions = [n for n in fichiers if re.match(r"ppt/slideLayouts/slideLayout\d+\.xml$", n) and n not in utilisees]
    for n in dispositions:
        for rels, ident in retirer(fichiers, n):
            maitre = posixpath.join(posixpath.dirname(posixpath.dirname(rels)), posixpath.basename(rels)[: -len(".rels")])
            if maitre in fichiers:
                texte = fichiers[maitre].decode("utf-8")
                fichiers[maitre] = re.sub(r'<p:sldLayoutId\b[^>]*r:id="{}"[^>]*/>'.format(re.escape(ident)), "", texte).encode("utf-8")
    if retirees or dispositions:
        messages.append("retirés : {} disposition(s) inutilisée(s){}".format(len(dispositions), ", " + ", ".join(retirees) if retirees else ""))


def tailles_affichage(fichiers: dict) -> dict[str, tuple[float, float]]:
    """Taille d'affichage maximale (px de la slide) de chaque image."""
    tailles: dict[str, tuple[float, float]] = {}
    for partie in [n for n in fichiers if re.match(r"ppt/(slides|slideLayouts|slideMasters)/[^/]+\.xml$", n)]:
        relations = cibles(fichiers, chemin_rels(partie))
        xml = fichiers[partie].decode("utf-8")
        for pic in re.findall(r"<p:pic>.*?</p:pic>", xml, re.S):
            embed = re.search(r'r:embed="([^"]+)"', pic)
            ext = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', pic)
            media = relations.get(embed.group(1)) if embed else None
            if media and ext:
                l, h = int(ext.group(1)) / EMU_PAR_PX, int(ext.group(2)) / EMU_PAR_PX
                avant = tailles.get(media, (0, 0))
                tailles[media] = (max(avant[0], l), max(avant[1], h))
    return tailles


def alleger_images(fichiers: dict, messages: list[str]) -> None:
    """Images au double de leur taille d'affichage au plus (nettes sur un écran haute densité), sans perte
    de qualité : photos et stickers restent en couleurs vraies (JPEG à 85 pour une photo retaillée), seuls logo
    et icônes passent sur la palette de leurs couleurs franches, sans perte."""
    from PIL import Image

    tailles = tailles_affichage(fichiers)
    avant = apres = 0
    for nom in sorted(n for n in fichiers if n.startswith("ppt/media/")):
        if nom not in tailles:
            continue
        try:
            im = Image.open(io.BytesIO(fichiers[nom]))
            im.load()
        except Exception:
            continue
        format_ = im.format
        if format_ not in ("PNG", "JPEG"):
            continue
        largeur, hauteur = tailles[nom]
        echelle = ECHELLE_MAXI * max(largeur / im.width, hauteur / im.height)
        retaillee = echelle < 1
        if retaillee:
            im = im.resize((max(LARGEUR_MINI, round(im.width * echelle)), max(1, round(im.height * echelle))), Image.LANCZOS)
        tampon = io.BytesIO()
        transparente = im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info)
        if transparente:
            transparente = im.convert("RGBA").getchannel("A").getextrema()[0] < 255
        if format_ == "JPEG":
            if not retaillee:
                continue  # photo déjà à la bonne taille : jamais recompressée
            im.convert("RGB").save(tampon, "JPEG", quality=QUALITE_JPEG, optimize=True, progressive=True)
        elif transparente and est_graphique(im):
            p, table = palette_transparente(im)  # logo, icône : sans perte
            p.save(tampon, "PNG", optimize=True, transparency=table)
        else:
            im.save(tampon, "PNG", optimize=True)  # sticker, photo composée (polaroïd, ombre) : couleurs vraies
        avant += len(fichiers[nom])
        if retaillee or len(tampon.getvalue()) < len(fichiers[nom]):
            fichiers[nom] = tampon.getvalue()
        apres += len(fichiers[nom])
    if avant:
        messages.append("images ramenées au double de leur taille d'affichage : {} Ko → {} Ko".format(round(avant / 1024), round(apres / 1024)))


def preparer_pptx(donnees: bytes) -> tuple[bytes, list[str]]:
    """PPTX allégé : (octets, liste de ce qui a été fait)."""
    source = zipfile.ZipFile(io.BytesIO(donnees))
    fichiers = {i.filename: source.read(i.filename) for i in source.infolist() if not i.filename.endswith("/")}
    messages: list[str] = []
    retirer_inutiles(fichiers, messages)
    alleger_images(fichiers, messages)
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as sortie:
        for nom in ["[Content_Types].xml"] + sorted(n for n in fichiers if n != "[Content_Types].xml"):
            sortie.writestr(nom, fichiers[nom])
    resultat = tampon.getvalue()
    messages.append("taille : {} Ko → {} Ko (base64 : {} caractères)".format(
        round(len(donnees) / 1024), round(len(resultat) / 1024), len(base64.b64encode(resultat))))
    return resultat, messages


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("pptx")
    parser.add_argument("--sortie")
    parser.add_argument("--base64", action="store_true", help="écrit aussi le base64 dans un fichier .b64.txt")
    args = parser.parse_args()
    source = Path(args.pptx)
    sortie = Path(args.sortie) if args.sortie else source.with_suffix(".google-slides.pptx")
    resultat, messages = preparer_pptx(source.read_bytes())
    sortie.write_bytes(resultat)
    for m in messages:
        print("- " + m)
    print(sortie)
    if args.base64:
        chemin = sortie.with_name(sortie.name + ".b64.txt")
        chemin.write_text(base64.b64encode(resultat).decode("ascii"), encoding="ascii")
        print(chemin)


if __name__ == "__main__":
    main()
