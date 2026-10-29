"""Support de formation Skazy Formation : lecture, valeurs par défaut et contrôle du support.json.

Le format et les 30 mises en page sont décrits dans references/format-support.md.
"""

from __future__ import annotations

import copy

import charte as ch

FORMAT = "skazy-support"

# Type de slide → numéro de la mise en page du modèle « 4. Support de formation par catégorie ».
TYPES = {
    "couverture": 1,
    "faisons-connaissance": 2,
    "objectifs": 3,
    "programme": 4,
    "chapitre": 5,
    "contenu": 6,
    "chiffre-cle": 7,
    "frise": 8,
    "graphique": 9,
    "image": 10,
    "texte": 11,
    "citation": 12,
    "avant-apres": 13,
    "notion-cle": 14,
    "code": 15,
    "capture": 16,
    "pas-a-pas": 17,
    "comparatif": 18,
    "raccourcis": 19,
    "bon-a-savoir": 20,
    "exercice": 21,
    "exercice-etapes": 22,
    "quiz": 23,
    "a-retenir": 24,
    "ressources": 25,
    "evaluation": 26,
    "questions": 27,
    "battle": 28,
    "accompagnement-360": 29,
    "autres-formations": 30,
}

ALIAS = {
    "chiffre": "chiffre-cle",
    "chiffre-clef": "chiffre-cle",
    "frise-chronologique": "frise",
    "image-pleine-page": "image",
    "formule": "code",
    "formule-ou-code": "code",
    "capture-annotee": "capture",
    "pas-a-pas": "pas-a-pas",
    "tableau-comparatif": "comparatif",
    "memo-raccourcis": "raccourcis",
    "encadres": "bon-a-savoir",
    "exercice-variante": "exercice-etapes",
    "atelier": "exercice",
    "evaluation-finale": "evaluation",
    "battle-de-questions": "battle",
    "accompagnement": "accompagnement-360",
    "intercalaire": "chapitre",
    "contenu-et-visuel": "contenu",
}

# Champs obligatoires par type (les autres ont une valeur par défaut ou sont facultatifs).
OBLIGATOIRES = {
    "objectifs": ["objectifs"],
    "programme": ["parties"],
    "chapitre": ["titre"],
    "contenu": ["titre"],
    "chiffre-cle": ["chiffre", "phrase"],
    "frise": ["titre", "etapes"],
    "graphique": ["titre", "barres"],
    "image": ["titre"],
    "texte": ["titre", "paragraphes"],
    "citation": ["citation"],
    "avant-apres": ["titre", "avant", "apres"],
    "notion-cle": ["titre", "definition"],
    "code": ["titre", "syntaxe"],
    "capture": ["titre", "reperes"],
    "pas-a-pas": ["titre", "etapes"],
    "comparatif": ["titre", "colonnes", "lignes"],
    "raccourcis": ["raccourcis"],
    "bon-a-savoir": ["encadres"],
    "exercice": ["titre", "consignes"],
    "exercice-etapes": ["titre", "etapes"],
    "quiz": ["question", "propositions", "bonne"],
    "a-retenir": ["messages"],
    "ressources": ["ressources"],
}

# Bornes conseillées : (champ, minimum, maximum) pour les listes.
BORNES = {
    "objectifs": [("objectifs", 3, 5)],
    "programme": [("parties", 2, 8)],
    "chapitre": [("points", 0, 5)],
    "contenu": [("points", 0, 4)],
    "chiffre-cle": [("reperes", 0, 2)],
    "frise": [("etapes", 3, 6)],
    "graphique": [("barres", 3, 8)],
    "texte": [("paragraphes", 1, 5)],
    "notion-cle": [("termes", 0, 3)],
    "code": [("elements", 0, 4)],
    "capture": [("reperes", 1, 6)],
    "pas-a-pas": [("etapes", 3, 4)],
    "comparatif": [("lignes", 2, 5), ("colonnes", 2, 2)],
    "raccourcis": [("raccourcis", 2, 12)],
    "bon-a-savoir": [("encadres", 1, 3)],
    "exercice": [("consignes", 2, 5)],
    "exercice-etapes": [("etapes", 3, 3)],
    "quiz": [("propositions", 2, 4)],
    "a-retenir": [("messages", 1, 3)],
    "ressources": [("ressources", 1, 4)],
}

# Longueurs conseillées (caractères) au-delà desquelles le texte risque de déborder.
LONGUEURS = {
    "titre": 60,
    "texte": 260,
    "phrase": 70,
    "explication": 200,
    "definition": 170,
    "citation": 140,
    "contexte": 180,
    "question": 110,
    "message": 160,
}

TOUR_DE_TABLE = [
    "Votre prénom et votre poste",
    "Votre usage ou votre expérience sur l'outil",
    "Ce que vous attendez de la formation",
    "Une info (passion, loisir, dessert, plat, film, livre, etc.)",
]

REGLES_BATTLE = [
    "Chaque équipe prépare 5 questions sur la formation (5 min)",
    "Tour à tour, une équipe pose une question à l'autre",
    "1 point par bonne réponse, 30 secondes pour répondre",
    "2 points bonus si la question piège le formateur",
]

TOUCHES_MAC = {"ctrl": "Cmd", "alt": "Option"}


def type_slide(nom: str) -> str | None:
    cle = ch.normaliser(nom or "").replace(" ", "-")
    cle = ALIAS.get(cle, cle)
    return cle if cle in TYPES else None


def normaliser_support(brut: dict, dossier=None) -> tuple[dict, ch.Rapport]:
    """Valeurs par défaut, numérotation, photos et contrôle du contenu.

    `dossier` : dossier du JSON, auquel se rapportent les chemins d'images relatifs.
    """
    r = ch.Rapport()

    def image(valeur: str, ou: str) -> str:
        """URL d'une image ; un fichier local est intégré (data URI), un fichier introuvable est signalé."""
        if ch.IMAGE_LOCALE.search(valeur) and not valeur.startswith(("http://", "https://", "data:")) and not ch.fichier_local(valeur, dossier):
            r.avertir("{} : image introuvable « {} » (chemin relatif au dossier du JSON).".format(ou, valeur))
        return ch.url_photo(valeur, dossier=dossier)

    s = copy.deepcopy(brut.get("support", brut))
    if s.get("format") not in (None, FORMAT):
        r.erreur("format attendu « {} », reçu « {} ».".format(FORMAT, s.get("format")))
    f = s.get("formation") or {}
    for champ in ("intitule", "categorie"):
        if not f.get(champ):
            r.erreur("formation.{} est obligatoire.".format(champ))
    if not isinstance(s.get("slides"), list) or not s["slides"]:
        r.erreur("la liste « slides » est vide ou absente.")
    if not r.ok:
        return s, r
    try:
        cat = ch.categorie(f["categorie"])
        f["niveau"] = ch.niveau(f.get("niveau"))
    except ValueError as e:
        r.erreur(str(e))
        return s, r
    f["categorie"] = cat["nom"]
    f["_cat"] = cat
    f.setdefault("duree", "")
    f["formateur"] = f.get("formateur") or ch.CONTACT["formateur"]
    f["email"] = f.get("email") or ch.CONTACT["email"]
    f["role"] = f.get("role") or ch.CONTACT["role"]
    f["stickers"] = f.get("stickers", True) is not False
    f["animations"] = f.get("animations", True) is not False
    f["_couverture"] = image(f.get("photoCouverture") or cat["photos"][0], "formation")
    s["formation"] = f

    slides = []
    num_chapitre = num_exercice = num_photo = 0
    chapitre_courant = None
    for i, slide in enumerate(s["slides"], 1):
        if isinstance(slide, str):
            slide = {"type": slide}
        t = type_slide(slide.get("type", ""))
        if not t:
            r.erreur("slide {} : type inconnu « {} ». Types possibles : {}.".format(i, slide.get("type"), ", ".join(TYPES)))
            continue
        slide = dict(slide, type=t, _n=i)
        for champ in OBLIGATOIRES.get(t, []):
            if slide.get(champ) in (None, "", []):
                r.erreur("slide {} ({}) : champ « {} » manquant.".format(i, t, champ))
        for champ, mini, maxi in BORNES.get(t, []):
            valeur = slide.get(champ) or []
            if valeur and not mini <= len(valeur) <= maxi:
                r.avertir("slide {} ({}) : {} éléments dans « {} » ({} à {} conseillés).".format(i, t, len(valeur), champ, mini, maxi))
        for champ, maxi in LONGUEURS.items():
            valeur = slide.get(champ)
            if isinstance(valeur, str) and len(ch.sans_gras(valeur)) > maxi:
                r.avertir("slide {} ({}) : « {} » long ({} caractères, {} conseillés).".format(i, t, champ, len(valeur), maxi))
        if t == "chapitre":
            num_chapitre += 1
            slide.setdefault("numero", num_chapitre)
            chapitre_courant = slide
            if not slide.get("photo"):
                num_photo += 1
                slide["photo"] = cat["photos"][num_photo % len(cat["photos"])]
        if t == "a-retenir" and "sousTitre" not in slide and chapitre_courant:
            # Comme le modèle : « Chapitre 1 », puis le titre du chapitre, sur deux lignes.
            slide["sousTitre"] = "Chapitre {}\n{}".format(chapitre_courant["numero"], chapitre_courant.get("titre", ""))
        if t in ("exercice", "exercice-etapes"):
            num_exercice += 1
            slide.setdefault("numero", num_exercice)
        if t == "objectifs":
            slide.setdefault("photo", cat["photos"][1])
        if t == "programme":
            slide.setdefault("photo", cat["photos"][2])
        if t == "image":
            slide.setdefault("image", cat["photos"][1])
        if t == "faisons-connaissance":
            slide.setdefault("tourDeTable", TOUR_DE_TABLE)
            slide.setdefault("photo", f.get("photoFormateur", ""))
            # Lignes du modèle : téléphone et e-mail, en liens discrets.
            slide.setdefault("infos", [
                {"label": "Téléphone", "texte": ch.CONTACT["telephone"], "lien": "tel:" + "".join(x for x in ch.CONTACT["telephone"] if x.isdigit() or x == "+")},
                {"label": "E-mail", "texte": f["email"], "lien": "mailto:" + f["email"].strip()},
            ])
        if t == "battle":
            slide.setdefault("regles", REGLES_BATTLE)
        if t == "quiz":
            props = slide.get("propositions") or []
            bonne = slide.get("bonne")
            if isinstance(bonne, str) and bonne.strip().upper() in "ABCD" and len(bonne.strip()) == 1:
                bonne = "ABCD".index(bonne.strip().upper())
            if not isinstance(bonne, int) or not 0 <= bonne < len(props):
                r.erreur("slide {} (quiz) : « bonne » doit être l'indice (0 à {}) de la bonne proposition.".format(i, len(props) - 1))
            slide["bonne"] = bonne
        ou = "slide {} ({})".format(i, t)
        for champ in ("photo", "image", "qrCode"):
            if isinstance(slide.get(champ), str):
                slide[champ] = image(slide[champ], ou)
        # Images imbriquées : avant et après, étapes du pas-à-pas.
        for champ in ("avant", "apres"):
            if isinstance(slide.get(champ), dict) and isinstance(slide[champ].get("image"), str):
                slide[champ] = dict(slide[champ], image=image(slide[champ]["image"], ou))
        if isinstance(slide.get("etapes"), list):
            slide["etapes"] = [dict(e, image=image(e["image"], ou)) if isinstance(e, dict) and isinstance(e.get("image"), str) else e
                               for e in slide["etapes"]]
        slides.append(slide)

    # Numérotation des quiz : « Question 2 sur 5 » dans chaque suite de slides quiz.
    groupe: list[dict] = []
    for slide in slides + [{"type": "_fin"}]:
        if slide["type"] == "quiz":
            groupe.append(slide)
            continue
        for k, q in enumerate(groupe, 1):
            q.setdefault("numero", k)
            q.setdefault("total", len(groupe))
        groupe = []

    # Le quiz se projette en deux temps : question, puis réponse (slide dupliquée).
    deroule = []
    for slide in slides:
        if slide["type"] == "quiz":
            deroule.append(dict(slide, _reponse=False))
            deroule.append(dict(slide, _reponse=True, notes=slide.get("explication") or slide.get("notes", "")))
        else:
            deroule.append(slide)
    s["_slides"] = deroule

    types = [x["type"] for x in slides]
    if types and types[0] != "couverture":
        r.avertir("le support ne commence pas par une couverture.")
    chapitres = types.count("chapitre")
    exercices = types.count("exercice") + types.count("exercice-etapes")
    if chapitres and exercices < chapitres:
        r.avertir("{} chapitres pour {} exercices : prévoyez au moins un exercice par chapitre.".format(chapitres, exercices))
    sans_notes = [x["_n"] for x in slides if not x.get("notes") and x["type"] not in ("couverture", "questions", "accompagnement-360", "autres-formations")]
    if sans_notes:
        r.avertir("{} slide(s) sans notes formateur ({}) : ajoutez « notes » à chaque slide de contenu.".format(
            len(sans_notes), ", ".join(map(str, sans_notes[:12])) + (" …" if len(sans_notes) > 12 else "")))
    return s, r


def touches(raccourci: dict, mac: bool = False) -> list[str]:
    """Liste des touches d'un raccourci : ["Ctrl", "C"] ou « Ctrl+C »."""
    t = raccourci.get("touches") or raccourci.get("raccourci") or []
    if isinstance(t, str):
        t = [x.strip() for x in t.split("+") if x.strip()]
    if mac:
        t = [TOUCHES_MAC.get(x.lower(), x) for x in t]
    return t
