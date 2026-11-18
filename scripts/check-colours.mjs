// Colour section check.
// docs/data/govuk-brand-colours.json is a verbatim copy of the GOV.UK Brand
// Guidelines colour pages (read 2026-11-18). This check proves that:
//   1. the record is internally sound (hex and RGB agree, every reference exists);
//   2. each palette has exactly the number of colours the GOV.UK page shows;
//   3. each built Colour page shows every colour of its palette, with its values.
// Run after the docs build: node scripts/check-colours.mjs
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';

const data = JSON.parse(readFileSync('docs/data/govuk-brand-colours.json', 'utf8'));
const { colours, pages } = data;
const BUILD = 'docs/build/styles';

// 1. Integrity.
for (const [id, colour] of Object.entries(colours)) {
  assert.match(colour.hex, /^#[0-9A-F]{6}$/, `${id}: hex is upper-case #RRGGBB`);
  assert.deepEqual(colour.rgb, [1, 3, 5].map(at => parseInt(colour.hex.slice(at, at + 2), 16)), `${id}: RGB matches hex`);
  if (colour.print) {
    assert.equal(colour.print.cmyk.length, 4, `${id}: CMYK has four values`);
    assert.ok(colour.print.pantone, `${id}: Pantone reference`);
  }
}
assert.equal(new Set(Object.values(colours).map(colour => colour.name)).size, Object.keys(colours).length, 'Colour names are unique');
const known = id => assert.ok(colours[id], `Unknown colour ${id}`);
const groupIds = groups => groups.flatMap(group => group.colours);

// 2. Palette sizes as published on the GOV.UK Brand Guidelines (2026-11-18).
const SIZES = { web: 68, app: 73, social: 71, print: 39, maps: 63, illustrations: 3 };
for (const [page, size] of Object.entries(SIZES)) {
  const ids = groupIds(pages[page].palette);
  ids.forEach(known);
  assert.equal(ids.length, size, `${page}: ${size} colours`);
  assert.equal(new Set(ids).size, ids.length, `${page}: no colour listed twice`);
  assert.match(pages[page].url, /^https:\/\/brand\.design-system\.service\.gov\.uk\/colour\/[a-z]+\/$/, `${page}: source URL`);
}
assert.equal(pages.web.functional.flatMap(group => group.tokens).length, 20, 'web: 20 functional colours');
pages.web.functional.flatMap(group => group.tokens).forEach(token => known(token.colour));
assert.equal(pages.charts.categorical.length, 8, 'charts: 8 categorical entries');
assert.equal(groupIds(pages.charts.sequential).length, 49, 'charts: 49 sequential and divergent colours');
assert.equal(pages.charts.additional.length, 14, 'charts: 14 additional colours');
[...pages.charts.categorical.map(item => item.colour), ...groupIds(pages.charts.sequential), ...pages.charts.additional].forEach(known);
assert.equal(pages.social.companion.length, 9, 'social: 9 companion pairings');
pages.social.companion.forEach(pair => { known(pair.foreground); known(pair.background); });

// 3. Published pages show every colour of their palette.
const decode = text => text.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
for (const [page, file, show] of [['web', 'colour-web', ['hex', 'rgb']], ['app', 'colour-app', ['hex', 'rgb']], ['print', 'colour-print', ['cmyk', 'pantone']]]) {
  const path = `${BUILD}/${file}.html`;
  if (!existsSync(path)) continue;
  const html = decode(readFileSync(path, 'utf8'));
  const swatches = [...html.matchAll(/<li class="c-swatch">([\s\S]*?)<\/dl>\s*<\/li>/g)].map(match => match[1]);
  const listed = swatches.slice(0, groupIds(pages[page].palette).length);
  groupIds(pages[page].palette).forEach((id, position) => {
    const colour = colours[id];
    const swatch = listed[position] || '';
    assert.ok(swatch.includes(`<p class="c-swatch__name">${colour.name}</p>`), `${file}: swatch ${position + 1} is ${colour.name}`);
    if (show.includes('hex')) assert.ok(swatch.includes(`>${colour.hex}</code>`), `${file}: ${colour.name} hex`);
    if (show.includes('rgb')) assert.ok(swatch.includes(`>${colour.rgb.join(' ')}</code>`), `${file}: ${colour.name} RGB`);
    if (show.includes('cmyk') && colour.print) assert.ok(swatch.includes(`>${colour.print.cmyk.join(' ')}</code>`), `${file}: ${colour.name} CMYK`);
    if (show.includes('pantone') && colour.print) assert.ok(swatch.includes(`>${colour.print.pantone}</code>`), `${file}: ${colour.name} Pantone`);
    assert.ok(swatch.includes(`style="background-color:${colour.hex};`), `${file}: ${colour.name} sample`);
  });
  assert.equal((html.match(/data-copy-value-status/g) || []).length, 1, `${file}: one copy status region`);
  for (const button of html.matchAll(/<button type="button" class="c-copy-value" data-copy-value="([^"]+)" aria-label="([^"]+)" hidden>/g)) {
    assert.ok(button[2].includes(button[1]), `${file}: copy button label names its value ${button[1]}`);
  }
}
console.log(`Colour record is consistent: ${Object.keys(colours).length} GOV.UK colours across ${Object.keys(pages).length} pages, read ${data.source.read_on}.`);
