/**
 * node outils/ouvrir-lien.mjs <url> sortie.png : ouvre une page (lien de partage du Quiz, site publié)
 * et en affiche le texte, pour vérifier un rendu de bout en bout.
 */
import { chromium } from '@playwright/test';

const [url, sortie] = process.argv.slice(2);
const navigateur = await chromium.launch();
const page = await navigateur.newPage({ viewport: { width: 1200, height: 900 } });
page.on('pageerror', (e) => console.error('Erreur de page :', e.message));
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);
console.log((await page.evaluate(() => document.body.innerText)).slice(0, 1200));
if (sortie) await page.screenshot({ path: sortie });
await navigateur.close();
