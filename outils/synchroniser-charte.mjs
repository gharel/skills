/**
 * npm run synchroniser : la charte vient du design system design-skazy (github.com/gharel/design-skazy),
 * seule source de vérité. Deux étapes :
 *   1. design-skazy → commun/charte : charte/charte.json, charte/plan-formation.{css,js} (générés par
 *      npm run charte dans design-skazy) et les logos des modèles (assets/logo-color.png, logo-white.png).
 *      Les modèles eux-mêmes restent dans design-skazy : aucune autre version n'en existe ici.
 *      Le dépôt design-skazy est cherché dans $DESIGN_SKAZY, puis à côté de ce dépôt (…/www/design-skazy).
 *      Introuvable : étape sautée, commun/charte reste tel quel.
 *   2. commun/charte → chaque skill qui la déclare (metadata.charte dans SKILL.md), pour qu'il reste autonome :
 *        charte: skazy-formation          → scripts/charte.py + assets/charte/ complet (logos, icônes ;
 *                                           <modèle>.css et .js seulement pour le skill skazy-<modèle>)
 *        charte: skazy-formation-donnees  → scripts/charte.py + assets/charte/charte.json seulement
 * Avec --verifier, ne copie rien : échoue si une copie diffère de sa source (npm run check, CI), ou si un
 * modèle de design-skazy a changé depuis la dernière comparaison des rendus des skills avec lui
 * (npm run modeles, qui verrouille l'empreinte des modèles dans commun/charte/alignement.json).
 * charte.py et les icônes Lucide (npm run icones) restent propres à ce dépôt : du code et une bibliothèque
 * d'icônes, pas la charte.
 */
import { readFile, writeFile, mkdir, readdir, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname, resolve } from 'node:path';
import {
  RACINE,
  listerSkills,
  MODELES as MODELES_DESIGN,
  ALIGNEMENT,
  empreintesModeles,
  trouverDesign,
} from './skills.mjs';

const SOURCE = join(RACINE, 'commun/charte');
const verifier = process.argv.includes('--verifier');

// Fichiers repris de design-skazy : chemin dans design-skazy → nom dans commun/charte.
const DEPUIS_DESIGN = {
  'charte/charte.json': 'charte.json',
  'charte/plan-formation.css': 'plan-formation.css',
  'charte/plan-formation.js': 'plan-formation.js',
  'assets/logo-color.png': 'logo-color.png',
  'assets/logo-white.png': 'logo-white.png',
};
// Fichiers propres à un modèle : copiés seulement dans le skill skazy-<modèle>.
const MODELES = /^(plan-formation|support-formation)\.(css|js)$/;

const ecarts = [];
let copies = 0;

async function copier(source, cible) {
  const contenu = await readFile(source);
  const actuel = existsSync(cible) ? await readFile(cible) : null;
  if (actuel && actuel.equals(contenu)) return;
  if (verifier) {
    ecarts.push(`${cible} diffère de ${source}`);
    return;
  }
  await mkdir(dirname(cible), { recursive: true });
  await writeFile(cible, contenu);
  copies++;
}

// 1. design-skazy → commun/charte
const design = trouverDesign();
if (design) {
  for (const [depuis, vers] of Object.entries(DEPUIS_DESIGN))
    await copier(join(design, depuis), join(SOURCE, vers));
  if (!verifier) {
    let commit = 'inconnu';
    try {
      commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: design }).toString().trim();
    } catch {
      // design-skazy sans git (copie, archive) : commit inconnu.
    }
    const origine = {
      depot: 'https://github.com/gharel/design-skazy',
      commit,
      fichiers: DEPUIS_DESIGN,
    };
    const chemin = join(SOURCE, 'origine.json');
    const actuel = existsSync(chemin) ? JSON.parse(await readFile(chemin, 'utf8')) : null;
    if (copies || !actuel) await writeFile(chemin, JSON.stringify(origine, null, 2) + '\n');
  }
} else {
  console.warn(
    'design-skazy introuvable ($DESIGN_SKAZY ou ../design-skazy) : commun/charte non comparée au design system.',
  );
}

// 2. commun/charte → skills
async function fichiersCharte(skill, complet) {
  if (!complet) return ['charte.json'];
  const nom = skill.donnees.name;
  const liste = (await readdir(SOURCE)).filter(
    (f) =>
      !['charte.py', 'icones', 'origine.json', 'alignement.json'].includes(f) &&
      (!MODELES.test(f) || nom === `skazy-${f.replace(MODELES, '$1')}`),
  );
  const icones = (await readdir(join(SOURCE, 'icones'))).map((f) => `icones/${f}`);
  return [...liste, ...icones];
}

for (const skill of await listerSkills()) {
  const charte = skill.donnees.metadata?.charte;
  if (!charte) continue;
  const complet = charte === 'skazy-formation';
  const paires = [[join(SOURCE, 'charte.py'), join(skill.dossier, 'scripts/charte.py')]];
  for (const f of await fichiersCharte(skill, complet))
    paires.push([join(SOURCE, f), join(skill.dossier, 'assets/charte', f)]);
  // Fichiers en trop dans assets/charte (icône retirée de la source, skill passé en « données »).
  const attendus = new Set(paires.map(([, cible]) => resolve(cible)));
  const dossierCharte = join(skill.dossier, 'assets/charte');
  if (existsSync(dossierCharte)) {
    for (const f of await readdir(dossierCharte, { recursive: true, withFileTypes: true })) {
      const chemin = join(f.parentPath ?? f.path, f.name);
      if (f.isFile() && !attendus.has(resolve(chemin))) {
        if (verifier) ecarts.push(`${chemin} n'existe pas dans commun/charte`);
        else await rm(chemin);
      }
    }
  }
  for (const [source, cible] of paires) await copier(source, cible);
}

// 3. Verrou : les rendus des skills ont été comparés à la version actuelle des modèles de design-skazy.
const verrou = existsSync(ALIGNEMENT) ? JSON.parse(await readFile(ALIGNEMENT, 'utf8')).modeles : {};
for (const [nom, empreinte] of Object.entries(design ? await empreintesModeles(design) : {})) {
  if (verrou?.[nom]?.empreinte !== empreinte) {
    const message = `le modèle ${nom} a changé depuis la dernière comparaison avec le skill ${MODELES_DESIGN[nom].skill} : réalignez le skill, puis lancez npm run modeles`;
    if (verifier) ecarts.push(message);
    else console.warn('ATTENTION : ' + message + '.');
  }
}

if (verifier) {
  if (ecarts.length) {
    console.error(
      'Charte désynchronisée (lancez npm run synchroniser) :\n- ' + ecarts.join('\n- '),
    );
    process.exit(1);
  }
  console.log(
    `Charte synchronisée dans tous les skills${design ? ', à jour avec design-skazy' : ''}.`,
  );
} else {
  console.log(`${copies} fichier(s) de charte recopié(s)${design ? ` depuis ${design}` : ''}.`);
}
