# Sortie Google Forms

Google Forms n'a pas de format d'import de quiz. La façon la plus fiable de créer un formulaire en mode quiz, avec les bonnes réponses, les points et les commentaires, est un **script Google Apps Script**. Le script `rendre_quiz.py` le produit : `quiz-….google-forms.gs`.

## Utiliser le script

1. Ouvrez https://script.google.com et créez un **Nouveau projet**.
2. Remplacez le code par tout le contenu du fichier `.gs`, puis enregistrez.
3. Choisissez la fonction `creerQuiz` et cliquez sur **Exécuter**. La première fois, autorisez l'accès à Google Forms ; il faut parfois passer par « Paramètres avancés ».
4. Le journal d'exécution affiche deux liens : le formulaire **à partager** et le formulaire **à modifier**. Le formulaire est aussi rangé dans Google Drive.

## Ce que fait le script

- Il crée le formulaire avec `FormApp.create(titre)`, en mode quiz (`setIsQuiz(true)`), avec sa description et une barre de progression.
- Chaque question est obligatoire et reçoit ses points (0, 1 ou 2).
- Les bonnes réponses sont réglées (`createChoice(texte, true)`).
- L'explication est donnée en commentaire, qu'on ait répondu juste ou faux.
- Les images en `https://` sont ajoutées avant leur question.

## Conversions

| Type Skazy            | Dans Google Forms                                                                                                                                                                                                                                     |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `single`, `truefalse` | Choix multiples (une réponse)                                                                                                                                                                                                                         |
| `multiple`            | Cases à cocher                                                                                                                                                                                                                                        |
| `slider`              | Choix multiples à 4 valeurs : la bonne et trois voisines                                                                                                                                                                                              |
| `order`               | Choix multiples à 4 ordres possibles                                                                                                                                                                                                                  |
| `text`                | Réponse courte, sans correction automatique (Apps Script ne permet pas de régler la clé de correction d'une réponse courte). Les réponses acceptées figurent dans le commentaire ; on peut ajouter la clé à la main dans Forms (Questions > Corrigé). |

## Sans exécution de code

Le fichier `.gs` est un simple texte : tu peux l'écrire toi-même en suivant le modèle de `scripts/rendre_quiz.py` (`GABARIT_FORMS`).

1. Remplace `__TITRE__` par le titre du quiz.
2. Remplace `__DONNEES__` par un objet JSON de la forme suivante :

   ```json
   {
     "titre": "…",
     "description": "…",
     "questions": [
       {
         "type": "choix",
         "texte": "…",
         "choix": ["…", "…"],
         "bonnes": [1],
         "points": 1,
         "explication": "…"
       }
     ]
   }
   ```

   - `type` vaut `choix`, `cases` ou `texte` ;
   - `bonnes` contient les indices des bonnes réponses, à partir de 0 ;
   - une question de type `texte` prend un champ `acceptees` au lieu de `choix` et `bonnes`.
