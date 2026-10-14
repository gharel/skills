"""python outils/planche_png.py dossier sortie.png première dernière [colonnes]
Planche-contact d'images de slides (contrôle visuel des exports PowerPoint)."""
import sys
from pathlib import Path
from PIL import Image

dossier, sortie, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
colonnes = int(sys.argv[5]) if len(sys.argv) > 5 else 3
images = sorted(Path(dossier).glob("*.png"))[a - 1 : b]
w, h, m = 600, 338, 12
rangs = (len(images) + colonnes - 1) // colonnes
planche = Image.new("RGB", (colonnes * (w + m) + m, rangs * (h + m) + m), (110, 110, 110))
for k, f in enumerate(images):
    img = Image.open(f).convert("RGB").resize((w, h), Image.LANCZOS)
    planche.paste(img, (m + (k % colonnes) * (w + m), m + (k // colonnes) * (h + m)))
planche.save(sortie)
print(sortie)
