---
name: skazy-support-formation
description: "Crée le support de formation (diaporama) d'une formation Skazy Formation à partir de son plan de formation (JSON du skill skazy-plan-formation, DOCX, PDF ou simple texte). Découpe chaque partie du programme en slides variées, une idée par slide, avec exercices pratiques, quiz, points à retenir et notes formateur, en suivant les 30 mises en page du modèle « Support de formation » du design system Skazy Formation (couleurs, photos et stickers de la catégorie). Produit un HTML à projeter ou à imprimer en PDF et un PPTX pour PowerPoint ou Google Slides. À utiliser dès que l'on demande un support, un diaporama, des slides, un deck ou une présentation de formation, ou de transformer un plan en support."
license: Propriétaire. Réservé à Skazy Formation.
metadata:
  version: '1.2.1'
  categorie: pro
  auteur: Guillaume Harel, Skazy Formation
  source: https://github.com/gharel/skills
  ordre: '2'
  charte: skazy-formation
---

# Support de formation Skazy Formation

Transformer un plan de formation en diaporama prêt à animer. Le diaporama suit le modèle « 4. Support de formation par catégorie » du Skazy Formation Design System :

- format 1920 × 1080, fond blanc, police Raleway ;
- couleur, photos et stickers donnés par la catégorie ;
- 30 mises en page, de la couverture à « Nos autres formations ».

Tu rédiges le contenu dans un fichier JSON. Un script produit le HTML et le PPTX, fidèles à la charte.

## Déroulé

1. **Lire le plan.** Récupère l'intitulé, la catégorie, le niveau, la durée, les objectifs et les parties du programme avec leurs points et leurs durées.
   - Le plan peut venir d'un `plan.json` du skill `skazy-plan-formation`, d'un DOCX ou PDF de plan, ou d'un texte collé.
   - S'il n'y a pas de plan, propose d'abord d'en créer un avec `skazy-plan-formation`. Une demande simple (« un support sur X ») peut aussi être traitée directement : fais alors des hypothèses raisonnables sur le plan.
2. **Cadrer en une seule question groupée, si besoin.** Selon ce qui manque :
   - le nom du formateur et son e-mail (par défaut : Guillaume Harel, formation@skazy.nc) ;
   - le public ;
   - le volume souhaité (support complet ou un seul chapitre) ;
   - les captures ou fichiers d'exercice disponibles.

   Ne repose pas une question dont la réponse figure déjà dans le plan ou dans la conversation.

3. **Concevoir l'architecture, partie par partie, avant de rédiger.** Suis [references/pedagogie.md](references/pedagogie.md) :
   - **ouverture** : couverture, faisons connaissance, objectifs, programme ;
   - **chaque partie du plan** : un intercalaire `chapitre`, puis 3 à 8 slides de contenu aux mises en page variées, au moins un `exercice`, éventuellement un ou deux `quiz`, et un `a-retenir` ;
   - **clôture** : évaluation, ressources, questions, puis au choix battle, accompagnement 360° et autres formations.
4. **Rédiger le JSON** au format de [references/format-support.md](references/format-support.md) : les 30 types de slides, leurs champs et quand les utiliser.
   - Une idée par slide.
   - Textes courts.
   - Gras `**…**` sur les mots-clés.
   - Des **notes formateur** (`notes`) sur chaque slide : ce qu'il faut dire, une question à poser, la durée, la transition.
   - Exemple complet : `exemples/support-exemple.json`, qui utilise les 30 mises en page.
5. **Produire les fichiers** :
   - **Si tu peux exécuter du Python** : lance la commande ci-dessous. Elle crée `support-<intitulé>.html` et `support-<intitulé>.pptx`.

     ```bash
     python scripts/rendre_support.py support.json --sortie <dossier>
     ```

     Corrige chaque `ERREUR`. Prends en compte les `ATTENTION` : texte trop long, chapitre sans exercice, notes manquantes. Les dépendances sont `python-pptx` et `pillow`. Si elles manquent, le script affiche la commande `pip install`. Les photos Unsplash de la banque de la charte sont téléchargées au moment du rendu. Sans accès réseau, le PPTX garde des emplacements à remplir.

   - **Sinon** : donne le JSON complet dans un bloc de code. Invite ensuite l'utilisateur à le coller dans l'atelier https://gharel.github.io/skills/atelier/, qui produit le HTML et le PPTX.
6. **Livrer** :
   - **Résumé** : nombre de slides, chapitres, exercices et quiz.
   - **Emplacements à compléter** : liste les captures d'écran à fournir (slides `contenu`, `capture`, `pas-a-pas`, `avant-apres`) et le QR code de satisfaction.
   - **HTML** : flèches pour naviguer, **N** pour les notes formateur, **F** pour le plein écran, bouton PDF pour l'impression en 16:9.
   - **PPTX** : s'ouvre dans PowerPoint ; dans Google Slides, passer par Fichier > Importer des diapositives. Les notes formateur sont dans les notes du présentateur. Chaque slide de contenu se dévoile clic par clic, en fondu de 0,4 s (`"animations": false` dans `formation` pour les retirer).
   - **Suite** : propose de créer le quiz de la formation à partir de ce support avec le skill `skazy-quiz`.

## Règles essentielles

- **Une idée par slide.** Une slide qui porte plus de 4 éléments se découpe en deux. Le support compte en général plus de slides que le plan n'a de lignes : 25 à 45 slides pour une journée, c'est normal.
- **L'ordre des éléments est l'ordre des clics.** Dans le PPTX, chaque point, carte, étape ou ligne de tableau apparaît à son tour : range-les dans l'ordre où tu veux les présenter.
- **Varier les mises en page.** Ne répète jamais deux fois de suite la même, sauf pour les quiz. Choisis-la selon le contenu, en t'aidant du tableau de `references/format-support.md` :
  - une notion : `contenu` ou `notion-cle` ;
  - une donnée : `chiffre-cle` ou `graphique` ;
  - une procédure : `pas-a-pas` ou `capture` ;
  - un choix : `comparatif` ;
  - une syntaxe : `code` ;
  - une mise en garde : `bon-a-savoir` ;
  - une histoire : `frise`.
- **Pratiquer.** Au moins un exercice par chapitre, au plus un par sous-partie. Mélange manipulations d'outil et mises en situation. Un exercice indique toujours :
  - la durée ;
  - les consignes numérotées, qui commencent par un verbe ;
  - le livrable ;
  - un bonus si possible.
- **Rester fidèle au plan.** Reprends ses objectifs, ses parties, ses durées et son vocabulaire. Pas de notion hors sujet.
- **Ne rien inventer** de vérifiable sans le signaler : chiffre, source, date, nom d'outil. Pour une donnée d'illustration, écris-le dans `source` (« chiffres d'illustration, à vérifier »).
- **Liens cliquables** vers les outils et ressources utiles, regroupés sur la slide `ressources`.
- Le ton suit la charte : professionnel, accessible, encourageant, vouvoiement. Pas d'emoji. Les titres prennent une majuscule initiale seulement.

## Fichiers du skill

- `scripts/rendre_support.py` : contrôle du JSON, puis rendu HTML et PPTX. Il s'appuie sur `support_modele.py`, `support_html.py`, `support_pptx.py` et `charte.py`.
- `scripts/pptx_google_slides.py` : allège le PPTX (dispositions inutilisées, vignette, images à leur taille d'affichage), appliqué à chaque rendu et utilisable sur un PPTX retouché.
- `assets/charte/` : charte du design system design-skazy, seule source de vérité (couleurs, catégories, logos, banque de photos). Le rendu reproduit le modèle « Support de formation » de design-skazy. `scripts/charte.py` la lit et dessine icônes et stickers.
- `references/format-support.md` : les 30 types de slides, leurs champs et quand les utiliser.
- `references/pedagogie.md` : construction du déroulé à partir du plan, rythme, exercices, quiz, notes formateur.
- `exemples/support-exemple.json` : support complet (Excel, les bases).

Version 1.2.1. Sources, mises à jour et autres skills : https://gharel.github.io/skills/
