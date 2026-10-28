---
name: skazy-quiz
description: "Crée le quiz d'évaluation d'une formation à partir de son support de formation (JSON du skill skazy-support-formation, PPTX, PDF, HTML ou texte) ou d'un cours, sans rien inventer d'absent du support. Questions progressives (QCM, choix multiples, vrai ou faux, réponse libre, curseur, remise en ordre) avec bonnes réponses et explications. Trois sorties au choix : fichier d'import Kahoot (.xlsx), script Google Forms (formulaire en mode quiz) ou JSON pour le Quiz de Skazy Formation, avec un lien direct qui ouvre le quiz. À utiliser dès que l'on demande un quiz, un QCM, un vrai ou faux, un questionnaire d'évaluation, un test de positionnement ou un Kahoot à partir d'un support ou d'un cours."
license: Propriétaire. Réservé à Skazy Formation.
metadata:
  version: '1.0.5'
  categorie: pro
  auteur: Guillaume Harel, Skazy Formation
  source: https://github.com/gharel/skills
  ordre: '3'
  charte: skazy-formation-donnees
---

# Quiz de formation Skazy Formation

Produire un quiz fiable, pédagogiquement progressif et **strictement fondé sur le support fourni**. Il est livré au format de son choix :

| Sortie           | Fichier                                                                           | Usage                                                                                                               |
| ---------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Quiz Skazy**   | `quiz-….skazy-quiz.json` et un lien `https://gharel.github.io/quiz/#/partage?q=…` | Le Quiz de Skazy Formation, en direct ou en solo. Le lien ouvre le quiz sans rien importer.                         |
| **Kahoot**       | `quiz-….kahoot.xlsx`                                                              | Kahoot ! : créer un kahoot, Ajouter une question > Importer > Importer une feuille de calcul                        |
| **Google Forms** | `quiz-….google-forms.gs`                                                          | Script à coller dans script.google.com. Il crée un formulaire en mode quiz (points, bonnes réponses, commentaires). |

Un corrigé lisible (`quiz-….corrige.md`) est toujours fourni pour le formateur.

## Déroulé

1. **Paramètres.** Repère dans la demande, ou demande en une seule question groupée :
   - le support (fichier, JSON du skill `skazy-support-formation`, texte collé) ;
   - le **nombre de questions** : 10 par défaut, 15 à 20 pour un quiz final ;
   - la **part de vrai ou faux** : 25 % par défaut ;
   - la **sortie** : Quiz Skazy, Kahoot, Google Forms, ou les trois.

   Si la sortie n'est pas précisée, produis les trois et explique à quoi sert chacune.

2. **Vérifier le support.** S'il est trop court ou trop vague pour le volume demandé, dis-le avant de générer. Propose alors de réduire le nombre de questions, de fournir un support plus complet ou de te limiter aux notions présentes.
3. **Récapituler** en quelques lignes avant de produire : support utilisé, nombre de questions, part de vrai ou faux, sortie choisie. Ensuite, enchaîne sans attendre de validation, sauf si un paramètre est vraiment ambigu.
4. **Plan de couverture.** Liste les notions du support : objectifs, chapitres, points à retenir, exercices. Répartis les questions sur ces notions sans en surreprésenter une.
5. **Rédiger** en suivant [references/regles-qcm.md](references/regles-qcm.md) :
   - progression du simple au complexe ;
   - 4 propositions par QCM, une seule bonne réponse ;
   - distracteurs plausibles ;
   - bonne réponse placée à des endroits variés ;
   - une explication courte par question.
6. **Écrire le JSON** au format Skazy Quiz v1, décrit dans [references/format-quiz.md](references/format-quiz.md). C'est le format de base des trois sorties. L'exemple complet est dans `exemples/quiz-exemple.json`. Selon la sortie visée :
   - **Kahoot ou Google Forms** : privilégie les types `single`, `multiple` et `truefalse`, qui passent tels quels.
   - **Kahoot** : respecte aussi ses limites, soit 120 caractères par question et 75 par réponse (idéalement 95 et 60). Voir [references/kahoot.md](references/kahoot.md).
   - **Google Forms** : voir [references/google-forms.md](references/google-forms.md).
   - **Quiz Skazy** : tous les types sont possibles, y compris `text`, `slider` et `order`.
7. **Produire les fichiers** :
   - **Si tu peux exécuter du Python** : lance la commande ci-dessous. Elle écrit les fichiers et affiche le lien du quiz. Les dépendances sont `openpyxl` (pour Kahoot), le reste n'utilise que la bibliothèque standard.

     ```bash
     python scripts/rendre_quiz.py quiz.json --sortie <dossier> --formats skazy,kahoot,forms,corrige
     ```

     Corrige chaque `ERREUR` : ce sont les règles de l'éditeur du Quiz. Lis les `ATTENTION` : conversions pour Kahoot ou Forms, bonne réponse toujours à la même place, explications manquantes.

   - **Sinon** :
     - donne le JSON complet dans un bloc de code ;
     - invite l'utilisateur à l'importer dans le Quiz (https://gharel.github.io/quiz/, Bibliothèque > Importer) ou à le coller dans l'atelier https://gharel.github.io/skills/atelier/, qui produit aussi le fichier Kahoot, le script Google Forms et le lien ;
     - si l'utilisateur ne veut que Kahoot, tu peux donner directement le tableau à coller dans le modèle Kahoot (voir references/kahoot.md).
8. **Livrer.**
   - Donne les paramètres retenus, le lien du quiz et les fichiers.
   - Explique en une ligne comment importer chaque sortie.
   - Signale les questions converties ou écartées pour Kahoot ou Forms.

## Règles impératives

- **Fidélité au support** : chaque question et chaque bonne réponse doivent se vérifier dans le support. N'invente aucune notion, aucun chiffre, aucun exemple et aucune règle. En cas de doute, reformule prudemment ou renonce à la question.
- **Une bonne réponse indiscutable.** Pas de piège, pas de double négation, pas d'indice involontaire : la bonne réponse ne doit pas être plus longue, plus précise ou plus technique que les autres.
- **Explication** pour chaque question : une ou deux phrases qui disent pourquoi la réponse est juste, en s'appuyant sur le support.
- Vouvoiement, ton professionnel et encourageant. Pas d'emoji.

## Fichiers du skill

- `scripts/rendre_quiz.py` : contrôle du JSON (règles de l'éditeur du Quiz et contrôles pédagogiques), puis production du JSON Skazy Quiz, du lien de partage, du fichier Kahoot, du script Google Forms et du corrigé.
- `references/regles-qcm.md` : règles de rédaction, progression, distracteurs.
- `references/format-quiz.md` : format Skazy Quiz v1, type par type, avec les limites de l'éditeur.
- `references/kahoot.md` : modèle d'import Kahoot et conversions.
- `references/google-forms.md` : script Apps Script et conversions.
- `exemples/quiz-exemple.json` : quiz de 12 questions (Excel, les bases) qui utilise les 6 types.

Version 1.0.5. Sources, mises à jour et autres skills : https://gharel.github.io/skills/
