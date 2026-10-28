#!/usr/bin/env python3
"""Corrige l'interligne d'un Google Docs importé d'un .docx en interligne « exact ».

Usage :
    python scripts/interligne_google_docs.py plan.docx doc.json [--sortie requetes.json]

- plan.docx : le .docx importé (celui d'origine, pas celui passé par docx_google_docs.py) ;
- doc.json : la lecture du Google Docs (documents.get de l'API Google Docs, ou l'outil de lecture d'un
  connecteur, enregistré dans un fichier) ;
- requetes.json : les requêtes à envoyer en un seul lot (documents.batchUpdate, ou l'outil de mise à
  jour du connecteur), avec writeControl.requiredRevisionId = revisionId de la lecture.

Google Docs convertit un interligne exact de L twips en L/240 × 100 %, puis applique ce pourcentage à
la hauteur de ligne naturelle de la police (Raleway : 1,174 × la taille). Le texte s'étire, et le plan
passe de 2 à 3 pages. L'interligne juste, paragraphe par paragraphe, est :

    interligne (%) = (L / 20) / (taille × 1,174) × 100

où taille est la taille de police du paragraphe dans Google Docs, ou 10 pt (style « Texte normal »)
quand elle n'est pas définie, comme pour les paragraphes vides d'espacement.

Les paragraphes des deux documents sont appariés par leur texte. Les plages consécutives de même valeur
sont regroupées. Le paragraphe vide que Google ajoute au début d'une section, avant son tableau
d'en-tête, est ramené à 1 pt et 100 %.

Mieux vaut, quand c'est possible, réimporter le .docx passé par docx_google_docs.py : il n'a plus
d'interligne exact, et rien n'est à corriger. Le script sert pour un Google Docs déjà importé et retouché.
"""

from __future__ import annotations

import argparse
import difflib
import io
import json
import re
import sys
import zipfile
from pathlib import Path

HAUTEUR_LIGNE = 1.174  # hauteur de ligne naturelle de Raleway, rapportée à la taille de police
TAILLE_DEFAUT = 10  # pt : style « Texte normal » du document converti
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def paragraphes_docx(donnees: bytes, partie: str = "word/document.xml") -> list[dict]:
    """Paragraphes d'une partie du .docx : texte, interligne (w:line, w:lineRule) et taille (pt)."""
    from lxml import etree

    racine = etree.fromstring(zipfile.ZipFile(io.BytesIO(donnees)).read(partie))
    resultat = []
    for p in racine.iter(W + "p"):
        espacement = p.find("{0}pPr/{0}spacing".format(W))
        ligne = espacement.get(W + "line") if espacement is not None else None
        regle = espacement.get(W + "lineRule") if espacement is not None else None
        tailles = [int(s.get(W + "val")) / 2 for s in p.iter(W + "sz") if s.get(W + "val", "").isdigit()]
        texte = "".join(t.text or "" for t in p.iter(W + "t"))
        resultat.append({"texte": texte, "line": int(ligne) if ligne and ligne.lstrip("-").isdigit() else None,
                         "regle": regle or ("auto" if ligne else None), "taille": max(tailles) if tailles else None})
    return resultat


def document_google(lecture: dict) -> dict:
    """Le document, que la lecture soit enregistrée telle quelle ou sous la clé « content »."""
    return lecture.get("content", lecture)


def paragraphes_google(document: dict) -> list[dict]:
    """Paragraphes du corps du Google Docs, tableaux compris, dans l'ordre : texte, indices, taille, interligne."""
    onglets = document.get("tabs")
    corps = onglets[0]["documentTab"]["body"]["content"] if onglets else document["body"]["content"]
    resultat = []

    def parcourir(contenu):
        for el in contenu:
            if "paragraph" in el:
                p = el["paragraph"]
                passages = [e["textRun"] for e in p["elements"] if "textRun" in e]
                tailles = [t.get("textStyle", {}).get("fontSize", {}).get("magnitude") for t in passages]
                tailles = [t for t in tailles if t]
                resultat.append({"texte": "".join(t.get("content", "") for t in passages).rstrip("\n"),
                                 "debut": el["startIndex"], "fin": el["endIndex"],
                                 "taille": max(tailles) if tailles else None,
                                 "interligne": p.get("paragraphStyle", {}).get("lineSpacing")})
            elif "table" in el:
                for rangee in el["table"]["tableRows"]:
                    for cellule in rangee["tableCells"]:
                        parcourir(cellule["content"])

    parcourir(corps)
    return resultat


def cle(texte: str) -> str:
    return re.sub(r"\s+", " ", texte.replace("\u000b", " ")).strip()[:60]


def interligne_juste(line_twips: int, taille_pt: float, hauteur_ligne: float = HAUTEUR_LIGNE) -> float:
    """Interligne Google Docs (%) qui redonne la hauteur exacte de Word."""
    return round(line_twips / 20 / (taille_pt * hauteur_ligne) * 100, 1)


def requetes_interligne(lecture: dict, paragraphes: list[dict], hauteur_ligne: float = HAUTEUR_LIGNE,
                        taille_defaut: float = TAILLE_DEFAUT) -> tuple[list[dict], list[str]]:
    """Requêtes updateParagraphStyle (lineSpacing) et liste des paragraphes non appariés."""
    document = document_google(lecture)
    google = paragraphes_google(document)
    a, b = [cle(p["texte"]) for p in paragraphes], [cle(p["texte"]) for p in google]
    paires, non_apparies = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            paires += zip(range(i1, i2), range(j1, j2))
        else:
            non_apparies += ["Word : " + t for t in a[i1:i2] if t] + ["Google Docs : " + t for t in b[j1:j2] if t]
    voulus = {}
    for i, j in paires:
        source, cible = paragraphes[i], google[j]
        if source["regle"] == "exact" and source["line"]:
            voulu = interligne_juste(source["line"], cible["taille"] or taille_defaut, hauteur_ligne)
            if cible["interligne"] is None or abs(cible["interligne"] - voulu) >= 0.6:
                voulus[j] = voulu
    plages = []
    for j in sorted(voulus, key=lambda j: google[j]["debut"]):
        p = google[j]
        if plages and plages[-1]["valeur"] == voulus[j] and plages[-1]["fin"] == p["debut"]:
            plages[-1]["fin"] = p["fin"]
        else:
            plages.append({"debut": p["debut"], "fin": p["fin"], "valeur": voulus[j]})
    requetes = [{"updateParagraphStyle": {"range": {"startIndex": r["debut"], "endIndex": r["fin"]},
                                          "paragraphStyle": {"lineSpacing": r["valeur"]}, "fields": "lineSpacing"}}
                for r in plages]
    return requetes + requetes_paragraphes_ajoutes(document), non_apparies


def requetes_paragraphes_ajoutes(document: dict) -> list[dict]:
    """Paragraphe vide ajouté par Google au début d'une section, avant son tableau : 1 pt et 100 %."""
    onglets = document.get("tabs")
    corps = onglets[0]["documentTab"]["body"]["content"] if onglets else document["body"]["content"]
    requetes = []
    for avant, el, apres in zip(corps, corps[1:], corps[2:]):
        if "sectionBreak" in avant and "paragraph" in el and "table" in apres and avant.get("startIndex") is not None:
            texte = "".join(e.get("textRun", {}).get("content", "") for e in el["paragraph"]["elements"])
            if texte == "\n":
                plage = {"startIndex": el["startIndex"], "endIndex": el["endIndex"]}
                requetes += [{"updateTextStyle": {"range": plage, "textStyle": {"fontSize": {"magnitude": 1, "unit": "PT"}},
                                                  "fields": "fontSize"}},
                             {"updateParagraphStyle": {"range": plage, "paragraphStyle": {"lineSpacing": 100},
                                                       "fields": "lineSpacing"}}]
    return requetes


def main() -> None:
    # Console Windows (cp1252) : un caractère non représentable s'affiche « ? » au lieu d'arrêter le script.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Requêtes de correction de l'interligne d'un Google Docs importé d'un .docx.")
    parser.add_argument("docx", help=".docx importé dans Google Docs")
    parser.add_argument("lecture", help="lecture du Google Docs (JSON de documents.get)")
    parser.add_argument("--sortie", help="fichier des requêtes (par défaut : sortie standard)")
    parser.add_argument("--hauteur-ligne", type=float, default=HAUTEUR_LIGNE, help="hauteur de ligne naturelle / taille (Raleway : 1,174)")
    args = parser.parse_args()
    paragraphes = paragraphes_docx(Path(args.docx).read_bytes())
    requetes, non_apparies = requetes_interligne(json.loads(Path(args.lecture).read_text(encoding="utf-8")),
                                                 paragraphes, args.hauteur_ligne)
    exacts = sum(p["regle"] == "exact" for p in paragraphes)
    print("{} paragraphes Word dont {} en interligne exact ; {} requête(s)".format(len(paragraphes), exacts, len(requetes)), file=sys.stderr)
    for t in non_apparies[:20]:
        print("non apparié, " + t, file=sys.stderr)
    texte = json.dumps({"requests": requetes}, ensure_ascii=False, separators=(",", ":"))
    if args.sortie:
        Path(args.sortie).write_text(texte, encoding="utf-8")
        print(args.sortie, file=sys.stderr)
    else:
        print(texte)


if __name__ == "__main__":
    sys.exit(main())
