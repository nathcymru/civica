import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CHART_COLOUR_SPEC as spec, chartColour, chartSeriesStyle, chartSlotColour, chartLabelColour, chartAxisColour } from '../design-system/chart-colours.mjs';

const govuk = JSON.parse(readFileSync('docs/data/govuk-brand-colours.json', 'utf8'));
const examples = spec.exampleKeys.map(({ key }) => key);
const modes = ['light', 'dark'];
const categorical = govuk.pages.charts.categorical.filter(item => !item.role).map(item => govuk.colours[item.colour].hex);

test('the categorical palette is the GOV.UK chart palette, unchanged and in order', () => {
  assert.deepEqual(spec.categorical.map(colour => colour.hex), categorical);
  assert.deepEqual(spec.categorical.map(colour => colour.name), govuk.pages.charts.categorical.filter(item => !item.role).map(item => govuk.colours[item.colour].name));
  const axes = govuk.pages.charts.categorical.find(item => item.role === 'Axes & lines').colour;
  const labels = govuk.pages.charts.categorical.find(item => item.role === 'Labels').colour;
  assert.equal(chartAxisColour(), govuk.colours[axes].hex);
  assert.equal(chartLabelColour('light'), govuk.colours[labels].hex);
  assert.equal(chartLabelColour('dark'), govuk.colours.white.hex);
  assert.equal(spec.source.url, govuk.pages.charts.url);
});

test('every series colour is a GOV.UK categorical colour, the same in light and dark mode', () => {
  const identities = [...Object.keys(spec.roles).filter(role => role !== 'consumption'), ...examples, ...Array.from({ length: 300 }, (_, i) => `sensor.additional_energy_${i}`)];
  for (const key of identities) {
    const light = chartColour(key, { mode: 'light' });
    assert.ok(categorical.includes(light), `${key} uses ${light}`);
    assert.equal(chartColour(key, { mode: 'dark' }), light, key);
  }
  // Only the total consumption line follows the label colour.
  assert.equal(chartColour('consumption'), chartLabelColour('light'));
  assert.equal(chartColour('consumption', { mode: 'dark' }), chartLabelColour('dark'));
});

test('energy roles keep fixed GOV.UK colours, and shared colours differ by pattern', () => {
  for (const [key, role] of Object.entries(spec.roles)) {
    if (role.colour === 'labels') continue;
    assert.equal(chartColour(key), spec.categorical.find(colour => colour.id === role.colour).hex, key);
    assert.equal(chartSeriesStyle(key).pattern, role.pattern, key);
  }
  const roleStyles = Object.keys(spec.roles).map(key => JSON.stringify([chartSeriesStyle(key).color, chartSeriesStyle(key).pattern]));
  assert.equal(new Set(roleStyles).size, roleStyles.length, 'No two energy roles share both colour and pattern');
});

test('the 24 named examples use all six colours and stay distinct through pattern, dash and marker', () => {
  assert.equal(examples.length, 24);
  for (const mode of modes) {
    const styles = examples.map(key => chartSeriesStyle(key, { mode }));
    assert.equal(new Set(styles.map(style => style.color)).size, 6);
    assert.equal(new Set(styles.map(style => JSON.stringify([style.color, style.pattern, style.lineDash, style.symbol]))).size, 24);
  }
});

test('a second meter in a family keeps the family colour with its own pattern', () => {
  for (const role of ['grid-consumption', 'grid-return', 'solar', 'gas', 'water', 'battery-in', 'battery-out']) {
    const one = chartSeriesStyle(`${role}:meter-one`);
    assert.equal(one.color, chartColour(role), role);
    assert.notEqual(one.pattern, 'solid', role);
    assert.deepEqual(chartSeriesStyle(`${role}:meter-one`), one);
  }
});

test('identity survives ordering, filtering, extension and equivalent Unicode without a theme input', () => {
  for (const mode of modes) {
    const original = new Map(examples.map(key => [key, chartSeriesStyle(key, { mode })]));
    for (const key of [...examples].reverse().concat('sensor.newly_added_energy')) {
      if (original.has(key)) assert.deepEqual(chartSeriesStyle(key, { mode }), original.get(key));
    }
  }
  assert.equal(chartColour(' sensor.café '), chartColour('sensor.café'));
  for (const key of ['constructor', '__proto__', 'toString', 'constructor:meter']) assert.ok(categorical.includes(chartColour(key)), key);
  const beforeEviction = chartSeriesStyle(examples[0]);
  for (let i = 0; i < 2200; i++) chartColour(`sensor.cache_eviction_${i}`);
  assert.deepEqual(chartSeriesStyle(examples[0]), beforeEviction);
});

test('returned styles cannot change shared state', () => {
  const original = chartSeriesStyle('gas');
  const modified = chartSeriesStyle('gas'); modified.lineDash.push(999);
  assert.deepEqual(chartSeriesStyle('gas'), original);
  assert.throws(() => { spec.roles.solar.colour = 'blue'; }, TypeError);
  for (const style of examples.map(key => chartSeriesStyle(key))) {
    assert.ok(spec.patterns.includes(style.pattern));
    assert.ok(style.lineDash.every(value => Number.isFinite(value) && value > 0));
    assert.ok(Number.isInteger(style.index) && style.index >= 0);
  }
});

test('numbered theme slots keep the energy mapping, then repeat the six colours', () => {
  const roles = Object.entries(spec.roles).sort((a, b) => a[1].index - b[1].index).map(([role]) => role);
  for (let slot = 1; slot <= roles.length; slot++) assert.equal(chartSlotColour(slot), chartColour(roles[slot - 1]));
  for (let slot = roles.length + 1; slot <= 24; slot++) assert.equal(chartSlotColour(slot), categorical[(slot - roles.length - 1) % 6]);
  assert.throws(() => chartSlotColour(25), RangeError);
});

test('invalid identities and modes fail explicitly', () => {
  for (const key of ['', ' ', null, 123]) assert.throws(() => chartColour(key), TypeError);
  assert.throws(() => chartColour('grid-consumption', { mode: 'auto' }), TypeError);
});
