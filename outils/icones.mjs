/**
 * npm run icones : prépare les images de la charte utilisées par les rendus DOCX et PPTX.
 * - icônes Lucide (version figée du design system) en PNG noir, 256 px, fond transparent, et en SVG ;
 * - logos Skazy Formation (couleur et blanc) en PNG haute définition.
 * À relancer seulement si la liste des icônes ou les logos changent, puis npm run synchroniser.
 */
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { Resvg } from '@resvg/resvg-js';

const CHARTE = fileURLToPath(new URL('../commun/charte/', import.meta.url));
const LUCIDE = fileURLToPath(new URL('../node_modules/lucide-static/icons/', import.meta.url));

const charte = JSON.parse(await readFile(`${CHARTE}charte.json`, 'utf8'));

// Icônes des catégories + icônes des stickers et des mises en page du support.
const ICONES = [
  ...new Set([
    ...charte.categories.map((c) => c.icone),
    'hand',
    'target',
    'rocket',
    'user-round',
    'zap',
    'image',
    'lightbulb',
    'triangle-alert',
    'circle-check',
    'clock',
    'link',
    // Page 2 du plan de formation : modalités et accompagnement.
    'users',
    'video',
    'blend',
    'handshake',
  ]),
];

await mkdir(`${CHARTE}icones`, { recursive: true });

for (const nom of ICONES) {
  const svg = (await readFile(`${LUCIDE}${nom}.svg`, 'utf8')).replaceAll('currentColor', '#000');
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: 256 } }).render().asPng();
  await writeFile(`${CHARTE}icones/${nom}.png`, png);
  // SVG d'origine (currentColor) : les rendus HTML l'intègrent en masque CSS, sans réseau.
  await writeFile(`${CHARTE}icones/${nom}.svg`, await readFile(`${LUCIDE}${nom}.svg`, 'utf8'));
}

for (const variante of ['couleur', 'blanc']) {
  const svg = await readFile(`${CHARTE}logo-${variante}.svg`, 'utf8');
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: 480 } }).render().asPng();
  await writeFile(`${CHARTE}logo-${variante}.png`, png);
}

console.log(`${ICONES.length} icônes et 2 logos écrits dans commun/charte/.`);
