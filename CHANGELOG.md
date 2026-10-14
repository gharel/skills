# Journal des versions

Les versions sont propres à chaque skill (`metadata.version` dans son `SKILL.md`). Les entrées les plus récentes sont en haut.

## 2026-10-14

### skazy-plan-formation 1.0.0

- Première version. Elle fusionne les règles de l'ancien skill `plan-creator` et celles du modèle « Plan de formation » du design system Skazy Formation.
- Le plan est rédigé en JSON, puis rendu en HTML A4 (impression PDF) et en DOCX.
- Le DOCX a de vrais en-têtes et pieds de page Word et Google Docs : bandeau pleine largeur, page 1 différente des suivantes.

### skazy-support-formation 1.0.0

- Première version. Elle fusionne les conventions de l'ancien skill `support-creator` et les 30 mises en page du modèle « Support de formation » du design system.
- Le support est rédigé en JSON, puis rendu en HTML 1920 × 1080 (navigation, notes formateur, PDF) et en PPTX (PowerPoint, Google Slides) avec les notes du présentateur.

### skazy-quiz 1.0.0

- Première version. Elle reprend les règles de l'ancien skill `qcm-creator` et le format Skazy Quiz v1 (6 types de questions).
- Sorties : JSON Skazy Quiz et lien de partage direct, fichier d'import Kahoot (.xlsx), script Google Forms (.gs) et corrigé.

### Dépôt

- Catalogue sur GitHub Pages, atelier Pyodide, scripts d'installation, place de marché Claude Code, compatibilité `npx skills`.
