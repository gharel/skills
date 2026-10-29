/**
 * npm run modeles : compare au pixel les rendus HTML des skills plan et support à leurs modèles de design-skazy
 * (templates/plan-formation et templates/support-formation), seule référence de leur design.
 *
 * Les modèles sont lus dans design-skazy, sans copie dans ce dépôt. Les deux côtés affichent le même contenu :
 * celui des modèles, repris comme données de test dans tests/modeles/*.json. Pour chaque
 * texte du modèle, le texte identique du skill doit être à la même place (1 px près), de la même taille, avec
 * la même police, le même interligne, la même graisse et la même couleur. Sans écart, l'empreinte des modèles
 * est verrouillée dans commun/charte/alignement.json (npm run construire la recopie dans les skills) : npm run
 * check refuse ensuite un modèle changé dans design-skazy tant que cette comparaison n'a pas été refaite.
 *
 * Demande design-skazy ($DESIGN_SKAZY ou ../design-skazy) et un Python qui a les dépendances des skills
 * ($PYTHON, sinon « python »). Usage : npm run modeles [-- plan-formation|support-formation]
 */
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { join, extname, basename } from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { RACINE, MODELES, ALIGNEMENT, empreintesModeles, trouverDesign } from './skills.mjs';

const TOLERANCE = 1; // px du modèle
const CAS = {
  'plan-formation': {
    largeur: 794,
    script: 'skills/pro/skazy-plan-formation/scripts/rendre_plan.py',
    json: 'tests/modeles/plan-modele.json',
    pages: '.page[data-screen-label]',
  },
  'support-formation': {
    largeur: 1920,
    script: 'skills/pro/skazy-support-formation/scripts/rendre_support.py',
    json: 'tests/modeles/support-modele.json',
    pages: 'section[data-screen-label], section.slide',
  },
};

const design = trouverDesign();
if (!design) {
  console.error(
    'design-skazy introuvable ($DESIGN_SKAZY ou ../design-skazy) : comparaison impossible.',
  );
  process.exit(1);
}
// Rendus HTML des skills pour le contenu des modèles, avec la charte du même design-skazy.
const SORTIE = join(RACINE, 'sorties/modeles');
await mkdir(SORTIE, { recursive: true });
const python = process.env.PYTHON || 'python';
const rendus = {};
for (const [nom, c] of Object.entries(CAS)) {
  const sortie = execFileSync(
    python,
    [join(RACINE, c.script), join(RACINE, c.json), '--sortie', SORTIE, '--formats', 'html'],
    { encoding: 'utf8', env: { ...process.env, DESIGN_SKAZY: design, PYTHONIOENCODING: 'utf-8' } },
  );
  rendus[nom] = sortie.trim().split(/\r?\n/).pop().trim();
}

// design-skazy servi en HTTP : ses modèles chargent leurs scripts et le design system par chemins relatifs.
const TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.jpg': 'image/jpeg',
};
const serveur = createServer(async (req, res) => {
  const chemin = join(design, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  let contenu;
  try {
    contenu = await readFile(chemin);
  } catch {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[extname(chemin)] ?? 'application/octet-stream' });
  res.end(contenu);
});
await new Promise((ok) => serveur.listen(0, '127.0.0.1', ok));
const base = `http://127.0.0.1:${serveur.address().port}/`;

/** Textes (rectangles des nœuds texte) et styles de chaque page ou slide, en px du modèle. */
async function mesurer(page, url, selecteur, largeur) {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(3000);
  // Mise en page d'impression : le diaporama du modèle n'affiche sinon que la slide courante.
  await page.emulateMedia({ media: 'print' });
  await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
  await page.waitForTimeout(1500);
  return page.evaluate(
    ({ selecteur, largeur }) => {
      const pages = [...document.querySelectorAll(selecteur)];
      return pages.map((s) => {
        const r0 = s.getBoundingClientRect();
        const k = r0.width / largeur;
        const textes = [];
        const marcheur = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
        for (let n = marcheur.nextNode(); n; n = marcheur.nextNode()) {
          const t = n.textContent.replace(/\s+/g, ' ').trim();
          if (!t) continue;
          const el = n.parentElement;
          const cs = getComputedStyle(el);
          if (cs.display === 'none' || cs.visibility === 'hidden') continue;
          const plage = document.createRange();
          plage.selectNodeContents(n);
          const r = plage.getBoundingClientRect();
          if (!r.width || !r.height) continue;
          const f = (v) => Math.round((v / k) * 10) / 10;
          textes.push({
            t,
            x: f(r.left - r0.left),
            y: f(r.top - r0.top),
            w: f(r.width),
            h: f(r.height),
            style: [
              cs.fontFamily.split(',')[0].replace(/["']/g, ''),
              cs.fontSize,
              cs.lineHeight,
              cs.fontWeight,
              cs.fontStyle,
              cs.color,
              cs.textTransform,
              cs.letterSpacing,
            ].join(' '),
          });
        }
        return { titre: s.dataset.screenLabel || s.getAttribute('aria-label') || '', textes };
      });
    },
    { selecteur, largeur },
  );
}

const normaliser = (t) => t.replace(/[\s\u00a0\u202f]+/g, '').replace(/’/g, "'");

function comparer(modele, skill) {
  const ecarts = [];
  // Le skill rend la réponse du quiz sur une slide à part : on l'écarte pour apparier les slides dans l'ordre.
  const slides = skill.filter(
    (s) =>
      !/quiz/.test(s.titre) ||
      !s.textes.some((x) => /Bonne réponse/.test(x.t)) ||
      modele.some((m) => /Bonne réponse/.test(JSON.stringify(m))),
  );
  modele.forEach((m, i) => {
    const s = slides[i];
    if (!s) return ecarts.push(`${m.titre} : page absente du rendu du skill`);
    const libres = [...s.textes];
    for (const e of m.textes) {
      const candidats = libres.filter((x) => normaliser(x.t) === normaliser(e.t));
      if (!candidats.length) {
        ecarts.push(`${m.titre} : « ${e.t.slice(0, 40)} » absent du skill`);
        continue;
      }
      const x = candidats.reduce((a, b) =>
        Math.abs(b.x - e.x) + Math.abs(b.y - e.y) < Math.abs(a.x - e.x) + Math.abs(a.y - e.y)
          ? b
          : a,
      );
      libres.splice(libres.indexOf(x), 1);
      const d = ['x', 'y', 'w', 'h'].map((c) => Math.round((x[c] - e[c]) * 10) / 10);
      if (d.some((v) => Math.abs(v) > TOLERANCE))
        ecarts.push(
          `${m.titre} : « ${e.t.slice(0, 40)} » décalé (dx ${d[0]}, dy ${d[1]}, dw ${d[2]}, dh ${d[3]})`,
        );
      if (x.style !== e.style)
        ecarts.push(`${m.titre} : « ${e.t.slice(0, 40)} » style ${x.style} au lieu de ${e.style}`);
    }
  });
  return ecarts;
}

const choix = process.argv.slice(2).filter((a) => CAS[a]);
const navigateur = await chromium.launch();
let total = 0;
try {
  for (const nom of choix.length ? choix : Object.keys(CAS)) {
    const c = CAS[nom];
    const page = await navigateur.newPage({
      viewport: { width: c.largeur === 1920 ? 1920 : 1100, height: 1300 },
    });
    const modele = await mesurer(page, base + MODELES[nom].source, c.pages, c.largeur);
    const skill = await mesurer(page, pathToFileURL(rendus[nom]).href, c.pages, c.largeur);
    await page.close();
    const ecarts = comparer(modele, skill);
    const textes = modele.reduce((n, p) => n + p.textes.length, 0);
    console.log(
      `${nom} : ${modele.length} page(s), ${textes} textes comparés, ${ecarts.length} écart(s) (${basename(rendus[nom])}).`,
    );
    for (const e of ecarts.slice(0, 60)) console.log('  - ' + e);
    total += ecarts.length;
  }
} finally {
  await navigateur.close();
  serveur.close();
}

if (total) {
  console.error(
    `\n${total} écart(s) : le skill ne reproduit pas son modèle. Alignement non verrouillé.`,
  );
  process.exit(1);
}
if (choix.length) {
  console.log(
    'Comparaison partielle : alignement non verrouillé (lancez npm run modeles sans argument).',
  );
} else {
  const empreintes = await empreintesModeles(design);
  let commit = 'inconnu';
  try {
    commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: design }).toString().trim();
  } catch {
    // design-skazy sans git : commit inconnu.
  }
  const modeles = Object.fromEntries(
    Object.entries(empreintes).map(([nom, empreinte]) => [
      nom,
      { empreinte, skill: MODELES[nom].skill },
    ]),
  );
  await writeFile(ALIGNEMENT, JSON.stringify({ design: commit, modeles }, null, 2) + '\n');
  console.log(
    'Rendus identiques aux modèles : alignement verrouillé dans commun/charte/alignement.json. Lancez npm run construire pour le recopier dans les skills.',
  );
}
