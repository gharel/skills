# Google Docs : importer le plan à l'identique

Méthode validée le 28/10/2026 sur un plan de 2 pages A4 en Raleway, importé par un connecteur Google Drive. Chaque import s'est converti du premier coup. Le Google Docs obtenu fait 2 pages, avec le même contenu et la même mise en page, au millimètre près. Le contrôle a porté sur l'export PDF, comparé page à page avec le rendu Word.

## Ce qui rend un DOCX compatible

Le DOCX produit par `scripts/rendre_plan.py` respecte déjà ces règles. Les quatre premières viennent d'écarts constatés à l'import, puis corrigés.

- **Pas d'images flottantes.** Le bandeau, les encadrés et les cartes sont des tableaux avec un fond de cellule. Les seules images (sticker, logo) sont alignées sur le texte.
- **Pas de marge gauche dans les cellules**, mais un retrait des paragraphes. Google Docs place le bord d'un tableau au retrait du tableau moins la marge gauche de sa première cellule. Le bandeau perdait ainsi 17 mm à gauche, et les cartes glissaient de 5 à 7 mm.
- **Même marge haute et basse dans toutes les cellules d'une rangée.** Word applique à la rangée la plus grande des marges de ses cellules, alors que Google Docs applique celle de chaque cellule. Le titre du bandeau (11 mm) remontait de 4 mm à côté du sticker (15 mm).
- **Un paragraphe minuscule avant un tableau placé en tête d'en-tête.** Sinon Google Docs ajoute un paragraphe vide de taille normale, et le bandeau descend de 5 mm.
- **Jamais d'interligne « exact ».** Google Docs le convertit en pourcentage de la hauteur de ligne naturelle de la police : le texte s'étire, et le plan passe de 2 à 3 pages. L'interligne est toujours un multiple (1,2 ; 1,45…), que Word et Google Docs lisent de la même façon.
- **Capitales écrites en toutes lettres** (« MODALITÉS ET INFOS PRATIQUES »), et non par l'attribut « majuscules » : Google Docs ne le connaît pas, et Word en français retire alors les accents.
- **Police et langue par défaut** : Raleway et français. Le texte ajouté dans Google Docs garde donc la charte.
- **Fichier léger**, 25 Ko environ :
  - pas de police embarquée (Raleway existe dans Google Docs) ;
  - pas de styles inutilisés ;
  - images réduites à leur taille d'affichage.

  Un connecteur Google Drive qui reçoit le fichier en base64 peut ainsi le transmettre.

Pour un DOCX retouché dans Word ou venu d'ailleurs, applique les mêmes règles avec le script :

```bash
python scripts/docx_google_docs.py plan.docx            # crée plan.google-docs.docx
python scripts/docx_google_docs.py plan.docx --base64   # écrit aussi le base64, en lignes de 12 000 caractères
```

Le script :

- retire les polices embarquées, les parties inutiles (vignette, `stylesWithEffects`, commentaires et notes non appelés) et les styles non utilisés ;
- convertit chaque interligne exact en interligne multiple équivalent ;
- remplace la marge gauche des cellules par un retrait des paragraphes ;
- aligne les marges haute et basse des cellules sur la plus grande de leur rangée ;
- ajoute un paragraphe minuscule avant un tableau placé en tête d'en-tête, de pied ou de document ;
- réduit les images à leur taille d'affichage, à 110 dpi (200 px au moins pour les images transparentes), sur une palette réduite qui garde la transparence.

À la fin, il affiche la taille obtenue et le plus long passage répété du base64.

Toujours rouvrir le fichier produit dans Word, ou dans LibreOffice : il doit s'ouvrir et faire le même nombre de pages.

## Fausses pistes

- **Reconstruire le document avec l'API Google Docs.** Elle ne sait pas créer d'images flottantes, et elle ne lit pas un .docx.
- **Importer du HTML.** Les images flottantes et les pieds de page sont perdus.
- **Copier un .docx dans Drive** (copie de fichier, Google Drive pour ordinateur). Il reste un .docx, sans conversion. Google Drive pour ordinateur peut en plus être connecté à un autre compte.

Seul l'import d'un .docx par Google Drive, avec conversion, conserve tout.

## Importer

### À la main

Dans Google Docs, passe par Fichier > Ouvrir > Importer, puis choisis le .docx.

Autre voie : dans Google Drive, Nouveau > Importer un fichier, puis clic droit sur le fichier > Ouvrir avec > Google Docs.

### Avec un connecteur Google Drive

Crée le fichier avec :

- le type MIME `application/vnd.openxmlformats-officedocument.wordprocessingml.document` ;
- le dossier cible ;
- la conversion en Google Docs laissée active (ne la désactive pas).

Drive convertit alors le fichier en Google Docs.

Quand le connecteur demande le contenu en base64 recopié dans l'appel, la recopie est le point critique. Les deux premiers échecs de la méthode (« Invalid conversion requested ») venaient d'erreurs de recopie, pas du contenu :

- **Une recopie saute d'un passage à son jumeau** quand deux passages du base64 se ressemblent longuement. C'est le cas de deux images de même taille et de même palette : leurs en-têtes PNG sont identiques sur plus de 60 caractères. Le script donne donc à chaque image une largeur légèrement différente.
- **Le plus long passage répété** doit rester sous 40 caractères environ. Ceux du répertoire central du zip sont inévitables et sans danger.
- **Les images restent compressées** dans le zip (DEFLATE). Sans compression, les palettes produisent de longues séquences répétées.
- **Recopie bout à bout** les lignes de 12 000 caractères du fichier `.b64.txt`, sans rien ajouter entre elles. Lis d'abord toutes les lignes, puis envoie-les en un seul appel. Avec un fichier de 25 Ko (33 000 caractères) et un plus long passage répété de 35 à 38 caractères, chaque import a réussi du premier coup.
- **Pour tester le connecteur à moindre coût**, envoie d'abord un .docx minimal de quelques centaines d'octets. S'il se convertit, un refus sur le vrai fichier vient de la recopie.

## Vérifier

1. **Rendu de référence.** Exporte le .docx en PDF.
   - Avec Word sous Windows, sans ouvrir de fenêtre :

     ```powershell
     $w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0
     try { $doc = $w.Documents.Open("$PWD\plan.docx", $false, $true); "pages : " + $doc.ComputeStatistics(2); $doc.ExportAsFixedFormat("$PWD\reference.pdf", 17); $doc.Close(0) } finally { $w.Quit() }
     ```

   - Avec LibreOffice : `soffice --headless --convert-to pdf plan.docx`.
2. **Export du Google Docs.** Exporte-le en PDF : Fichier > Télécharger > PDF, ou export PDF du connecteur Drive.
3. **Comparaison.** Compare :
   - le nombre de pages ;
   - le rendu page à page, côte à côte ;
   - le texte des deux PDF. Seules différences attendues : l'ordre d'extraction des pieds de page et le glyphe des puces.

## Corriger un Google Docs déjà importé avec un interligne exact

Le plus simple : réimporter le .docx passé par `docx_google_docs.py`. Sinon, corrige l'interligne avec l'API Google Docs.

1. **Repère, dans le .docx, les paragraphes en interligne exact** : `w:spacing w:line="L" w:lineRule="exact"`, où L est en vingtièmes de point.
2. **Calcule l'interligne de chaque paragraphe du Google Docs** :

   ```
   interligne (%) = (L / 20) / (taille × 1,174) × 100
   ```

   - `taille` est la taille de police du paragraphe dans Google Docs. Quand elle n'est pas définie, c'est 10 pt, celle du style « Texte normal » (cas des paragraphes vides d'espacement).
   - 1,174 est la hauteur de ligne naturelle de Raleway rapportée à la taille de police.

3. **Apparie les paragraphes** des deux documents par leur texte. Regroupe les plages consécutives de même valeur.
4. **Envoie les requêtes en un seul lot** : `updateParagraphStyle`, `fields: lineSpacing`, avec l'identifiant de révision lu juste avant. L'API accepte les valeurs basses (6,4 %) comme les hautes (370 %).
5. **Paragraphe vide ajouté.** Google ajoute un paragraphe vide au début d'une deuxième section, avant son tableau d'en-tête. Mets-le à 1 pt et à 100 %.
6. **Réexporte en PDF**, compare, puis ajuste les derniers écarts mesurés, par exemple l'espace avant un titre.

## Limites connues

- **Interlettrage.** Google Docs n'espace pas les lettres : les petits titres en capitales (« MODALITÉS ET INFOS PRATIQUES », « EFFECTIF ») perdent leur interlettrage.
- **Images allégées.** Elles sont nettes à l'écran, un peu moins à l'impression. Pour imprimer, préfère le HTML enregistré en PDF.
- **Retours à la ligne.** Ils peuvent varier d'un mot (métriques de police).
- **Hauteur exacte de rangée.** Google Docs n'a qu'une hauteur minimale : le bandeau de la page 1 grandit d'environ 1 mm pour loger le sticker, que Word rogne à 40 mm.
