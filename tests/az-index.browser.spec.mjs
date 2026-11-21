// Patterns index: the same paged A to Z template as Components.
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const index = '/docs/build/patterns/index.html';

test('patterns are split by letter and the first letter page is the index', async ({ page }) => {
  await page.goto(index);
  const bar = page.getByRole('navigation', { name: 'A to Z navigation' });
  await expect(bar.locator('ol.style-a-z > li')).toHaveCount(27);
  await expect(bar.locator('a[aria-current="page"]')).toHaveText('A');
  const entries = page.locator('[data-az-list] [data-az-entry]');
  expect(await entries.count()).toBeGreaterThan(0);
  for (const title of await entries.evaluateAll(nodes => nodes.map(node => node.dataset.azEntry))) expect(title.match(/[A-Za-z0-9]/)?.[0].toUpperCase()).toBe('A');
});

test('the bar and the pager step through every populated letter in order', async ({ page }) => {
  await page.goto(index);
  const bar = page.getByRole('navigation', { name: 'A to Z navigation' });
  const letters = await bar.locator('ol.style-a-z > li a').evaluateAll(nodes => nodes.map(node => node.textContent));
  const pager = page.getByRole('navigation', { name: 'Patterns pages' });
  for (const letter of letters.slice(1)) {
    await pager.getByRole('link', { name: /^Next/ }).click();
    await expect(page.locator('h2.style-a-z__letter')).toHaveText(letter);
    await expect(bar.locator('a[aria-current="page"]')).toHaveText(letter);
    await expect(pager.locator('li').nth(2)).toContainText(letter);
    for (const title of await page.locator('[data-az-entry]').evaluateAll(nodes => nodes.map(node => node.dataset.azEntry))) {
      const first = title.normalize('NFD').replace(/\p{Mn}/gu, '').match(/[A-Za-z0-9]/)?.[0];
      expect(/\d/.test(first) ? '0-9' : first.toUpperCase()).toBe(letter);
    }
  }
  await expect(pager.locator('li').nth(3).locator('a')).toHaveCount(0);
  await expect(pager.locator('li').nth(4).locator('a')).toHaveCount(0);
});

test('every pattern appears on exactly one letter page and the pages reflow at 320px', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto(index);
  const bar = page.getByRole('navigation', { name: 'A to Z navigation' });
  const hrefs = await bar.locator('ol.style-a-z > li a').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
  const seen = [];
  for (const href of hrefs) {
    await page.goto(new URL(href, `http://127.0.0.1:4173${index}`).pathname);
    seen.push(...await page.locator('[data-az-entry]').evaluateAll(nodes => nodes.map(node => node.dataset.azEntry)));
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect((await new AxeBuilder({ page }).include('main').analyze()).violations).toEqual([]);
  }
  expect(new Set(seen).size).toBe(seen.length);
});

test('the two A to Z style guides are paged the same way and entry links reach the right letter', async ({ page }) => {
  for (const name of ['a-to-z', 'technical-a-to-z']) {
    await page.goto(`/docs/build/content/style-guides/${name}.html`);
    const bar = page.getByRole('navigation', { name: 'A to Z navigation' });
    await expect(bar.locator('ol.style-a-z > li')).toHaveCount(27);
    await expect(bar.locator('a[aria-current="page"]')).toHaveText('A');
    await expect(page.locator('h2.style-a-z__letter')).toHaveCount(1);
    const pager = page.getByRole('navigation', { name: /pages$/ });
    await pager.getByRole('link', { name: /^Next/ }).click();
    await expect(page.locator('h2.style-a-z__letter')).toHaveText('B');
    await expect(page).toHaveURL(new RegExp(`${name}-b\\.html$`));
    await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
    await page.reload();
    await expect(page.locator('h2.style-a-z__letter')).toHaveText('B');
  }
  // A link to an entry on another letter opens that letter page at the entry.
  await page.goto('/docs/build/content/style-guides/a-to-z-e.html');
  await page.locator('a[href="technical-a-to-z-e.html#ht-entity"]').first().click();
  await expect(page).toHaveURL(/technical-a-to-z-e\.html#ht-entity$/);
  await expect(page.locator('#ht-entity')).toBeVisible();
});
