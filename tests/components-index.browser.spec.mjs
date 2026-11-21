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
// Pages outside the inventory stay in the sidebar until Branch 2 retires them (pinned in scripts/check-components.mjs).
const legacy = ['chart-examples', 'controls', 'details', 'devices', 'error-summary', 'example', 'expander',
  'generic-header', 'password-input', 'review-date', 'status', 'warning-callout']
  .map(name => `/components/${name}.html`).filter(sourceFor)
  .map(route => ({ route, title: YAML.parse(readFileSync(sourceFor(route), 'utf8').split(/^---$/m)[1]).title }));
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

const bucketOf = name => {
  const first = name.normalize('NFD').replace(/\p{Mn}/gu, '').match(/[A-Za-z0-9]/)?.[0];
  return /\d/.test(first) ? '0-9' : first.toUpperCase();
};
const buckets = [...letters, '0-9'];
const populated = buckets.filter(bucket => parents.some(parent => bucketOf(parent.parent) === bucket));
const pageFor = bucket => (bucket === populated[0] ? index : `/docs/build/components/a-z/${bucket.toLowerCase()}.html`);

test('the A to Z bar lists every letter and 0-9, marks the current one and mutes the empty ones', async ({ page }) => {
  for (const current of populated) {
    await page.goto(pageFor(current));
    const nav = page.getByRole('navigation', { name: 'A to Z navigation' });
    await expect(nav).toBeVisible();
    const items = nav.locator('ol.style-a-z > li');
    await expect(items).toHaveCount(27);
    for (const [position, bucket] of buckets.entries()) {
      const item = items.nth(position);
      if (bucket === current) {
        const link = item.locator('a[aria-current="page"]');
        await expect(link).toHaveText(bucket);
        // White on the blue used by the letter heading.
        const styles = await link.evaluate(node => { const style = getComputedStyle(node); return [style.color, style.backgroundColor]; });
        const heading = await page.locator('h2.style-a-z__letter').evaluate(node => { const style = getComputedStyle(node); return [style.color, style.backgroundColor]; });
        expect(styles).toEqual(heading);
      } else if (populated.includes(bucket)) {
        await expect(item.locator('a.govuk-link')).toHaveText(bucket);
        await expect(item.locator('a[aria-current]')).toHaveCount(0);
      } else {
        await expect(item.locator('span.style-a-z__empty')).toHaveText(bucket);
        await expect(item.locator('a')).toHaveCount(0);
      }
    }
    await expect(page.locator('h2.style-a-z__letter')).toHaveText(current);
  }
});

test('the bar and the pager move between letter pages and stay in step', async ({ page }) => {
  await page.goto(index);
  const pager = page.getByRole('navigation', { name: 'Components pages' });
  await expect(pager.locator('li')).toHaveCount(5);
  await expect(pager.locator('li').nth(0)).toHaveText('First');
  await expect(pager.locator('li').nth(0).locator('a')).toHaveCount(0);
  await expect(pager.locator('li').nth(1).locator('a')).toHaveCount(0);
  await expect(pager.locator('li').nth(2)).toContainText(populated[0]);
  await pager.getByRole('link', { name: /^Next/ }).click();
  await expect(page).toHaveURL(new RegExp(`${pageFor(populated[1]).replace(/\./g, '\\.')}$`));
  await expect(page.locator('h2.style-a-z__letter')).toHaveText(populated[1]);
  await expect(page.getByRole('navigation', { name: 'A to Z navigation' }).locator('a[aria-current="page"]')).toHaveText(populated[1]);
  await pager.getByRole('link', { name: /^Last/ }).click();
  await expect(page.locator('h2.style-a-z__letter')).toHaveText(populated.at(-1));
  await expect(pager.locator('li').nth(3).locator('a')).toHaveCount(0);
  await expect(pager.locator('li').nth(4).locator('a')).toHaveCount(0);
  await pager.getByRole('link', { name: /^Previous/ }).click();
  await expect(page.locator('h2.style-a-z__letter')).toHaveText(populated.at(-2));
  await pager.getByRole('link', { name: /^First/ }).click();
  await expect(page.locator('h2.style-a-z__letter')).toHaveText(populated[0]);
  // A letter page can be opened and refreshed directly.
  await page.goto(pageFor('T'));
  await page.reload();
  await expect(page.locator('h2.style-a-z__letter')).toHaveText('T');
});

test('each letter page lists exactly the parents that start with that letter, links published pages and marks the rest', async ({ page }) => {
  for (const bucket of populated) {
    await page.goto(pageFor(bucket));
    const wanted = parents.filter(parent => bucketOf(parent.parent) === bucket);
    const entries = page.locator('[data-az-list] [data-az-entry]');
    await expect(entries).toHaveCount(wanted.length);
    expect(await entries.evaluateAll(nodes => nodes.map(node => node.dataset.azEntry))).toEqual(wanted.map(parent => parent.parent));
    for (const parent of wanted) {
      const entry = page.locator(`[data-az-entry="${parent.parent.replace(/"/g, '\\"')}"]`);
      if (available.includes(parent)) await expect(entry.locator('a')).toHaveAttribute('href', new RegExp(`${parent.route.replace('/components/', '').replace(/\./g, '\\.')}$`));
      else {
        await expect(entry.locator('a')).toHaveCount(0);
        await expect(entry).toContainText('Specification not yet published');
      }
    }
  }
});

test('the combobox finds parents, elements and variants and goes to the owning anchor', async ({ page }) => {
  await page.goto(index);
  await page.waitForLoadState('networkidle');
  // Searching uses the embedded data only: no request of any kind after the page has loaded.
  // The browser may fetch the favicon late on its own; that is not the search.
  const requests = [];
  page.on('request', request => { if (!request.url().endsWith('/favicon.svg')) requests.push(request.url()); });
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

  // An honest empty result.
  await box.fill('zzzz-no-such-element');
  await expect(page.locator('[data-component-search-status]')).toHaveText('No components or elements match.');
  await expect(box).toHaveAttribute('aria-expanded', 'false');
  expect(requests).toEqual([]);

  // A child element resolves to its anchor on the owning page.
  await box.fill('<details>');
  await listbox.getByRole('option', { name: /^<details>/ }).first().click();
  const accordion = parents.find(parent => parent.parent === 'Accordion');
  await expect(page).toHaveURL(new RegExp(`components/accordion\\.html${anchorPattern(accordion, 'child-details')}`));

  // A parent that has no page yet resolves to its entry in the A to Z list, and focus moves there.
  await page.goto(index);
  const again = page.getByRole('combobox', { name: 'Find a component or element' });
  await again.fill('hui-tile-card');
  await again.press('ArrowDown');
  await again.press('Enter');
  const tile = parents.find(parent => parent.parent === 'Tile Card');
  if (available.includes(tile)) await expect(page).toHaveURL(new RegExp(`tile-card\\.html${anchorPattern(tile, 'child-hui-tile-card')}`));
  else {
    await expect(page).toHaveURL(/components\/a-z\/t\.html#parent-tile-card$/);
    await expect(page.locator('#parent-tile-card')).toBeFocused();
  }
});

test('a cross-referenced element appears once, under its owner, naming the other pages', async ({ page }) => {
  await page.goto(index);
  const box = page.getByRole('combobox', { name: 'Find a component or element' });
  const exact = name => page.getByRole('listbox').locator('.c-component-search__option', { has: page.locator('.c-component-search__name', { hasText: new RegExp(`^${name}$`) }) });
  for (const item of parents.flatMap(parent => parent.children.flatMap(child => [child, ...(child.grandchildren || [])]).filter(entry => entry.cross_reference).map(entry => ({ parent, entry })))) {
    await box.fill(item.entry.name);
    const options = exact(item.entry.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    await expect(options).toHaveCount(1);
    await expect(options).toContainText(`in ${item.entry.cross_reference.parent}`);
    await expect(options).toContainText(item.parent.parent);
    if (item.entry.note) await expect(options).toContainText(item.entry.note);
  }
});

test('the combobox keyboard follows the ARIA combobox pattern', async ({ page }) => {
  await page.goto(index);
  const box = page.getByRole('combobox', { name: 'Find a component or element' });
  await box.fill('ha-');
  // More than 50 matches: the first 50 are shown and the status says so.
  await expect(page.getByRole('listbox').getByRole('option')).toHaveCount(50);
  await expect(page.locator('[data-component-search-status]')).toHaveText(/^\d+ results, showing the first 50\.$/);
  await box.press('ArrowUp');
  await expect(box).toHaveAttribute('aria-activedescendant', 'component-option-49');
  await box.press('ArrowDown');
  await expect(box).toHaveAttribute('aria-activedescendant', 'component-option-0');
  for (const key of ['Home', 'End', 'ArrowLeft', 'ArrowRight']) {
    await box.press('ArrowDown');
    await expect(box).toHaveAttribute('aria-activedescendant', /component-option-\d+/);
    await box.press(key);
    await expect(box).not.toHaveAttribute('aria-activedescendant');
    await expect(box).toBeFocused();
    await expect(box).toHaveAttribute('aria-expanded', 'true');
  }
  await box.press('Escape');
  await expect(box).toHaveAttribute('aria-expanded', 'false');
  await box.press('Escape');
  await expect(box).toHaveValue('');
});

test('the index passes automated accessibility checks and reflows at 320px', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto(index);
  await page.getByRole('combobox', { name: 'Find a component or element' }).fill('button');
  expect((await new AxeBuilder({ page }).include('main').analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('without JavaScript the A to Z pages remain and the combobox is not offered', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  try {
    await page.goto(`http://127.0.0.1:4173${index}`);
    await expect(page.locator('[data-component-search]')).toBeHidden();
    await expect(page.locator('[data-az-list] [data-az-entry]')).toHaveCount(parents.filter(parent => bucketOf(parent.parent) === populated[0]).length);
  } finally { await context.close(); }
});

test('the sidebar is the shared section menu: Introduction first, the current page marked, its branch open', async ({ page }) => {
  for (const [route, current] of [['/components/buttons.html', 'Buttons'], ...legacy.map(item => [item.route, item.title])]) {
    await page.goto(`/docs/build${route}`);
    const sidebar = page.getByRole('navigation', { name: 'Pages in this section' });
    await expect(sidebar.locator('.app-subnav__theme')).toHaveCount(0);
    await expect(sidebar.locator('ul.app-subnav__tree')).toHaveCount(1);
    await expect(sidebar.locator('.app-subnav__tree > li').first()).toHaveText('Introduction');
    await expect(sidebar.locator('a[aria-current="page"]'), route).toHaveCount(1);
  }
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
