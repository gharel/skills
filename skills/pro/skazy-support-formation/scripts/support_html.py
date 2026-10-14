"""Support de formation : rendu HTML (deck 1920 × 1080, navigation au clavier, notes, impression PDF).

Reproduit les 30 mises en page du modèle « 4. Support de formation par catégorie »
du Skazy Formation Design System (Claude Design).
"""

from __future__ import annotations

import html as _html
import re

import charte as ch
from charte import esc
from support_modele import touches

H2 = "margin:0;font-size:72px;font-weight:600;line-height:1.05;letter-spacing:-.01em"
SURTITRE = "font-size:24px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--ci)"
PASTILLE = "align-self:flex-start;background:var(--c);color:var(--co);font-size:24px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;padding:10px 28px;border-radius:999px"
MONO = "font-family:ui-monospace,Menlo,Consolas,monospace"


def g(texte, couleur="#1F1F24") -> str:
    """Texte avec **gras** (le gras prend la couleur du titre)."""
    return ch.html_gras(texte or "", "color:{}".format(couleur) if couleur else "")


def puce(texte: str, taille=30, marge=15) -> str:
    return (
        '<li style="display:flex;gap:20px"><span style="width:12px;height:12px;background:var(--c);border-radius:2px;'
        'margin-top:{}px;flex-shrink:0"></span><span>{}</span></li>'.format(marge, texte)
    )


def point(p) -> str:
    """Point de liste : « texte » ou {label, texte} → <strong>label</strong> : texte."""
    if isinstance(p, dict):
        label, texte = p.get("label", ""), p.get("texte", "")
        return ('<strong style="color:#1F1F24">{}</strong>&nbsp;: {}'.format(esc(label), g(texte))) if label else g(texte)
    return g(p)


def photo(url: str, style: str, position="center") -> str:
    if not url:
        return vide("Photo", style)
    return '<div style="{};background:#DADADF url(&quot;{}&quot;) {}/cover no-repeat;filter:saturate(1.2) contrast(1.05)"></div>'.format(
        style, _html.escape(url, quote=True), position
    )


def visuel(url: str, libelle: str, style: str, rayon=16, fond=True) -> str:
    """Capture ou schéma (contain) dans un cadre gris ; emplacement vide si pas d'image."""
    if not url:
        return vide(libelle, style, rayon)
    return '<div style="{};border-radius:{}px;background:{} url(&quot;{}&quot;) center/contain no-repeat"></div>'.format(
        style, rayon, "#F6F6F7" if fond else "transparent", _html.escape(url, quote=True)
    )


def vide(libelle: str, style: str, rayon=16) -> str:
    return (
        '<div class="vide" style="{};border-radius:{}px"><i class="ic" style="--i:url({})"></i><span>{}</span></div>'.format(
            style, rayon, ch.icone_data_uri("image"), esc(libelle)
        )
    )


def sticker(position: str, taille: int, rotation: int, icone: str | None) -> str:
    """Sticker du design system ; icone None = icône de la catégorie."""
    rayon, marge, trait = round(taille * 0.28), round(taille * 0.073), 4 if taille < 150 else 5
    image = "var(--si)" if icone is None else "url({})".format(ch.icone_data_uri(icone))
    return (
        '<div class="stk" aria-hidden="true" style="position:absolute;{pos};width:{t}px;height:{t}px;transform:rotate({r}deg);'
        'border-radius:{ra}px;padding:{m}px"><div style="border:{tr}px solid #1F1F24;border-radius:{ri}px">'
        '<i class="ic" style="--i:{im};width:48%;height:48%"></i></div></div>'
    ).format(pos=position, t=taille, r=rotation, ra=rayon, m=marge, tr=trait, ri=rayon - marge, im=image)


def pied(intitule: str, couleur=False) -> str:
    if couleur:
        return (
            '<div class="pied pied-c"><span>{}</span><img src="{}" alt="Skazy Formation" style="filter:var(--lf)">'
            '<span class="pn"></span></div>'
        ).format(esc(intitule), ch.logo_svg_data_uri("blanc"))
    return '<div class="pied"><span>{}</span><img src="{}" alt="Skazy Formation"><span class="pn"></span></div>'.format(
        esc(intitule), ch.logo_svg_data_uri("couleur")
    )


def colorer_code(code: str) -> str:
    """Coloration minimale : FONCTION( en couleur de catégorie, "chaînes" en jaune."""
    sortie = _html.escape(code or "")
    sortie = re.sub(r"(&quot;.*?&quot;|'.*?')", r'<span style="color:#FFD58A">\1</span>', sortie)
    sortie = re.sub(r"\b([A-Z][A-Z0-9_.]{1,})(?=\()", r'<span style="color:var(--c)">\1</span>', sortie)
    return sortie


# ---------------------------------------------------------------- mises en page


def couverture(s, f):
    return """<div style="position:absolute;left:0;top:0;bottom:0;width:960px;background:#DADADF url(&quot;{photo}&quot;) center/cover;filter:saturate(1.25) contrast(1.06)"></div>
<div style="position:absolute;top:0;right:0;bottom:0;width:960px;background:var(--c)"></div>
<div style="position:absolute;top:0;bottom:0;right:0;width:960px;padding:110px 120px 100px;display:flex;flex-direction:column;color:var(--co)">
<div role="img" aria-label="Skazy Formation" style="width:322px;height:106px;flex-shrink:0;background:var(--logo) left center/contain no-repeat"></div>
<div style="margin:auto 0;display:flex;flex-direction:column;gap:32px">
<h1 style="margin:0;font-size:{taille}px;font-weight:700;line-height:1;letter-spacing:-.02em;text-wrap:balance">{intitule}</h1>
<div style="display:flex;gap:14px;flex-wrap:wrap"><span class="pl">{cat}</span><span class="pl">{niveau}</span></div>
<div style="font-size:28px;font-weight:500">{duree}</div>
</div>
<div style="font-size:28px;line-height:1.45"><div style="font-weight:700">{formateur}</div><div>{email}</div></div>
</div>""".format(
        photo=_html.escape(s.get("photo") or f["_couverture"], quote=True),
        taille=104 if len(f["intitule"]) <= 30 else 84,
        intitule=esc(f["intitule"]),
        cat=esc(f["categorie"]),
        niveau=esc(f["niveau"]),
        duree=esc(f["duree"]),
        formateur=esc(f["formateur"]),
        email=esc(f["email"]),
    )


def faisons_connaissance(s, f):
    infos = "".join(puce(point(x), 28, 14) for x in s.get("infos") or [])
    tour = "".join(
        '<div style="display:flex;align-items:center;gap:28px"><span class="rond" style="width:64px;height:64px;font-size:28px">{}</span>'
        '<span style="font-size:36px;font-weight:500">{}</span></div>'.format(k, g(t))
        for k, t in enumerate(s["tourDeTable"], 1)
    )
    portrait = (
        photo(s["photo"], "width:200px;height:200px;flex-shrink:0;border-radius:50%")
        if s.get("photo")
        else '<div style="width:200px;height:200px;flex-shrink:0;border-radius:50%;background:var(--ct);display:flex;align-items:center;justify-content:center"><i class="ic" style="--i:url({});width:96px;height:96px;background:var(--ci)"></i></div>'.format(ch.icone_data_uri("user-round"))
    )
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 72px;display:grid;grid-template-columns:640px 1fr;gap:96px">
<div style="display:flex;flex-direction:column;justify-content:center;gap:40px">
<h2 style="{h2}">{titre}</h2>
<div style="display:flex;align-items:center;gap:32px">{portrait}<div><div style="font-size:38px;font-weight:700">{formateur}</div><div style="font-size:26px;color:#55555E;margin-top:6px">{role}</div></div></div>
<ul class="liste" style="font-size:28px;color:#45454F;line-height:1.4;gap:18px">{infos}</ul>
</div>
<div style="background:var(--ct);border-radius:32px;padding:64px 72px;display:flex;flex-direction:column;gap:36px;justify-content:center">
<div style="{surtitre}">Tour de table</div>
{tour}
</div>
</div>""".format(
        h2=H2, titre=esc(s.get("titre") or "Faisons connaissance"), portrait=portrait, formateur=esc(f["formateur"]),
        role=esc(f["role"]), infos=infos, surtitre=SURTITRE, tour=tour,
    ) + (sticker("top:70px;right:90px", 150, 8, "hand") if f["stickers"] else "")


def objectifs(s, f):
    lignes = "".join(
        '<div style="display:flex;gap:28px;align-items:baseline"><span style="font-size:28px;font-weight:800;color:var(--ci);min-width:48px">{:02d}</span>'
        '<span style="font-size:{}px;line-height:1.4;color:#45454F">{}</span></div>'.format(k, 34 if len(s["objectifs"]) <= 4 else 30, g(o))
        for k, o in enumerate(s["objectifs"], 1)
    )
    return """<div style="position:absolute;top:0;right:0;bottom:80px;width:760px">{photo}</div>
<div style="position:absolute;top:0;left:0;bottom:80px;width:1160px;padding:96px 96px 80px 120px;display:flex;flex-direction:column">
<h2 style="{h2}">{titre}</h2>
<p style="margin:20px 0 0;font-size:30px;color:#55555E">{intro}</p>
<div style="margin-top:auto;display:flex;flex-direction:column;gap:34px">{lignes}</div>
</div>""".format(
        photo=photo(s.get("photo"), "width:100%;height:100%"), h2=H2, titre=esc(s.get("titre") or "Objectifs pédagogiques"),
        intro=esc(s.get("intro") or "À la fin de la formation, vous serez capable de :"), lignes=lignes,
    ) + (sticker("top:150px;left:1075px", 170, -10, "target") if f["stickers"] else "")


def programme(s, f):
    parties = s["parties"]
    taille = 32 if len(parties) <= 8 else 28
    lignes = "".join(
        '<div style="display:grid;grid-template-columns:64px 1fr auto;align-items:baseline;column-gap:20px;padding:{pad}px 0;{bord}font-size:{t}px">'
        '<span style="font-weight:800">{k}.</span><span style="font-weight:600">{titre}</span><span style="font-size:26px;font-weight:500">{duree}</span></div>'.format(
            pad=20 if len(parties) <= 8 else 14,
            bord="" if k == len(parties) else "border-bottom:2px solid {};".format(ch.melange(f["_cat"]["surCouleur"], f["_cat"]["couleur"], 0.14)),
            t=taille, k=k, titre=esc(p["titre"] if isinstance(p, dict) else p), duree=esc(p.get("duree", "") if isinstance(p, dict) else ""),
        )
        for k, p in enumerate(parties, 1)
    )
    return """<div style="position:absolute;top:0;left:0;bottom:80px;width:820px;padding:96px 80px 80px 120px;display:flex;flex-direction:column">
<h2 style="{h2}">{titre}</h2>
<p style="margin:16px 0 0;font-size:30px;color:#55555E">{duree}</p>
<div style="flex:1;min-height:0;display:flex;align-items:center;justify-content:center;margin-left:-60px"><div style="flex-shrink:0;width:440px;height:380px;background:#fff;padding:18px 18px 56px;box-shadow:0 16px 40px rgba(0,0,0,.14);transform:rotate(-4deg)">{photo}</div></div>
</div>
{sticker}
<div style="position:absolute;top:0;right:0;bottom:80px;width:1100px;background:var(--c);color:var(--co);padding:80px 110px;display:flex;flex-direction:column;justify-content:center">{lignes}</div>""".format(
        h2=H2, titre=esc(s.get("titre") or "Programme"), duree=esc(s.get("duree") or f["duree"]),
        photo=photo(s.get("photo"), "width:100%;height:100%"),
        sticker=sticker("top:690px;left:530px", 140, 10, None) if f["stickers"] else "", lignes=lignes,
    )


def chapitre(s, f):
    points = "".join(
        '<li style="display:flex;gap:20px;align-items:center"><span style="width:12px;height:12px;background:var(--c);border-radius:2px;flex-shrink:0"></span>{}</li>'.format(g(p))
        for p in s.get("points") or []
    )
    duree = '<span style="background:var(--ct);color:var(--ci);font-size:28px;font-weight:800;padding:12px 30px;border-radius:999px;white-space:nowrap">{}</span>'.format(esc(s["duree"])) if s.get("duree") else ""
    return """<div style="position:absolute;top:0;right:0;bottom:80px;width:760px">{photo}</div>
<div style="position:absolute;top:0;left:0;bottom:80px;width:1160px;padding:88px 96px 88px 120px;display:flex;flex-direction:column">
<div style="display:flex;justify-content:space-between;align-items:flex-start"><span style="font-size:200px;font-weight:800;line-height:.85;color:var(--c);letter-spacing:-.04em">{num:02d}</span>{duree}</div>
<h2 style="margin:40px 0 0;font-size:{taille}px;font-weight:600;line-height:1.02;letter-spacing:-.015em">{titre}</h2>
<ul style="list-style:none;margin:auto 0 0;padding:0;display:flex;flex-direction:column;gap:18px;font-size:32px;color:#45454F">{points}</ul>
</div>""".format(
        photo=photo(s.get("photo"), "width:100%;height:100%"), num=int(s["numero"]), duree=duree,
        taille=88 if len(s["titre"]) <= 40 else 72, titre=esc(s["titre"]), points=points,
    ) + (sticker("bottom:150px;left:1080px", 160, -8, None) if f["stickers"] else "")


def contenu(s, f):
    points = "".join(puce(point(p)) for p in s.get("points") or [])
    texte = '<p style="margin:0;font-size:32px;line-height:1.55;color:#45454F">{}</p>'.format(g(s["texte"])) if s.get("texte") else ""
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:grid;grid-template-columns:1fr 760px;gap:96px">
<div style="display:flex;flex-direction:column;gap:36px">
<h2 style="{h2}">{titre}</h2>
{texte}
<ul class="liste" style="gap:22px;font-size:30px;line-height:1.45;color:#45454F">{points}</ul>
</div>
<div style="background:#F6F6F7;border-radius:28px;padding:28px;align-self:center;height:640px">{visuel}</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), texte=texte, points=points,
                 visuel=visuel(s.get("image"), s.get("legendeImage") or "Capture d'écran ou schéma", "width:100%;height:100%", fond=False))


def chiffre_cle(s, f):
    reperes = "".join(
        '<div style="background:var(--ct);border-radius:24px;padding:32px 36px;display:flex;flex-direction:column;gap:10px"><span style="font-size:64px;font-weight:800;line-height:1;color:var(--ci)">{}</span><span style="font-size:26px;line-height:1.4;color:#3B3B42">{}</span></div>'.format(esc(x.get("valeur")), g(x.get("texte")))
        for x in s.get("reperes") or []
    )
    source = '<span style="font-size:24px;color:#6E6E78">Source&nbsp;: {}</span>'.format(esc(s["source"])) if s.get("source") else ""
    chiffre = str(s["chiffre"])
    taille = 280 if len(chiffre) <= 3 else (220 if len(chiffre) <= 5 else 160)
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:grid;grid-template-columns:1fr 1fr;gap:120px;align-items:center">
<div style="display:flex;flex-direction:column;gap:32px"><span style="font-size:{taille}px;font-weight:800;line-height:.85;letter-spacing:-.04em;color:var(--ci)">{chiffre}<span style="font-size:{tu}px">{unite}</span></span><span style="font-size:44px;font-weight:700;line-height:1.2;text-wrap:balance">{phrase}</span></div>
<div style="display:flex;flex-direction:column;gap:40px"><p style="margin:0;font-size:34px;line-height:1.5;color:#45454F">{explication}</p><div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">{reperes}</div>{source}</div>
</div>""".format(taille=taille, chiffre=esc(chiffre), tu=round(taille * 0.54), unite=esc(s.get("unite", "")), phrase=g(s["phrase"]),
                 explication=g(s.get("explication", "")), reperes=reperes, source=source)


def frise(s, f):
    etapes = s["etapes"]
    cols = []
    for k, e in enumerate(etapes):
        derniere = k == len(etapes) - 1
        bloc = '<div style="align-self:{al};display:flex;flex-direction:column;gap:10px"><span style="font-size:52px;font-weight:800;line-height:1;color:{c}">{d}</span><span style="font-size:28px;line-height:1.4;color:#45454F">{t}</span></div>'.format(
            al="end" if k % 2 == 0 else "start", c="var(--ci)" if derniere else "#1F1F24", d=esc(e.get("date")), t=g(e.get("texte")))
        rond = '<span style="width:36px;height:36px;border-radius:50%;background:{};border:6px solid var(--c)"></span>'.format("var(--c)" if derniere else "#fff")
        haut, bas = (bloc, "<div></div>") if k % 2 == 0 else ("<div></div>", bloc)
        cols.append('<div style="position:relative;display:grid;grid-template-rows:1fr auto 1fr;gap:32px">{}{}{}</div>'.format(haut, rond, bas))
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:flex;flex-direction:column;gap:20px">
<h2 style="{h2}">{titre}</h2>
<p style="margin:0;font-size:30px;color:#55555E">{intro}</p>
<div style="flex:1;position:relative;display:grid;grid-template-columns:repeat({n},1fr);gap:32px">
<div style="position:absolute;left:0;right:0;top:50%;height:6px;transform:translateY(-50%);background:var(--ct);border-radius:3px"></div>
{cols}
</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), intro=g(s.get("intro", "")), n=len(etapes), cols="".join(cols))


def graphique(s, f):
    barres = s["barres"]
    valeurs = [float(b.get("valeur", 0)) for b in barres]
    maxi = max(valeurs) or 1
    cible = s.get("miseEnAvant", len(barres) - 1)
    colonnes = "".join(
        '<div style="height:100%;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:14px"><span style="font-size:28px;font-weight:800;color:{c}">{v}</span><div style="width:100%;height:calc((100% - 56px) * {h:.2f});background:{b};border-radius:12px 12px 0 0"></div></div>'.format(
            c="var(--ci)" if k == cible else "#55555E", v=esc(b.get("affichage") or _nombre(b.get("valeur"))), h=valeurs[k] / maxi,
            b="var(--c)" if k == cible else "#D9D9DE")
        for k, b in enumerate(barres)
    )
    labels = "".join('<span style="text-align:center;font-size:24px;font-weight:600;color:#6E6E78">{}</span>'.format(esc(b.get("label"))) for b in barres)
    source = '<span style="font-size:24px;color:#6E6E78">Source&nbsp;: {}</span>'.format(esc(s["source"])) if s.get("source") else ""
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:grid;grid-template-columns:1fr 600px;gap:120px">
<div style="display:flex;flex-direction:column;gap:40px;min-height:0">
<h2 style="{h2}">{titre}</h2>
<div style="flex:1;min-height:0;display:grid;grid-template-columns:repeat({n},1fr);gap:28px;border-bottom:3px solid #1F1F24;padding:0 8px">{colonnes}</div>
<div style="display:grid;grid-template-columns:repeat({n},1fr);gap:28px;padding:0 8px;margin-top:-20px">{labels}</div>
</div>
<div style="display:flex;flex-direction:column;justify-content:center;gap:28px"><span style="{surtitre}">{surtitre_txt}</span><span style="font-size:128px;font-weight:800;line-height:.9;letter-spacing:-.02em;color:var(--ci)">{chiffre}</span><p style="margin:0;font-size:32px;line-height:1.5;color:#45454F">{message}</p>{source}</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), n=len(barres), colonnes=colonnes, labels=labels, surtitre=SURTITRE,
                 surtitre_txt=esc(s.get("surtitre") or "À retenir"), chiffre=esc(s.get("chiffre", "")), message=g(s.get("message", "")), source=source)


def _nombre(v) -> str:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v or "")
    return ("{:,.0f}" if x == int(x) else "{:,.1f}").format(x).replace(",", " ").replace(".", ",")


def image(s, f):
    return """{fond}
<div style="position:absolute;left:120px;bottom:120px;max-width:1040px;background:#fff;border-radius:28px;padding:48px 56px;display:flex;flex-direction:column;gap:16px;box-shadow:0 20px 50px rgba(0,0,0,.25)"><span style="{surtitre}">{surtitre_txt}</span><span style="font-size:56px;font-weight:700;line-height:1.1;text-wrap:balance">{titre}</span><span style="font-size:28px;line-height:1.45;color:#45454F">{texte}</span></div>
<span class="pn" style="position:absolute;right:64px;bottom:48px;background:#fff;border-radius:999px;padding:8px 22px;font-size:24px;font-weight:700;color:#1F1F24"></span>""".format(
        fond=photo(s.get("image"), "position:absolute;inset:0"), surtitre=SURTITRE, surtitre_txt=esc(s.get("surtitre") or "Légende"),
        titre=esc(s["titre"]), texte=g(s.get("texte", "")))


def texte(s, f):
    paragraphes = "".join('<p style="margin:0 0 28px;break-inside:avoid-column">{}</p>'.format(g(p)) for p in s["paragraphes"])
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:grid;grid-template-columns:520px 1fr;gap:120px">
<div style="display:flex;flex-direction:column;gap:32px"><span style="width:96px;height:10px;background:var(--c);border-radius:5px"></span><h2 style="{h2}">{titre}</h2><p style="margin:0;font-size:30px;line-height:1.5;color:#55555E">{intro}</p></div>
<div style="align-self:center;column-count:{cols};column-gap:72px;font-size:30px;line-height:1.6;color:#3B3B42">{paragraphes}</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), intro=g(s.get("intro", "")), cols=2 if len(s["paragraphes"]) > 1 else 1, paragraphes=paragraphes)


def citation(s, f):
    auteur = s.get("auteur") or ""
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:120px 200px;display:flex;flex-direction:column;justify-content:center;gap:56px">
<span style="font-size:220px;font-weight:800;line-height:.6;height:110px">«</span>
<p style="margin:0;font-size:{taille}px;font-weight:600;line-height:1.2;letter-spacing:-.01em;max-width:1500px">{citation}</p>
<div style="display:flex;align-items:center;gap:28px"><span style="width:120px;height:120px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;flex-shrink:0"><i class="ic" style="--i:url({icone});width:64px;height:64px"></i></span><div style="font-size:34px;font-weight:700">{auteur}</div></div>
</div>""".format(taille=72 if len(s["citation"]) <= 100 else 60, citation=g(s["citation"], ""), icone=ch.icone_data_uri("user-round"), auteur=esc(auteur))


def avant_apres(s, f):
    def cote(d, libelle, style_pastille):
        return '<div style="display:flex;flex-direction:column;gap:28px;min-height:0"><div style="flex:1;min-height:0;background:#F6F6F7;border-radius:28px;padding:20px">{}</div><div style="display:flex;gap:24px;align-items:center"><span style="{};font-size:24px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;padding:10px 26px;border-radius:999px;flex-shrink:0">{}</span><span style="font-size:30px;line-height:1.4;color:#45454F">{}</span></div></div>'.format(
            visuel(d.get("image"), "Capture " + libelle.lower(), "width:100%;height:100%", fond=False), style_pastille, libelle, g(d.get("texte")))

    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:flex;flex-direction:column;gap:48px">
<h2 style="{h2}">{titre}</h2>
<div style="flex:1;min-height:0;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:minmax(0,1fr);gap:48px">{avant}{apres}</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), avant=cote(s["avant"], "Avant", "background:#E4E4E8;color:#1F1F24"),
                 apres=cote(s["apres"], "Après", "background:var(--c);color:var(--co)"))


def notion_cle(s, f):
    termes = "".join(
        '<span style="background:#fff;border-radius:18px;padding:18px 28px;font-size:28px;color:#45454F"><code style="{mono};font-weight:700;color:var(--ci);margin-right:14px">{}</code>{}</span>'.format(esc(t.get("terme")), g(t.get("definition")), mono=MONO)
        for t in s.get("termes") or []
    )
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:120px 160px;display:flex;flex-direction:column;justify-content:center;gap:40px">
<span style="{pastille}">{surtitre}</span>
<h2 style="margin:0;font-size:{taille}px;font-weight:700;line-height:1;letter-spacing:-.02em">{titre}</h2>
<p style="margin:0;font-size:44px;line-height:1.4;color:#3B3B42;max-width:1400px">{definition}</p>
<div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:16px">{termes}</div>
</div>""".format(pastille=PASTILLE, surtitre=esc(s.get("surtitre") or "Notion clé"), taille=112 if len(s["titre"]) <= 26 else 84,
                 titre=esc(s["titre"]), definition=g(s["definition"]), termes=termes)


def code(s, f):
    elements = "".join(
        '<div><code style="{mono};font-weight:700;color:var(--ci)">{}</code><br>{}</div>'.format(esc(x.get("code")), g(x.get("texte")), mono=MONO)
        for x in s.get("elements") or []
    )
    exemple = ""
    if s.get("exemple"):
        exemple = '<div style="height:2px;background:rgba(255,255,255,.12);margin:12px 0"></div><span style="font-size:24px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#A8A8B3">Exemple</span><pre style="margin:0;{mono};font-size:34px;line-height:1.5;white-space:pre-wrap">{}</pre>'.format(colorer_code(s["exemple"]), mono=MONO)
    resultat = '<span style="font-size:28px;color:#D4D4DA">{}</span>'.format(g(s["resultat"], "#fff")) if s.get("resultat") else ""
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:grid;grid-template-columns:1fr 860px;gap:96px;align-items:center">
<div style="display:flex;flex-direction:column;gap:36px">
<h2 style="{h2}">{titre}</h2>
<p style="margin:0;font-size:32px;line-height:1.55;color:#45454F">{intro}</p>
<div style="display:flex;flex-direction:column;gap:24px;font-size:28px;line-height:1.45;color:#45454F">{elements}</div>
</div>
<div style="background:#1E1E24;border-radius:28px;padding:52px 56px;display:flex;flex-direction:column;gap:22px;color:#fff">
<span style="font-size:24px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#A8A8B3">{libelle}</span>
<pre style="margin:0;{mono};font-size:34px;line-height:1.5;white-space:pre-wrap">{syntaxe}</pre>
{exemple}
{resultat}
</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), intro=g(s.get("intro", "")), elements=elements, libelle=esc(s.get("libelle") or "Syntaxe"),
                 mono=MONO, syntaxe=colorer_code(s["syntaxe"]), exemple=exemple, resultat=resultat)


def capture(s, f):
    reperes = s["reperes"]
    pastilles = "".join(
        '<span class="rond" style="position:absolute;left:calc({x}% - 32px);top:calc({y}% - 32px);width:64px;height:64px;font-size:28px;border:4px solid #fff;box-shadow:0 6px 16px rgba(0,0,0,.2)">{k}</span>'.format(
            x=float(r.get("x", 15 + 70 * ((k - 1) % 2))), y=float(r.get("y", 15 + 25 * ((k - 1) // 2))), k=k)
        for k, r in enumerate(reperes, 1)
    )
    legendes = "".join(
        '<div style="display:flex;gap:22px"><span style="font-size:32px;font-weight:800;color:var(--ci);min-width:28px">{k}</span><span style="font-size:28px;line-height:1.4;color:#45454F"><strong style="color:#1F1F24;display:block;font-size:32px">{t}</strong>{x}</span></div>'.format(
            k=k, t=esc(r.get("titre")), x=g(r.get("texte")))
        for k, r in enumerate(reperes, 1)
    )
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:88px 120px 72px;display:flex;flex-direction:column;gap:44px">
<h2 style="{h2}">{titre}</h2>
<div style="flex:1;display:grid;grid-template-columns:1140px 1fr;grid-template-rows:minmax(0,1fr);gap:72px;min-height:0">
<div style="position:relative;background:#F6F6F7;border-radius:24px;padding:20px"><div style="position:relative;width:100%;height:100%">{visuel}{pastilles}</div></div>
<div style="display:flex;flex-direction:column;justify-content:center;gap:36px">{legendes}</div>
</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), visuel=visuel(s.get("image"), "Capture d'écran à annoter", "position:absolute;inset:0", 12, fond=False),
                 pastilles=pastilles, legendes=legendes)


def pas_a_pas(s, f):
    etapes = s["etapes"]
    blocs = "".join(
        '<div style="display:flex;flex-direction:column;gap:28px"><div style="height:260px;background:#F6F6F7;border-radius:20px;padding:12px">{v}</div><span class="rond" style="width:64px;height:64px;font-size:28px">{k}</span><p style="margin:0;font-size:30px;line-height:1.4;color:#45454F">{t}</p></div>'.format(
            v=visuel((e or {}).get("image") if isinstance(e, dict) else "", "Capture étape {}".format(k), "width:100%;height:100%", 12, fond=False),
            k=k, t=g(e.get("texte") if isinstance(e, dict) else e))
        for k, e in enumerate(etapes, 1)
    )
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:flex;flex-direction:column;gap:64px">
<h2 style="{h2}">{titre}</h2>
<div style="flex:1;display:grid;grid-template-columns:repeat({n},1fr);gap:32px">{blocs}</div>
</div>""".format(h2=H2, titre=esc(s["titre"]), n=len(etapes), blocs=blocs)


def comparatif(s, f):
    a, b = (s["colonnes"] + ["", ""])[:2]
    cellules = '<div style="background:#F4F4F5;padding:26px 32px"></div><div style="background:#F4F4F5;padding:26px 32px;font-size:30px;font-weight:800">{}</div><div style="background:var(--c);color:var(--co);padding:26px 32px;font-size:30px;font-weight:800">{}</div>'.format(esc(a), esc(b))
    for ligne in s["lignes"]:
        v = (ligne.get("valeurs") or []) + ["", ""]
        cellules += '<div style="padding:26px 32px;font-weight:700;border-top:2px solid #EEEEF0">{}</div><div style="padding:26px 32px;color:#45454F;border-top:2px solid #EEEEF0">{}</div><div style="padding:26px 32px;border-top:2px solid #EEEEF0;background:var(--ct)">{}</div>'.format(
            esc(ligne.get("critere")), g(v[0]), g(v[1]))
    reco = '<p style="margin:0;font-size:28px;color:#55555E"><strong style="color:var(--ci)">Recommandation</strong>&nbsp;: {}</p>'.format(g(s["recommandation"])) if s.get("recommandation") else ""
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 72px;display:flex;flex-direction:column;gap:56px">
<h2 style="{h2}">{titre}</h2>
<div style="display:grid;grid-template-columns:440px 1fr 1fr;font-size:28px;line-height:1.4;border-radius:24px;overflow:hidden;border:2px solid #EEEEF0">{cellules}</div>
{reco}
</div>""".format(h2=H2, titre=esc(s["titre"]), cellules=cellules, reco=reco)


def raccourcis(s, f):
    kbd = 'font:700 26px Raleway,sans-serif;color:#1F1F24;background:#fff;border:2px solid #D9D9DE;border-bottom-width:5px;border-radius:12px;padding:6px 18px'
    items = "".join(
        '<div style="display:grid;grid-template-columns:320px 1fr;align-items:center;gap:24px;background:#F6F6F7;border-radius:20px;padding:20px 32px"><span style="display:flex;gap:10px;align-items:center;font-size:24px;color:#9A9AA6">{}</span><span style="font-size:30px">{}</span></div>'.format(
            "+".join('<kbd style="{}">{}</kbd>'.format(kbd, esc(t)) for t in touches(r)), esc(r.get("action")))
        for r in s["raccourcis"]
    )
    remarque = '<span style="font-size:26px;color:#6E6E78">{}</span>'.format(g(s["remarque"])) if s.get("remarque") else ""
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 72px;display:flex;flex-direction:column;gap:56px">
<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:40px"><h2 style="{h2}">{titre}</h2>{remarque}</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px 40px">{items}</div>
</div>""".format(h2=H2, titre=esc(s.get("titre") or "Raccourcis à connaître"), remarque=remarque, items=items)


GENRES = {
    "astuce": ("Astuce", "var(--ct)", "var(--ci)"),
    "attention": ("Attention", "#FFF4DE", "#8A5A00"),
    "bonne-pratique": ("Bonne pratique", "#E8F5F0", "#3D7A62"),
}


def genre_encadre(e: dict) -> tuple[str, str, str]:
    cle = ch.normaliser(e.get("genre", "astuce")).replace(" ", "-")
    return GENRES.get(cle, GENRES["astuce"])


def bon_a_savoir(s, f):
    blocs = ""
    for e in s["encadres"]:
        libelle, fond, encre = genre_encadre(e)
        blocs += '<div style="background:{};border-radius:28px;padding:48px;display:flex;flex-direction:column;gap:24px"><span style="font-size:24px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:{}">{}</span><span style="font-size:40px;font-weight:700;line-height:1.15">{}</span><p style="margin:0;font-size:30px;line-height:1.5;color:#3B3B42">{}</p></div>'.format(
            fond, encre, esc(e.get("libelle") or libelle), esc(e.get("titre")), g(e.get("texte")))
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:flex;flex-direction:column;gap:56px">
<h2 style="{h2}">{titre}</h2>
<div style="flex:1;display:grid;grid-template-columns:repeat({n},1fr);gap:32px">{blocs}</div>
</div>""".format(h2=H2, titre=esc(s.get("titre") or "Bon à savoir"), n=len(s["encadres"]), blocs=blocs)


def exercice(s, f):
    consignes = "".join(
        '<li style="display:flex;gap:22px;align-items:flex-start;font-size:30px;line-height:1.4;color:#45454F"><span class="rond" style="width:48px;height:48px;font-size:24px">{}</span><span>{}</span></li>'.format(k, g(c))
        for k, c in enumerate(s["consignes"], 1)
    )
    carte = '<div style="background:#fff;border-radius:22px;padding:28px 32px;display:flex;flex-direction:column;gap:6px"><span style="font-size:24px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--ci)">{}</span><span style="{}">{}</span></div>'
    cartes = ""
    if s.get("duree"):
        cartes += carte.format("Durée", "font-size:34px;font-weight:700", esc(s["duree"]))
    if s.get("fichier"):
        cartes += carte.format("Fichier", "font-size:30px;font-weight:600;" + MONO, esc(s["fichier"]))
    if s.get("livrable"):
        cartes += carte.format("Livrable", "font-size:28px;line-height:1.4", g(s["livrable"]))
    if s.get("bonus"):
        cartes += '<div style="background:var(--c);color:var(--co);border-radius:22px;padding:28px 32px;display:flex;flex-direction:column;gap:6px"><span style="font-size:24px;font-weight:800;letter-spacing:.1em;text-transform:uppercase">Pour aller plus loin</span><span style="font-size:28px;line-height:1.4;font-weight:600">{}</span></div>'.format(g(s["bonus"], ""))
    return """<div style="position:absolute;top:0;right:0;bottom:80px;width:760px;background:#F6F6F7"></div>
<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:88px 120px 80px;display:grid;grid-template-columns:1fr 560px;gap:200px">
<div style="display:flex;flex-direction:column;gap:32px">
<span style="{pastille}">Exercice {num}</span>
<h2 style="margin:0;font-size:64px;font-weight:600;line-height:1.08;letter-spacing:-.01em">{titre}</h2>
<p style="margin:0;font-size:30px;line-height:1.5;color:#45454F">{contexte}</p>
<ol style="list-style:none;margin:8px 0 0;padding:0;display:flex;flex-direction:column;gap:20px">{consignes}</ol>
</div>
<div style="display:flex;flex-direction:column;gap:20px;justify-content:center">{cartes}</div>
</div>""".format(pastille=PASTILLE, num=s["numero"], titre=esc(s["titre"]), contexte=g(s.get("contexte", "")), consignes=consignes, cartes=cartes)


def exercice_etapes(s, f):
    etapes = "".join(
        '<div style="background:#F6F6F7;border-radius:28px;padding:40px 44px;display:flex;flex-direction:column;gap:18px"><span style="font-size:96px;font-weight:800;line-height:.9;color:var(--ci)">{}</span><span style="font-size:34px;font-weight:700;line-height:1.2">{}</span><span style="font-size:28px;line-height:1.45;color:#45454F">{}</span></div>'.format(
            k, esc(e.get("titre") if isinstance(e, dict) else ""), g(e.get("texte") if isinstance(e, dict) else e))
        for k, e in enumerate(s["etapes"], 1)
    )
    infos = ""
    for libelle, cle, style in (("Fichier", "fichier", MONO + ";color:#1F1F24"), ("Modalité", "modalite", ""), ("Livrable", "livrable", "")):
        if s.get(cle):
            infos += '<span><strong style="color:var(--ci)">{}</strong>&nbsp;: <span style="{}">{}</span></span>'.format(libelle, style, g(s[cle]))
    duree = str(s.get("duree", "")).strip()
    nombre, _, unite = duree.partition(" ")
    if not nombre.isdigit():
        nombre, unite = duree, ""
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:88px 120px 64px;display:flex;flex-direction:column;gap:44px">
<div style="display:flex;justify-content:space-between;align-items:center;gap:60px">
<div style="display:flex;flex-direction:column;gap:24px;max-width:1200px"><span style="{pastille}">Exercice {num}</span><h2 style="margin:0;font-size:64px;font-weight:600;line-height:1.08;letter-spacing:-.01em">{titre}</h2><p style="margin:0;font-size:30px;line-height:1.5;color:#45454F">{contexte}</p></div>
<div style="flex-shrink:0;width:240px;height:240px;border-radius:50%;border:10px solid var(--c);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px"><span style="font-size:{tn}px;font-weight:800;line-height:1;color:var(--ci)">{nombre}</span><span style="font-size:26px;font-weight:700;color:#55555E">{unite}</span></div>
</div>
<div style="flex:1;min-height:0;display:grid;grid-template-columns:repeat({n},1fr);gap:28px">{etapes}</div>
<div style="display:flex;flex-wrap:wrap;gap:20px 56px;align-items:center;border-top:2px solid #EEEEF0;padding-top:28px;font-size:28px;color:#45454F">{infos}</div>
</div>""".format(pastille=PASTILLE, num=s["numero"], titre=esc(s["titre"]), contexte=g(s.get("contexte", "")),
                 tn=84 if len(nombre) <= 3 else 56, nombre=esc(nombre or "–"), unite=esc(unite or ("minutes" if nombre.isdigit() else "")),
                 n=len(s["etapes"]), etapes=etapes, infos=infos)


def quiz(s, f):
    props = s["propositions"]
    tuiles = ""
    for k, p in enumerate(props):
        bonne = s["_reponse"] and k == s["bonne"]
        if bonne:
            tuiles += '<div style="background:var(--ct);border:4px solid var(--c);border-radius:28px;padding:0 44px;display:flex;align-items:center;gap:32px"><span style="width:72px;height:72px;border-radius:18px;background:var(--c);color:var(--co);display:flex;align-items:center;justify-content:center;font-size:34px;font-weight:800;flex-shrink:0">{l}</span><span style="font-size:40px;font-weight:600">{t}</span><span style="margin-left:auto;font-size:26px;font-weight:800;color:var(--ci);white-space:nowrap">Bonne réponse</span></div>'.format(l="ABCD"[k], t=esc(p))
        else:
            tuiles += '<div style="background:#F6F6F7;border:4px solid #F6F6F7;border-radius:28px;padding:0 44px;display:flex;align-items:center;gap:32px"><span style="width:72px;height:72px;border-radius:18px;background:#fff;color:#1F1F24;display:flex;align-items:center;justify-content:center;font-size:34px;font-weight:800;flex-shrink:0">{l}</span><span style="font-size:40px;font-weight:600">{t}</span></div>'.format(l="ABCD"[k], t=esc(p))
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:flex;flex-direction:column;gap:48px">
<div style="display:flex;align-items:center;gap:24px"><span style="background:var(--c);color:var(--co);font-size:24px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;padding:10px 28px;border-radius:999px">Quiz</span><span style="font-size:28px;font-weight:600;color:#6E6E78">Question {num} sur {total}</span></div>
<h2 style="margin:0;font-size:64px;font-weight:600;line-height:1.12;letter-spacing:-.01em;max-width:1500px">{question}</h2>
<div style="flex:1;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat({lignes},1fr);gap:28px">{tuiles}</div>
</div>""".format(num=s.get("numero", 1), total=s.get("total", 1), question=esc(s["question"]), lignes=(len(props) + 1) // 2, tuiles=tuiles)


def a_retenir(s, f):
    messages = "".join(
        '<div style="display:flex;gap:40px;align-items:baseline"><span style="font-size:72px;font-weight:800;color:var(--c);line-height:1;min-width:80px">{}</span><p style="margin:0;font-size:38px;line-height:1.4;color:#3B3B42">{}</p></div>'.format(k, g(m))
        for k, m in enumerate(s["messages"], 1)
    )
    return """<div style="position:absolute;top:0;left:0;bottom:80px;width:720px;background:var(--c);color:var(--co);padding:96px 80px 96px 120px;display:flex;flex-direction:column;justify-content:space-between">
<h2 style="margin:0;font-size:96px;font-weight:700;line-height:1;letter-spacing:-.02em">{titre}</h2>
<span style="font-size:28px;font-weight:600">{sous_titre}</span>
</div>
<div style="position:absolute;top:0;left:720px;right:0;bottom:80px;padding:96px 120px;display:flex;flex-direction:column;justify-content:center;gap:56px">{messages}</div>""".format(
        titre=esc(s.get("titre") or "À retenir"), sous_titre=esc(s.get("sousTitre", "")), messages=messages)


def ressources(s, f):
    blocs = ""
    for x in s["ressources"]:
        lien = x.get("lien") or ""
        skazy = x.get("skazy") or "skazy.nc" in lien
        affiche = re.sub(r"^https?://(www\.)?", "", lien).rstrip("/")
        blocs += '<div style="background:{};border-radius:28px;padding:44px 48px;display:flex;flex-direction:column;gap:14px"><span style="font-size:36px;font-weight:700">{}</span><span style="font-size:28px;line-height:1.45;color:#45454F;flex:1">{}</span>{}</div>'.format(
            "var(--ct)" if skazy else "#F6F6F7", esc(x.get("titre")), g(x.get("texte")),
            '<a href="{}" style="font-size:28px;font-weight:700;color:var(--ci)">{}</a>'.format(_html.escape(lien, quote=True), esc(affiche)) if lien else "")
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:flex;flex-direction:column;gap:56px">
<h2 style="{h2}">{titre}</h2>
<div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:28px">{blocs}</div>
</div>""".format(h2=H2, titre=esc(s.get("titre") or "Pour continuer"), blocs=blocs)


def evaluation(s, f):
    qr = visuel(s.get("qrCode"), "QR code", "width:100%;height:100%", 12, fond=False)
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:flex;flex-direction:column;gap:56px">
<h2 style="{h2}">{titre}</h2>
<div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:32px">
<div style="background:var(--ct);border-radius:32px;padding:56px;display:flex;flex-direction:column;gap:22px"><span style="{surtitre}">1 · Quiz final</span><span style="font-size:44px;font-weight:700;line-height:1.15">Mesurez votre progression</span><p style="margin:0;font-size:30px;line-height:1.5;color:#3B3B42;flex:1">Quelques questions pour vérifier ce que vous avez retenu de la formation.</p><span style="align-self:flex-start;background:var(--c);color:var(--co);font-size:30px;font-weight:800;padding:14px 32px;border-radius:999px">{acces}</span></div>
<div style="background:#F6F6F7;border-radius:32px;padding:56px;display:grid;grid-template-columns:1fr 280px;gap:40px;align-items:center"><div style="display:flex;flex-direction:column;gap:22px"><span style="{surtitre}">2 · Satisfaction</span><span style="font-size:44px;font-weight:700;line-height:1.15">Trois minutes, anonyme</span><p style="margin:0;font-size:30px;line-height:1.5;color:#3B3B42">Vos retours font évoluer la formation. Scannez le QR code.</p></div><div style="width:280px;height:280px;background:#fff;border-radius:24px;padding:16px">{qr}</div></div>
</div>
<p style="margin:0;font-size:28px;color:#55555E">{message}</p>
</div>""".format(h2=H2, titre=esc(s.get("titre") or "Votre avis compte"), surtitre=SURTITRE,
                 acces=esc(s.get("quiz") or "Sur kahoot.it, code affiché à l'écran"), qr=qr,
                 message=esc(s.get("message") or "Votre attestation de fin de formation vous parvient par e-mail."))


def questions(s, f):
    return """<div style="position:absolute;left:0;top:0;bottom:0;width:960px;background:#DADADF url(&quot;{photo}&quot;) right center/cover;filter:saturate(1.2) contrast(1.05)"></div>
<div style="position:absolute;top:0;right:0;bottom:0;width:960px;background:var(--c)"></div>
<div style="position:absolute;top:0;bottom:0;right:0;width:960px;padding:110px 120px 100px;display:flex;flex-direction:column;color:var(--co)">
<div role="img" aria-label="Skazy Formation" style="width:322px;height:106px;flex-shrink:0;background:var(--logo) left center/contain no-repeat"></div>
<h2 style="margin:auto 0;font-size:88px;font-weight:700;line-height:1.05;letter-spacing:-.02em;text-wrap:balance">{titre}</h2>
<div style="font-size:28px;line-height:1.45"><div style="font-weight:700">{formateur}</div><div>{email}</div></div>
</div>""".format(photo=_html.escape(ch.url_photo(s.get("photo") or ch.CHARTE["photoQuestions"]), quote=True),
                 titre=esc(s.get("titre") or "Avez-vous des questions ?"), formateur=esc(f["formateur"]), email=esc(f["email"]))


def battle(s, f):
    tirets = "border:3px dashed {}".format
    def equipe(nom, fond, couleur, bord, trait):
        return '<div style="background:{};color:{};{}border-radius:32px;padding:48px 52px;display:flex;flex-direction:column;gap:24px"><span style="font-size:24px;font-weight:800;letter-spacing:.14em;text-transform:uppercase">{}</span><div style="display:flex;flex-direction:column;gap:8px"><span style="font-size:26px;font-weight:700">Nom de l\'équipe</span><div style="height:110px;border-bottom:3px dashed {}"></div></div><div style="flex:1;min-height:120px;display:flex;flex-direction:column;gap:12px"><span style="font-size:26px;font-weight:700">Score</span><div style="flex:1;{};border-radius:20px"></div></div></div>'.format(
            fond, couleur, bord, nom, trait, tirets(trait))
    c = f["_cat"]
    regles = "".join(
        '<div style="display:flex;gap:18px;align-items:flex-start"><span class="rond" style="width:48px;height:48px;font-size:24px;background:var(--ct);color:var(--ci)">{}</span><span style="font-size:26px;line-height:1.4;color:#45454F">{}</span></div>'.format(k, g(r))
        for k, r in enumerate(s["regles"], 1)
    )
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:88px 120px 64px;display:flex;flex-direction:column;gap:44px">
<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:40px"><div style="display:flex;flex-direction:column;gap:24px"><span style="align-self:flex-start;display:inline-flex;align-items:center;gap:12px;background:#1F1F24;color:#fff;font-size:24px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;padding:10px 28px;border-radius:999px"><i class="ic" style="--i:url({zap});width:28px;height:28px;background:#fff"></i>Battle</span><h2 style="{h2}">{titre}</h2></div><span style="font-size:30px;color:#55555E;white-space:nowrap">{accroche}</span></div>
<div style="flex:1;min-height:0;display:grid;grid-template-columns:1fr auto 1fr;gap:40px">{a}<div style="display:flex;align-items:center"><span style="width:140px;height:140px;border-radius:50%;background:var(--ct);color:var(--ci);display:flex;align-items:center;justify-content:center;font-size:52px;font-weight:800">VS</span></div>{b}</div>
<div style="display:grid;grid-template-columns:repeat({n},1fr);gap:32px">{regles}</div>
</div>""".format(zap=ch.icone_data_uri("zap"), h2=H2, titre=esc(s.get("titre") or "Battle de questions"),
                 accroche=esc(s.get("accroche") or "Deux équipes, un objectif : piéger l'autre."),
                 a=equipe("Équipe A", "var(--c)", "var(--co)", "", ch.melange(c["surCouleur"], c["couleur"], 0.4)),
                 b=equipe("Équipe B", "#F6F6F7", "#1F1F24", "border:3px solid #E4E4E8;", "#A5A5A7"),
                 n=len(s["regles"]), regles=regles)


POLES = [
    ("com", "#FF6E3D", "Social media, publicité digitale, webmarketing, SEO, SEA, identité visuelle, print et édition"),
    ("numérique", "#009BCA", "Développement de logiciels, web et mobile, UX/UI design, hébergement"),
    ("data", "#B8901A", "Informatique décisionnelle, business intelligence, AMOA, modélisation, intégration et restitution de données"),
    ("formation", "#3D7A62", "Webmarketing, développement, data, web, gestion de projet, design, bureautique, NoCode et Intelligence Artificielle"),
]


def accompagnement_360(s, f):
    poles = "".join(
        '<div style="background:#F6F6F7;border-radius:28px;padding:48px 40px;display:flex;flex-direction:column;gap:28px"><span style="font-size:52px;font-weight:800;line-height:.9;color:#3B3B42;letter-spacing:-.02em">skazy<span style="display:block;font-size:30px;color:{};letter-spacing:0">{}</span></span><p style="margin:0;font-size:26px;line-height:1.5;color:#45454F">{}</p></div>'.format(c, esc(n), esc(t))
        for n, c, t in POLES
    )
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:96px 120px 80px;display:flex;flex-direction:column;gap:64px">
<div><h2 style="{h2}">Skazy</h2><p style="margin:6px 0 0;font-size:44px;font-weight:500;color:#3B3B42">Accompagnement 360°</p></div>
<div style="flex:1;display:grid;grid-template-columns:repeat(4,1fr);gap:28px">{poles}</div>
</div>""".format(h2=H2, poles=poles) + (sticker("top:80px;right:120px", 150, 8, "rocket") if f["stickers"] else "")


def autres_formations(s, f):
    tuiles = ""
    for c in ch.CHARTE["categories"]:
        blanc = c["surCouleur"].upper() == "#FFFFFF"
        tuiles += '<div style="position:relative;border-radius:22px;overflow:hidden;background:{fond}"><div style="position:absolute;inset:0 38% 0 0;clip-path:polygon(0 0,100% 0,78% 100%,0 100%);background:rgba(255,255,255,.24);display:flex;align-items:center;justify-content:center;padding:0 12% 64px 0"><i class="ic" style="--i:url({ic});width:84px;height:84px;background:{coul}"></i></div><span style="position:absolute;left:20px;bottom:20px;max-width:calc(100% - 40px);background:#fff;border-radius:12px;padding:10px 20px;font-size:26px;font-weight:700;line-height:1.2">{nom}</span></div>'.format(
            fond=c["couleur"], ic=ch.icone_data_uri(c["icone"]), coul="#fff" if blanc else "#1F1F24", nom=esc(c["nom"]))
    tuiles += '<div style="border-radius:22px;background:#1F1F24;color:#fff;padding:32px;display:flex;flex-direction:column;justify-content:flex-end;gap:10px"><span style="font-size:30px;font-weight:700;line-height:1.2">Tout le catalogue</span><a href="{url}" style="font-size:24px;font-weight:700;color:#fff">{site}</a></div>'.format(
        url=ch.CONTACT["url"], site=ch.CONTACT["site"])
    texte = s.get("texte") or "**L'IA au quotidien** : ChatGPT, Claude, Copilot, Mistral, Gemini. Et aussi Make, Canva, Figma, Power BI, Microsoft 365."
    return """<div style="position:absolute;top:0;left:0;right:0;bottom:80px;padding:88px 120px 64px;display:flex;flex-direction:column;gap:48px">
<div><h2 style="{h2}">Nos autres formations</h2><p style="margin:10px 0 0;font-size:34px;color:#3B3B42">Le catalogue complet&nbsp;: <a href="{url}" style="color:var(--ci);font-weight:700">{site}</a></p></div>
<div style="flex:1;display:grid;grid-template-columns:repeat(5,1fr);grid-template-rows:1fr 1fr;gap:24px">{tuiles}</div>
<p style="margin:0;font-size:28px;line-height:1.4;color:#45454F">{texte}</p>
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
FOND = {"citation": "background:var(--c);color:var(--co)", "notion-cle": "background:var(--ct)", "image": "background:#DADADF"}

CSS = """
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#111;font-family:Raleway,system-ui,sans-serif;color:#1F1F24;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.scene{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;overflow:hidden}
.deck{position:relative;width:1920px;height:1080px;flex-shrink:0;transform-origin:center center;counter-reset:sf}
.slide{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;background:#fff;counter-increment:sf;visibility:hidden}
.slide.active{visibility:visible}
.pn::after{content:counter(sf,decimal-leading-zero)}
.pied{position:absolute;left:0;right:0;bottom:0;height:80px;background:#F4F4F5;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:0 64px;font-size:24px;font-weight:600;color:#55555E}
.pied img{height:64px;width:auto}
.pied .pn{justify-self:end;font-weight:700;color:#1F1F24}
.pied-c{background:var(--c);color:var(--co);font-weight:700}
.pied-c .pn{color:inherit}
.liste{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}
.pl{background:#fff;color:var(--ci);font-size:24px;font-weight:700;padding:12px 30px;border-radius:999px}
.rond{border-radius:50%;background:var(--c);color:var(--co);display:flex;align-items:center;justify-content:center;font-weight:800;flex-shrink:0}
.ic{display:inline-block;background:#1F1F24;-webkit-mask:var(--i) center/contain no-repeat;mask:var(--i) center/contain no-repeat}
.stk{background:#fff;box-shadow:0 8px 20px rgba(0,0,0,.18)}
.stk>div{width:100%;height:100%;background:var(--sk);display:flex;align-items:center;justify-content:center}
.vide{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;background:#F6F6F7;border:3px dashed #D9D9DE;color:#9A9AA6;font-size:24px;font-weight:600;text-align:center;padding:16px}
.vide .ic{width:56px;height:56px;background:#B5B5BD}
strong{font-weight:700}
a{color:var(--ci)}
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
        c=c["couleur"], i=c["encre"], t=c["teinte"], o=c["surCouleur"], sk=c["sticker"], si=ch.icone_data_uri(c["icone"]),
        logo=ch.logo_svg_data_uri(ch.variante_logo(c)), lf="none" if c["surCouleur"].upper() == "#FFFFFF" else "brightness(0)",
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
            '<section class="slide" data-type="{}" aria-label="{}" style="{}">{}{}</section>'.format(
                t, esc(etiquette), FOND.get(t, ""), corps, modele
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
""".format(titre=esc(f["intitule"]), variables=variables, css=CSS, sections="\n".join(sections), js=JS)
