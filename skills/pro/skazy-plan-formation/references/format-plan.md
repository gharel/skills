# Format du fichier plan.json (`skazy-plan`, version 1)

Un objet JSON encodé en UTF-8. Le gras s'écrit `**ainsi**` dans les textes. Le script corrige seul les espaces insécables de la typographie française, devant `:`, `?`, `!` et entre un nombre et son unité.

| Champ         | Type             | Obligatoire | Contenu                                                                                                                                                           |
| ------------- | ---------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `format`      | texte            | conseillé   | Toujours `"skazy-plan"`                                                                                                                                           |
| `version`     | nombre           | conseillé   | Toujours `1`                                                                                                                                                      |
| `intitule`    | texte            | oui         | Titre de la formation, 60 caractères au plus                                                                                                                      |
| `categorie`   | texte            | oui         | L'une des 9 catégories : `Bureautique`, `Data`, `Développement`, `Gestion de projet`, `Graphisme & UX`, `Intelligence Artificielle`, `Marketing`, `NoCode`, `Web` |
| `niveau`      | texte            | oui         | `Initiation`, `Intermédiaire` ou `Avancé`                                                                                                                         |
| `etiquette`   | texte            | non         | Texte de la première pastille (par défaut : la catégorie)                                                                                                         |
| `sticker`     | booléen          | non         | `false` pour retirer le sticker (par défaut : `true`)                                                                                                             |
| `description` | texte            | oui         | 2 à 4 lignes, commence par un verbe d'action                                                                                                                      |
| `objectifs`   | liste de textes  | oui         | 3 à 5 objectifs, verbe en gras : `"**Créer** un tableau…"`                                                                                                        |
| `prerequis`   | texte            | oui         | Connaissances nécessaires avant la formation                                                                                                                      |
| `public`      | texte            | oui         | Profils ou postes concernés                                                                                                                                       |
| `duree`       | texte            | oui         | Par exemple `"2 jours (14 h)"`                                                                                                                                    |
| `programme`   | liste de parties | oui         | 2 à 8 parties, voir le tableau suivant                                                                                                                            |
| `modalites`   | objet ou `false` | non         | Page 2. `false` = plan d'une seule page. Champs absents = valeurs standard                                                                                        |

Une partie du `programme` :

| Champ    | Type            | Obligatoire | Contenu                                                                  |
| -------- | --------------- | ----------- | ------------------------------------------------------------------------ |
| `titre`  | texte           | oui         | Titre de la partie (la numérotation 01, 02… est automatique)             |
| `points` | liste de textes | oui         | 2 à 6 notions, quelques mots chacune                                     |
| `duree`  | texte           | non         | Par exemple `"1 h 30"`, affiché à côté du titre et repris par le support |

Les champs de `modalites`, tous facultatifs :

| Champ        | Valeur standard                                                                                                                                                                                          |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `methodes`   | « Alternance d'apports théoriques et d'ateliers pratiques. Mises en situation en sous-groupes sur un cas réel apporté par les participants. Support de formation remis à chaque participant. »           |
| `evaluation` | « Quiz de positionnement en début et en fin de formation pour mesurer la progression. Évaluation des acquis par la mise en pratique. Questionnaire de satisfaction et attestation de fin de formation. » |
| `effectif`   | « 8 personnes max. »                                                                                                                                                                                     |
| `lieu`       | « Nouméa ou vos locaux »                                                                                                                                                                                 |
| `tarif`      | « Sur devis »                                                                                                                                                                                            |

## Exemple minimal

```json
{
  "format": "skazy-plan",
  "version": 1,
  "intitule": "Prompter efficacement avec ChatGPT",
  "categorie": "Intelligence Artificielle",
  "niveau": "Initiation",
  "description": "Gagnez du temps au quotidien en confiant à ChatGPT la rédaction, la synthèse et la reformulation de vos documents. Vous apprenez à écrire des consignes précises et à vérifier les réponses.",
  "objectifs": [
    "**Rédiger** une consigne structurée (rôle, contexte, tâche, format)",
    "**Utiliser** ChatGPT pour résumer, reformuler et traduire un document",
    "**Vérifier** une réponse et repérer ses limites"
  ],
  "prerequis": "Savoir utiliser un ordinateur et Internet",
  "public": "Toute personne qui rédige ou synthétise des documents",
  "duree": "1 jour (7 h)",
  "programme": [
    {
      "titre": "Comprendre l'IA générative",
      "points": [
        "Fonctionnement d'un modèle de langage",
        "Forces et limites",
        "Confidentialité des données"
      ]
    },
    {
      "titre": "Écrire de bonnes consignes",
      "points": ["La méthode RCTF", "Exemples et contre-exemples", "Itérer sur une réponse"]
    },
    {
      "titre": "Cas pratiques",
      "points": [
        "Résumer un compte rendu",
        "Rédiger un e-mail délicat",
        "Atelier pratique : vos propres documents"
      ]
    }
  ]
}
```

L'exemple complet, avec durées par partie et modalités, est dans `exemples/plan-exemple.json`.

## Contrôles du script

`python scripts/rendre_plan.py plan.json --verifier` signale deux types de problèmes.

**Erreurs, qui bloquent le rendu** :

- champ obligatoire manquant ;
- catégorie ou niveau inconnus ;
- partie sans titre.

**Avertissements** :

- intitulé ou description trop longs ;
- description qui commence par « Cette formation » ;
- nombre d'objectifs, de parties ou de points hors des fourchettes ;
- verbe d'objectif peu observable ;
- page 1 trop chargée.
