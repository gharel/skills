# Format du fichier support.json (`skazy-support`, version 1)

```json
{
  "format": "skazy-support",
  "version": 1,
  "formation": { "intitule": "…", "categorie": "…", "niveau": "…", "duree": "…" },
  "slides": [{ "type": "couverture" }, { "type": "objectifs", "objectifs": ["…"], "notes": "…" }]
}
```

Dans tous les textes :

- le gras s'écrit `**ainsi**` ;
- les espaces insécables de la typographie française sont ajoutés automatiquement.

Une image (`photo`, `image`, `qrCode`, `photoFormateur`, `photoCouverture`, images de `avant`, `apres` et des étapes du `pas-a-pas`) peut prendre trois formes :

- une URL `https://…` ;
- un identifiant de la banque Unsplash validée (`photo-1616587226960-4a03badbe8bf`) ;
- un chemin de fichier local, absolu ou relatif au dossier du JSON (`captures/interface.png`). L'image est intégrée au HTML et au PPTX, qui restent autonomes. Un fichier introuvable est signalé par un avertissement.

## Bloc `formation`

| Champ                | Obligatoire | Contenu                                                                                                                                    |
| -------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `intitule`           | oui         | Titre de la formation, affiché en couverture et dans chaque pied de slide                                                                  |
| `categorie`          | oui         | `Bureautique`, `Data`, `Développement`, `Gestion de projet`, `Graphisme & UX`, `Intelligence Artificielle`, `Marketing`, `NoCode` ou `Web` |
| `niveau`             | conseillé   | `Initiation` (par défaut), `Intermédiaire` ou `Avancé`                                                                                     |
| `duree`              | conseillé   | Par exemple `"2 jours · 14 h"`                                                                                                             |
| `formateur`, `email` | non         | Par défaut : Guillaume Harel, formation@skazy.nc                                                                                           |
| `role`               | non         | Sous le nom du formateur. Par défaut : « Formateur et consultant »                                                                         |
| `photoCouverture`    | non         | Par défaut : la première photo de la banque de la catégorie                                                                                |
| `photoFormateur`     | non         | Photo ronde de la slide « Faisons connaissance »                                                                                           |
| `stickers`           | non         | `false` pour retirer les stickers                                                                                                          |
| `animations`         | non         | `false` pour un PPTX sans animations (voir « Animations du PPTX »)                                                                         |

## Champs communs à toutes les slides

| Champ   | Contenu                                                                                                                                    |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `type`  | L'un des 30 types ci-dessous (obligatoire)                                                                                                 |
| `notes` | Notes formateur : texte ou liste de lignes. Elles vont dans les notes du présentateur du PPTX et s'affichent avec la touche N dans le HTML |

## Les 30 types de slides

Les champs marqués `*` sont obligatoires. Les nombres entre crochets donnent la quantité conseillée.

### Ouverture

| Type                   | Rôle                                                   | Champs                                                                                                                                                                            |
| ---------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `couverture`           | Titre, catégorie, niveau, durée, formateur, photo      | `photo`                                                                                                                                                                           |
| `faisons-connaissance` | Présentation du formateur et tour de table             | `titre`, `infos` [0-3] : `{label, texte, lien}` (par défaut : téléphone et e-mail), `tourDeTable` [4] : textes (par défaut : prénom et poste, usage, attentes, une info), `photo` |
| `objectifs`            | Objectifs pédagogiques numérotés, photo à droite       | `objectifs*` [3-5] : verbe en gras, `intro`, `photo`                                                                                                                              |
| `programme`            | Parties du programme et leurs durées, sur fond couleur | `parties*` [2-8] : `{titre, duree}`, `duree`, `photo`                                                                                                                             |

### Chapitres et contenus

| Type           | Rôle, quand l'utiliser                                       | Champs                                                                                                                                                                                                                                                                             |
| -------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `chapitre`     | Intercalaire numéroté au début de chaque partie du plan      | `titre*`, `duree`, `points` [0-5] (ceux de la partie du plan, regroupés s'il y en a plus de 5), `numero` (automatique), `photo`                                                                                                                                                    |
| `contenu`      | Une notion expliquée, avec une capture ou un schéma à droite | `titre*`, `texte`, `points` [0-4] : texte ou `{label, texte}`, `image`, `legendeImage`                                                                                                                                                                                             |
| `notion-cle`   | Une définition à retenir, en très grand                      | `titre*`, `definition*`, `termes` [0-3] : `{terme, definition}`, `surtitre`                                                                                                                                                                                                        |
| `chiffre-cle`  | Un chiffre fort qui marque les esprits                       | `chiffre*`, `unite`, `phrase*`, `explication`, `reperes` [0-2] : `{valeur, texte}`, `source`                                                                                                                                                                                       |
| `graphique`    | Une tendance ou une comparaison chiffrée (histogramme)       | `titre*`, `barres*` [3-8] : `{label, valeur, affichage}` (`affichage` : valeur écrite au-dessus de la barre, par défaut le nombre), `miseEnAvant` (indice, par défaut la dernière), `surtitre` (par défaut « À retenir »), `chiffre`, `message` (160 caractères au plus), `source` |
| `frise`        | Repères chronologiques, histoire d'un outil                  | `titre*`, `intro`, `etapes*` [3-6] : `{date, texte}` (la dernière est mise en avant)                                                                                                                                                                                               |
| `image`        | Image pleine page avec légende : pause, résultat, discussion | `titre*`, `texte`, `surtitre`, `image` (par défaut : photo de la catégorie)                                                                                                                                                                                                        |
| `texte`        | Texte à lire : définition détaillée, étude de cas            | `titre*`, `intro`, `paragraphes*` [1-5], 150 mots au plus                                                                                                                                                                                                                          |
| `citation`     | Citation courte sur fond couleur                             | `citation*`, `auteur`                                                                                                                                                                                                                                                              |
| `avant-apres`  | Comparer deux états : avant et après une méthode             | `titre*`, `avant*` et `apres*` : `{texte, image}`                                                                                                                                                                                                                                  |
| `code`         | Formule, commande ou extrait de code commenté                | `titre*`, `intro`, `syntaxe*` (sauts de ligne `\n`), `exemple`, `resultat`, `elements` [0-4] : `{code, texte}`, `libelle`                                                                                                                                                          |
| `capture`      | Capture d'écran annotée de repères numérotés                 | `titre*`, `image`, `reperes*` [1-6] : `{titre, texte, x, y}` (position du repère en % de l'image)                                                                                                                                                                                  |
| `pas-a-pas`    | Procédure en 3 ou 4 étapes illustrées                        | `titre*`, `etapes*` [3-4] : `{texte, image}`                                                                                                                                                                                                                                       |
| `comparatif`   | Tableau à deux options, la seconde mise en avant             | `titre*`, `colonnes*` [2], `lignes*` [2-5] : `{critere, valeurs: [a, b]}`, `recommandation`                                                                                                                                                                                        |
| `raccourcis`   | Mémo de raccourcis clavier                                   | `titre`, `remarque`, `raccourcis*` [2-12] : `{touches: ["Ctrl", "C"], action}`                                                                                                                                                                                                     |
| `bon-a-savoir` | Encadrés astuce, attention, bonne pratique                   | `titre`, `encadres*` [1-3] : `{genre: "astuce" \| "attention" \| "bonne-pratique", titre, texte, libelle}` (`libelle` remplace « Astuce », « Attention » ou « Bonne pratique »)                                                                                                    |

### Pratique et vérification

| Type              | Rôle                                                                                                         | Champs                                                                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `exercice`        | Consigne d'atelier, avec un panneau durée, fichier, livrable et bonus                                        | `titre*`, `contexte`, `consignes*` [2-5], `duree`, `fichier`, `livrable`, `bonus`, `numero` (automatique)                                   |
| `exercice-etapes` | Atelier en 3 temps : préparer, réaliser, vérifier                                                            | `titre*`, `contexte`, `duree` (« 20 minutes »), `etapes*` [3] : `{titre, texte}`, `fichier`, `modalite`, `livrable`                         |
| `quiz`            | Question à 2 à 4 propositions. Le rendu produit **deux slides** : la question, puis la réponse mise en avant | `question*`, `propositions*` [2-4], `bonne*` (indice 0 à 3, ou lettre « A » à « D »), `explication` (va dans les notes de la slide réponse) |
| `a-retenir`       | Les messages clés d'un chapitre                                                                              | `messages*` [1-3], `titre`, `sousTitre` (`\n` pour deux lignes ; par défaut « Chapitre N » puis le titre du chapitre en cours)              |

### Clôture

| Type                 | Rôle                                                              | Champs                                                                                                        |
| -------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `evaluation`         | Quiz final et questionnaire de satisfaction (QR code)             | `titre`, `quiz` (texte du bouton, par exemple « Sur kahoot.it, code affiché à l'écran »), `qrCode`, `message` |
| `ressources`         | Liens pour continuer (le lien skazy.nc est mis en avant)          | `titre`, `ressources*` [1-4] : `{titre, texte, lien}`                                                         |
| `questions`          | « Avez-vous des questions ? », avec le contact du formateur       | `titre`, `photo`                                                                                              |
| `battle`             | Jeu en équipes : chaque équipe prépare des questions pour l'autre | `titre`, `accroche`, `regles` [4]                                                                             |
| `accompagnement-360` | Les pôles Skazy (com, numérique, data, formation)                 | —                                                                                                             |
| `autres-formations`  | Les 9 catégories du catalogue Skazy Formation                     | `texte`                                                                                                       |

## Animations du PPTX

Le PPTX dévoile chaque slide de contenu clic par clic, sans jamais montrer d'encart vide. Le HTML n'est pas animé.

- **Effet unique** : fondu en entrée, 0,4 s, au clic.
- **Un clic, un bloc complet** : fond, icône, titre, texte et lien apparaissent ensemble, dans le sens de lecture.
- **Toujours fixes** : titre, sous-titre (`intro`, `contexte`, `accroche`, `remarque`), surtitre en pastille, pied de page, logo et stickers.
- **Conteneurs** : une carte, un panneau ou un fond coloré apparaît au même clic que son premier contenu, jamais avant.
- **Sans animation** : `couverture`, `chapitre`, `image` (pause), `questions`, et la slide réponse d'un `quiz`, qui sert elle-même de révélation.

| Type                                                                                                                                                                 | Un clic par…                                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `objectifs`, `programme`, `texte`, `a-retenir`, `pas-a-pas`, `raccourcis`, `bon-a-savoir`, `ressources`, `accompagnement-360`, `quiz` (question), `frise`, `capture` | élément de la liste (objectif, partie, paragraphe, étape, encadré, proposition, repère…)        |
| `contenu`                                                                                                                                                            | texte, puis chaque point, puis la carte de l'image                                              |
| `notion-cle`, `chiffre-cle`                                                                                                                                          | définition ou chiffre et phrase, puis explication, chaque terme ou repère, source               |
| `graphique`                                                                                                                                                          | barres et axe, puis encadré « À retenir »                                                       |
| `comparatif`                                                                                                                                                         | ligne du tableau (l'en-tête est fixe, sans cadre global), puis la recommandation                |
| `avant-apres`                                                                                                                                                        | avant, puis après (étiquette et légende comprises)                                              |
| `code`                                                                                                                                                               | élément expliqué, puis encadré de syntaxe, exemple, résultat                                    |
| `exercice`, `exercice-etapes`                                                                                                                                        | consigne ou étape, puis chaque encart (durée, fichier, livrable), puis « Pour aller plus loin » |
| `faisons-connaissance`, `citation`, `evaluation`, `battle`, `autres-formations`                                                                                      | bloc visible : formateur, info, question du tour de table ; citation, auteur ; carte ; équipe…  |

## Longueurs conseillées

Le script prévient au-delà de ces longueurs, qui permettent de tenir dans la slide :

| Champ               | Longueur maximale conseillée     |
| ------------------- | -------------------------------- |
| Titre de slide      | 60 caractères                    |
| `texte`             | 260 caractères                   |
| `phrase`            | 70 caractères                    |
| `explication`       | 200 caractères                   |
| `definition`        | 170 caractères                   |
| `citation`          | 140 caractères                   |
| `contexte`          | 180 caractères                   |
| `question`          | 110 caractères                   |
| Point de liste      | une ligne, environ 70 caractères |
| Proposition de quiz | 40 caractères                    |

## Contrôles du script

`python scripts/rendre_support.py support.json --verifier` signale deux types de problèmes.

**Erreurs, qui bloquent le rendu** :

- type de slide inconnu ;
- champ obligatoire absent ;
- `bonne` hors des propositions.

**Avertissements** :

- listes hors des fourchettes ;
- textes trop longs ;
- support qui ne commence pas par une couverture ;
- moins d'exercices que de chapitres ;
- trop de slides sans notes formateur.
