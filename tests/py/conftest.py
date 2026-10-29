"""Accès aux scripts des skills (chaque skill garde sa copie identique de charte.py)."""

import sys
from pathlib import Path

# La charte se lit dans le dépôt design-skazy du poste ($DESIGN_SKAZY, sinon ../design-skazy) : ce dépôt n'en
# garde aucune copie.
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

# Le module charte est importé une fois pour toutes, depuis un skill qui a la charte complète (icônes,
# alignement du modèle) : sinon, le premier script importé (rendre_quiz, rendre_notation…) imposerait la sienne.
import charte  # noqa: E402, F401
