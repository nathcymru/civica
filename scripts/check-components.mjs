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
import { existsSync, readFileSync } from 'node:fs';

// Changing the inventory needs the project owner's approval. Update this hash in
// the same commit as the approved inventory change, and say so in the pull request.
const INVENTORY_PATH = 'docs/data/component-inventory.json';
const INVENTORY_SHA256 = 'e02aea7792f0c6b10f5af17846e58565160e8db2c9f89d34505aaa7cf786345d';
const PARENT_COUNT = 144;
const ORIGINS = ['HTML5', 'Home Assistant', 'Lovelace', 'Civica'];
const BUILD = 'docs/build';

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
const expected = parents.flatMap(parent => [
  { name: parent.parent, kind: 'parent', owner: parent.parent, route: parent.route, anchor: null },
  ...parent.children.flatMap(child => [child, ...(child.grandchildren || [])].map((item, position) => {
    const owner = item.cross_reference ? byName.get(item.cross_reference.parent) : parent;
    return { name: item.name, kind: position === 0 ? 'child' : 'grandchild', owner: owner.parent, route: owner.route,
      anchor: item.cross_reference ? item.cross_reference.anchor : item.anchor };
  }))
]);
assert.deepEqual(index.entries.map(({ name, kind, owner, route, anchor }) => ({ name, kind, owner, route, anchor })), expected,
  'Every parent, child and grandchild appears once, in inventory order, with its single owner');
for (const entry of index.entries) assert.equal(entry.available, published(entry.route), `${entry.name}: availability`);

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

// 4. The index page and the sidebar show exactly the derived lists.
const page = readFileSync(`${BUILD}/components/index.html`, 'utf8');
const used = new Set(parents.map(parent => parent.letter));
const bar = page.match(/<nav[^>]*aria-label="A to Z navigation"[^>]*>([\s\S]*?)<\/nav>/)?.[1] || '';
for (const letter of 'ABCDEFGHIJKLMNOPQRSTUVWXYZ') {
  if (used.has(letter)) assert.ok(bar.includes(`href="#${letter.toLowerCase()}">${letter}</a>`), `A to Z bar links ${letter}`);
  else assert.ok(bar.includes(`<span class="style-a-z__empty">${letter}</span>`), `A to Z bar marks ${letter} as empty`);
}
const listed = [...page.matchAll(/data-component-parent="([^"]+)"/g)].map(match => match[1].replace(/&amp;/g, '&').replace(/&#39;/g, "'").replace(/&quot;/g, '"'));
assert.deepEqual(listed, parents.map(parent => parent.parent), 'Index lists every parent once in order');
const sample = parents.find(parent => published(parent.route));
if (sample) {
  const sidebar = readFileSync(`${BUILD}${sample.route}`, 'utf8').match(/<nav class="app-subnav c-sidebar"[\s\S]*?<\/nav>/)[0];
  const names = [...sidebar.matchAll(/class="app-subnav__link[^"]*"[^>]*>([^<]+)<\/a>/g)].map(match => match[1].replace(/&amp;/g, '&').replace(/&#39;/g, "'"));
  assert.deepEqual(names, parents.filter(parent => published(parent.route)).map(parent => parent.parent), 'Sidebar lists published parents in A to Z order');
}

const live = parents.filter(parent => published(parent.route)).length;
console.log(`Components inventory is consistent: ${parents.length} parents, ${owned.size} owned elements and variants; ${live} of ${parents.length} parent pages published, ${declaring} declare the component schema.`);
