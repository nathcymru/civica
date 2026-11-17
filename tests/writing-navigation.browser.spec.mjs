import { test, expect } from '@playwright/test';
import { readFileSync, readdirSync } from 'node:fs';
import YAML from 'yaml';

const frontmatter = source => YAML.parse(source.match(/^---\r?\n([\s\S]*?)\r?\n---/)[1]);
const contentPages = readdirSync('docs/source/content', { recursive: true }).filter(name => name.endsWith('.html.md.erb')).map(name => ({
  path: `/content/${name.replace(/\.md\.erb$/, '')}`,
  data: frontmatter(readFileSync(`docs/source/content/${name}`, 'utf8')),
}));
const writingPaths = [...contentPages.map(page => page.path), '/styles/content.html'].sort();
const relativePaths = nodes => nodes.map(node => new URL(node.href).pathname.replace(/^\/docs\/build/, '')).sort();
const reflow = async page => expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);

test('all existing writing URLs belong to one top-level section', () => {
  const navigation = YAML.parse(readFileSync('docs/data/navigation.yml', 'utf8')).sections;
  expect(navigation.filter(section => section.id === 'content')).toEqual([{ id: 'content', title: 'Writing guide', path: '/content/index.html' }]);
  expect(new Set(navigation.map(section => section.path)).size).toBe(navigation.length);
  for (const page of contentPages) expect(page.data.section, page.path).toBe('content');
  const legacy = frontmatter(readFileSync('docs/source/styles/content.html.md.erb', 'utf8'));
  expect(legacy.section).toBe('content');
  expect(legacy.group).toBe('Quick reference');
});

test('writing pages have the correct active navigation, breadcrumbs and a single section-home link', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  for (const path of ['/content/index.html', '/content/writing-guidelines/clear-language.html', '/content/style-guides/technical-a-to-z.html', '/styles/content.html']) {
    const response = await page.goto(`/docs/build${path}`);
    expect(response.ok(), path).toBe(true);
    const main = page.getByRole('navigation', { name: 'Main navigation' });
    await expect(main.getByRole('link', { name: 'Writing guide', exact: true })).toHaveAttribute('aria-current', 'true');
    await expect(main.locator('a[aria-current]')).toHaveCount(1);
    await expect(main.getByRole('link', { name: 'Styles', exact: true })).not.toHaveAttribute('aria-current');
    // As on the GOV.UK Design System, the sidebar lists pages in themed groups and
    // does not repeat the section home, which is reached from the breadcrumb.
    const sidebar = page.getByRole('navigation', { name: 'Pages in this section' });
    expect((await sidebar.locator('a').evaluateAll(relativePaths)).filter(path => path === '/content/index.html')).toHaveLength(0);
    await expect(sidebar.locator('a[aria-current="page"]')).toHaveCount(path === '/content/index.html' ? 0 : 1);
    await expect(sidebar.locator('.app-subnav__theme')).toHaveText(['Writing guidelines', 'Formatting content', 'Publish, update or retire', 'Lexicons', 'Quick reference']);
    const breadcrumb = page.getByRole('navigation', { name: 'Breadcrumb' });
    await expect(breadcrumb).toContainText('Writing guide');
    await expect(breadcrumb.getByRole('link', { name: 'Styles', exact: true })).toHaveCount(0);
    if (path === '/content/index.html') await expect(breadcrumb.locator('li')).toHaveText(['Home', 'Writing guide']);
  }
});

test('search and sitemap classify every writing page once and remove them from Styles', async ({ page }) => {
  await page.goto('/docs/build/search.html');
  const writing = page.locator('[data-catalogue-group]').filter({ has: page.getByRole('heading', { level: 2, name: 'Writing guide', exact: true }) });
  await expect(writing).toHaveCount(1);
  expect(await writing.locator('[data-catalogue-item] h3 a').evaluateAll(relativePaths)).toEqual(writingPaths);
  await expect(writing.locator('.c-catalogue__meta')).not.toHaveCount(0);
  for (const meta of await writing.locator('.c-catalogue__meta').all()) await expect(meta).toHaveText('Reference guidance · apply within its stated scope');
  const styles = page.locator('[data-catalogue-group]').filter({ has: page.getByRole('heading', { level: 2, name: 'Styles', exact: true }) });
  expect((await styles.locator('[data-catalogue-item] h3 a').evaluateAll(relativePaths)).filter(path => writingPaths.includes(path))).toEqual([]);
  await page.locator('[data-catalogue-filter]').fill('Use clear language');
  await expect(writing).toBeVisible();
  await expect(writing.locator('[data-catalogue-item]:visible')).toHaveCount(1);
  await expect(writing.locator('[data-catalogue-item]:visible a')).toHaveText('Use clear language');
  await page.goto('/docs/build/sitemap.html');
  const writingMap = page.locator('[data-sitemap-section="content"]');
  await expect(writingMap.getByRole('heading', { level: 2 })).toHaveText('Writing guide');
  expect(await writingMap.locator('a').evaluateAll(relativePaths)).toEqual(writingPaths);
  expect((await page.locator('[data-sitemap-section="styles"] a').evaluateAll(relativePaths)).filter(path => writingPaths.includes(path))).toEqual([]);
});

test('Writing guide navigation works by keyboard at 320px and with doubled navigation text', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto('/docs/build/content/writing-guidelines/clear-language.html');
  const menu = page.getByRole('button', { name: 'Menu', exact: true });
  const writingLink = page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Writing guide', exact: true });
  await menu.focus(); await page.keyboard.press('Enter');
  await expect(menu).toHaveAttribute('aria-expanded', 'true');
  await writingLink.focus(); await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/\/content\/index\.html$/);
  await expect(menu).toHaveAttribute('aria-expanded', 'false');
  await menu.focus(); await page.keyboard.press('Space');
  // Like GOV.UK, the section sub-navigation is not shown on narrow screens.
  await expect(page.locator('.app-subnav')).toBeHidden();
  const originalSize = await writingLink.evaluate(node => parseFloat(getComputedStyle(node).fontSize));
  // Double actual computed text sizes: changing only the root size would miss
  // the explicit pixel sizes used by the native documentation navigation.
  await page.evaluate(() => {
    const sizes = [...document.querySelectorAll('.c-menu-toggle, .c-navigation a, .c-sidebar a, .c-sidebar summary')]
      .map(node => [node, parseFloat(getComputedStyle(node).fontSize)]);
    for (const [node, size] of sizes) node.style.fontSize = `${size * 2}px`;
  });
  await expect(writingLink).toHaveCSS('font-size', `${originalSize * 2}px`);
  await expect(writingLink).toBeVisible();
  await reflow(page);
  await page.setViewportSize({ width: 1280, height: 900 });
  await expect(page.locator('.app-subnav')).toBeVisible();
  await expect(menu).toBeHidden();
  await expect(writingLink).toBeVisible();
  await expect(writingLink).toHaveAttribute('aria-current', 'true');
  await reflow(page);
});

test('Writing guide navigation and grouped catalogue remain usable without JavaScript', async ({ browser, baseURL }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 320, height: 900 } });
  const page = await context.newPage();
  try {
    await page.goto(new URL('/docs/build/content/writing-guidelines/clear-language.html', baseURL).href);
    await expect(page.getByRole('button', { name: 'Menu', exact: true })).toBeHidden();
    const writing = page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Writing guide', exact: true });
    await expect(writing).toBeVisible();
    await writing.click();
    await expect(page).toHaveURL(/\/content\/index\.html$/);
    await expect(page.locator('.app-subnav')).toBeHidden();
    await expect(writing).toHaveAttribute('aria-current', 'true');
    await reflow(page);
    await page.goto(new URL('/docs/build/search.html', baseURL).href);
    const group = page.locator('[data-catalogue-group]').filter({ has: page.getByRole('heading', { level: 2, name: 'Writing guide', exact: true }) });
    expect(await group.locator('[data-catalogue-item] h3 a').evaluateAll(relativePaths)).toEqual(writingPaths);
  } finally { await context.close(); }
});
