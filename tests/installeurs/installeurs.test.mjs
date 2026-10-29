/**
 * npm run test:installeurs (après npm run construire) : lance les installeurs de la plateforme sur le
 * site construit, dans un dossier personnel temporaire. Windows : installer.ps1 sous PowerShell 5.1,
 * et 7 s'il est présent ; macOS et Linux : installer.sh, et installer.ps1 si pwsh est présent.
 * Lancé par la CI sur Ubuntu, macOS et Windows. Rien n'est écrit hors du dossier temporaire.
 */
import { after, before, describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { lstat, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const RACINE = fileURLToPath(new URL('../../', import.meta.url));
const SITE = join(RACINE, '_site');
const windows = process.platform === 'win32';
const SKILLS = [
  'skazy-plan-formation',
  'skazy-support-formation',
  'skazy-quiz',
  'notation-etudiants',
];
const MARQUE = 'source: https://github.com/gharel/skills';

const present = (cmd, args) => spawnSync(cmd, args, { stdio: 'ignore' }).status === 0;
const INSTALLEURS = [];
const ps1 = join(RACINE, 'site/installer.ps1');
if (windows)
  INSTALLEURS.push({
    nom: 'installer.ps1 (PowerShell 5.1)',
    cmd: 'powershell.exe',
    args: ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ps1],
  });
else
  INSTALLEURS.push({ nom: 'installer.sh', cmd: 'sh', args: [join(RACINE, 'site/installer.sh')] });
if (present('pwsh', ['-NoProfile', '-Command', 'exit 0']))
  INSTALLEURS.push({
    nom: 'installer.ps1 (PowerShell 7)',
    cmd: 'pwsh',
    args: ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ps1],
  });

// Fichiers servis à la place de ceux du site, pour simuler un skill déprécié ou retiré.
const remplacements = {};
let serveur;
let adresse;
let index;

before(async () => {
  assert.ok(existsSync(join(SITE, 'skills.tsv')), 'lancez npm run construire avant ces tests');
  index = await readFile(join(SITE, 'skills.tsv'), 'utf8');
  serveur = createServer(async (requete, reponse) => {
    const chemin = decodeURIComponent(new URL(requete.url, 'http://local').pathname).slice(1);
    if (chemin in remplacements) return reponse.end(remplacements[chemin]);
    try {
      reponse.end(await readFile(join(SITE, chemin)));
    } catch {
      reponse.writeHead(404).end();
    }
  });
  await new Promise((pret) => serveur.listen(0, '127.0.0.1', pret));
  adresse = `http://127.0.0.1:${serveur.address().port}/`;
});
after(() => serveur?.close());

/** skills.tsv avec le statut (et le remplaçant) d'un skill changé. */
function indexAvec(nom, statut, remplacePar = '-') {
  return index.replace(
    new RegExp(`^(${nom}\\t[^\\t]+\\t[^\\t]+)\\t[^\\t]+\\t[^\\t\\n]+$`, 'm'),
    `$1\t${statut}\t${remplacePar}`,
  );
}

const estLien = async (chemin) => (await lstat(chemin)).isSymbolicLink();

for (const installeur of INSTALLEURS) {
  describe(installeur.nom, () => {
    let accueil;
    const agents = (...p) => join(accueil, '.agents', ...p);
    const claude = (...p) => join(accueil, '.claude', 'skills', ...p);

    // Lancement asynchrone : spawnSync bloquerait le serveur du test, dans le même processus.
    async function lancer(env = {}) {
      const base = Object.fromEntries(
        Object.entries(process.env).filter(([cle]) => !cle.toUpperCase().startsWith('SKILLS')),
      );
      const enfant = spawn(installeur.cmd, installeur.args, {
        env: {
          ...base,
          ...(windows ? {} : { HOME: accueil }),
          SKILLS_SITE: adresse,
          SKILLS_ACCUEIL: accueil,
          SKILLS_WINDOWS: '0',
          ...env,
        },
      });
      let sortie = '';
      enfant.stdout.on('data', (d) => (sortie += d));
      enfant.stderr.on('data', (d) => (sortie += d));
      const code = await new Promise((fin) => enfant.on('close', fin));
      assert.equal(code, 0, sortie);
      return sortie;
    }

    before(async () => {
      accueil = await mkdtemp(join(tmpdir(), 'installeur-'));
      await mkdir(join(accueil, '.codex'), { recursive: true });
      // Copie laissée par l'ancien installeur, et skill personnel homonyme dans Claude Code.
      await mkdir(join(accueil, '.gemini/skills/skazy-quiz'), { recursive: true });
      await writeFile(join(accueil, '.gemini/skills/skazy-quiz/SKILL.md'), `---\n${MARQUE}\n---\n`);
      await mkdir(claude('notation-etudiants'), { recursive: true });
      await writeFile(claude('notation-etudiants', 'SKILL.md'), 'perso');
    });
    after(() => rm(accueil, { recursive: true, force: true }));

    it('installe une copie par skill et un lien pour Claude Code', async () => {
      const sortie = await lancer();
      for (const nom of SKILLS) {
        assert.ok(existsSync(agents('skills', nom, 'SKILL.md')), nom);
        assert.ok(await estLien(claude(nom)), `${nom} : lien attendu`);
        assert.ok(existsSync(claude(nom, 'SKILL.md')), `${nom} : lien valide`);
      }
      assert.match(sortie, /\+ skazy-quiz/);
      assert.ok(!existsSync(join(accueil, '.gemini/skills/skazy-quiz')), 'ancienne copie retirée');
      assert.equal((await readdir(agents('.gharel-skills', 'sauvegardes'))).length, 1);
      assert.match(
        await readFile(agents('.gharel-skills', 'manifeste.tsv'), 'utf8'),
        /^skill\tskazy-quiz\t/m,
      );
    });

    it('ne télécharge rien au deuxième passage et garde les copies intactes', async () => {
      const sortie = await lancer();
      for (const nom of SKILLS) assert.match(sortie, new RegExp(`= ${nom} `));
      assert.doesNotMatch(sortie, /^\s+[+^] /m);
      for (const nom of SKILLS) {
        assert.ok(await estLien(claude(nom)), nom);
        assert.ok(existsSync(agents('skills', nom, 'SKILL.md')), `${nom} : copie intacte`);
      }
    });

    it('garde un skill déprécié déjà installé, supprime un skill retiré, ne réinstalle pas un déprécié', async () => {
      remplacements['skills.tsv'] = indexAvec('skazy-quiz', 'deprecie', 'skazy-plan-formation');
      assert.match(await lancer(), /par skazy-plan-formation/);
      assert.ok(existsSync(agents('skills', 'skazy-quiz', 'SKILL.md')));

      remplacements['skills.tsv'] = indexAvec('skazy-quiz', 'retire');
      assert.match(await lancer(), /- skazy-quiz/);
      assert.ok(!existsSync(agents('skills', 'skazy-quiz')));
      assert.ok(!existsSync(claude('skazy-quiz')));
      assert.ok(existsSync(agents('skills', 'skazy-plan-formation', 'SKILL.md')));

      remplacements['skills.tsv'] = indexAvec('skazy-quiz', 'deprecie', 'skazy-plan-formation');
      await lancer();
      assert.ok(!existsSync(agents('skills', 'skazy-quiz')));
      delete remplacements['skills.tsv'];
    });

    it('retient la sélection d’une fois sur l’autre', async () => {
      const sortie = await lancer({ SKILLS_CATEGORIE: 'pro' });
      assert.match(sortie, /- notation-etudiants/);
      assert.match(sortie, /\+ skazy-quiz/);
      assert.ok(!existsSync(agents('skills', 'notation-etudiants')));
      assert.ok(!existsSync(claude('notation-etudiants')), 'lien retiré');
      await lancer();
      assert.ok(!existsSync(agents('skills', 'notation-etudiants')));
      assert.match(
        await readFile(agents('.gharel-skills', 'manifeste.tsv'), 'utf8'),
        /^selection\tcategories\tpro$/m,
      );
    });

    it('prépare la mise à jour automatique (essai, sans l’inscrire)', async (t) => {
      if (installeur.cmd === 'pwsh' && !windows)
        return t.skip('installer.sh s’en charge hors de Windows');
      const sortie = await lancer({ SKILLS_AUTO: 'essai' });
      assert.match(sortie, /\(essai\)/);
      if (windows) assert.ok(existsSync(agents('.gharel-skills', 'installer.ps1')));
      else if (process.platform === 'darwin')
        assert.ok(existsSync(join(accueil, 'Library/LaunchAgents/nc.skazy.gharel-skills.plist')));
      else assert.ok(existsSync(join(accueil, '.config/systemd/user/gharel-skills.timer')));
    });

    it('désinstalle tout et restaure le skill personnel', async () => {
      await lancer({ SKILLS_ACTION: 'desinstaller' });
      assert.ok(!existsSync(agents('skills')));
      assert.ok(!existsSync(agents('.gharel-skills')));
      assert.deepEqual(await readdir(claude()), ['notation-etudiants']);
      assert.equal(await readFile(claude('notation-etudiants', 'SKILL.md'), 'utf8'), 'perso');
    });
  });
}
