# Estimer l'usage de l'IA (indicatif, hors note)

Objectif : donner à l'enseignant, pour chaque étudiant, deux estimations argumentées.

- **Probabilité d'usage de l'IA** : à quel point il est probable qu'une IA ait produit tout ou partie du rendu.
- **Part estimée** : la part du travail qui semble produite, ou fortement assistée, par une IA, et sur quelles parties (code serveur, client, CSS, commentaires, README, REPONSES.md, commandes git).

## Règles impératives

- **Pas de preuve.** Aucun outil ne prouve l'usage d'une IA. Ces chiffres sont des estimations tirées d'indices : ils ne modifient pas la note et ne fondent aucune sanction.
- **Toujours une fourchette.** Écris « 50 à 70 % », jamais une valeur précise. Jamais 100 %, sauf usage déclaré couvrant tout le rendu.
- **Pas de détecteur en ligne.** Les « détecteurs d'IA » sont peu fiables, et envoyer le travail des étudiants à un service tiers pose un problème de confidentialité.
- **L'usage déclaré est un fait.** Un usage déclaré par l'étudiant, dans le mail ou le README, s'indique avec son périmètre exact (« commentaires et commandes git selon l'étudiant »). La déclaration ne doit pas pénaliser l'étudiant face à ceux qui ne déclarent rien : applique à tous la même grille d'indices.
- **Le doute se lève à l'oral.** La seule vérification fiable est un échange avec l'étudiant : explication orale de son code, modification en direct. Propose-le dans le compte rendu quand la probabilité est élevée.

## Relever les indices

`python scripts/indices_depot.py <depot>` donne les mesures automatiques :

- taille et rythme des commits ;
- émojis et symboles décoratifs dans le code et les messages de commit ;
- densité de commentaires et de JSDoc par fichier ;
- messages de commit en anglais ;
- structure du README.

Sans Python, relève-les à la main dans l'historique GitHub et dans les fichiers.

Lis ensuite le code, le README et l'historique. Note chaque indice observé avec son fichier :

| Indice                                                                                                                                                                               | Force                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| Usage déclaré par l'étudiant                                                                                                                                                         | Fait établi pour le périmètre déclaré                        |
| Rupture nette de niveau ou de style avec ses rendus précédents (TP antérieurs du même étudiant) : nommage, gestion d'erreurs, structure, langue des commentaires                     | Fort                                                         |
| Gros volume livré d'un coup (un seul commit « projet complet », ou plusieurs centaines de lignes en quelques minutes) sans étapes intermédiaires ni corrections                      | Fort                                                         |
| Commentaires de tutoriel uniformes partout (JSDoc sur chaque fonction, en-tête descriptif dans chaque fichier, étapes numérotées « 1. 2. 3. », remarques adressées au lecteur)       | Moyen                                                        |
| Émojis ou symboles décoratifs dans le code, les commentaires ou les messages de commit                                                                                               | Moyen                                                        |
| Notions avancées non vues en cours et non nécessaires (comparaison en temps constant, repli `execCommand`, `asyncHandler`, échappement HTML systématique) sans trace d'apprentissage | Moyen                                                        |
| README très structuré et générique (cases à cocher, arborescence commentée, ton marketing), en décalage avec le style des mails de l'étudiant                                        | Moyen                                                        |
| Code très défensif ou exhaustif par rapport à la demande, mais erreurs basiques ailleurs (incohérence de niveau dans un même projet)                                                 | Moyen                                                        |
| Messages de commit en anglais conventionnel (« Refine content and structure in… ») alors que l'étudiant écrit en français                                                            | Faible                                                       |
| Mélange de styles d'un fichier à l'autre (guillemets, indentation, langue) qui suggère des sources différentes                                                                       | Faible (peut aussi venir de copies de cours ou de camarades) |

**Indices contraires**, qui baissent l'estimation :

- historique progressif, avec essais et corrections ;
- erreurs typiques de débutant, cohérentes partout ;
- commentaires personnels et maladroits ;
- style identique aux TP précédents ;
- code proche du code fourni en cours.

Le code de départ fourni par l'enseignant (gabarit, starter) ne compte pas : compare avec lui avant d'attribuer un fichier à l'étudiant ou à une IA.

## Comparer avec les rendus précédents

Quand les rendus antérieurs du même étudiant sont disponibles (liens des TP précédents trouvés dans les mails), clone ces dépôts et compare :

- l'indentation et le nommage ;
- la gestion des erreurs ;
- la densité et la langue des commentaires ;
- la structure des fichiers ;
- la qualité du README.

C'est l'indice le plus parlant : cite-le explicitement.

## Calculer les estimations

1. **Probabilité** : pars des indices observés et choisis une fourchette.

   | Fourchette | Situation                                                                                                                       |
   | ---------- | ------------------------------------------------------------------------------------------------------------------------------- |
   | 0 à 20 %   | Aucun indice, ou un indice faible isolé ; historique progressif                                                                 |
   | 20 à 50 %  | Quelques indices faibles ou moyens, sans convergence nette                                                                      |
   | 50 à 80 %  | Plusieurs indices moyens convergents, ou un indice fort                                                                         |
   | 80 à 95 %  | Plusieurs indices forts convergents (rupture nette avec le TP précédent et livraison en un bloc, par exemple), ou usage déclaré |

2. **Part estimée** :
   - classe chaque fichier ou partie du rendu (serveur, routeurs, base, client JS, HTML et CSS, README, REPONSES.md) en « indices forts », « indices moyens » ou « pas d'indice » ;
   - pondère par le nombre de lignes ;
   - déduis-en une fourchette arrondie à la dizaine, par exemple « 30 à 50 % du code, surtout le client et le README » ;
   - distingue l'aide à la compréhension (commentaires, explications) de la production du code lui-même.
3. **Justification** : rédige-la courte. Cite les indices précis (fichier, commit, extrait de moins de quinze mots) et les indices contraires.
