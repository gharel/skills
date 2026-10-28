# Journal des versions

Les versions sont propres à chaque skill (`metadata.version` dans son `SKILL.md`). Les entrées les plus récentes sont en haut.

## 2026-10-28

### skazy-plan-formation 1.2.1

- HTML aligné au pixel sur le modèle `templates/plan-formation` du design system :
  - titre centré dans le bandeau, ajusté en 42, 36 puis 26 px ;
  - page 2 : badge, tuiles, cartes, encart et colonnes aux valeurs du modèle, liens du pied et du contact cliquables.
- Titre des bandeaux à la couleur « sur couleur » de la catégorie (jeton `-on`) : anthracite pour Data, Gestion de projet, Graphisme & UX, IA, Marketing et NoCode, blanc pour Bureautique, Développement et Web. Le skill les écrivait toujours en anthracite.
- DOCX :
  - titre de la page 1 ajusté comme dans le modèle (31,5 pt sur une ligne, 27 pt sur deux, centré dans le bandeau) ;
  - titre de la page 2 ajusté en 16,5, 15 puis 14,25 pt, le bandeau grandissant s'il passe sur deux lignes ;
  - cartes des modalités avec liseré, barre de 5 px, rayon et icônes du modèle, icônes à la couleur d'encre.

### skazy-support-formation 1.1.2

- Charte resynchronisée sur les jetons du design system : encre de Gestion de projet, IA et NoCode, texte anthracite sur Graphisme & UX, IA, Marketing et NoCode (contraste AA).

### skazy-quiz 1.0.2

- Charte resynchronisée sur les jetons de couleur du design system.

### notation-etudiants 1.0.2

- Charte resynchronisée sur les jetons de couleur du design system.

### notation-etudiants 1.0.0

- Premier skill UNC. Il reprend la procédure de correction des TP rendus par mail (GitHub et déploiement), réécrite pour tous les assistants : chaque étape propose une voie avec outils (messagerie, terminal, navigateur, Google Sheets) et une voie sans.
- `scripts/indices_depot.py` relève dans les dépôts git les indices de livraison, de qualité, d'usage possible de l'IA et de copie, sous Windows comme sous Linux.
- `scripts/rendre_notation.py` contrôle `notation.json` et produit un classeur `.xlsx` : synthèse, barème, un onglet par étudiant, bloc IA hors du total. Aussi disponible dans l'atelier.

### skazy-plan-formation 1.2.0

- **Nouvelle mise en page, identique dans Word et dans Google Docs**, sur le modèle du Google Docs « Plan de formation - L'IA pour vos reportings » :
  - page 1 : pastilles arrondies à cheval sur le bandeau, sticker incliné, encadré arrondi, programme « 01 Titre · durée » ;
  - page 2 : cartes effectif, lieu et tarif, puis « Modalités et lieu de la formation » (présentiel, distanciel, hybride), « Accompagnement personnalisé », « Méthodes et moyens pédagogiques », encadrement, évaluation des acquis, mode de validation, boîte de contact.
- Le DOCX est réécrit (`scripts/plan_docx.py`). Les aplats arrondis sont des images ancrées derrière le texte, et le texte est en tableaux sans marge, à interlignes multiples. Rendu par Word, il est à 0,2 mm près du modèle pour toutes les lignes de texte et tous les fonds.
- Le texte du badge « Modalités et infos pratiques » est centré dans le badge : il était 0,7 mm trop bas dans le modèle de référence. Les pastilles de la page 1 sont centrées elles aussi, à 0,1 mm près.
- Dans Google Docs, l'en-tête de la page 2 ne descend plus sous son badge. Une image ancrée à la page y devient un caractère de la taille de son passage : ce passage fait désormais 1 pt.
- Le HTML suit la même mise en page : titre foncé sur le bandeau, page 2 complète.
- Nouveaux champs facultatifs de `modalites` : `formats`, `accompagnement`, `moyens`, `encadrement`, `validation`. Les valeurs standard sont dans la charte. `false` retire un bloc. Un avertissement signale une page 2 trop chargée.
- Objectifs sans gras, comme dans le modèle. Nouvel exemple `exemples/plan-ia-reportings.json`.
- Méthode « .docx vers Google Docs » reprise étape par étape dans `references/google-docs.md` : rendu de référence, allègement, recopie fiable du base64 (au-delà de 30 000 caractères, importer à la main), correction de l'interligne, vérification, limites.
- Nouveaux scripts :
  - `interligne_google_docs.py` : requêtes de correction de l'interligne d'un Google Docs déjà importé ;
  - `comparer_rendus.py` : compare le PDF de Google Docs à celui de Word, ligne à ligne et image par image.
- `docx_google_docs.py` allège davantage le DOCX :
  - il retire les propriétés redondantes, les styles de liste, numérotations, polices et thème inutilisés, et les identifiants de révision ;
  - il réduit les palettes des images ;
  - il vérifie une recopie du base64 avant l'envoi (`--verifier-recopie`) ;
  - il ne s'arrête plus sur une console Windows.

### skazy-support-formation 1.1.1

- Charte resynchronisée : icônes Lucide `users`, `video`, `blend` et `handshake`, valeurs standard des modalités du plan.

### skazy-quiz 1.0.1

- Charte resynchronisée (valeurs standard des modalités du plan), sans effet sur le quiz.

### notation-etudiants 1.0.1

- Charte resynchronisée (valeurs standard des modalités du plan), sans effet sur la notation.

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
