# Construire le support à partir du plan

Ces conventions reprennent celles de l'ancien skill `support-creator`, adaptées au modèle « Support de formation » du design system Skazy Formation. Elles servent l'apprentissage : on retient mieux ce qui est lisible, rythmé et mis en pratique.

## Correspondance entre le plan et le support

| Élément du plan                      | Dans le support                                                                           |
| ------------------------------------ | ----------------------------------------------------------------------------------------- |
| Intitulé, catégorie, niveau, durée   | Bloc `formation` (couverture, pied de chaque slide)                                       |
| Objectifs                            | Slide `objectifs`, mêmes verbes en gras                                                   |
| Parties du programme et leurs durées | Slide `programme`, puis un `chapitre` par partie (même titre, même durée, mêmes points)   |
| Points d'une partie                  | Slides de contenu du chapitre, au moins une par point important                           |
| « Atelier pratique : … »             | Slide `exercice` ou `exercice-etapes` du chapitre                                         |
| « Projet final »                     | `exercice` détaillé, éventuellement suivi d'une slide `image` (« Votre projet est prêt ») |
| Modalités d'évaluation               | Slide `evaluation` (quiz final, satisfaction)                                             |

## Déroulé type d'une journée (7 h)

1. **Ouverture** : `couverture`, `faisons-connaissance`, `objectifs`, `programme`.
2. **Chaque chapitre**, pour chaque partie du plan :
   - `chapitre` ;
   - 3 à 8 slides de contenu aux mises en page variées ;
   - au moins un `exercice` ou `exercice-etapes`, placé après les notions qu'il mobilise ;
   - 0 à 3 `quiz` (questions rapides), facultatifs ;
   - `a-retenir`, 3 messages au plus.
3. **Clôture** : `evaluation`, `ressources`, `questions`, puis au choix `battle`, `accompagnement-360` et `autres-formations` (les deux dernières pour les sessions inter-entreprises).

Repère de volume : 25 à 45 slides par journée, soit 8 à 12 minutes par slide de contenu en comptant les exercices.

## Une idée par slide

- Une slide porte **une seule idée**. Au-delà d'environ 4 éléments, découpe en deux slides : mieux vaut deux slides claires qu'une slide tassée.
- Les points de liste tiennent sur une ligne : mot-clé en gras, deux-points, explication courte.
- Chaque slide a un élément visuel : capture, chiffre, icône, tableau, frise. Une slide « titre et puces » répétée s'oublie aussitôt.

## Choisir la mise en page

| Le contenu est…                                      | Mise en page                                                  |
| ---------------------------------------------------- | ------------------------------------------------------------- |
| Une notion à expliquer, avec un exemple              | `contenu` (capture ou schéma à droite)                        |
| Un terme à définir, à faire répéter                  | `notion-cle`                                                  |
| Un chiffre marquant                                  | `chiffre-cle`                                                 |
| Une évolution, une comparaison chiffrée              | `graphique`                                                   |
| Une suite d'étapes dans un outil                     | `pas-a-pas` (3-4 captures) ou `capture` (une capture annotée) |
| Deux options à comparer                              | `comparatif` ou `avant-apres`                                 |
| Une formule, une commande, du code                   | `code`                                                        |
| Des raccourcis clavier                               | `raccourcis`                                                  |
| Une astuce, une erreur fréquente, une bonne pratique | `bon-a-savoir`                                                |
| Un historique, des versions                          | `frise`                                                       |
| Une définition longue, une étude de cas              | `texte`                                                       |
| Une pause, une phrase forte                          | `citation` ou `image`                                         |

Alterne les mises en page : deux slides consécutives n'utilisent jamais la même, sauf pour les quiz.

## Exercices

- **Au moins un exercice par chapitre**, au plus un par sous-partie.
- Mélange les manipulations concrètes (tester, configurer, produire) et les mises en situation (cas client, jeu de rôle, analyse en binôme).
- Un exercice comprend :
  - un contexte en une ou deux phrases (la situation, ce qu'on attend) ;
  - 2 à 5 consignes numérotées qui commencent par un verbe d'action, la dernière servant à vérifier le résultat ;
  - une durée réaliste ;
  - le fichier fourni s'il y en a un ;
  - le livrable attendu ;
  - un bonus pour les plus rapides.
- `exercice-etapes` convient aux ateliers longs, découpés en préparer, réaliser, vérifier.

## Quiz dans le support

- Questions rapides de fin de chapitre : 2 à 4 propositions courtes, une seule bonne réponse, des distracteurs plausibles.
- La bonne réponse ne doit pas toujours être à la même place.
- L'`explication` s'affiche dans les notes de la slide réponse.
- Le quiz final complet se fait avec le skill `skazy-quiz` (Kahoot, Google Forms ou Quiz Skazy) : la slide `evaluation` y renvoie.

## Notes formateur

Renseigne `notes` sur chaque slide de contenu, d'exercice et de quiz. Les notes rendent le support animable par un autre formateur. Elles contiennent, en 2 à 5 phrases :

- ce qu'il faut dire ou montrer (démonstration en direct, exemple à donner) ;
- une question à poser au groupe ;
- la durée indicative ;
- la transition vers la slide suivante.

## Liens et ressources

- Dès qu'un sujet appelle un outil (site d'entraînement, documentation, gabarit), mets le lien dans la slide ou dans les notes.
- Regroupe ces liens sur la slide `ressources`, avec 4 liens au plus.
- Préfère les ressources stables, officielles et en français.
- La dernière ressource renvoie vers la suite chez Skazy (formation.skazy.nc, niveau supérieur).

## Captures d'écran

Le rendu met un emplacement « Capture d'écran… » quand `image` est vide. Liste ces emplacements dans ta réponse pour que le formateur les remplisse. Ne mets jamais une image inventée ou sans rapport.

## À éviter

- Garder des slides denses pour ne pas perdre de contenu : on perd l'audience.
- Utiliser un ton anxiogène ou trop technique pour le niveau visé.
- Enchaîner la théorie sans mise en pratique : elle est oubliée en quelques jours.
- Oublier les notes formateur : le support n'est alors animable que par son auteur.
- Inventer des chiffres ou des sources.
