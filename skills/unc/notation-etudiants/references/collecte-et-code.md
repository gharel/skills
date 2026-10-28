# Collecte des rendus et analyse du code

## 1. Collecter les rendus dans la messagerie

Avec un accès à la messagerie de l'utilisateur, cherche large, puis recoupe. Requêtes types (syntaxe Gmail) :

- `(TP6 OR CC4 OR "TP 6" OR "CC 4" OR <mots-clés du projet>) newer_than:120d`
- `(github.com OR onrender.com OR vercel.app OR <identifiant du TP>) newer_than:60d -from:me`
- `from:<domaine des étudiants> after:<date de l'énoncé>`

Ensuite :

- **Libellé commun.** Repère le libellé qui regroupe les rendus : il aide à ne rien oublier.
- **Autres TP.** Écarte les rendus d'autres TP (TP4, TP5…) reçus pendant la même période. Note quand même leurs liens GitHub : ils servent de référence pour l'estimation de l'usage de l'IA.
- **Lecture complète.** Ouvre chaque mail en entier, en texte brut. Les extraits sont tronqués et cachent souvent le lien de déploiement.
- **Fiche par étudiant** :
  - nom et objet exact ;
  - date, en convertissant l'UTC en heure locale (Nouméa = UTC+11) ;
  - lien GitHub et lien de déploiement ;
  - remarques : usage déclaré de l'IA et sur quoi, excuses de retard.
- **Mails de l'enseignant.** Cherche aussi ses mails envoyés : délais accordés, échanges. Signale les étudiants attendus sans rendu.
- **Doublons.** Les mails transférés (« TR : ») depuis une autre adresse de l'enseignant sont des doublons : garde l'original.

Sans accès à la messagerie, demande les mails collés, ou un tableau avec ces mêmes colonnes.

## 2. Récupérer le code

Clone chaque dépôt **avec son historique** (`.git`) : il sert à noter les commits et les tags, et à estimer l'usage de l'IA.

```bash
git clone https://github.com/<utilisateur>/<depot>.git <utilisateur>_<depot>
```

**Échec du clonage.** `fatal: could not read Username` signale un dépôt privé ou inexistant. Pour vérifier :

- ouvre `https://github.com/<utilisateur>/<depot>` (404) ;
- liste ses dépôts publics : `https://github.com/<utilisateur>?tab=repositories`.

L'étudiant est alors « non évaluable » : demande l'accès.

### Vue d'ensemble de chaque dépôt

```bash
python scripts/indices_depot.py depots/* --comparer          # résumé lisible
python scripts/indices_depot.py depots/* --comparer --json   # pour un traitement automatique
```

Le résumé donne, par dépôt :

- les tags, et s'ils pointent tous sur le même commit ;
- le nombre de commits et les auteurs ;
- chaque commit avec sa date et le nombre de lignes ajoutées, hors fichiers générés ;
- le plus gros commit et sa part du total ;
- les messages de commit en anglais ;
- les `console.log` et `console.debug` ;
- l'indentation, et si elle est mêlée ;
- les fichiers versionnés par erreur (`.env`, `desktop.ini`, `__pycache__`, `node_modules`) ;
- la densité de commentaires et de JSDoc ;
- les émojis et symboles décoratifs ;
- le README.

### Détection de copie entre étudiants

L'option `--comparer` mesure, pour chaque paire de dépôts :

- la similarité des fichiers homonymes ;
- le nombre de fichiers identiques ;
- les adresses d'auteur communes.

Ce sont des indices à signaler, jamais une preuve à sanctionner. Le code de départ fourni par l'enseignant rend les dépôts semblables : compare avec lui avant de conclure.

Autres indices à relever :

- un diff vide entre deux dépôts ;
- un commit unique ;
- le nom ou l'adresse d'un autre étudiant comme auteur.

### Relire le code

Lis le code utile de chaque dépôt : serveur, configuration, base, routeurs, client, schéma SQL, README. Relève :

- **entrées** : validation, gestion des collisions ;
- **erreurs** : `async`/`await`, codes HTTP ;
- **secrets** : exposés, ou jamais renvoyés au créateur ;
- **adresses** : URL codées en dur (`localhost`) ;
- **dépôt** : fichiers versionnés par erreur (`.env`, `desktop.ini`, `__pycache__`) ;
- **forme** : indentation (mélange de 2 et 4 espaces) ;
- **documentation** : présence de Swagger et des routes demandées.

## 3. Tester en local les projets sans déploiement

```bash
cd <depot>
npm install --no-audit --no-fund --loglevel=error   # ajouter --legacy-peer-deps en cas d'ERESOLVE
PORT=9101 NODE_ENV=production node server.mjs        # sous Windows PowerShell : $env:PORT=9101; node server.mjs
```

Dans un bac à sable Linux sans accès à nodejs.org, `export npm_config_nodedir=/usr` évite le téléchargement des en-têtes de Node.

Teste ensuite au `curl` :

- réponse JSON ;
- POST valide et POST invalide ;
- redirection : `-w '%{http_code} -> %{redirect_url}'` ;
- DELETE sans clé, puis avec une mauvaise clé ;
- `Accept: image/png` pour le 406 ;
- `/api-docs/`.

Masque les secrets dans la sortie (`sed 's/"secret":"[^"]*"/"secret":"***"/'`). Arrête les serveurs à la fin. Précise « testé en local seulement » dans la justification.

Pour un projet libre, regarde aussi les captures d'écran du dépôt.

## Annexe : commandes shell d'origine (Linux, macOS)

Équivalents bash de `indices_depot.py`, si Python n'est pas disponible :

```bash
for d in */; do echo "=== $d"; cd "$d"
  echo "tags: $(git tag | tr '\n' ' ')"
  git show-ref --tags -d
  echo "commits: $(git rev-list --all --count)  auteurs: $(git log --format='%an <%ae>' | sort | uniq -c | tr '\n' ';')"
  git log --format='%ad %s' --date=short | head -15
  echo "console.log/debug: $(grep -rn 'console\.\(log\|debug\)' --include=*.mjs --include=*.js --include=*.ejs --include=*.html --exclude-dir=node_modules . | wc -l)"
  cd ..; done
# Taille de chaque commit, hors fichiers générés
git log --numstat --format='--- %h %ad %s' --date=iso -- . ':!package-lock.json' ':!*.lock' \
 | awk '/^---/{if(h)print h" | +"n; h=$0; n=0; next} $1~/^[0-9]+$/{n+=$1} END{print h" | +"n}'
# Émojis et symboles décoratifs
grep -rnP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]|→' --exclude-dir=node_modules --exclude-dir=.git . | head -20
# Copie : comparer deux dépôts à structure voisine
diff -rq --exclude=.git A B
```
