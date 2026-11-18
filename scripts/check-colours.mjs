// Colour section check.
// docs/data/govuk-brand-colours.json is a verbatim copy of the GOV.UK Brand
// Guidelines colour pages (read 2026-11-18). This check proves that:
//   1. the record is internally sound (hex and RGB agree, every reference exists);
//   2. each palette matches the pinned upstream record: group titles, order,
//      and every colour's id, hex, RGB, CMYK and Pantone;
//   3. each built Colour page shows every colour of its palette, with its values;
//   4. the Chart colours page and chart module use the GOV.UK chart palette;
//   5. the Map colours page shows the GOV.UK map example colours;
//   6. the Social colours page shows the GOV.UK companion pairings.
// Run after the docs build: node scripts/check-colours.mjs
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
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
// The pins are sha256 of the ordered palette, recorded when the GOV.UK pages
// were read (source.read_on). A reordered, retitled or changed group fails here,
// even though the pages and browser tests render from the same file.
const PINS = {
  web: 'b7cb5d625d92c1d931dfc9ec4fe456f167eac51f870765966b7278b2adc68935',
  app: '2d74f1722bc3b71eac669fceebd8d4ec238afa4d985591e6fde44871bda5bfce',
  social: '289fae2ff85b180fd505b8279d4a090f2df1ae26dc3a8d7a95151994979e56e0',
  print: '85b569eb2fe0ef5700fce8a819853e38368ec3aec1f6ad0ddc00e4ec4234aed4',
  maps: 'd62e79b85340197e2e92b395d0dc7a3dea13fde09885418f84a2e90b1d021427',
  illustrations: '58fbd838f55925f98fd61b708d8046b6925dd7b367bd58782ba37c2c3bc74d58',
};
assert.equal(data.source.read_on, '2026-11-18', 'Pins were recorded on 2026-11-18: re-read upstream before changing them');
const fingerprint = page => createHash('sha256').update(JSON.stringify(pages[page].palette.map(group => [group.title,
  group.colours.map(id => [id, colours[id].hex, colours[id].rgb, colours[id].print?.cmyk ?? null, colours[id].print?.pantone ?? null])]))).digest('hex');
for (const [page, pin] of Object.entries(PINS)) assert.equal(fingerprint(page), pin, `${page}: palette differs from the pinned GOV.UK record`);
const functionalPin = createHash('sha256').update(JSON.stringify(pages.web.functional.map(group => [group.title, group.tokens.map(token => [token.token, token.colour])]))).digest('hex');
assert.equal(functionalPin, '80641b37502bbb75c9c81b226b9c54cabd1ce0612553aaf7addc54033017c198', 'web: functional colours differ from the pinned GOV.UK record');
assert.equal(pages.web.functional.flatMap(group => group.tokens).length, 20, 'web: 20 functional colours');
pages.web.functional.flatMap(group => group.tokens).forEach(token => known(token.colour));
assert.equal(pages.charts.categorical.length, 8, 'charts: 8 categorical entries');
assert.equal(groupIds(pages.charts.sequential).length, 49, 'charts: 49 sequential and divergent colours');
assert.equal(pages.charts.additional.length, 14, 'charts: 14 additional colours');
[...pages.charts.categorical.map(item => item.colour), ...groupIds(pages.charts.sequential), ...pages.charts.additional].forEach(known);
assert.equal(pages.social.companion.length, 9, 'social: 9 companion pairings');
pages.social.companion.forEach(pair => { known(pair.foreground); known(pair.background); });

const luminance = hex => {
  const linear = [1, 3, 5].map(at => parseInt(hex.slice(at, at + 2), 16) / 255).map(c => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
};
const contrast = (a, b) => { const [x, y] = [luminance(a), luminance(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };

// 3. Published pages show every colour of their palette.
const decode = text => text.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
for (const [page, file, show] of [['web', 'colour-web', ['hex', 'rgb']], ['app', 'colour-app', ['hex', 'rgb']], ['print', 'colour-print', ['cmyk', 'pantone']], ['maps', 'colour-maps', ['hex', 'rgb']], ['social', 'colour-social', ['hex', 'rgb']]]) {
  const path = `${BUILD}/${file}.html`;
  assert.ok(existsSync(path), `${path} missing: run the docs build first`);
  const raw = readFileSync(path, 'utf8');
  const html = decode(raw);
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
  // Match the raw HTML. Values that contain double quotes (Sass) are written
  // with single-quoted attributes, so accept either quote style.
  let buttons = 0;
  for (const button of raw.matchAll(/<button type="button" class="c-copy-value" data-copy-value=(?:"([^"]+)"|'([^']+)') aria-label=(?:"([^"]+)"|'([^']+)') hidden>/g)) {
    const [value, label] = [decode(button[1] ?? button[2]), decode(button[3] ?? button[4])];
    assert.ok(label.startsWith('Copy ') && label.includes(value), `${file}: copy button label names its value ${value}`);
    buttons += 1;
  }
  assert.equal(buttons, (raw.match(/class="c-copy-value"/g) || []).length, `${file}: every copy button was checked`);
  // Sample labels are 19px bold (large text), so each needs at least 3:1.
  for (const sample of html.matchAll(/style="background-color:(#[0-9A-F]{6});color:(#[0-9A-F]{6})"/g)) {
    assert.ok(contrast(sample[1], sample[2]) >= 3, `${file}: sample label on ${sample[1]} reaches 3:1`);
  }
}
// 4. The Chart colours page shows the categorical, scale and additional
// palettes in GOV.UK order, and the chart module uses the same categorical colours.
{
  const path = `${BUILD}/chart-colour.html`;
  assert.ok(existsSync(path), `${path} missing: run the docs build first`);
  const html = decode(readFileSync(path, 'utf8'));
  const names = [...html.matchAll(/<p class="c-swatch__name">([^<]+)<\/p>/g)].map(match => match[1]);
  const expected = [
    ...pages.charts.categorical.map(item => item.role ? `${item.role}: ${colours[item.colour].name}` : colours[item.colour].name),
    ...groupIds(pages.charts.sequential).map(id => colours[id].name),
    ...pages.charts.additional.map(id => colours[id].name),
  ];
  assert.deepEqual(names, expected, 'chart-colour: swatches match the GOV.UK chart palette in order');
  const module = JSON.parse(readFileSync('design-system/chart-colours.json', 'utf8'));
  assert.deepEqual(module.categorical.map(colour => colour.hex), pages.charts.categorical.filter(item => !item.role).map(item => colours[item.colour].hex), 'chart module uses the GOV.UK categorical colours');
}
// 6. The Social colours page shows the nine GOV.UK companion pairings in order,
// and every pairing's foreground and background reach 3:1 at least.
{
  const html = decode(readFileSync(`${BUILD}/colour-social.html`, 'utf8'));
  const names = [...html.matchAll(/<p class="c-swatch__name">([^<]+ on [^<]+)<\/p>/g)].map(match => match[1]);
  assert.deepEqual(names, pages.social.companion.map(pair => `${colours[pair.foreground].name} on ${colours[pair.background].name}`), 'colour-social: companion pairings in GOV.UK order');
}
// 5. The map example colours are GOV.UK's, and the Map colours page lists them.
{
  const example = pages.maps.example;
  [...example.points_of_interest, ...example.base_map].forEach(item => { known(item.colour); if (item.outline) known(item.outline); });
  const html = decode(readFileSync(`${BUILD}/colour-maps.html`, 'utf8'));
  for (const item of [...example.points_of_interest, ...example.base_map]) {
    assert.ok(html.includes(`${colours[item.colour].name}</p>`), `colour-maps: shows ${colours[item.colour].name}`);
    if (item.outline) assert.ok(html.includes(`${colours[item.outline].name}</p>`), `colour-maps: shows ${colours[item.outline].name}`);
  }
  // Data must reach 3:1 with the land through its outline (GOV.UK maps guidance).
  const land = colours[example.base_map.find(item => item.role === 'Land').colour].hex;
  assert.ok(contrast(colours[example.points_of_interest[0].outline].hex, land) >= 3, 'map data outline reaches 3:1 on the land');
}
console.log(`Colour record is consistent: ${Object.keys(colours).length} GOV.UK colours across ${Object.keys(pages).length} pages, read ${data.source.read_on}.`);
