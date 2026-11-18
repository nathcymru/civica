import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import YAML from 'yaml';
import { chartColour, chartSeriesStyle, chartContrast, CHART_COLOUR_SPEC } from '../design-system/chart-colours.mjs';

const readExamples = name => YAML.parse(readFileSync(`docs/data/${name}-examples.yml`, 'utf8')).examples;
const colours = readExamples('data-colour');
const dashboards = readExamples('dashboard-data');
const identities = readExamples('personalisation');
const palettes = JSON.parse(readFileSync('design-system/palettes.json', 'utf8')).palettes;
const exampleUrl = id => `/docs/build/examples/${id}.html`;
const rgb = hex => `rgb(${hex.slice(1).match(/../g).map(channel => parseInt(channel, 16)).join(', ')})`;
const clean = text => text.replace(/\s+/g, ' ').trim();
const numeric = text => Number(text.replace('−', '-'));
const govuk = JSON.parse(readFileSync('docs/data/govuk-brand-colours.json', 'utf8'));
const tableRows = table => table.locator('tbody tr').evaluateAll(rows => rows.map(row => [...row.querySelectorAll('th,td')].map(cell => cell.textContent.replace(/\s+/g, ' ').trim())));

// The guide-wide suite covers general accessibility and source rendering. These
// checks own the numerical meaning and the separation of colour from identity.
test('categorical line chart takes civica-chart-1 to civica-chart-4 in order, in light and dark mode', async ({ page }) => {
  const spec = colours['data-colour-categorical'];
  const data = spec.chart_data;
  // civica-chart-N in the first (light) block of the theme, and the same in dark mode.
  const theme = readFileSync('themes/civica.yaml', 'utf8');
  const themeHex = n => theme.match(new RegExp(`"civica-chart-${n}": "(#[0-9A-F]{6})"`))[1];
  for (const [index, series] of data.series.entries()) {
    expect(series.theme_colour).toBe(`civica-chart-${index + 1}`);
    expect(series.hex).toBe(themeHex(index + 1));
    expect(series.hex).toBe(govuk.colours[series.colour_id].hex);
  }
  await page.goto(exampleUrl('data-colour-categorical'));
  for (const mode of ['light', 'dark']) {
    const svg = page.locator(`svg[data-chart-mode="${mode}"]`);
    await expect(svg).toHaveAttribute('role', 'img');
    const lines = await svg.locator('path[data-series]').evaluateAll(nodes => nodes.map(node => ({ key: node.dataset.series, values: node.dataset.values.split(',').map(value => value === '' ? null : Number(value)), stroke: node.getAttribute('stroke'), dash: node.getAttribute('stroke-dasharray') ?? '' })));
    expect(lines.map(line => line.key)).toEqual(data.series.map(series => series.key));
    expect(new Set(lines.map(line => line.dash)).size).toBe(lines.length);
    for (const [index, series] of data.series.entries()) {
      expect(lines[index].values).toEqual(series.values);
      expect(lines[index].stroke).toBe(series.hex);
      expect(lines[index].dash).toBe(series.line_dash.join(' '));
    }
    // Each room is named twice: in the legend and at the end of its line.
    const labels = await svg.locator('text').allTextContents();
    for (const series of data.series) expect(labels.filter(label => label === series.label)).toHaveLength(2);
    expect(labels).toContain('No data');
  }
  const rows = await tableRows(page.getByRole('table'));
  expect(rows).toEqual(data.times.map((time, index) => [time, ...data.series.map(series => series.values[index] === null ? 'Not supplied' : String(series.values[index]))]));
  await expect(page.locator('.c-example-canvas')).not.toContainText(/Vivid|Muted|OKLCH|GOV\.UK/i);
  await expect(page.getByRole('button')).toHaveCount(0);
});

test('quantitative heatmaps use listed scale steps, print every value and keep missing distinct from zero', async ({ page }) => {
  const reference = colours['data-colour-quantitative'].colour_reference;
  const chartScaleIds = govuk.pages.charts.sequential.flatMap(scale => scale.colours);
  await page.goto(exampleUrl('data-colour-quantitative'));
  for (const name of ['sequential', 'divergent']) {
    const scale = reference[name];
    for (const step of scale.steps) {
      // Each step is a named chart scale colour, copied unchanged; nothing is interpolated.
      expect(chartScaleIds).toContain(step.colour);
      expect(step.hex).toBe(govuk.colours[step.colour].hex);
      expect(step.name).toBe(govuk.colours[step.colour].name);
    }
    const svg = page.locator(`svg[data-chart="heatmap-${name}"]`);
    await expect(svg).toHaveAttribute('role', 'img');
    const cells = await svg.locator('rect[data-room]').evaluateAll(nodes => nodes.map(node => ({ room: node.dataset.room, value: node.dataset.value, step: node.dataset.step ?? null, fill: node.getAttribute('fill') })));
    expect(cells).toHaveLength(scale.rows.length * scale.days.length);
    for (const [r, row] of scale.rows.entries()) for (const [c, value] of row.values.entries()) {
      const cell = cells[r * row.values.length + c];
      expect(cell.room).toBe(row.room);
      if (value === null) {
        expect(cell.value).toBe('missing');
        expect(scale.steps.map(step => step.hex)).not.toContain(cell.fill);
        continue;
      }
      expect(Number(cell.value)).toBe(value);
      const step = scale.steps.find(item => item.colour === row.colour_ids[c]);
      expect(cell.fill).toBe(step.hex);
      expect(value).toBeGreaterThanOrEqual(step.from);
      expect(value).toBeLessThanOrEqual(step.to);
    }
    const table = page.getByRole('table', { name: name === 'sequential' ? /Energy used each day by room/ : /Difference from the 20 °C target/ });
    const rendered = await tableRows(table);
    expect(rendered.map(row => row[0])).toEqual(scale.rows.map(row => row.room));
    for (const [r, row] of scale.rows.entries()) for (const [c, value] of row.values.entries()) {
      if (value === null) expect(rendered[r][c + 1]).toBe('Not supplied');
      else expect(numeric(rendered[r][c + 1])).toBeCloseTo(value, 5);
    }
  }
  // A supplied zero takes a colour; a missing reading does not.
  expect(reference.sequential.rows.some(row => row.values.includes(0))).toBe(true);
  await expect(page.locator('.c-example-canvas')).toContainText('outside this scale');
  // The two-scale limit is stated once, on the Chart colours page, not in the example.
  expect(readFileSync('docs/build/styles/chart-colour.html', 'utf8')).toContain('Use no more than 2 colour scales in one chart.');
  await expect(page.locator('.c-example-canvas')).not.toContainText(/interpolate/i);
});

test('electricity dashboard columns, table and partial total describe the same six intervals', async ({ page }) => {
  const data = dashboards['dashboard-data-electricity-monitor'].chart_data;
  const known = data.values.filter(value => value !== null);
  expect(data.known_interval_sum).toBeCloseTo(known.reduce((sum, value) => sum + value, 0), 10);
  expect(data.known_interval_count).toBe(known.length);
  expect(data.expected_interval_count).toBe(data.values.length);
  expect((Date.parse(data.period_end) - Date.parse(data.period_start)) / 3_600_000).toBe(data.values.length);
  expect(data.colour).toBe(chartColour(data.source_identity, { mode: 'light' }));
  await page.goto(exampleUrl('dashboard-data-electricity-monitor'));
  const rows = await tableRows(page.getByRole('table'));
  expect(rows.map(row => row[1])).toEqual(data.values.map(value => value === null ? 'Not supplied' : value.toFixed(2)));
  expect(rows.map(row => row[2])).toEqual(data.values.map(value => value === null ? 'Missing interval' : 'Complete interval'));
  const bars = await page.locator('.civica-data-dashboard__bars rect').evaluateAll(nodes => nodes.map(node => ({
    x: Number(node.getAttribute('x')), y: Number(node.getAttribute('y')), height: Number(node.getAttribute('height')),
    fill: getComputedStyle(node).fill, opacity: getComputedStyle(node).opacity,
  })));
  expect(bars).toHaveLength(known.length);
  let column = 0;
  for (const [index, value] of data.values.entries()) {
    if (value === null) { expect(bars.some(bar => bar.x === 78 + 90 * index)).toBe(false); continue; }
    const bar = bars[column++];
    expect(bar.x).toBe(78 + 90 * index);
    expect(bar.height / 300).toBeCloseTo(value, 10);
    expect(bar.y + bar.height).toBe(260);
    expect(bar.fill).toBe(rgb(data.colour));
    expect(bar.opacity).toBe('1');
  }
  const metrics = page.locator('.civica-data-dashboard__metrics');
  await expect(metrics).toContainText(`${data.known_interval_sum.toFixed(2)} kWh`);
  await expect(metrics).toContainText(`${known.length} of ${data.values.length}`);
  await expect(metrics).toContainText('The full period total is unknown');
  await expect(page.locator('.civica-data-dashboard')).toContainText('not current power readings');
  await expect(page.locator(`time[datetime="${data.reported_at}"]`)).toBeVisible();
  await page.getByRole('link', { name: 'Check the source and missing coverage' }).click();
  await expect(page).toHaveURL(/#electricity-source$/);
  await expect(page.locator('#electricity-source')).toBeInViewport();
});

test('room report coverage excludes old readings without erasing them or treating unconfigured rooms as zero', async ({ page }) => {
  await page.goto(exampleUrl('dashboard-data-room-report'));
  const rows = page.locator('.civica-data-dashboard__room-list > div');
  const records = await rows.evaluateAll(nodes => nodes.map(node => ({
    name: node.querySelector('dt').textContent.trim(), text: node.querySelector('dd').textContent.replace(/\s+/g, ' ').trim(),
    time: node.querySelector('time')?.getAttribute('datetime') ?? null,
  })));
  expect(records.map(record => record.name)).toEqual(['Kitchen', 'Study', 'Bedroom', 'Garden room']);
  const end = Date.parse('2026-11-12T12:00:00+00:00'), start = end - 5 * 60_000;
  const configured = records.filter(record => record.time !== null);
  const recent = configured.filter(record => Date.parse(record.time) >= start && Date.parse(record.time) <= end);
  expect(configured).toHaveLength(3);
  expect(recent.map(record => record.name)).toEqual(['Kitchen', 'Study']);
  await expect(page.locator('.civica-data-dashboard')).toContainText(`${recent.length} of ${configured.length} configured sensors`);
  const readings = recent.map(record => Number(record.text.match(/([\d.]+) °C/)[1]));
  expect(readings[0] - readings[1]).toBeCloseTo(0.7, 10);
  expect(Math.abs(Date.parse(recent[0].time) - Date.parse(recent[1].time))).toBe(60_000);
  expect(records[2].text).toContain('Last supplied value: 21.0 °C');
  expect(records[2].text).toContain('temperature at 12:00 is unknown');
  expect(records[3].time).toBeNull();
  expect(records[3].text).toContain('No temperature sensor configured');
  expect(records[3].text).toContain('not a zero temperature or evidence of a device failure');
  await page.getByRole('link', { name: 'Read the bedroom record' }).click();
  await expect(page).toHaveURL(/#room-report-bedroom$/);
  await expect(page.locator('#room-report-bedroom')).toBeInViewport();
});

test('optional household identity keeps its text and real home link without requiring project artwork', async ({ page }) => {
  await page.goto('/docs/build/get-started/personalisation.html');
  const guide = page.locator('main');
  await expect(guide).toContainText('not new theme settings');
  await expect(guide).toContainText('has not been implemented');
  await expect(guide).toContainText('current companion still inserts civica artwork');
  expect(Object.keys(identities)).toHaveLength(3);
  for (const id of Object.keys(identities)) {
    await page.goto(exampleUrl(id));
    const canvas = page.locator('.c-example-canvas');
    const home = canvas.locator('header a');
    const name = id === 'identity-business-name' ? 'Example workshop' : 'Morgan household';
    await expect(home).toHaveAccessibleName(name);
    await expect(home).toHaveText(name);
    await expect(canvas.locator('button,input,select,textarea')).toHaveCount(0);
    await expect(canvas.locator('img[src*="civica"], header img')).toHaveCount(0);
    const illustrations = home.locator('svg');
    for (const illustration of await illustrations.all()) await expect(illustration).toHaveAttribute('aria-hidden', 'true');
    // Model the image being unavailable: the name and navigation must survive.
    await illustrations.evaluateAll(nodes => nodes.forEach(node => node.remove()));
    await expect(home).toHaveAccessibleName(name);
    await home.focus();
    await home.press('Enter');
    await expect(page).toHaveURL(new RegExp(`#${id}-home$`));
    await expect(page.locator(`main[id="${id}-home"]`)).toBeInViewport();
  }
});

test('every theme colour preview changes only the header colour and retains household identity and state', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto('/docs/build/styles/colour.html');
  const demo = page.locator('[data-palette-demo]');
  const select = demo.getByLabel('Theme colour');
  const header = demo.locator('.c-demo__header');
  const state = clean(await demo.locator('.c-status').textContent());
  const shell = page.locator('.c-header');
  const shellIdentity = await shell.textContent();
  const shellColour = await shell.evaluate(node => getComputedStyle(node).backgroundColor);
  await expect(select.locator('option')).toHaveCount(palettes.length);
  const requests = [];
  const track = request => requests.push(request.url());
  page.on('request', track);
  try {
    for (const palette of palettes) {
      await select.selectOption({ label: palette.name });
      await expect(header).toHaveCSS('background-color', rgb(palette.primary.hex));
      await expect(demo).toHaveCSS('background-color', 'rgb(255, 255, 255)');
      await expect(header).toHaveText('Morgan household');
      await expect(header.locator('img,svg')).toHaveCount(0);
      await expect(demo.locator('.c-status')).toHaveText(state);
      await expect(demo.getByRole('status')).toHaveText(`${palette.name} preview. This choice affects this example only.`);
      await expect(shell).toHaveCSS('background-color', shellColour);
      expect(await shell.textContent()).toBe(shellIdentity);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    }
    expect(requests, 'The documentation colour preview must not fetch identity artwork or call a backend').toEqual([]);
  } finally { page.off('request', track); }
});

test('data meanings and identity remain available without JavaScript at a narrow width', async ({ browser, baseURL }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 320, height: 800 }, baseURL });
  const page = await context.newPage();
  try {
    for (const id of ['data-colour-categorical', 'data-colour-quantitative', 'dashboard-data-electricity-monitor', 'dashboard-data-room-report', 'identity-household-name']) {
      await page.goto(exampleUrl(id));
      await expect(page.locator('.c-example-canvas')).toBeVisible();
      if (id === 'data-colour-categorical') await expect(page.getByRole('table')).toContainText('Not supplied');
      if (id === 'data-colour-quantitative') {
        await expect(page.getByRole('table')).toHaveCount(2);
        await expect(page.locator('rect[data-value="missing"]')).toHaveCount(2);
      }
      if (id === 'dashboard-data-electricity-monitor') await expect(page.getByRole('table')).toContainText('Not supplied');
      if (id === 'dashboard-data-room-report') await expect(page.locator('.civica-data-dashboard__room-list > div')).toHaveCount(4);
      if (id === 'identity-household-name') await expect(page.getByRole('link', { name: 'Morgan household' })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), id).toBe(true);
    }
  } finally { await context.close(); }
});
