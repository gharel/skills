# Journal des versions

Les versions sont propres à chaque skill (`metadata.version` dans son `SKILL.md`). Les entrées les plus récentes sont en haut.

## 2026-10-29

### skazy-support-formation 1.3.2, skazy-plan-formation 1.4.2, skazy-quiz 1.0.7, notation-etudiants 1.0.7

- Images locales : `charte.url_photo` prenait un chemin de fichier pour un identifiant Unsplash, si bien qu'une capture locale restait vide dans les slides `contenu` et `capture`, la photo du formateur et la couverture. Un fichier local est désormais intégré en data URI : le HTML et le PPTX restent autonomes, sans dépendre du dossier des images.
- Support : les chemins relatifs se lisent depuis le dossier du JSON (`captures/interface.png`). Les images de `avant`, `apres`, des étapes du `pas-a-pas` et le `qrCode` sont intégrées de la même façon, et une image introuvable est signalée par un avertissement.
- Les autres skills reçoivent la nouvelle copie de `charte.py` (`fichier_local`, `url_photo`), sans changement de rendu.

### Dépôt : page de documentation

- Nouvelle page `documentation.html`, reliée au catalogue (héros, section d'installation, pied) : installation par assistant et par système (Windows, macOS, Linux, WSL, Git Bash), fonctionnement de la commande, options, mise à jour automatique, désinstallation, usage des skills (chaîne plan, support, quiz ; notation UNC), statuts et dépannage.
- Le bouton « Copier » met une commande sur une seule ligne, même quand le formatage du HTML la coupe.

### Dépôt : installeurs multi-assistants, inspirés de SkillCrew

- `installer.ps1` (Windows, PowerShell 5.1 et 7) et `installer.sh` (macOS, Linux, WSL ; Git Bash passe la main à PowerShell) posent une seule copie de chaque skill dans `~/.agents/skills`, que lisent Codex, Gemini CLI, GitHub Copilot, Cursor et OpenCode, et un lien par skill pour Claude Code et Windsurf (jonction sous Windows, sans droits administrateur). Fini les copies en double dans `~/.gemini`, `~/.cursor`, `~/.copilot` et `~/.config/opencode` : les anciennes sont retirées. Claude Code ne reçoit pas de lien si le plugin `gharel-skills` est installé.
- Ils lisent le site publié (fichiers contrôlés par la CI) au lieu de la branche `main`, et ne téléchargent que les skills changés. Un manifeste (`~/.agents/.gharel-skills/manifeste.tsv`) retient l'installation : un skill sorti du catalogue ou de la sélection est supprimé, un skill personnel du même nom est sauvegardé, `SKILLS_ACTION=desinstaller` retire tout et restaure les sauvegardes. La sélection (`SKILLS`, `SKILLS_CATEGORIE`) est retenue.
- `SKILLS_AUTO=1` : mise à jour quotidienne par tâche planifiée (Windows), LaunchAgent (macOS), timer systemd utilisateur ou crontab (Linux, WSL). Sous WSL, la commande équipe aussi les assistants de Windows (`SKILLS_WINDOWS=0` pour s'en passer).
- Statuts de skill (`metadata.statut`) : `recommande` par défaut, `disponible` (installé sur demande), `deprecie` (avec `metadata.remplace_par`), `retire`. Le catalogue publie `skills.tsv` et ajoute statut et remplaçant à `skills.json`.

### Dépôt : l'atelier est retiré

- Le site n'a plus d'atelier, et Pyodide n'est plus chargé nulle part : les assistants exécutent eux-mêmes les scripts Python des skills. Le catalogue sert les stickers des skills dans `icones/` au lieu de recopier leurs sources.
- Instructions courtes et version un fichier : l'assistant produit les fichiers avec les scripts du `.zip`. Sans exécution de code, il donne le JSON et la commande à lancer.

### skazy-plan-formation 1.4.1, skazy-support-formation 1.3.1, skazy-quiz 1.0.6, notation-etudiants 1.0.6

- Sans exécution de code, l'assistant donne le JSON et la commande de rendu, à lancer sur son poste, au lieu de renvoyer vers l'atelier. Le quiz peut toujours s'importer dans le Quiz.
- `charte.telecharger` ne lit plus de cache d'images fourni par le navigateur (`IMAGES_LOCALES`) ; `support_pptx.urls_images` est retiré.

### skazy-support-formation 1.3.0

- Le HTML n'emploie plus que la feuille de style que design-skazy exporte pour le modèle « Support de formation » (`support-formation.css`, une classe par style du modèle) : il ne recopie plus aucune valeur de design. Seules restent en ligne les valeurs qui dépendent du contenu (position d'un repère, hauteur d'une barre, nombre de colonnes, taille réduite d'un texte trop long). Rendu identique au pixel (435 textes du modèle comparés, captures avant et après).
- Un mot trop long pour sa colonne réduit la taille du texte au lieu d'être coupé (« communicatio / n ») : titre de couverture, dates de la frise, titres de chapitre, citations, chiffres, en HTML comme en PPTX.
- Images : photos, polaroïds et stickers gardent leurs couleurs vraies, jusqu'au double de leur taille d'affichage ; seuls le logo et les icônes passent sur une palette, sans perte. La photo du polaroïd n'est plus réduite à quelques aplats.
- Durée d'un exercice en étapes reconnue même avec une espace insécable. Avertissement pour chaque slide de contenu sans notes formateur ; notes ajoutées à l'exemple. Documentation des champs `affichage`, `surtitre`, `libelle` et des options `--verifier` et `--formats`.

### skazy-plan-formation 1.4.0

- DOCX : logo et sticker nets à l'impression (220 dpi, sticker en couleurs vraies) ; le fichier pèse 65 Ko environ. Option `--compact` de `docx_google_docs.py` pour un connecteur Google Drive (moins de 30 000 caractères de base64, images moins nettes).
- L'avertissement de débordement de la page 1 nomme le champ qui prend le plus de place. Règles de rédaction : intitulé imposé par l'utilisateur, longueur du public visé.

### skazy-quiz 1.0.5, notation-etudiants 1.0.5

- Typographie : espace insécable aussi pour px, pt, mm, cm, ms, dpi, Ko, Mo, Go, minutes, semaines, mois, participants et le séparateur des milliers (« 1 250 000 »).

## 2026-10-28

### Dépôt : rendus comparés aux modèles de design-skazy

- `npm run modeles` compare au pixel les rendus HTML des skills plan et support à leurs modèles, lus directement dans design-skazy (aucune copie des modèles dans ce dépôt) : même place à 1 px près, même police, taille, interligne, graisse et couleur pour chaque texte du modèle (86 pour le plan, 435 pour le support). Sans écart, il verrouille l'empreinte des modèles dans `commun/charte/alignement.json`.
- `npm run check` refuse un modèle changé dans design-skazy tant que cette comparaison n'a pas été refaite.

### skazy-support-formation 1.2.2

- Titres équilibrés et texte sans mot isolé en fin de paragraphe, comme dans le moteur de diaporama du modèle.
- « Bon à savoir » : le gras garde la couleur du texte. Exercice en étapes : durée « XX minutes » en nombre et unité, modalité et livrable écrits comme dans le modèle.
- Espace insécable (et non plus fine) avant « ? », « ! » et « ; », comme dans le modèle.

### skazy-plan-formation 1.3.1

- Espace insécable (et non plus fine) avant « ? », « ! » et « ; », comme dans le modèle.

### skazy-quiz 1.0.4

- Espace insécable (et non plus fine) avant « ? », « ! » et « ; », comme dans les modèles de design-skazy.

### notation-etudiants 1.0.4

- Espace insécable (et non plus fine) avant « ? », « ! » et « ; », comme dans les modèles de design-skazy.

### skazy-support-formation 1.2.1

- L'exemple n'impose plus ses propres lignes « Passions » et « Desserts » à « Faisons connaissance » : la slide affiche celles du modèle de design-skazy, téléphone et e-mail.

### Dépôt : la charte vient de design-skazy

- Les skills n'ont plus de charte à eux. La charte qui fait foi est celle du design system [design-skazy](https://github.com/gharel/design-skazy) : son export `charte/` (couleurs des jetons, catégories, photos, contact, logos, textes standard du plan, feuille de style et ajustements du modèle « Plan de formation ») est recopié par `npm run synchroniser`, qui note le commit d'origine dans `commun/charte/origine.json`.
- Logos : ceux des modèles du design system (PNG avec marges), à la place des SVG redessinés.

### skazy-plan-formation 1.3.0

- Le HTML reprend tel quel le modèle `plan-formation` de design-skazy : sa feuille de style, son balisage (classes `pf-*`) et ses ajustements (taille des titres, densité du programme, pages de suite si le programme déborde, page 2 resserrée). Le pied de page porte le logo du modèle, à sa taille.
- Valeurs standard de la page 2 : celles du modèle (méthodes, moyens, évaluation).
- DOCX sous 30 000 caractères de base64 (29 400 pour le plan de référence, page 2 complète, au lieu de 34 600), pour l'import par un connecteur Google Drive :
  - fonds, logo et sticker à 84 dpi ;
  - images transparentes sur la palette de leurs couleurs franches ;
  - sans table des polices, sans propriétés du document ni réglages d'affichage.
- Rendu Word inchangé, au dixième de millimètre près.

### skazy-support-formation 1.2.0

- Le HTML et le PPTX reproduisent le modèle « Support de formation » de design-skazy, mesuré slide par slide (écarts de 1 px au plus en HTML) :
  - interligne 1,5 du design system, logo du pied 2,4 fois plus petit (celui du modèle, à sa taille), logo de couverture noir ou blanc selon la catégorie ;
  - photos sans filtre, sauf la couverture et « Questions » ;
  - numéros de chapitre et chiffres « À retenir » à la couleur d'encre, couleurs des pôles de l'accompagnement 360° prises dans les jetons ;
  - « Faisons connaissance » affiche par défaut le téléphone et l'e-mail ; « À retenir » rappelle le chapitre en cours.
- PPTX :
  - graisses 500, 600 et 800 (Raleway Medium, SemiBold, ExtraBold), espacement des lettres des titres, contours à l'intérieur des formes comme en CSS ;
  - positions et tailles corrigées sur une vingtaine de mises en page (code, exercice, exercice en étapes, battle, comparatif, frise, quiz…) ;
  - le comparatif garde son cadre quand il est animé.
- PPTX allégé (`scripts/pptx_google_slides.py`, appliqué à chaque rendu) : dispositions inutilisées, vignette et propriétés retirées, images à leur taille d'affichage, logo et stickers sur la palette de leurs couleurs franches. L'exemple passe de 2,1 à 1,2 Mo.

### skazy-quiz 1.0.3

- Charte recopiée de design-skazy, sans effet sur le quiz.

### notation-etudiants 1.0.3

- Charte recopiée de design-skazy, sans effet sur la notation.

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
