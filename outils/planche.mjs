/**
 * node outils/planche.mjs support.html sortie.png [première] [dernière] [colonnes]
 * Planche-contact d'un support HTML (slides première à dernière, numérotées à partir de 1).
 */
import { chromium } from '@playwright/test';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const [fichier, sortie, premiere = '1', derniere = '12', colonnes = '3'] = process.argv.slice(2);
const navigateur = await chromium.launch();
const largeur = Number(colonnes) * 1968 + 48;
const page = await navigateur.newPage({
  viewport: { width: largeur, height: 1200 },
  deviceScaleFactor: 1800 / largeur,
});
await page.goto(pathToFileURL(resolve(fichier)).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.evaluate(
  ([a, b, n]) => {
    document.querySelectorAll('.barre,.notes').forEach((e) => e.remove());
    const style = document.createElement('style');
    style.textContent = `html,body{height:auto;background:#777}.scene{position:static;display:block}
      .deck{transform:none!important;width:auto;height:auto;display:grid;grid-template-columns:repeat(${n},1920px);gap:48px;padding:48px}
      .slide{position:relative;visibility:visible}.slide.masquee{display:none}`;
    document.head.append(style);
    document.querySelectorAll('.slide').forEach((s, k) => {
      if (k + 1 < a || k + 1 > b) s.classList.add('masquee');
    });
  },
  [Number(premiere), Number(derniere), Number(colonnes)],
);
await page.waitForTimeout(500);
await page.screenshot({ path: sortie, fullPage: true });
await navigateur.close();
console.log(sortie);
