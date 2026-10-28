# Préparer le barème

## Lire le barème

Relève, dans le tableur ou le document de l'enseignant :

- la colonne des notes (souvent B) et celle des maxima (souvent C) ;
- les lignes de pénalité, par exemple « déploiement : -10 si absent » ou la ligne « Erreurs » ;
- la formule du total ;
- la cellule de commentaire, souvent fusionnée ;
- le nombre de lignes de l'onglet modèle.

## Écrire les règles avant de noter

Écris la règle de chaque ligne avant de noter le premier étudiant, puis applique-la à l'identique. Grille type, qui a bien fonctionné :

| Ligne              | Règle                                                                                                                                     |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Mail               | 1 : objet avec NOM et identifiant du contrôle, et URL ; 0,5 : seule l'URL est fournie ; 0 : rien d'exploitable                            |
| Indentation        | 1 : homogène (Prettier) ; 0,5 : mélange de 2 et 4 espaces ; 0 : désordonnée                                                               |
| Pas de console.log | 1 : aucun (un `console.error` dans un `catch` est toléré) ; 0,5 : logs de démarrage ou d'erreur ; 0 : logs de débogage dispersés          |
| Interface          | Ce qui marche en ligne (un client cassé en ligne fait fortement baisser la note), retours d'erreur, bouton demandé, sobriété              |
| Fonctionnalités    | Validation des entrées, unicité garantie (vérification de collision ou nouvel essai), persistance, redirection                            |
| Livraison GitHub   | 1 : tags complets, commits par partie et README ; 0,5 : tags ou commits incomplets ; 0 : commit unique sans tag                           |
| Déploiement        | 0 si le site est en ligne et fonctionnel ; pénalité du barème sinon                                                                       |
| Erreurs            | -0,5 à -1 par défaut fonctionnel non couvert ailleurs : secret jamais renvoyé, faille de sécurité, Swagger absent, route demandée absente |

## Cas particuliers

- **Ligne ambiguë** (par exemple « URL unique ») : retiens une interprétation, applique-la à tous et signale-la dans le compte rendu.
- **Projet libre autorisé** : garde les points et les maxima du barème. Renomme les lignes fonctionnelles dans l'onglet de l'étudiant pour qu'elles décrivent son projet (« 1.1 Récupération des données », « 1.2 Unicité des données »). Indique-le en tête de l'onglet, ou dans `libelles` pour le script.
- **Pénalités lourdes** (déploiement absent, lien de démo vers le site d'un autre étudiant) : applique la règle, mais signale-la comme point à trancher.
- **Étudiant non évaluable** (dépôt inaccessible) : laisse les notes vides et explique pourquoi.
- **Usage de l'IA** : l'estimation n'entre jamais dans le total.
