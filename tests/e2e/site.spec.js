import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const SKILLS = ['skazy-plan-formation', 'skazy-support-formation', 'skazy-quiz'];

test.describe('Catalogue', () => {
  test('présente les trois skills Pro dans l’ordre de la chaîne, et les catégories à venir', async ({
    page,
  }) => {
    await page.goto('./');
    await expect(page).toHaveTitle('Skills IA · Skazy Formation');
    const cartes = page.locator('.carte[data-skill]');
    await expect(cartes).toHaveCount(3);
    expect(await cartes.evaluateAll((l) => l.map((c) => c.dataset.skill))).toEqual(SKILLS);
    await expect(page.locator('#categorie-unc')).toBeVisible();
    await expect(page.locator('#categorie-perso')).toBeVisible();
    await expect(page.locator('.carte--vide')).toHaveCount(2);
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
    for (const fichier of ['installer.ps1', 'installer.sh', 'sources/index.json']) {
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

test.describe('Atelier', () => {
  test('accessibilité (axe)', async ({ page }) => {
    await page.goto('atelier/');
    const resultat = await new AxeBuilder({ page }).analyze();
    expect(resultat.violations.map((v) => v.id)).toEqual([]);
  });

  const CAS = [
    ['quiz', ['.skazy-quiz.json', '.kahoot.xlsx', '.google-forms.gs', '.corrige.md']],
    ['plan', ['.html', '.docx']],
    ['support', ['.html', '.pptx']],
  ];
  for (const [exemple, extensions] of CAS) {
    test(`produit les fichiers de l’exemple « ${exemple} » dans le navigateur`, async ({
      page,
    }) => {
      test.setTimeout(240_000);
      await page.goto('atelier/');
      await page.getByRole('button', { name: exemple, exact: true }).click();
      await expect(page.locator('#formats')).toBeVisible();
      await page.getByRole('button', { name: 'Produire les fichiers' }).click();
      await expect(page.locator('#etat')).toHaveText('Fichiers prêts.', { timeout: 220_000 });
      const noms = await page
        .locator('#fichiers a[download]')
        .evaluateAll((l) => l.map((a) => a.download));
      for (const extension of extensions)
        expect(
          noms.some((n) => n.endsWith(extension)),
          extension,
        ).toBe(true);
      if (exemple === 'quiz')
        await expect(page.getByRole('link', { name: 'Ouvrir dans le Quiz' })).toHaveAttribute(
          'href',
          /gharel\.github\.io\/quiz\/#\/partage\?q=/,
        );
    });
  }
});
