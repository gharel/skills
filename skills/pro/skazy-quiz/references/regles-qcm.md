# Règles de rédaction des questions

Ces règles reprennent celles de l'ancien skill `qcm-creator`, étendues aux six types de questions du Quiz Skazy.

## Fidélité au support

- Appuie-toi **uniquement** sur le support ou le sujet fourni.
- N'invente jamais une notion, un chiffre, un exemple, une définition ou une règle qui n'y figure pas.
- En cas d'ambiguïté ou d'information incomplète, reformule prudemment ou renonce à la question.
- Préfère une couverture fidèle à une couverture artificiellement large.
- Si le support aborde plusieurs thèmes, répartis les questions entre eux, sauf si le support lui-même en privilégie clairement un.

## Progression

Classe les questions du plus simple au plus complexe :

1. repérage de notions ou de définitions explicites ;
2. compréhension des relations entre notions ;
3. application, ou distinction entre des concepts proches ;
4. questions plus fines ou de synthèse tirées du support.

Ne commence pas par des questions difficiles si le support suit une progression simple.

## Répartition des types

| Type           | Quand l'utiliser                                                   | Part conseillée                      |
| -------------- | ------------------------------------------------------------------ | ------------------------------------ |
| `single` (QCM) | Cas général : une bonne réponse parmi 4                            | 50 à 70 %                            |
| `truefalse`    | Affirmation nette, directement vérifiable dans le support          | 25 % par défaut, ou la part demandée |
| `multiple`     | Plusieurs bonnes réponses (au moins deux)                          | 0 à 15 %                             |
| `order`        | Étapes d'une procédure, chronologie                                | 0 à 10 %                             |
| `slider`       | Valeur numérique précise donnée dans le support                    | 0 à 10 %                             |
| `text`         | Mot-clé à retrouver : nom d'une fonction, d'un outil, d'un concept | 0 à 10 %                             |

Calcule le nombre de vrai ou faux au plus près du pourcentage demandé, en gardant le total exact. Pour une sortie Kahoot ou Google Forms, privilégie `single`, `multiple` et `truefalse`. Les autres types y sont convertis ou écartés.

## Rédaction des questions

Chaque question est :

- claire, précise, sans ambiguïté ;
- adaptée au niveau réel du contenu ;
- sans piège artificiel ;
- sans indice involontaire sur la bonne réponse.

À éviter :

- les formulations inutilement compliquées ;
- les doubles négations ;
- les questions dont la réponse se devine au style.

Longueurs :

- question : 240 caractères au plus (limite de l'éditeur), viser 110 ;
- Kahoot : 120 caractères au plus, idéalement 95.

## QCM (`single`)

- Exactement **4 propositions**, avec **une seule** bonne réponse et 3 distracteurs.
- Les distracteurs sont cohérents avec le sujet, plausibles, non ambigus et non piégeux. Ils sont assez proches de la bonne réponse pour tester une vraie compréhension.
- À éviter absolument :
  - une bonne réponse toujours au même rang ;
  - une bonne réponse visiblement plus longue ou plus courte que les autres ;
  - une bonne réponse très technique au milieu de distracteurs simplistes ;
  - une bonne réponse très précise au milieu de réponses vagues ;
  - des distracteurs manifestement absurdes.
- **Répartis la position de la bonne réponse** (A, B, C, D) de façon variée et non mécanique. Le script prévient si plus de la moitié des bonnes réponses sont au même rang.
- **Distracteur humoristique** : autorisé dans environ 10 % des QCM, à quatre conditions :
  - il est clairement faux ;
  - il ne crée aucune ambiguïté ;
  - il ne rend pas la bonne réponse évidente ;
  - le contexte n'est ni formel, ni certifiant, ni sensible.

## Vrai ou faux (`truefalse`)

- Équilibre autant que possible les affirmations vraies et fausses.
- Évite les formulations triviales.
- Écris des affirmations claires, directement vérifiables dans le support.
- Une affirmation fausse doit l'être sans discussion : elle déforme une notion du support, sans jouer sur un détail.

## Autres types

- **`multiple`** : au moins deux bonnes réponses sur 4 propositions. Indique-le dans la question (« Lesquelles… », « Cochez les… »).
- **`order`** : 3 ou 4 éléments courts, donnés **dans le bon ordre** dans le JSON. L'application les mélange elle-même.
- **`slider`** : la valeur exacte figure dans le support. Choisis des bornes plausibles et une marge (`tolerance`) adaptée, 0 pour une valeur exacte.
- **`text`** : la réponse tient en un ou deux mots. Liste les variantes acceptées : synonyme, sigle, avec ou sans article. La casse, les accents et la ponctuation sont ignorés par l'application.

## Explications

Pour chaque question, une explication courte, de 300 caractères au plus, qui dit pourquoi la bonne réponse est juste. Elle s'appuie sur le support et peut rappeler l'astuce ou la règle à retenir.

## Temps et points

| Type        | Temps par défaut |
| ----------- | ---------------- |
| `single`    | 20 s             |
| `multiple`  | 30 s             |
| `truefalse` | 15 s             |
| `text`      | 30 s             |
| `slider`    | 30 s             |
| `order`     | 40 s             |

- Valeurs de temps possibles : 5, 10, 15, 20, 30, 45, 60, 90 ou 120 s.
- Points : 1 (standard), 2 (question importante, double) ou 0 (question d'échauffement sans points).

## Contrôle avant de livrer

- [ ] Les notions importantes du support sont couvertes, sans qu'un sous-thème écrase les autres.
- [ ] La difficulté est progressive.
- [ ] Chaque bonne réponse se vérifie dans le support.
- [ ] Les bonnes réponses des QCM sont bien réparties entre A, B, C et D.
- [ ] Les vrai ou faux sont équilibrés.
- [ ] Chaque question a une explication.

## Cas limites

- **Support trop pauvre** : dis-le et propose de réduire le nombre de questions, de fournir un support plus complet ou de te limiter aux notions présentes.
- **Support très long** : identifie d'abord les axes majeurs, puis répartis les questions entre eux.
- **Demande contradictoire** (par exemple 100 % de vrai ou faux pour une certification) : applique la solution la plus sûre sur le plan pédagogique et explique-la brièvement.
