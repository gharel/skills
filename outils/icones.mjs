/**
 * npm run icones : icônes Lucide (version figée du design system) en PNG noir, 256 px, fond transparent,
 * et en SVG, pour les rendus HTML, DOCX et PPTX. Les icônes des catégories sont lues dans la charte de
 * design-skazy. À relancer seulement si la liste des icônes change, puis npm run construire.
 */
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Resvg } from '@resvg/resvg-js';
import { trouverDesign, DESIGN_INTROUVABLE } from './skills.mjs';

const CHARTE = fileURLToPath(new URL('../commun/charte/', import.meta.url));
const LUCIDE = fileURLToPath(new URL('../node_modules/lucide-static/icons/', import.meta.url));

const design = trouverDesign();
if (!design) {
  console.error(DESIGN_INTROUVABLE);
  process.exit(1);
}
const charte = JSON.parse(await readFile(join(design, 'charte/charte.json'), 'utf8'));

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
    // Page 2 du plan de formation : formats (modèle plan-formation) et accompagnement.
    ...charte.modalitesParDefaut.formats.map((f) => f.icone),
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

console.log(`${ICONES.length} icônes écrites dans commun/charte/icones/.`);
