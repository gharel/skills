---
name: notation-etudiants
description: "Corrige et note les rendus d'étudiants (projets web sur GitHub avec un déploiement Render, Vercel ou autre) à partir d'un énoncé, des mails reçus et d'un barème : une note justifiée par critère, un onglet par étudiant dans Google Sheets ou dans un classeur .xlsx, et une estimation indicative de l'usage de l'IA (probabilité et part du travail). À utiliser quand l'utilisateur demande de corriger, noter ou évaluer un TP, un CC ou un projet rendu par mail avec des liens GitHub ou de déploiement, ou de remplir une grille de notation."
license: Propriétaire.
metadata:
  version: '1.0.1'
  categorie: unc
  auteur: Guillaume Harel
  source: https://github.com/gharel/skills
  ordre: '1'
  charte: skazy-formation-donnees
---

# Notation de rendus étudiants

Corriger un TP ou un contrôle continu rendu par mail (lien GitHub, lien de déploiement) :

- noter chaque étudiant selon le barème, critère par critère ;
- justifier chaque note par un fait observé ;
- estimer l'usage de l'IA, à titre indicatif ;
- remettre à l'enseignant un tableur avec un onglet par étudiant et un compte rendu court.

## Principes

- **Zéro invention.** Chaque note s'appuie sur un fait observé : code, test, commit, mail. Ce qui n'a pas pu être vérifié est écrit comme tel (« non testé »).
- **Même règle pour tous.** Écris la règle de chaque ligne du barème avant de noter, puis applique-la à l'identique à chaque étudiant.
- **L'enseignant tranche.** Ne décide jamais seul d'une sanction : plagiat, usage de l'IA, retard ou pénalité douteuse. Note sur le plan technique et signale le reste.
- **Typographie française.** Pas de tiret cadratin ni d'émoji. Espaces insécables avant `: ; ? !` et à l'intérieur des guillemets « ». Le script de rendu les ajoute.

## Déroulé

### 0. Réunir les entrées

1. **L'énoncé** (URL ou fichier) : lis-le en entier. Relève les livrables attendus : tags git, routes, README, déploiement, schémas JSON, critères d'évaluation.
2. **Le barème**, sous la forme d'un tableur Google Sheets, d'un fichier ou d'un texte : relève ses lignes, leurs maxima, les pénalités et la formule du total.
3. **Les consignes particulières** : projet libre autorisé pour certains, délais accordés, politique sur l'IA.

S'il manque l'énoncé ou le barème, demande-le. Sinon, commence directement.

### 1. Collecter les rendus

- **Si tu as accès à la messagerie de l'utilisateur** : cherche large, puis recoupe. Les requêtes, le libellé commun, la lecture complète de chaque mail et les doublons transférés sont décrits dans [references/collecte-et-code.md](references/collecte-et-code.md).
- **Sinon** : demande à l'utilisateur de coller les mails, ou un tableau « nom, prénom, objet, date, lien GitHub, lien de déploiement, remarques ».

Pour chaque étudiant, note :

- nom et objet exact du mail ;
- date, convertie en heure locale (Nouméa = UTC+11) ;
- liens GitHub et de déploiement ;
- remarques : usage déclaré de l'IA et sur quoi, excuses de retard.

Repère aussi :

- les étudiants attendus sans rendu ;
- les délais accordés par l'enseignant ;
- les liens des TP précédents : ils servent de référence pour l'usage de l'IA (étape 4).

### 2. Récupérer et analyser le code

- **Si tu peux lancer des commandes** (git et Python) :
  - clone chaque dépôt avec son historique ;
  - lance `python scripts/indices_depot.py depot1 depot2 … --comparer`.

  Le script relève les tags (et s'ils pointent tous sur le même commit), les commits et leur taille, les auteurs, les `console.log`, l'indentation, les fichiers versionnés par erreur, les commentaires, les émojis et le README. Il compare aussi les dépôts deux à deux, comme indice de copie.

- **Sinon** : lis les dépôts sur GitHub (fichiers, historique des commits, tags) ou demande une archive zip. Relève les mêmes points à la main.

Un dépôt inaccessible (404, dépôt privé) rend l'étudiant **non évaluable** : demande l'accès, ne note pas.

Lis ensuite le code utile : serveur, configuration, base, routeurs, client, schéma SQL, README. La liste de ce qu'il faut relever est dans [references/collecte-et-code.md](references/collecte-et-code.md).

Une copie entre étudiants se signale, elle ne se sanctionne pas : diff vide, commit unique, auteur ou adresse mail d'un autre étudiant.

### 3. Tester les déploiements

- **Si tu peux piloter un navigateur** : ouvre d'abord tous les sites pour réveiller les hébergements gratuits. Teste ensuite l'API depuis la page elle-même, puis l'interface comme un utilisateur.
- **Sinon, si tu peux lancer des commandes** : teste au `curl`. Un projet sans déploiement se teste en local.
- **Sinon** : écris « non testé » et donne à l'enseignant la liste des vérifications à faire.

Vérifie que le site déployé est bien celui de l'étudiant (nom en pied de page, titre). N'affiche jamais un secret ni un jeton dans une sortie. Les scripts de test et les pièges courants sont dans [references/tests-deploiement.md](references/tests-deploiement.md).

### 4. Estimer l'usage de l'IA (indicatif, hors note)

Pour chaque étudiant évalué, donne deux fourchettes argumentées :

- **probabilité d'usage de l'IA**, par exemple « 50 à 80 % » ;
- **part estimée du travail** produite ou fortement assistée par une IA, et sur quelles parties.

Règles impératives :

- aucun outil ne prouve l'usage d'une IA : ce sont des estimations, jamais une preuve, et elles ne modifient pas la note ;
- toujours une fourchette, jamais 100 % (sauf usage déclaré couvrant tout le rendu) ;
- pas de « détecteur d'IA » en ligne : peu fiable, et le travail des étudiants n'a pas à partir chez un tiers ;
- un usage déclaré est un fait : indique son périmètre exact, et applique à cet étudiant la même grille d'indices qu'aux autres, sans le pénaliser ;
- probabilité élevée : propose un échange oral avec l'étudiant, seule vérification fiable.

Le tableau des indices et leur force, les indices contraires, la comparaison avec les rendus précédents et le calcul des fourchettes sont dans [references/usage-ia.md](references/usage-ia.md).

### 5. Fixer les règles du barème

Avant de noter, écris la règle de chaque ligne : ce qui vaut tous les points, la moitié, zéro. Une grille type, le traitement des pénalités, des projets libres et des lignes ambiguës sont dans [references/bareme.md](references/bareme.md).

### 6. Remplir le tableur

- **Si tu as accès au Google Sheets du barème** : duplique l'onglet modèle pour chaque étudiant, puis remplis notes, justifications, commentaire et bloc IA. La procédure est dans [references/google-sheets.md](references/google-sheets.md).
- **Sinon** : rédige `notation.json` au format de [references/format-notation.md](references/format-notation.md). Un exemple complet se trouve dans `exemples/notation-exemple.json`. Ensuite :
  - **si tu peux exécuter du Python** : lance la commande ci-dessous, qui crée `notation-<contrôle>.xlsx`. Corrige chaque `ERREUR` et prends en compte les `ATTENTION`. La dépendance est `openpyxl`.

    ```bash
    python scripts/rendre_notation.py notation.json --sortie <dossier>
    ```

  - **sinon** : donne le JSON complet dans un bloc de code. Invite l'utilisateur à le coller dans l'atelier https://gharel.github.io/skills/atelier/, qui produit le classeur.

Le classeur contient :

- **un onglet Synthèse** : notes de la meilleure à la plus basse, estimations d'IA, points à trancher ;
- **un onglet Barème** : les règles appliquées ;
- **un onglet par étudiant** : critère, note, maximum, justification et total, plus un bloc IA sur fond gris, hors du total.

Il s'importe dans Google Sheets par Fichier > Importer.

### 7. Rendre compte à l'enseignant

Un compte rendu court, en français :

- le lien du tableur, ou le fichier produit, et ce qui a été fait ;
- le tableau des notes, de la meilleure à la plus basse, avec deux colonnes « IA (probabilité) » et « IA (part estimée) » ;
- un rappel en une phrase : ces estimations sont indicatives, fondées sur des indices, sans valeur de preuve, à vérifier par un échange avec l'étudiant si besoin ;
- les points à trancher :
  - suspicion de copie (faits observés) ;
  - probabilité d'usage de l'IA élevée (indices principaux, échange oral proposé) ;
  - pénalités lourdes discutables ;
  - étudiants non évaluables, rendus hors délai, étudiants sans rendu ;
  - interprétations du barème retenues ;
- les défauts récurrents de la promotion ;
- une section « Sources » avec le lien de chaque mail utilisé et de l'énoncé.

## Fichiers du skill

- `scripts/indices_depot.py` : indices relevés dans les dépôts git (livraison, code, IA, copie), sous Windows, macOS et Linux.
- `scripts/rendre_notation.py` : contrôle de `notation.json` et rendu du classeur `.xlsx`. Il s'appuie sur `charte.py`.
- `references/collecte-et-code.md` : recherche des mails, clonage, relecture du code, tests en local.
- `references/tests-deploiement.md` : tests en ligne de l'API et de l'interface.
- `references/usage-ia.md` : indices, fourchettes et règles de l'estimation de l'usage de l'IA.
- `references/bareme.md` : règles de notation, grille type, projets libres.
- `references/google-sheets.md` : remplissage direct du tableur Google Sheets de l'enseignant.
- `references/format-notation.md` : format du JSON lu par le script et par l'atelier.
- `exemples/notation-exemple.json` : notation complète (CC de réducteur d'URL, quatre étudiants fictifs).

Version 1.0.1. Sources et mises à jour : https://gharel.github.io/skills/
