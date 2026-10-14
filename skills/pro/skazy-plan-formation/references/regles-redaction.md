# Règles de rédaction d'un plan de formation

Ces règles réunissent celles de l'ancien skill `plan-creator` et les consignes du modèle « Plan de formation » du design system Skazy Formation.

## Langue et ton

- Rédige en français, sauf si la demande est dans une autre langue. Ne change pas de langue en cours de document.
- Le ton est professionnel mais accessible : phrases courtes, verbes d'action, orienté bénéfice pour l'apprenant.
- Vouvoiement dans les textes destinés au public : description, modalités.
- Les titres et les points du programme sont écrits avec une majuscule initiale seulement.
- Pas d'emoji.
- Pour mettre un mot en gras, entoure-le de `**…**`. Le gras sert surtout au verbe de chaque objectif.

## Intitulé

- Court, clair, accrocheur, orienté formation professionnelle : 60 caractères au plus, soit deux lignes dans le bandeau.
- Évite les titres trop génériques (« Formation Excel ») ou trop longs.
- Exemples : « Excel : les bases », « Prompter efficacement avec ChatGPT », « Piloter un projet en Scrum ».

## Étiquette (facultative)

Texte de la première pastille. Par défaut, c'est le nom de la catégorie. On peut y mettre un intitulé plus précis, comme « Microsoft 365 » ou « IA générative », en 25 caractères au plus.

## Description

- Deux à quatre lignes, soit environ 2 phrases et 420 caractères au plus.
- Commence par un verbe d'action : Découvrez, Maîtrisez, Créez, Prenez en main, Automatisez…
- Ne commence **jamais** par « Cette formation », « Ce parcours » ou une tournure équivalente.
- Dis ce que l'apprenant découvre et ce que la formation lui apporte au quotidien. Cite les outils ou méthodes utilisés.
- Ne fais pas référence au document fourni dans la demande.

## Objectifs pédagogiques

- Rédige 3 à 5 objectifs, un par ligne.
- Commence chaque objectif par un verbe **observable et mesurable** en gras, choisi selon la taxonomie de Bloom :

  | Niveau de Bloom | Verbes conseillés                                     |
  | --------------- | ----------------------------------------------------- |
  | Se souvenir     | identifier, citer, repérer, nommer                    |
  | Comprendre      | expliquer, distinguer, illustrer                      |
  | Appliquer       | utiliser, appliquer, configurer, réaliser, paramétrer |
  | Analyser        | analyser, comparer, diagnostiquer, structurer         |
  | Évaluer         | évaluer, vérifier, choisir, justifier                 |
  | Créer           | créer, concevoir, produire, automatiser, rédiger      |

- Évite « comprendre », « connaître », « savoir » et « découvrir » quand un verbe plus observable existe.
- Adapte l'ambition au niveau et à la durée. Une initiation de 7 h vise surtout appliquer et utiliser ; une formation avancée vise analyser, évaluer et créer.

## Prérequis

- Par défaut : « Savoir utiliser un ordinateur et Internet ».
- Niveau Intermédiaire ou Avancé : « Avoir suivi la formation <niveau précédent> ou maîtriser <acquis équivalents> ».
- N'ajoute que les prérequis vraiment nécessaires.

## Public visé

Profils ou postes concernés, en une ligne ou deux. Par exemple : « Assistants, gestionnaires et toute personne amenée à manipuler des tableaux de chiffres ».

## Durée

- Réaliste au regard de l'étendue du sujet : 2 heures au minimum, 5 jours au maximum.
- Format conseillé : « 1 jour (7 h) », « 2 jours (14 h) », « 3 h », « 4 demi-journées (14 h) ».
- La durée doit être cohérente avec le niveau, les objectifs et le programme. Si les parties ont une durée, leur somme doit correspondre à la durée totale.

## Programme

- Prévois 2 à 8 parties. Le modèle en montre 7 pour 2 jours ; 4 à 5 conviennent pour une journée.
- Chaque partie compte 2 à 6 points, chacun en quelques mots. Un point commence par un nom ou par un verbe.
- Garde le même niveau de détail d'une partie à l'autre.
- Organise les parties de façon logique et progressive : des bases vers l'autonomie. Chaque partie sert au moins un objectif.
- Annonce les mises en pratique : « Atelier pratique : <exercice réalisé> ».
- La dernière partie est souvent un **projet final** ou une **mise en pratique** qui mobilise l'ensemble.
- Durée par partie : facultative, par exemple « 1 h 30 ». Elle est reprise par le support de formation.
- Tout doit tenir sur la page 1. Le script prévient en cas de débordement : raccourcis alors les points ou fusionne des parties.

## Modalités (page 2)

Les champs sont `methodes`, `evaluation`, `effectif`, `lieu` et `tarif`. Chaque champ absent reprend la valeur standard de Skazy Formation :

- **Effectif** : 8 personnes max.
- **Lieu** : Nouméa ou vos locaux.
- **Tarif** : sur devis.
- **Méthodes** et **évaluation** : textes du modèle.

Ne les remplace que si l'utilisateur donne d'autres informations. N'invente ni tarif, ni date, ni lieu.

## Calibrage par niveau

| Niveau        | Contenu                                                                              | Prérequis                                       | Durée type  |
| ------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------- | ----------- |
| Initiation    | Bases, vocabulaire, premières manipulations, pratique guidée                         | Minimal                                         | 1 à 2 jours |
| Intermédiaire | Usage opérationnel, méthodes structurées, bonnes pratiques, exercices plus autonomes | Niveau Initiation ou acquis équivalents         | 1 à 3 jours |
| Avancé        | Optimisation, cas complexes, stratégie, dépannage, usage en production               | Niveau Intermédiaire ou autonomie sur les bases | 1 à 5 jours |

## Exemples de demandes

- « Crée un plan de formation sur Excel débutant ». Niveau Initiation, prérequis minimal, 2 jours, de l'interface aux premières formules et graphiques.
- « Reprends ce plan Canva et rends-le plus professionnel : prise en main, modèles, réseaux sociaux, export ». Séquence plus pédagogique, titres clarifiés, objectifs précis, catégorie Graphisme & UX.
- « À partir de ces notes, crée un plan avancé sur l'IA générative pour les communicants ». Niveau Avancé, prérequis plus exigeants, programme centré sur le prompting, la production, la relecture et la gouvernance, catégorie Intelligence Artificielle.
