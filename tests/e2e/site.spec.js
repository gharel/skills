import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const SKILLS = [
  'skazy-plan-formation',
  'skazy-support-formation',
  'skazy-quiz',
  'notation-etudiants',
];

test.describe('Catalogue', () => {
  test('présente les skills Pro dans l’ordre de la chaîne, puis les skills UNC', async ({
    page,
  }) => {
    await page.goto('./');
    await expect(page).toHaveTitle('Skills IA · Skazy Formation');
    const cartes = page.locator('.carte[data-skill]');
    await expect(cartes).toHaveCount(4);
    expect(await cartes.evaluateAll((l) => l.map((c) => c.dataset.skill))).toEqual(SKILLS);
    await expect(page.locator('#categorie-unc')).toBeVisible();
    await expect(page.locator('#categorie-perso')).toBeVisible();
    await expect(page.locator('.carte--vide')).toHaveCount(1);
  });

  test('les téléchargements existent', async ({ page, request }) => {
    await page.goto('./');
    for (const nom of SKILLS) {
      for (const extension of ['zip', 'md']) {
        const reponse = await request.get(`telechargements/${nom}.${extension}`);
        expect(reponse.ok(), `${nom}.${extension}`).toBe(true);
      }
    }
    const index = await (await request.get('skills.json')).json();
    expect(index.skills.map((s) => s.nom)).toEqual(SKILLS);
    expect(index.skills.map((s) => s.statut)).toEqual(SKILLS.map(() => 'recommande'));
    // Index des installeurs : nom, catégorie, version, statut, remplaçant.
    const tsv = (await (await request.get('skills.tsv')).text()).trim().split('\n');
    expect(tsv[0]).toMatch(/^# nom\tcategorie\tversion\tstatut/);
    expect(tsv.slice(1).map((l) => l.split('\t')[0])).toEqual(SKILLS);
    for (const l of tsv.slice(1)) expect(l.split('\t')).toHaveLength(5);
    for (const fichier of [
      'installer.ps1',
      'installer.sh',
      ...SKILLS.map((n) => `icones/${n}.svg`),
    ]) {
      expect((await request.get(fichier)).ok(), fichier).toBe(true);
    }
  });

  test('les onglets d’installation affichent un seul panneau à la fois', async ({ page }) => {
    await page.goto('./');
    const onglets = page.getByRole('tab');
    await expect(onglets).toHaveCount(5);
    await expect(page.locator('#panneau-claude')).toBeVisible();
    await expect(page.locator('#panneau-chatgpt')).toBeHidden();
    await page.getByRole('tab', { name: 'ChatGPT' }).click();
    await expect(page.locator('#panneau-chatgpt')).toBeVisible();
    await expect(page.locator('#panneau-claude')).toBeHidden();
    await page.getByRole('tab', { name: 'ChatGPT' }).press('ArrowRight');
    await expect(page.locator('#panneau-claude-code')).toBeVisible();
    await expect(page.locator('#panneau-claude-code code').first()).toHaveText(
      '/plugin marketplace add gharel/skills',
    );
  });

  test('signale une nouvelle version depuis la dernière visite', async ({ page }) => {
    await page.goto('./');
    await page.evaluate(() =>
      localStorage.setItem('skazy-skills:versions', JSON.stringify({ 'skazy-quiz': '0.9.0' })),
    );
    await page.reload();
    await expect(page.locator('#skill-skazy-quiz .badge--nouveau')).toBeVisible();
    await expect(page.locator('#skill-skazy-plan-formation .badge--nouveau')).toBeHidden();
    await page.reload();
    await expect(page.locator('#skill-skazy-quiz .badge--nouveau')).toBeHidden();
  });

  for (const theme of ['light', 'dark']) {
    test(`accessibilité (axe), thème ${theme}`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: theme });
      await page.goto('./');
      const resultat = await new AxeBuilder({ page }).analyze();
      expect(
        resultat.violations.map((v) => `${v.id} : ${v.nodes.map((n) => n.target).join(', ')}`),
      ).toEqual([]);
    });
  }

  for (const largeur of [390, 360, 820, 1280]) {
    test(`pas de défilement horizontal à ${largeur} px`, async ({ page }) => {
      await page.setViewportSize({ width: largeur, height: 800 });
      await page.goto('./');
      const deborde = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      expect(deborde).toBe(false);
    });
  }
});

test.describe('Documentation', () => {
  test('est reliée au catalogue et son sommaire mène à chaque section', async ({ page }) => {
    await page.goto('./');
    await page.locator('.heros').getByRole('link', { name: 'Documentation' }).click();
    await expect(page).toHaveTitle('Documentation · Skills IA');
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(
      'Installer et utiliser les skills',
    );
    const cibles = await page
      .locator('.sommaire a')
      .evaluateAll((liens) => liens.map((a) => a.getAttribute('href')));
    expect(cibles.length).toBeGreaterThan(8);
    for (const cible of cibles) await expect(page.locator(cible), cible).toHaveCount(1);
    // Les icônes du sprite sont remplacées à la construction.
    await expect(page.locator('#i-arrow-left')).toHaveCount(1);
  });

  test('donne les commandes des installeurs, à copier', async ({ page }) => {
    await page.goto('documentation.html');
    const commandes = (await page.locator('.commande code').allTextContents()).map((c) =>
      c.replace(/\s+/g, ' ').trim(),
    );
    expect(commandes).toContain('irm https://gharel.github.io/skills/installer.ps1 | iex');
    expect(commandes).toContain('curl -fsSL https://gharel.github.io/skills/installer.sh | sh');
    expect(commandes).toContain(
      'curl -fsSL https://gharel.github.io/skills/installer.sh | SKILLS_CATEGORIE=pro sh',
    );
    await expect(page.locator('.commande .copier')).toHaveCount(commandes.length);
  });

  test('copie une commande coupée par le formatage sur une seule ligne', async ({
    page,
    context,
  }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    await page.goto('documentation.html');
    const bloc = page.locator('.commande', { hasText: 'SKILLS_CATEGORIE=pro sh' });
    await bloc.getByRole('button', { name: 'Copier' }).click();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
      'curl -fsSL https://gharel.github.io/skills/installer.sh | SKILLS_CATEGORIE=pro sh',
    );
  });

  for (const theme of ['light', 'dark']) {
    test(`accessibilité (axe), thème ${theme}`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: theme });
      await page.goto('documentation.html');
      const resultat = await new AxeBuilder({ page }).analyze();
      expect(
        resultat.violations.map((v) => `${v.id} : ${v.nodes.map((n) => n.target).join(', ')}`),
      ).toEqual([]);
    });
  }

  for (const largeur of [360, 820, 1280]) {
    test(`pas de défilement horizontal à ${largeur} px`, async ({ page }) => {
      await page.setViewportSize({ width: largeur, height: 800 });
      await page.goto('documentation.html');
      const deborde = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      expect(deborde).toBe(false);
    });
  }
});
