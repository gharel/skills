import js from '@eslint/js';
import globals from 'globals';

export default [
  {
    ignores: [
      'node_modules/',
      '.venv/',
      '_site/',
      'sorties/',
      'playwright-report/',
      'test-results/',
      // Clone de design-skazy par la CI.
      'design-skazy/',
      'skills/**/assets/',
    ],
  },
  js.configs.recommended,
  {
    // Les scripts Playwright passent des fonctions exécutées dans la page (page.evaluate).
    files: ['outils/**/*.mjs', 'tests/**/*.js', 'tests/**/*.mjs', '*.config.js'],
    languageOptions: { globals: { ...globals.node, ...globals.browser } },
  },
  {
    files: ['site/**/*.js'],
    languageOptions: { globals: globals.browser },
  },
];
