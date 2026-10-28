"""Charte Skazy Formation partagée par les scripts des skills Pro.

Source unique : commun/charte/charte.py du dépôt gharel/skills. Chaque skill Pro en garde une
copie identique dans scripts/charte.py (npm run synchroniser) pour rester autonome une fois installé.

Contenu : catégories et couleurs, niveaux, logos, icônes Lucide, stickers (Pillow),
typographie française (espaces insécables), gras en ligne (**texte**) et petits utilitaires.
"""

from __future__ import annotations

import base64
import html
import io
import json
import re
import sys
import unicodedata
import urllib.request
from functools import lru_cache
from pathlib import Path

DOSSIER_SKILL = Path(__file__).resolve().parent.parent
DOSSIER_CHARTE = DOSSIER_SKILL / "assets" / "charte"
CHARTE = json.loads((DOSSIER_CHARTE / "charte.json").read_text(encoding="utf-8"))
COULEURS = CHARTE["couleurs"]
CONTACT = CHARTE["contact"]
NIVEAUX = CHARTE["niveaux"]
URL_LUCIDE = "https://unpkg.com/lucide-static@{}/icons/".format(CHARTE["lucide"])
NBSP = " "
NNBSP = " "


# ---------------------------------------------------------------- dépendances


def exiger(*modules: str) -> None:
    """Arrête le script avec la commande d'installation si un module Python manque."""
    paquets = {"docx": "python-docx", "pptx": "python-pptx", "openpyxl": "openpyxl", "PIL": "pillow"}
    manquants = []
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            manquants.append(paquets.get(module, module))
    if manquants:
        print(
            "Modules Python manquants : {}.\nInstallez-les avec : pip install {}".format(
                ", ".join(manquants), " ".join(manquants)
            ),
            file=sys.stderr,
        )
        sys.exit(2)


# ---------------------------------------------------------------- texte


def normaliser(texte: str) -> str:
    """Minuscules, sans accents ni ponctuation superflue : sert aux correspondances souples."""
    texte = unicodedata.normalize("NFKD", str(texte)).encode("ascii", "ignore").decode()
    texte = texte.lower().replace("&", " et ")
    return re.sub(r"[^a-z0-9]+", " ", texte).strip()


def slug(texte: str, longueur: int = 60) -> str:
    """Nom de fichier lisible : « Excel : les bases » → « excel-les-bases »."""
    return normaliser(texte).replace(" ", "-")[:longueur].strip("-") or "document"


def typographie(texte: str) -> str:
    """Espaces insécables de la typographie française (avant : ; ? ! », après «, entre nombre et unité)."""
    if not texte:
        return ""
    t = str(texte)
    t = re.sub(r"\s+([:»])", NBSP + r"\1", t)
    t = re.sub(r"\s+([;?!])", NNBSP + r"\1", t)
    t = re.sub(r"«\s*", "«" + NBSP, t)
    t = re.sub(r"(\d)\s+(%|h\b|min\b|€|F\b|XPF\b|jours?\b|heures?\b|ans?\b|personnes?\b)", r"\1" + NBSP + r"\2", t)
    t = re.sub(r"\s·\s", NBSP + "· ", t)
    return t


def segments_gras(texte: str) -> list[tuple[str, bool]]:
    """Découpe « du **gras** ici » en [(« du », False), (« gras », True), (« ici », False)]."""
    morceaux = re.split(r"\*\*(.+?)\*\*", typographie(texte or ""))
    return [(m, i % 2 == 1) for i, m in enumerate(morceaux) if m]


def html_gras(texte: str, style_gras: str = "") -> str:
    """Texte échappé pour le HTML, avec **gras** → <strong>."""
    attribut = ' style="{}"'.format(style_gras) if style_gras else ""
    return "".join(
        "<strong{}>{}</strong>".format(attribut, html.escape(m)) if g else html.escape(m)
        for m, g in segments_gras(texte)
    )


def sans_gras(texte: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", texte or "")


def esc(texte) -> str:
    return html.escape(typographie(str(texte if texte is not None else "")))


# ---------------------------------------------------------------- catégories et niveaux


def categorie(nom: str | None) -> dict:
    """Retrouve une catégorie par son nom, son slug, son identifiant Quiz ou un alias."""
    cible = normaliser(nom or "")
    for c in CHARTE["categories"]:
        candidats = [c["nom"], c["slug"], c["quiz"], *c.get("alias", [])]
        if cible in {normaliser(x) for x in candidats}:
            return c
    noms = ", ".join(c["nom"] for c in CHARTE["categories"])
    raise ValueError("Catégorie inconnue : « {} ». Catégories possibles : {}.".format(nom, noms))


def niveau(nom: str | None) -> str:
    cible = normaliser(nom or "initiation")
    synonymes = {
        "initiation": "Initiation",
        "debutant": "Initiation",
        "decouverte": "Initiation",
        "intermediaire": "Intermédiaire",
        "perfectionnement": "Intermédiaire",
        "avance": "Avancé",
        "avancee": "Avancé",
        "expert": "Avancé",
    }
    if cible in synonymes:
        return synonymes[cible]
    raise ValueError("Niveau inconnu : « {} ». Niveaux possibles : {}.".format(nom, ", ".join(NIVEAUX)))


def variante_logo(cat: dict) -> str:
    """Logo blanc sur les couleurs à texte blanc, logo couleur sur Data et Gestion de projet."""
    return "blanc" if cat["surCouleur"].upper() == "#FFFFFF" else "couleur"


def url_photo(photo: str, largeur: int = 1800) -> str:
    """Identifiant Unsplash de la banque validée (photo-…) ou URL complète."""
    if not photo:
        return ""
    if photo.startswith(("http://", "https://", "data:")):
        return photo
    return "https://images.unsplash.com/{}?w={}&q=75&auto=format&fit=crop".format(photo, largeur)


# ---------------------------------------------------------------- couleurs


def rgb(couleur: str) -> tuple[int, int, int]:
    c = couleur.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def melange(couleur: str, fond: str, part: float) -> str:
    """Mélange part de couleur avec (1 - part) de fond, en hexadécimal (remplace color-mix)."""
    a, b = rgb(couleur), rgb(fond)
    return "#{:02X}{:02X}{:02X}".format(*(round(x * part + y * (1 - part)) for x, y in zip(a, b)))


# ---------------------------------------------------------------- fichiers de la charte


def chemin_logo(variante: str = "couleur") -> Path:
    return DOSSIER_CHARTE / "logo-{}.png".format(variante)


@lru_cache(maxsize=None)
def logo_svg_data_uri(variante: str = "couleur") -> str:
    svg = (DOSSIER_CHARTE / "logo-{}.svg".format(variante)).read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode()


@lru_cache(maxsize=None)
def icone_data_uri(nom: str) -> str:
    """Icône Lucide en data URI (pour les masques CSS) ; repli sur unpkg si elle n'est pas embarquée."""
    chemin = DOSSIER_CHARTE / "icones" / "{}.svg".format(nom)
    if not chemin.exists():
        return URL_LUCIDE + nom + ".svg"
    return "data:image/svg+xml;base64," + base64.b64encode(chemin.read_bytes()).decode()


def icone_image(nom: str, couleur: str = "#1F1F24", taille: int = 256):
    """Icône Lucide recolorée (image Pillow RGBA)."""
    from PIL import Image

    chemin = DOSSIER_CHARTE / "icones" / "{}.png".format(nom)
    if not chemin.exists():
        chemin = DOSSIER_CHARTE / "icones" / "image.png"
    source = Image.open(chemin).convert("RGBA")
    if source.size != (taille, taille):
        source = source.resize((taille, taille), Image.LANCZOS)
    couleur_pleine = Image.new("RGBA", source.size, rgb(couleur) + (255,))
    couleur_pleine.putalpha(source.getchannel("A"))
    return couleur_pleine


def png(image) -> bytes:
    tampon = io.BytesIO()
    image.save(tampon, format="PNG")
    return tampon.getvalue()


def sticker_image(fond: str, icone: str, taille: int = 300, rotation: float = 8, ombre: bool = True):
    """Sticker du design system : pastille carrée arrondie, liseré blanc, aplat cerné de noir,
    icône Lucide au centre, légère rotation. Renvoie une image Pillow RGBA (fond transparent)."""
    from PIL import Image, ImageDraw, ImageFilter

    echelle = 4
    s = taille * echelle
    marge = int(s * 0.18)
    toile = Image.new("RGBA", (s + 2 * marge, s + 2 * marge), (0, 0, 0, 0))
    pastille = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(pastille)
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.28), fill=(255, 255, 255, 255))
    p = int(s * 0.073)
    trait = max(2, int(s * 0.033))
    d.rounded_rectangle(
        (p, p, s - 1 - p, s - 1 - p),
        radius=int(s * 0.22),
        fill=rgb(fond) + (255,),
        outline=rgb(COULEURS["texte"]) + (255,),
        width=trait,
    )
    ic = int((s - 2 * p) * 0.48)
    pastille.alpha_composite(icone_image(icone, COULEURS["texte"], ic), ((s - ic) // 2, (s - ic) // 2))
    if ombre:
        masque = Image.new("RGBA", toile.size, (0, 0, 0, 0))
        ImageDraw.Draw(masque).rounded_rectangle(
            (marge, marge + int(s * 0.05), marge + s, marge + s + int(s * 0.05)),
            radius=int(s * 0.28),
            fill=(0, 0, 0, 46),
        )
        toile.alpha_composite(masque.filter(ImageFilter.GaussianBlur(s * 0.06)))
    toile.alpha_composite(pastille, (marge, marge))
    toile = toile.rotate(-rotation, resample=Image.BICUBIC, expand=True)
    largeur = toile.width // echelle
    return toile.resize((largeur, toile.height * largeur // toile.width), Image.LANCZOS)


def sticker_png(fond: str, icone: str, taille: int = 300, rotation: float = 8) -> bytes:
    return png(sticker_image(fond, icone, taille, rotation))


# ---------------------------------------------------------------- images distantes


# Images déjà téléchargées par l'hôte (l'atelier dans le navigateur n'a pas d'accès réseau direct).
IMAGES_LOCALES: dict[str, bytes] = {}


def telecharger(url: str, delai: float = 10) -> bytes | None:
    """Télécharge une image ; None sans accès réseau (le rendu met alors un emplacement vide)."""
    if not url:
        return None
    if url in IMAGES_LOCALES:
        return IMAGES_LOCALES[url]
    if sys.platform == "emscripten":
        return None
    if url.startswith("data:"):
        try:
            return base64.b64decode(url.split(",", 1)[1])
        except Exception:
            return None
    chemin = Path(url)
    if not url.startswith(("http://", "https://")) and chemin.exists():
        return chemin.read_bytes()
    try:
        requete = urllib.request.Request(url, headers={"User-Agent": "skazy-skills/1.0"})
        with urllib.request.urlopen(requete, timeout=delai) as reponse:
            return reponse.read()
    except Exception:
        return None


def image_recadree(donnees: bytes, largeur: int, hauteur: int, saturation: float = 1.0):
    """Recadre une image en mode « cover » aux proportions demandées (image Pillow RGB)."""
    from PIL import Image, ImageEnhance

    image = Image.open(io.BytesIO(donnees)).convert("RGB")
    ratio = largeur / hauteur
    if image.width / image.height > ratio:
        nouvelle = int(image.height * ratio)
        gauche = (image.width - nouvelle) // 2
        image = image.crop((gauche, 0, gauche + nouvelle, image.height))
    else:
        nouvelle = int(image.width / ratio)
        haut = (image.height - nouvelle) // 2
        image = image.crop((0, haut, image.width, haut + nouvelle))
    if saturation != 1.0:
        image = ImageEnhance.Color(image).enhance(saturation)
    return image


# ---------------------------------------------------------------- JSON


def lire_json(chemin: str | Path) -> dict:
    texte = Path(chemin).read_text(encoding="utf-8-sig")
    try:
        return json.loads(texte)
    except json.JSONDecodeError as erreur:
        raise SystemExit("JSON invalide dans {} : {} (ligne {}, colonne {}).".format(chemin, erreur.msg, erreur.lineno, erreur.colno))


class Rapport:
    """Erreurs bloquantes et avertissements d'un contrôle de contenu."""

    def __init__(self) -> None:
        self.erreurs: list[str] = []
        self.avertissements: list[str] = []

    def erreur(self, message: str) -> None:
        self.erreurs.append(message)

    def avertir(self, message: str) -> None:
        self.avertissements.append(message)

    def afficher(self) -> None:
        for m in self.erreurs:
            print("ERREUR : " + m, file=sys.stderr)
        for m in self.avertissements:
            print("ATTENTION : " + m, file=sys.stderr)

    @property
    def ok(self) -> bool:
        return not self.erreurs
