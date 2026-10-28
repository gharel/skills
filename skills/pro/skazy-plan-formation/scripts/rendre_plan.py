#!/usr/bin/env python3
"""Plan de formation Skazy Formation : plan.json → plan.html (A4) et plan.docx (Word, Google Docs).

Usage :
    python scripts/rendre_plan.py plan.json [--sortie DOSSIER] [--formats html,docx] [--verifier]

Le JSON suit references/format-plan.md. Le HTML reproduit le modèle « 3. Plan de formation »
du Skazy Formation Design System (Claude Design) ; le DOCX en reprend la mise en page avec de vrais
en-têtes et pieds de page (bandeau couleur pleine largeur), lisibles dans Word et Google Docs. Il est
allégé par docx_google_docs.py (environ 25 Ko) : il s'importe tel quel dans Google Docs.
"""

from __future__ import annotations

import argparse
import io
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import charte as ch  # noqa: E402
from charte import esc, html_gras, typographie  # noqa: E402

FORMAT = "skazy-plan"

# ---------------------------------------------------------------- lecture et contrôle


def normaliser_plan(brut: dict) -> tuple[dict, ch.Rapport]:
    """Complète les valeurs par défaut et contrôle le contenu (règles de references/regles-redaction.md)."""
    r = ch.Rapport()
    p = dict(brut.get("plan", brut))
    if p.get("format") not in (None, FORMAT):
        r.erreur("format attendu « {} », reçu « {} ».".format(FORMAT, p.get("format")))
    for champ in ("intitule", "categorie", "description", "objectifs", "prerequis", "public", "duree", "programme"):
        if not p.get(champ):
            r.erreur("champ obligatoire manquant : « {} ».".format(champ))
    if not r.ok:
        return p, r
    try:
        p["_cat"] = ch.categorie(p["categorie"])
    except ValueError as e:
        r.erreur(str(e))
        return p, r
    try:
        p["niveau"] = ch.niveau(p.get("niveau"))
    except ValueError as e:
        r.erreur(str(e))
        return p, r
    p["categorie"] = p["_cat"]["nom"]
    p["etiquette"] = p.get("etiquette") or p["categorie"]
    p["sticker"] = p.get("sticker", True) is not False

    if len(p["intitule"]) > 60:
        r.avertir("intitulé long ({} caractères) : visez 60 au plus pour tenir sur deux lignes.".format(len(p["intitule"])))
    if len(p["description"]) > 420:
        r.avertir("description longue ({} caractères) : deux à quatre lignes suffisent.".format(len(p["description"])))
    if ch.normaliser(p["description"]).startswith(("cette formation", "ce parcours", "cette session")):
        r.avertir("la description commence par « Cette formation » : commencez par un verbe d'action.")
    n = len(p["objectifs"])
    if not 3 <= n <= 5:
        r.avertir("{} objectifs : le modèle en prévoit 3 à 5.".format(n))
    vagues = [o for o in p["objectifs"] if ch.normaliser(ch.sans_gras(o)).split(" ")[0] in {"comprendre", "connaitre", "savoir", "apprendre", "decouvrir"}]
    for o in vagues:
        r.avertir("objectif peu observable (Bloom) : « {} ». Préférez identifier, utiliser, créer, analyser…".format(o))

    programme = []
    for i, partie in enumerate(p["programme"], 1):
        if isinstance(partie, str):
            partie = {"titre": partie, "points": []}
        if not partie.get("titre"):
            r.erreur("partie {} du programme sans titre.".format(i))
        points = partie.get("points") or []
        if not 2 <= len(points) <= 6:
            r.avertir("partie {} « {} » : {} points (2 à 6 attendus).".format(i, partie.get("titre", ""), len(points)))
        programme.append({"titre": partie.get("titre", ""), "points": points, "duree": partie.get("duree", "")})
    p["programme"] = programme
    if not 2 <= len(programme) <= 8:
        r.avertir("{} parties au programme : 2 à 8 attendues.".format(len(programme)))

    modalites = p.get("modalites", {})
    if modalites is False or p.get("page2") is False:
        p["_modalites"] = None
    else:
        p["_modalites"] = normaliser_modalites(modalites or {}, r)

    p["_coupure"] = couper_programme(p["programme"])
    p["_charge"] = estimer_charge(p)
    if p["_charge"] > 1.0:
        r.avertir(
            "le contenu de la page 1 dépasse d'environ {:.0f} % la place disponible : la taille du programme "
            "sera réduite, raccourcissez les points ou supprimez une partie.".format((p["_charge"] - 1) * 100)
        )
    return p, r


def normaliser_modalites(modalites: dict, r: ch.Rapport) -> dict:
    """Page 2 : valeurs standard pour les champs absents ; false ou liste vide retire un bloc facultatif."""
    defaut = ch.CHARTE["modalitesParDefaut"]
    m = {}
    for cle, valeur in defaut.items():
        donnee = modalites.get(cle)
        if donnee is None or donnee == "":
            donnee = valeur
        if donnee is False and cle in ("effectif", "lieu", "tarif", "methodes"):
            r.avertir("modalités : « {} » ne peut pas être retiré, valeur standard gardée.".format(cle))
            donnee = valeur
        m[cle] = donnee
    formats = []
    for i, f in enumerate(m["formats"] or []):
        if isinstance(f, str):
            f = {"titre": f, "texte": ""}
        if not f.get("titre"):
            r.erreur("modalités : format {} sans titre.".format(i + 1))
            continue
        icone = f.get("icone") or (defaut["formats"][i]["icone"] if i < len(defaut["formats"]) else "circle-check")
        formats.append({"titre": f["titre"], "texte": f.get("texte", ""), "icone": icone})
    if len(formats) > 3:
        r.avertir("modalités : {} formats, la page en affiche 3 au plus ; les suivants sont ignorés.".format(len(formats)))
    m["formats"] = formats[:3]
    m["moyens"] = [x for x in (m["moyens"] or []) if x]
    m["accompagnement"] = m["accompagnement"] or ""
    for cle in ("encadrement", "evaluation", "validation"):
        m[cle] = m[cle] or ""
    charge = estimer_page2(m)
    if charge > 1.0:
        r.avertir(
            "les textes de la page 2 dépassent d'environ {:.0f} % la place disponible : raccourcissez les méthodes, "
            "les moyens ou l'évaluation, sinon le plan passe sur trois pages.".format((charge - 1) * 100)
        )
    return m


def estimer_page2(m: dict) -> float:
    """Rapport entre la hauteur estimée des deux colonnes du bas de la page 2 et la place disponible (pt)."""
    place = 260 + (0 if m["formats"] else 196) + (0 if m["accompagnement"] else 45)
    gauche = 23 + 15.1 * lignes(m["methodes"], 50) + (6 + sum(16.2 * lignes(x, 46) for x in m["moyens"]) if m["moyens"] else 0)
    textes = [t for t in (m["encadrement"], m["evaluation"], m["validation"]) if t]
    droite = sum(23 + 15.1 * lignes(t, 50) for t in textes) + 15 * max(0, len(textes) - 1)
    return max(gauche, droite) / place


def lignes(texte: str, largeur_car: int) -> int:
    return max(1, math.ceil(len(ch.sans_gras(texte)) / largeur_car))


def hauteur_parties(parties: list[dict]) -> float:
    """Hauteur (px) d'une colonne du programme à 13 px : titre + points + marge."""
    h = 0.0
    for partie in parties:
        h += 18.5 * lignes(partie["titre"], 40) + 3
        h += sum(18.5 * lignes(pt, 44) for pt in partie["points"])
        h += 12
    return h


def couper_programme(programme: list[dict]) -> int:
    """Indice de coupure qui équilibre les deux colonnes (ordre de lecture conservé)."""
    meilleur, ecart = len(programme), float("inf")
    for i in range(len(programme) + 1):
        a, b = hauteur_parties(programme[:i]), hauteur_parties(programme[i:])
        if max(a, b) < ecart:
            meilleur, ecart = i, max(a, b)
    return meilleur


def estimer_charge(p: dict) -> float:
    """Rapport entre la hauteur estimée du contenu de la page 1 et la place disponible (1.0 = plein)."""
    fixe = 150 + 40 + 84 + 58 + 78
    fixe += 21.7 * lignes(p["description"], 92)
    fixe += 52 + sum(23.3 * lignes(o, 96) for o in p["objectifs"])
    infos = max(lignes(p["prerequis"], 30), lignes(p["public"], 26), 1)
    fixe += 18.9 * infos
    i = couper_programme(p["programme"])
    programme = max(hauteur_parties(p["programme"][:i]), hauteur_parties(p["programme"][i:]))
    return (fixe + programme) / 1123


# ---------------------------------------------------------------- HTML


# Le design des pages est celui du modèle « plan-formation » de design-skazy : sa feuille de style et ses
# ajustements (titres, densité du programme, pages de suite) sont recopiés tels quels dans assets/charte/
# (npm run synchroniser). Ce module n'ajoute que la présentation à l'écran et l'impression.
CSS_ECRAN = """
html,body{margin:0}
body{background:var(--color-gray-200);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:794px;height:1123px;margin:32px auto;box-shadow:var(--shadow-lg)}
.outils{position:fixed;top:16px;right:16px;z-index:10;display:flex;gap:8px}
.outils button{font:700 14px Raleway,sans-serif;border:0;border-radius:var(--radius-full);padding:10px 18px;background:var(--color-doc-text);color:#fff;cursor:pointer;box-shadow:var(--shadow-md)}
.outils button:focus-visible{outline:3px solid var(--c);outline-offset:2px}
@page{size:A4;margin:0}
@media print{body{background:none}.page{margin:0;box-shadow:none;break-after:page;width:210mm;height:297mm}.outils{display:none}}
"""

JS_AJUSTER = """
const ajuster = () => window.SkazyPlanFormation.ajuster(document.querySelector('main'));
addEventListener('load', ajuster);
if (document.fonts) document.fonts.ready.then(ajuster);
addEventListener('beforeprint', ajuster);
"""


def fichier_charte(nom: str) -> str:
    return (ch.DOSSIER_CHARTE / nom).read_text(encoding="utf-8")


def rendre_html(p: dict) -> str:
    c = p["_cat"]
    variables = "--c:{};--ci:{};--ct:{};--co:{};--sk:{};--si:url({})".format(
        c["couleur"], c["encre"], c["teinte"], c["surCouleur"], c["sticker"], ch.icone_data_uri(c["icone"])
    )
    parties = []
    for n, partie in enumerate(p["programme"], 1):
        duree = " · " + esc(partie["duree"]) if partie.get("duree") else ""
        points = "".join("<li>{}</li>".format(html_gras(pt)) for pt in partie["points"])
        parties.append('<div class="pf-part"><div class="pf-pt"><b>{:02d}</b>{}{}</div><ul>{}</ul></div>'.format(n, esc(partie["titre"]), duree, points))
    sticker = (
        '<div class="pf-stk" aria-hidden="true"><div class="pf-stk-c"><div class="pf-stk-i"></div></div></div>' if p["sticker"] else ""
    )
    logo = ch.logo_data_uri("couleur")
    k = ch.CONTACT
    page1 = """
<section class="page pf-page" data-screen-label="Page 1 Programme">
<div class="pf-band" data-stk="{stk}">
<h1 class="pf-h1" data-fit="42,36,26">{intitule}</h1>
<div class="pf-chips"><span class="pf-chip">{etiquette}</span><span class="pf-chip">{niveau}</span></div>
</div>
{sticker}
<div class="pf-body pf-body--cover">
<p class="pf-desc">{description}</p>
<h2 class="pf-sh">Objectifs</h2>
<ul class="pf-obj">{objectifs}</ul>
<div class="pf-facts">
<div><div class="pf-fk">Prérequis</div><div class="pf-fv">{prerequis}</div></div>
<div><div class="pf-fk">Public visé</div><div class="pf-fv">{public}</div></div>
<div><div class="pf-fk">Durée</div><div class="pf-fv pf-fv--nw">{duree}</div></div>
</div>
<h2 class="pf-sh" data-prog-h="">Programme</h2>
<div class="pf-prog" data-prog="">
<section class="pf-day">
<div class="pf-parts">
{programme}
</div>
</section>
</div>
<div class="pf-foot" data-pfoot="">
<span><a class="lk" href="{url}" target="_blank" rel="noopener">{site}</a> · <a class="lk" href="mailto:{email}">{email}</a></span>
<img class="pf-logo" src="{logo}" alt="Skazy Formation">
</div>
</div>
</section>""".format(
        stk="on" if p["sticker"] else "off",
        intitule=esc(p["intitule"]),
        etiquette=esc(p["etiquette"]),
        niveau=esc(p["niveau"]),
        sticker=sticker,
        description=html_gras(p["description"]),
        objectifs="".join("<li>{}</li>".format(html_gras(o)) for o in p["objectifs"]),
        prerequis=html_gras(p["prerequis"]),
        public=html_gras(p["public"]),
        duree=esc(p["duree"]),
        programme="\n".join(parties),
        url=k["url"],
        site=k["site"],
        email=k["email"],
        logo=logo,
    )
    page2 = ""
    m = p["_modalites"]
    if m:
        h2 = '<h2 class="pf-h2"><span class="pf-sq"></span>{}</h2>'
        modes = "".join(
            '<div class="pf-mode"><div class="pf-ico"><i aria-hidden="true" style="--ic:url({})"></i></div>'
            '<h3 class="pf-mt">{}</h3><p class="pf-mp">{}</p></div>'.format(ch.icone_data_uri(f["icone"]), esc(f["titre"]), html_gras(f["texte"]))
            for f in m["formats"]
        )
        bloc_modes = h2.format("Modalités et lieu de la formation") + '<div class="pf-modes">{}</div>'.format(modes) if m["formats"] else ""
        note = (
            '<div class="pf-note"><i aria-hidden="true" style="--ic:url({})"></i><span><b>Accompagnement personnalisé&nbsp;:</b> {}</span></div>'.format(
                ch.icone_data_uri("handshake"), html_gras(m["accompagnement"])
            )
            if m["accompagnement"]
            else ""
        )
        section_modalites = '<div class="pf-sec">\n{}\n{}\n</div>'.format(bloc_modes, note) if bloc_modes or note else ""
        moyens = '<ul class="pf-ul">{}</ul>'.format("".join("<li>{}</li>".format(html_gras(x)) for x in m["moyens"])) if m["moyens"] else ""
        pile = "".join(
            '<div>{}<p class="pf-p">{}</p></div>'.format(h2.format(titre), html_gras(valeur))
            for titre, valeur in (("Encadrement", m["encadrement"]), ("Évaluation des acquis", m["evaluation"]), ("Mode de validation", m["validation"]))
            if valeur
        )
        page2 = """
<section class="page pf-page" data-screen-label="Page Informations">
<div class="pf-strip pf-strip--info">
<span class="pf-strip-t" data-fit="22,20,19">{intitule}</span>
<span class="pf-pill">Modalités et infos pratiques</span>
</div>
<div class="pf-info" data-info="">
<div class="pf-tiles">
<div class="pf-tile"><div class="pf-k">Effectif</div><div class="pf-v">{effectif}</div></div>
<div class="pf-tile"><div class="pf-k">Lieu</div><div class="pf-v">{lieu}</div></div>
<div class="pf-tile"><div class="pf-k">Tarif</div><div class="pf-v">{tarif}</div></div>
</div>
{modalites}
<div class="pf-sec pf-cols">
<div>
{h2_methodes}
<p class="pf-p">{methodes}</p>
{moyens}
</div>
<div class="pf-stack">{pile}</div>
</div>
<div class="pf-gap"></div>
<div class="pf-contact">
<div class="pf-cq"><span class="pf-cqt">Une question sur cette formation&nbsp;?</span><span class="pf-cqv"><a class="lk" href="mailto:{email}">{email}</a> · <a class="lk" href="tel:{tel_lien}">{tel}</a><br><a class="pf-csite" href="{url}" target="_blank" rel="noopener">{site}</a></span></div>
<img class="pf-logo pf-logo--contact" src="{logo}" alt="Skazy Formation">
</div>
<div class="pf-foot pf-foot--info"><span>RIDET {ridet} · N° DFPC {dfpc}</span></div>
</div>
</section>""".format(
            intitule=esc(p["intitule"]),
            effectif=esc(m["effectif"]),
            lieu=esc(m["lieu"]),
            tarif=esc(m["tarif"]),
            modalites=section_modalites,
            h2_methodes=h2.format("Méthodes et moyens pédagogiques"),
            methodes=html_gras(m["methodes"]),
            moyens=moyens,
            pile=pile,
            email=k["email"],
            tel=esc(k["telephone"]),
            tel_lien=k["telephone"].replace(" ", ""),
            url=k["url"],
            site=k["site"],
            ridet=esc(k["ridet"]),
            dfpc=esc(k["dfpc"]),
            logo=logo,
        )
    return """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre} · Plan de formation · Skazy Formation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Raleway:ital,wght@0,400;0,500;0,600;0,700;0,800;1,600;1,700&amp;display=swap" rel="stylesheet">
<style>{css_modele}</style>
<style>:root{{{variables}}}{css_ecran}</style>
</head>
<body>
<div class="outils"><button type="button" onclick="print()">Imprimer ou enregistrer en PDF</button></div>
<main>{page1}{page2}</main>
<script>{js_modele}</script>
<script>{js}</script>
</body>
</html>
""".format(
        titre=esc(p["intitule"]),
        css_modele=fichier_charte("plan-formation.css"),
        variables=variables,
        css_ecran=CSS_ECRAN,
        page1=page1,
        page2=page2,
        js_modele=fichier_charte("plan-formation.js"),
        js=JS_AJUSTER,
    )


# ---------------------------------------------------------------- DOCX


def rendre_docx(p: dict) -> bytes:
    """DOCX identique dans Word et dans Google Docs : voir plan_docx.py."""
    import plan_docx

    return plan_docx.rendre_docx(p)


# ---------------------------------------------------------------- programme principal


def rendre(chemin_json: str, sortie: str | None = None, formats=("html", "docx")) -> list[Path]:
    p, rapport = normaliser_plan(ch.lire_json(chemin_json))
    rapport.afficher()
    if not rapport.ok:
        raise SystemExit(1)
    dossier = Path(sortie) if sortie else Path(chemin_json).resolve().parent
    dossier.mkdir(parents=True, exist_ok=True)
    base = "plan-" + ch.slug(p["intitule"])
    fichiers = []
    if "html" in formats:
        f = dossier / (base + ".html")
        f.write_text(rendre_html(p), encoding="utf-8")
        fichiers.append(f)
    if "docx" in formats:
        f = dossier / (base + ".docx")
        f.write_bytes(rendre_docx(p))
        fichiers.append(f)
    return fichiers


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan de formation Skazy Formation : JSON → HTML et DOCX.")
    parser.add_argument("json", help="fichier plan.json (voir references/format-plan.md)")
    parser.add_argument("--sortie", help="dossier de sortie (par défaut : celui du JSON)")
    parser.add_argument("--formats", default="html,docx", help="formats à produire : html, docx (séparés par des virgules)")
    parser.add_argument("--verifier", action="store_true", help="contrôle le JSON sans rien produire")
    args = parser.parse_args()
    if args.verifier:
        _, rapport = normaliser_plan(ch.lire_json(args.json))
        rapport.afficher()
        print("Plan valide." if rapport.ok else "Plan à corriger.")
        raise SystemExit(0 if rapport.ok else 1)
    for f in rendre(args.json, args.sortie, [x.strip() for x in args.formats.split(",") if x.strip()]):
        print(f)


if __name__ == "__main__":
    main()
