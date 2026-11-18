// Colour pages: swatches render from the GOV.UK record and every value can be
// copied with a working, accessible button.
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync } from 'node:fs';

const data = JSON.parse(readFileSync('docs/data/govuk-brand-colours.json', 'utf8'));
const page = name => `/docs/build/styles/colour-${name}.html`;
const ids = name => data.pages[name].palette.flatMap(group => group.colours);

for (const name of ['web', 'app', 'print']) {
  test(`${name} colours show every GOV.UK colour in order`, async ({ page: browser }) => {
    await browser.goto(page(name));
    const names = await browser.locator('.c-swatch-list').first().locator('xpath=ancestor::main').locator('.c-swatch__name').allTextContents();
    expect(names.slice(0, ids(name).length).map(text => text.trim())).toEqual(ids(name).map(id => data.colours[id].name));
  });

  test(`${name} colours pass automated accessibility checks and reflow at 320px`, async ({ page: browser }) => {
    await browser.setViewportSize({ width: 320, height: 800 });
    await browser.goto(page(name));
    expect((await new AxeBuilder({ page: browser }).include('main').analyze()).violations).toEqual([]);
    expect(await browser.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
}

test('a copy button copies the exact value and says so', async ({ page: browser, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await browser.goto(page('web'));
  const button = browser.getByRole('button', { name: 'Copy hex #1D70B8 for Primary blue', exact: true });
  await expect(button).toBeVisible();
  await button.focus();
  await browser.keyboard.press('Enter');
  expect(await browser.evaluate(() => navigator.clipboard.readText())).toBe('#1D70B8');
  await expect(browser.locator('[data-copy-value-status]')).toHaveText('Copied hex #1D70B8 for Primary blue');
  await expect(button).toHaveAttribute('data-copied', 'true');
  await expect(button).not.toHaveAttribute('data-copied', /.*/, { timeout: 4000 });

  // The same value copied from another colour is still announced, because the
  // status names the colour as well as the value.
  await browser.getByRole('button', { name: 'Copy hex #1D70B8 for brand', exact: true }).click();
  await expect(browser.locator('[data-copy-value-status]')).toHaveText('Copied hex #1D70B8 for brand');

  await browser.goto(page('print'));
  await browser.getByRole('button', { name: 'Copy Pantone 7461 C for Primary blue' }).click();
  expect(await browser.evaluate(() => navigator.clipboard.readText())).toBe('7461 C');
});

test('a failed copy tells the person to select the value instead', async ({ page: browser }) => {
  await browser.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', { value: { writeText: () => Promise.reject(new Error('denied')) } });
  });
  await browser.goto(page('web'));
  await browser.getByRole('button', { name: 'Copy RGB 29 112 184 for Primary blue' }).click();
  await expect(browser.locator('[data-copy-value-status]')).toHaveText('Copy failed. Select 29 112 184 and copy it instead.');
});

test('without JavaScript the values remain and no copy button is offered', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const noScript = await context.newPage();
  try {
    await noScript.goto(`http://127.0.0.1:4173${page('web')}`);
    await expect(noScript.locator('.c-copy-value').first()).toBeHidden();
    await expect(noScript.getByText('#1D70B8', { exact: true }).first()).toBeVisible();
  } finally { await context.close(); }
});
