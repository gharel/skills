#!/usr/bin/env python3
"""Support de formation Skazy Formation : support.json → support.html (deck) et support.pptx.

Usage :
    python scripts/rendre_support.py support.json [--sortie DOSSIER] [--formats html,pptx] [--verifier]

Le JSON suit references/format-support.md. Le HTML reproduit les 30 mises en page du modèle
« 4. Support de formation par catégorie » (Skazy Formation Design System, Claude Design) ;
le PPTX en reprend la mise en page, avec les notes formateur, pour PowerPoint et Google Slides.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import charte as ch  # noqa: E402
from support_modele import normaliser_support  # noqa: E402


def rendre(chemin_json: str, sortie: str | None = None, formats=("html", "pptx")) -> list[Path]:
    s, rapport = normaliser_support(ch.lire_json(chemin_json))
    rapport.afficher()
    if not rapport.ok:
        raise SystemExit(1)
    dossier = Path(sortie) if sortie else Path(chemin_json).resolve().parent
    dossier.mkdir(parents=True, exist_ok=True)
    base = "support-" + ch.slug(s["formation"]["intitule"])
    fichiers = []
    if "html" in formats:
        from support_html import rendre_html

        f = dossier / (base + ".html")
        f.write_text(rendre_html(s), encoding="utf-8")
        fichiers.append(f)
    if "pptx" in formats:
        from support_pptx import rendre_pptx

        f = dossier / (base + ".pptx")
        f.write_bytes(rendre_pptx(s))
        fichiers.append(f)
    return fichiers


def main() -> None:
    parser = argparse.ArgumentParser(description="Support de formation Skazy Formation : JSON → HTML et PPTX.")
    parser.add_argument("json", help="fichier support.json (voir references/format-support.md)")
    parser.add_argument("--sortie", help="dossier de sortie (par défaut : celui du JSON)")
    parser.add_argument("--formats", default="html,pptx", help="formats à produire : html, pptx (séparés par des virgules)")
    parser.add_argument("--verifier", action="store_true", help="contrôle le JSON sans rien produire")
    args = parser.parse_args()
    if args.verifier:
        s, rapport = normaliser_support(ch.lire_json(args.json))
        rapport.afficher()
        if rapport.ok:
            print("Support valide : {} slides.".format(len(s["_slides"])))
        raise SystemExit(0 if rapport.ok else 1)
    for f in rendre(args.json, args.sortie, [x.strip() for x in args.formats.split(",") if x.strip()]):
        print(f)


if __name__ == "__main__":
    main()
