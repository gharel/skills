/**
 * npm run synchroniser : recopie la charte commune (commun/charte) dans chaque skill qui la déclare
 * (metadata.charte dans SKILL.md), pour que chaque skill reste autonome une fois installé.
 *   charte: skazy-formation          → scripts/charte.py + assets/charte/ complet (logos, icônes)
 *   charte: skazy-formation-donnees  → scripts/charte.py + assets/charte/charte.json seulement
 * Avec --verifier, ne copie rien : échoue si une copie diffère de la source (npm run check, CI).
 */
import { readFile, writeFile, mkdir, readdir, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { RACINE, listerSkills } from './skills.mjs';

const SOURCE = join(RACINE, 'commun/charte');
const verifier = process.argv.includes('--verifier');

async function fichiersCharte(complet) {
  if (!complet) return ['charte.json'];
  const liste = (await readdir(SOURCE)).filter((f) => f !== 'charte.py' && f !== 'icones');
  const icones = (await readdir(join(SOURCE, 'icones'))).map((f) => `icones/${f}`);
  return [...liste, ...icones];
}

const ecarts = [];
let copies = 0;
for (const skill of await listerSkills()) {
  const charte = skill.donnees.metadata?.charte;
  if (!charte) continue;
  const complet = charte === 'skazy-formation';
  const paires = [[join(SOURCE, 'charte.py'), join(skill.dossier, 'scripts/charte.py')]];
  for (const f of await fichiersCharte(complet))
    paires.push([join(SOURCE, f), join(skill.dossier, 'assets/charte', f)]);
  // Fichiers en trop dans assets/charte (icône retirée de la source, skill passé en « données »).
  const attendus = new Set(paires.map(([, cible]) => cible));
  const dossierCharte = join(skill.dossier, 'assets/charte');
  if (existsSync(dossierCharte)) {
    for (const f of await readdir(dossierCharte, { recursive: true, withFileTypes: true })) {
      const chemin = join(f.parentPath ?? f.path, f.name);
      if (f.isFile() && !attendus.has(chemin)) {
        if (verifier) ecarts.push(`${chemin} n'existe pas dans commun/charte`);
        else await rm(chemin);
      }
    }
  }
  for (const [source, cible] of paires) {
    const contenu = await readFile(source);
    const actuel = existsSync(cible) ? await readFile(cible) : null;
    if (actuel && actuel.equals(contenu)) continue;
    if (verifier) {
      ecarts.push(`${cible} diffère de ${source}`);
      continue;
    }
    await mkdir(dirname(cible), { recursive: true });
    await writeFile(cible, contenu);
    copies++;
  }
}

if (verifier) {
  if (ecarts.length) {
    console.error(
      'Charte désynchronisée (lancez npm run synchroniser) :\n- ' + ecarts.join('\n- '),
    );
    process.exit(1);
  }
  console.log('Charte synchronisée dans tous les skills.');
} else {
  console.log(`${copies} fichier(s) de charte recopié(s).`);
}
