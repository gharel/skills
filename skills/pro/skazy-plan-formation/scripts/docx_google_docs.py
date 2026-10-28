#!/usr/bin/env python3
"""DOCX prêt pour Google Docs : allège un .docx et remplace l'interligne exact, que Google Docs convertit mal.

Usage :
    python scripts/docx_google_docs.py plan.docx [--sortie plan.google-docs.docx] [--dpi 110] [--base64]

Méthode validée sur des plans de formation (voir references/google-docs.md) :

- Google Docs convertit l'interligne « exact » de Word (w:line en twips) en pourcentage de la hauteur de
  ligne naturelle de la police : le texte s'étire, 3 pages au lieu de 2. Il est remplacé ici par
  l'interligne multiple équivalent, que Word et Google Docs lisent de la même façon.
- Un connecteur Google Drive reçoit le fichier en base64 recopié dans l'appel : il faut viser 25 Ko
  environ. Le script retire les polices embarquées (Raleway existe dans Google Docs), les parties
  inutiles et les styles non utilisés, puis réduit chaque image à sa taille d'affichage.

rendre_plan.py applique ce traitement à chaque DOCX qu'il produit. Le script sert aussi pour un plan
retouché dans Word ou venu d'ailleurs.
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

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
HAUTEUR_LIGNE = 1.174  # hauteur de ligne naturelle de Raleway, rapportée à la taille de police
DPI = 110  # images : nettes à l'écran, un peu moins à l'impression
LARGEUR_MINI_TRANSPARENTE = 200  # px : logo et sticker gardent du détail
PARTIES = re.compile(r"word/(document|header\d+|footer\d+|footnotes|endnotes|comments)\.xml$")
INUTILES = re.compile(
    r"^(word/fonts/.+|word/stylesWithEffects\.xml|word/webSettings\.xml|docProps/(app|custom)\.xml|"
    r"docProps/thumbnail\.\w+|customXml/.+)$"
)


def q(nom: str) -> str:
    prefixe, local = nom.split(":")
    return "{%s}%s" % (NS[prefixe], local)


def lire_xml(donnees: bytes):
    from lxml import etree

    return etree.fromstring(donnees)


def ecrire_xml(racine) -> bytes:
    from lxml import etree

    return etree.tostring(racine, xml_declaration=True, encoding="UTF-8", standalone=True)


# ---------------------------------------------------------------- parties du paquet


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


def retirer(fichiers: dict, partie: str) -> None:
    """Retire une partie, ses relations sortantes, les relations qui la visent et son type de contenu."""
    fichiers.pop(partie, None)
    fichiers.pop(chemin_rels(partie), None)
    for rels in [n for n in fichiers if n.endswith(".rels")]:
        visees = {i for i, c in cibles(fichiers, rels).items() if c == partie}
        if visees:
            texte = fichiers[rels].decode("utf-8")
            texte = re.sub(r"<Relationship\b[^>]*>", lambda m: "" if re.search(r'Id="([^"]+)"', m.group(0)).group(1) in visees else m.group(0), texte)
            fichiers[rels] = texte.encode("utf-8")
    types = fichiers["[Content_Types].xml"].decode("utf-8")
    fichiers["[Content_Types].xml"] = re.sub(r'<Override PartName="/{}"[^>]*/>'.format(re.escape(partie)), "", types).encode("utf-8")


def transformer(fichiers: dict, partie: str, fonction) -> None:
    if partie in fichiers:
        fichiers[partie] = fonction(fichiers[partie].decode("utf-8")).encode("utf-8")


def retirer_inutiles(fichiers: dict, messages: list[str]) -> None:
    corps = b"".join(v for n, v in fichiers.items() if PARTIES.match(n)).decode("utf-8", "replace")
    inutiles = [n for n in fichiers if INUTILES.match(n)]
    # Commentaires et notes : seulement s'ils ne sont pas appelés dans le texte.
    if "commentReference" not in corps:
        inutiles += [n for n in fichiers if re.match(r"word/(comments\w*|people)\.xml$", n)]
    for genre in ("footnote", "endnote"):
        if not re.search(r"<w:{}Reference\b".format(genre), corps):
            inutiles += [n for n in fichiers if n == "word/{}s.xml".format(genre)]
            transformer(fichiers, "word/settings.xml", lambda s, g=genre: re.sub(r"<w:{0}Pr>.*?</w:{0}Pr>".format(g), "", s, flags=re.S))
    polices = sum(1 for n in inutiles if n.startswith("word/fonts/"))
    for n in inutiles:
        retirer(fichiers, n)
    if polices:
        transformer(fichiers, "word/fontTable.xml", lambda s: re.sub(r"<w:embed(Regular|Bold|Italic|BoldItalic)\b[^>]*/>", "", s))
        messages.append("{} police(s) embarquée(s) retirée(s)".format(polices))
    transformer(fichiers, "word/settings.xml", lambda s: re.sub(r"<w:(embedTrueTypeFonts|embedSystemFonts|saveSubsetFonts)\b[^>]*/>", "", s))
    if not any(n.endswith(".odttf") for n in fichiers):
        transformer(fichiers, "[Content_Types].xml", lambda s: re.sub(r'<Default Extension="odttf"[^>]*/>', "", s))
    autres = [n for n in inutiles if not n.startswith("word/fonts/")]
    if autres:
        messages.append("parties inutiles retirées : " + ", ".join(sorted(autres)))


def elaguer_styles(fichiers: dict, messages: list[str]) -> None:
    """Retire les styles latents et les styles que rien n'utilise (ils pèsent l'essentiel de styles.xml)."""
    if "word/styles.xml" not in fichiers:
        return
    racine = lire_xml(fichiers["word/styles.xml"])
    for latents in racine.findall(q("w:latentStyles")):
        racine.remove(latents)
    styles = {s.get(q("w:styleId")): s for s in racine.findall(q("w:style"))}
    texte = b"".join(v for n, v in fichiers.items() if PARTIES.match(n) or n in ("word/numbering.xml", "word/settings.xml")).decode("utf-8", "replace")
    garder = set(re.findall(r'w:(?:pStyle|rStyle|tblStyle|numStyleLink|styleLink|clickAndTypeStyle|defaultTableStyle) w:val="([^"]+)"', texte))
    garder |= {i for i, s in styles.items() if s.get(q("w:default")) in ("1", "true", "on")}
    pile = list(garder)
    while pile:
        style = styles.get(pile.pop())
        for lien in ("w:basedOn", "w:link", "w:next") if style is not None else ():
            e = style.find(q(lien))
            if e is not None and e.get(q("w:val")) not in garder:
                garder.add(e.get(q("w:val")))
                pile.append(e.get(q("w:val")))
    retires = [i for i in styles if i not in garder]
    for i in retires:
        racine.remove(styles[i])
    fichiers["word/styles.xml"] = ecrire_xml(racine)
    if retires:
        messages.append("{} styles inutilisés retirés".format(len(retires)))


# ---------------------------------------------------------------- interligne


def tailles_styles(fichiers: dict) -> tuple[dict[str, float], float]:
    """Taille de police (pt) de chaque style de paragraphe, héritage compris, et taille par défaut."""
    if "word/styles.xml" not in fichiers:
        return {}, 10.0
    racine = lire_xml(fichiers["word/styles.xml"])
    sz = racine.find("{}/{}/{}/{}".format(q("w:docDefaults"), q("w:rPrDefault"), q("w:rPr"), q("w:sz")))
    defaut = int(sz.get(q("w:val"))) / 2 if sz is not None else 10.0
    styles = {s.get(q("w:styleId")): s for s in racine.findall(q("w:style"))}

    def taille(ident, vus=()):
        s = styles.get(ident)
        if s is None or ident in vus:
            return defaut
        e = s.find("{}/{}".format(q("w:rPr"), q("w:sz")))
        if e is not None:
            return int(e.get(q("w:val"))) / 2
        base = s.find(q("w:basedOn"))
        return taille(base.get(q("w:val")), vus + (ident,)) if base is not None else defaut

    return {i: taille(i) for i in styles}, defaut


def interligne_multiple(line_twips: int, taille_pt: float, hauteur_ligne: float) -> int:
    """Interligne exact (twips) → interligne multiple (240e de ligne) qui donne la même hauteur."""
    return max(15, round(240 * (line_twips / 20) / (taille_pt * hauteur_ligne)))


def convertir_interlignes(fichiers: dict, messages: list[str], hauteur_ligne: float) -> None:
    par_style, defaut = tailles_styles(fichiers)
    normal = next((i for i in par_style if i.lower() == "normal"), None)
    total = 0
    for nom in [n for n in fichiers if PARTIES.match(n) or n == "word/styles.xml"]:
        racine = lire_xml(fichiers[nom])
        modifie = False
        for espacement in racine.iter(q("w:spacing")):
            ppr = espacement.getparent()
            if ppr.tag != q("w:pPr") or espacement.get(q("w:lineRule")) != "exact" or not espacement.get(q("w:line")):
                continue
            porteur = ppr.getparent()
            if porteur.tag == q("w:p"):
                # Taille : le plus grand texte du paragraphe (sans les zones de texte imbriquées), sinon la marque de paragraphe, sinon le style.
                tailles = [
                    int(sz.get(q("w:val"))) / 2
                    for r in porteur.iter(q("w:r"))
                    if next(a for a in r.iterancestors(q("w:p"))) is porteur
                    for sz in r.findall("{}/{}".format(q("w:rPr"), q("w:sz")))
                ]
                marque = ppr.find("{}/{}".format(q("w:rPr"), q("w:sz")))
                style = ppr.find(q("w:pStyle"))
                taille = (
                    max(tailles) if tailles
                    else int(marque.get(q("w:val"))) / 2 if marque is not None
                    else par_style.get(style.get(q("w:val")) if style is not None else normal, defaut)
                )
            elif porteur.tag == q("w:style"):
                taille = par_style.get(porteur.get(q("w:styleId")), defaut)
            else:
                continue
            espacement.set(q("w:line"), str(interligne_multiple(int(espacement.get(q("w:line"))), taille, hauteur_ligne)))
            espacement.set(q("w:lineRule"), "auto")
            modifie = True
            total += 1
        if modifie:
            fichiers[nom] = ecrire_xml(racine)
    if total:
        messages.append("{} interligne(s) exact(s) converti(s) en interligne multiple".format(total))


# ---------------------------------------------------------------- tableaux

# Ordre des enfants de w:pPr imposé par le schéma (Word refuse un w:ind mal placé).
ORDRE_PPR = (
    "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs "
    "suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd "
    "snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection textAlignment "
    "textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange"
).split()
ORDRE_TCPR = "cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText vAlign hideMark".split()
ORDRE_TCMAR = "top start left bottom end right".split()


def enfant(parent, nom: str, ordre=ORDRE_PPR):
    """Enfant w:nom de parent, créé à sa place dans l'ordre du schéma s'il manque."""
    from lxml import etree

    e = parent.find(q("w:" + nom))
    if e is None:
        e = etree.SubElement(parent, q("w:" + nom))
        rang = ordre.index(nom)
        suivant = next((c for c in parent if c is not e and c.tag.startswith("{%s}" % NS["w"])
                        and c.tag.split("}")[1] in ordre and ordre.index(c.tag.split("}")[1]) > rang), None)
        if suivant is not None:
            suivant.addprevious(e)
    return e


def marges_de_rangees(fichiers: dict, messages: list[str]) -> None:
    """Marges haute et basse de chaque cellule alignées sur la plus grande de sa rangée.

    Word applique à toute la rangée la plus grande marge haute (et basse) de ses cellules ; Google Docs
    applique celle de chaque cellule. Le titre du bandeau (11 mm) remontait de 4 mm à côté du sticker (15 mm).
    """
    total = 0
    for nom in [n for n in fichiers if PARTIES.match(n)]:
        racine = lire_xml(fichiers[nom])
        modifie = False
        for tableau in racine.iter(q("w:tbl")):
            defaut = tableau.find("{}/{}".format(q("w:tblPr"), q("w:tblCellMar")))
            for rangee in tableau.findall(q("w:tr")):
                cellules = rangee.findall(q("w:tc"))
                for cote in ("top", "bottom"):
                    def marge(tc):
                        e = tc.find("{}/{}/{}".format(q("w:tcPr"), q("w:tcMar"), q("w:" + cote)))
                        if e is None and defaut is not None:
                            e = defaut.find(q("w:" + cote))
                        return int(e.get(q("w:w")) or 0) if e is not None and e.get(q("w:type"), "dxa") == "dxa" else 0

                    valeurs = [marge(tc) for tc in cellules]
                    if len(set(valeurs)) < 2:
                        continue
                    for tc, valeur in zip(cellules, valeurs):
                        if valeur < max(valeurs):
                            tcpr = tc.find(q("w:tcPr"))
                            if tcpr is None:
                                tcpr = tc.makeelement(q("w:tcPr"), {})
                                tc.insert(0, tcpr)
                            e = enfant(enfant(tcpr, "tcMar", ORDRE_TCPR), cote, ORDRE_TCMAR)
                            e.set(q("w:w"), str(max(valeurs)))
                            e.set(q("w:type"), "dxa")
                            total += 1
                    modifie = True
        if modifie:
            fichiers[nom] = ecrire_xml(racine)
    if total:
        messages.append("{} marge(s) haute(s) ou basse(s) de cellule alignée(s) sur leur rangée".format(total))


def retraits_styles(fichiers: dict) -> dict[str, int]:
    """Retrait gauche (twips) de chaque style de paragraphe, héritage compris."""
    if "word/styles.xml" not in fichiers:
        return {}
    racine = lire_xml(fichiers["word/styles.xml"])
    styles = {s.get(q("w:styleId")): s for s in racine.findall(q("w:style"))}

    def retrait(ident, vus=()):
        s = styles.get(ident)
        if s is None or ident in vus:
            return 0
        ind = s.find("{}/{}".format(q("w:pPr"), q("w:ind")))
        valeur = None if ind is None else ind.get(q("w:left")) or ind.get(q("w:start"))
        if valeur is not None:
            return int(valeur)
        base = s.find(q("w:basedOn"))
        return retrait(base.get(q("w:val")), vus + (ident,)) if base is not None else 0

    return {i: retrait(i) for i in styles}


def marges_en_retraits(fichiers: dict, messages: list[str]) -> None:
    """Marge gauche des cellules → retrait des paragraphes de la cellule.

    Google Docs place le bord d'un tableau au retrait du tableau moins la marge gauche de sa première
    cellule (ancien comportement de Word) : le tableau glisse vers la gauche, de 17 mm pour le bandeau
    du plan. Sans marge gauche de cellule, Word et Google Docs le placent au même endroit.
    """
    par_style = retraits_styles(fichiers)
    normal = next((i for i in par_style if i.lower() == "normal"), None)
    total = 0
    for nom in [n for n in fichiers if PARTIES.match(n)]:
        racine = lire_xml(fichiers[nom])
        modifie = False
        for marge in racine.iter(q("w:tcMar")):
            gauche = marge.find(q("w:left"))
            if gauche is None:
                gauche = marge.find(q("w:start"))
            if gauche is None or gauche.get(q("w:type"), "dxa") != "dxa" or int(gauche.get(q("w:w")) or 0) <= 0:
                continue
            valeur = int(gauche.get(q("w:w")))
            cellule = marge.getparent().getparent()
            for p in cellule.findall(q("w:p")):
                ppr = p.find(q("w:pPr"))
                if ppr is None:
                    ppr = p.makeelement(q("w:pPr"), {})
                    p.insert(0, ppr)
                ind = enfant(ppr, "ind")
                actuel = ind.get(q("w:left")) or ind.get(q("w:start"))
                if actuel is None:
                    style = ppr.find(q("w:pStyle"))
                    actuel = par_style.get(style.get(q("w:val")) if style is not None else normal, 0)
                ind.set(q("w:start") if ind.get(q("w:start")) is not None else q("w:left"), str(int(actuel) + valeur))
            gauche.set(q("w:w"), "0")
            modifie = True
            total += 1
        if modifie:
            fichiers[nom] = ecrire_xml(racine)
    if total:
        messages.append("{} marge(s) gauche(s) de cellule convertie(s) en retrait de paragraphe".format(total))


def paragraphes_avant_tableaux(fichiers: dict, messages: list[str]) -> None:
    """Paragraphe minuscule avant un tableau placé en tête d'en-tête, de pied ou de document.

    Google Docs y ajoute sinon un paragraphe vide de taille normale : le bandeau descend de 5 mm.
    """
    from lxml import etree

    total = 0
    for nom in [n for n in fichiers if re.match(r"word/(document|header\d+|footer\d+)\.xml$", n)]:
        racine = lire_xml(fichiers[nom])
        conteneur = racine.find(q("w:body")) if racine.tag == q("w:document") else racine
        premier = next((c for c in conteneur if isinstance(c.tag, str)), None)
        if premier is None or premier.tag != q("w:tbl"):
            continue
        p = etree.fromstring(
            '<w:p xmlns:w="{}"><w:pPr><w:spacing w:before="0" w:after="0" w:line="15" w:lineRule="auto"/>'
            '<w:ind w:left="0" w:right="0"/><w:rPr><w:sz w:val="2"/></w:rPr></w:pPr></w:p>'.format(NS["w"])
        )
        premier.addprevious(p)
        fichiers[nom] = ecrire_xml(racine)
        total += 1
    if total:
        messages.append("{} paragraphe(s) minuscule(s) ajouté(s) avant un tableau d'en-tête".format(total))


# ---------------------------------------------------------------- images


def largeurs_affichage(fichiers: dict) -> dict[str, float]:
    """Largeur d'affichage maximale (pouces) de chaque image du document."""
    largeurs: dict[str, float] = {}
    for nom in [n for n in fichiers if PARTIES.match(n)]:
        relations = cibles(fichiers, chemin_rels(nom))
        for dessin in lire_xml(fichiers[nom]).iter(q("w:drawing")):
            etendue = next(dessin.iter(q("wp:extent")), None)
            if etendue is None:
                continue
            for blip in dessin.iter(q("a:blip")):
                media = relations.get(blip.get(q("r:embed")))
                if media:
                    largeurs[media] = max(largeurs.get(media, 0), int(etendue.get("cx")) / 914400)
    return largeurs


def palette_transparente(im, couleurs: int = 16, niveaux: int = 16):
    """Image RGBA → palette de couleurs × niveaux de transparence, et sa table de transparence.

    Les bords lissés et les ombres douces (sticker) survivent, alors que la quantification RGBA de
    Pillow les écrase.
    """
    from PIL import Image

    rgb = im.convert("RGB").quantize(couleurs, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = (rgb.getpalette() or [])[: 3 * couleurs]
    pal += [0] * (3 * couleurs - len(pal))
    pas = 255 / (niveaux - 1)
    indices = bytes(c * niveaux + round(a / pas) for c, a in zip(rgb.tobytes(), im.getchannel("A").tobytes()))
    p = Image.frombytes("P", im.size, indices)
    p.putpalette([v for c in range(couleurs) for _ in range(niveaux) for v in pal[3 * c:3 * c + 3]])
    return p, bytes(round(n * pas) for _ in range(couleurs) for n in range(niveaux))


def alleger_images(fichiers: dict, messages: list[str], dpi: float) -> None:
    from PIL import Image

    largeurs = largeurs_affichage(fichiers)
    avant = apres = 0
    for k, nom in enumerate(sorted(n for n in fichiers if n.startswith("word/media/"))):
        try:
            im = Image.open(io.BytesIO(fichiers[nom]))
            im.load()
        except Exception:
            continue
        format_ = im.format
        if format_ not in ("PNG", "JPEG") or nom not in largeurs:
            continue
        transparente = im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info)
        if transparente:
            im = im.convert("RGBA")
            transparente = im.getchannel("A").getextrema()[0] < 255
        cible = max(24, round(largeurs[nom] * dpi))
        if transparente:
            cible = max(cible, LARGEUR_MINI_TRANSPARENTE)
        cible += k % 8  # en-têtes d'images distincts : la recopie du base64 ne saute pas d'une image à l'autre
        if im.width > cible:
            im = im.resize((cible, max(1, round(im.height * cible / im.width))), Image.LANCZOS)
        tampon = io.BytesIO()
        if format_ == "JPEG":
            im.convert("RGB").save(tampon, "JPEG", quality=82, optimize=True)
        elif transparente:
            p, table = palette_transparente(im)
            p.save(tampon, "PNG", optimize=True, transparency=table)
        elif im.convert("RGB").getcolors(4096) is not None:
            im.convert("RGB").quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(tampon, "PNG", optimize=True)
        else:
            im.convert("RGB").save(tampon, "PNG", optimize=True)
        avant += len(fichiers[nom])
        if len(tampon.getvalue()) < len(fichiers[nom]):
            fichiers[nom] = tampon.getvalue()
        apres += len(fichiers[nom])
    if avant:
        messages.append("images réduites à leur taille d'affichage : {} Ko → {} Ko".format(round(avant / 1024), round(apres / 1024)))
    # Noms courts : 0.png, 1.png…
    medias = sorted(n for n in fichiers if n.startswith("word/media/"))
    noms = {m: "word/media/{}{}".format(i, posixpath.splitext(m)[1].lower()) for i, m in enumerate(medias)}
    for rels in [n for n in fichiers if n.endswith(".rels")]:
        texte = fichiers[rels].decode("utf-8")
        for ancien, nouveau in noms.items():
            texte = texte.replace('"media/{}"'.format(ancien[11:]), '"media/{}"'.format(nouveau[11:]))
            texte = texte.replace('"/{}"'.format(ancien), '"/{}"'.format(nouveau))
        fichiers[rels] = texte.encode("utf-8")
    contenus = {nouveau: fichiers.pop(ancien) for ancien, nouveau in noms.items()}
    fichiers.update(contenus)


# ---------------------------------------------------------------- base64


def plus_long_repete(texte: str, k: int = 16) -> tuple[int, int, int]:
    """Plus long passage présent deux fois dans le texte : (longueur, position 1, position 2).

    Une recopie à la main du base64 « saute » volontiers d'un passage à son jumeau : au-delà de
    40 caractères environ, le risque devient réel.
    """
    index: dict[str, list[int]] = {}
    for i in range(len(texte) - k + 1):
        positions = index.setdefault(texte[i:i + k], [])
        if len(positions) < 50:
            positions.append(i)
    meilleur = (0, 0, 0)
    for positions in index.values():
        for a in range(len(positions)):
            for b in range(a + 1, len(positions)):
                i, j = positions[a], positions[b]
                if i > 0 and texte[i - 1] == texte[j - 1]:
                    continue
                n = 0
                while j + n < len(texte) and texte[i + n] == texte[j + n]:
                    n += 1
                meilleur = max(meilleur, (n, i, j))
    return meilleur


# ---------------------------------------------------------------- traitement complet


def preparer_docx(donnees: bytes, dpi: float = DPI, hauteur_ligne: float = HAUTEUR_LIGNE) -> tuple[bytes, list[str]]:
    """DOCX allégé et sans interligne exact : (octets, liste de ce qui a été fait)."""
    source = zipfile.ZipFile(io.BytesIO(donnees))
    fichiers = {i.filename: source.read(i.filename) for i in source.infolist() if not i.filename.endswith("/")}
    messages: list[str] = []
    retirer_inutiles(fichiers, messages)
    elaguer_styles(fichiers, messages)
    convertir_interlignes(fichiers, messages, hauteur_ligne)
    marges_en_retraits(fichiers, messages)
    marges_de_rangees(fichiers, messages)
    paragraphes_avant_tableaux(fichiers, messages)
    alleger_images(fichiers, messages, dpi)
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as sortie:
        for nom in ["[Content_Types].xml"] + sorted(n for n in fichiers if n != "[Content_Types].xml"):
            sortie.writestr(nom, fichiers[nom])
    resultat = tampon.getvalue()
    messages.append("taille : {} Ko → {} Ko (base64 : {} caractères)".format(
        round(len(donnees) / 1024), round(len(resultat) / 1024), len(base64.b64encode(resultat))))
    return resultat, messages


def main() -> None:
    parser = argparse.ArgumentParser(description="DOCX prêt pour Google Docs : allégé, sans interligne exact.")
    parser.add_argument("docx", help="fichier .docx à préparer")
    parser.add_argument("--sortie", help="fichier produit (par défaut : <nom>.google-docs.docx)")
    parser.add_argument("--dpi", type=float, default=DPI, help="résolution des images à leur taille d'affichage (110 par défaut)")
    parser.add_argument("--hauteur-ligne", type=float, default=HAUTEUR_LIGNE,
                        help="hauteur de ligne naturelle de la police / taille (Raleway : 1,174)")
    parser.add_argument("--base64", action="store_true", help="écrit aussi le base64 en lignes de 12 000 caractères (.b64.txt)")
    args = parser.parse_args()
    source = Path(args.docx)
    sortie = Path(args.sortie) if args.sortie else source.with_name(source.stem + ".google-docs.docx")
    resultat, messages = preparer_docx(source.read_bytes(), args.dpi, args.hauteur_ligne)
    sortie.write_bytes(resultat)
    for m in messages:
        print("- " + m)
    texte = base64.b64encode(resultat).decode()
    n, _, _ = plus_long_repete(texte)
    print("- plus long passage répété du base64 : {} caractères{}".format(n, " (au-delà de 40 : recopie risquée)" if n > 40 else ""))
    if args.base64:
        b64 = sortie.with_name(sortie.name + ".b64.txt")
        b64.write_text("\n".join(texte[i:i + 12000] for i in range(0, len(texte), 12000)) + "\n", encoding="ascii")
        print(b64)
    print(sortie)


if __name__ == "__main__":
    sys.exit(main())
