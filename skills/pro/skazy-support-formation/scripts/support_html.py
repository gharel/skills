"""Support de formation : rendu HTML (deck 1920 × 1080, navigation au clavier, notes, impression PDF).

Reproduit les 30 mises en page du modèle « 4. Support de formation par catégorie » du Skazy Formation
Design System (design-skazy, templates/support-formation).

Tout le design vient de la feuille que design-skazy exporte pour ce modèle (assets/charte/support-formation.css),
incluse telle quelle dans la page : jetons, styles.css du design system, styles du modèle, puis une classe
`sf-xxxxxx` par style en ligne du modèle (xxxxxx : début du SHA-1 du style). Chaque élément reprend la classe
de l'élément équivalent du modèle ; un attribut style ne porte que ce qui dépend du contenu (positions, nombre
de colonnes, hauteur d'une barre, taille adaptée à un texte long, URL d'une image). Le CSS propre au skill se
limite au deck à l'écran et à l'impression, plus le composant image-slot du modèle, qui n'a pas de classe.
"""

from __future__ import annotations

import base64
import html as _html
import math
import re
from functools import lru_cache
from pathlib import Path

import charte as ch
from charte import esc
from support_modele import touches

C = ch.COULEURS

# Classes du modèle employées sur la plupart des slides.
SECTION = "sf-b45648"  # slide sur fond blanc (voir FOND pour les autres)
H2 = "sf-2f766c"  # titre de slide
SURTITRE = "sf-b76084"  # « Tour de table », « À retenir », « Légende »…
PASTILLE = "sf-ee5903"  # « Notion clé », « Exercice 1 »
GRAS = "sf-e320ef"  # **gras** d'un texte courant


@lru_cache(maxsize=None)
def feuille() -> str:
    """Feuille exportée par design-skazy pour le modèle, dans la charte de ce skill (le module charte importé
    peut venir d'un autre skill, dont la charte n'a pas cette feuille)."""
    return (Path(__file__).resolve().parent.parent / "assets" / "charte" / "support-formation.css").read_text(encoding="utf-8")


def propriete(classe: str, nom: str, defaut: str | None = None) -> str:
    """Valeur d'une propriété d'une classe du modèle, jeton --color-… résolu (couleurs du PPTX, mesures)."""
    regle = re.search(r"^\.{}\{{(.*)\}}$".format(classe), feuille(), re.M).group(1)
    valeur = dict(d.split(":", 1) for d in regle.split(";")).get(nom, defaut)
    if valeur is None:
        raise KeyError("{} : pas de propriété {} dans le modèle".format(classe, nom))
    jeton = re.fullmatch(r"var\((--color-[\w-]+)\)", valeur)
    if jeton:
        valeur = re.search(r"{}:\s*(#[0-9A-Fa-f]{{6}})".format(jeton.group(1)), feuille()).group(1).upper()
    return valeur


# ---------------------------------------------------------------- mots trop longs pour leur colonne

LARGEUR = 1920  # largeur d'une slide (deck de 1920 × 1080 px, comme le modèle)


def longueurs(classe: str, nom: str) -> list[float]:
    """Longueurs en px d'une propriété d'une classe du modèle (« 96px 120px 80px » → [96, 120, 80])."""
    return [float(t[:-2]) if t.endswith("px") else 0.0 for t in propriete(classe, nom, "0").split()]


def interieur(classe: str, largeur: float = LARGEUR) -> float:
    """Largeur du contenu d'un bloc du modèle : sa largeur (width, sinon `largeur`) moins ses marges intérieures."""
    p = longueurs(classe, "padding")
    droite = p[1] if len(p) > 1 else p[0]
    gauche = p[3] if len(p) == 4 else droite
    return (longueurs(classe, "width")[0] or largeur) - gauche - droite


def colonne(classe: str, rang=0, n: int | None = None, largeur: float | None = None) -> float:
    """Largeur d'une colonne d'une grille du modèle (pistes en px et 1fr ; n pistes 1fr si le contenu les compte)."""
    pistes = ["1fr"] * n if n else propriete(classe, "grid-template-columns").split()
    ecart = longueurs(classe, "gap")[-1]
    fixe = sum(float(p[:-2]) for p in pistes if p.endswith("px"))
    fr = ((largeur or interieur(classe)) - fixe - ecart * (len(pistes) - 1)) / max(1, sum(p == "1fr" for p in pistes))
    return float(pistes[rang][:-2]) if pistes[rang].endswith("px") else fr


def taille(classe: str, texte, dispo: float, base: float | None = None) -> str:
    """font-size en ligne pour un grand texte : taille de la classe du modèle (ou `base`, déjà adaptée à un texte
    long), réduite juste assez pour que le mot le plus long tienne dans `dispo` px, sans jamais couper un mot.
    Rien quand la taille du modèle convient. Mesure : table de chasse Raleway par graisse du rendu PPTX."""
    from support_pptx import taille_ajustee

    modele = longueurs(classe, "font-size")[0]
    espacement = propriete(classe, "letter-spacing", "0em")
    t = taille_ajustee(str(texte or ""), dispo, base or modele, int(propriete(classe, "font-weight", "400")),
                       float(espacement[:-2] or 0))
    return "font-size:{:g}px".format(t) if t != modele else ""


def titre(texte, dispo: float, classe: str = H2, base: float | None = None, balise="h2") -> str:
    """Grand titre du modèle (classe `classe`), réduit seulement si un mot ne tient pas dans `dispo` px."""
    return '<{b} class="{}"{}>{}</{b}>'.format(classe, en_ligne(taille(classe, texte, dispo, base)), esc(texte), b=balise)


@lru_cache(maxsize=None)
def icone(nom: str) -> str:
    """Icône Lucide en data URI, tracée dans la couleur du texte des slides du modèle.

    Le modèle pose ses icônes en image (noires, couleur par défaut d'un SVG) ; le skill les trace dans la
    couleur du texte de la slide, celle du cadre des stickers. Les icônes blanches du modèle (filtre
    invert de leur classe) gardent le SVG d'origine : ch.icone_data_uri.
    """
    chemin = ch.DOSSIER_CHARTE / "icones" / "{}.svg".format(nom)
    if not chemin.exists():
        return ch.icone_data_uri(nom)
    svg = chemin.read_text(encoding="utf-8").replace('stroke="currentColor"', 'stroke="{}"'.format(propriete(SECTION, "color")))
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


def en_ligne(*declarations: str) -> str:
    """Attribut style des seules propriétés qui dépendent du contenu (rien si aucune)."""
    texte = ";".join(d for d in declarations if d)
    return ' style="{}"'.format(texte) if texte else ""


def colonnes(n: int) -> str:
    return "grid-template-columns:repeat({},1fr)".format(n)


def g(texte, classe: str | None = GRAS) -> str:
    """Texte avec **gras** → <strong> de la classe du modèle (sans classe : gras hérité du contexte)."""
    attribut = ' class="{}"'.format(classe) if classe else ""
    return "".join(
        "<strong{}>{}</strong>".format(attribut, _html.escape(m)) if gras else _html.escape(m)
        for m, gras in ch.segments_gras(texte or "")
    )


def puce(texte: str, li="sf-5fe0d0", carre="sf-32d39d") -> str:
    """Point de liste du modèle : carré de couleur, puis le texte."""
    return '<li class="{}"><span class="{}"></span><span>{}</span></li>'.format(li, carre, texte)


def point(p) -> str:
    """Point de liste : « texte » ou {label, texte, lien} → <strong>label</strong> : texte (lien discret)."""
    if isinstance(p, dict):
        label, texte = p.get("label", ""), g(p.get("texte", ""))
        if p.get("lien"):
            texte = '<a class="lk" href="{}">{}</a>'.format(_html.escape(p["lien"], quote=True), texte)
        return ('<strong class="{}">{}</strong>&nbsp;: {}'.format(GRAS, esc(label), texte)) if label else texte
    return g(p)


# ---------------------------------------------------------------- images (composant image-slot du modèle)


def slot(classe: str, url: str | None, libelle: str, attributs="", contain=False, contenu="") -> str:
    """<image-slot> du modèle : image posée (cover, ou contain pour une capture), ou emplacement vide."""
    if url:
        return '<image-slot class="{}"{}{} style="background-image:url(&quot;{}&quot;)">{}</image-slot>'.format(
            classe, attributs, ' fit="contain"' if contain else "", _html.escape(url, quote=True), contenu
        )
    return '<image-slot class="{} vide"{}><i style="--i:url({})"></i><span>{}</span>{}</image-slot>'.format(
        classe, attributs, ch.icone_data_uri("image"), esc(libelle), contenu
    )


def photo(url: str | None, classe="sf-61be7c") -> str:
    """Photo en « cover », sans filtre (seules la couverture et « Questions » sont saturées)."""
    return slot(classe, url, "Photo", "" if url else ' radius="16"')


def visuel(url: str | None, libelle: str, rayon=16) -> str:
    """Capture ou schéma (contain), coins arrondis ; emplacement vide si pas d'image."""
    return slot("sf-61be7c", url, libelle, ' radius="{}"'.format(rayon), contain=True)


def sticker(cadre: str, fond: str, dessin: str, nom: str | None = None) -> str:
    """Sticker du modèle (classes du cadre, du fond et de l'icône) ; nom None = icône de la catégorie."""
    image = en_ligne("background-image:url({})".format(icone(nom))) if nom else ""
    return '<div class="{}" aria-hidden="true"><div class="{}"><div class="{}"{}></div></div></div>'.format(
        cadre, fond, dessin, image
    )


def pied(intitule: str, couleur=False) -> str:
    """Pied du modèle : logo PNG du design system (marges transparentes comprises), numéro de slide."""
    if couleur:
        return '<div class="sf-b9acd7"><span>{}</span><img class="sf-7e461f" src="{}" alt="Skazy Formation"><span class="sf-e563d3" data-pn></span></div>'.format(
            esc(intitule), ch.logo_data_uri("blanc")
        )
    return '<div class="sf-ee9ac1"><span>{}</span><img class="sf-a0c7cb" src="{}" alt="Skazy Formation"><span class="sf-81a087" data-pn></span></div>'.format(
        esc(intitule), ch.logo_data_uri("couleur")
    )


def mailto(email: str) -> str:
    """Adresse e-mail en lien discret (couleur héritée), comme dans le modèle."""
    return '<a class="lk" href="mailto:{}">{}</a>'.format(_html.escape(str(email).strip(), quote=True), esc(email))


def colorer_code(code: str) -> str:
    """Coloration du modèle : FONCTION( en couleur de catégorie, "chaînes" en jaune."""
    sortie = _html.escape(code or "")
    sortie = re.sub(r"(&quot;.*?&quot;|'.*?')", r'<span class="sf-f1f8dc">\1</span>', sortie)
    sortie = re.sub(r"\b([A-Z][A-Z0-9_.]{1,})(?=\()", r'<span class="sf-ce0590">\1</span>', sortie)
    return sortie


# ---------------------------------------------------------------- mises en page


def couverture(s, f):
    return """<div class="sf-35ef55" style="--cover:url(&quot;{photo}&quot;)"></div>
<div class="sf-bc4cec"></div>
<div class="sf-147da3">
<div role="img" aria-label="Skazy Formation" class="sf-4059b6"></div>
<div class="sf-ec4210">
{intitule}
<div class="sf-e5977c"><span class="sf-6b3f8e">{cat}</span><span class="sf-6b3f8e">{niveau}</span></div>
<div class="sf-3a8463">{duree}</div>
</div>
<div class="sf-39ba17"><div class="sf-e3ec02">{formateur}</div><div>{email}</div></div>
</div>""".format(
        photo=_html.escape(s.get("photo") or f["_couverture"], quote=True),
        intitule=titre(f["intitule"], interieur("sf-147da3"), "sf-3ff854", balise="h1"),
        cat=esc(f["categorie"]),
        niveau=esc(f["niveau"]),
        duree=esc(f["duree"]),
        formateur=esc(f["formateur"]),
        email=mailto(f["email"]),
    )


def faisons_connaissance(s, f):
    infos = "".join(puce(point(x), "sf-bf85f5", "sf-a4b773") for x in s.get("infos") or [])
    tour = "".join(
        '<div class="sf-b0e840"><span class="sf-be8a95">{}</span><span class="sf-1178dd">{}</span></div>'.format(k, g(t))
        for k, t in enumerate(s["tourDeTable"], 1)
    )
    if s.get("photo"):
        portrait = slot("sf-2514c4", s["photo"], "Photo", ' shape="circle"')
    else:
        portrait = '<image-slot class="sf-2514c4 vide" shape="circle"><i style="--i:url({})"></i></image-slot>'.format(
            ch.icone_data_uri("user-round")
        )
    return """<div class="sf-553991">
<div class="sf-c62e4b">
{titre}
<div class="sf-5c9e88">{portrait}<div><div class="sf-9c0c82">{formateur}</div><div class="sf-b7f8e0">{role}</div></div></div>
<ul class="sf-7e47d1">{infos}</ul>
</div>
<div class="sf-5413e6">
<div class="{surtitre}">Tour de table</div>
{tour}
</div>
</div>""".format(
        titre=titre(s.get("titre") or "Faisons connaissance", colonne("sf-553991")), portrait=portrait, formateur=esc(f["formateur"]),
        role=esc(f["role"]), infos=infos, surtitre=SURTITRE, tour=tour,
    ) + (sticker("sf-d1b108", "sf-b271cb", "sf-3f4783", "hand") if f["stickers"] else "")


def objectifs(s, f):
    serres = en_ligne("font-size:30px" if len(s["objectifs"]) > 4 else "")
    lignes = "".join(
        '<div class="sf-695da1"><span class="sf-5d25c9">{:02d}</span><span class="sf-b6750a"{}>{}</span></div>'.format(
            k, serres, g(o, "sf-00fe65")
        )
        for k, o in enumerate(s["objectifs"], 1)
    )
    return """<div class="sf-11d674">{photo}</div>
<div class="sf-33b79d">
{titre}
<p class="sf-bc7868">{intro}</p>
<div class="sf-2ff816">{lignes}</div>
</div>""".format(
        photo=photo(s.get("photo")), titre=titre(s.get("titre") or "Objectifs pédagogiques", interieur("sf-33b79d")),
        intro=esc(s.get("intro") or "À la fin de la formation, vous serez capable de :"), lignes=lignes,
    ) + (sticker("sf-bb5024", "sf-287a5d", "sf-88f54a", "target") if f["stickers"] else "")


def programme(s, f):
    parties = s["parties"]
    serre = en_ligne("padding-block:14px;font-size:28px" if len(parties) > 8 else "")
    lignes = "".join(
        '<div class="{ligne}"{serre}><span class="sf-2b9532">{k}.</span><span class="sf-eed0f8">{titre}</span><span class="sf-d39b0d">{duree}</span></div>'.format(
            ligne="sf-4a712a" if k == len(parties) else "sf-c6927c", serre=serre, k=k,
            titre=esc(p["titre"] if isinstance(p, dict) else p), duree=esc(p.get("duree", "") if isinstance(p, dict) else ""),
        )
        for k, p in enumerate(parties, 1)
    )
    return """<div class="sf-701ade">
{titre}
<p class="sf-3c4443">{duree}</p>
<div class="sf-fdb105"><div class="sf-cd421a">{photo}</div></div>
</div>
{sticker}
<div class="sf-c194e5">{lignes}</div>""".format(
        titre=titre(s.get("titre") or "Programme", interieur("sf-701ade")), duree=esc(s.get("duree") or f["duree"]),
        photo=photo(s.get("photo")),
        sticker=sticker("sf-c5a2c8", "sf-75448f", "sf-35241d") if f["stickers"] else "", lignes=lignes,
    )


def chapitre(s, f):
    points = "".join('<li class="sf-06e597"><span class="sf-98e742"></span>{}</li>'.format(g(p)) for p in s.get("points") or [])
    duree = '<span class="sf-8c22a3">{}</span>'.format(esc(s["duree"])) if s.get("duree") else ""
    return """<div class="sf-11d674">{photo}</div>
<div class="sf-a52777">
<div class="sf-69957c"><span class="sf-69df12">{num:02d}</span>{duree}</div>
{titre}
<ul class="sf-9d7b91">{points}</ul>
</div>""".format(
        photo=photo(s.get("photo")), num=int(s["numero"]), duree=duree,
        titre=titre(s["titre"], interieur("sf-a52777"), "sf-155fa0", 72 if len(s["titre"]) > 40 else None), points=points,
    ) + (sticker("sf-e22c1f", "sf-bbe8d1", "sf-35241d") if f["stickers"] else "")


def contenu(s, f):
    points = "".join(puce(point(p)) for p in s.get("points") or [])
    texte = '<p class="sf-768979">{}</p>'.format(g(s["texte"])) if s.get("texte") else ""
    return """<div class="sf-0a4cf0">
<div class="sf-a99ac7">
{titre}
{texte}
<ul class="sf-17fcf3">{points}</ul>
</div>
<div class="sf-c5ab9b">{visuel}</div>
</div>""".format(titre=titre(s["titre"], colonne("sf-0a4cf0")), texte=texte, points=points,
                 visuel=visuel(s.get("image"), s.get("legendeImage") or "Capture d'écran ou schéma"))


def chiffre_ajuste(chiffre: str, unite: str) -> tuple[str, str]:
    """font-size en ligne du chiffre clé et de son unité (« 73 » et « % ») : taille du modèle, réduite pour un
    chiffre long, puis juste assez pour que le mot le plus large (le dernier porte l'unité) tienne dans sa colonne.
    L'unité garde la proportion du modèle."""
    from support_pptx import largeur

    modele = longueurs("sf-f6719a", "font-size")[0]
    proportion = longueurs("sf-5c7395", "font-size")[0] / modele
    espacement = float(propriete("sf-f6719a", "letter-spacing")[:-2])  # en em, hérité en px par l'unité
    t = modele if len(chiffre) <= 3 else (220 if len(chiffre) <= 5 else 160)
    mots = [m for m in re.split(r"[ \n]+", ch.typographie(chiffre)) if m] or [""]  # l'espace insécable lie

    def plus_large(t: float) -> float:
        tu = t * proportion
        derniere = largeur(mots[-1], t, 800, espacement=espacement) + largeur(unite, tu, 800, espacement=espacement / proportion)
        return max([largeur(m, t, 800, espacement=espacement) for m in mots[:-1]] + [derniere])

    dispo = colonne("sf-e31056") * 0.98
    if plus_large(t) > dispo:
        t = math.floor(t * dispo / plus_large(t))
    if t == modele:
        return "", ""
    return "font-size:{:g}px".format(t), "font-size:{}px".format(round(t * proportion))


def chiffre_cle(s, f):
    reperes = "".join(
        '<div class="sf-167e99"><span class="sf-eb0379">{}</span><span class="sf-30cf9b">{}</span></div>'.format(
            esc(x.get("valeur")), g(x.get("texte"))
        )
        for x in s.get("reperes") or []
    )
    source = '<span class="sf-a271c7">Source&nbsp;: {}</span>'.format(esc(s["source"])) if s.get("source") else ""
    chiffre, unite = str(s["chiffre"]), str(s.get("unite", ""))
    grand = chiffre_ajuste(chiffre, unite)
    return """<div class="sf-e31056">
<div class="sf-d55390"><span class="sf-f6719a"{taille}>{chiffre}<span class="sf-5c7395"{tu}>{unite}</span></span><span class="sf-7c5d06">{phrase}</span></div>
<div class="sf-67d22e"><p class="sf-0df0ae">{explication}</p><div class="sf-fe27dd">{reperes}</div>{source}</div>
</div>""".format(taille=en_ligne(grand[0]), chiffre=esc(chiffre), tu=en_ligne(grand[1]), unite=esc(unite), phrase=g(s["phrase"], "sf-00fe65"),
                 explication=g(s.get("explication", "")), reperes=reperes, source=source)


def frise(s, f):
    etapes = s["etapes"]
    cols = []
    dispo = colonne("sf-ba0db5", n=len(etapes), largeur=interieur("sf-15a01c"))  # une colonne par étape
    for k, e in enumerate(etapes):
        derniere = k == len(etapes) - 1
        date = "sf-cbb07a" if derniere else "sf-2e8d89"
        bloc = '<div class="{}"><span class="{}"{}>{}</span><span class="sf-f6cca1">{}</span></div>'.format(
            "sf-203cf8" if k % 2 == 0 else "sf-e157a8", date, en_ligne(taille(date, e.get("date"), dispo)), esc(e.get("date")), g(e.get("texte")))
        rond = '<span class="{}"></span>'.format("sf-75e660" if derniere else "sf-7c2017")
        haut, bas = (bloc, "<div></div>") if k % 2 == 0 else ("<div></div>", bloc)
        cols.append('<div class="sf-d71b61">{}{}{}</div>'.format(haut, rond, bas))
    return """<div class="sf-15a01c">
<h2 class="{h2}">{titre}</h2>
<p class="sf-2751dd">{intro}</p>
<div class="sf-ba0db5"{n}>
<div class="sf-b7764e"></div>
{cols}
</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), intro=g(s.get("intro", "")), n=en_ligne(colonnes(len(etapes))), cols="".join(cols))


def graphique(s, f):
    barres = s["barres"]
    valeurs = [float(b.get("valeur", 0)) for b in barres]
    maxi = max(valeurs) or 1
    cible = s.get("miseEnAvant", len(barres) - 1)
    # Barre : classe de la 1re barre du modèle (grise) ou de la barre mise en avant ; hauteur selon la valeur.
    barres_html = "".join(
        '<div class="sf-f64a14"><span class="{c}">{v}</span><div class="{b}" style="height:calc((100% - 56px) * {h:.2f})"></div></div>'.format(
            c="sf-245f55" if k == cible else "sf-a2d6d7", v=esc(b.get("affichage") or _nombre(b.get("valeur"))), h=valeurs[k] / maxi,
            b="sf-0b720d" if k == cible else "sf-5db468")
        for k, b in enumerate(barres)
    )
    labels = "".join('<span class="sf-0dedc5">{}</span>'.format(esc(b.get("label"))) for b in barres)
    source = '<span class="sf-a271c7">Source&nbsp;: {}</span>'.format(esc(s["source"])) if s.get("source") else ""
    return """<div class="sf-d28f9b">
<div class="sf-9ef6d9">
{titre}
<div class="sf-7c101a"{n}>{barres}</div>
<div class="sf-89aee2"{n}>{labels}</div>
</div>
<div class="sf-dc3ee7"><span class="{surtitre}">{surtitre_txt}</span><span class="sf-b59cdf"{grand}>{chiffre}</span><p class="sf-b8f277">{message}</p>{source}</div>
</div>""".format(titre=titre(s["titre"], colonne("sf-d28f9b")), n=en_ligne(colonnes(len(barres))), barres=barres_html, labels=labels, surtitre=SURTITRE,
                 surtitre_txt=esc(s.get("surtitre") or "À retenir"), chiffre=esc(s.get("chiffre", "")),
                 grand=en_ligne(taille("sf-b59cdf", s.get("chiffre", ""), colonne("sf-d28f9b", 1))), message=g(s.get("message", "")), source=source)


def _nombre(v) -> str:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v or "")
    return ("{:,.0f}" if x == int(x) else "{:,.1f}").format(x).replace(",", " ").replace(".", ",")


def image(s, f):
    return """{fond}
<div class="sf-01367a"><span class="{surtitre}">{surtitre_txt}</span><span class="sf-69a829">{titre}</span><span class="sf-18ed2c">{texte}</span></div>
<span class="sf-ab188d" data-pn></span>""".format(
        fond=photo(s.get("image"), "sf-b93df6"), surtitre=SURTITRE, surtitre_txt=esc(s.get("surtitre") or "Légende"),
        titre=esc(s["titre"]), texte=g(s.get("texte", "")))


def texte(s, f):
    paragraphes = "".join('<p class="sf-f3552b">{}</p>'.format(g(p)) for p in s["paragraphes"])
    return """<div class="sf-8de91b">
<div class="sf-d55390"><span class="sf-c639d2"></span>{titre}<p class="sf-fa85a6">{intro}</p></div>
<div class="sf-80020d"{cols}>{paragraphes}</div>
</div>""".format(titre=titre(s["titre"], colonne("sf-8de91b")), intro=g(s.get("intro", "")),
                 cols=en_ligne("column-count:1" if len(s["paragraphes"]) <= 1 else ""), paragraphes=paragraphes)


def citation(s, f):
    auteur = s.get("auteur") or ""
    return """<div class="sf-e5be35">
<span class="sf-b81946">«</span>
<p class="sf-99aeb9"{grand}>{citation}</p>
<div class="sf-b0e840"><span class="sf-0c1005"><img class="sf-7021d6" src="{icone}" alt=""></span><div class="sf-2ddfee">{auteur}</div></div>
</div>""".format(grand=en_ligne(taille("sf-99aeb9", s["citation"], min(interieur("sf-e5be35"), longueurs("sf-99aeb9", "max-width")[0]),
                                       60 if len(s["citation"]) > 100 else None)), citation=g(s["citation"], "sf-e3ec02"),
                 icone=icone("user-round"), auteur=esc(auteur))


def avant_apres(s, f):
    def cote(d, libelle, pastille):
        return '<div class="sf-d4f7b6"><div class="sf-8f2b69">{}</div><div class="sf-e6b8ce"><span class="{}">{}</span><span class="sf-ef06bf">{}</span></div></div>'.format(
            visuel(d.get("image"), "Capture " + libelle.lower()), pastille, libelle, g(d.get("texte")))

    return """<div class="sf-ff09b9">
<h2 class="{h2}">{titre}</h2>
<div class="sf-c9e7b7">{avant}{apres}</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), avant=cote(s["avant"], "Avant", "sf-090a27"), apres=cote(s["apres"], "Après", "sf-46e33f"))


def notion_cle(s, f):
    termes = "".join(
        '<span class="sf-260485"><code class="sf-18d63c">{}</code>{}</span>'.format(esc(t.get("terme")), g(t.get("definition")))
        for t in s.get("termes") or []
    )
    return """<div class="sf-9fb14f">
<span class="{pastille}">{surtitre}</span>
{titre}
<p class="sf-fd2487">{definition}</p>
<div class="sf-c78185">{termes}</div>
</div>""".format(pastille=PASTILLE, surtitre=esc(s.get("surtitre") or "Notion clé"), titre=titre(s["titre"], interieur("sf-9fb14f"), "sf-39498d", 84 if len(s["titre"]) > 26 else None), definition=g(s["definition"], None), termes=termes)


def code(s, f):
    elements = "".join(
        '<div><code class="sf-779c30">{}</code><br>{}</div>'.format(esc(x.get("code")), g(x.get("texte")))
        for x in s.get("elements") or []
    )
    exemple = ""
    if s.get("exemple"):
        exemple = '<div class="sf-e825d5"></div><span class="sf-8d9346">Exemple</span><pre class="sf-791822">{}</pre>'.format(colorer_code(s["exemple"]))
    resultat = '<span class="sf-1cda80">{}</span>'.format(g(s["resultat"], "sf-729d2f")) if s.get("resultat") else ""
    return """<div class="sf-9d4366">
<div class="sf-a99ac7">
{titre}
<p class="sf-768979">{intro}</p>
<div class="sf-8ae138">{elements}</div>
</div>
<div class="sf-37f820">
<span class="sf-8d9346">{libelle}</span>
<pre class="sf-791822">{syntaxe}</pre>
{exemple}
{resultat}
</div>
</div>""".format(titre=titre(s["titre"], colonne("sf-9d4366")), intro=g(s.get("intro", "")), elements=elements, libelle=esc(s.get("libelle") or "Syntaxe"),
                 syntaxe=colorer_code(s["syntaxe"]), exemple=exemple, resultat=resultat)


def capture(s, f):
    reperes = s["reperes"]
    # Pastilles : classe de la 1re pastille du modèle, placée au repère (x, y en % de la capture).
    pastilles = "".join(
        '<span class="sf-21a34d" style="left:calc({x}% - 32px);top:calc({y}% - 32px)">{k}</span>'.format(
            x=float(r.get("x", 15 + 70 * ((k - 1) % 2))), y=float(r.get("y", 15 + 25 * ((k - 1) // 2))), k=k)
        for k, r in enumerate(reperes, 1)
    )
    legendes = "".join(
        '<div class="sf-dd2223"><span class="sf-e0e675">{k}</span><span class="sf-f6cca1"><strong class="sf-b3851b">{t}</strong>{x}</span></div>'.format(
            k=k, t=esc(r.get("titre")), x=g(r.get("texte")))
        for k, r in enumerate(reperes, 1)
    )
    # Les pastilles se placent sur le cadre de la capture ; sans image, l'emplacement vide occupe tout ce cadre.
    if s.get("image"):
        cadre = slot("sf-61be7c", s["image"], "", ' radius="12"', contain=True, contenu=pastilles)
    else:
        cadre = '<image-slot class="sf-61be7c" radius="12" fit="contain">{}{}</image-slot>'.format(
            slot("sf-b93df6", None, "Capture d'écran à annoter", ' radius="12"'), pastilles)
    return """<div class="sf-f2c06d">
<h2 class="{h2}">{titre}</h2>
<div class="sf-cc08e2">
<div class="sf-b0fef8">{cadre}</div>
<div class="sf-9f1edf">{legendes}</div>
</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), cadre=cadre, legendes=legendes)


def pas_a_pas(s, f):
    etapes = s["etapes"]
    blocs = "".join(
        '<div class="sf-44e002"><div class="sf-20a906">{v}</div><span class="sf-fc003e">{k}</span><p class="sf-7bf723">{t}</p></div>'.format(
            v=visuel((e or {}).get("image") if isinstance(e, dict) else "", "Capture étape {}".format(k), 12),
            k=k, t=g(e.get("texte") if isinstance(e, dict) else e))
        for k, e in enumerate(etapes, 1)
    )
    return """<div class="sf-f66861">
<h2 class="{h2}">{titre}</h2>
<div class="sf-16a7f1"{n}>{blocs}</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), n=en_ligne(colonnes(len(etapes))), blocs=blocs)


def comparatif(s, f):
    a, b = (s["colonnes"] + ["", ""])[:2]
    cellules = '<div class="sf-0e50e5"></div><div class="sf-3e5326">{}</div><div class="sf-99973c">{}</div>'.format(esc(a), esc(b))
    for ligne in s["lignes"]:
        v = (ligne.get("valeurs") or []) + ["", ""]
        cellules += '<div class="sf-f804ba">{}</div><div class="sf-49ab48">{}</div><div class="sf-c09fae">{}</div>'.format(
            esc(ligne.get("critere")), g(v[0]), g(v[1]))
    reco = '<p class="sf-77556a"><strong class="sf-9411a5">Recommandation</strong>&nbsp;: {}</p>'.format(g(s["recommandation"])) if s.get("recommandation") else ""
    return """<div class="sf-8bbc1c">
<h2 class="{h2}">{titre}</h2>
<div class="sf-d76e84">{cellules}</div>
{reco}
</div>""".format(h2=H2, titre=esc(s["titre"]), cellules=cellules, reco=reco)


def raccourcis(s, f):
    items = "".join(
        '<div class="sf-ebf939"><span class="sf-bcce19">{}</span><span class="sf-12f66e">{}</span></div>'.format(
            "+".join('<kbd class="sf-9d977f">{}</kbd>'.format(esc(t)) for t in touches(r)), esc(r.get("action")))
        for r in s["raccourcis"]
    )
    remarque = '<span class="sf-9c1cda">{}</span>'.format(g(s["remarque"])) if s.get("remarque") else ""
    return """<div class="sf-8bbc1c">
<div class="sf-8e456d"><h2 class="{h2}">{titre}</h2>{remarque}</div>
<div class="sf-aa240c">{items}</div>
</div>""".format(h2=H2, titre=esc(s.get("titre") or "Raccourcis à connaître"), remarque=remarque, items=items)


# Encadrés de « Bon à savoir » : libellé, puis classes du modèle (cadre, libellé) de chaque variante.
GENRES = {
    "astuce": ("Astuce", "sf-985f0c", SURTITRE),
    "attention": ("Attention", "sf-009b93", "sf-9904ca"),
    "bonne-pratique": ("Bonne pratique", "sf-424182", "sf-83467c"),
}


def genre(e: dict) -> tuple[str, str, str]:
    cle = ch.normaliser(e.get("genre", "astuce")).replace(" ", "-")
    return GENRES.get(cle, GENRES["astuce"])


def genre_encadre(e: dict) -> tuple[str, str, str]:
    """Pour le PPTX : libellé, fond et encre de l'encadré, lus dans les classes du modèle."""
    libelle, cadre, etiquette = genre(e)
    return libelle, propriete(cadre, "background"), propriete(etiquette, "color")


def bon_a_savoir(s, f):
    blocs = ""
    for e in s["encadres"]:
        libelle, cadre, etiquette = genre(e)
        blocs += '<div class="{}"><span class="{}">{}</span><span class="sf-4f6531">{}</span><p class="sf-5acb09">{}</p></div>'.format(
            cadre, etiquette, esc(e.get("libelle") or libelle), esc(e.get("titre")), g(e.get("texte"), None))
    return """<div class="sf-b4b4b8">
<h2 class="{h2}">{titre}</h2>
<div class="sf-05505c"{n}>{blocs}</div>
</div>""".format(h2=H2, titre=esc(s.get("titre") or "Bon à savoir"), n=en_ligne(colonnes(len(s["encadres"]))), blocs=blocs)


def exercice(s, f):
    consignes = "".join(
        '<li class="sf-f09eb0"><span class="sf-fdc20a">{}</span><span>{}</span></li>'.format(k, g(c))
        for k, c in enumerate(s["consignes"], 1)
    )
    carte = '<div class="sf-5a6e0b"><span class="sf-0dee18">{}</span><span class="{}">{}</span></div>'
    cartes = ""
    if s.get("duree"):
        cartes += carte.format("Durée", "sf-2ddfee", esc(s["duree"]))
    if s.get("fichier"):
        cartes += carte.format("Fichier", "sf-449a9e", esc(s["fichier"]))
    if s.get("livrable"):
        cartes += carte.format("Livrable", "sf-9e616c", g(s["livrable"]))
    if s.get("bonus"):
        cartes += '<div class="sf-771b20"><span class="sf-1f8ce9">Pour aller plus loin</span><span class="sf-51080c">{}</span></div>'.format(g(s["bonus"], "sf-e3ec02"))
    return """<div class="sf-e0e59c"></div>
<div class="sf-fd2dbd">
<div class="sf-d55390">
<span class="{pastille}">Exercice {num}</span>
{titre}
<p class="sf-38d0fe">{contexte}</p>
<ol class="sf-47e64a">{consignes}</ol>
</div>
<div class="sf-785898">{cartes}</div>
</div>""".format(pastille=PASTILLE, num=s["numero"], titre=titre(s["titre"], colonne("sf-fd2dbd"), "sf-f62ea3"),
                 contexte=g(s.get("contexte", "")), consignes=consignes, cartes=cartes)


def exercice_etapes(s, f):
    etapes = "".join(
        '<div class="sf-20cd43"><span class="sf-b594b4">{}</span><span class="sf-03f6b1">{}</span><span class="sf-18ed2c">{}</span></div>'.format(
            k, esc(e.get("titre") if isinstance(e, dict) else ""), g(e.get("texte") if isinstance(e, dict) else e))
        for k, e in enumerate(s["etapes"], 1)
    )
    infos = ""
    for libelle, cle, classe in (("Fichier", "fichier", "sf-416b59"), ("Modalité", "modalite", ""), ("Livrable", "livrable", "")):
        if s.get(cle):
            valeur = '<span class="{}">{}</span>'.format(classe, g(s[cle])) if classe else g(s[cle])
            infos += '<span><strong class="sf-9411a5">{}</strong>&nbsp;: {}</span>'.format(libelle, valeur)
    duree = str(s.get("duree", "")).strip()
    # « 40 minutes » : nombre et unité, séparés par n'importe quelle espace (insécable comprise) ; « 1 h 30 » : d'un bloc.
    nombre, unite = (re.split(r"[\s\u00a0\u202f]+", duree, maxsplit=1) + [""])[:2]
    if not unite or re.search(r"[\s\u00a0\u202f]", unite):
        nombre, unite = duree, ""
    return """<div class="sf-541127">
<div class="sf-1252b5">
<div class="sf-f11511"><span class="{pastille}">Exercice {num}</span>{titre}<p class="sf-38d0fe">{contexte}</p></div>
<div class="sf-885e50"><span class="sf-dce7d8"{long}>{nombre}</span><span class="sf-6f7ed2">{unite}</span></div>
</div>
<div class="sf-d1541b"{n}>{etapes}</div>
<div class="sf-02d2b6">{infos}</div>
</div>""".format(pastille=PASTILLE, num=s["numero"], titre=titre(s["titre"], longueurs("sf-f11511", "max-width")[0], "sf-f62ea3"),
                 contexte=g(s.get("contexte", "")), long=en_ligne("font-size:56px" if len(nombre) > 3 else ""), nombre=esc(nombre or "–"),
                 unite=esc(unite or ("minutes" if nombre.isdigit() else "")),
                 n=en_ligne(colonnes(len(s["etapes"]))), etapes=etapes, infos=infos)


def quiz(s, f):
    props = s["propositions"]
    tuiles = ""
    for k, p in enumerate(props):
        if s["_reponse"] and k == s["bonne"]:
            # « Bonne réponse » sur une ligne, quelle que soit la longueur de la proposition : espace insécable.
            tuiles += '<div class="sf-66c63a"><span class="sf-f84e62">{l}</span><span class="sf-135317">{t}</span><span class="sf-0bfdad">Bonne&nbsp;réponse</span></div>'.format(l="ABCD"[k], t=esc(p))
        else:
            tuiles += '<div class="sf-759b1f"><span class="sf-639b76">{l}</span><span class="sf-135317">{t}</span></div>'.format(l="ABCD"[k], t=esc(p))
    return """<div class="sf-ff09b9">
<div class="sf-57a094"><span class="sf-0415e9">Quiz</span><span class="sf-bcc324">Question {num} sur {total}</span></div>
<h2 class="sf-d09ace">{question}</h2>
<div class="sf-53490d" style="grid-template-rows:repeat({lignes},1fr)">{tuiles}</div>
</div>""".format(num=s.get("numero", 1), total=s.get("total", 1), question=esc(s["question"]), lignes=(len(props) + 1) // 2, tuiles=tuiles)


def a_retenir(s, f):
    messages = "".join(
        '<div class="sf-bde44c"><span class="sf-bdee0a">{}</span><p class="sf-6aed6e">{}</p></div>'.format(k, g(m))
        for k, m in enumerate(s["messages"], 1)
    )
    return """<div class="sf-f39d3f">
{titre}
<span class="sf-d742a1">{sous_titre}</span>
</div>
<div class="sf-c9ca6b">{messages}</div>""".format(
        titre=titre(s.get("titre") or "À retenir", interieur("sf-f39d3f"), "sf-7f284f"), sous_titre="<br>".join(esc(x) for x in str(s.get("sousTitre") or "").split("\n")), messages=messages)


def ressources(s, f):
    blocs = ""
    for x in s["ressources"]:
        lien = x.get("lien") or ""
        skazy = x.get("skazy") or "skazy.nc" in lien
        affiche = re.sub(r"^https?://(www\.)?", "", lien).rstrip("/")
        blocs += '<div class="{}"><span class="sf-4fe681">{}</span><span class="sf-a650a0">{}</span>{}</div>'.format(
            "sf-d989c9" if skazy else "sf-4ac9c7", esc(x.get("titre")), g(x.get("texte")),
            '<a href="{}" class="sf-8816ec">{}</a>'.format(_html.escape(lien, quote=True), esc(affiche)) if lien else "")
    return """<div class="sf-b4b4b8">
<h2 class="{h2}">{titre}</h2>
<div class="sf-17c390">{blocs}</div>
</div>""".format(h2=H2, titre=esc(s.get("titre") or "Pour continuer"), blocs=blocs)


def evaluation(s, f):
    qr = visuel(s.get("qrCode"), "QR code", 12)
    return """<div class="sf-b4b4b8">
<h2 class="{h2}">{titre}</h2>
<div class="sf-e65200">
<div class="sf-7035b1"><span class="{surtitre}">1 · Quiz final</span><span class="sf-c000eb">Mesurez votre progression</span><p class="sf-18aa66">Quelques questions pour vérifier ce que vous avez retenu de la formation.</p><span class="sf-55a134">{acces}</span></div>
<div class="sf-0f346f"><div class="sf-b9d24a"><span class="{surtitre}">2 · Satisfaction</span><span class="sf-c000eb">Trois minutes, anonyme</span><p class="sf-5acb09">Vos retours font évoluer la formation. Scannez le QR code.</p></div><div class="sf-2e8d2c">{qr}</div></div>
</div>
<p class="sf-77556a">{message}</p>
</div>""".format(h2=H2, titre=esc(s.get("titre") or "Votre avis compte"), surtitre=SURTITRE,
                 acces=esc(s.get("quiz") or "Sur kahoot.it, code affiché à l'écran"), qr=qr,
                 message=esc(s.get("message") or "Votre attestation de fin de formation vous parvient par e-mail."))


def questions(s, f):
    return """<div class="sf-97d93b" style="background-image:url(&quot;{photo}&quot;)"></div>
<div class="sf-bc4cec"></div>
<div class="sf-147da3">
<div role="img" aria-label="Skazy Formation" class="sf-4059b6"></div>
{titre}
<div class="sf-39ba17"><div class="sf-e3ec02">{formateur}</div><div>{email}</div></div>
</div>""".format(photo=_html.escape(ch.url_photo(s.get("photo") or ch.CHARTE["photoQuestions"]), quote=True),
                 titre=titre(s.get("titre") or "Avez-vous des questions ?", interieur("sf-147da3"), "sf-2596f1"), formateur=esc(f["formateur"]), email=mailto(f["email"]))


def battle(s, f):
    def equipe(nom, cadre):
        return '<div class="{}"><span class="sf-326561">{}</span><div class="sf-be2653"><span class="sf-f306ad">Nom de l\'équipe</span><div class="sf-46570a"></div></div><div class="sf-11e585"><span class="sf-f306ad">Score</span><div class="sf-ce36df"></div></div></div>'.format(
            cadre, nom)
    regles = "".join(
        '<div class="sf-166111"><span class="sf-e49986">{}</span><span class="sf-cbd31c">{}</span></div>'.format(k, g(r))
        for k, r in enumerate(s["regles"], 1)
    )
    return """<div class="sf-541127">
<div class="sf-8e456d"><div class="sf-21e642"><span class="sf-ab4fb4"><img class="sf-b5b165" src="{zap}" alt="">Battle</span><h2 class="{h2}">{titre}</h2></div><span class="sf-1cd374">{accroche}</span></div>
<div class="sf-b8cfe9">{a}<div class="sf-0e1a6d"><span class="sf-eab361">VS</span></div>{b}</div>
<div class="sf-4e3b06"{n}>{regles}</div>
</div>""".format(zap=ch.icone_data_uri("zap"), h2=H2, titre=esc(s.get("titre") or "Battle de questions"),
                 accroche=esc(s.get("accroche") or "Deux équipes, un objectif : piéger l'autre."),
                 a=equipe("Équipe A", "sf-2284e6"), b=equipe("Équipe B", "sf-f45856"),
                 n=en_ligne(colonnes(len(s["regles"]))), regles=regles)


# Pôles du groupe : couleur = encre (-ink) du jeton de la catégorie correspondante, vert foncé pour la formation
# (utilisées par le PPTX ; le HTML prend la classe du pôle dans le modèle, CLASSES_POLES).
POLES = [
    ("com", ch.CHARTE["jetons"]["cat-ia-ink"], "Social media, publicité digitale, webmarketing, SEO, SEA, identité visuelle, print et édition"),
    ("numérique", ch.CHARTE["jetons"]["cat-dev-ink"], "Développement de logiciels, web et mobile, UX/UI design, hébergement"),
    ("data", ch.CHARTE["jetons"]["cat-data-ink"], "Informatique décisionnelle, business intelligence, AMOA, modélisation, intégration et restitution de données"),
    ("formation", C["primaireFonce"], "Webmarketing, développement, data, web, gestion de projet, design, bureautique, NoCode et Intelligence Artificielle"),
]
CLASSES_POLES = ["sf-368ff5", "sf-61ca3e", "sf-9ae266", "sf-428ff7"]


def accompagnement_360(s, f):
    poles = "".join(
        '<div class="sf-17f5c7"><span class="sf-fd7db1">skazy<span class="{}">{}</span></span><p class="sf-7f4edb">{}</p></div>'.format(classe, esc(n), esc(t))
        for (n, _, t), classe in zip(POLES, CLASSES_POLES)
    )
    return """<div class="sf-f66861">
<div><h2 class="{h2}">Skazy</h2><p class="sf-432496">Accompagnement 360°</p></div>
<div class="sf-f6e72d">{poles}</div>
</div>""".format(h2=H2, poles=poles) + (sticker("sf-01011a", "sf-b271cb", "sf-7fe7e4", "rocket") if f["stickers"] else "")


# Tuiles des catégories (ordre alphabétique de la charte, comme le modèle) : classe de la tuile du modèle.
TUILES = {
    "bureautique": "sf-ab697a", "data": "sf-88c591", "dev": "sf-5842cd", "gestion": "sf-193d99", "graphisme": "sf-fddbe2",
    "ia": "sf-0cf6da", "marketing": "sf-b9453b", "nocode": "sf-e5d580", "web": "sf-9854a6",
}


def autres_formations(s, f):
    tuiles = ""
    for c in ch.CHARTE["categories"]:
        blanc = c["surCouleur"].upper() == "#FFFFFF"
        tuiles += '<div class="{tuile}"><div class="sf-f24931"><img class="{icone}" src="{ic}" alt=""></div><span class="sf-46d049">{nom}</span></div>'.format(
            tuile=TUILES[c["slug"]], icone="sf-769ae1" if blanc else "sf-f20416",
            ic=ch.icone_data_uri(c["icone"]) if blanc else icone(c["icone"]), nom=esc(c["nom"]))
    tuiles += '<div class="sf-c16d60"><span class="sf-5f8926">Tout le catalogue</span><a href="{url}" class="sf-6b527d">{site}</a></div>'.format(
        url=ch.CONTACT["url"], site=ch.CONTACT["site"])
    texte = s.get("texte") or "**L'IA au quotidien** : ChatGPT, Claude, Copilot, Mistral, Gemini. Et aussi Make, Canva, Figma, Power BI, Microsoft 365."
    return """<div class="sf-745768">
<div><h2 class="{h2}">Nos autres formations</h2><p class="sf-ae3ad1">Le catalogue complet&nbsp;: <a href="{url}" class="sf-a5208f">{site}</a></p></div>
<div class="sf-83822c">{tuiles}</div>
<p class="sf-86c6ee">{texte}</p>
</div>""".format(h2=H2, url=ch.CONTACT["url"], site=ch.CONTACT["site"], tuiles=tuiles, texte=g(texte))


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
# Classe de la slide (<section>) dans le modèle : SECTION (fond blanc), sauf ces mises en page.
FOND ={"citation": "sf-4f8d48", "notion-cle": "sf-daa442", "image": "sf-e016d1"}

# CSS propre au skill : le deck à l'écran (mise à l'échelle, une slide visible, barre de navigation, notes
# formateur) et l'impression, que le modèle confie à deck-stage.js (runtime Claude Design). Puis le composant
# image-slot du modèle, runtime lui aussi et sans classe exportée : image posée et emplacement vide (.vide).
CSS = """
html,body{height:100%;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.scene{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;overflow:hidden}
.deck{position:relative;width:1920px;height:1080px;flex-shrink:0;transform-origin:center center;counter-reset:sf}
.slide{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;counter-increment:sf;visibility:hidden}
.slide.active{visibility:visible}
image-slot{display:block;position:relative;background:var(--color-doc-photo) center/cover no-repeat}
image-slot[fit=contain]{background-color:transparent;background-size:contain}
image-slot[shape=circle]{border-radius:50%}
image-slot[radius="12"]{border-radius:12px}
image-slot[radius="16"]{border-radius:16px}
.vide{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:16px;background:var(--color-doc-bg-soft);border:3px dashed var(--color-doc-bar);color:#9A9AA6;font-size:24px;font-weight:600;text-align:center}
.vide i{width:56px;height:56px;background:#B5B5BD;-webkit-mask:var(--i) center/contain no-repeat;mask:var(--i) center/contain no-repeat}
.vide[shape=circle]{padding:0;border:0;background:var(--ct)}
.vide[shape=circle] i{width:96px;height:96px;background:var(--ci)}
.barre{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:5;display:flex;align-items:center;gap:6px;background:rgba(24,24,28,.88);color:#fff;border-radius:999px;padding:6px;font:600 14px Raleway,system-ui,sans-serif;opacity:.15;transition:opacity .2s}
.barre:hover,.barre:focus-within{opacity:1}
.barre button{font:inherit;color:#fff;background:transparent;border:0;border-radius:999px;padding:8px 14px;cursor:pointer}
.barre button:hover,.barre button:focus-visible{background:rgba(255,255,255,.16);outline:none}
.barre output{min-width:64px;text-align:center}
.notes{position:fixed;left:16px;right:16px;bottom:72px;z-index:5;max-height:34vh;overflow:auto;background:#fff;color:#1F1F24;border-radius:16px;padding:18px 22px;font:500 17px/1.5 Raleway,system-ui,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.4);white-space:pre-wrap}
.notes[hidden]{display:none}
.notes b{display:block;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#6E6E78;margin-bottom:6px}
@page{size:1920px 1080px;margin:0}
@media print{
  html,body{height:auto;background:#fff}
  .scene{position:static;display:block;overflow:visible}
  .deck{transform:none!important;width:auto;height:auto}
  .slide{position:relative;visibility:visible;break-after:page}
  .barre,.notes{display:none!important}
}
"""

JS = """
(() => {
  const deck = document.querySelector('.deck');
  const slides = [...document.querySelectorAll('.slide')];
  const compteur = document.querySelector('.barre output');
  const notes = document.querySelector('.notes');
  let i = Math.max(0, Math.min(slides.length - 1, (parseInt(location.hash.slice(1), 10) || 1) - 1));
  const ajuster = () => {
    const e = Math.min(innerWidth / 1920, innerHeight / 1080);
    deck.style.transform = 'scale(' + e + ')';
  };
  const afficher = (n) => {
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, k) => s.classList.toggle('active', k === i));
    compteur.textContent = (i + 1) + ' / ' + slides.length;
    const texte = slides[i].querySelector('template.notes-slide');
    notes.innerHTML = '<b>Notes formateur</b>' + (texte ? texte.innerHTML : 'Pas de notes pour cette slide.');
    history.replaceState(null, '', '#' + (i + 1));
  };
  const actions = {
    suivante: () => afficher(i + 1),
    precedente: () => afficher(i - 1),
    notes: () => { notes.hidden = !notes.hidden; },
    plein: () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()),
    imprimer: () => print(),
  };
  document.querySelectorAll('.barre [data-action]').forEach((b) => b.addEventListener('click', () => actions[b.dataset.action]()));
  addEventListener('keydown', (e) => {
    if (e.target.closest('button') && (e.key === ' ' || e.key === 'Enter')) return;
    const k = e.key;
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(k)) actions.suivante();
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(k)) actions.precedente();
    else if (k === 'Home') afficher(0);
    else if (k === 'End') afficher(slides.length - 1);
    else if (k === 'n' || k === 'N') actions.notes();
    else if (k === 'f' || k === 'F') actions.plein();
    else return;
    e.preventDefault();
  });
  addEventListener('resize', ajuster);
  addEventListener('hashchange', () => afficher((parseInt(location.hash.slice(1), 10) || 1) - 1));
  ajuster();
  afficher(i);
})();
"""


def rendre_html(s: dict) -> str:
    f = s["formation"]
    c = f["_cat"]
    variables = "--c:{c};--ci:{i};--ct:{t};--co:{o};--sk:{sk};--si:url({si});--logo:url({logo});--lf:{lf}".format(
        c=c["couleur"], i=c["encre"], t=c["teinte"], o=c["surCouleur"], sk=c["sticker"], si=icone(c["icone"]),
        logo=ch.logo_data_uri(ch.variante_logo(c), rogne=True), lf="none" if c["surCouleur"].upper() == "#FFFFFF" else "brightness(0)",
    )
    sections = []
    for slide in s["_slides"]:
        t = slide["type"]
        corps = RENDUS[t](slide, f)
        if t not in SANS_PIED:
            corps += pied(f["intitule"], couleur=(t == "chapitre"))
        notes = slide.get("notes") or ""
        if isinstance(notes, list):
            notes = "\n".join(notes)
        modele = '<template class="notes-slide">{}</template>'.format(ch.html_gras(notes)) if notes else ""
        etiquette = "{} · {}".format(len(sections) + 1, t)
        sections.append(
            '<section class="slide {}" data-type="{}" aria-label="{}">{}{}</section>'.format(
                FOND.get(t, SECTION), t, esc(etiquette), corps, modele
            )
        )
    return """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre} · Support de formation · Skazy Formation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Raleway:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&amp;display=swap" rel="stylesheet">
<style>{feuille}</style>
<style>:root{{{variables}}}{css}</style>
</head>
<body>
<div class="scene"><div class="deck">
{sections}
</div></div>
<div class="notes" hidden></div>
<nav class="barre" aria-label="Navigation du support">
<button type="button" data-action="precedente" aria-label="Slide précédente">←</button>
<output aria-live="polite"></output>
<button type="button" data-action="suivante" aria-label="Slide suivante">→</button>
<button type="button" data-action="notes" title="Touche N">Notes</button>
<button type="button" data-action="plein" title="Touche F">Plein écran</button>
<button type="button" data-action="imprimer">PDF</button>
</nav>
<script>{js}</script>
</body>
</html>
""".format(titre=esc(f["intitule"]), feuille=feuille(), variables=variables, css=CSS, sections="\n".join(sections), js=JS)
