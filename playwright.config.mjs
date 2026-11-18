import { defineConfig } from '@playwright/test';

// The pull-request smoke run skips the four slowest specs, which check every
// guide page, every remediation record, coverage tables and the energy chart
// matrix. They take about 80% of the browser time and run nightly instead.
const smoke = process.env.CIVICA_BROWSER_SMOKE === '1';

export default defineConfig({
  testDir: './tests', testMatch: '**/*.browser.spec.mjs', fullyParallel: true,
  testIgnore: smoke ? ['**/docs.browser.spec.mjs', '**/remediation.browser.spec.mjs', '**/coverage.browser.spec.mjs', '**/energy-charts.browser.spec.mjs'] : undefined,
  // Hosted runners have 4 vCPUs; the default would use only 2.
  workers: process.env.CI ? 4 : undefined,
  use: { baseURL: 'http://127.0.0.1:4173', headless: true, channel: process.platform === 'darwin' ? 'chrome' : undefined, screenshot: 'only-on-failure', trace: 'off' },
  webServer: { command: 'python3 -m http.server 4173 --bind 127.0.0.1', url: 'http://127.0.0.1:4173/ui/dev/', reuseExistingServer: !process.env.CI },
});
