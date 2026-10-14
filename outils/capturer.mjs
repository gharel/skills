/**
 * node outils/capturer.mjs fichier.html|url sortie.png [largeur] [hauteur] [échelle]   (THEME=dark pour le thème sombre)
 * Capture pleine page d'un rendu HTML (contrôle visuel des plans et des supports).
 */
import { chromium } from '@playwright/test';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const [fichier, sortie, largeur = '900', hauteur = '1200', echelle = '1'] = process.argv.slice(2);
if (!fichier || !sortie) {
  console.error(
    'Usage : node outils/capturer.mjs fichier.html sortie.png [largeur] [hauteur] [échelle]',
  );
  process.exit(1);
}
const navigateur = await chromium.launch();
const page = await navigateur.newPage({
  viewport: { width: Number(largeur), height: Number(hauteur) },
  deviceScaleFactor: Number(echelle),
});
const cible = /^https?:/.test(fichier) ? fichier : pathToFileURL(resolve(fichier)).href;
if (process.env.THEME) await page.emulateMedia({ colorScheme: process.env.THEME });
await page.goto(cible, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: sortie, fullPage: true });
await navigateur.close();
console.log(sortie);
