import { defineConfig, devices } from '@playwright/test';

// Port dédié aux tests (PORT_E2E pour en changer si npm run dev tourne déjà ailleurs).
const PORT = Number(process.env.PORT_E2E) || 4183;

export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: `http://localhost:${PORT}/`,
    ...devices['Desktop Chrome'],
  },
  webServer: {
    // Le site est construit par npm run construire avant les tests.
    command: 'node outils/dev.mjs',
    env: { PORT: String(PORT) },
    url: `http://localhost:${PORT}/`,
    reuseExistingServer: false,
  },
});
