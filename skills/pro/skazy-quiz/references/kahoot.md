# Sortie Kahoot

Kahoot ! importe un quiz depuis une feuille de calcul `.xlsx` au gabarit officiel. Le script `rendre_quiz.py` produit ce fichier (`quiz-….kahoot.xlsx`) avec la même structure :

| Ligne          | Contenu                                                                                                                                                                                                                               |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2 à 6          | Consignes du modèle (ignorées à l'import)                                                                                                                                                                                             |
| 8              | En-têtes : `Question - max 120 characters`, `Answer 1 - max 75 characters` … `Answer 4 - max 75 characters`, `Time limit (sec) – 5, 10, 20, 30, 60, 90, 120, or 240 secs`, `Correct answer(s) - choose at least one` (colonnes B à H) |
| 9 et suivantes | Une question par ligne : n° en A, question en B, réponses en C à F, temps en G, bonne(s) réponse(s) en H (`2`, ou `1,3` s'il y en a plusieurs)                                                                                        |

## Limites de Kahoot

- Seules les questions **à choix** s'importent : 2 à 4 réponses, au moins une bonne.
- Question : **120 caractères** au plus. Réponse : **75 caractères** au plus. Les anciennes limites de 95 et 60 restent un bon repère pour la lisibilité sur un écran projeté.
- Temps limite : 5, 10, 20, 30, 60, 90, 120 ou 240 secondes.
- Fichier de 1 Mo au plus.

## Conversions faites par le script

| Type Skazy           | Dans Kahoot                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------ |
| `single`, `multiple` | Tels quels                                                                                       |
| `truefalse`          | Deux réponses « Vrai » et « Faux »                                                               |
| `slider`             | QCM à 4 valeurs : la bonne et trois valeurs voisines, hors de la marge d'erreur                  |
| `order`              | QCM à 4 ordres possibles, si chaque ordre tient en 75 caractères ; sinon la question est écartée |
| `text`               | Écartée : l'import Kahoot ne gère pas les réponses libres                                        |

- Le temps de chaque question est ramené à la valeur Kahoot la plus proche ; à égalité, la plus longue.
- Une question ou une réponse trop longue est raccourcie avec « … ».
- Chaque conversion est signalée par un `ATTENTION`. Mieux vaut écrire directement des questions courtes quand Kahoot est la cible.

## Importer dans Kahoot

1. Sur https://create.kahoot.it, créez un kahoot.
2. Cliquez sur **Ajouter une question**, puis **Importer**.
3. Choisissez **Importer une feuille de calcul**, puis le fichier `.kahoot.xlsx`.
4. Vérifiez l'aperçu et corrigez les éventuelles lignes signalées. Ajoutez des images si besoin, puis enregistrez.

## Sans exécution de code

Donne un tableau à coller à partir de la cellule B9 du modèle officiel, téléchargeable depuis la fenêtre d'import de Kahoot. Le tableau a 7 colonnes séparées par des tabulations, dans cet ordre : question, réponse 1, réponse 2, réponse 3, réponse 4, temps, bonnes réponses.
