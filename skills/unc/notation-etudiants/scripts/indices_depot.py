#!/usr/bin/env python3
"""Indices relevés dans des dépôts git d'étudiants : livraison, qualité du code, usage possible de l'IA, copie.

Usage :
    python scripts/indices_depot.py DEPOT [DEPOT…] [--comparer] [--json]

DEPOT est un dossier cloné avec son historique (.git). Le script ne lance que des commandes git en lecture
et la bibliothèque standard de Python : il fonctionne sous Windows, macOS et Linux.

Les mesures sont des indices à lire avec references/usage-ia.md, jamais des preuves : aucun outil ne prouve
l'usage d'une IA ni une copie.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import itertools
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath

CODE = {".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx", ".py", ".php", ".java", ".cs", ".go", ".rb", ".vue", ".svelte"}
GABARITS = {".ejs", ".html", ".htm", ".hbs", ".pug", ".twig"}
TEXTE = CODE | GABARITS | {".css", ".scss", ".md", ".txt", ".json", ".yml", ".yaml", ".sql", ".sh", ".env"}
GENERES = re.compile(r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|[^/]+\.lock|[^/]+\.min\.(js|css))$")
A_NE_PAS_VERSIONNER = re.compile(
    r"(^|/)(\.env(\.(?!example|sample|dist)[^/]+)?|desktop\.ini|Thumbs\.db|\.DS_Store|[^/]+\.pyc)$|(^|/)(__pycache__|node_modules|\.idea)/"
)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐→]")
COMMENTAIRE = re.compile(r"^\s*(//|#|\*|/\*)")
CONSOLE = re.compile(r"console\.(log|debug)\s*\(")
# Message qui commence, après un éventuel préfixe « feat(x): », par un verbe anglais.
PREFIXE_COMMIT = re.compile(r"^\w+(\([^)]*\))?!?:\s*")
ANGLAIS = re.compile(
    r"^(add|added|adds|update|updated|fix|fixed|refactor|refine|implement|implemented|create|created|remove|removed|"
    r"improve|initial commit|clean|enhance|rename|move|merge|set ?up)\b",
    re.IGNORECASE,
)
SEUIL_MASSIF = 300  # lignes ajoutées en un commit


def git(depot: Path, *args: str) -> str:
    try:
        resultat = subprocess.run(["git", "-C", str(depot), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise SystemExit("git est introuvable : installez-le (https://git-scm.com) ou relevez les indices à la main.")
    if resultat.returncode != 0:
        raise RuntimeError(resultat.stderr.strip() or "git {} a échoué".format(" ".join(args)))
    return resultat.stdout


def lire(chemin: Path) -> str | None:
    try:
        if chemin.stat().st_size > 500_000:
            return None
        return chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def style_indentation(lignes: list[str]) -> str | None:
    """« tabulations », « 2 espaces », « 4 espaces » ou « mélange » (tabulations et espaces) ; None sans indentation."""
    tabs = espaces = 0
    largeurs = []
    for ligne in lignes:
        if not ligne.strip():
            continue
        if ligne.startswith("\t"):
            tabs += 1
        elif ligne.startswith(" "):
            espaces += 1
            largeurs.append(len(ligne) - len(ligne.lstrip(" ")))
    if tabs and espaces > 3:
        return "mélange"
    if tabs:
        return "tabulations"
    largeurs = [x for x in largeurs if x > 1]
    if not largeurs:
        return None
    return "2 espaces" if sum(1 for x in largeurs if x % 4 == 2) > len(largeurs) * 0.1 else "4 espaces"


def melange(styles: dict[str, str]) -> bool:
    """Indentation mêlée dans un fichier, ou différente d'un fichier à l'autre pour une même extension."""
    par_extension: dict[str, set[str]] = {}
    for nom, style in styles.items():
        par_extension.setdefault(PurePosixPath(nom).suffix.lower(), set()).add(style)
    return "mélange" in styles.values() or any(len(s) > 1 for s in par_extension.values())


def analyser_depot(chemin: str | Path) -> dict:
    """Mesures d'un dépôt cloné : livraison (tags, commits), code (logs, indentation, fichiers) et indices d'IA."""
    depot = Path(chemin).resolve()
    git(depot, "rev-parse", "--git-dir")
    fichiers = [f for f in git(depot, "ls-files").splitlines() if f]

    # Tags : tous sur le même commit trahissent souvent des tags posés à la fin.
    tags = {}
    for ligne in git(depot, "show-ref", "--tags", "-d").splitlines() if git(depot, "tag") else []:
        sha, ref = ligne.split(" ", 1)
        nom = ref.replace("refs/tags/", "").replace("^{}", "")
        tags[nom] = sha  # la forme déréférencée (^{}) vient après et l'emporte
    tags_meme_commit = len(tags) > 1 and len(set(tags.values())) == 1

    # Commits : taille (lignes ajoutées hors fichiers générés), rythme, auteurs, langue des messages.
    commits = []
    for bloc in git(depot, "log", "--all", "--numstat", "--date=iso-strict", "--format=%x1e%h%x1f%aI%x1f%an%x1f%ae%x1f%s").split("\x1e"):
        if not bloc.strip():
            continue
        entete, *stats = bloc.strip("\n").split("\n")
        h, date, auteur, email, message = entete.split("\x1f")
        ajoutees = 0
        for s in stats:
            morceaux = s.split("\t")
            if len(morceaux) == 3 and morceaux[0].isdigit() and not GENERES.search(morceaux[2]):
                ajoutees += int(morceaux[0])
        commits.append({"commit": h, "date": date, "auteur": auteur, "email": email, "message": message, "ajoutees": ajoutees})
    commits.sort(key=lambda c: c["date"])
    total = sum(c["ajoutees"] for c in commits) or 0
    plus_gros = max(commits, key=lambda c: c["ajoutees"]) if commits else None
    duree_h = 0.0
    if len(commits) > 1:
        duree_h = (datetime.fromisoformat(commits[-1]["date"]) - datetime.fromisoformat(commits[0]["date"])).total_seconds() / 3600

    # Parcours des fichiers suivis.
    emojis, console, code, styles = [], [], [], {}
    for nom in fichiers:
        p = PurePosixPath(nom)
        if GENERES.search(nom) or "node_modules/" in nom or p.suffix.lower() not in TEXTE:
            continue
        contenu = lire(depot / nom)
        if contenu is None:
            continue
        lignes = contenu.splitlines()
        for k, ligne in enumerate(lignes, 1):
            if EMOJI.search(ligne):
                emojis.append({"fichier": nom, "ligne": k, "extrait": ligne.strip()[:80]})
        if p.suffix.lower() in CODE | GABARITS:
            n = len(CONSOLE.findall(contenu))
            if n:
                console.append({"fichier": nom, "nombre": n})
            style = style_indentation(lignes)
            if style:
                styles[nom] = style
        if p.suffix.lower() in CODE:
            code.append({
                "fichier": nom,
                "lignes": len(lignes),
                "commentaires": sum(1 for x in lignes if COMMENTAIRE.match(x)),
                "jsdoc": contenu.count("/**"),
            })

    readme = next((f for f in fichiers if re.fullmatch(r"readme(\.[a-z]+)?", f, re.IGNORECASE)), None)
    infos_readme = None
    if readme:
        texte = lire(depot / readme) or ""
        infos_readme = {
            "fichier": readme,
            "lignes": len(texte.splitlines()),
            "titres": len(re.findall(r"^#{1,6} ", texte, re.MULTILINE)),
            "cases": len(re.findall(r"^\s*[-*] \[[ xX]\]", texte, re.MULTILINE)),
            "emojis": len(EMOJI.findall(texte)),
        }

    lignes_code = sum(c["lignes"] for c in code)
    return {
        "depot": str(depot),
        "fichiers": len(fichiers),
        "tags": sorted(tags),
        "tags_meme_commit": tags_meme_commit,
        "commits": commits,
        "nb_commits": len(commits),
        "auteurs": dict(Counter("{} <{}>".format(c["auteur"], c["email"]) for c in commits)),
        "lignes_ajoutees": total,
        "plus_gros_commit": plus_gros,
        "part_plus_gros": round(plus_gros["ajoutees"] / total, 2) if plus_gros and total else 0,
        "commits_massifs": [c for c in commits if c["ajoutees"] >= SEUIL_MASSIF],
        "duree_heures": round(duree_h, 1),
        "messages_anglais": [c["message"] for c in commits if ANGLAIS.match(PREFIXE_COMMIT.sub("", c["message"]))],
        "emojis": emojis,
        "emojis_commits": [c["message"] for c in commits if EMOJI.search(c["message"])],
        "console": console,
        "a_ne_pas_versionner": [f for f in fichiers if A_NE_PAS_VERSIONNER.search(f)],
        "indentation": styles,
        "melange_indentation": melange(styles),
        "code": code,
        "densite_commentaires": round(sum(c["commentaires"] for c in code) / lignes_code, 2) if lignes_code else 0,
        "jsdoc": sum(c["jsdoc"] for c in code),
        "readme": infos_readme,
    }


def empreintes(depot: Path) -> dict[str, str]:
    """Contenu normalisé (fins de ligne, espaces de fin) des fichiers de code et de texte suivis."""
    resultat = {}
    for nom in git(depot, "ls-files").splitlines():
        if GENERES.search(nom) or PurePosixPath(nom).suffix.lower() not in TEXTE - {".md", ".txt"}:
            continue
        contenu = lire(depot / nom)
        if contenu is not None:
            resultat[nom] = "\n".join(x.rstrip() for x in contenu.splitlines()).strip()
    return resultat


def comparer_depots(chemins: list[str | Path]) -> list[dict]:
    """Pour chaque paire de dépôts : fichiers identiques, similarité des fichiers homonymes, auteurs communs."""
    donnees = []
    for chemin in chemins:
        depot = Path(chemin).resolve()
        contenus = empreintes(depot)
        auteurs = {x.lower() for x in git(depot, "log", "--all", "--format=%ae").split()}
        donnees.append((depot, contenus, auteurs))
    paires = []
    for (a, ca, aa), (b, cb, ab) in itertools.combinations(donnees, 2):
        ha = {hashlib.sha1(v.encode()).hexdigest() for v in ca.values() if v}
        hb = {hashlib.sha1(v.encode()).hexdigest() for v in cb.values() if v}
        communs = sorted(set(ca) & set(cb))
        ratios = []
        for nom in communs:
            poids = max(1, len(ca[nom].splitlines()))
            ratios.append((difflib.SequenceMatcher(None, ca[nom], cb[nom], autojunk=False).ratio(), poids))
        similarite = sum(r * p for r, p in ratios) / sum(p for _, p in ratios) if ratios else 0
        paires.append({
            "a": a.name,
            "b": b.name,
            "fichiers_identiques": len(ha & hb),
            "fichiers_comparables": min(len(ha), len(hb)),
            "homonymes": len(communs),
            "similarite": round(similarite, 2),
            "auteurs_communs": sorted(aa & ab),
        })
    return sorted(paires, key=lambda p: -p["similarite"])


# ---------------------------------------------------------------- affichage


def resume(x: dict) -> str:
    sortie = ["=== {}".format(x["depot"])]
    sortie.append("Tags : {}{}".format(", ".join(x["tags"]) or "aucun", " (tous sur le même commit)" if x["tags_meme_commit"] else ""))
    sortie.append("Commits : {} sur {} h · auteurs : {}".format(x["nb_commits"], x["duree_heures"], "; ".join("{} ({})".format(k, v) for k, v in x["auteurs"].items()) or "aucun"))
    if x["plus_gros_commit"]:
        p = x["plus_gros_commit"]
        sortie.append("Lignes ajoutées : {} · plus gros commit : {} lignes ({:.0%}), {} « {} »".format(
            x["lignes_ajoutees"], p["ajoutees"], x["part_plus_gros"], p["commit"], p["message"]))
    for c in x["commits"][:30]:
        sortie.append("  {} {} +{} {}".format(c["date"][:16].replace("T", " "), c["commit"], c["ajoutees"], c["message"]))
    if len(x["commits"]) > 30:
        sortie.append("  … {} commits de plus".format(len(x["commits"]) - 30))
    if x["commits_massifs"]:
        sortie.append("Commits de plus de {} lignes : {}".format(SEUIL_MASSIF, len(x["commits_massifs"])))
    if x["messages_anglais"]:
        sortie.append("Messages de commit en anglais conventionnel : {} sur {}".format(len(x["messages_anglais"]), x["nb_commits"]))
    sortie.append("console.log / debug : {}".format(", ".join("{} ({})".format(c["fichier"], c["nombre"]) for c in x["console"]) or "aucun"))
    sortie.append("Indentation : {}{}".format(", ".join(sorted(set(x["indentation"].values()))) or "—", " (mélange)" if x["melange_indentation"] else ""))
    sortie.append("Fichiers à ne pas versionner : {}".format(", ".join(x["a_ne_pas_versionner"]) or "aucun"))
    sortie.append("Commentaires : {:.0%} des lignes de code, {} blocs JSDoc".format(x["densite_commentaires"], x["jsdoc"]))
    for c in x["code"]:
        sortie.append("  {} : {} lignes, {} de commentaire, {} JSDoc".format(c["fichier"], c["lignes"], c["commentaires"], c["jsdoc"]))
    sortie.append("Émojis et symboles décoratifs : {} dans le code, {} dans les commits".format(len(x["emojis"]), len(x["emojis_commits"])))
    for e in x["emojis"][:10]:
        sortie.append("  {}:{} {}".format(e["fichier"], e["ligne"], e["extrait"]))
    r = x["readme"]
    sortie.append("README : " + ("{} ({} lignes, {} titres, {} cases à cocher, {} émojis)".format(r["fichier"], r["lignes"], r["titres"], r["cases"], r["emojis"]) if r else "absent"))
    return "\n".join(sortie)


def main() -> None:
    parser = argparse.ArgumentParser(description="Indices relevés dans des dépôts git d'étudiants (livraison, code, IA, copie).")
    parser.add_argument("depots", nargs="+", help="dossiers clonés avec leur historique")
    parser.add_argument("--comparer", action="store_true", help="compare les dépôts deux à deux (indices de copie)")
    parser.add_argument("--json", action="store_true", help="sortie JSON")
    args = parser.parse_args()
    analyses, erreurs = [], []
    for d in args.depots:
        try:
            analyses.append(analyser_depot(d))
        except RuntimeError as e:
            erreurs.append("{} : {}".format(d, e))
    paires = comparer_depots([a["depot"] for a in analyses]) if args.comparer and len(analyses) > 1 else []
    if args.json:
        print(json.dumps({"depots": analyses, "comparaisons": paires, "erreurs": erreurs}, ensure_ascii=False, indent=2))
    else:
        for a in analyses:
            print(resume(a) + "\n")
        if paires:
            print("=== Comparaisons (indices de copie, jamais une preuve)")
            for p in paires:
                print("{} / {} : similarité {:.0%} sur {} fichiers homonymes, {} fichiers identiques{}".format(
                    p["a"], p["b"], p["similarite"], p["homonymes"], p["fichiers_identiques"],
                    ", auteurs communs : " + ", ".join(p["auteurs_communs"]) if p["auteurs_communs"] else ""))
        for e in erreurs:
            print("ERREUR : " + e, file=sys.stderr)
    raise SystemExit(1 if erreurs and not analyses else 0)


if __name__ == "__main__":
    main()
