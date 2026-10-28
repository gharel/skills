# Journal des versions

Les versions sont propres à chaque skill (`metadata.version` dans son `SKILL.md`). Les entrées les plus récentes sont en haut.

## 2026-10-28

### notation-etudiants 1.0.0

- Premier skill UNC. Il reprend la procédure de correction des TP rendus par mail (GitHub et déploiement), réécrite pour tous les assistants : chaque étape propose une voie avec outils (messagerie, terminal, navigateur, Google Sheets) et une voie sans.
- `scripts/indices_depot.py` relève dans les dépôts git les indices de livraison, de qualité, d'usage possible de l'IA et de copie, sous Windows comme sous Linux.
- `scripts/rendre_notation.py` contrôle `notation.json` et produit un classeur `.xlsx` : synthèse, barème, un onglet par étudiant, bloc IA hors du total. Aussi disponible dans l'atelier.

### skazy-plan-formation 1.1.0

- Le DOCX s'importe dans Google Docs à l'identique (2 pages, même mise en page) et pèse 25 Ko environ au lieu de 85 : sans gabarit python-docx superflu ni styles inutilisés, images réduites à leur taille d'affichage. Un connecteur Google Drive peut le transmettre en base64.
- Police et langue par défaut du DOCX : Raleway et français. Les petits titres en capitales sont écrits en toutes lettres : Word en français gardait sinon « MODALITES » sans accent.
- Validé par trois imports dans Google Drive, tous convertis du premier coup. Trois écarts de mise en page constatés sont corrigés dans le DOCX, sans changer le rendu Word :
  - les tableaux glissaient vers la gauche (marge gauche des cellules) ;
  - le titre du bandeau remontait de 4 mm (marges hautes différentes dans une rangée) ;
  - le bandeau descendait de 5 mm (paragraphe ajouté par Google avant un tableau d'en-tête).
- Nouveau script `docx_google_docs.py` : prépare pour Google Docs un DOCX retouché dans Word ou venu d'ailleurs (polices embarquées retirées, interligne exact converti en interligne multiple, images allégées, contrôle du base64).
- Nouvelle référence `google-docs.md` : import manuel ou par connecteur, recopie fiable du base64, vérification par export PDF, correction d'un Google Docs déjà importé, limites.

### skazy-support-formation 1.1.0

- Le PPTX dévoile chaque slide de contenu clic par clic : un bloc complet (carte, étape, ligne de tableau, encart) par clic, en fondu de 0,4 s, dans le sens de lecture.
- Titre, sous-titre, surtitre, pied de page, logo et stickers restent fixes. Un panneau ou un fond apparaît avec son premier contenu, jamais avant.
- Couverture, intercalaires, pauses (`image`), « Avez-vous des questions ? » et réponses de quiz restent sans animation.
- Animé, le tableau comparatif n'a plus de cadre global : l'en-tête est fixe et chaque ligne apparaît seule.
- Nouveau champ `formation.animations` (`false` pour retirer les animations).

## 2026-10-14

### skazy-plan-formation 1.0.0

- Première version. Elle fusionne les règles de l'ancien skill `plan-creator` et celles du modèle « Plan de formation » du design system Skazy Formation.
- Le plan est rédigé en JSON, puis rendu en HTML A4 (impression PDF) et en DOCX.
- Le DOCX a de vrais en-têtes et pieds de page Word et Google Docs : bandeau pleine largeur, page 1 différente des suivantes.

### skazy-support-formation 1.0.0

- Première version. Elle fusionne les conventions de l'ancien skill `support-creator` et les 30 mises en page du modèle « Support de formation » du design system.
- Le support est rédigé en JSON, puis rendu en HTML 1920 × 1080 (navigation, notes formateur, PDF) et en PPTX (PowerPoint, Google Slides) avec les notes du présentateur.

### skazy-quiz 1.0.0

- Première version. Elle reprend les règles de l'ancien skill `qcm-creator` et le format Skazy Quiz v1 (6 types de questions).
- Sorties : JSON Skazy Quiz et lien de partage direct, fichier d'import Kahoot (.xlsx), script Google Forms (.gs) et corrigé.

### Dépôt

- Catalogue sur GitHub Pages, atelier Pyodide, scripts d'installation, place de marché Claude Code, compatibilité `npx skills`.
