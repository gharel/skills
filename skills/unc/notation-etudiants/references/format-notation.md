# Format du fichier notation.json (`notation-etudiants`, version 1)

`scripts/rendre_notation.py` (ou l'atelier) lit ce JSON. Il produit un classeur `.xlsx` qui contient :

- un onglet **Synthèse** ;
- un onglet **Barème** ;
- un onglet par étudiant.

Les espaces insécables de la typographie française sont ajoutés automatiquement.

```json
{
  "format": "notation-etudiants",
  "version": 1,
  "controle": {
    "intitule": "CC4 · Réducteur d'URL",
    "matiere": "…",
    "enonce": "https://…",
    "date": "2026-10-20"
  },
  "bareme": [
    { "id": "mail", "libelle": "Mail de rendu", "max": 1, "regle": "1 : … ; 0,5 : … ; 0 : …" },
    {
      "id": "deploiement",
      "libelle": "Déploiement",
      "penalite": -10,
      "regle": "0 si en ligne ; -10 sinon"
    }
  ],
  "etudiants": [
    {
      "nom": "MARTIN",
      "prenom": "Léa",
      "statut": "evalue",
      "rendu": {
        "date": "18/10/2026 21:40",
        "github": "https://…",
        "deploiement": "https://…",
        "horsDelai": false
      },
      "notes": {
        "mail": { "note": 1, "justification": "…" },
        "deploiement": { "note": 0, "justification": "…" }
      },
      "commentaire": "…",
      "ia": {
        "probabilite": "20 à 50 %",
        "part": "10 à 30 %",
        "indices": "…",
        "parties": "…",
        "declare": ""
      },
      "aTrancher": ["…"]
    }
  ],
  "promotion": { "defauts": ["…"], "interpretations": ["…"] }
}
```

Exemple complet : `exemples/notation-exemple.json`.

## Bloc `controle`

| Champ      | Obligatoire | Contenu                                        |
| ---------- | ----------- | ---------------------------------------------- |
| `intitule` | oui         | Nom du TP ou du contrôle, qui nomme le fichier |
| `matiere`  | non         | Enseignement                                   |
| `enonce`   | non         | Lien de l'énoncé                               |
| `date`     | non         | Date du contrôle ou de l'échéance              |

## Liste `bareme`

Une entrée par ligne du barème, dans l'ordre du tableur de l'enseignant.

| Champ      | Contenu                                                                                    |
| ---------- | ------------------------------------------------------------------------------------------ |
| `id`       | Identifiant court et unique (`mail`, `indentation`, `deploiement`…), repris dans `notes`   |
| `libelle`  | Intitulé affiché                                                                           |
| `max`      | Points de la ligne (nombre positif). Le total « sur » est la somme des `max`               |
| `penalite` | À la place de `max`, pour une pénalité : la valeur la plus basse (nombre négatif, ex. -10) |
| `regle`    | La règle appliquée à tous, écrite avant de noter (onglet Barème)                           |

## Liste `etudiants`

| Champ         | Contenu                                                                                                                                                      |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `nom`         | Nom de famille (affiché en majuscules)                                                                                                                       |
| `prenom`      | Prénom                                                                                                                                                       |
| `statut`      | `evalue` (par défaut), `non-evaluable` (dépôt inaccessible…) ou `sans-rendu`                                                                                 |
| `rendu`       | `date` (heure locale), `github`, `deploiement`, `horsDelai` (booléen)                                                                                        |
| `notes`       | Pour chaque `id` du barème : `{note, justification}`. La note peut être `0.5` ou `"0,5"`. Une pénalité absente vaut 0                                        |
| `libelles`    | Projet libre : nouveaux intitulés de lignes, par `id` (`{"validation": "1.1 Récupération des données"}`). Points et maxima ne changent pas                   |
| `commentaire` | Synthèse pour l'étudiant. Pour un non évaluable ou un sans-rendu, la raison                                                                                  |
| `ia`          | `probabilite` et `part` : fourchettes « 50 à 80 % » ; `indices` : indices et indices contraires ; `parties` : parties concernées ; `declare` : usage déclaré |
| `aTrancher`   | Points que l'enseignant doit trancher : copie, échange oral proposé, retard, pénalité discutable                                                             |

## Bloc `promotion`

- `defauts` : défauts récurrents de la promotion.
- `interpretations` : interprétations du barème retenues.

## Contrôles du script

`python scripts/rendre_notation.py notation.json --verifier` contrôle le JSON sans rien produire.

**Erreurs, qui bloquent le rendu** :

- champ obligatoire absent ;
- critère inconnu, ou identifiant en double ;
- ligne de barème sans `max` ni `penalite`, ou avec les deux ;
- note manquante, illisible, supérieure au maximum, ou pénalité hors bornes ;
- note donnée à un étudiant non évaluable ou sans rendu ;
- estimation de l'IA qui n'est pas une fourchette « x à y % » ;
- fourchette qui monte à 100 % sans usage déclaré.

**Avertissements** :

- règle de barème absente ;
- note sans justification ;
- total négatif ;
- estimation de l'IA absente, ou sans indices ;
- probabilité de 50 % ou plus sans échange oral proposé dans `aTrancher` ;
- tiret cadratin ou émoji dans un texte.

## Classeur produit

- **Synthèse** : une ligne par étudiant, avec :
  - la note, sous forme de formule liée à son onglet ;
  - le total sur lequel elle est notée ;
  - le statut ;
  - les estimations de l'IA ;
  - la date de rendu ;
  - les points à trancher.

  Les étudiants sont classés de la meilleure note à la plus basse, puis viennent les non évaluables et les sans-rendu. Suivent le rappel sur les estimations de l'IA, les défauts de la promotion et les interprétations du barème.

- **Barème** : critère, maximum, pénalité et règle.
- **Un onglet par étudiant** (« NOM Prénom ») :
  - colonnes A critère, B note, C maximum ou pénalité, D justification ;
  - une ligne Total, sous forme de formule `SUM` ;
  - le commentaire, le rendu et les points à trancher ;
  - le bloc IA sur fond gris, en texte, hors du total.
