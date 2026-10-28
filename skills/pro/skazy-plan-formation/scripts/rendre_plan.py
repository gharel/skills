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


CSS_PLAN = """
*{box-sizing:border-box}
html,body{margin:0}
body{background:#E9E9EC;font-family:Raleway,system-ui,sans-serif;color:#1F1F24;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{position:relative;width:794px;height:1123px;margin:32px auto;background:#fff;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 12px 40px rgba(0,0,0,.14)}
.bandeau{position:relative;background:var(--c);color:#1F1F24;padding:46px 64px 0;height:150px;flex-shrink:0}
.bandeau h1{margin:0;font-size:42px;font-weight:700;line-height:1.05;letter-spacing:-.01em;max-width:560px}
.pastilles{position:absolute;left:64px;bottom:-14px;display:flex;gap:8px}
.pastilles span{background:#F1F1F3;color:#1F1F24;font-size:13px;font-weight:700;padding:6px 14px;border-radius:999px;box-shadow:0 0 0 3px #fff}
.sticker{position:absolute;top:68px;right:52px;width:100px;height:100px;transform:rotate(8deg);background:#fff;border-radius:28px;padding:7px;box-shadow:0 6px 14px rgba(0,0,0,.18)}
.sticker div{width:100%;height:100%;background:var(--sk);border:3px solid #1F1F24;border-radius:22px;display:flex;align-items:center;justify-content:center}
.sticker i{width:48px;height:48px;background:#1F1F24;-webkit-mask:var(--si) center/contain no-repeat;mask:var(--si) center/contain no-repeat}
.corps{flex:1;display:flex;flex-direction:column;padding:40px 64px 0;min-height:0}
.description{margin:0;font-size:14px;line-height:1.55;color:#3B3B42;max-width:600px}
h2{margin:24px 0 8px;font-size:17px;font-weight:700}
.objectifs{margin:0;padding:0 0 0 20px;display:flex;flex-direction:column;gap:3px;font-size:14px;line-height:1.45;color:#3B3B42}
strong{color:#1F1F24}
.infos{margin-top:22px;background:#F4F4F5;border-radius:12px;padding:18px 22px;display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1.3fr) minmax(108px,max-content);gap:18px}
.infos .t{font-size:15px;font-weight:700;margin-bottom:6px}
.infos .v{font-size:13px;line-height:1.45;color:#3B3B42}
.infos .duree .v{white-space:nowrap}
.h-prog{margin:26px 0 12px}
.programme{column-count:2;column-gap:40px;font-size:13px;line-height:1.42;color:#3B3B42}
.partie{break-inside:avoid;margin-bottom:12px}
.partie .titre{font-weight:700;font-style:italic;color:#1F1F24;margin-bottom:3px}
.partie .num{color:var(--ci);font-style:normal;font-weight:800;margin-right:6px}
.partie ul{margin:0;padding:0 0 0 18px}
.pied{margin-top:auto;padding:18px 0 26px;display:flex;align-items:center;justify-content:space-between;gap:16px;border-top:1px solid #EEEEF0;font-size:11px;color:#6E6E78}
.pied img{height:15px;width:auto}
.bandeau2{background:var(--c);height:74px;padding:0 64px;display:flex;justify-content:space-between;align-items:center;gap:24px;flex-shrink:0}
.bandeau2 .i{font-size:22px;font-weight:700;color:#1F1F24}
.bandeau2 .m{background:var(--ci);color:#fff;font-size:12px;font-weight:700;text-transform:uppercase;padding:5px 40px;border-radius:999px;white-space:nowrap}
.corps2{flex:1;display:flex;flex-direction:column;padding:34px 64px 0;min-height:0}
.cartes{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.cartes>div{background:#F4F4F5;border-radius:12px;padding:17px 18px 14px;min-height:64px}
.cartes .t{font-size:11.3px;font-weight:800;text-transform:uppercase;color:var(--ci);margin-bottom:5px}
.cartes .v{font-size:14.7px;font-weight:700}
.p2 h2{margin:31px 0 10px;font-size:16px;display:flex;gap:9px;align-items:center}
.p2 h2::before{content:"";width:10px;height:10px;border-radius:2.5px;background:var(--c);flex-shrink:0}
.formats{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:14px}
.formats>div{border:1px solid #E4E4E8;border-top:4px solid var(--c);border-radius:12px;padding:17px 17px 14px;min-height:220px}
.formats .ic{display:flex;align-items:center;justify-content:center;width:33px;height:33px;border-radius:8px;background:var(--ct);margin-bottom:24px}
.formats .ic i,.accomp i{display:block;width:17px;height:17px;background:var(--c);-webkit-mask:var(--i) center/contain no-repeat;mask:var(--i) center/contain no-repeat}
.formats .t{font-size:14px;font-weight:700;margin-bottom:5px}
.formats .v{font-size:12.7px;line-height:1.5;color:#3B3B42}
.accomp{margin-top:14px;background:var(--ct);border-radius:12px;min-height:46px;padding:12px 18px 12px 19px;display:flex;align-items:center;gap:15px;font-size:13.3px;line-height:1.5}
.accomp i{flex-shrink:0}
.deux{display:grid;grid-template-columns:1fr 1fr;gap:0 40px;margin-top:6px}
.deux h2{margin:22px 0 10px}
.deux p{margin:0;font-size:13.3px;line-height:1.5;color:#3B3B42}
.deux ul{margin:8px 0 0;padding:0 0 0 18px;font-size:13.3px;line-height:1.46;color:#3B3B42;display:flex;flex-direction:column;gap:2px}
.contact{margin-top:auto;background:var(--ct);border-radius:16px;min-height:112px;padding:16px 28px;display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center}
.contact .q{font-size:18px;font-weight:700;display:block;margin-bottom:6px}
.contact .c{font-size:13.3px;line-height:1.5;color:#3B3B42}
.contact a{color:var(--ci);font-weight:700;text-decoration:none}
.contact img{width:83px;height:auto}
.p2 .pied{margin-top:26px}
.outils{position:fixed;top:16px;right:16px;z-index:10;display:flex;gap:8px}
.outils button{font:700 14px Raleway,system-ui,sans-serif;border:0;border-radius:999px;padding:10px 18px;background:#1F1F24;color:#fff;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,.2)}
.outils button:focus-visible{outline:3px solid var(--c);outline-offset:2px}
@page{size:A4;margin:0}
@media print{body{background:none}.page{margin:0;box-shadow:none;break-after:page;width:210mm;height:297mm}.outils{display:none}}
"""

JS_AJUSTER = """
// Si le contenu déborde de la page 1, on réduit la taille du programme (13 px → 10 px au plus).
addEventListener('load', () => {
  const page = document.querySelector('.p1');
  const prog = page && page.querySelector('.programme');
  if (!prog) return;
  let taille = 13;
  while (page.scrollHeight > page.clientHeight + 1 && taille > 10) {
    taille -= 0.25;
    prog.style.fontSize = taille + 'px';
  }
});
"""


def rendre_html(p: dict) -> str:
    c = p["_cat"]
    variables = "--c:{};--ci:{};--ct:{};--co:{};--sk:{};--si:url({})".format(
        c["couleur"], c["encre"], c["teinte"], c["surCouleur"], c["sticker"], ch.icone_data_uri(c["icone"])
    )
    i = couper_programme(p["programme"])
    parties = []
    for n, partie in enumerate(p["programme"], 1):
        duree = " · " + esc(partie["duree"]) if partie.get("duree") else ""
        points = "".join("<li>{}</li>".format(html_gras(pt)) for pt in partie["points"])
        coupure = ' style="break-before:column"' if n == i + 1 and i not in (0, len(p["programme"])) else ""
        parties.append(
            '<div class="partie"{}><div class="titre"><span class="num">{:02d}</span>{}{}</div><ul>{}</ul></div>'.format(
                coupure, n, esc(partie["titre"]), duree, points
            )
        )
    sticker = '<div class="sticker" aria-hidden="true"><div><i></i></div></div>' if p["sticker"] else ""
    logo = ch.logo_svg_data_uri("couleur")
    page1 = """
<section class="page p1" aria-label="Page 1, programme">
<div class="bandeau"><h1>{intitule}</h1><div class="pastilles"><span>{etiquette}</span><span>{niveau}</span></div></div>
{sticker}
<div class="corps">
<p class="description">{description}</p>
<h2>Objectifs</h2>
<ul class="objectifs">{objectifs}</ul>
<div class="infos">
<div><div class="t">Prérequis</div><div class="v">{prerequis}</div></div>
<div><div class="t">Public visé</div><div class="v">{public}</div></div>
<div class="duree"><div class="t">Durée</div><div class="v">{duree}</div></div>
</div>
<h2 class="h-prog">Programme</h2>
<div class="programme">{programme}</div>
<div class="pied"><span>{site} · {email}</span><img src="{logo}" alt="Skazy Formation"></div>
</div>
</section>""".format(
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
        site=ch.CONTACT["site"],
        email=ch.CONTACT["email"],
        logo=logo,
    )
    page2 = ""
    m = p["_modalites"]
    if m:
        formats = "".join(
            '<div><span class="ic"><i style="--i:url({})"></i></span><div class="t">{}</div><div class="v">{}</div></div>'.format(
                ch.icone_data_uri(f["icone"]), esc(f["titre"]), html_gras(f["texte"])
            )
            for f in m["formats"]
        )
        bloc_formats = (
            '<h2>Modalités et lieu de la formation</h2><div class="formats" style="--n:{}">{}</div>'.format(len(m["formats"]), formats)
            if m["formats"]
            else ""
        )
        accomp = (
            '<div class="accomp"><i style="--i:url({})"></i><span><strong>Accompagnement personnalisé&nbsp;:</strong> {}</span></div>'.format(
                ch.icone_data_uri("handshake"), html_gras(m["accompagnement"])
            )
            if m["accompagnement"]
            else ""
        )
        moyens = "<ul>{}</ul>".format("".join("<li>{}</li>".format(html_gras(x)) for x in m["moyens"])) if m["moyens"] else ""
        droite = "".join(
            "<h2>{}</h2><p>{}</p>".format(titre, html_gras(valeur))
            for titre, valeur in (("Encadrement", m["encadrement"]), ("Évaluation des acquis", m["evaluation"]), ("Mode de validation", m["validation"]))
            if valeur
        )
        page2 = """
<section class="page p2" aria-label="Page 2, modalités et informations pratiques">
<div class="bandeau2"><span class="i">{intitule}</span><span class="m">Modalités et infos pratiques</span></div>
<div class="corps2">
<div class="cartes">
<div><div class="t">Effectif</div><div class="v">{effectif}</div></div>
<div><div class="t">Lieu</div><div class="v">{lieu}</div></div>
<div><div class="t">Tarif</div><div class="v">{tarif}</div></div>
</div>
{formats}
{accomp}
<div class="deux">
<div><h2>Méthodes et moyens pédagogiques</h2><p>{methodes}</p>{moyens}</div>
<div>{droite}</div>
</div>
<div class="contact"><div><span class="q">Une question sur cette formation&nbsp;?</span><span class="c">{email} · {tel}<br><a href="{url}">{site}</a></span></div><img src="{logo}" alt="Skazy Formation"></div>
<div class="pied"><span>RIDET {ridet} · N° DFPC {dfpc}</span></div>
</div>
</section>""".format(
            intitule=esc(p["intitule"]),
            effectif=esc(m["effectif"]),
            lieu=esc(m["lieu"]),
            tarif=esc(m["tarif"]),
            formats=bloc_formats,
            accomp=accomp,
            methodes=html_gras(m["methodes"]),
            moyens=moyens,
            droite=droite,
            email=ch.CONTACT["email"],
            tel=esc(ch.CONTACT["telephone"]),
            url=ch.CONTACT["url"],
            site=ch.CONTACT["site"],
            ridet=esc(ch.CONTACT["ridet"]),
            dfpc=esc(ch.CONTACT["dfpc"]),
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
<style>:root{{{variables}}}{css}</style>
</head>
<body>
<div class="outils"><button type="button" onclick="print()">Imprimer ou enregistrer en PDF</button></div>
<main>{page1}{page2}</main>
<script>{js}</script>
</body>
</html>
""".format(titre=esc(p["intitule"]), variables=variables, css=CSS_PLAN, page1=page1, page2=page2, js=JS_AJUSTER)


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
