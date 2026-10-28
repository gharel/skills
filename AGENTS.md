# AGENTS.md : Skills IA de Guillaume Harel

Consignes pour les agents de code (Claude Code, Codex, Copilot, Cursor…) et pour les humains qui travaillent sur ce dépôt.

## Le projet

Ce dépôt réunit des **skills IA génériques** au format ouvert [Agent Skills](https://agentskills.io) : un dossier avec un `SKILL.md`, des références, des modèles et des scripts. Ils fonctionnent dans ChatGPT, Claude, Codex, Gemini CLI, Cursor, Copilot et dans les assistants sans exécution de code (grâce à l'atelier).

Le site https://gharel.github.io/skills/ présente le catalogue. On y trouve aussi les téléchargements, les instructions d'installation et l'**atelier**, qui exécute les scripts Python des skills dans le navigateur avec Pyodide.

Trois catégories, une par dossier :

| Dossier         | Catégorie                                 | Plugin Claude Code |
| --------------- | ----------------------------------------- | ------------------ |
| `skills/pro/`   | Pro · Skazy Formation                     | `skazy-formation`  |
| `skills/unc/`   | UNC · Université de la Nouvelle-Calédonie | `unc`              |
| `skills/perso/` | Perso                                     | `perso`            |

Les trois skills Pro forment une chaîne. Chaque skill accepte le JSON produit par le précédent.

| Étape | Skill                     | Produit                                                                   |
| ----- | ------------------------- | ------------------------------------------------------------------------- |
| 1     | `skazy-plan-formation`    | `plan.json`, puis HTML A4 et DOCX                                         |
| 2     | `skazy-support-formation` | `support.json`, puis HTML 1920 × 1080 et PPTX                             |
| 3     | `skazy-quiz`              | JSON Skazy Quiz, puis lien, Kahoot `.xlsx`, Google Forms `.gs` et corrigé |

## Arborescence

```
skills/<catégorie>/<nom>/        Un skill : SKILL.md, agents/openai.yaml, references/, scripts/, assets/, exemples/
commun/charte/                   Copie de la charte de design-skazy (charte.json, plan-formation.css/.js, logos) + charte.py et icônes Lucide
modele/                          Modèle à copier pour créer un skill
site/                            Sources du site : index.html (gabarit), atelier/, assets/, installer.ps1, installer.sh
outils/                          Scripts Node : construire, synchroniser la charte, icônes, captures, serveur local
tests/                           Vitest (outils), pytest (tests/py : rendus), Playwright (tests/e2e : site et atelier)
.claude-plugin/marketplace.json  Généré par npm run construire : un plugin Claude Code par catégorie
_site/                           Site construit (non versionné), publié par GitHub Actions
```

## Commandes

| Commande               | Rôle                                                                                                                                                          |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm run construire`   | Contrôle les skills et construit `_site/` (catalogue, zip, versions un fichier, sources de l'atelier). Régénère `.claude-plugin/marketplace.json`.            |
| `npm run dev`          | Sert `_site/` sur http://localhost:4182 (après `construire`)                                                                                                  |
| `npm run check`        | Prettier, ESLint, charte synchronisée, skills conformes, versions montées, marketplace à jour (**avant chaque commit**)                                       |
| `npm test`             | Vitest : lecture et contrôle des skills                                                                                                                       |
| `npm run test:py`      | pytest : rendus du plan, du support et du quiz (`pip install python-docx python-pptx openpyxl pillow pytest`)                                                 |
| `npm run test:e2e`     | Playwright : catalogue, accessibilité, mobile, atelier de bout en bout (**avant chaque push**, après `construire`)                                            |
| `npm run synchroniser` | Recopie la charte de design-skazy dans `commun/charte`, puis `commun/charte` dans les skills qui la déclarent                                                 |
| `npm run modeles`      | Compare au pixel les rendus HTML des skills plan et support à leurs modèles de design-skazy, puis verrouille leur empreinte (`commun/charte/alignement.json`) |
| `npm run icones`       | Régénère les icônes Lucide de la charte en PNG et SVG (rare)                                                                                                  |

Contrôle visuel des rendus :

- `node outils/capturer.mjs fichier.html sortie.png` : capture d'un plan ou d'une page ;
- `node outils/planche.mjs support.html planche.png 1 12` : planche de slides ;
- `pwsh outils/office-pdf.ps1 fichier.docx sortie.pdf` : DOCX ou PPTX vu par Word ou PowerPoint, sous Windows.

## Ajouter un skill

1. Copier `modele/` dans `skills/<catégorie>/<nom-du-skill>/`, puis renommer `SKILL.md.modele` en `SKILL.md`. Le nom est en minuscules, avec des tirets, 64 caractères au plus, et c'est **exactement** le nom du dossier.
2. Remplir l'en-tête de `SKILL.md`. Seules les clés standard sont autorisées : `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
   - `description` : sur une ligne, 1 024 caractères au plus, sans `<` ni `>`. Elle dit ce que fait le skill **et quand l'utiliser**, avec les mots que l'utilisateur emploierait.
   - `metadata.version` : `"1.0.0"` entre guillemets.
   - `metadata.categorie` : le dossier parent (`pro`, `unc`, `perso`).
   - `metadata.ordre` : facultatif, ordre d'affichage.
   - `metadata.charte` : `skazy-formation` (charte complète) ou `skazy-formation-donnees` (données seules), si le skill a besoin de la charte.
3. Remplir `agents/openai.yaml` (titre et résumé affichés par ChatGPT, Codex et le catalogue) et `assets/icon.svg` (sticker 64 × 64).
4. **Rédiger pour tous les assistants** :
   - aucun nom d'outil propre à une IA (pas de « utilise l'outil X ») ;
   - toujours deux cas : « si tu peux exécuter du Python… sinon… » ;
   - les fichiers s'obtiennent par un script, ou par un JSON collé dans l'atelier ;
   - SKILL.md fait moins de 500 lignes, le détail va dans `references/` ;
   - tout fichier cité dans SKILL.md doit exister (contrôlé).
5. Si le skill produit des fichiers, l'IA écrit seulement un **JSON documenté** (`references/format-….md` et un exemple dans `exemples/`). Un script Python (`scripts/rendre_….py`) le contrôle et le rend. Le script :
   - n'utilise que la bibliothèque standard, `python-docx`, `python-pptx`, `openpyxl` et `pillow`, disponibles dans les bacs à sable ChatGPT et Claude comme dans Pyodide ;
   - expose des fonctions pures (`normaliser_…`, `rendre_…`) appelables depuis l'atelier ;
   - ne doit pas dépendre du réseau : les images passent par `charte.telecharger`, qui sait lire un cache fourni par l'atelier.
6. Ajouter les tests (`tests/py/test_<skill>.py`) et, si le skill a un rendu, son cas dans l'atelier : `site/assets/js/atelier.js` (types `TYPES` et `PYTHON`) et `tests/e2e/site.spec.js`.
7. `npm run synchroniser`, `npm run construire`, `npm run check`, puis tous les tests.

## Charte Skazy Formation

- **La charte qui fait foi est celle du design system [design-skazy](https://github.com/gharel/design-skazy)** (Claude Design, projet `f89db454-87c5-41c4-bebe-3efb5e50fc4f`). Les skills n'ont pas de charte à eux. Les modèles `templates/plan-formation` et `templates/support-formation` sont la seule source de vérité de leur design : un écart entre un rendu et le modèle se corrige dans le skill. Si le modèle doit changer, on le modifie dans design-skazy, sans changer son design.
- design-skazy exporte la charte dans son dossier `charte/` (`npm run charte` dans design-skazy) :
  - `charte.json` : couleurs (jetons), catégories, photos, contact, logos et textes standard de la page 2 du plan ;
  - `plan-formation.css` et `plan-formation.js` : feuille de style et ajustements du modèle de plan, que le HTML du plan reprend tels quels.
- `npm run synchroniser` recopie cet export et les logos dans `commun/charte` (dépôt cherché dans `$DESIGN_SKAZY`, sinon `../design-skazy`), note le commit dans `commun/charte/origine.json`, puis recopie `commun/charte` dans les skills. Une couleur, une catégorie, une photo ou un texte standard manquant s'ajoute dans design-skazy, jamais ici.
- Les rendus HTML reprennent les mesures en pixels des modèles. Les rendus DOCX et PPTX les transposent : 1 px = 0,5 pt sur une slide de 1 920 px, et le A4 correspond à 794 × 1 123 px.
- Les modèles ne sont pas copiés dans ce dépôt : il n'en existe qu'une version, celle de design-skazy. `npm run modeles` les y lit, rend les skills plan et support avec le contenu d'exemple des modèles (`tests/modeles/*.json`, données de test seulement) et compare chaque texte au pixel (place, police, taille, interligne, graisse, couleur). Sans écart, il verrouille l'empreinte des modèles dans `commun/charte/alignement.json`. Si un modèle change dans design-skazy, `npm run check` échoue jusqu'à ce que le skill soit réaligné et la comparaison refaite. Les skills restent libres de leur contenu : seul le design vient des modèles.
- Les scripts lisent les couleurs dans `charte.json` (`couleurs`, `categories`, `jetons`), jamais en dur.
- Utilitaires Python (stickers, typographie, gras `**…**`, images, logos) : seulement dans `commun/charte/charte.py`.
- Ne jamais modifier une copie, ni dans `commun/charte` ni dans un skill : modifier design-skazy (ou `charte.py`), puis `npm run synchroniser`. `npm run check` refuse une copie désynchronisée et, si design-skazy est présent, une charte en retard sur lui.
- Raleway pour les documents et les slides, Georama pour le site. Icônes : **Lucide** 0.460.0 uniquement. Pas d'emoji.
- Le site reprend le bandeau commun et le thème partagé des outils Skazy Formation : clé `skazy-outils:theme`, `site/assets/js/theme.js` et `site/assets/css/charte.css` copiés depuis `www/home`.

## Versions et mises à jour

- Tout changement dans le dossier d'un skill, y compris une resynchronisation de la charte, exige de **monter `metadata.version`** (semver) et d'ajouter une ligne dans `CHANGELOG.md`. `npm run check` le vérifie en comparant avec `HEAD`, ou avec `BASE` en CI.
- Comment chaque installation se met à jour :
  - **Claude Code** : `/plugin marketplace update gharel-skills` ;
  - **CLI** : `npx skills update -g`, ou relancer `installer.ps1` / `installer.sh` ;
  - **Claude.ai et ChatGPT** : réimporter le `.zip`.
- Le catalogue signale à chaque visiteur les skills dont la version a changé depuis sa dernière visite.

## Règles

- **En français** : identifiants, commentaires, textes affichés, messages de commit en Conventional Commits (`feat(quiz): …`, `fix(plan): …`, `docs: …`).
- Typographie française : espace insécable avant `: ; ? !` et entre un nombre et son unité. `charte.typographie()` s'en charge dans les rendus.
- Le site est publié par `.github/workflows/publier.yml` à chaque push sur `main`, seulement si les vérifications passent.
- Ne jamais committer `_site/`, `sorties/`, `.venv/`, `node_modules/`.
