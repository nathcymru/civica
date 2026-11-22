#!/usr/bin/env node
// Content rules for every published page, checked on the built site.
//
// These are the owner's standing rules for civica guidance (18 November 2026):
//   1. Page text does not name outside sources (GOV.UK, ONS, NHS). The only
//      exception is a source note: a <small> paragraph that starts
//      "Source note:", and the attribution pages that exist to credit sources.
//   2. Readers never see internal rule IDs such as BG-TYP-01 or WG-031.
//      Anchors (id="bg-typ-01") are fine; visible text is not.
//   3. No paragraph or list item is copied onto another page. Say it once and link to it.
//   4. Map colours shows a working OpenStreetMap example on the page itself.
//
// Pages written before these rules are listed in
// docs/data/content-rules-baseline.json with their known faults. A page may
// only improve: a new fault, or a fault on a page not in the baseline, fails.
// When a page is fixed, run with --update to shrink the baseline. --update
// never adds a fault; --reset rebuilds the list when the rules change.
//
// Usage: node scripts/check-content-rules.mjs [--update [--reset]]

import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, relative } from 'node:path';

const BUILD = 'docs/build';
const BASELINE = 'docs/data/content-rules-baseline.json';
const update = process.argv.includes('--update');

// Pages whose purpose is to credit or compare outside sources. They may name
// them; every other page may not.
const ATTRIBUTION_PAGES = new Set(['community/licence', 'community/sources']);
// Generated pages that repeat other pages' text by design.
const SKIP = new Set(['search', '404']);

const SOURCES = /\b(GOV\.UK|ONS|NHS|GDS|Office for National Statistics|Government Digital Service)\b/g;
const RULE_ID = /\b(?:BG|WG)-(?:[A-Z]{2,4}-)?\d{2,3}\b/g;
// Paragraphs and list items shorter than this are too generic to count as copied text.
const MIN_REPEAT = 120;
// Text on this many pages or more counts as copied.
const REPEAT_PAGES = 2;

const decode = value => value
  .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"').replace(/&#39;|&rsquo;|&#8217;/g, '’').replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)));
const plain = html => decode(html.replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();

function pages(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) out.push(...pages(path));
    else if (name.endsWith('.html')) out.push(path);
  }
  return out;
}

// Everything a reader can see or hear in the page body: text (including page
// history and text inside drawings) and the alt, aria-label and title
// attributes. Code, scripts and the one allowed source note are left out.
function readable(html) {
  const start = html.indexOf('<main');
  const end = html.indexOf('</main>');
  let main = start >= 0 ? html.slice(start, end >= 0 ? end : undefined) : html.slice(html.indexOf('<body'));
  main = main.replace(/<(script|style|pre|code|template)\b[\s\S]*?<\/\1>/g, ' ');
  main = main.replace(/<p>\s*<small>\s*Source note:[\s\S]*?<\/small>\s*<\/p>/g, ' ');
  const attributes = [...main.matchAll(/\s(?:alt|aria-label|title)="([^"]*)"/g)].map(match => match[1]);
  return { main, text: `${plain(main)} ${decode(attributes.join(' '))}` };
}

// Guidance text for the repeat rule. The page history is a dated record, and
// the "Help improve this guidance" block and the example code note are shared
// page furniture like the footer, so they are not counted as copied guidance.
function guidance(main) {
  return main
    .replace(/<(svg|iframe)\b[\s\S]*?<\/\1>/g, ' ')
    .replace(/<details id="full-publication-update-history">[\s\S]*?<\/details>/g, ' ')
    .replace(/<div class="c-contribute">[\s\S]*?<\/div>/g, ' ')
    .replace(/<details class="c-example__code">[\s\S]*?<\/details>/g, ' ');
}

const found = {};
const blocks = new Map();
for (const file of pages(BUILD)) {
  const page = relative(BUILD, file).replace(/\.html$/, '');
  if (SKIP.has(page)) continue;
  const html = readFileSync(file, 'utf8');
  const example = page.startsWith('examples/');
  if (!example && !html.includes('<main')) continue;
  const { main, text } = readable(html);
  const faults = [];
  if (!ATTRIBUTION_PAGES.has(page)) {
    const names = [...new Set((text.match(SOURCES) || []))].sort();
    if (names.length) faults.push(`names ${names.join(', ')}`);
  }
  if (RULE_ID.test(text)) faults.push('shows rule IDs');
  RULE_ID.lastIndex = 0;
  // Example pages are reused inside guide pages by design; only guide pages
  // are compared for copied text.
  if (!example) {
    for (const match of guidance(main).matchAll(/<(p|li)\b[^>]*>([\s\S]*?)<\/\1>/g)) {
      const block = plain(match[2]);
      if (block.length < MIN_REPEAT) continue;
      if (!blocks.has(block)) blocks.set(block, new Set());
      blocks.get(block).add(page);
    }
  }
  if (faults.length) found[page] = faults;
}

for (const [block, where] of blocks) {
  if (where.size < REPEAT_PAGES) continue;
  for (const page of where) {
    (found[page] ||= []).push(`repeats "${block.slice(0, 60)}…"`);
  }
}

// Rule 4: the Map colours page has its own working OpenStreetMap example.
// The shared example() helper renders it as an example frame: an iframe whose
// built example page carries the map renderer's data-map-example marker and
// reads its provider record, which must name OpenStreetMap.
const maps = join(BUILD, 'styles/colour-maps.html');
const workingMap = src => {
  const example = join(BUILD, 'styles', src);
  if (!existsSync(example)) return false;
  const html = readFileSync(example, 'utf8');
  const config = html.match(/<section\b[^>]*\bdata-map-example\b[^>]*\bdata-map-config="([^"]+)"/);
  if (!config) return false;
  const provider = join(example, '..', config[1]);
  return existsSync(provider) && /OpenStreetMap/.test(readFileSync(provider, 'utf8'));
};
if (existsSync(maps)) {
  const frames = [...readFileSync(maps, 'utf8').matchAll(/<iframe\b[^>]*\bsrc="([^"?#]*examples\/[a-z0-9-]+\.html)/g)].map(match => match[1]);
  if (!frames.some(workingMap)) (found['styles/colour-maps'] ||= []).push('has no working OpenStreetMap example');
}

for (const page of Object.keys(found)) found[page] = [...new Set(found[page])].sort();

const baseline = existsSync(BASELINE) ? JSON.parse(readFileSync(BASELINE, 'utf8')).pages : {};

if (update) {
  // --update only removes fixed faults. A new fault must be fixed, not listed.
  // --reset rewrites the list from scratch; use it only when the rules
  // themselves change, and say so in the commit.
  const reset = process.argv.includes('--reset');
  const kept = {};
  const refused = [];
  for (const page of Object.keys(found).sort()) {
    const known = new Set(baseline[page] || []);
    const faults = reset ? found[page] : found[page].filter(fault => known.has(fault));
    if (!reset) for (const fault of found[page]) if (!known.has(fault)) refused.push(`${page}: ${fault}`);
    if (faults.length) kept[page] = faults;
  }
  writeFileSync(BASELINE, `${JSON.stringify({
    description: 'Known content-rule faults on pages written before 18 November 2026. Entries may only be removed. See scripts/check-content-rules.mjs.',
    pages: kept,
  }, null, 2)}\n`);
  console.log(`Baseline written: ${Object.keys(kept).length} pages with known faults.`);
  if (refused.length) {
    console.error(`Not added to the baseline, fix these instead (${refused.length}):\n${refused.map(f => `  - ${f}`).join('\n')}`);
    process.exit(1);
  }
  process.exit(0);
}

const failures = [];
let stale = 0;
for (const [page, faults] of Object.entries(found)) {
  const known = new Set(baseline[page] || []);
  for (const fault of faults) if (!known.has(fault)) failures.push(`${page}: ${fault}`);
}
for (const [page, faults] of Object.entries(baseline)) {
  const now = new Set(found[page] || []);
  for (const fault of faults) if (!now.has(fault)) stale += 1;
}

if (stale) failures.push(`${stale} fixed fault(s) are still listed in ${BASELINE}: run node scripts/check-content-rules.mjs --update`);
if (failures.length) {
  console.error(`Content rules failed (${failures.length}):\n${failures.map(f => `  - ${f}`).join('\n')}`);
  process.exit(1);
}
const remaining = Object.values(found).reduce((sum, faults) => sum + faults.length, 0);
console.log(`Content rules: no new faults. ${remaining} known fault(s) on ${Object.keys(found).length} page(s) still to fix.`);
