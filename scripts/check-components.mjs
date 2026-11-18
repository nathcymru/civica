// Components specification check.
// The Master Component Inventory (docs/data/component-inventory.json) is the sole
// source of truth for component parent pages. This check proves that:
//   1. the inventory is the approved, hash-pinned version and is internally sound;
//   2. the published index, combobox data and sidebar are derived from it exactly;
//   3. any page that declares a `component:` front matter block declares exactly
//      what the inventory assigns to it.
// Run after the docs build: node scripts/check-components.mjs
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';

// Changing the inventory needs the project owner's approval. Update this hash in
// the same commit as the approved inventory change, and say so in the pull request.
const INVENTORY_PATH = 'docs/data/component-inventory.json';
const INVENTORY_SHA256 = '383ec55ad1c85c1de8c88e7abb1e9c992b8a94dc58c48e5f5025e660d69d89f9';
const PARENT_COUNT = 144;
const ORIGINS = ['HTML5', 'Home Assistant', 'Lovelace', 'Civica'];
const BUILD = 'docs/build';
// Pages in /components/ that are not inventory parents. They stay in the sidebar
// until Branch 2 retires or moves them. This list may shrink; it must never grow.
const LEGACY_PAGES = ['chart-examples', 'controls', 'details', 'devices', 'error-summary', 'example', 'expander',
  'generic-header', 'password-input', 'review-date', 'status', 'warning-callout'].map(name => `/components/${name}.html`);

const raw = readFileSync(INVENTORY_PATH);
assert.equal(createHash('sha256').update(raw).digest('hex'), INVENTORY_SHA256,
  `${INVENTORY_PATH} changed. Inventory changes need the owner's approval and a deliberate hash update in this script.`);
const inventory = JSON.parse(raw);
const parents = inventory.parents;

// 1. Inventory integrity.
assert.equal(parents.length, PARENT_COUNT, `Inventory has ${PARENT_COUNT} parents`);
const lower = value => value.toLowerCase();
const byCodePoint = (a, b) => (lower(a) < lower(b) ? -1 : lower(a) > lower(b) ? 1 : 0);
assert.deepEqual(parents.map(parent => parent.parent), parents.map(parent => parent.parent).sort(byCodePoint), 'Parents are in A to Z order');
assert.equal(new Set(parents.map(parent => parent.parent)).size, parents.length, 'Parent names are unique');
assert.equal(new Set(parents.map(parent => parent.route)).size, parents.length, 'Parent routes are unique');
const byName = new Map(parents.map(parent => [parent.parent, parent]));
const owned = new Map();
for (const parent of parents) {
  assert.match(parent.route, /^\/components\/[a-z0-9-]+\.html$/, `${parent.parent}: route`);
  assert.equal(parent.letter, parent.parent[0].toUpperCase(), `${parent.parent}: letter`);
  assert.ok(parent.children.length > 0, `${parent.parent}: has at least one child`);
  const anchors = new Set();
  const origins = new Set();
  for (const item of parent.children.flatMap(child => [child, ...(child.grandchildren || [])])) {
    assert.match(item.anchor, /^(child|xref)-[a-z0-9-]+$/, `${parent.parent} › ${item.name}: anchor`);
    assert.ok(!anchors.has(item.anchor), `${parent.parent}: duplicate anchor ${item.anchor}`);
    anchors.add(item.anchor);
    assert.ok(ORIGINS.includes(item.origin), `${parent.parent} › ${item.name}: origin ${item.origin}`);
    if (item.cross_reference) continue;
    assert.ok(item.anchor.startsWith('child-'), `${parent.parent} › ${item.name}: owned anchors start child-`);
    assert.ok(!owned.has(item.name), `${item.name} is owned by both ${owned.get(item.name)?.parent.parent} and ${parent.parent}`);
    owned.set(item.name, { parent, item });
  }
  for (const child of parent.children) if (!child.cross_reference) origins.add(child.origin);
  assert.deepEqual([...parent.origins].sort(), [...origins].sort(), `${parent.parent}: origins match its children`);
}
for (const parent of parents) for (const item of parent.children.flatMap(child => [child, ...(child.grandchildren || [])])) {
  if (!item.cross_reference) continue;
  const target = owned.get(item.name);
  assert.ok(target, `${parent.parent} › ${item.name}: cross-reference has an owner`);
  assert.equal(item.cross_reference.parent, target.parent.parent, `${parent.parent} › ${item.name}: cross-reference names the owner`);
  assert.equal(item.cross_reference.route, target.parent.route, `${parent.parent} › ${item.name}: cross-reference route`);
  assert.equal(item.cross_reference.anchor, target.item.anchor, `${parent.parent} › ${item.name}: cross-reference anchor`);
}

// 2. Published outputs are derived from the inventory.
assert.ok(existsSync(`${BUILD}/reference/component-index.json`), 'Build the docs before running this check');
const published = route => existsSync(`${BUILD}${route}`);
const index = JSON.parse(readFileSync(`${BUILD}/reference/component-index.json`, 'utf8'));
assert.equal(index.source, INVENTORY_PATH, 'Published index names its source');
assert.deepEqual(index.parents.map(parent => [parent.name, parent.route, parent.available]),
  parents.map(parent => [parent.parent, parent.route, published(parent.route)]), 'Published parents and availability');
assert.deepEqual(index.parents.map(parent => parent.children), parents.map(parent => parent.children), 'Published children equal the inventory');
const declaredRoutes = new Set(index.declarations.filter(item => item.declared && Object.keys(item.declared).length).map(item => item.route));
assert.deepEqual(index.parents.map(parent => [parent.letter, parent.origins, parent.declared]),
  parents.map(parent => [parent.letter, parent.origins, declaredRoutes.has(parent.route)]), 'Published letters, origins and declared flags');
const expected = parents.flatMap(parent => [
  { name: parent.parent, kind: 'parent', owner: parent.parent, route: parent.route, anchor: null,
    available: published(parent.route), anchor_published: declaredRoutes.has(parent.route) },
  ...parent.children.flatMap(child => [child, ...(child.grandchildren || [])].map((item, position) => {
    const owner = item.cross_reference ? byName.get(item.cross_reference.parent) : parent;
    const entry = { name: item.name, kind: position === 0 ? 'child' : 'grandchild', origin: item.origin, owner: owner.parent,
      route: owner.route, anchor: item.cross_reference ? item.cross_reference.anchor : item.anchor,
      available: published(owner.route), anchor_published: declaredRoutes.has(owner.route) };
    if (position > 0) entry.within = child.name;
    if (item.cross_reference) entry.listed_on = parent.parent;
    if (item.note) entry.note = item.note;
    return entry;
  }))
]);
assert.deepEqual(index.entries, expected,
  'Every parent, child and grandchild appears once, in inventory order, with its single owner, origin, availability and notes');

// 3. Declared front matter matches the inventory.
let declaring = 0;
for (const { route, declared } of index.declarations) {
  if (!declared || !Object.keys(declared).length) continue;
  declaring++;
  const parent = parents.find(candidate => candidate.route === route);
  assert.equal(declared.parent, parent.parent, `${route}: component.parent`);
  assert.equal(declared.letter, parent.letter, `${route}: component.letter`);
  assert.deepEqual([...declared.origins].sort(), [...parent.origins].sort(), `${route}: component.origins`);
  const names = items => items.map(item => [item.name, item.anchor, (item.grandchildren || []).map(grandchild => [grandchild.name, grandchild.anchor])]);
  assert.deepEqual(names(declared.children || []), names(parent.children), `${route}: component.children match the inventory`);
}

// 4. The index page, its embedded search data and the sidebar show exactly the derived lists.
const page = readFileSync(`${BUILD}/components/index.html`, 'utf8');
const decode = text => text.replace(/&amp;/g, '&').replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
const slug = text => text.toLowerCase().replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const used = new Set(parents.map(parent => parent.letter));
const bar = page.match(/<nav[^>]*aria-label="A to Z navigation"[^>]*>([\s\S]*?)<\/nav>/)?.[1] || '';
const barItems = [...bar.matchAll(/<li>([\s\S]*?)<\/li>/g)].map(match => match[1]);
assert.equal(barItems.length, 26, 'A to Z bar has 26 letters');
'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').forEach((letter, position) => {
  const wanted = used.has(letter)
    ? `<a class="govuk-link govuk-link--no-visited-state" href="#${letter.toLowerCase()}">${letter}</a>`
    : `<span class="style-a-z__empty">${letter}</span>`;
  assert.equal(barItems[position], wanted, `A to Z bar item ${letter}`);
});
const list = page.match(/<div class="c-component-az" data-component-list>([\s\S]*?)<\/div>/)?.[1] || '';
assert.deepEqual([...list.matchAll(/<h2 class="style-a-z__letter" id="([a-z])">([A-Z])<\/h2>/g)].map(match => [match[1], match[2]]),
  [...used].map(letter => [letter.toLowerCase(), letter]), 'Letter headings match the used letters, in order');
const items = [...list.matchAll(/<li id="([^"]+)" data-component-parent="([^"]+)">([\s\S]*?)<\/li>/g)];
assert.deepEqual(items.map(match => decode(match[2])), parents.map(parent => parent.parent), 'Index lists every parent once in order');
items.forEach((match, position) => {
  const parent = parents[position];
  assert.equal(match[1], `parent-${slug(parent.parent)}`, `${parent.parent}: list anchor`);
  const linked = /<a class="govuk-link" href="([^"]+)">/.exec(match[3]);
  if (published(parent.route)) {
    assert.ok(linked && linked[1].endsWith(parent.route.replace('/components/', '')), `${parent.parent}: linked to its page`);
    assert.ok(!match[3].includes('Specification not yet published'), `${parent.parent}: not marked pending`);
  } else {
    assert.ok(!linked, `${parent.parent}: pending parent is not linked`);
    assert.ok(match[3].includes('Specification not yet published'), `${parent.parent}: marked pending`);
  }
  const origins = parent.origins.map(origin => (origin === 'Civica' ? 'civica' : origin)).join(', ');
  assert.ok(decode(match[3]).includes(`Origin: ${origins}`), `${parent.parent}: origin line`);
});

// The combobox data is the published entries, with cross-references folded into their owner entry.
const search = JSON.parse(page.match(/<script type="application\/json" id="component-search-data">([\s\S]*?)<\/script>/)[1]);
const expectedSearch = expected.filter(entry => !entry.listed_on).map(entry => {
  const also = expected.filter(other => other.listed_on && other.name === entry.name && other.owner === entry.owner);
  const notes = also.map(other => other.note).filter(Boolean);
  const href = entry.available
    ? `${entry.route.replace('/components/', '')}${entry.anchor && entry.anchor_published ? `#${entry.anchor}` : ''}`
    : `#parent-${slug(entry.owner)}`;
  const item = { n: entry.name, k: entry.kind, o: entry.owner, h: href, a: entry.available };
  if (entry.within) item.w = entry.within;
  if (entry.origin) item.g = entry.origin === 'Civica' ? 'civica' : entry.origin;
  if (also.length) item.l = also.map(other => other.listed_on);
  if (notes.length) item.t = notes.join(' ');
  return item;
});
assert.equal(search.length, expectedSearch.length, 'Search data has one option per owned item');
search.forEach((item, position) => {
  const want = expectedSearch[position];
  assert.ok(item.h.endsWith(want.h), `${want.n}: search link ${item.h} ends ${want.h}`);
  assert.deepEqual({ ...item, h: want.h }, want, `${want.n}: search data`);
});

// The sidebar: every published parent plus the pinned legacy pages, flat and in code-point order.
const legacyLive = LEGACY_PAGES.filter(published);
const legacyFound = execFileSync('find', [`${BUILD}/components`, '-maxdepth', '1', '-name', '*.html'], { encoding: 'utf8' })
  .trim().split('\n').map(path => path.replace(BUILD, '')).filter(route => route !== '/components/index.html' && !parents.some(parent => parent.route === route)).sort();
assert.deepEqual(legacyFound, [...legacyLive].sort(), 'Only the pinned legacy pages sit outside the inventory');
const sample = parents.find(parent => published(parent.route));
if (sample) {
  for (const route of [sample.route, ...legacyLive]) {
    const sidebar = readFileSync(`${BUILD}${route}`, 'utf8').match(/<nav class="app-subnav c-sidebar"[\s\S]*?<\/nav>/)[0];
    const links = [...sidebar.matchAll(/<a class="app-subnav__link[^"]*" href="([^"]+)"( aria-current="page")?>([^<]+)<\/a>/g)];
    const names = links.map(match => decode(match[3]));
    assert.deepEqual(names, [...names].sort(byCodePoint), `${route}: sidebar is in A to Z order`);
    const parentNames = parents.filter(parent => published(parent.route)).map(parent => parent.parent);
    assert.deepEqual(names.filter(name => parentNames.includes(name)), parentNames, `${route}: sidebar lists every published parent`);
    assert.equal(names.length, parentNames.length + legacyLive.length, `${route}: sidebar adds only the legacy pages`);
    const current = links.filter(match => match[2]);
    assert.equal(current.length, 1, `${route}: one current item`);
    assert.ok(current[0][1].endsWith(route.replace('/components/', '')), `${route}: current item is this page`);
  }
}

const live = parents.filter(parent => published(parent.route)).length;
console.log(`Components inventory is consistent: ${parents.length} parents, ${owned.size} owned elements and variants; ${live} of ${parents.length} parent pages published, ${declaring} declare the component schema; ${legacyLive.length} legacy pages awaiting retirement.`);
