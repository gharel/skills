"""Charte Skazy Formation partagée par les scripts des skills Pro.

La charte (couleurs, catégories, photos, contact, logos, textes standard du plan, feuilles de style des
modèles) vient du design system design-skazy (github.com/gharel/design-skazy), seule source de vérité. Le
dépôt gharel/skills n'en garde aucune copie : ce module la lit dans le dépôt design-skazy du poste
($DESIGN_SKAZY, sinon un dossier design-skazy à côté du skill, du dossier courant ou de l'un de leurs
parents, ou ~/www/design-skazy), dans son export charte/ et ses logos. Sans design-skazy, il la lit dans
assets/charte, où le .zip du skill (npm run construire) embarque cet export. DESIGN_SKAZY=0 n'utilise que
ce dernier.

Ce module est le code commun : commun/charte/charte.py du dépôt gharel/skills, recopié à l'identique dans
scripts/charte.py de chaque skill pour qu'il reste autonome une fois installé. Il lit la charte et fournit
icônes Lucide, logos, stickers (Pillow), typographie française (espaces insécables), gras en ligne
(**texte**) et petits utilitaires.

Les modèles de design-skazy (templates/) ne sont lus que pour leur empreinte, comparée à celle de
l'alignement du skill (assets/charte/alignement.json, npm run modeles). Si un modèle a changé depuis, un
avertissement demande de réaligner le skill, et le rendu garde la feuille de style alignée quand le .zip
l'embarque.
"""

from __future__ import annotations

import base64
import hashlib
import html
import io
import json
import mimetypes
import os
import re
import sys
import unicodedata
import urllib.request
from functools import lru_cache
from pathlib import Path

DOSSIER_SKILL = Path(__file__).resolve().parent.parent
DOSSIER_CHARTE = DOSSIER_SKILL / "assets" / "charte"

# Export de design-skazy : chemin dans design-skazy → nom dans assets/charte du .zip.
EXPORT = {
    "charte/charte.json": "charte.json",
    "charte/plan-formation.css": "plan-formation.css",
    "charte/plan-formation.js": "plan-formation.js",
    "charte/support-formation.css": "support-formation.css",
    "assets/logo-color.png": "logo-color.png",
    "assets/logo-white.png": "logo-white.png",
}
# Feuilles propres à un modèle, et ce modèle dans design-skazy.
MODELES = {
    "plan-formation": ("templates/plan-formation/PlanFormation.dc.html", ("plan-formation.css", "plan-formation.js")),
    "support-formation": ("templates/support-formation/SupportFormation.dc.html", ("support-formation.css",)),
}


def trouver_design() -> Path | None:
    """Dépôt design-skazy du poste, ou None ($DESIGN_SKAZY=0, ou introuvable)."""
    valeur = os.environ.get("DESIGN_SKAZY", "")
    if valeur == "0":
        return None
    candidats = [Path(valeur)] if valeur else []
    for depart in (DOSSIER_SKILL, Path.cwd()):
        candidats += [d.parent / "design-skazy" for d in (depart, *depart.parents)]
    candidats += [Path.home() / "www" / "design-skazy", Path.home() / "design-skazy"]
    return next((d for d in candidats if (d / "charte" / "charte.json").is_file()), None)


def sources_charte(
    design: Path | None, dossier: Path = DOSSIER_CHARTE, skill: str = DOSSIER_SKILL.name
) -> tuple[dict[str, Path], list[str]]:
    """Fichier lu pour chaque élément de la charte, et avertissements.

    L'export de design-skazy l'emporte sur celui que le .zip embarque dans assets/charte, sauf pour la
    feuille d'un modèle changé depuis l'alignement du skill, quand le .zip l'embarque. Seul le modèle du
    skill (skazy-<modèle>) est comparé à l'alignement.
    """
    embarques = {f.name: f for f in dossier.iterdir() if f.is_file() and f.name in EXPORT.values()} if dossier.is_dir() else {}
    sources = dict(embarques)
    avertissements: list[str] = []
    if not design:
        return sources, avertissements
    alignement = dossier / "alignement.json"
    verrou = json.loads(alignement.read_text(encoding="utf-8")).get("modeles", {}) if alignement.is_file() else {}
    perimes = set()
    for modele, (gabarit, feuilles) in MODELES.items():
        if skill != "skazy-" + modele:
            continue
        chemin = design / gabarit
        empreinte = hashlib.sha256(chemin.read_bytes()).hexdigest() if chemin.is_file() else None
        if empreinte == verrou.get(modele, {}).get("empreinte"):
            continue
        alignees = all(f in embarques for f in feuilles)
        if alignees:
            perimes.update(feuilles)
        avertissements.append(
            "ATTENTION : le modèle {} a changé dans design-skazy depuis l'alignement de ce skill : rendu selon {}. "
            "Réalignez le skill (dépôt gharel/skills : npm run modeles).".format(
                modele, "la version alignée" if alignees else "sa nouvelle version, peut-être décalé du modèle"
            )
        )
    for chemin, nom in EXPORT.items():
        if nom not in perimes and (design / chemin).is_file():
            sources[nom] = design / chemin
    return sources, avertissements


DESIGN = trouver_design()
SOURCES, _avertissements = sources_charte(DESIGN)
for _message in _avertissements:
    print(_message, file=sys.stderr)


def fichier_charte(nom: str) -> Path:
    """Fichier de la charte (charte.json, feuille d'un modèle, logo) : export de design-skazy, ou celui du .zip."""
    if nom not in SOURCES:
        raise SystemExit(
            "Charte Skazy Formation introuvable ({}). Ce skill la lit dans le dépôt design-skazy : indiquez son "
            "dossier dans la variable DESIGN_SKAZY, ou installez le skill depuis son .zip "
            "(https://gharel.github.io/skills/), qui embarque la charte.".format(nom)
        )
    return SOURCES[nom]


CHARTE = json.loads(fichier_charte("charte.json").read_text(encoding="utf-8"))
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
    t = re.sub(r"\s+([;?!])", NBSP + r"\1", t)
    t = re.sub(r"«\s*", "«" + NBSP, t)
    t = re.sub(r"(?<=\d)\s+(?=\d{3}(?!\d))", NBSP, t)  # séparateur des milliers : « 1 080 », « 1 250 000 »
    t = re.sub(
        r"(\d)\s+(%|h\b|min\b|minutes?\b|€|F\b|XPF\b|jours?\b|heures?\b|semaines?\b|mois\b|ans?\b|personnes?\b"
        r"|participants?\b|px\b|pt\b|mm\b|cm\b|ms\b|dpi\b|ppp\b|Ko\b|Mo\b|Go\b)",
        r"\1" + NBSP + r"\2",
        t,
    )
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


IMAGE_LOCALE = re.compile(r"\.(png|jpe?g|gif|webp|svg)$", re.IGNORECASE)


def fichier_local(chemin: str, dossier: str | Path | None = None) -> Path | None:
    """Fichier image local : chemin absolu, ou relatif au dossier donné (celui du JSON), puis au dossier courant."""
    if not chemin or chemin.startswith(("http://", "https://", "data:")):
        return None
    candidats = [Path(chemin)]
    if dossier and not candidats[0].is_absolute():
        candidats.insert(0, Path(dossier) / chemin)
    return next((c for c in candidats if c.is_file()), None)


def url_photo(photo: str, largeur: int = 1800, dossier: str | Path | None = None) -> str:
    """Identifiant Unsplash de la banque validée (photo-…), URL complète, ou fichier local intégré en data URI."""
    if not photo:
        return ""
    if photo.startswith(("http://", "https://", "data:")):
        return photo
    fichier = fichier_local(photo, dossier)
    if fichier:
        type_mime = mimetypes.guess_type(fichier.name)[0] or "image/png"
        return "data:{};base64,{}".format(type_mime, base64.b64encode(fichier.read_bytes()).decode())
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
    """Logo du design system, tel que ses modèles l'utilisent (marges transparentes comprises)."""
    return fichier_charte(CHARTE["logos"][variante])


@lru_cache(maxsize=None)
def logo_rogne(variante: str = "couleur") -> bytes:
    """Logo sans ses marges transparentes (PNG), pour le placer au millimètre dans un DOCX ou un PPTX."""
    from PIL import Image

    image = Image.open(chemin_logo(variante)).convert("RGBA")
    return png(image.crop(image.getchannel("A").getbbox()))


@lru_cache(maxsize=None)
def logo_data_uri(variante: str = "couleur", rogne: bool = False) -> str:
    """Logo en data URI pour les rendus HTML (sans réseau)."""
    donnees = logo_rogne(variante) if rogne else chemin_logo(variante).read_bytes()
    return "data:image/png;base64," + base64.b64encode(donnees).decode()


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


# ---------------------------------------------------------------- images légères (DOCX, PPTX)


def palette_transparente(im, niveaux: int = 16, maxi: int = 8):
    """Image RGBA → palette (couleurs franches × niveaux de transparence) et sa table de transparence.

    Pour un logo ou une icône seulement (voir est_graphique) : quelques aplats lissés sur fond transparent,
    dont les couleurs franches suffisent ; les bords et l'ombre douce passent par les 16 niveaux de
    transparence. La quantification de Pillow, elle, perd une couleur rare (le vert du logo) au profit des
    pixels transparents ou de l'ombre. Une photo n'y passe jamais : elle serait réduite à quelques aplats.
    """
    from PIL import Image

    im = im.convert("RGBA")
    pal = couleurs_franches(im, maxi=maxi)
    couleurs = len(pal)
    reference = Image.new("P", (1, 1))
    reference.putpalette([v for c in pal for v in c] + [0] * 3 * (256 - couleurs))
    rgb = im.convert("RGB").quantize(palette=reference, dither=Image.Dither.NONE)
    pas = 255 / (niveaux - 1)
    indices = bytes(min(c, couleurs - 1) * niveaux + round(a / pas) for c, a in zip(rgb.tobytes(), im.getchannel("A").tobytes()))
    p = Image.frombytes("P", im.size, indices)
    p.putpalette([v for c in pal for _ in range(niveaux) for v in c])
    return p, bytes(round(n * pas) for _ in range(couleurs) for n in range(niveaux))


def est_graphique(im, maxi: int = 8, couverture: float = 0.99) -> bool:
    """Logo, icône : quelques couleurs franches couvrent tous les pixels opaques, la palette est sans perte.
    Faux pour un sticker (le contour lissé sur l'aplat se crénellerait), une photo ou une photo composée."""
    cases: dict[tuple, int] = {}
    octets = im.convert("RGBA").tobytes()
    for r, v, b, a in zip(octets[0::4], octets[1::4], octets[2::4], octets[3::4]):
        if a > 200:
            cle = (r >> 3, v >> 3, b >> 3)
            cases[cle] = cases.get(cle, 0) + 1
    opaques = sum(cases.values())
    return opaques > 0 and sum(sorted(cases.values(), reverse=True)[:maxi]) >= couverture * opaques


def couleurs_franches(im, part: float = 0.01, maxi: int = 8) -> list[tuple[int, int, int]]:
    """Couleurs des pixels opaques couvrant chacune au moins 1 % de ceux-ci (moyenne de chaque case de 5 bits
    par canal), des plus fréquentes aux plus rares, maxi au plus."""
    cases: dict[tuple, list[int]] = {}
    opaques = 0
    octets = im.convert("RGBA").tobytes()
    for r, v, b, a in zip(octets[0::4], octets[1::4], octets[2::4], octets[3::4]):
        if a > 200:
            opaques += 1
            c = cases.setdefault((r >> 3, v >> 3, b >> 3), [0, 0, 0, 0])
            c[0] += 1
            c[1] += r
            c[2] += v
            c[3] += b
    retenues = sorted((c for c in cases.values() if c[0] >= part * max(1, opaques)), reverse=True)[:maxi]
    return [(round(r / n), round(v / n), round(b / n)) for n, r, v, b in retenues] or [(255, 255, 255)]


# ---------------------------------------------------------------- images distantes


def telecharger(url: str, delai: float = 10) -> bytes | None:
    """Télécharge une image ; None sans accès réseau (le rendu met alors un emplacement vide)."""
    if not url:
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
