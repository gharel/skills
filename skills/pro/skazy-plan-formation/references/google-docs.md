# Google Docs : importer le plan à l'identique

Méthode validée le 28/10/2026 sur des plans de 2 pages A4 en Raleway (design system Skazy).

- **Modèle de référence** : le Google Docs « Plan de formation - L'IA pour vos reportings », importé d'un .docx à fonds ancrés. `scripts/plan_docx.py` en reprend la structure. Le DOCX qu'il produit, rendu par Word, est à 0,2 mm près de ce Google Docs pour toutes les lignes de texte et tous les fonds (`exemples/plan-ia-reportings.json`, comparé par `scripts/comparer_rendus.py`).
- **Imports par un connecteur Google Drive** : tous les DOCX de 30 600 caractères de base64 au plus se sont convertis du premier coup. Le Google Docs obtenu était à 0,2 mm près du rendu de Word, sur l'export PDF comparé ligne à ligne.

## Principe

1. **Importer le .docx, ne pas reconstruire le document.** Seul l'import d'un .docx par Google Drive, avec conversion, conserve les fonds ancrés derrière le texte, les images et les pieds de page. L'API Google Docs ne crée pas d'images flottantes et ne lit pas un .docx. Un import HTML perd les fonds et les pieds de page. Une copie de fichier (`copy_file`, Google Drive pour ordinateur) reste un .docx, sans conversion.
2. **Partir d'un DOCX compatible.** Celui de `scripts/rendre_plan.py` l'est déjà (règles ci-dessous). Un DOCX retouché dans Word ou venu d'ailleurs passe par `scripts/docx_google_docs.py` (étape 1).
3. **Un Google Docs déjà importé avec un interligne exact** se corrige par l'API Google Docs (étape 3).
4. **Vérifier** : export PDF, nombre de pages, comparaison ligne à ligne et image par image avec le rendu de Word (`scripts/comparer_rendus.py`).

## Ce qui rend un DOCX compatible

`plan_docx.py` respecte ces règles. Chacune vient d'un écart mesuré à l'import, puis corrigé, ou du modèle de référence.

| Règle                                                                                                                                                                                                                                                                                                                                 | Écart sans elle                                                                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Aplats à coins arrondis (bandeau et ses pastilles, sticker, encadré, cartes, encart, boîte de contact) : images PNG ancrées derrière le texte, sans habillage. Bandeau et sticker sont ancrés à la page. Les autres fonds sont portés par un paragraphe vide de hauteur connue, juste avant leur tableau, et décalés de cette hauteur | un fond de cellule n'a pas de coins arrondis ; une image en ligne pousse le texte                                                                                                           |
| Jamais d'interligne « exact », toujours un multiple (0,98 ; 1,2 ; 1,32…)                                                                                                                                                                                                                                                              | le texte s'étire, 3 pages au lieu de 2                                                                                                                                                      |
| Aucune marge de cellule : retraits et espaces avant ou après de paragraphe à la place                                                                                                                                                                                                                                                 | Google place le bord d'un tableau au retrait moins la marge gauche de sa première cellule (17 mm perdus). Word compte la hauteur minimale d'une rangée hors marges, Google marges comprises |
| Hauteur de rangée minimale, jamais exacte                                                                                                                                                                                                                                                                                             | Google Docs n'a pas de hauteur exacte                                                                                                                                                       |
| Un paragraphe, même minuscule, avant tout tableau placé en tête de section, d'en-tête ou de pied                                                                                                                                                                                                                                      | Google ajoute un paragraphe vide de taille normale : 5 mm de décalage                                                                                                                       |
| Image en ligne (logos) dans une rangée de hauteur minimale fixée, centrée verticalement                                                                                                                                                                                                                                               | Google ajoute environ 4 pt autour de l'image : la rangée grandit et le pied remonte de 1,3 mm                                                                                               |
| Paragraphe vide : marque de paragraphe à taille fixée (10 pt, ou 1 pt) et interligne multiple calculé (hauteur ÷ 11,74 pt pour 10 pt)                                                                                                                                                                                                 | hauteur différente dans Word et dans Google Docs                                                                                                                                            |
| Puces « • » en Arial, à la taille du texte                                                                                                                                                                                                                                                                                            | une puce Symbol, plus haute, étire chaque ligne de liste dans Word                                                                                                                          |
| Capitales écrites en toutes lettres, sans interlettrage                                                                                                                                                                                                                                                                               | Google Docs n'a ni l'attribut « majuscules » (Word en français retire alors les accents) ni l'espacement des lettres                                                                        |
| Raleway ExtraBold appelée par son nom de police (numéros des parties, intitulés des cartes)                                                                                                                                                                                                                                           | Google Docs la lit comme Raleway, graisse 800, la même que le modèle                                                                                                                        |
| Police et langue par défaut : Raleway et français                                                                                                                                                                                                                                                                                     | le texte ajouté dans Google Docs sort de la charte                                                                                                                                          |
| Un seul `w:tblBorders` et un seul `w:tblLayout` par tableau                                                                                                                                                                                                                                                                           | XML invalide, lu au hasard                                                                                                                                                                  |

Les mesures de la mise en page (en points), les fonds dessinés et les interlignes sont dans `scripts/plan_docx.py`. Les espacements reprennent ceux du Google Docs de référence. Word lit les interlignes multiples comme Google Docs.

## Étape 0 : rendu de référence

Exporte le .docx en PDF.

- Avec Word sous Windows, sans ouvrir de fenêtre :

  ```powershell
  $w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0
  try { $doc = $w.Documents.Open("$PWD\plan.docx", $false, $true); "pages : " + $doc.ComputeStatistics(2); $doc.ExportAsFixedFormat("$PWD\reference.pdf", 17); $doc.Close(0) } finally { $w.Quit() }
  ```

- Avec LibreOffice : `soffice --headless --convert-to pdf plan.docx`.

## Étape 1 : alléger le .docx

Le DOCX de `rendre_plan.py` privilégie la qualité : logo et sticker nets à l'impression, en couleurs vraies (65 Ko pour le plan de référence). Un connecteur Google Drive, lui, reçoit le fichier en base64 recopié dans l'appel et doit rester sous 22 Ko (30 000 caractères) : `--compact` y ramène le DOCX (29 900 caractères pour le plan de référence), au prix d'un logo et d'un sticker moins nets. Un .docx de Word avec ses polices embarquées en fait 10 fois plus.

```bash
python scripts/docx_google_docs.py plan.docx --compact --base64   # pour un connecteur : plan.google-docs.docx et son base64 (.b64.txt)
```

Le script, que `rendre_plan.py` applique à chaque DOCX :

- retire les polices embarquées (Raleway existe dans Google Docs), la table des polices, la vignette, `stylesWithEffects`, `webSettings`, `docProps/app`, `core` et `custom`, les commentaires et notes non appelés, les réglages d'affichage (zoom, langue du thème, séparateurs), et nettoie `[Content_Types].xml` et les `.rels` ;
- retire les styles, numérotations, polices et thème que rien n'utilise, et les propriétés redondantes (`szCs`, `bCs`, `iCs`, police identique à celle par défaut) ;
- convertit chaque interligne exact en interligne multiple équivalent ;
- remplace la marge gauche des cellules par un retrait, aligne les marges haute et basse de chaque rangée, et ajoute un paragraphe minuscule avant un tableau en tête d'en-tête, de pied ou de document ;
- réduit les images à leur taille d'affichage : fonds à 110 dpi (90 pour `rendre_plan.py`), logo et sticker à 220 dpi, avec des noms courts (`0.png`, `1.png`…). Le logo passe sur la palette de ses couleurs franches, sans perte ; le sticker et les photos gardent leurs couleurs vraies (une palette crénelle le contour du sticker et réduit une photo à quelques aplats). Avec `--compact`, tout est à 80 dpi et en palette.

Il affiche la taille obtenue et le plus long passage répété du base64. Rouvre toujours le fichier produit dans Word (commande de l'étape 0) : il doit s'ouvrir et faire le même nombre de pages.

## Étape 2 : fiabiliser la recopie du base64

C'est le point critique. Chaque refus du connecteur (« Invalid conversion requested ») venait d'une erreur de recopie, jamais du contenu. Elles ont toutes été trouvées en écrivant la recopie dans un fichier local, comparé ensuite à l'original :

- **saut vers un passage jumeau** : deux images de même taille et de même palette ont des en-têtes PNG identiques sur plus de 60 caractères ;
- **retour à une version précédente** : quand une version antérieure du même fichier a déjà été recopiée dans la conversation, la recopie y revient d'elle-même, sur des milliers de caractères.

Règles :

- **Réduire les passages répétés.** Le script donne à chaque image une largeur un peu différente (+0 à +7 px) et garde les images compressées dans le zip. Le plus long passage répété doit rester sous 40 caractères environ (ceux du répertoire central du zip sont sans danger).
- **Afficher le base64 juste avant de le recopier**, en deux moitiés (`head -c 15300` puis `tail -c +15301` sur une seule ligne), ou ligne par ligne dans le `.b64.txt` (lignes de 12 000 caractères).
- **Répéter avant d'envoyer.** Écris la recopie dans un fichier, puis :

  ```bash
  python scripts/docx_google_docs.py --verifier-recopie plan.google-docs.docx.b64.txt recopie.b64
  ```

  Le script donne la position et le contenu de chaque écart. N'envoie que la recopie déclarée identique, telle quelle.

- **Recopier dans un contexte neuf.** Après plusieurs versions du même fichier, confie la recopie et l'envoi à un sous-agent ou à une nouvelle conversation, qui n'a vu que la dernière.
- **Rester sous 30 000 caractères environ.** Au-delà, l'appel au connecteur, qui recopie tout le base64 d'un bloc, dérive en cours de route même quand chaque tranche a été vérifiée, et un filtre peut l'interrompre (deux essais à 34 000 et 42 000 caractères). Passe le DOCX par `--compact`. Ce n'est pas une garantie : le 28/10/2026, un filtre a encore coupé l'envoi de 29 400 caractères, pourtant vérifiés identiques. Ne relance pas un envoi coupé par un filtre : importe le DOCX à la main (ci-dessous), puis vérifie-le avec l'export PDF du connecteur, qui marche quelle que soit la taille.
- **Tester le connecteur à moindre coût.** Un .docx minimal de quelques centaines d'octets suffit : s'il se convertit, un refus sur le vrai fichier vient de la recopie.

Puis importe :

- **avec un connecteur Google Drive** : création de fichier avec le type MIME `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, le dossier cible et la conversion en Google Docs laissée active ;
- **à la main** : dans Google Docs, Fichier > Ouvrir > Importer ; ou dans Google Drive, Nouveau > Importer un fichier, puis clic droit > Ouvrir avec > Google Docs.

## Étape 3 : corriger l'interligne d'un Google Docs déjà importé

Le plus simple est de réimporter le .docx passé par `docx_google_docs.py`. Sinon, pour un Google Docs importé d'un .docx en interligne exact, et peut-être retouché depuis :

Google convertit un interligne exact de L twips en L/240 × 100 %, puis applique ce pourcentage à la hauteur de ligne naturelle de la police (Raleway : 1,174 × la taille). Les grandes polices et les paragraphes d'espacement grossissent : 3 pages au lieu de 2. L'interligne juste est :

```
interligne (%) = (L / 20) / (taille × 1,174) × 100
```

`taille` est la taille de police du paragraphe dans Google Docs, ou 10 pt (style « Texte normal ») quand elle n'est pas définie, comme pour les paragraphes vides d'espacement.

1. Lis le Google Docs (`documents.get`, ou l'outil de lecture du connecteur) et enregistre le résultat dans `doc.json`.
2. Calcule les requêtes :

   ```bash
   python scripts/interligne_google_docs.py plan.docx doc.json --sortie requetes.json
   ```

   Le script apparie les paragraphes des deux documents par leur texte, regroupe les plages consécutives de même valeur, et ramène à 1 pt et 100 % le paragraphe vide que Google ajoute au début d'une section, avant son tableau d'en-tête. Il signale les paragraphes qu'il n'a pas pu apparier.

3. Envoie le lot (`documents.batchUpdate`, ou l'outil de mise à jour du connecteur) avec `writeControl.requiredRevisionId` égal au `revisionId` de la lecture. L'API accepte les valeurs basses (6,4 %) comme les hautes (370 %).
4. Réexporte en PDF, compare (ci-dessous), puis ajuste les derniers écarts mesurés, par exemple l'espace avant un titre.

## Vérification

1. Exporte le Google Docs en PDF : Fichier > Télécharger > PDF, ou export PDF du connecteur (`exportMimeType: application/pdf`).
2. Compare avec le rendu de référence :

   ```bash
   python scripts/comparer_rendus.py reference.pdf google-docs.pdf --sortie comparaison
   ```

   Le second fichier peut aussi être le JSON enregistré par l'export du connecteur. Le script demande PyMuPDF (`pip install pymupdf`), facultatif pour le reste du skill. Il :

   - compare le nombre de pages ;
   - apparie les lignes de texte et donne le décalage de chacune, en mm, et l'écart de taille de police ;
   - signale les lignes présentes d'un seul côté (attendu : l'ordre d'extraction des pieds de page) ;
   - écrit `cmp-N.png` (Word à gauche, Google Docs à droite) et `diff-N.png` (en rouge, ce qui diffère) ;
   - sort en erreur au-delà de 0,5 mm (`--tolerance`), `--tout` affiche toutes les lignes.

3. Regarde les images : les écarts de position des images, des fonds et des filets ne se lisent pas dans le texte.

## Limites connues

- **Interlettrage.** Google Docs n'espace pas les lettres : le modèle n'en met donc nulle part, pas même dans les petits titres en capitales.
- **Images en ligne.** Google les décale d'environ 0,6 mm vers la droite : les puces carrées des intertitres de la page 2, et le texte qui les suit, sont 1,1 mm plus à droite que dans Word.
- **Images allégées.** Elles sont nettes à l'écran, un peu moins à l'impression. Pour imprimer, préfère le HTML enregistré en PDF.
- **Retours à la ligne.** Ils peuvent varier d'un mot : Word mesure Raleway un peu plus large que Google Docs. Sur le modèle de référence, deux paragraphes de la page 2 se coupent un mot plus tôt dans Word.
- **Hauteur exacte de rangée.** Google Docs n'a qu'une hauteur minimale : une rangée trop pleine grandit au lieu d'être rognée.
- **Transparence.** Une image aplatie sur fond blanc ne convient que si elle repose sur du blanc. Celles qui chevauchent un aplat de couleur, comme le sticker sur le bandeau, gardent leur transparence.

## Scripts

| Script                              | Rôle                                                                      | Correspond, dans la méthode d'origine, à |
| ----------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------- |
| `scripts/docx_google_docs.py`       | allège le .docx et le rend compatible ; `--base64` ; `--verifier-recopie` | `mini.py`, `rep.py`                      |
| `scripts/interligne_google_docs.py` | requêtes de correction de l'interligne d'un Google Docs déjà importé      | `docx_pars.py`, `fix_ls.py`              |
| `scripts/comparer_rendus.py`        | comparaison ligne à ligne et images côte à côte                           | `render.py`                              |

Python 3 avec `python-docx` et `pillow`, plus PyMuPDF pour la comparaison. Place les fichiers à traiter (le .docx, les exports) dans un dossier de travail, hors du dossier du skill.
