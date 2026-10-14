"""Accès aux scripts des skills Pro (chaque skill garde sa copie identique de charte.py)."""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SKILLS = RACINE / "skills" / "pro"
for skill in ("skazy-plan-formation", "skazy-support-formation", "skazy-quiz"):
    sys.path.insert(0, str(SKILLS / skill / "scripts"))
