#!/usr/bin/env python3
"""DOCX prêt pour Google Docs : allège un .docx et remplace l'interligne exact, que Google Docs convertit mal.

Usage :
    python scripts/docx_google_docs.py plan.docx [--sortie plan.google-docs.docx] [--dpi 110] [--base64]
    python scripts/docx_google_docs.py --verifier-recopie plan.google-docs.docx.b64.txt recopie.b64

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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from charte import est_graphique, palette_transparente  # noqa: E402  (images transparentes : voir charte.py)

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
HAUTEUR_LIGNE = 1.174  # hauteur de ligne naturelle de Raleway, rapportée à la taille de police
DPI = 110  # images : nettes à l'écran, un peu moins à l'impression
DPI_GRAPHIQUE = 220  # images transparentes (logo, sticker) : nettes à l'écran comme à l'impression
DPI_COMPACT = 80  # --compact : tout le DOCX sous 30 000 caractères de base64, pour un connecteur Google Drive
PARTIES = re.compile(r"word/(document|header\d+|footer\d+|footnotes|endnotes|comments)\.xml$")
INUTILES = re.compile(
    r"^(word/fonts/.+|word/fontTable\.xml|word/stylesWithEffects\.xml|word/webSettings\.xml|docProps/(app|core|custom)\.xml|"
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
    # Réglages d'affichage et d'édition sans effet sur la mise en page (zoom, langue du thème, séparateurs…).
    transformer(fichiers, "word/settings.xml", lambda s: re.sub(
        r"<w:(zoom|proofState|characterSpacingControl|themeFontLang|clrSchemeMapping|doNotAutoCompressPictures|decimalSymbol|listSeparator)\b[^>]*/>"
        r"|<w14:(docId|defaultImageDpi)\b[^>]*/>", "", s))
    # Identifiants de révision, réglages mathématiques et formes par défaut : inutiles à l'affichage.
    transformer(fichiers, "word/settings.xml", lambda s: re.sub(
        r"<w:rsids>.*?</w:rsids>|<m:mathPr>.*?</m:mathPr>|<w:shapeDefaults>.*?</w:shapeDefaults>|<w:(savePreviewPicture|attachedTemplate)\b[^>]*/>",
        "", s, flags=re.S))
    if not any(n.endswith(".odttf") for n in fichiers):
        transformer(fichiers, "[Content_Types].xml", lambda s: re.sub(r'<Default Extension="odttf"[^>]*/>', "", s))
    autres = [n for n in inutiles if not n.startswith("word/fonts/")]
    if autres:
        messages.append("parties inutiles retirées : " + ", ".join(sorted(autres)))


def alleger_proprietes(fichiers: dict, messages: list[str]) -> None:
    """Retire les propriétés de passage redondantes : attributs des écritures complexes (szCs, bCs, iCs) et
    police identique à la police par défaut, si aucun style n'en impose une autre."""
    styles = fichiers.get("word/styles.xml", b"").decode("utf-8")
    defaut = re.search(r"<w:rPrDefault>.*?</w:rPrDefault>", styles, re.S)
    police = re.search(r'<w:rFonts\b[^>]*w:ascii="([^"]+)"', defaut.group(0)) if defaut else None
    police = police.group(1) if police else None

    def redondante(attributs: str) -> bool:
        valeurs = dict(re.findall(r'w:(\w+)="([^"]*)"', attributs))
        return {"ascii", "hAnsi"} <= set(valeurs) <= {"ascii", "hAnsi", "cs", "eastAsia"} and set(valeurs.values()) == {police}

    hors_defaut = styles.replace(defaut.group(0), "") if defaut else styles
    if police and not all(redondante(a) for a in re.findall(r"<w:rFonts\b([^>]*)/>", hors_defaut)):
        police = None  # un style impose une autre police : chaque passage garde la sienne
    # Couleur et taille identiques à celles du style Normal, si aucun autre style n'en impose.
    normal = re.search(r'<w:style\b[^>]*w:styleId="Normal"[^>]*>.*?</w:style>', styles, re.S)
    rpr_normal = re.search(r"<w:rPr>.*?</w:rPr>", normal.group(0), re.S) if normal else None
    rpr_normal = rpr_normal.group(0) if rpr_normal else ""
    valeurs = {balise: re.search(r'<w:{} w:val="([0-9A-Fa-f]+)"/>'.format(balise), rpr_normal) for balise in ("color", "sz")}
    autres = [st for st in re.findall(r"<w:style\b[^>]*>.*?</w:style>", styles, re.S)
              if 'w:styleId="Normal"' not in st and 'w:type="table"' not in st]
    if any(re.search(r"<w:(color|sz)\b", st) for st in autres):
        valeurs = {}
    retirees = 0
    for nom in [n for n in fichiers if PARTIES.match(n)]:
        texte = fichiers[nom].decode("utf-8")
        texte, n = re.subn(r"<w:(szCs|bCs|iCs)\b[^>]*/>", "", texte)
        retirees += n
        texte = re.sub(r'\sw:rsid\w*="[0-9A-Fa-f]+"', "", texte)
        if police:
            texte, n = re.subn(r"<w:rFonts\b([^>]*)/>", lambda m: "" if redondante(m.group(1)) else m.group(0), texte)
            retirees += n
        for balise, trouve in valeurs.items():
            if trouve:
                motif = r'(<w:rPr>(?:(?!</w:rPr>).)*?)<w:{} w:val="{}"/>'.format(balise, trouve.group(1))
                texte, n = re.subn(motif, r"\1", texte, flags=re.S)
                retirees += n
        texte = re.sub(r"<w:rPr>\s*</w:rPr>|<w:rPr/>", "", texte)
        fichiers[nom] = texte.encode("utf-8")
    if retirees:
        messages.append("{} propriété(s) de passage redondante(s) retirée(s)".format(retirees))


def elaguer_styles(fichiers: dict, messages: list[str]) -> None:
    """Retire les styles latents et les styles que rien n'utilise (ils pèsent l'essentiel de styles.xml)."""
    if "word/styles.xml" not in fichiers:
        return
    racine = lire_xml(fichiers["word/styles.xml"])
    for latents in racine.findall(q("w:latentStyles")):
        racine.remove(latents)
    styles = {s.get(q("w:styleId")): s for s in racine.findall(q("w:style"))}
    texte = b"".join(v for n, v in fichiers.items() if PARTIES.match(n) or n == "word/settings.xml").decode("utf-8", "replace")
    # Une numérotation ne garde ses styles (puces, listes) que si le texte s'en sert : sinon le gabarit
    # python-docx garde six styles de liste et leurs numérotations, qui se retiennent mutuellement.
    numerotation = fichiers.get("word/numbering.xml", b"").decode("utf-8", "replace")
    utilises = set(re.findall(r'<w:numId w:val="(\d+)"', texte))
    abstraits = {a for n, a in re.findall(r'<w:num w:numId="(\d+)"[^>]*>\s*<w:abstractNumId w:val="(\d+)"', numerotation) if n in utilises}
    texte += "".join(m.group(0) for m in re.finditer(r'<w:abstractNum\b[^>]*w:abstractNumId="(\d+)".*?</w:abstractNum>', numerotation, re.S)
                     if m.group(1) in abstraits)
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


def elaguer_numerotation_polices_theme(fichiers: dict, messages: list[str]) -> None:
    """Retire les numérotations et les polices que rien n'utilise, et le thème s'il ne sert pas.

    Le gabarit python-docx en apporte une douzaine de chaque : autant de base64 en moins à recopier.
    """
    texte = lambda: b"".join(v for n, v in fichiers.items() if PARTIES.match(n) or n in ("word/styles.xml", "word/numbering.xml")).decode("utf-8", "replace")  # noqa: E731
    retires = []
    if "word/numbering.xml" in fichiers:
        racine = lire_xml(fichiers["word/numbering.xml"])
        utilises = set(re.findall(r'<w:numId w:val="(\d+)"', b"".join(v for n, v in fichiers.items() if PARTIES.match(n) or n == "word/styles.xml").decode("utf-8", "replace")))
        abstraits = set()
        for num in racine.findall(q("w:num")):
            if num.get(q("w:numId")) in utilises:
                abstraits.add(num.find(q("w:abstractNumId")).get(q("w:val")))
            else:
                racine.remove(num)
                retires.append("num")
        for a in racine.findall(q("w:abstractNum")):
            if a.get(q("w:abstractNumId")) not in abstraits:
                racine.remove(a)
        fichiers["word/numbering.xml"] = ecrire_xml(racine)
    if "word/fontTable.xml" in fichiers:
        polices = set(re.findall(r'w:(?:ascii|hAnsi|cs|eastAsia)="([^"]+)"', texte()))
        racine = lire_xml(fichiers["word/fontTable.xml"])
        for f in racine.findall(q("w:font")):
            if f.get(q("w:name")) not in polices:
                racine.remove(f)
                retires.append("police")
        fichiers["word/fontTable.xml"] = ecrire_xml(racine)
    themes = [n for n in fichiers if re.match(r"word/theme/theme\d+\.xml$", n)]
    if themes and not re.search(r"Theme=|w:theme(Color|Fill|Shade|Tint)=", texte()):
        for n in themes:
            retirer(fichiers, n)
        retires.append("thème")
    if retires:
        messages.append("{} numérotation(s) et {} police(s) inutilisée(s) retirée(s){}".format(
            retires.count("num"), retires.count("police"), ", thème retiré" if "thème" in retires else ""))


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


def alleger_images(fichiers: dict, messages: list[str], dpi: float, compact: bool = False) -> None:
    """Images à leur taille d'affichage : fonds à dpi, images transparentes (logo, sticker) à DPI_GRAPHIQUE.
    Seuls logo et icônes passent sur une palette, sans perte ; sticker et photos restent en couleurs vraies.
    En mode compact (connecteur Google Drive), tout est à DPI_COMPACT et en palette : plus léger, moins net."""
    from PIL import Image

    largeurs = largeurs_affichage(fichiers)
    largeurs_vues: set[int] = set()
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
        cible = max(24, round(largeurs[nom] * (DPI_GRAPHIQUE if transparente and not compact else dpi)))
        cible += k % 8  # en-têtes d'images distincts : la recopie du base64 ne saute pas d'une image à l'autre
        if not transparente and im.mode != "RGB":
            im = im.convert("RGB")
        retaillee = False
        if im.width > cible:
            im = im.resize((cible, max(1, round(im.height * cible / im.width))), Image.LANCZOS)
            retaillee = True
        # Deux images de même largeur ont des en-têtes PNG jumeaux, même sans retaille : 1 px de moins.
        while im.width in largeurs_vues and im.width > 24:
            im = im.resize((im.width - 1, max(1, round(im.height * (im.width - 1) / im.width))), Image.LANCZOS)
            retaillee = True
        largeurs_vues.add(im.width)
        tampon = io.BytesIO()
        if format_ == "JPEG":
            im.convert("RGB").save(tampon, "JPEG", quality=82, optimize=True)
        elif transparente:
            if compact or est_graphique(im):  # logo : couleurs franches et 16 niveaux de transparence
                p, table = palette_transparente(im, *((6, 5) if compact else ()))
                p.save(tampon, "PNG", optimize=True, transparency=table)
            else:
                im.save(tampon, "PNG", optimize=True)  # sticker : couleurs vraies, contour lisse
        elif im.convert("RGB").getcolors(4096) is not None:
            im.convert("RGB").quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(tampon, "PNG", optimize=True)
        else:
            im.convert("RGB").save(tampon, "PNG", optimize=True)
        avant += len(fichiers[nom])
        if retaillee or len(tampon.getvalue()) < len(fichiers[nom]):
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


def comparer_recopie(original: str, recopie: str) -> list[tuple[int, str, str]]:
    """Écarts entre le base64 et sa recopie : (position dans l'original, attendu, recopié).

    C'est le diagnostic qui a trouvé les erreurs des imports refusés : une recopie de 30 000 caractères
    qui saute d'un passage à son jumeau, ou qui reprend une version précédente du même fichier.
    """
    import difflib

    original, recopie = re.sub(r"\s", "", original), re.sub(r"\s", "", recopie)
    return [(i1, original[i1:i2][:60], recopie[j1:j2][:60])
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, original, recopie, autojunk=False).get_opcodes()
            if tag != "equal"]


# ---------------------------------------------------------------- traitement complet


def preparer_docx(donnees: bytes, dpi: float = DPI, hauteur_ligne: float = HAUTEUR_LIGNE, compact: bool = False) -> tuple[bytes, list[str]]:
    """DOCX allégé et sans interligne exact : (octets, liste de ce qui a été fait)."""
    source = zipfile.ZipFile(io.BytesIO(donnees))
    fichiers = {i.filename: source.read(i.filename) for i in source.infolist() if not i.filename.endswith("/")}
    messages: list[str] = []
    retirer_inutiles(fichiers, messages)
    elaguer_styles(fichiers, messages)
    elaguer_numerotation_polices_theme(fichiers, messages)
    alleger_proprietes(fichiers, messages)
    convertir_interlignes(fichiers, messages, hauteur_ligne)
    marges_en_retraits(fichiers, messages)
    marges_de_rangees(fichiers, messages)
    paragraphes_avant_tableaux(fichiers, messages)
    alleger_images(fichiers, messages, DPI_COMPACT if compact else dpi, compact)
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as sortie:
        for nom in ["[Content_Types].xml"] + sorted(n for n in fichiers if n != "[Content_Types].xml"):
            sortie.writestr(nom, fichiers[nom])
    resultat = tampon.getvalue()
    messages.append("taille : {} Ko → {} Ko (base64 : {} caractères)".format(
        round(len(donnees) / 1024), round(len(resultat) / 1024), len(base64.b64encode(resultat))))
    return resultat, messages


def main() -> None:
    # Console Windows (cp1252) : un caractère non représentable s'affiche « ? » au lieu d'arrêter le script.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="DOCX prêt pour Google Docs : allégé, sans interligne exact.")
    parser.add_argument("docx", nargs="?", help="fichier .docx à préparer")
    parser.add_argument("--sortie", help="fichier produit (par défaut : <nom>.google-docs.docx)")
    parser.add_argument("--dpi", type=float, default=DPI, help="résolution des images à leur taille d'affichage (110 par défaut)")
    parser.add_argument("--hauteur-ligne", type=float, default=HAUTEUR_LIGNE,
                        help="hauteur de ligne naturelle de la police / taille (Raleway : 1,174)")
    parser.add_argument("--compact", action="store_true",
                        help="pour un connecteur Google Drive : images à 80 dpi, sous 30 000 caractères de base64 (logo et sticker moins nets)")
    parser.add_argument("--base64", action="store_true", help="écrit aussi le base64 en lignes de 12 000 caractères (.b64.txt)")
    parser.add_argument("--verifier-recopie", nargs=2, metavar=("ORIGINAL", "RECOPIE"),
                        help="compare le base64 (.b64.txt) à sa recopie avant de l'envoyer au connecteur")
    args = parser.parse_args()
    if args.verifier_recopie:
        original, recopie = (Path(f).read_text(encoding="ascii", errors="replace") for f in args.verifier_recopie)
        ecarts = comparer_recopie(original, recopie)
        for position, attendu, recopie in ecarts[:10]:
            print("- position {} : attendu {!r}, recopié {!r}".format(position, attendu, recopie))
        print("Recopie identique : elle peut partir." if not ecarts else "{} écart(s) : refaire la recopie.".format(len(ecarts)))
        raise SystemExit(1 if ecarts else 0)
    if not args.docx:
        parser.error("indiquer le fichier .docx à préparer")
    source = Path(args.docx)
    sortie = Path(args.sortie) if args.sortie else source.with_name(source.stem + ".google-docs.docx")
    resultat, messages = preparer_docx(source.read_bytes(), args.dpi, args.hauteur_ligne, args.compact)
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
