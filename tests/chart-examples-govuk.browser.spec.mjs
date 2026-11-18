import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync } from 'node:fs';
import YAML from 'yaml';

// Like-for-like versions of the GOV.UK Brand Guidelines chart compositions
// (https://brand.design-system.service.gov.uk/colour/charts/) with synthetic
// Home Assistant data. These checks own the colours, the data equivalence and
// the narrow-screen behaviour of each example.
const examples = YAML.parse(readFileSync('docs/data/data-colour-examples.yml', 'utf8')).examples;
const govuk = JSON.parse(readFileSync('docs/data/govuk-brand-colours.json', 'utf8'));
const exampleUrl = id => `/docs/build/examples/${id}.html`;
const tableRows = table => table.locator('tbody tr').evaluateAll(rows => rows.map(row => [...row.querySelectorAll('th,td')].map(cell => cell.textContent.replace(/\s+/g, ' ').trim())));
const tableHead = table => table.locator('thead th').evaluateAll(cells => cells.map(cell => cell.textContent.replace(/\s+/g, ' ').trim()));
const svgColours = svg => svg.evaluate(root => {
  const found = new Set();
  for (const node of [root, ...root.querySelectorAll('*')]) {
    for (const attribute of ['fill', 'stroke', 'stop-color', 'color']) {
      const value = node.getAttribute(attribute);
      if (value && !['none', 'currentColor', 'transparent'].includes(value)) found.add(value.toUpperCase());
    }
    if (node.getAttribute('style')?.match(/#[\da-f]{3,8}|rgb/i)) found.add(`style:${node.getAttribute('style')}`);
  }
  return [...found].sort();
});
// Every SVG element that paints must use an explicit, opaque colour attribute.
const paintedWithoutColour = svg => svg.evaluate(root => [...root.querySelectorAll('rect,circle,path,line,text,polygon,polyline,ellipse')]
  .filter(node => {
    const style = getComputedStyle(node);
    return (node.getAttribute('fill') === null && node.closest('[fill]') === null && style.fill !== 'none' && node.tagName !== 'line')
      || ['opacity', 'fill-opacity', 'stroke-opacity'].some(property => style[property] !== '1');
  }).map(node => node.outerHTML.slice(0, 80)));

const ids = ['chart-govuk-single', 'chart-govuk-multiple', 'chart-govuk-divergent', 'chart-govuk-social'];

for (const id of ids) {
  test(`${id} uses exactly its listed GOV.UK colours, labels synthetic data and works at 320px`, async ({ page }) => {
    const spec = examples[id];
    const listed = spec.colour_reference.govuk_colours;
    expect(spec.colour_reference.source).toBe(govuk.pages.charts.url);
    for (const colour of listed) {
      expect(govuk.colours[colour.id], `${id}: ${colour.id} is a GOV.UK colour`).toBeTruthy();
      expect(colour.hex).toBe(govuk.colours[colour.id].hex);
      expect(colour.name).toBe(govuk.colours[colour.id].name);
    }
    await page.setViewportSize({ width: 320, height: 900 });
    await page.goto(exampleUrl(id));
    const canvas = page.locator('.c-example-canvas');
    const svg = canvas.locator('svg[data-chart]');
    await expect(svg).toHaveCount(1);
    expect(await svgColours(svg)).toEqual([...new Set(listed.map(colour => colour.hex))].sort());
    expect(await paintedWithoutColour(svg)).toEqual([]);
    // The visible colour list repeats the record, as the GOV.UK page does.
    const rendered = await canvas.locator('[data-govuk-colours] li').evaluateAll(items => items.map(item => [item.dataset.govukColour, item.dataset.hex, item.textContent]));
    expect(rendered.map(([colour, hex]) => [colour, hex])).toEqual(listed.map(colour => [colour.id, colour.hex]));
    for (const [index, [, , text]] of rendered.entries()) expect(text).toContain(`${listed[index].name} ${listed[index].hex}`);
    // Accessible graphic: an image with a title and description; its drawing is hidden.
    await expect(svg).toHaveAttribute('role', 'img');
    const [titleId, descId] = (await svg.getAttribute('aria-labelledby')).split(' ');
    await expect(svg.locator(`title#${titleId}`)).toHaveCount(1);
    await expect(svg.locator(`desc#${descId}`)).toHaveCount(1);
    await expect(svg.locator(':scope > g')).toHaveAttribute('aria-hidden', 'true');
    await expect(canvas.locator('figure figcaption')).toHaveCount(1);
    await expect(canvas).toContainText('Synthetic data');
    await expect(canvas).toContainText('not readings from a Home Assistant instance');
    if (id === 'chart-govuk-social') await expect(canvas).toContainText('Illustrative example');
    await expect(canvas.getByRole('table')).toHaveCount(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${id}: no horizontal scroll`).toBe(true);
    const box = await svg.boundingBox();
    expect(box.width).toBeLessThanOrEqual(320);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
}

test('single category bars and table show the same daily energy values', async ({ page }) => {
  const data = examples['chart-govuk-single'].chart_data;
  await page.goto(exampleUrl('chart-govuk-single'));
  const bars = await page.locator('svg[data-chart] rect[data-value]').evaluateAll(nodes => nodes.map(node => ({ label: node.dataset.label, value: Number(node.dataset.value), height: Number(node.getAttribute('height')), fill: node.getAttribute('fill') })));
  expect(bars.map(bar => [bar.label, bar.value])).toEqual(data.rows.map(row => [row.label, row.value]));
  for (const bar of bars) {
    expect(bar.fill).toBe(govuk.colours.blue.hex);
    expect(bar.height / bar.value).toBeCloseTo(bars[0].height / bars[0].value, 1);
  }
  const table = page.getByRole('table');
  expect(await tableHead(table)).toEqual(['Day', 'Energy (kWh)']);
  expect(await tableRows(table)).toEqual(data.rows.map(row => [row.day, row.value.toFixed(1)]));
  const labels = await page.locator('svg[data-chart] text').allTextContents();
  for (const row of data.rows) expect(labels).toContain(row.value.toFixed(1));
});

test('multiple category lines and table show the same temperatures, with distinct dashes and end labels', async ({ page }) => {
  const data = examples['chart-govuk-multiple'].chart_data;
  await page.goto(exampleUrl('chart-govuk-multiple'));
  const lines = await page.locator('svg[data-chart] path[data-series]').evaluateAll(nodes => nodes.map(node => ({ key: node.dataset.series, values: node.dataset.values.split(',').map(Number), points: node.getAttribute('d').match(/[ML][\d.]+ [\d.]+/g).length, stroke: node.getAttribute('stroke'), dash: node.getAttribute('stroke-dasharray') ?? '' })));
  expect(lines.map(line => line.key)).toEqual(data.series.map(series => series.key));
  expect(new Set(lines.map(line => line.dash)).size).toBe(lines.length);
  expect(new Set(lines.map(line => line.stroke)).size).toBe(lines.length);
  for (const [index, series] of data.series.entries()) {
    expect(lines[index].values).toEqual(series.values);
    expect(lines[index].points).toBe(data.times.length);
    expect(lines[index].stroke).toBe(govuk.colours[series.colour_id].hex);
    expect(lines[index].dash).toBe(series.line_dash.join(' '));
  }
  const labels = await page.locator('svg[data-chart] text').allTextContents();
  // Each series is named twice: once in the legend on top, once at its line end.
  for (const series of data.series) expect(labels.filter(label => label === series.label)).toHaveLength(2);
  const table = page.getByRole('table');
  expect(await tableHead(table)).toEqual(['Time', ...data.series.map(series => series.label)]);
  expect(await tableRows(table)).toEqual(data.times.map((time, index) => [time, ...data.series.map(series => series.values[index].toFixed(1))]));
});

test('divergent bars and table show the same hours, with under target left and over target right', async ({ page }) => {
  const data = examples['chart-govuk-divergent'].chart_data;
  await page.goto(exampleUrl('chart-govuk-divergent'));
  const segments = await page.locator('svg[data-chart] rect[data-band]').evaluateAll(nodes => nodes.map(node => ({ room: node.dataset.room, band: node.dataset.band, value: Number(node.dataset.value), x: Number(node.getAttribute('x')), width: Number(node.getAttribute('width')), fill: node.getAttribute('fill') })));
  const centre = await page.locator('svg[data-chart] line[stroke-width="2"]').getAttribute('x1').then(Number);
  for (const row of data.rows) {
    expect(row['far-under'] + row.under + row.on + row.over + row['far-over']).toBe(data.scheduled_hours_per_room);
    for (const band of data.bands) {
      const segment = segments.find(item => item.room === row.label && item.band === band.id);
      expect(segment.value).toBe(row[band.id]);
      expect(segment.fill).toBe(govuk.colours[band.colour_id].hex);
      expect((segment.width + 1) / segment.value).toBe(5);
      if (band.id.includes('under')) expect(segment.x + segment.width).toBeLessThanOrEqual(centre);
      else expect(segment.x).toBeGreaterThanOrEqual(centre);
    }
    const near = segments.find(item => item.room === row.label && item.band === 'under'), far = segments.find(item => item.room === row.label && item.band === 'far-under');
    expect(far.x).toBeLessThan(near.x);
  }
  const table = page.getByRole('table');
  expect(await tableRows(table)).toEqual(data.rows.map(row => [row.label, row['far-under'], row.under, row.on, row.over, row['far-over']].map(String)));
  const legend = await page.locator('svg[data-chart] text').allTextContents();
  for (const band of data.bands) expect(legend).toContain(band.label);
});

test('social graphic circles and table show the same automation counts, sized by area', async ({ page }) => {
  const data = examples['chart-govuk-social'].chart_data;
  await page.goto(exampleUrl('chart-govuk-social'));
  const circles = await page.locator('svg[data-chart] circle[data-value]').evaluateAll(nodes => nodes.map(node => ({ label: node.dataset.automation, value: Number(node.dataset.value), r: Number(node.getAttribute('r')) })));
  expect(circles.map(circle => [circle.label, circle.value])).toEqual(data.rows.map(row => [row.label, row.runs]));
  for (const circle of circles) expect(circle.r ** 2 / circle.value).toBeCloseTo(circles[0].r ** 2 / circles[0].value, 1);
  expect(await tableRows(page.getByRole('table'))).toEqual(data.rows.map((row, index) => [row.label, String(index + 1), row.runs.toLocaleString('en-GB')]));
  const labels = await page.locator('svg[data-chart] text').allTextContents();
  for (const row of data.rows) expect(labels).toContain(row.runs.toLocaleString('en-GB'));
  // Accent and additional colours appear only on the Blue shade 50% background.
  const background = page.locator('svg[data-chart] rect').first();
  await expect(background).toHaveAttribute('fill', govuk.colours['blue-shade-50'].hex);
  await expect(background).toHaveAttribute('width', '320');
  await expect(background).toHaveAttribute('height', '320');
});
