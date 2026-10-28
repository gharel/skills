/**
 * npm run construire : contrôle les skills puis construit le site dans _site/ :
 *   - index.html (catalogue généré), skills.json ;
 *   - telechargements/<skill>.zip (Claude.ai, ChatGPT) et <skill>.md (version un fichier) ;
 *   - icones/<skill>.svg (sticker affiché par le catalogue) ;
 *   - .claude-plugin/marketplace.json à la racine du dépôt (plugins Claude Code).
 * Avec --verifier : contrôles seulement (spécification, versions, marketplace à jour), sans écrire.
 * Variable BASE : commit de comparaison pour les versions (par défaut HEAD).
 */
import { readFile, writeFile, mkdir, rm, cp, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { zipSync } from 'fflate';
import {
  RACINE,
  CATEGORIES,
  URL_SITE,
  URL_DEPOT,
  listerSkills,
  controler,
  lireFrontmatter,
} from './skills.mjs';

const verifier = process.argv.includes('--verifier');
const SITE = join(RACINE, '_site');
const ICONES_PAGE = {
  'circle-half-stroke': 'contrast',
  sun: 'sun',
  moon: 'moon',
  github: 'github',
  download: 'download',
  'file-text': 'file-text',
};

const echapper = (t) =>
  String(t ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');

function git(...args) {
  try {
    return execFileSync('git', args, {
      cwd: RACINE,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
  } catch {
    return null;
  }
}

// ── 1. Contrôles ──────────────────────────────────────────
const skills = await listerSkills();
const erreurs = skills.flatMap(controler);
const noms = skills.map((s) => s.nom);
for (const nom of new Set(noms))
  if (noms.filter((n) => n === nom).length > 1)
    erreurs.push(`skill « ${nom} » présent dans plusieurs catégories.`);

// Un skill modifié depuis BASE doit changer de version (sinon les installations ne le voient pas).
const base = process.env.BASE || 'HEAD';
if (!/^0+$/.test(base) && git('rev-parse', '--verify', '--quiet', `${base}^{commit}`)) {
  for (const s of skills) {
    const ancien = git('show', `${base}:${s.chemin}/SKILL.md`);
    if (ancien === null) continue; // nouveau skill
    const modifie = git('diff', '--name-only', base, '--', s.chemin);
    const ancienneVersion = lireFrontmatter(ancien).donnees?.metadata?.version;
    if (modifie && ancienneVersion === s.version)
      erreurs.push(
        `${s.chemin} : contenu modifié depuis ${base.slice(0, 7)} mais version inchangée (${s.version}) : montez metadata.version et complétez CHANGELOG.md.`,
      );
  }
}

// ── 2. Place de marché Claude Code ───────────────────────
const marketplace = {
  name: 'gharel-skills',
  owner: { name: 'Guillaume Harel', url: 'https://github.com/gharel' },
  description:
    'Skills IA de Guillaume Harel : Skazy Formation (plan, support, quiz), UNC et usage personnel.',
  plugins: CATEGORIES.filter((c) => skills.some((s) => s.categorie === c.id)).map((c) => ({
    name: c.plugin,
    displayName: `${c.titre} · ${c.sousTitre}`,
    description: c.description,
    source: './',
    strict: false,
    homepage: URL_SITE,
    skills: skills.filter((s) => s.categorie === c.id).map((s) => `./${s.chemin}`),
  })),
};
const cheminMarketplace = join(RACINE, '.claude-plugin/marketplace.json');
const texteMarketplace = JSON.stringify(marketplace, null, 2) + '\n';
if (verifier) {
  const actuel = existsSync(cheminMarketplace) ? await readFile(cheminMarketplace, 'utf8') : '';
  if (actuel.replaceAll('\r\n', '\n') !== texteMarketplace)
    erreurs.push('.claude-plugin/marketplace.json n’est pas à jour : lancez npm run construire.');
}

if (erreurs.length) {
  console.error(
    'Contrôle des skills : ' + erreurs.length + ' erreur(s)\n- ' + erreurs.join('\n- '),
  );
  process.exit(1);
}
if (verifier) {
  console.log(`${skills.length} skill(s) conformes : ${noms.join(', ')}.`);
  process.exit(0);
}

await mkdir(join(RACINE, '.claude-plugin'), { recursive: true });
await writeFile(cheminMarketplace, texteMarketplace);

// ── 3. Site ──────────────────────────────────────────────
await rm(SITE, { recursive: true, force: true });
await cp(join(RACINE, 'site'), SITE, { recursive: true });
await mkdir(join(SITE, 'telechargements'), { recursive: true });
await mkdir(join(SITE, 'icones'), { recursive: true });

const aujourdhui = new Date().toISOString().slice(0, 10);
const dateFr = (iso) =>
  new Date(iso + 'T12:00:00').toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

function instructionsCourtes(s) {
  return [
    `Tu es l'assistant « ${s.titre} » (skill ${s.nom}, version ${s.version}).`,
    `Suis à la lettre les consignes du fichier « ${s.nom}.md » joint : déroulé, règles et format de sortie.`,
    'Produis les fichiers en exécutant les scripts Python du skill (dossier scripts/ du fichier .zip).',
    'Sans exécution de code, donne le JSON complet dans un bloc de code et la commande du script qui le rend.',
    'Réponds en français, avec le vouvoiement.',
  ].join('\n');
}

function versionUnFichier(s, annexes) {
  const morceaux = [
    `# ${s.titre} (skill ${s.nom}, version ${s.version})`,
    '',
    `> Version en un seul fichier du skill \`${s.nom}\`, pour les assistants qui n'importent pas de dossier de skill (GPT personnalisés, Gems, projets, agents).`,
    `> Les scripts de rendu ne sont pas inclus : joignez aussi le contenu du .zip (scripts et charte) et activez l'exécution de code.`,
    `> Source et mises à jour : ${URL_SITE}`,
    '',
    s.corps.trim(),
  ];
  for (const [chemin, contenu] of annexes) {
    morceaux.push('', '---', '', `## Annexe : ${chemin}`, '');
    if (chemin.endsWith('.md')) {
      // Les titres de l'annexe descendent d'un niveau (hors blocs de code).
      let code = false;
      morceaux.push(
        contenu
          .trim()
          .split('\n')
          .map((l) => {
            if (l.startsWith('```')) code = !code;
            return !code && /^#{1,5} /.test(l) ? '#' + l : l;
          })
          .join('\n'),
      );
    } else {
      morceaux.push('```' + (chemin.endsWith('.json') ? 'json' : ''), contenu.trim(), '```');
    }
  }
  return morceaux.join('\n') + '\n';
}

const resume = [];
for (const s of skills) {
  const date = git('log', '-1', '--format=%cs', '--', s.chemin) || aujourdhui;
  s.date = date;
  // Zip : le dossier du skill à la racine de l'archive (format attendu par Claude.ai et ChatGPT).
  const entrees = {};
  for (const f of s.fichiers)
    entrees[`${s.nom}/${f}`] = new Uint8Array(await readFile(join(s.dossier, f)));
  await writeFile(
    join(SITE, 'telechargements', `${s.nom}.zip`),
    zipSync(entrees, { level: 9, mtime: new Date(date) }),
  );
  // Version un fichier : SKILL.md + références + exemples.
  const annexes = [];
  for (const f of s.fichiers
    .filter((f) => /^(references\/.*\.md|exemples\/.*\.json)$/.test(f))
    .sort())
    annexes.push([f, await readFile(join(s.dossier, f), 'utf8')]);
  await writeFile(join(SITE, 'telechargements', `${s.nom}.md`), versionUnFichier(s, annexes));
  await cp(join(s.dossier, 'assets/icon.svg'), join(SITE, 'icones', `${s.nom}.svg`));
  resume.push({
    nom: s.nom,
    titre: s.titre,
    resume: s.resume,
    description: s.description,
    version: s.version,
    categorie: s.categorie,
    date,
    zip: `telechargements/${s.nom}.zip`,
    md: `telechargements/${s.nom}.md`,
    source: `${URL_DEPOT}/tree/main/${s.chemin}`,
  });
}
await writeFile(
  join(SITE, 'skills.json'),
  JSON.stringify({ genere: aujourdhui, skills: resume }, null, 2),
);

// ── 4. Catalogue dans index.html ─────────────────────────
function carte(s) {
  return `<article class="carte" id="skill-${s.nom}" data-skill="${s.nom}" data-version="${s.version}">
  <div class="carte__tete">
    <img src="icones/${s.nom}.svg" alt="" width="52" height="52" />
    <div><h4 class="carte__titre">${echapper(s.titre)}</h4><code class="carte__nom">${s.nom}</code></div>
  </div>
  <p class="carte__resume">${echapper(s.resume || s.description)}</p>
  <ul class="carte__meta">
    <li class="badge badge--version">v${s.version}</li>
    <li class="badge">${dateFr(s.date)}</li>
    <li class="badge badge--nouveau" hidden>Nouvelle version</li>
  </ul>
  <details><summary>Quand l’utiliser</summary><p>${echapper(s.description)}</p></details>
  <div class="carte__actions">
    <a class="bouton bouton--primaire" href="telechargements/${s.nom}.zip" download>
      <svg class="icone" aria-hidden="true"><use href="#i-download" /></svg>Télécharger le skill
    </a>
    <a class="bouton bouton--secondaire" href="telechargements/${s.nom}.md" download>
      <svg class="icone" aria-hidden="true"><use href="#i-file-text" /></svg>Version un fichier
    </a>
  </div>
  <div class="carte__liens">
    <button type="button" data-copier="instructions-${s.nom}">Copier les instructions</button>
    <a href="${URL_DEPOT}/tree/main/${s.chemin}">Code source</a>
  </div>
  <template id="instructions-${s.nom}">${echapper(instructionsCourtes(s))}</template>
</article>`;
}

const catalogue = CATEGORIES.map((c) => {
  const liste = skills.filter((s) => s.categorie === c.id);
  const cartes = liste.length
    ? liste.map(carte).join('\n')
    : `<div class="carte carte--vide"><strong>Bientôt</strong><p>Les skills ${echapper(c.titre)} arrivent.</p></div>`;
  return `<section class="categorie" aria-labelledby="categorie-${c.id}">
  <div class="categorie__tete"><h3 class="categorie__titre" id="categorie-${c.id}">${echapper(c.titre)}</h3><span class="categorie__sous-titre">${echapper(c.sousTitre)}</span></div>
  <p class="categorie__description">${echapper(c.description)}</p>
  <div class="grille">${cartes}</div>
</section>`;
}).join('\n');

let sprite = '<svg aria-hidden="true" width="0" height="0" style="position: absolute">';
for (const [id, nom] of Object.entries(ICONES_PAGE)) {
  const svg = await readFile(
    join(RACINE, 'node_modules/lucide-static/icons', `${nom}.svg`),
    'utf8',
  );
  const interieur = svg
    .slice(svg.indexOf('>', svg.indexOf('<svg')) + 1, svg.lastIndexOf('</svg>'))
    .trim();
  sprite += `<symbol id="i-${id}" viewBox="0 0 24 24">${interieur}</symbol>`;
}
sprite += '</svg>';

const nombre = skills.length;
const chapo = `${nombre} skill${nombre > 1 ? 's' : ''} pour l’instant, rangés en trois familles. Chaque carte donne le skill complet (.zip, pour Claude et ChatGPT) et sa version en un seul fichier (.md, pour les autres assistants).`;
const page = (await readFile(join(SITE, 'index.html'), 'utf8'))
  .replace('<!-- @icones -->', sprite)
  .replace('<!-- @catalogue -->', catalogue)
  .replace('<!-- @resume -->', echapper(chapo))
  .replace('<!-- @date -->', dateFr(aujourdhui));
await writeFile(join(SITE, 'index.html'), page);

const taille = (await readdir(join(SITE, 'telechargements'))).length;
console.log(`Site construit dans _site/ : ${nombre} skill(s), ${taille} fichier(s) à télécharger.`);
