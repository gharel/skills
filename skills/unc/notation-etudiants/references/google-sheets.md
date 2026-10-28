# Remplir le tableur Google Sheets de l'enseignant

À suivre quand tu as accès en écriture au Google Sheets du barème. Sinon, utilise `notation.json` et le script : voir [format-notation.md](format-notation.md).

## 1. Lire l'onglet modèle

Lis l'onglet modèle avec ses valeurs saisies (formules comprises) et ses cellules fusionnées. Relève :

- la colonne des notes et celle des maxima ;
- les lignes de pénalité ;
- la formule du total ;
- la cellule de commentaire fusionnée ;
- le nombre de lignes, qui fixe la plage à écrire (souvent `A1:D18`).

## 2. Créer les onglets, en une seule mise à jour groupée

1. **Dupliquer.** Duplique l'onglet modèle pour chaque étudiant (requête `duplicateSheet`) :
   - dans l'ordre alphabétique ;
   - avec des identifiants d'onglet choisis (101, 102…) ;
   - nommés « NOM Prénom ».
2. **Agrandir.** Pour chaque onglet :
   - ajoute une colonne, la colonne D « Justification » (requête `appendDimension`) ;
   - ajoute 3 lignes, pour le bloc IA sous le commentaire.

## 3. Écrire les notes, en une seule écriture par onglet

Écris la plage `'NOM Prénom'!A1:D18` (à adapter si le modèle a une autre taille) :

- **cellules à conserver** : valeur nulle ;
- **colonne B** : la note ;
- **colonne D** : la justification factuelle, c'est-à-dire ce qui a été observé ou testé, avec URL et date de test ;
- **cellule fusionnée** : le commentaire de synthèse ;
- **ligne 17** :
  - A : « Probabilité d'usage de l'IA (indicatif, hors note) » ;
  - B : la fourchette en texte, par exemple « 50 à 80 % », écrite telle quelle pour rester du texte ;
  - D : les indices et les indices contraires ;
- **ligne 18** :
  - A : « Part estimée du travail produite avec l'IA » ;
  - B : la fourchette, par exemple « 30 à 50 % » ;
  - D : les parties concernées et l'usage déclaré éventuel.

Remets la pénalité de déploiement à 0 quand le site fonctionne.

Pour un étudiant non évaluable, laisse vides les notes (`""`) et le bloc IA, et explique pourquoi dans le commentaire.

## 4. Mettre en forme, en une seule mise à jour groupée

- **Colonne D** : environ 560 px de large.
- **Retour à la ligne et alignement en haut** : pour D, le commentaire et les lignes 17-18.
- **Gras** : en-tête de D et étiquettes A17:A18.
- **Fond gris clair** sur A17:D18 : il distingue le bloc indicatif de la note.

## 5. Vérifier

- Relis toutes les plages B2:C13 en valeurs affichées.
- Contrôle chaque total contre le calcul attendu.
- Vérifie qu'aucune cellule n'affiche d'erreur.
- Vérifie que B17:B18 sont restés du texte, hors du total.

Le lien du tableur ne change pas : donne-le dans le compte rendu.
