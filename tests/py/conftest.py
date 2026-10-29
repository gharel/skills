"""Accès aux scripts des skills (chaque skill garde sa copie identique de charte.py)."""

import os
import sys
from pathlib import Path

# Les rendus testés suivent la copie de la charte du dépôt, jamais le design-skazy du poste.
os.environ["DESIGN_SKAZY"] = "0"

RACINE = Path(__file__).resolve().parents[2]
SKILLS = RACINE / "skills" / "pro"
UNC = RACINE / "skills" / "unc"
for dossier in (
    UNC / "notation-etudiants",
    SKILLS / "skazy-quiz",
    SKILLS / "skazy-support-formation",
    SKILLS / "skazy-plan-formation",
):
    sys.path.insert(0, str(dossier / "scripts"))

# Le module charte est importé une fois pour toutes, depuis un skill qui a la charte complète (logos,
# icônes) : sinon, le premier script importé (rendre_quiz, rendre_notation…) imposerait sa copie réduite.
import charte  # noqa: E402, F401
