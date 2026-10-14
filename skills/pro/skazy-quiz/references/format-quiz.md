# Format Skazy Quiz, version 1

C'est le format d'import et d'export du Quiz de Skazy Formation (https://gharel.github.io/quiz/, code source `gharel/quiz`, fichiers `src/lib/types.ts` et `src/lib/transfer.ts`). Les noms de champs sont en anglais, comme dans l'application.

```json
{
  "format": "skazy-quiz",
  "version": 1,
  "quiz": {
    "title": "Excel : les bases",
    "description": "Vérifiez vos acquis…",
    "category": "bureautique",
    "questions": [
      {
        "type": "single",
        "text": "…",
        "answers": ["…", "…", "…", "…"],
        "correct": [1],
        "time": 20,
        "points": 1,
        "explanation": "…"
      }
    ]
  }
}
```

L'enveloppe `{format, version, quiz}` est conseillée. Un objet `{title, description, category, questions}` seul est aussi accepté. Les champs `id`, `createdAt` et `updatedAt` sont facultatifs : l'application les régénère à l'import.

## Le quiz

| Champ         | Obligatoire | Contenu                                                                                                                                                                                                                                        |
| ------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`       | oui         | Titre, 120 caractères au plus                                                                                                                                                                                                                  |
| `description` | conseillé   | Une phrase, 300 caractères au plus                                                                                                                                                                                                             |
| `category`    | conseillé   | `bureautique`, `data`, `dev`, `gestion`, `graphisme`, `ia`, `nocode`, `webmarketing`, `web` ou `general`. Le script accepte aussi les noms des catégories Skazy Formation : « Marketing » donne `webmarketing`, « Développement » donne `dev`. |
| `questions`   | oui         | Liste des questions                                                                                                                                                                                                                            |

## Champs communs des questions

| Champ         | Obligatoire | Contenu                                                                                         |
| ------------- | ----------- | ----------------------------------------------------------------------------------------------- |
| `type`        | oui         | `single`, `multiple`, `truefalse`, `text`, `slider` ou `order`                                  |
| `text`        | oui         | Intitulé, 240 caractères au plus                                                                |
| `time`        | conseillé   | Secondes : 5, 10, 15, 20, 30, 45, 60, 90 ou 120. Une autre valeur est ramenée à la plus proche. |
| `points`      | conseillé   | `1` standard, `2` double, `0` sans points                                                       |
| `explanation` | conseillé   | Explication affichée après la réponse, 300 caractères au plus                                   |
| `image`       | non         | URL `https://…` d'une illustration                                                              |

## Champs propres à chaque type

| Type           | Champs                                                 | Règles (celles de l'éditeur du Quiz)                                                                         |
| -------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `single` (QCM) | `answers` : 2 à 4 textes ; `correct` : `[indice]`      | Une seule bonne réponse ; indices à partir de 0 ; 90 caractères par réponse                                  |
| `multiple`     | `answers` : 2 à 4 textes ; `correct` : `[i, j, …]`     | Au moins deux bonnes réponses                                                                                |
| `truefalse`    | `truth` : `true` ou `false`                            | —                                                                                                            |
| `text`         | `accepted` : 1 à 5 réponses acceptées                  | Casse, accents et ponctuation ignorés                                                                        |
| `slider`       | `slider` : `{min, max, step, answer, tolerance, unit}` | `max > min`, `step > 0`, `min ≤ answer ≤ max`, `tolerance ≥ 0`, `unit` de 12 caractères au plus (facultatif) |
| `order`        | `items` : 3 ou 4 textes, **dans le bon ordre**         | 90 caractères par élément                                                                                    |

## Exemples par type

```json
{ "type": "single", "text": "Par quel caractère commence toujours une formule ?", "answers": ["Le signe +", "Le symbole $", "Le signe =", "Une parenthèse"], "correct": [2], "time": 20, "points": 1, "explanation": "Sans le signe =, Excel traite la saisie comme du texte." }
{ "type": "multiple", "text": "Lesquelles de ces fonctions agrègent une plage ?", "answers": ["SOMME", "MOYENNE", "SI", "MAX"], "correct": [0, 1, 3], "time": 30, "points": 1 }
{ "type": "truefalse", "text": "Une référence relative reste figée à la recopie.", "truth": false, "time": 15, "points": 1 }
{ "type": "text", "text": "Quelle fonction teste une condition ?", "accepted": ["SI", "fonction SI"], "time": 30, "points": 1 }
{ "type": "slider", "text": "Combien de parts au plus dans un graphique en secteurs ?", "slider": { "min": 1, "max": 10, "step": 1, "answer": 5, "tolerance": 0 }, "time": 30, "points": 1 }
{ "type": "order", "text": "Remettez dans l'ordre les étapes de la recopie.", "items": ["Sélectionner la cellule", "Saisir la poignée", "Faire glisser", "Vérifier"], "time": 45, "points": 1 }
```

## Lien de partage

Le script calcule le lien `https://gharel.github.io/quiz/#/partage?q=<données>`, où `<données>` est le JSON `{title, description, category, questions}` compressé en deflate brut, puis encodé en base64url sans remplissage. C'est la même méthode que le bouton « Partager » de l'application. Ce lien ouvre le quiz directement, prêt à jouer ou à enregistrer dans la bibliothèque. Les images intégrées en `data:` en sont retirées.

Sans exécution de code, on importe le fichier `.skazy-quiz.json` dans l'application : Bibliothèque > Importer.
