import { test, expect } from '@playwright/test';
import { readdirSync, readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';

const read = name => JSON.parse(readFileSync(`docs/data/${name}.json`, 'utf8'));
const census = read('ha-interface-coverage');
const terms = read('ha-terminology');
const route = path => `/docs/build${path}`;
const noOverflow = async page => expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
const openAll = async (page, selector) => {
  // Exercise the semantic disclosure control, including keyboard operation.
  for (const detail of await page.locator(selector).all()) {
    if (await detail.getAttribute('open') !== null) continue;
    await detail.locator(':scope > summary').focus();
    await page.keyboard.press('Enter');
    await expect(detail).toHaveAttribute('open', '');
  }
};

test('every interface registry remains readable when expanded on a narrow screen', async ({ page }) => {
  test.setTimeout(90000);
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(route('/home-assistant/interface-coverage.html'));
  await openAll(page, 'details[id^="registry-"]');
  await openAll(page, 'details[id^="registry-"] details');
  await expect(page.locator('tr[id^="coverage-"]')).toHaveCount(census.entries.length);
  await noOverflow(page);
  const first = page.locator('tr[id^="coverage-"]').first();
  await expect(first.getByRole('link', { name: /^Task pattern:/ })).toBeVisible();
  await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
  await noOverflow(page);
  const results = await new AxeBuilder({ page }).exclude('iframe').analyze();
  expect(results.violations.map(({ id, nodes }) => ({ id, targets: nodes.map(node => node.target) }))).toEqual([]);
});

test('/content/style-guides/technical-a-to-z.html: every term and native label can be read without horizontal page scrolling', async ({ page }) => {
  test.setTimeout(300000);
  const path = '/content/style-guides/technical-a-to-z.html';
  // The lexicon is published one letter per page; the index page is the first letter.
  const pages = [path, ...readdirSync('docs/build/content/style-guides')
    .filter(name => /^technical-a-to-z-[a-z0-9]+\.html$/.test(name)).sort().map(name => `/content/style-guides/${name}`)];
  const expected = terms.terms.filter(term => term.local_path?.split('#')[0] === path);
  // Card types, card features, selector types and settings destinations are grouped into one entry each,
  // with a table row for every term. Every term still has its own anchor.
  const grouped = new Set(['card-types', 'card-features', 'selector-types', 'settings-labels']);
  const single = expected.filter(term => !grouped.has(term.category));
  const totals = { entries: 0, rows: 0, natives: 0 };
  await page.setViewportSize({ width: 320, height: 900 });
  for (const letterPage of pages) {
    await page.goto(route(letterPage));
    totals.entries += await page.locator('.lexicon-entry').count();
    totals.rows += await page.locator('tr[id^="ht-card-"], tr[id^="ht-feature-"], tr[id^="ht-selector-"], tr[id^="ht-settings-"]').count();
    await openAll(page, 'details');
    await noOverflow(page);
    totals.natives += await page.locator('tr[id^="ht-native-"]').count();
    await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
    await noOverflow(page);
    const results = await new AxeBuilder({ page }).exclude('iframe').analyze();
    expect(results.violations.map(({ id, nodes }) => ({ id, targets: nodes.map(node => node.target) })), letterPage).toEqual([]);
    await page.evaluate(() => { document.documentElement.style.fontSize = ''; });
  }
  expect(totals.entries).toBe(single.length + grouped.size);
  expect(totals.rows).toBe(expected.length - single.length);
  expect(totals.natives).toBe(terms.native_values.length);
});

test('complete interface and terminology records are linked from the visible audit page', async ({ page, request }) => {
  await page.goto(route('/community/home-assistant-coverage-audit.html'));
  for (const path of ['/home-assistant/interface-coverage.html', '/content/style-guides/technical-a-to-z.html', '/community/uk-design-system-review.html', '/components/sliders.html']) {
    const link = page.locator('main a').filter({ hasText: /./ });
    expect(await link.evaluateAll((nodes, suffix) => nodes.some(node => new URL(node.href).pathname.endsWith(suffix)), path)).toBe(true);
    await expect(page.locator(`main a[href$="${path.split('/').pop()}"]`).first()).toBeVisible();
    expect((await request.get(route(path))).ok()).toBe(true);
  }
});
