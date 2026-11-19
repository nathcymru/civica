// Colour section check.
// docs/data/govuk-brand-colours.json is a verbatim copy of the GOV.UK Brand
// Guidelines colour pages (read 2026-11-18). This check proves that:
//   1. the record is internally sound (hex and RGB agree, every reference exists);
//   2. each palette matches the pinned upstream record: group titles, order,
//      and every colour's id, hex, RGB, CMYK and Pantone;
//   3. each built Colour page shows every colour of its palette, with its values;
//   4. the Chart colours page and chart module use the GOV.UK chart palette;
//   5. the Map colours page shows the GOV.UK map example colours;
//   6. the Social colours page shows the GOV.UK companion pairings;
//   7. the illustration examples use only GOV.UK Web and illustration colours,
//      the web example only web palette colours and the app examples only app
//      palette colours (the generator checks text contrast);
// Run after the docs build: node scripts/check-colours.mjs
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import YAML from 'yaml';

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
// Web-app colours shows the web-app palettes as one palette: each
// group lists its web colours, then the app colours the web group lacks, so
// both palettes keep their order. Colours in only one palette carry a note.
const decode = text => text.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
const webIds = groupIds(pages.web.palette);
const appIds = groupIds(pages.app.palette);
const webAndAppIds = [...new Set([...pages.web.palette, ...pages.app.palette].map(group => group.title))].flatMap(title => [
  ...new Set([pages.web.palette, pages.app.palette].flatMap(groups => groups.find(group => group.title === title)?.colours ?? [])),
]);
assert.equal(webAndAppIds.length, new Set([...webIds, ...appIds]).size, 'web-app: the combined palette has every web-app colour once');
const paletteNote = id => (!appIds.includes(id) ? 'Web only' : !webIds.includes(id) ? 'App only' : null);
for (const [page, file, show] of [['web+app', 'colour-web-app', ['hex', 'rgb']], ['print', 'colour-print', ['cmyk', 'pantone']], ['maps', 'colour-maps', ['hex', 'rgb']], ['social', 'colour-social', ['hex', 'rgb']], ['illustrations', 'colour-illustrations', ['hex', 'rgb']]]) {
  const path = `${BUILD}/${file}.html`;
  assert.ok(existsSync(path), `${path} missing: run the docs build first`);
  const raw = readFileSync(path, 'utf8');
  const html = decode(raw);
  const swatches = [...html.matchAll(/<div class="c-swatch" style="--c-swatch-colour:(#[0-9A-F]{6});">([\s\S]*?)<\/div>/g)].map(match => ({ hex: match[1], body: match[2] }));
  const ids = page === 'web+app' ? webAndAppIds : groupIds(pages[page].palette);
  const listed = swatches.slice(0, ids.length);
  ids.forEach((id, position) => {
    const colour = colours[id];
    const { hex, body: swatch } = listed[position] || { hex: '', body: '' };
    assert.ok(swatch.includes(`<dt class="c-swatch__name">${colour.name}</dt>`), `${file}: swatch ${position + 1} is ${colour.name}`);
    if (page === 'web+app') {
      const note = paletteNote(id);
      if (note) assert.ok(swatch.includes(`<dd class="c-swatch__note">${note}</dd>`), `${file}: ${colour.name} is marked ${note}`);
      else assert.ok(!swatch.includes('c-swatch__note'), `${file}: ${colour.name} is in both palettes, so it has no note`);
    }
    if (show.includes('hex')) assert.ok(swatch.includes(`>${colour.hex}</code>`), `${file}: ${colour.name} hex`);
    if (show.includes('rgb')) assert.ok(swatch.includes(`>${colour.rgb.join(' ')}</code>`), `${file}: ${colour.name} RGB`);
    if (show.includes('cmyk') && colour.print) assert.ok(swatch.includes(`>${colour.print.cmyk.join(' ')}</code>`), `${file}: ${colour.name} CMYK`);
    if (show.includes('pantone') && colour.print) assert.ok(swatch.includes(`>${colour.print.pantone}</code>`), `${file}: ${colour.name} Pantone`);
    assert.equal(hex, colour.hex, `${file}: ${colour.name} sample`);
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
}
// App colours is retired: its page only points to Web-app colours and
// shows no swatches, so the app palette has one owner.
{
  const path = `${BUILD}/colour-app.html`;
  assert.ok(existsSync(path), `${path} missing: run the docs build first`);
  const html = readFileSync(path, 'utf8');
  assert.ok(!html.includes('class="c-swatch'), 'colour-app: the retired page shows no swatches');
  assert.ok(html.includes('href="colour-web-app.html#app-colours"'), 'colour-app: the retired page links to Web-app colours');
}
// 4. The Chart colours page shows the categorical, scale and additional
// palettes in GOV.UK order, and the chart module uses the same categorical colours.
{
  const path = `${BUILD}/chart-colour.html`;
  assert.ok(existsSync(path), `${path} missing: run the docs build first`);
  const full = decode(readFileSync(path, 'utf8'));
  // The palette sections end where the examples begin.
  const html = full.slice(0, full.indexOf('id="using-colour-in-charts"'));
  assert.ok(html.length < full.length, 'chart-colour: Using colour in charts section found');
  const names = [...html.matchAll(/<dt class="c-swatch__name">([^<]+)<\/dt>/g)].map(match => match[1]);
  const expected = [
    ...pages.charts.categorical.map(item => colours[item.colour].name),
    ...groupIds(pages.charts.sequential).map(id => colours[id].name),
    ...pages.charts.additional.map(id => colours[id].name),
  ];
  assert.deepEqual(names, expected, 'chart-colour: swatches match the GOV.UK chart palette in order');
  const module = JSON.parse(readFileSync('design-system/chart-colours.json', 'utf8'));
  assert.deepEqual(module.categorical.map(colour => colour.hex), pages.charts.categorical.filter(item => !item.role).map(item => colours[item.colour].hex), 'chart module uses the GOV.UK categorical colours');
}
// 5. The map example colours are GOV.UK's, and the Map colours page lists them.
{
  const example = pages.maps.example;
  [...example.points_of_interest, ...example.base_map].forEach(item => { known(item.colour); if (item.outline) known(item.outline); });
  const html = decode(readFileSync(`${BUILD}/colour-maps.html`, 'utf8'));
  for (const item of [...example.points_of_interest, ...example.base_map]) {
    assert.ok(html.includes(`${colours[item.colour].name}</dt>`), `colour-maps: shows ${colours[item.colour].name}`);
    if (item.outline) assert.ok(html.includes(`${colours[item.outline].name}</dt>`), `colour-maps: shows ${colours[item.outline].name}`);
  }
  // Data must reach 3:1 with the land through its outline (GOV.UK maps guidance).
  const land = colours[example.base_map.find(item => item.role === 'Land').colour].hex;
  assert.ok(contrast(colours[example.points_of_interest[0].outline].hex, land) >= 3, 'map data outline reaches 3:1 on the land');
}
// 6. The Social colours page shows the 9 GOV.UK companion pairings in order,
// every pairing reaches 3:1 at least, and every example tile colour is a
// GOV.UK social palette colour.
{
  const html = decode(readFileSync(`${BUILD}/colour-social.html`, 'utf8'));
  const names = [...html.matchAll(/<h4 class="c-pair__name">([^<]+ on [^<]+)<\/h4>/g)].map(match => match[1]);
  assert.deepEqual(names, pages.social.companion.map(pair => `${colours[pair.foreground].name} on ${colours[pair.background].name}`), 'colour-social: companion pairings in GOV.UK order');
  for (const pair of pages.social.companion) {
    assert.ok(contrast(colours[pair.foreground].hex, colours[pair.background].hex) >= 3, `colour-social: ${pair.foreground} on ${pair.background} reaches 3:1`);
  }
  const palette = new Set(groupIds(pages.social.palette).map(id => colours[id].hex.toUpperCase()));
  const tiles = readFileSync('docs/data/social-colour-examples.yml', 'utf8');
  const used = [...tiles.matchAll(/(?:fill|stroke)="(#[0-9A-Fa-f]{6})"/g)].map(match => match[1].toUpperCase());
  assert.ok(used.length > 0, 'colour-social: example tiles have colours');
  for (const hex of used) assert.ok(palette.has(hex), `colour-social: example colour ${hex} is in the GOV.UK social palette`);
}
// 7. Every colour in the illustration examples is a GOV.UK Web colour or one
// of the colours the GOV.UK illustrations page lists.
{
  const allowed = new Set([...groupIds(pages.web.palette), ...groupIds(pages.illustrations.palette)].map(id => colours[id].hex.toUpperCase()));
  const examples = readFileSync('docs/data/illustration-colour-examples.yml', 'utf8');
  const used = [...examples.matchAll(/(?:fill|stroke)="(#[0-9A-Fa-f]{6})"/g)].map(match => match[1].toUpperCase());
  assert.ok(used.length > 0, 'colour-illustrations: examples have colours');
  for (const hex of used) assert.ok(allowed.has(hex), `colour-illustrations: example colour ${hex} is a GOV.UK Web or illustration colour`);
}
// The same check for the Web and App colour pictures: the web example uses
// only web palette colours, and the app examples only app palette colours.
{
  const examples = YAML.parse(readFileSync('docs/data/web-app-colour-examples.yml', 'utf8')).examples;
  const palettes = { web: groupIds(pages.web.palette), app: groupIds(pages.app.palette) };
  const expected = { 'web-colour-dashboard': 'web', 'app-colour-mobile-web-header': 'app', 'app-colour-header': 'app', 'app-colour-examples': 'app' };
  assert.deepEqual(Object.keys(examples).sort(), Object.keys(expected).sort(), 'web-app examples: the expected pictures');
  for (const [id, page] of Object.entries(expected)) {
    const allowed = new Set(palettes[page].map(colour => colours[colour].hex.toUpperCase()));
    const used = [...examples[id].html.matchAll(/(?:fill|stroke)="(#[0-9A-Fa-f]{6})"/g)].map(match => match[1].toUpperCase());
    assert.ok(used.length > 0, `${id}: example has colours`);
    for (const hex of used) assert.ok(allowed.has(hex), `${id}: example colour ${hex} is in the GOV.UK ${page} palette`);
    assert.ok(/Colours: [^<]+\./.test(examples[id].html), `${id}: caption lists the colours`);
    assert.ok(/are invented[.,]/.test(examples[id].html), `${id}: says its details are invented`);
  }
}
// 8. Layout parity with the GOV.UK Brand colour pages. Text and records can
// pass review while the page looks nothing like its source, so check what a
// reader sees: the GOV.UK section headings in GOV.UK order (outline read from
// brand.design-system.service.gov.uk/colour/ on 18 November 2026), the GOV.UK
// swatch list rather than cards, no "On this page" box (GOV.UK has none), and
// GOV.UK's example pictures on the page rather than in example frames.
// This is not a visual comparison: also compare screenshots before release.
{
  const outline = {
    'colour-web-app': ['Theme colour', 'Web-app palette', 'Blues', 'Greens', 'Teals', 'Purples', 'Magentas', 'Reds', 'Oranges', 'Yellows', 'Browns', 'Neutrals', 'Functional colours', 'Dashboard example', 'App colours', 'App header', 'Mobile web header', 'App screens', 'Tinted tiles and menus'],
    'colour-social': ['Social palette', 'Blues', 'Greens', 'Teals', 'Purples', 'Magentas', 'Reds', 'Oranges', 'Yellows', 'Neutrals', 'Use colour to reflect tone', 'From most informative to most inspiring', 'Tonal colour examples', 'Companion colour set', 'Companion colour examples'],
    'colour-print': ['Print palette', 'Blues', 'Greens', 'Teals', 'Purples', 'Magentas', 'Reds', 'Oranges', 'Yellows', 'Neutrals'],
    'chart-colour': ['Chart palette', 'Categorical palette', 'Sequential and divergent scale palette', 'Using colour in charts', 'Single category', 'Multiple categories', 'Above and below a target', 'Using charts within social media'],
    'colour-maps': ['Map palette', 'Blues', 'Magentas', 'Reds', 'Greens', 'Purples', 'Teals', 'Oranges', 'Neutrals', 'Using colour combinations on maps', 'Example: zones on a base map', 'Colours used in the example', 'Points of interest', 'Base map'],
    'colour-illustrations': ['Illustrations palette', 'Applying colour', 'Colour pairing', 'Using contrast'],
  };
  const text = value => decode(value.replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim();
  for (const [file, expected] of Object.entries(outline)) {
    const html = readFileSync(`${BUILD}/${file}.html`, 'utf8');
    const main = html.slice(html.indexOf('<main'));
    const headings = [...main.matchAll(/<h[2-4][^>]*>([\s\S]*?)<\/h[2-4]>/g)].map(match => text(match[1]));
    let at = 0;
    for (const heading of expected) {
      const found = headings.indexOf(heading, at);
      assert.ok(found >= 0, `${file}: GOV.UK section "${heading}" is missing or out of GOV.UK order`);
      at = found + 1;
    }
    assert.ok(!main.includes('c-on-this-page'), `${file}: GOV.UK colour pages have no "On this page" box`);
    assert.ok(main.includes('class="c-swatch-list'), `${file}: swatches use the GOV.UK swatch list`);
  }
  // The Colour overview page has no swatch outline to check, but GOV.UK's
  // colour overview has no "On this page" box either.
  assert.ok(!readFileSync(`${BUILD}/colour.html`, 'utf8').includes('c-on-this-page'), 'colour: GOV.UK colour pages have no "On this page" box');
  for (const file of ['colour-social', 'colour-maps', 'colour-illustrations']) {
    const main = readFileSync(`${BUILD}/${file}.html`, 'utf8');
    // The colour pictures are on the page, not in example frames. The one
    // frame allowed is the working OpenStreetMap example on Map colours.
    const frames = [...main.matchAll(/<iframe\b[^>]*\bsrc="[^"]*examples\/([a-z0-9-]+)\.html/g)].map(match => match[1]);
    assert.deepEqual(frames, file === 'colour-maps' ? ['map-neighbourhood-records'] : [], `${file}: colour pictures are on the page, not in example frames${file === 'colour-maps' ? ', and the working OpenStreetMap example is framed' : ''}`);
    assert.ok(!main.includes('Indicative examples for illustrative purposes only.'), `${file}: no shared example disclaimer`);
  }
  // Web-app colours keeps its rule examples in frames, so check only the colour
  // pictures: each is on the page, not framed.
  for (const [file, figures] of [['colour-web-app', ['web-dashboard', 'mobile-web', 'app-header-1', 'app-header-2', 'app-examples']]]) {
    const main = readFileSync(`${BUILD}/${file}.html`, 'utf8');
    for (const id of figures) assert.ok(main.includes(`role="img" aria-labelledby="${id}-t ${id}-d"`), `${file}: the ${id} picture is on the page`);
    assert.ok(!/<iframe[^>]+(?:web|app)-colour-/.test(main), `${file}: these pictures are on the page, not in example frames`);
  }
  // Each colour example on the page says once, in its own caption or lead,
  // that its data is invented or synthetic. A shared page-level disclaimer
  // repeated the same statement up to 6 times, so it is not used. Drawings
  // (SVG text) are left out: a drawn label is part of the picture.
  for (const file of ['colour-web-app', 'colour-social', 'colour-maps', 'chart-colour']) {
    const main = readFileSync(`${BUILD}/${file}.html`, 'utf8');
    assert.ok(!main.includes('Indicative examples for illustrative purposes only.'), `${file}: no shared example disclaimer`);
    // Each example block, from its opening div to the matching closing div.
    const examples = [...main.matchAll(/<div class="c-colour-example">/g)].map(match => {
      const tags = /<\/?div\b[^>]*>/g;
      tags.lastIndex = match.index;
      let depth = 0;
      for (let tag; (tag = tags.exec(main));) {
        depth += tag[0].startsWith('</') ? -1 : 1;
        if (depth === 0) return main.slice(match.index, tags.lastIndex);
      }
      return main.slice(match.index);
    });
    assert.ok(examples.length > 0, `${file}: has colour examples`);
    for (const [index, example] of examples.entries()) {
      const words = decode(example.replace(/<svg\b[\s\S]*?<\/svg>/g, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
      const statements = words.split(/(?<=[.!?])\s+/).filter(sentence => /\b(invented|synthetic|simulated)\b/i.test(sentence));
      assert.equal(statements.length, 1, `${file}: colour example ${index + 1} says once that it is invented (found ${statements.length}: ${statements.join(' | ')})`);
    }
  }
  // Each example keeps its invented-data label and its data table.
  for (const [file, count] of [['chart-colour', 4], ['colour-maps', 1]]) {
    const main = readFileSync(`${BUILD}/${file}.html`, 'utf8');
    assert.ok((main.match(/<details class="govuk-details"><summary class="govuk-details__summary"><span class="govuk-details__summary-text">Show the data/g) || []).length >= count, `${file}: every GOV.UK example keeps its data table`);
  }
}
console.log(`Colour record is consistent: ${Object.keys(colours).length} GOV.UK colours across ${Object.keys(pages).length} pages, read ${data.source.read_on}.`);
