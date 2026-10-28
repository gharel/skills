# Skills IA

Skills IA génériques de Guillaume Harel, au format ouvert [Agent Skills](https://agentskills.io). Ils fonctionnent avec ChatGPT, Claude, Codex, Gemini, Cursor, Copilot et les autres assistants.

**Catalogue, téléchargements et installation : https://gharel.github.io/skills/**

| Catégorie                 | Skills                                                                                                                                                                                        |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pro · Skazy Formation** | `skazy-plan-formation` : plan de formation A4 (HTML, PDF, DOCX) · `skazy-support-formation` : support de formation (HTML, PDF, PPTX) · `skazy-quiz` : quiz (Kahoot, Google Forms, Quiz Skazy) |
| **UNC**                   | `notation-etudiants` : correction de TP rendus par mail (GitHub, déploiement), un onglet par étudiant (Google Sheets, XLSX) et estimation indicative de l'usage de l'IA                       |
| **Perso**                 | bientôt                                                                                                                                                                                       |

## Installer

| Assistant                           | Installation                                                                                                                            | Mise à jour                                |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Claude.ai, Claude Desktop           | Télécharger le `.zip` sur le catalogue, puis Paramètres > Capacités > Skills > Importer                                                 | Réimporter le `.zip`                       |
| ChatGPT                             | Importer le `.zip` dans les Skills, ou créer un GPT avec la version un fichier (`.md`) et l'interpréteur de code                        | Réimporter                                 |
| Claude Code                         | `/plugin marketplace add gharel/skills`, puis `/plugin install skazy-formation@gharel-skills` (ou `unc@gharel-skills`)                  | `/plugin marketplace update gharel-skills` |
| Codex, Gemini CLI, Cursor, Copilot… | `npx skills add gharel/skills -g`                                                                                                       | `npx skills update -g`                     |
| Sans Node.js                        | `irm https://gharel.github.io/skills/installer.ps1 \| iex` (Windows) ou `curl -fsSL https://gharel.github.io/skills/installer.sh \| sh` | Relancer la commande                       |
| Gemini, Mistral, Copilot…           | Instructions courtes, version un fichier (`.md`) et contenu du `.zip` en documents, exécution de code activée                           | Remplacer les fichiers                     |

## Développer

Les consignes de travail sont dans [AGENTS.md](AGENTS.md).

```bash
npm install
python -m pip install python-docx python-pptx openpyxl pillow pytest
npm run construire && npm run dev
```
