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
| `objectifs`   | liste de textes  | oui         | 3 à 5 objectifs qui commencent par un verbe observable : `"Créer un tableau…"`                                                                                    |
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

Les champs de `modalites`, tous facultatifs. Un champ absent reprend la valeur standard ; `false` (ou une liste vide) retire un bloc facultatif. Les valeurs standard sont les textes de la page « Modalités et infos pratiques » du modèle `plan-formation` de design-skazy (`modalitesParDefaut` dans `assets/charte/charte.json`).

| Champ            | Type             | Contenu et valeur standard                                                                                                                                                                                                                                                                            |
| ---------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `effectif`       | texte            | « 8 personnes max. »                                                                                                                                                                                                                                                                                  |
| `lieu`           | texte            | « Nouméa ou vos locaux »                                                                                                                                                                                                                                                                              |
| `tarif`          | texte            | « Sur devis »                                                                                                                                                                                                                                                                                         |
| `formats`        | liste ou `false` | Cartes « Modalités et lieu de la formation », 3 au plus : `{"titre", "texte", "icone"}` (icône Lucide de la charte : `users`, `video`, `blend`, `circle-check`, `clock`, `target`, `lightbulb`…). Par défaut : En présentiel (`users`), En distanciel (`video`), Hybride (`blend`), avec leurs textes |
| `accompagnement` | texte ou `false` | Suite de « Accompagnement personnalisé : ». Par défaut : « la formation s'appuie sur vos besoins métiers. »                                                                                                                                                                                           |
| `methodes`       | texte            | « Alternance d'apports théoriques et d'ateliers pratiques : présentation théorique, étude de cas en groupe, puis cas pratique sur une situation réelle apportée par les participants. »                                                                                                               |
| `moyens`         | liste de textes  | Puces sous les méthodes. Par défaut : salle équipée d'un matériel de projection, support de présentation numérique remis à chaque participant, poste informatique individuel                                                                                                                          |
| `encadrement`    | texte ou `false` | « Formateur qualifié. Ses références professionnelles et pédagogiques sont en annexe ou sur demande. »                                                                                                                                                                                                |
| `evaluation`     | texte ou `false` | « Quiz en fin de formation pour valider les acquis, complété par la mise en pratique en atelier. Un questionnaire de satisfaction clôt la formation. »                                                                                                                                                |
| `validation`     | texte ou `false` | « Attestation de formation délivrée aux participants ayant validé les acquis. »                                                                                                                                                                                                                       |

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
    "Rédiger une consigne structurée (rôle, contexte, tâche, format).",
    "Utiliser ChatGPT pour résumer, reformuler et traduire un document.",
    "Vérifier une réponse et repérer ses limites."
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

Deux exemples complets, avec durées par partie et modalités : `exemples/plan-exemple.json` (Excel, modalités standard) et `exemples/plan-ia-reportings.json` (toutes les rubriques de la page 2 adaptées au sujet).

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
