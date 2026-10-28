#!/usr/bin/env python3
"""Compare deux rendus PDF d'un même document : Word (référence) et Google Docs (export PDF).

Usage :
    python scripts/comparer_rendus.py reference.pdf google-docs.pdf [--sortie DOSSIER] [--tolerance 0.5]
    python scripts/comparer_rendus.py reference.pdf export.json      (export PDF d'un connecteur Drive)

Pour chaque page, le script :
- apparie les lignes de texte des deux PDF et mesure leur décalage (mm) et l'écart de taille de police ;
- signale les lignes présentes d'un seul côté ;
- écrit cmp-N.png (côte à côte : référence à gauche) et diff-N.png (en rouge, ce qui diffère).

Il sort en erreur (code 1) si le nombre de pages diffère ou si un décalage dépasse la tolérance.
C'est l'outil de vérification de references/google-docs.md. Il demande PyMuPDF (pip install pymupdf),
facultatif pour le reste du skill.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

MM = 25.4 / 72
PUCES = re.compile(r"[  ​•●▪■]")


def exiger_pymupdf():
    try:
        import fitz  # noqa: F401
    except ImportError:
        raise SystemExit("PyMuPDF manque. Installez-le avec : pip install pymupdf")
    import fitz

    return fitz


def normaliser(texte: str) -> str:
    """Texte d'une ligne sans puces, espaces insécables ni espaces d'interlettrage."""
    return re.sub(r"\s+", " ", PUCES.sub(" ", texte)).strip()


def lignes(page) -> list[tuple[str, tuple, float]]:
    """Lignes de texte d'une page : (texte, bbox en points, taille de police), dans l'ordre de lecture."""
    res = []
    for bloc in page.get_text("dict")["blocks"]:
        for ligne in bloc.get("lines", []):
            texte = normaliser("".join(s["text"] for s in ligne["spans"]))
            if texte:
                res.append((texte, tuple(ligne["bbox"]), max(s["size"] for s in ligne["spans"])))
    return sorted(res, key=lambda x: (round(x[1][1]), x[1][0]))


def comparer_pages(page_ref, page_gd, tolerance: float) -> dict:
    """Écarts entre deux pages : lignes appariées (dx, dy en mm, tailles) et lignes non appariées."""
    a, b = lignes(page_ref), lignes(page_gd)
    # Les capitales interlettrées de Word sont extraites avec des espaces (« EFFECT IF ») : on les compare sans espaces.
    cle = lambda x: x[0].replace(" ", "")  # noqa: E731
    appariees, seules = [], []
    sm = difflib.SequenceMatcher(None, [cle(x) for x in a], [cle(x) for x in b], autojunk=False)
    for tag, a1, a2, b1, b2 in sm.get_opcodes():
        if tag == "equal":
            for x, y in zip(a[a1:a2], b[b1:b2]):
                dx, dy = (y[1][0] - x[1][0]) * MM, (y[1][1] - x[1][1]) * MM
                appariees.append({"texte": x[0], "dx": round(dx, 2), "dy": round(dy, 2), "taille": (round(x[2], 1), round(y[2], 1)),
                                  "hors_tolerance": abs(dx) > tolerance or abs(dy) > tolerance})
        else:
            seules += [("référence", x[0]) for x in a[a1:a2]] + [("google", y[0]) for y in b[b1:b2]]
    return {"lignes": appariees, "seules": seules}


def images(page_ref, page_gd, dossier: Path, n: int, dpi: int = 80) -> None:
    from PIL import Image, ImageChops

    def image(page):
        pm = page.get_pixmap(dpi=dpi)
        return Image.frombytes("RGB", (pm.width, pm.height), pm.samples)

    ia, ib = image(page_ref), image(page_gd)
    cote = Image.new("RGB", (ia.width + ib.width + 10, max(ia.height, ib.height)), "white")
    cote.paste(ia, (0, 0))
    cote.paste(ib, (ia.width + 10, 0))
    cote.save(dossier / "cmp-{}.png".format(n))
    ib = ib.resize(ia.size)
    masque = ImageChops.difference(ia, ib).convert("L").point(lambda v: 255 if v > 40 else 0)
    fond = Image.blend(ia, Image.new("RGB", ia.size, "white"), 0.6)
    fond.paste(Image.new("RGB", ia.size, (220, 30, 30)), mask=masque)
    fond.save(dossier / "diff-{}.png".format(n))


def pdf_de_l_export(chemin: str) -> str:
    """Export PDF enregistré par un connecteur Google Drive (JSON, contenu en base64) → fichier .pdf voisin."""
    if not chemin.lower().endswith(".json"):
        return chemin
    import base64
    import json

    donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
    pdf = Path(chemin).with_suffix(".pdf")
    pdf.write_bytes(base64.b64decode(donnees.get("content", "")))
    return str(pdf)


def comparer(reference: str, google: str, sortie: str | None = None, tolerance: float = 0.5) -> dict:
    fitz = exiger_pymupdf()
    google = pdf_de_l_export(google)
    ref, gd = fitz.open(reference), fitz.open(google)
    dossier = Path(sortie) if sortie else Path(google).resolve().parent
    dossier.mkdir(parents=True, exist_ok=True)
    rapport = {"pages": (len(ref), len(gd)), "par_page": []}
    for n in range(min(len(ref), len(gd))):
        rapport["par_page"].append(comparer_pages(ref[n], gd[n], tolerance))
        images(ref[n], gd[n], dossier, n + 1)
    return rapport


def main() -> None:
    # Console Windows (cp1252) : un caractère non représentable s'affiche « ? » au lieu d'arrêter le script.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Compare le PDF de Word et celui de Google Docs, ligne par ligne.")
    parser.add_argument("reference", help="PDF de référence (Word)")
    parser.add_argument("google", help="PDF exporté de Google Docs, ou le JSON de l'export d'un connecteur Drive")
    parser.add_argument("--sortie", help="dossier des images cmp-N.png et diff-N.png (par défaut : celui du PDF Google)")
    parser.add_argument("--tolerance", type=float, default=0.5, help="décalage accepté, en mm (0,5 par défaut)")
    parser.add_argument("--tout", action="store_true", help="affiche toutes les lignes, pas seulement les écarts")
    args = parser.parse_args()
    r = comparer(args.reference, args.google, args.sortie, args.tolerance)
    ok = r["pages"][0] == r["pages"][1]
    print("Pages : {} (référence) / {} (Google Docs){}".format(*r["pages"], "" if ok else "  ÉCART"))
    for n, page in enumerate(r["par_page"], 1):
        hors = [x for x in page["lignes"] if x["hors_tolerance"]]
        dys = [x["dy"] for x in page["lignes"]] or [0]
        print("Page {} : {} lignes appariées, décalage vertical de {:+.1f} à {:+.1f} mm, {} hors tolérance".format(
            n, len(page["lignes"]), min(dys), max(dys), len(hors)))
        for x in page["lignes"] if args.tout else hors:
            print("  {:+5.1f} {:+5.1f} mm  {}/{} pt  {}".format(x["dx"], x["dy"], x["taille"][0], x["taille"][1], x["texte"][:60]))
        for cote, texte in page["seules"]:
            print("  seulement {} : {}".format(cote, texte[:60]))
        ok = ok and not hors
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    sys.exit(main())
