// Components index, A to Z jump bar, combobox and sidebar.
// Every expectation is derived from the locked inventory, so the interface and
// the machine-readable index cannot drift from docs/data/component-inventory.json.
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { existsSync, readFileSync } from 'node:fs';
import YAML from 'yaml';

const inventory = JSON.parse(readFileSync('docs/data/component-inventory.json', 'utf8'));
const parents = inventory.parents;
const index = '/docs/build/components/index.html';
const sourceFor = route => ['.html.md.erb', '.html.erb', '.html.md'].map(suffix => `docs/source${route.replace(/\.html$/, '')}${suffix}`).find(existsSync);
const available = parents.filter(parent => sourceFor(parent.route));
// A page links to an element's anchor only once it declares the component schema.
const declares = parent => {
  const source = sourceFor(parent.route);
  return Boolean(source && YAML.parse(readFileSync(source, 'utf8').split(/^---$/m)[1]).component);
};
const anchorPattern = (parent, anchor) => declares(parent) ? `#${anchor}$` : '$';
const letters = [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'];
const used = new Set(parents.map(parent => parent.letter));
// Locale-independent order (lower-case code points), the order the inventory is locked in.
const byName = (a, b) => (a.toLowerCase() < b.toLowerCase() ? -1 : a.toLowerCase() > b.toLowerCase() ? 1 : 0);

test('the inventory is complete, alphabetical and owns each element once', () => {
  expect(parents).toHaveLength(144);
  expect(parents.map(parent => parent.parent)).toEqual([...parents.map(parent => parent.parent)].sort(byName));
  const owned = parents.flatMap(parent => parent.children.flatMap(child => [child, ...(child.grandchildren || [])]))
    .filter(item => !item.cross_reference).map(item => item.name);
  expect(new Set(owned).size).toBe(owned.length);
});

test('the A to Z jump bar follows the hero and matches the Lexicon markup', async ({ page }) => {
  await page.goto(index);
  const nav = page.getByRole('navigation', { name: 'A to Z navigation' });
  await expect(nav).toBeVisible();
  const items = nav.locator('ol.style-a-z > li');
  await expect(items).toHaveCount(26);
  for (const [position, letter] of letters.entries()) {
    const item = items.nth(position);
    if (used.has(letter)) {
      const link = item.locator('a.govuk-link');
      await expect(link).toHaveText(letter);
      await expect(link).toHaveAttribute('href', `#${letter.toLowerCase()}`);
      await expect(page.locator(`h2.style-a-z__letter#${letter.toLowerCase()}`)).toHaveText(letter);
    } else {
      await expect(item.locator('span.style-a-z__empty')).toHaveText(letter);
      await expect(item.locator('a')).toHaveCount(0);
    }
  }
  // The jump bar comes straight after the hero, before the search and the list.
  const order = await page.locator('main').evaluate(main => {
    const nav = main.querySelector('nav[aria-label="A to Z navigation"]');
    const search = main.querySelector('[data-component-search]');
    const list = main.querySelector('[data-component-list]');
    return [nav.compareDocumentPosition(search) & Node.DOCUMENT_POSITION_FOLLOWING, search.compareDocumentPosition(list) & Node.DOCUMENT_POSITION_FOLLOWING];
  });
  expect(order.every(Boolean)).toBe(true);
});

test('the A to Z list names every parent once, links published pages and marks the rest', async ({ page }) => {
  await page.goto(index);
  const entries = page.locator('[data-component-list] [data-component-parent]');
  await expect(entries).toHaveCount(parents.length);
  expect(await entries.evaluateAll(nodes => nodes.map(node => node.dataset.componentParent))).toEqual(parents.map(parent => parent.parent));
  for (const parent of parents) {
    const entry = page.locator(`[data-component-parent="${parent.parent.replace(/"/g, '\\"')}"]`);
    if (available.includes(parent)) await expect(entry.locator('a')).toHaveAttribute('href', parent.route.replace('/components/', ''));
    else {
      await expect(entry.locator('a')).toHaveCount(0);
      await expect(entry).toContainText('Specification not yet published');
    }
  }
});

test('the combobox finds parents, elements and variants and goes to the owning anchor', async ({ page }) => {
  const requests = [];
  page.on('request', request => { if (!request.url().endsWith('.html') && request.resourceType() === 'fetch') requests.push(request.url()); });
  await page.goto(index);
  const box = page.getByRole('combobox', { name: 'Find a component or element' });
  await expect(box).toHaveAttribute('aria-expanded', 'false');
  await box.fill('ha-button');
  await expect(box).toHaveAttribute('aria-expanded', 'true');
  const listbox = page.getByRole('listbox');
  await expect(listbox.getByRole('option', { name: /^ha-button\b/ }).first()).toBeVisible();
  await expect(page.locator('[data-component-search-status]')).toHaveText(/\d+ results?/);
  await box.press('ArrowDown');
  const active = await box.getAttribute('aria-activedescendant');
  expect(active).toBeTruthy();
  await expect(page.locator(`#${active}`)).toHaveAttribute('aria-selected', 'true');
  await box.press('Escape');
  await expect(box).toHaveAttribute('aria-expanded', 'false');

  // A child element resolves to its anchor on the owning page.
  await box.fill('<details>');
  await listbox.getByRole('option', { name: /^<details>/ }).first().click();
  const accordion = parents.find(parent => parent.parent === 'Accordion');
  await expect(page).toHaveURL(new RegExp(`components/accordion\\.html${anchorPattern(accordion, 'child-details')}`));

  // A parent that has no page yet resolves to its entry in the A to Z list.
  await page.goto(index);
  await page.getByRole('combobox', { name: 'Find a component or element' }).fill('hui-tile-card');
  await page.getByRole('combobox', { name: 'Find a component or element' }).press('ArrowDown');
  await page.getByRole('combobox', { name: 'Find a component or element' }).press('Enter');
  const tile = parents.find(parent => parent.parent === 'Tile Card');
  await expect(page).toHaveURL(available.includes(tile) ? new RegExp(`tile-card\\.html${anchorPattern(tile, 'child-hui-tile-card')}`) : /index\.html#parent-tile-card$/);

  // An honest empty result.
  await page.getByRole('combobox', { name: 'Find a component or element' }).fill('zzzz-no-such-element');
  await expect(page.locator('[data-component-search-status]')).toHaveText('No components or elements match.');
  expect(requests).toEqual([]);
});

test('the index passes automated accessibility checks and reflows at 320px', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto(index);
  await page.getByRole('combobox', { name: 'Find a component or element' }).fill('button');
  expect((await new AxeBuilder({ page }).include('main').analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('without JavaScript the full A to Z list remains and the combobox is not offered', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  try {
    await page.goto(`http://127.0.0.1:4173${index}`);
    await expect(page.locator('[data-component-search]')).toBeHidden();
    await expect(page.locator('[data-component-list] [data-component-parent]')).toHaveCount(parents.length);
  } finally { await context.close(); }
});

test('the sidebar is one flat A to Z list of published parents with the current page marked', async ({ page }) => {
  await page.goto('/docs/build/components/buttons.html');
  const sidebar = page.getByRole('navigation', { name: 'Pages in this section' });
  await expect(sidebar.locator('.app-subnav__theme')).toHaveCount(0);
  await expect(sidebar.locator('ul.app-subnav__section')).toHaveCount(1);
  const names = await sidebar.locator('.app-subnav__section-item a').allTextContents();
  expect(names.map(name => name.trim())).toEqual(available.map(parent => parent.parent));
  await expect(sidebar.locator('.app-subnav__section-item--current > a[aria-current="page"]')).toHaveText('Button');
});

test('the machine-readable index lists every parent, child and grandchild with its owner', async ({ request }) => {
  const response = await request.get('/docs/build/reference/component-index.json');
  expect(response.ok()).toBe(true);
  const data = await response.json();
  expect(data.parents).toHaveLength(144);
  const expected = parents.flatMap(parent => [parent.parent, ...parent.children.flatMap(child => [child.name, ...(child.grandchildren || []).map(item => item.name)])]);
  expect(data.entries.map(entry => entry.name)).toEqual(expected);
  for (const entry of data.entries) {
    const owner = parents.find(parent => parent.parent === entry.owner);
    expect(owner, entry.name).toBeTruthy();
    expect(entry.available).toBe(available.includes(owner));
    expect(entry.anchor_published).toBe(declares(owner));
  }
});
