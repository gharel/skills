---
name: skazy-plan-formation
description: "Crée, restructure ou enrichit un plan de formation (fiche programme A4 d'une ou deux pages) aux couleurs de Skazy Formation, à partir d'un simple sujet, de notes ou d'un plan existant. Rédige l'intitulé, la description, 3 à 5 objectifs pédagogiques observables (taxonomie de Bloom), les prérequis, le public, la durée, le programme en parties et les modalités, puis produit un HTML imprimable en PDF et un DOCX pour Word ou Google Docs, fidèles au modèle « Plan de formation » du design system Skazy Formation. À utiliser dès que l'on demande un plan de formation, un programme ou une fiche de formation, un déroulé ou un syllabus, même sans citer Skazy."
license: Propriétaire. Réservé à Skazy Formation.
metadata:
  version: '1.2.0'
  categorie: pro
  auteur: Guillaume Harel, Skazy Formation
  source: https://github.com/gharel/skills
  ordre: '1'
  charte: skazy-formation
---

# Plan de formation Skazy Formation

Produire une fiche programme professionnelle, directement réutilisable, qui reprend le modèle « 3. Plan de formation » du Skazy Formation Design System :

- **page 1** : bandeau à la couleur de la catégorie, intitulé, pastilles (catégorie, niveau), sticker, description, objectifs, encadré prérequis / public / durée, programme sur deux colonnes ;
- **page 2** : effectif, lieu et tarif ; modalités (présentiel, distanciel, hybride) ; accompagnement personnalisé ; méthodes et moyens pédagogiques ; encadrement, évaluation des acquis et validation ; contact.

Le travail se fait en deux temps :

1. Tu rédiges le contenu dans un fichier JSON.
2. Un script produit les documents.

Le rendu est donc identique quel que soit l'assistant utilisé.

## Déroulé

1. **Comprendre la demande.** Repère la source :
   - un sujet seul ;
   - un plan à restructurer ;
   - des notes ou un document brut.

   Repère aussi l'intention : créer, restructurer, enrichir ou reformuler. Déduis le niveau, la durée et le public s'ils manquent : fais des hypothèses professionnelles raisonnables plutôt que de poser des questions inutiles. Ne pose une question groupée que si la **catégorie** ou la **durée** sont vraiment ambiguës.

2. **Choisir la catégorie** parmi les 9 du design system, écrites ainsi :
   - Bureautique
   - Data
   - Développement
   - Gestion de projet
   - Graphisme & UX
   - Intelligence Artificielle
   - Marketing
   - NoCode
   - Web

   Elle fixe la couleur et le sticker.

3. **Rédiger** en suivant [references/regles-redaction.md](references/regles-redaction.md). L'essentiel :
   - **description** : 2 à 4 lignes, qui commencent par un verbe d'action (Découvrez, Maîtrisez, Créez…) et jamais par « Cette formation » ;
   - **objectifs** : 3 à 5, qui commencent par un verbe observable, sans gras (`Créer un tableau…`) ;
   - **programme** : 2 à 8 parties de 2 à 6 points, progressives ; la dernière est souvent un projet final ou une mise en pratique ;
   - **durée** : réaliste, entre 2 h et 5 jours, cohérente avec le niveau, les objectifs et le programme ;
   - **page 2** : adapte au sujet les méthodes (part de pratique, cas fil rouge), les moyens (logiciels sur les postes) et l'évaluation ; garde les valeurs standard pour le reste.
4. **Écrire le JSON** au format décrit dans [references/format-plan.md](references/format-plan.md). Exemples complets : `exemples/plan-exemple.json` et `exemples/plan-ia-reportings.json`.
5. **Produire les documents** :
   - **Si tu peux exécuter du Python** : lance la commande ci-dessous. Elle crée `plan-<intitulé>.html` et `plan-<intitulé>.docx`.

     ```bash
     python scripts/rendre_plan.py plan.json --sortie <dossier>
     ```

     Le script contrôle le contenu. Corrige chaque `ERREUR`. Lis chaque `ATTENTION`, surtout celle qui signale un débordement de la page 1 : raccourcis alors les points du programme. Les dépendances sont `python-docx` et `pillow`. Si elles manquent, le script affiche la commande `pip install` à lancer.

   - **Sinon** : donne le JSON complet dans un bloc de code. Invite ensuite l'utilisateur à le coller dans l'atelier https://gharel.github.io/skills/atelier/, qui produit les mêmes fichiers HTML et DOCX dans le navigateur.
6. **Livrer** :
   - Présente un résumé en quelques lignes : intitulé, catégorie, niveau, durée, nombre de parties.
   - Donne les fichiers produits, ou le JSON.
   - Rappelle comment s'en servir :
     - le HTML s'imprime en PDF (bouton « Imprimer ou enregistrer en PDF ») ;
     - le DOCX s'ouvre dans Word ;
     - le DOCX s'importe tel quel dans Google Docs, avec la même mise en page : Fichier > Ouvrir > Importer, ou un connecteur Google Drive qui crée le fichier avec conversion. Il est léger (25 Ko environ) pour passer par un connecteur. Si le connecteur demande le contenu en base64 :
       - `python scripts/docx_google_docs.py plan-<intitulé>.docx --base64` l'écrit dans un `.b64.txt` ;
       - affiche-le juste avant de le recopier, écris d'abord ta recopie dans un fichier, et vérifie-la avec `python scripts/docx_google_docs.py --verifier-recopie <fichier>.b64.txt recopie.b64` ; n'envoie qu'une recopie identique ;
       - si la conversation contient déjà une version précédente du fichier, confie la recopie à un contexte neuf (sous-agent ou nouvelle conversation) : la recopie y revient sinon d'elle-même ;
     - un DOCX retouché dans Word se prépare d'abord avec `python scripts/docx_google_docs.py plan.docx`, qui l'allège et retire l'interligne exact ; un Google Docs déjà importé en interligne exact se corrige avec `scripts/interligne_google_docs.py` ;
     - pour vérifier l'import, `python scripts/comparer_rendus.py reference.pdf google-docs.pdf` compare l'export PDF de Google Docs au rendu de Word, ligne à ligne et image par image.

     La méthode complète, ses règles, la vérification et les limites sont dans [references/google-docs.md](references/google-docs.md).

   - Propose la suite logique : créer le support de formation à partir de ce plan avec le skill `skazy-support-formation`, en lui donnant le JSON.

## Quand on te donne un plan existant

- Améliore l'ordre pédagogique au lieu de le garder à tout prix.
- Fusionne les redites et découpe les parties surchargées.
- Reformule les titres vagues en titres orientés résultat.
- Garde le sujet et le niveau, sauf si la source montre clairement un décalage. Dans ce cas, signale-le.

## Contrôle avant de livrer

- [ ] Intitulé court et accrocheur (60 caractères au plus).
- [ ] Description qui donne envie, et qui cite les outils ou méthodes utilisés, sans parler du document fourni.
- [ ] Objectifs observables, adaptés au niveau et à la durée, et tous couverts par le programme.
- [ ] Prérequis justes : par défaut « Savoir utiliser un ordinateur et Internet » ; pour un niveau Intermédiaire ou Avancé, le niveau précédent ou des acquis équivalents.
- [ ] Programme progressif, au même niveau de détail d'une partie à l'autre, qui tient sur la page 1.
- [ ] Aucune information inventée sur Skazy (tarifs, dates, lieux) : laisse les valeurs par défaut des modalités si tu ne les connais pas.

## Fichiers du skill

- `scripts/rendre_plan.py` : contrôle du JSON, rendu HTML (A4) et DOCX.
- `scripts/plan_docx.py` : rendu DOCX, identique dans Word et dans Google Docs (fonds arrondis ancrés derrière le texte).
- `scripts/docx_google_docs.py` : DOCX prêt pour Google Docs (allégé, sans interligne exact), appliqué à chaque rendu et utilisable sur un DOCX retouché ; vérifie aussi la recopie du base64.
- `scripts/interligne_google_docs.py` : requêtes de correction de l'interligne d'un Google Docs déjà importé.
- `scripts/comparer_rendus.py` : comparaison du PDF de Google Docs avec celui de Word (demande PyMuPDF).
- `scripts/charte.py` et `assets/charte/` : couleurs, logos, icônes et stickers de la charte Skazy Formation.
- `references/regles-redaction.md` : règles de rédaction détaillées et calibrage par niveau.
- `references/format-plan.md` : format du JSON, champ par champ.
- `references/google-docs.md` : import dans Google Docs à l'identique, par Drive ou par un connecteur, et vérification.
- `exemples/plan-exemple.json` : plan complet (Excel, les bases), modalités standard.
- `exemples/plan-ia-reportings.json` : plan complet (L’IA pour vos reportings), page 2 adaptée au sujet.

Version 1.2.0. Sources, mises à jour et autres skills : https://gharel.github.io/skills/
