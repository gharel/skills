"""Support de formation : rendu PPTX (PowerPoint, Google Slides, Keynote).

Reprend les coordonnées du modèle HTML 1920 × 1080 (1 px = 6 350 EMU = 0,5 pt). Les éléments que
Google Slides importe mal (rotations groupées, ombres, dégradés) sont composés en images avec Pillow.
Chaque slide reçoit les notes formateur du JSON.
"""

from __future__ import annotations

import io
import math
import re

import charte as ch
from support_modele import touches

ch.exiger("pptx", "PIL")

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.dml import MSO_LINE_DASH_STYLE  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.util import Emu, Pt  # noqa: E402

PX = 6350
W, H = 1920, 1080
BAS = 1000  # haut du pied de slide
POLICE = ch.CHARTE["police"]
MONO = "Consolas"
C = ch.COULEURS
GAUCHE, CENTRE, DROITE = PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.RIGHT
HAUT, MILIEU, BAS_ = MSO_ANCHOR.TOP, MSO_ANCHOR.MIDDLE, MSO_ANCHOR.BOTTOM


def e(px: float) -> Emu:
    return Emu(int(round(px * PX)))


def couleur(h: str) -> RGBColor:
    return RGBColor(*ch.rgb(h))


# ---------------------------------------------------------------- mesure du texte


def largeur_car(taille: float, gras=False, mono=False) -> float:
    """Largeur moyenne d'un caractère de Raleway, pour estimer les retours à la ligne."""
    return taille * (0.6 if mono else (0.57 if gras else 0.52))


def nb_lignes(texte: str, largeur: float, taille: float, gras=False, mono=False) -> int:
    total = 0
    par_ligne = max(1, int(largeur / largeur_car(taille, gras, mono)))
    for ligne in ch.sans_gras(texte or "").split("\n"):
        mots, n, courant = ligne.split(" "), 1, 0
        for mot in mots:
            if courant and courant + 1 + len(mot) > par_ligne:
                n += 1
                courant = len(mot)
            else:
                courant += (1 if courant else 0) + len(mot)
        total += n
    return max(1, total)


def hauteur(texte: str, largeur: float, taille: float, interligne=1.2, gras=False, mono=False) -> float:
    return nb_lignes(texte, largeur, taille, gras, mono) * taille * interligne


def largeur_texte(texte: str, taille: float, gras=False) -> float:
    """Largeur prudente d'un texte sur une ligne (pastilles, étiquettes) : mieux vaut trop large que coupé."""
    return len(ch.sans_gras(texte or "")) * taille * (0.62 if gras else 0.55)


# ---------------------------------------------------------------- formes de base


class Slide:
    """Enveloppe d'une slide python-pptx avec des primitives en pixels du modèle."""

    def __init__(self, deck: "Deck", fond: str = "#FFFFFF") -> None:
        self.deck = deck
        self.s = deck.prs.slides.add_slide(deck.prs.slide_layouts[6])
        if fond.upper() != "#FFFFFF":
            self.rect(0, 0, W, H, fond)

    # -- formes
    def rect(self, x, y, w, h, fond=None, rayon=0, trait=None, epaisseur=2, tirets=False, alpha=None):
        forme = MSO_SHAPE.ROUNDED_RECTANGLE if rayon else MSO_SHAPE.RECTANGLE
        sh = self.s.shapes.add_shape(forme, e(x), e(y), e(w), e(h))
        if rayon:
            sh.adjustments[0] = min(0.5, rayon / max(1, min(w, h)))
        if fond:
            sh.fill.solid()
            sh.fill.fore_color.rgb = couleur(fond)
            if alpha is not None:
                srgb = sh.fill._xPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
                a = srgb.makeelement(qn("a:alpha"), {"val": str(int(alpha * 100000))})
                srgb.append(a)
        else:
            sh.fill.background()
        if trait:
            sh.line.color.rgb = couleur(trait)
            sh.line.width = e(epaisseur)
            if tirets:
                sh.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        sh.text_frame.text = ""
        return sh

    def rond(self, x, y, d, fond, trait=None, epaisseur=2):
        sh = self.s.shapes.add_shape(MSO_SHAPE.OVAL, e(x), e(y), e(d), e(d))
        sh.fill.solid()
        sh.fill.fore_color.rgb = couleur(fond)
        if trait:
            sh.line.color.rgb = couleur(trait)
            sh.line.width = e(epaisseur)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    def polygone(self, points, fond, alpha=None):
        constructeur = self.s.shapes.build_freeform(e(points[0][0]), e(points[0][1]), scale=1.0)
        constructeur.add_line_segments([(e(x), e(y)) for x, y in points[1:]], close=True)
        sh = constructeur.convert_to_shape()
        sh.fill.solid()
        sh.fill.fore_color.rgb = couleur(fond)
        if alpha is not None:
            srgb = sh.fill._xPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
            srgb.append(srgb.makeelement(qn("a:alpha"), {"val": str(int(alpha * 100000))}))
        sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    def ligne(self, x, y, w, h, fond):
        return self.rect(x, y, w, max(h, 1), fond)

    # -- texte
    def texte(self, x, y, w, h, contenu, taille, coul=None, gras=False, italique=False, align=GAUCHE, ancre=HAUT,
              interligne=1.2, gras_coul=None, majuscules=False, espacement=0.0, police=None, lien=None, forme=None):
        coul = coul or C["texte"]
        cible = forme if forme is not None else self.s.shapes.add_textbox(e(x), e(y), e(w), e(h))
        tf = cible.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = ancre
        lignes = str(contenu if contenu is not None else "").split("\n")
        for k, ligne in enumerate(lignes):
            p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            p.alignment = align
            # line-height CSS → interligne PowerPoint (hauteur d'une ligne simple de Raleway ≈ 1,17 em).
            p.line_spacing = round(interligne / 1.17, 3)
            segments = ch.segments_gras(ligne) or [("", False)]
            for segment, est_gras in segments:
                r = p.add_run()
                r.text = segment
                f = r.font
                f.name = police or POLICE
                f.size = Pt(taille / 2)
                f.bold = gras or est_gras
                f.italic = italique
                f.color.rgb = couleur(gras_coul if (est_gras and gras_coul) else coul)
                rpr = r._r.get_or_add_rPr()
                if majuscules:
                    rpr.set("cap", "all")
                if espacement:
                    rpr.set("spc", str(int(espacement * taille / 2 * 100)))
        if lien:
            # Lien porté par la forme : la couleur du texte reste celle de la charte.
            cible.click_action.hyperlink.address = lien
        return cible

    def pile(self, x, y, w, elements, ecart=0):
        """Empile des textes : [(contenu, taille, options)] ; renvoie le y de fin."""
        for contenu, taille, opts in elements:
            if not contenu:
                continue
            inter = opts.get("interligne", 1.2)
            h = hauteur(contenu, w, taille, inter, opts.get("gras", False), opts.get("police") == MONO)
            self.texte(x, y, w, h + 4, contenu, taille, **opts)
            y += h + ecart
        return y - ecart

    def pastille(self, x, y, texte, taille=24, fond=None, coul=None, pad_x=28, pad_y=10, majuscules=True, droite=False):
        fond = fond or self.deck.c["couleur"]
        coul = coul or self.deck.c["surCouleur"]
        lt = largeur_texte(texte, taille, True) * (1.18 if majuscules else 1.0)
        w, h = lt + 2 * pad_x, taille * 1.25 + 2 * pad_y
        if droite:
            x -= w
        sh = self.rect(x, y, w, h, fond, rayon=h / 2)
        self.texte(x, y, w, h, texte, taille, coul, gras=True, align=CENTRE, ancre=MILIEU, majuscules=majuscules,
                   espacement=0.12 if majuscules else 0, forme=sh)
        return w, h

    def numero(self, x, y, d, n, taille, fond=None, coul=None):
        sh = self.rond(x, y, d, fond or self.deck.c["couleur"])
        self.texte(x, y, d, d, str(n), taille, coul or self.deck.c["surCouleur"], gras=True, align=CENTRE, ancre=MILIEU, forme=sh)

    # -- images
    def image(self, donnees: bytes, x, y, w, h):
        return self.s.shapes.add_picture(io.BytesIO(donnees), e(x), e(y), e(w), e(h))

    def photo(self, url, x, y, w, h, libelle="Photo", position="center", saturation=1.2):
        donnees = self.deck.telecharger(url)
        if not donnees:
            return self.vide(x, y, w, h, libelle, rayon=0, fond=C["photoVide"])
        try:
            img = ch.image_recadree(donnees, int(w), int(h), saturation)
        except Exception:
            return self.vide(x, y, w, h, libelle, rayon=0, fond=C["photoVide"])
        if position == "right":
            pass
        return self.image(jpeg(img, max(1, int(w * 1.25))), x, y, w, h)

    def visuel(self, url, x, y, w, h, libelle, rayon=16):
        """Capture ou schéma ajusté (contain) ; emplacement vide à remplacer sinon."""
        donnees = self.deck.telecharger(url) if url else None
        if not donnees:
            return self.vide(x, y, w, h, libelle, rayon)
        try:
            img = Image.open(io.BytesIO(donnees)).convert("RGB")
        except Exception:
            return self.vide(x, y, w, h, libelle, rayon)
        ratio = min(w / img.width, h / img.height)
        iw, ih = img.width * ratio, img.height * ratio
        return self.image(jpeg(img, int(iw * 1.25)), x + (w - iw) / 2, y + (h - ih) / 2, iw, ih)

    def vide(self, x, y, w, h, libelle, rayon=16, fond=None):
        self.rect(x, y, w, h, fond or C["fondCarte"], rayon=rayon, trait=C["barreGrise"], epaisseur=3, tirets=True)
        ic = min(56, h / 4)
        self.image(ch.png(ch.icone_image("image", "#B5B5BD", 128)), x + (w - ic) / 2, y + h / 2 - ic - 4, ic, ic)
        self.texte(x + 12, y + h / 2 + 8, w - 24, 40, libelle, 22 if w > 200 else 18, C["grisClair"], gras=True, align=CENTRE)

    def icone(self, nom, x, y, taille, coul="#1F1F24"):
        self.image(ch.png(ch.icone_image(nom, coul, 256)), x, y, taille, taille)

    def sticker(self, x, y, taille, rotation, icone=None):
        if not self.deck.f["stickers"]:
            return
        c = self.deck.c
        img = ch.sticker_image(c["sticker"], icone or c["icone"], taille=taille * 2, rotation=rotation)
        w, h = img.width / 2, img.height / 2
        self.image(ch.png(img), x + taille / 2 - w / 2, y + taille / 2 - h / 2, w, h)

    # -- pied et notes
    def pied(self, couleur_cat=False):
        c, f = self.deck.c, self.deck.f
        n = "{:02d}".format(len(self.deck.prs.slides))
        if couleur_cat:
            self.rect(0, BAS, W, 80, c["couleur"])
            coul, gras = c["surCouleur"], True
            logo = self.deck.logo("blanc" if c["surCouleur"].upper() == "#FFFFFF" else "noir")
        else:
            self.rect(0, BAS, W, 80, C["fondGris"])
            coul, gras = C["texte4"], True
            logo = self.deck.logo("couleur")
        self.texte(64, BAS, 760, 80, f["intitule"], 24, coul, gras=gras, ancre=MILIEU)
        lw = 64 * 218 / 72
        self.image(logo, (W - lw) / 2, BAS + 8, lw, 64)
        self.texte(W - 64 - 200, BAS, 200, 80, n, 24, coul if couleur_cat else C["texte"], gras=True, align=DROITE, ancre=MILIEU)

    def notes(self, texte):
        if isinstance(texte, list):
            texte = "\n".join(texte)
        if texte:
            self.s.notes_slide.notes_text_frame.text = ch.typographie(ch.sans_gras(texte))


def url_image(url: str) -> str:
    """URL réellement téléchargée (photos Unsplash en 1600 px, suffisant pour une demi-slide)."""
    return re.sub(r"([?&])w=\d+", r"\1w=1600", url)


def urls_images(s: dict) -> list[str]:
    """Toutes les images distantes du support (préchargées par l'atelier dans le navigateur)."""
    urls = [s["formation"]["_couverture"]]
    for slide in s["_slides"]:
        for cle in ("photo", "image", "qrCode"):
            if isinstance(slide.get(cle), str):
                urls.append(slide[cle])
        for cle in ("avant", "apres"):
            if isinstance(slide.get(cle), dict) and slide[cle].get("image"):
                urls.append(slide[cle]["image"])
        for etape in slide.get("etapes") or []:
            if isinstance(etape, dict) and etape.get("image"):
                urls.append(etape["image"])
        if slide["type"] == "questions":
            urls.append(ch.url_photo(slide.get("photo") or ch.CHARTE["photoQuestions"]))
    return sorted({url_image(u) for u in urls if u and u.startswith("https://")})


def jpeg(img: Image.Image, largeur_max: int) -> bytes:
    if img.width > largeur_max:
        img = img.resize((largeur_max, int(img.height * largeur_max / img.width)), Image.LANCZOS)
    tampon = io.BytesIO()
    img.convert("RGB").save(tampon, format="JPEG", quality=82, optimize=True)
    return tampon.getvalue()


class Deck:
    def __init__(self, s: dict) -> None:
        self.s = s
        self.f = s["formation"]
        self.c = self.f["_cat"]
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = e(W), e(H)
        self.prs.core_properties.title = self.f["intitule"]
        self.prs.core_properties.author = self.f["formateur"]
        self._cache: dict[str, bytes | None] = {}
        self._logos: dict[str, bytes] = {}

    def telecharger(self, url):
        if not url:
            return None
        if url not in self._cache:
            self._cache[url] = ch.telecharger(url_image(url))
        return self._cache[url]

    def logo(self, variante: str) -> bytes:
        if variante not in self._logos:
            if variante == "noir":
                img = Image.open(ch.chemin_logo("blanc")).convert("RGBA")
                noir = Image.new("RGBA", img.size, (0, 0, 0, 255))
                noir.putalpha(img.getchannel("A"))
                self._logos[variante] = ch.png(noir)
            else:
                self._logos[variante] = ch.chemin_logo(variante).read_bytes()
        return self._logos[variante]


# ---------------------------------------------------------------- éléments composés


def titre(sl: Slide, x, y, w, texte, taille=72, coul=None):
    h = hauteur(texte, w, taille, 1.08, True)
    sl.texte(x, y, w, h + 6, texte, taille, coul or C["texte"], gras=True, interligne=1.0)
    return y + h


def puces(sl: Slide, x, y, w, items, taille, ecart, coul=C["texte3"], interligne=1.4):
    for item in items:
        t = formater_point(item)
        h = hauteur(t, w - 32, taille, interligne)
        sl.rect(x, y + taille * interligne / 2 - 6, 12, 12, sl.deck.c["couleur"], rayon=2)
        sl.texte(x + 32, y, w - 32, h + 4, t, taille, coul, interligne=interligne, gras_coul=C["texte"])
        y += h + ecart
    return y - ecart


def formater_point(p) -> str:
    if isinstance(p, dict):
        return "**{}** : {}".format(p.get("label"), p.get("texte", "")) if p.get("label") else p.get("texte", "")
    return p or ""


def hauteur_puces(items, w, taille, ecart, interligne=1.4):
    return sum(hauteur(formater_point(i), w - 32, taille, interligne) for i in items) + ecart * max(0, len(items) - 1)


def polaroid(url_donnees: bytes | None, largeur=440, hauteur_=380, rotation=-4) -> Image.Image:
    """Photo façon polaroïd (cadre blanc, ombre, rotation), composée en une image."""
    k = 2
    w, h = largeur * k, hauteur_ * k
    marge = 60 * k
    toile = Image.new("RGBA", (w + 2 * marge, h + 2 * marge), (0, 0, 0, 0))
    ombre = Image.new("RGBA", toile.size, (0, 0, 0, 0))
    ImageDraw.Draw(ombre).rectangle((marge, marge + 16 * k, marge + w, marge + h + 16 * k), fill=(0, 0, 0, 40))
    toile.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(20 * k)))
    carte = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    pw, ph = w - 36 * k, h - (18 + 56) * k
    if url_donnees:
        try:
            carte.paste(ch.image_recadree(url_donnees, pw, ph, 1.2).resize((pw, ph)), (18 * k, 18 * k))
        except Exception:
            ImageDraw.Draw(carte).rectangle((18 * k, 18 * k, 18 * k + pw, 18 * k + ph), fill=ch.rgb(C["photoVide"]))
    else:
        ImageDraw.Draw(carte).rectangle((18 * k, 18 * k, 18 * k + pw, 18 * k + ph), fill=ch.rgb(C["photoVide"]))
    toile.alpha_composite(carte, (marge, marge))
    return toile.rotate(-rotation, resample=Image.BICUBIC, expand=True)


# ---------------------------------------------------------------- mises en page


def couverture(sl: Slide, s):
    d, f, c = sl.deck, sl.deck.f, sl.deck.c
    sl.photo(s.get("photo") or f["_couverture"], 0, 0, 960, H)
    sl.rect(960, 0, 960, H, c["couleur"])
    sl.image(d.logo(ch.variante_logo(c)), 1080, 110, 322, 106)
    co = c["surCouleur"]
    taille = 104 if len(f["intitule"]) <= 30 else 84
    h_titre = hauteur(f["intitule"], 720, taille, 1.0, True)
    bloc = h_titre + 32 + 53 + 32 + 34
    y = (216 + 900) / 2 - bloc / 2
    sl.texte(1080, y, 720, h_titre + 8, f["intitule"], taille, co, gras=True, interligne=0.95)
    y += h_titre + 32
    w, _ = sl.pastille(1080, y, f["categorie"], 24, "#FFFFFF", c["encre"], pad_x=30, pad_y=12, majuscules=False)
    sl.pastille(1080 + w + 14, y, f["niveau"], 24, "#FFFFFF", c["encre"], pad_x=30, pad_y=12, majuscules=False)
    y += 53 + 32
    sl.texte(1080, y, 720, 40, f["duree"], 28, co)
    sl.texte(1080, 900, 720, 42, f["formateur"], 28, co, gras=True)
    sl.texte(1080, 940, 720, 42, f["email"], 28, co)


def faisons_connaissance(sl: Slide, s):
    d, f, c = sl.deck, sl.deck.f, sl.deck.c
    # Colonne gauche, centrée verticalement.
    infos = s.get("infos") or []
    h_titre = hauteur(s.get("titre") or "Faisons connaissance", 640, 72, 1.05, True)
    h_infos = hauteur_puces(infos, 640, 28, 18) if infos else 0
    bloc = h_titre + 40 + 200 + (40 + h_infos if infos else 0)
    y = (96 + 928) / 2 - bloc / 2
    y = titre(sl, 120, y, 640, s.get("titre") or "Faisons connaissance") + 40
    if s.get("photo") and d.telecharger(s["photo"]):
        img = ch.image_recadree(d.telecharger(s["photo"]), 400, 400)
        masque = Image.new("L", (400, 400), 0)
        ImageDraw.Draw(masque).ellipse((0, 0, 399, 399), fill=255)
        rond = img.convert("RGBA")
        rond.putalpha(masque)
        sl.image(ch.png(rond), 120, y, 200, 200)
    else:
        sl.rond(120, y, 200, c["teinte"])
        sl.icone("user-round", 172, y + 52, 96, c["encre"])
    sl.texte(352, y + 50, 420, 50, f["formateur"], 38, gras=True)
    sl.texte(352, y + 104, 420, 40, f["role"], 26, C["texte4"])
    y += 240
    if infos:
        puces(sl, 120, y, 640, infos, 28, 18)
    # Panneau « Tour de table ».
    sl.rect(856, 96, 944, 832, c["teinte"], rayon=32)
    tour = s["tourDeTable"]
    hauteurs = [max(64, hauteur(t, 944 - 144 - 92, 36, 1.2)) for t in tour]
    bloc = 30 + 36 + sum(hauteurs) + 36 * (len(tour) - 1)
    y = 96 + 832 / 2 - bloc / 2
    sl.texte(928, y, 800, 32, "Tour de table", 24, c["encre"], gras=True, majuscules=True, espacement=0.14)
    y += 30 + 36
    for k, (t, h) in enumerate(zip(tour, hauteurs), 1):
        sl.numero(928, y + (h - 64) / 2, 64, k, 28)
        sl.texte(1020, y, 944 - 144 - 92, h, t, 36, ancre=MILIEU)
        y += h + 36
    sl.sticker(1680, 70, 150, 8, "hand")


def objectifs(sl: Slide, s):
    sl.photo(s.get("photo"), 1160, 0, 760, BAS)
    y = titre(sl, 120, 96, 944, s.get("titre") or "Objectifs pédagogiques")
    sl.texte(120, y + 20, 944, 44, s.get("intro") or "À la fin de la formation, vous serez capable de :", 30, C["texte4"])
    taille = 34 if len(s["objectifs"]) <= 4 else 30
    hauteurs = [hauteur(o, 868, taille, 1.4) for o in s["objectifs"]]
    y = 920 - sum(hauteurs) - 34 * (len(hauteurs) - 1)
    for k, (o, h) in enumerate(zip(s["objectifs"], hauteurs), 1):
        sl.texte(120, y + (taille - 28) * 0.9, 60, 40, "{:02d}".format(k), 28, sl.deck.c["encre"], gras=True)
        sl.texte(196, y, 868, h + 4, o, taille, C["texte3"], interligne=1.4, gras_coul=C["texte"])
        y += h + 34
    sl.sticker(1075, 150, 170, -10, "target")


def programme(sl: Slide, s):
    d, f, c = sl.deck, sl.deck.f, sl.deck.c
    y = titre(sl, 120, 96, 620, s.get("titre") or "Programme")
    sl.texte(120, y + 16, 620, 44, s.get("duree") or f["duree"], 30, C["texte4"])
    img = polaroid(d.telecharger(s.get("photo")))
    w, h = img.width / 2, img.height / 2
    sl.image(ch.png(img), 400 - w / 2, 600 - h / 2, w, h)
    sl.sticker(530, 690, 140, 10)
    sl.rect(820, 0, 1100, BAS, c["couleur"])
    parties = s["parties"]
    pad = 20 if len(parties) <= 8 else 14
    taille = 32 if len(parties) <= 8 else 28
    hauteurs = [hauteur(p["titre"] if isinstance(p, dict) else p, 640, taille, 1.2, True) + 2 * pad for p in parties]
    y = BAS / 2 - sum(hauteurs) / 2
    filet = ch.melange(c["surCouleur"], c["couleur"], 0.14)
    for k, (p, h) in enumerate(zip(parties, hauteurs), 1):
        titre_p = p["titre"] if isinstance(p, dict) else p
        duree = p.get("duree", "") if isinstance(p, dict) else ""
        sl.texte(930, y + pad, 60, h - 2 * pad, "{}.".format(k), taille, c["surCouleur"], gras=True)
        sl.texte(1014, y + pad, 640, h - 2 * pad, titre_p, taille, c["surCouleur"], gras=True)
        sl.texte(1660, y + pad + 4, 150, h - 2 * pad, duree, 26, c["surCouleur"], align=DROITE)
        if k < len(parties):
            sl.ligne(930, y + h - 2, 880, 2, filet)
        y += h


def chapitre(sl: Slide, s):
    c = sl.deck.c
    sl.photo(s.get("photo"), 1160, 0, 760, BAS)
    sl.texte(120, 88, 600, 180, "{:02d}".format(int(s["numero"])), 200, c["couleur"], gras=True, interligne=0.85)
    if s.get("duree"):
        sl.pastille(1064, 96, s["duree"], 28, c["teinte"], c["encre"], pad_x=30, pad_y=12, majuscules=False, droite=True)
    taille = 88 if len(s["titre"]) <= 40 else 72
    titre(sl, 120, 298, 944, s["titre"], taille)
    points = s.get("points") or []
    hauteurs = [hauteur(p, 900, 32, 1.25) for p in points]
    y = 912 - sum(hauteurs) - 18 * max(0, len(points) - 1)
    for p, h in zip(points, hauteurs):
        sl.rect(120, y + 14, 12, 12, c["couleur"], rayon=2)
        sl.texte(152, y, 900, h + 4, p, 32, C["texte3"], interligne=1.25, gras_coul=C["texte"])
        y += h + 18
    sl.sticker(1080, 770, 160, -8)


def contenu(sl: Slide, s):
    x, w = 120, 824
    y = titre(sl, x, 96, w, s["titre"]) + 36
    if s.get("texte"):
        y = sl.pile(x, y, w, [(s["texte"], 32, {"coul": C["texte3"], "interligne": 1.5, "gras_coul": C["texte"]})]) + 36
    puces(sl, x, y, w, s.get("points") or [], 30, 22)
    sl.rect(1040, 180, 760, 640, C["fondCarte"], rayon=28)
    sl.visuel(s.get("image"), 1068, 208, 704, 584, s.get("legendeImage") or "Capture d'écran ou schéma")


def chiffre_cle(sl: Slide, s):
    c = sl.deck.c
    chiffre = str(s["chiffre"])
    taille = 280 if len(chiffre) <= 3 else (220 if len(chiffre) <= 5 else 160)
    h_phrase = hauteur(s["phrase"], 780, 44, 1.2, True)
    bloc = taille * 0.85 + 32 + h_phrase
    y = 508 - bloc / 2
    tb = sl.texte(120, y, 780, taille * 0.9, chiffre, taille, c["encre"], gras=True, interligne=0.85)
    if s.get("unite"):
        r = tb.text_frame.paragraphs[0].add_run()
        r.text = s["unite"]
        r.font.name, r.font.size, r.font.bold = POLICE, Pt(taille * 0.54 / 2), True
        r.font.color.rgb = couleur(c["encre"])
    sl.texte(120, y + taille * 0.85 + 32, 780, h_phrase + 4, s["phrase"], 44, gras=True)
    # Colonne droite.
    reperes = s.get("reperes") or []
    h_expl = hauteur(s.get("explication", ""), 780, 34, 1.5)
    h_rep = max([hauteur(r.get("texte"), 300, 26, 1.4) for r in reperes] or [0]) + 64 + 10 + 64
    bloc = h_expl + (40 + h_rep if reperes else 0) + (40 + 30 if s.get("source") else 0)
    y = 508 - bloc / 2
    y = sl.pile(1020, y, 780, [(s.get("explication", ""), 34, {"coul": C["texte3"], "interligne": 1.5, "gras_coul": C["texte"]})]) + 40
    if reperes:
        for k, r in enumerate(reperes[:2]):
            x = 1020 + k * (378 + 24)
            sl.rect(x, y, 378, h_rep, c["teinte"], rayon=24)
            sl.texte(x + 36, y + 32, 310, 70, r.get("valeur"), 64, c["encre"], gras=True, interligne=1.0)
            sl.texte(x + 36, y + 32 + 74, 310, h_rep - 110, r.get("texte"), 26, C["texte2"], interligne=1.4)
        y += h_rep + 40
    if s.get("source"):
        sl.texte(1020, y, 780, 34, "Source : " + s["source"], 24, C["gris"])


def frise(sl: Slide, s):
    c = sl.deck.c
    y = titre(sl, 120, 96, 1680, s["titre"]) + 20
    if s.get("intro"):
        sl.texte(120, y, 1680, 44, s["intro"], 30, C["texte4"])
    haut, bas = y + 64, 920
    milieu = (haut + bas) / 2
    sl.rect(120, milieu - 3, 1680, 6, c["teinte"], rayon=3)
    etapes = s["etapes"]
    n = len(etapes)
    lc = (1680 - 32 * (n - 1)) / n
    for k, et in enumerate(etapes):
        x = 120 + k * (lc + 32)
        derniere = k == n - 1
        sl.rond(x, milieu - 18, 36, c["couleur"] if derniere else "#FFFFFF", trait=c["couleur"], epaisseur=6)
        h_t = hauteur(et.get("texte"), lc, 28, 1.4)
        bloc = 56 + 10 + h_t
        yb = milieu - 18 - 32 - bloc if k % 2 == 0 else milieu + 18 + 32
        sl.texte(x, yb, lc, 60, et.get("date"), 52, c["encre"] if derniere else C["texte"], gras=True, interligne=1.0)
        sl.texte(x, yb + 66, lc, h_t + 4, et.get("texte"), 28, C["texte3"], interligne=1.4)


def graphique(sl: Slide, s):
    c = sl.deck.c
    y = titre(sl, 120, 96, 960, s["titre"]) + 40
    barres = s["barres"]
    valeurs = [float(b.get("valeur", 0)) for b in barres]
    maxi = max(valeurs) or 1
    cible = s.get("miseEnAvant", len(barres) - 1)
    n = len(barres)
    base = 860
    lc = (944 - 28 * (n - 1)) / n
    zone = base - y - 56
    for k, b in enumerate(barres):
        x = 128 + k * (lc + 28)
        hb = zone * valeurs[k] / maxi
        sl.rect(x, base - hb, lc, hb, c["couleur"] if k == cible else C["barreGrise"])
        valeur = b.get("affichage") or _nombre(b.get("valeur"))
        sl.texte(x - 20, base - hb - 48, lc + 40, 40, valeur, 28, c["encre"] if k == cible else C["texte4"], gras=True, align=CENTRE)
        sl.texte(x - 20, base + 12, lc + 40, 36, b.get("label"), 24, C["gris"], gras=True, align=CENTRE)
    sl.rect(120, base, 960, 3, C["texte"])
    elements = [
        (s.get("surtitre") or "À retenir", 24, {"coul": c["encre"], "gras": True, "majuscules": True, "espacement": 0.14}),
        (s.get("chiffre", ""), 128, {"coul": c["encre"], "gras": True, "interligne": 0.95}),
        (s.get("message", ""), 32, {"coul": C["texte3"], "interligne": 1.5, "gras_coul": C["texte"]}),
        ("Source : " + s["source"] if s.get("source") else "", 24, {"coul": C["gris"]}),
    ]
    total = sum(hauteur(t, 600, tl, o.get("interligne", 1.2), o.get("gras", False)) for t, tl, o in elements if t) + 28 * 3
    sl.pile(1200, 508 - total / 2, 600, elements, 28)


def _nombre(v) -> str:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v or "")
    return ("{:,.0f}" if x == int(x) else "{:,.1f}").format(x).replace(",", " ").replace(".", ",")


def image(sl: Slide, s):
    sl.photo(s.get("image"), 0, 0, W, H)
    w = 1040
    h_t = hauteur(s["titre"], w - 112, 56, 1.1, True)
    h_x = hauteur(s.get("texte", ""), w - 112, 28, 1.45) if s.get("texte") else 0
    h = 96 + 30 + 16 + h_t + (16 + h_x if h_x else 0)
    y = H - 120 - h
    sl.rect(120, y, w, h, "#FFFFFF", rayon=28)
    sl.pile(176, y + 48, w - 112, [
        (s.get("surtitre") or "Légende", 24, {"coul": sl.deck.c["encre"], "gras": True, "majuscules": True, "espacement": 0.14}),
        (s["titre"], 56, {"gras": True, "interligne": 1.1}),
        (s.get("texte", ""), 28, {"coul": C["texte3"], "interligne": 1.45}),
    ], 16)
    n = "{:02d}".format(len(sl.deck.prs.slides))
    sl.pastille(W - 64, H - 48 - 46, n, 24, "#FFFFFF", C["texte"], pad_x=22, pad_y=8, majuscules=False, droite=True)


def texte(sl: Slide, s):
    c = sl.deck.c
    paragraphes = s["paragraphes"]
    sl.rect(120, 96, 96, 10, c["couleur"], rayon=5)
    y = titre(sl, 120, 138, 520, s["titre"]) + 32
    if s.get("intro"):
        sl.texte(120, y, 520, hauteur(s["intro"], 520, 30, 1.5) + 4, s["intro"], 30, C["texte4"], interligne=1.5)
    deux = len(paragraphes) > 1
    lc = 484 if deux else 1040
    hauteurs = [hauteur(p, lc, 30, 1.6) for p in paragraphes]
    # Répartition en deux colonnes équilibrées.
    coupe = len(paragraphes)
    if deux:
        meilleur = None
        for i in range(1, len(paragraphes)):
            m = max(sum(hauteurs[:i]) + 28 * (i - 1), sum(hauteurs[i:]) + 28 * (len(paragraphes) - i - 1))
            if meilleur is None or m < meilleur:
                meilleur, coupe = m, i
    colonnes = [list(zip(paragraphes[:coupe], hauteurs[:coupe])), list(zip(paragraphes[coupe:], hauteurs[coupe:]))]
    for k, col in enumerate(colonnes):
        total = sum(h for _, h in col) + 28 * max(0, len(col) - 1)
        y = 508 - total / 2
        for p, h in col:
            sl.texte(760 + k * (484 + 72), y, lc, h + 4, p, 30, C["texte2"], interligne=1.6, gras_coul=C["texte"])
            y += h + 28


def citation(sl: Slide, s):
    c = sl.deck.c
    sl.rect(0, 0, W, BAS, c["couleur"])
    taille = 72 if len(s["citation"]) <= 100 else 60
    h_q = hauteur(s["citation"], 1500, taille, 1.2, True)
    bloc = 110 + 56 + h_q + 56 + 120
    y = 500 - bloc / 2
    sl.texte(200, y - 40, 300, 200, "«", 220, c["surCouleur"], gras=True, interligne=1.0)
    y += 110 + 56
    sl.texte(200, y, 1500, h_q + 8, s["citation"], taille, c["surCouleur"], gras=True, interligne=1.2)
    y += h_q + 56
    sl.rond(200, y, 120, "#FFFFFF")
    sl.icone("user-round", 228, y + 28, 64)
    sl.texte(348, y, 1200, 120, s.get("auteur") or "", 34, c["surCouleur"], gras=True, ancre=MILIEU)


def avant_apres(sl: Slide, s):
    c = sl.deck.c
    y = titre(sl, 120, 96, 1680, s["titre"]) + 48
    lc = (1680 - 48) / 2
    for k, (cle, libelle) in enumerate((("avant", "Avant"), ("apres", "Après"))):
        d = s.get(cle) or {}
        x = 120 + k * (lc + 48)
        h_box = 920 - y - 28 - 54
        sl.rect(x, y, lc, h_box, C["fondCarte"], rayon=28)
        sl.visuel(d.get("image"), x + 20, y + 20, lc - 40, h_box - 40, "Capture " + libelle.lower())
        yb = y + h_box + 28
        fond, coul = (C["bordure"], C["texte"]) if k == 0 else (c["couleur"], c["surCouleur"])
        w, _ = sl.pastille(x, yb, libelle, 24, fond, coul, pad_x=26)
        sl.texte(x + w + 24, yb, lc - w - 24, 54, d.get("texte", ""), 30, C["texte3"], ancre=MILIEU)


def notion_cle(sl: Slide, s):
    c = sl.deck.c
    sl.rect(0, 0, W, BAS, c["teinte"])
    taille = 112 if len(s["titre"]) <= 26 else 84
    h_t = hauteur(s["titre"], 1600, taille, 1.0, True)
    h_d = hauteur(s["definition"], 1400, 44, 1.4)
    termes = s.get("termes") or []
    bloc = 53 + 40 + h_t + 40 + h_d + (56 + 76 if termes else 0)
    y = 500 - bloc / 2
    sl.pastille(160, y, s.get("surtitre") or "Notion clé", 24)
    y += 53 + 40
    sl.texte(160, y, 1600, h_t + 8, s["titre"], taille, gras=True, interligne=1.0)
    y += h_t + 40
    sl.texte(160, y, 1400, h_d + 6, s["definition"], 44, C["texte2"], interligne=1.4, gras_coul=C["texte"])
    y += h_d + 56
    x = 160
    for t in termes:
        lt = largeur_texte(t.get("terme"), 28, True) * 1.15 + 14 + largeur_texte(t.get("definition"), 28) + 56
        if x + lt > 1800:
            break
        sl.rect(x, y, lt, 76, "#FFFFFF", rayon=18)
        tb = sl.texte(x + 28, y, lt - 56, 76, "", 28, ancre=MILIEU)
        p = tb.text_frame.paragraphs[0]
        for contenu, police, gras, coul in ((t.get("terme", "") + "  ", MONO, True, c["encre"]), (ch.typographie(t.get("definition", "")), POLICE, False, C["texte3"])):
            r = p.add_run()
            r.text = contenu
            r.font.name, r.font.size, r.font.bold = police, Pt(14), gras
            r.font.color.rgb = couleur(coul)
        x += lt + 20


def code(sl: Slide, s):
    c = sl.deck.c
    elements = s.get("elements") or []
    h_g = hauteur(s["titre"], 724, 72, 1.05, True) + 36 + hauteur(s.get("intro", ""), 724, 32, 1.55) + 36
    h_g += sum(hauteur(x.get("texte"), 724, 28, 1.45) + 40 for x in elements) + 24 * max(0, len(elements) - 1)
    y = 508 - h_g / 2
    y = titre(sl, 120, y, 724, s["titre"]) + 36
    if s.get("intro"):
        y = sl.pile(120, y, 724, [(s["intro"], 32, {"coul": C["texte3"], "interligne": 1.55})]) + 36
    for x in elements:
        sl.texte(120, y, 724, 40, x.get("code"), 28, c["encre"], gras=True, police=MONO)
        h = hauteur(x.get("texte"), 724, 28, 1.45)
        sl.texte(120, y + 40, 724, h + 4, x.get("texte"), 28, C["texte3"], interligne=1.45)
        y += 40 + h + 24
    # Encadré sombre.
    h_syn = hauteur(s["syntaxe"], 748, 34, 1.5, mono=True)
    h_ex = hauteur(s.get("exemple", ""), 748, 34, 1.5, mono=True) if s.get("exemple") else 0
    h_res = hauteur(s.get("resultat", ""), 748, 28, 1.4) if s.get("resultat") else 0
    h = 104 + 30 + 22 + h_syn + (12 + 2 + 12 + 22 + 30 + 22 + h_ex if h_ex else 0) + (22 + h_res if h_res else 0)
    y = 508 - h / 2
    sl.rect(940, y, 860, h, C["codeFond"], rayon=28)
    y += 52
    sl.texte(996, y, 748, 32, s.get("libelle") or "Syntaxe", 24, C["codeLibelle"], gras=True, majuscules=True, espacement=0.14)
    y += 52
    code_colore(sl, 996, y, 748, h_syn, s["syntaxe"], c["couleur"])
    y += h_syn + 12
    if h_ex:
        sl.ligne(996, y, 748, 2, "#3A3A40")
        y += 14 + 22
        sl.texte(996, y, 748, 32, "Exemple", 24, C["codeLibelle"], gras=True, majuscules=True, espacement=0.14)
        y += 52
        code_colore(sl, 996, y, 748, h_ex, s["exemple"], c["couleur"])
        y += h_ex + 22
    if h_res:
        sl.texte(996, y, 748, h_res + 4, s["resultat"], 28, C["codeTexte"], interligne=1.4, gras_coul="#FFFFFF")


def code_colore(sl: Slide, x, y, w, h, source, coul_fonction):
    tb = sl.texte(x, y, w, h + 6, "", 34, police=MONO)
    tf = tb.text_frame
    for k, ligne in enumerate((source or "").split("\n")):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.line_spacing = round(1.5 / 1.17, 3)
        for morceau in re.split(r'("[^"]*"|\'[^\']*\'|\b[A-Z][A-Z0-9_.]{1,}(?=\())', ligne):
            if not morceau:
                continue
            r = p.add_run()
            r.text = morceau
            r.font.name, r.font.size = MONO, Pt(17)
            if morceau.startswith(("\"", "'")):
                r.font.color.rgb = couleur(C["codeChaine"])
            elif re.fullmatch(r"[A-Z][A-Z0-9_.]{1,}", morceau):
                r.font.color.rgb = couleur(coul_fonction)
            else:
                r.font.color.rgb = couleur("#FFFFFF")


def capture(sl: Slide, s):
    c = sl.deck.c
    titre(sl, 120, 88, 1680, s["titre"])
    y0, y1 = 208, 928
    sl.rect(120, y0, 1140, y1 - y0, C["fondCarte"], rayon=24)
    zx, zy, zw, zh = 140, y0 + 20, 1100, y1 - y0 - 40
    sl.visuel(s.get("image"), zx, zy, zw, zh, "Capture d'écran à annoter", 12)
    reperes = s["reperes"]
    for k, r in enumerate(reperes, 1):
        px = zx + zw * float(r.get("x", 15 + 70 * ((k - 1) % 2))) / 100 - 32
        py = zy + zh * float(r.get("y", 15 + 25 * ((k - 1) // 2))) / 100 - 32
        sl.rond(px - 4, py - 4, 72, "#FFFFFF")
        sl.numero(px, py, 64, k, 28)
    hauteurs = [40 + hauteur(r.get("texte"), 420, 28, 1.4) for r in reperes]
    y = (y0 + y1) / 2 - (sum(hauteurs) + 36 * (len(reperes) - 1)) / 2
    for k, (r, h) in enumerate(zip(reperes, hauteurs), 1):
        sl.texte(1332, y, 40, 44, str(k), 32, c["encre"], gras=True)
        sl.texte(1382, y, 420, 44, r.get("titre"), 32, gras=True)
        sl.texte(1382, y + 42, 420, h - 40, r.get("texte"), 28, C["texte3"], interligne=1.4)
        y += h + 36


def pas_a_pas(sl: Slide, s):
    titre(sl, 120, 96, 1680, s["titre"])
    etapes = s["etapes"]
    n = len(etapes)
    lc = (1680 - 32 * (n - 1)) / n
    for k, et in enumerate(etapes):
        x = 120 + k * (lc + 32)
        d = et if isinstance(et, dict) else {"texte": et}
        sl.rect(x, 236, lc, 260, C["fondCarte"], rayon=20)
        sl.visuel(d.get("image"), x + 12, 248, lc - 24, 236, "Capture étape {}".format(k + 1), 12)
        sl.numero(x, 524, 64, k + 1, 28)
        sl.texte(x, 616, lc, 300, d.get("texte"), 30, C["texte3"], interligne=1.4, gras_coul=C["texte"])


def comparatif(sl: Slide, s):
    c = sl.deck.c
    y = titre(sl, 120, 96, 1680, s["titre"]) + 56
    colonnes = (s["colonnes"] + ["", ""])[:2]
    xs, ws = [120, 560, 1180], [440, 620, 620]
    lignes = s["lignes"]
    h_tete = 30 * 1.4 + 52
    hauteurs = [max(hauteur(l.get("critere"), 376, 28, 1.4, True), *[hauteur(v, 556, 28, 1.4) for v in (l.get("valeurs") or ["", ""])[:2]]) + 52 for l in lignes]
    total = h_tete + sum(hauteurs)
    sl.rect(120, y, 1680, total, "#FFFFFF", rayon=24, trait=C["filet"], epaisseur=2)
    sl.rect(122, y + 2, 1056, h_tete - 2, C["fondGris"])
    sl.rect(1180, y + 2, 618, h_tete - 2, c["couleur"])
    sl.texte(xs[1] + 32, y, 556, h_tete, colonnes[0], 30, gras=True, ancre=MILIEU)
    sl.texte(xs[2] + 32, y, 556, h_tete, colonnes[1], 30, c["surCouleur"], gras=True, ancre=MILIEU)
    yl = y + h_tete
    for l, h in zip(lignes, hauteurs):
        v = (l.get("valeurs") or []) + ["", ""]
        sl.rect(1180, yl, 618, h - (2 if l is lignes[-1] else 0), c["teinte"])
        sl.ligne(122, yl, 1676, 2, C["filet"])
        sl.texte(xs[0] + 32, yl + 26, 376, h - 52, l.get("critere"), 28, gras=True, interligne=1.4)
        sl.texte(xs[1] + 32, yl + 26, 556, h - 52, v[0], 28, C["texte3"], interligne=1.4, gras_coul=C["texte"])
        sl.texte(xs[2] + 32, yl + 26, 556, h - 52, v[1], 28, interligne=1.4)
        yl += h
    if s.get("recommandation"):
        sl.texte(120, yl + 56, 1680, 90, "**Recommandation** : " + s["recommandation"], 28, C["texte4"], gras_coul=c["encre"])


def raccourcis(sl: Slide, s):
    y = titre(sl, 120, 96, 1100, s.get("titre") or "Raccourcis à connaître")
    if s.get("remarque"):
        sl.texte(1200, y - 40, 600, 40, s["remarque"], 26, C["gris"], align=DROITE)
    y += 56
    for k, r in enumerate(s["raccourcis"]):
        x = 120 + (k % 2) * 860
        yy = y + (k // 2) * 106
        sl.rect(x, yy, 820, 90, C["fondCarte"], rayon=20)
        xk = x + 32
        for i, t in enumerate(touches(r)):
            if i:
                sl.texte(xk, yy, 24, 90, "+", 24, C["grisClair"], align=CENTRE, ancre=MILIEU)
                xk += 30
            lt = largeur_texte(t, 26, True) + 40
            sl.rect(xk, yy + 20, lt, 50, "#FFFFFF", rayon=12, trait=C["barreGrise"], epaisseur=2)
            sl.texte(xk, yy + 20, lt, 50, t, 26, gras=True, align=CENTRE, ancre=MILIEU)
            xk += lt + 6
        sl.texte(x + 32 + 320 + 24, yy, 820 - 408, 90, r.get("action"), 30, ancre=MILIEU)


def bon_a_savoir(sl: Slide, s):
    from support_html import genre_encadre

    y = titre(sl, 120, 96, 1680, s.get("titre") or "Bon à savoir") + 56
    encadres = s["encadres"]
    n = len(encadres)
    lc = (1680 - 32 * (n - 1)) / n
    for k, en in enumerate(encadres):
        libelle, fond, encre = genre_encadre(en)
        fond = sl.deck.c["teinte"] if fond.startswith("var") else fond
        encre = sl.deck.c["encre"] if encre.startswith("var") else encre
        x = 120 + k * (lc + 32)
        sl.rect(x, y, lc, 920 - y, fond, rayon=28)
        sl.pile(x + 48, y + 48, lc - 96, [
            (en.get("libelle") or libelle, 24, {"coul": encre, "gras": True, "majuscules": True, "espacement": 0.14}),
            (en.get("titre", ""), 40, {"gras": True, "interligne": 1.15}),
            (en.get("texte", ""), 30, {"coul": C["texte2"], "interligne": 1.5, "gras_coul": C["texte"]}),
        ], 24)


def exercice(sl: Slide, s):
    c = sl.deck.c
    sl.rect(1160, 0, 760, BAS, C["fondCarte"])
    x, w = 120, 920
    sl.pastille(x, 88, "Exercice {}".format(s["numero"]), 24)
    y = titre(sl, x, 88 + 53 + 32, w, s["titre"], 64) + 32
    if s.get("contexte"):
        y = sl.pile(x, y, w, [(s["contexte"], 30, {"coul": C["texte3"], "interligne": 1.5, "gras_coul": C["texte"]})]) + 40
    for k, consigne in enumerate(s["consignes"], 1):
        h = max(48, hauteur(consigne, w - 70, 30, 1.4))
        sl.numero(x, y, 48, k, 24)
        sl.texte(x + 70, y + 2, w - 70, h, consigne, 30, C["texte3"], interligne=1.4, gras_coul=C["texte"])
        y += h + 20
    cartes = []
    if s.get("duree"):
        cartes.append(("Durée", s["duree"], 34, True, POLICE, False))
    if s.get("fichier"):
        cartes.append(("Fichier", s["fichier"], 30, True, MONO, False))
    if s.get("livrable"):
        cartes.append(("Livrable", s["livrable"], 28, False, POLICE, False))
    if s.get("bonus"):
        cartes.append(("Pour aller plus loin", s["bonus"], 28, True, POLICE, True))
    hauteurs = [56 + 6 + hauteur(v, 496, t, 1.4, g, p == MONO) + 4 for _, v, t, g, p, _ in cartes]
    y = 500 - (sum(hauteurs) + 20 * max(0, len(cartes) - 1)) / 2
    for (libelle, valeur, taille, gras, police, plein), h in zip(cartes, hauteurs):
        fond, coul_l, coul_v = (c["couleur"], c["surCouleur"], c["surCouleur"]) if plein else ("#FFFFFF", c["encre"], C["texte"])
        sl.rect(1240, y, 560, h, fond, rayon=22)
        sl.texte(1272, y + 28, 496, 32, libelle, 24, coul_l, gras=True, majuscules=True, espacement=0.1)
        sl.texte(1272, y + 28 + 36, 496, h - 70, valeur, taille, coul_v, gras=gras, police=police, interligne=1.4)
        y += h + 20


def exercice_etapes(sl: Slide, s):
    c = sl.deck.c
    sl.pastille(120, 88, "Exercice {}".format(s["numero"]), 24)
    y = titre(sl, 120, 88 + 53 + 24, 1200, s["titre"], 64) + 24
    if s.get("contexte"):
        y = sl.pile(120, y, 1200, [(s["contexte"], 30, {"coul": C["texte3"], "interligne": 1.5})])
    # Cercle de durée.
    duree = str(s.get("duree", "")).strip()
    nombre, _, unite = duree.partition(" ")
    if not nombre.isdigit():
        nombre, unite = duree, ""
    cy = (88 + y) / 2 - 120
    sl.rond(1560, max(64, cy), 240, "#FFFFFF", trait=c["couleur"], epaisseur=10)
    sl.texte(1560, max(64, cy) + 60, 240, 90, nombre or "–", 84 if len(nombre) <= 3 else 56, c["encre"], gras=True, align=CENTRE, interligne=1.0)
    sl.texte(1560, max(64, cy) + 150, 240, 40, unite or ("minutes" if nombre.isdigit() else ""), 26, C["texte4"], gras=True, align=CENTRE)
    y = max(y, max(64, cy) + 240) + 44
    infos = [(lib, s[cle]) for lib, cle in (("Fichier", "fichier"), ("Modalité", "modalite"), ("Livrable", "livrable")) if s.get(cle)]
    bas_etapes = 1000 - 64 - (30 + 28 + 40 if infos else 0) - 44
    etapes = s["etapes"]
    n = len(etapes)
    lc = (1680 - 28 * (n - 1)) / n
    for k, et in enumerate(etapes):
        d = et if isinstance(et, dict) else {"texte": et}
        x = 120 + k * (lc + 28)
        sl.rect(x, y, lc, bas_etapes - y, C["fondCarte"], rayon=28)
        sl.pile(x + 44, y + 40, lc - 88, [
            (str(k + 1), 96, {"coul": c["encre"], "gras": True, "interligne": 0.9}),
            (d.get("titre", ""), 34, {"gras": True}),
            (d.get("texte", ""), 28, {"coul": C["texte3"], "interligne": 1.45, "gras_coul": C["texte"]}),
        ], 18)
    if infos:
        yi = bas_etapes + 44
        sl.ligne(120, yi, 1680, 2, C["filet"])
        texte_infos = "     ".join("**{}** : {}".format(lib, ch.sans_gras(v)) for lib, v in infos)
        sl.texte(120, yi + 28, 1680, 44, texte_infos, 28, C["texte3"], gras_coul=c["encre"])


def quiz(sl: Slide, s):
    c = sl.deck.c
    w, _ = sl.pastille(120, 96, "Quiz", 24)
    sl.texte(120 + w + 24, 96, 600, 53, "Question {} sur {}".format(s.get("numero", 1), s.get("total", 1)), 28, C["gris"], gras=True, ancre=MILIEU)
    y = titre(sl, 120, 197, 1500, s["question"], 64) + 48
    props = s["propositions"]
    rangs = (len(props) + 1) // 2
    ht = (920 - y - 28 * (rangs - 1)) / rangs
    for k, p in enumerate(props):
        x = 120 + (k % 2) * (826 + 28)
        yy = y + (k // 2) * (ht + 28)
        bonne = s["_reponse"] and k == s["bonne"]
        if bonne:
            sl.rect(x, yy, 826, ht, c["teinte"], rayon=28, trait=c["couleur"], epaisseur=4)
            sl.rect(x + 44, yy + ht / 2 - 36, 72, 72, c["couleur"], rayon=18)
            sl.texte(x + 44, yy + ht / 2 - 36, 72, 72, "ABCD"[k], 34, c["surCouleur"], gras=True, align=CENTRE, ancre=MILIEU)
            sl.texte(x + 148, yy, 470, ht, p, 40, gras=True, ancre=MILIEU)
            sl.texte(x + 600, yy, 190, ht, "Bonne réponse", 26, c["encre"], gras=True, align=DROITE, ancre=MILIEU)
        else:
            sl.rect(x, yy, 826, ht, C["fondCarte"], rayon=28)
            sl.rect(x + 44, yy + ht / 2 - 36, 72, 72, "#FFFFFF", rayon=18)
            sl.texte(x + 44, yy + ht / 2 - 36, 72, 72, "ABCD"[k], 34, gras=True, align=CENTRE, ancre=MILIEU)
            sl.texte(x + 148, yy, 640, ht, p, 40, gras=True, ancre=MILIEU)


def a_retenir(sl: Slide, s):
    c = sl.deck.c
    sl.rect(0, 0, 720, BAS, c["couleur"])
    sl.texte(120, 96, 540, 300, s.get("titre") or "À retenir", 96, c["surCouleur"], gras=True, interligne=1.0)
    if s.get("sousTitre"):
        sl.texte(120, 860, 540, 44, s["sousTitre"], 28, c["surCouleur"], gras=True)
    messages = s["messages"]
    hauteurs = [max(72, hauteur(m, 840, 38, 1.4)) for m in messages]
    y = 500 - (sum(hauteurs) + 56 * (len(messages) - 1)) / 2
    for k, (m, h) in enumerate(zip(messages, hauteurs), 1):
        sl.texte(840, y - 14, 100, 80, str(k), 72, c["couleur"], gras=True, interligne=1.0)
        sl.texte(960, y, 840, h + 4, m, 38, C["texte2"], interligne=1.4, gras_coul=C["texte"])
        y += h + 56


def ressources(sl: Slide, s):
    c = sl.deck.c
    y = titre(sl, 120, 96, 1680, s.get("titre") or "Pour continuer") + 56
    items = s["ressources"]
    rangs = (len(items) + 1) // 2
    hc = (920 - y - 28 * (rangs - 1)) / rangs
    for k, r in enumerate(items):
        x = 120 + (k % 2) * (826 + 28)
        yy = y + (k // 2) * (hc + 28)
        lien = r.get("lien") or ""
        skazy = r.get("skazy") or "skazy.nc" in lien
        sl.rect(x, yy, 826, hc, c["teinte"] if skazy else C["fondCarte"], rayon=28)
        sl.texte(x + 48, yy + 44, 730, 50, r.get("titre"), 36, gras=True)
        sl.texte(x + 48, yy + 44 + 56, 730, hc - 44 - 56 - 90, r.get("texte"), 28, C["texte3"], interligne=1.45)
        if lien:
            affiche = re.sub(r"^https?://(www\.)?", "", lien).rstrip("/")
            sl.texte(x + 48, yy + hc - 44 - 40, 730, 40, affiche, 28, c["encre"], gras=True, lien=lien)


def evaluation(sl: Slide, s):
    c = sl.deck.c
    y = titre(sl, 120, 96, 1680, s.get("titre") or "Votre avis compte") + 56
    bas = 920 - 28 - 56
    lc = (1680 - 32) / 2
    sl.rect(120, y, lc, bas - y, c["teinte"], rayon=32)
    sl.pile(176, y + 56, lc - 112, [
        ("1 · Quiz final", 24, {"coul": c["encre"], "gras": True, "majuscules": True, "espacement": 0.14}),
        ("Mesurez votre progression", 44, {"gras": True, "interligne": 1.15}),
        ("Quelques questions pour vérifier ce que vous avez retenu de la formation.", 30, {"coul": C["texte2"], "interligne": 1.5}),
    ], 22)
    sl.pastille(176, bas - 56 - 66, s.get("quiz") or "Sur kahoot.it, code affiché à l'écran", 30, pad_x=32, pad_y=14, majuscules=False)
    x2 = 120 + lc + 32
    sl.rect(x2, y, lc, bas - y, C["fondCarte"], rayon=32)
    total = 24 + 22 + 2 * 44 * 1.15 + 22 + 3 * 30 * 1.5
    sl.pile(x2 + 56, (y + bas) / 2 - total / 2, lc - 112 - 320, [
        ("2 · Satisfaction", 24, {"coul": c["encre"], "gras": True, "majuscules": True, "espacement": 0.14}),
        ("Trois minutes, anonyme", 44, {"gras": True, "interligne": 1.15}),
        ("Vos retours font évoluer la formation. Scannez le QR code.", 30, {"coul": C["texte2"], "interligne": 1.5}),
    ], 22)
    qx, qy = x2 + lc - 56 - 280, (y + bas) / 2 - 140
    sl.rect(qx, qy, 280, 280, "#FFFFFF", rayon=24)
    sl.visuel(s.get("qrCode"), qx + 16, qy + 16, 248, 248, "QR code", 12)
    sl.texte(120, bas + 28, 1680, 44, s.get("message") or "Votre attestation de fin de formation vous parvient par e-mail.", 28, C["texte4"])


def questions(sl: Slide, s):
    d, f, c = sl.deck, sl.deck.f, sl.deck.c
    sl.photo(ch.url_photo(s.get("photo") or ch.CHARTE["photoQuestions"]), 0, 0, 960, H)
    sl.rect(960, 0, 960, H, c["couleur"])
    sl.image(d.logo(ch.variante_logo(c)), 1080, 110, 322, 106)
    t = s.get("titre") or "Avez-vous des questions ?"
    h = hauteur(t, 720, 88, 1.05, True)
    sl.texte(1080, 558 - h / 2, 720, h + 10, t, 88, c["surCouleur"], gras=True, interligne=1.0)
    sl.texte(1080, 900, 720, 42, f["formateur"], 28, c["surCouleur"], gras=True)
    sl.texte(1080, 940, 720, 42, f["email"], 28, c["surCouleur"])


def battle(sl: Slide, s):
    c = sl.deck.c
    w, h = 220, 53
    sl.rect(120, 88, w, h, C["texte"], rayon=h / 2)
    sl.icone("zap", 148, 88 + 12, 28, "#FFFFFF")
    sl.texte(184, 88, w - 64, h, "Battle", 24, "#FFFFFF", gras=True, majuscules=True, espacement=0.12, ancre=MILIEU)
    titre(sl, 120, 88 + h + 24, 1100, s.get("titre") or "Battle de questions")
    sl.texte(1000, 88 + h + 24 + 30, 800, 50, s.get("accroche") or "Deux équipes, un objectif : piéger l'autre.", 30, C["texte4"], align=DROITE)
    y0, y1 = 88 + h + 24 + 76 + 44, 1000 - 64 - 74 - 44
    lc = (1680 - 140 - 80) / 2
    for k, (nom, fond, coul, trait) in enumerate((
        ("Équipe A", c["couleur"], c["surCouleur"], ch.melange(c["surCouleur"], c["couleur"], 0.4)),
        ("Équipe B", C["fondCarte"], C["texte"], "#A5A5A7"),
    )):
        x = 120 + k * (lc + 220)
        sl.rect(x, y0, lc, y1 - y0, fond, rayon=32, trait=None if k == 0 else C["bordure"], epaisseur=3)
        sl.texte(x + 52, y0 + 48, lc - 104, 32, nom, 24, coul, gras=True, majuscules=True, espacement=0.14)
        sl.texte(x + 52, y0 + 104, lc - 104, 34, "Nom de l'équipe", 26, coul, gras=True)
        sl.ligne(x + 52, y0 + 252, lc - 104, 3, trait)
        sl.texte(x + 52, y0 + 284, lc - 104, 34, "Score", 26, coul, gras=True)
        sl.rect(x + 52, y0 + 330, lc - 104, y1 - y0 - 330 - 48, None, rayon=20, trait=trait, epaisseur=3, tirets=True)
    sl.rond(120 + lc + 40, (y0 + y1) / 2 - 70, 140, c["teinte"])
    sl.texte(120 + lc + 40, (y0 + y1) / 2 - 70, 140, 140, "VS", 52, c["encre"], gras=True, align=CENTRE, ancre=MILIEU)
    regles = s["regles"]
    n = len(regles)
    lr = (1680 - 32 * (n - 1)) / n
    for k, r in enumerate(regles):
        x = 120 + k * (lr + 32)
        sl.numero(x, y1 + 44, 48, k + 1, 24, c["teinte"], c["encre"])
        sl.texte(x + 66, y1 + 44, lr - 66, 110, r, 26, C["texte3"], interligne=1.4)


def accompagnement_360(sl: Slide, s):
    from support_html import POLES

    titre(sl, 120, 96, 1200, "Skazy")
    sl.texte(120, 96 + 76 + 6, 1200, 60, "Accompagnement 360°", 44, C["texte2"])
    y = 96 + 76 + 6 + 53 + 64
    lc = (1680 - 28 * 3) / 4
    for k, (nom, coul, texte_) in enumerate(POLES):
        x = 120 + k * (lc + 28)
        sl.rect(x, y, lc, 920 - y, C["fondCarte"], rayon=28)
        sl.texte(x + 40, y + 48, lc - 80, 52, "skazy", 52, C["texte2"], gras=True, interligne=0.9)
        sl.texte(x + 40, y + 48 + 50, lc - 80, 40, nom, 30, coul, gras=True)
        sl.texte(x + 40, y + 48 + 50 + 40 + 28, lc - 80, 400, texte_, 26, C["texte3"], interligne=1.5)
    sl.sticker(1920 - 120 - 150, 80, 150, 8, "rocket")


def autres_formations(sl: Slide, s):
    titre(sl, 120, 88, 1680, "Nos autres formations")
    sl.texte(120, 88 + 76 + 10, 1680, 50, "Le catalogue complet : **{}**".format(ch.CONTACT["site"]), 34, C["texte2"], gras_coul=sl.deck.c["encre"])
    y0, y1 = 88 + 76 + 10 + 48 + 48, 1000 - 64 - 40 - 48
    lc, hc = (1680 - 24 * 4) / 5, (y1 - y0 - 24) / 2
    for k, c in enumerate(ch.CHARTE["categories"] + [None]):
        x = 120 + (k % 5) * (lc + 24)
        y = y0 + (k // 5) * (hc + 24)
        if c is None:
            sl.rect(x, y, lc, hc, C["texte"], rayon=22)
            sl.texte(x + 32, y + hc - 32 - 120, lc - 64, 80, "Tout le catalogue", 30, "#FFFFFF", gras=True, ancre=BAS_)
            sl.texte(x + 32, y + hc - 32 - 36, lc - 64, 36, ch.CONTACT["site"], 24, "#FFFFFF", gras=True, lien=ch.CONTACT["url"])
            continue
        sl.rect(x, y, lc, hc, c["couleur"], rayon=22)
        sl.polygone([(x, y), (x + lc * 0.62, y), (x + lc * 0.62 * 0.78, y + hc), (x, y + hc)], "#FFFFFF", alpha=0.24)
        blanc = c["surCouleur"].upper() == "#FFFFFF"
        sl.icone(c["icone"], x + lc * 0.62 * 0.44 - 42, y + (hc - 64) / 2 - 42, 84, "#FFFFFF" if blanc else C["texte"])
        lt = min(lc - 40, max(120, largeur_texte(c["nom"], 26, True) + 48))
        hl = 26 * 1.2 * nb_lignes(c["nom"], lt - 40, 26, True) + 20
        sl.rect(x + 20, y + hc - 20 - hl, lt, hl, "#FFFFFF", rayon=12)
        sl.texte(x + 40, y + hc - 20 - hl, lt - 40, hl, c["nom"], 26, gras=True, ancre=MILIEU)
    texte_ = s.get("texte") or "**L'IA au quotidien** : ChatGPT, Claude, Copilot, Mistral, Gemini. Et aussi Make, Canva, Figma, Power BI, Microsoft 365."
    sl.texte(120, y1 + 40, 1680, 44, texte_, 28, C["texte3"], gras_coul=C["texte"])


RENDUS = {
    "couverture": couverture, "faisons-connaissance": faisons_connaissance, "objectifs": objectifs, "programme": programme,
    "chapitre": chapitre, "contenu": contenu, "chiffre-cle": chiffre_cle, "frise": frise, "graphique": graphique,
    "image": image, "texte": texte, "citation": citation, "avant-apres": avant_apres, "notion-cle": notion_cle,
    "code": code, "capture": capture, "pas-a-pas": pas_a_pas, "comparatif": comparatif, "raccourcis": raccourcis,
    "bon-a-savoir": bon_a_savoir, "exercice": exercice, "exercice-etapes": exercice_etapes, "quiz": quiz,
    "a-retenir": a_retenir, "ressources": ressources, "evaluation": evaluation, "questions": questions,
    "battle": battle, "accompagnement-360": accompagnement_360, "autres-formations": autres_formations,
}

SANS_PIED = {"couverture", "image", "questions"}


def rendre_pptx(s: dict) -> bytes:
    deck = Deck(s)
    for slide in s["_slides"]:
        t = slide["type"]
        sl = Slide(deck)
        RENDUS[t](sl, slide)
        if t not in SANS_PIED:
            sl.pied(couleur_cat=(t == "chapitre"))
        sl.notes(slide.get("notes"))
    tampon = io.BytesIO()
    deck.prs.save(tampon)
    _ = math  # gardé pour les calculs de mise en page futurs
    return tampon.getvalue()
