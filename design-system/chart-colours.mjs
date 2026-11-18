import specification from './chart-colours.json' with { type: 'json' };

// civica chart colours. The six categorical colours come unchanged from the
// GOV.UK Brand Guidelines chart palette (see chart-colours.json `source`).
// Colours are the same in light and dark mode; only the label colour used for
// the total consumption line follows the mode. Because six colours cannot tell
// every series apart, each identity also gets a stable pattern, dash and marker.
const freeze = (value) => {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
};
export const CHART_COLOUR_SPEC = freeze(specification);
const styleCache = new Map();
const CACHE_LIMIT = CHART_COLOUR_SPEC.memoization.maximumEntries;
const CATEGORICAL = CHART_COLOUR_SPEC.categorical;
const colourById = Object.fromEntries(CATEGORICAL.map((colour) => [colour.id, colour.hex]));
const roleFor = (key) => Object.hasOwn(CHART_COLOUR_SPEC.roles, key) ? CHART_COLOUR_SPEC.roles[key] : undefined;
const normalise = (key) => {
  if (typeof key !== 'string' || !key.trim()) throw new TypeError('A non-empty stable chart identity is required');
  return key.trim().normalize('NFC');
};
const checkMode = (mode) => {
  if (!['light', 'dark'].includes(mode)) throw new TypeError('Chart mode must be light or dark');
  return mode;
};
function hash(key) {
  let value = 2166136261;
  for (let i = 0; i < key.length; i++) value = Math.imul(value ^ key.charCodeAt(i), 16777619);
  value ^= value >>> 16; value = Math.imul(value, 0x85ebca6b);
  value ^= value >>> 13; value = Math.imul(value, 0xc2b2ae35);
  return (value ^ value >>> 16) >>> 0;
}
const decode = (channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
const channels = (colour) => colour.match(/[\da-f]{2}/gi).map((channel) => parseInt(channel, 16) / 255);
const luminance = (colour) => channels(colour).map(decode).reduce((sum, channel, i) => sum + channel * [0.2126, 0.7152, 0.0722][i], 0);
export function chartContrast(one, two) {
  const a = luminance(one), b = luminance(two);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

/** The label colour: Black on light surfaces, White on dark surfaces. */
export const chartLabelColour = (mode = 'light') => CHART_COLOUR_SPEC.labels[checkMode(mode)].hex;
/** GOV.UK "Axes & lines": Black tint 80%, in both modes. */
export const chartAxisColour = () => CHART_COLOUR_SPEC.axesAndLines.hex;

function resolve(key, mode) {
  const cacheKey = `${mode}\0${key}`;
  if (styleCache.has(cacheKey)) return styleCache.get(cacheKey);
  const family = key.includes(':') ? key.slice(0, key.indexOf(':')) : '';
  const role = roleFor(key) ?? roleFor(family);
  const value = hash(key);
  let colour, pattern, index;
  if (role) {
    colour = role.colour === 'labels' ? chartLabelColour(mode) : colourById[role.colour];
    // A second meter in a family keeps the family colour and gets its own pattern.
    pattern = roleFor(key) ? role.pattern : CHART_COLOUR_SPEC.patterns[1 + hash(`${key}\0pattern`) % (CHART_COLOUR_SPEC.patterns.length - 1)];
    index = roleFor(key) ? role.index : value;
  } else {
    // One slot per colour and pattern pair, so series that share a colour
    // usually differ in pattern too.
    const slot = value % (CATEGORICAL.length * CHART_COLOUR_SPEC.patterns.length);
    colour = CATEGORICAL[slot % CATEGORICAL.length].hex;
    pattern = CHART_COLOUR_SPEC.patterns[Math.floor(slot / CATEGORICAL.length)];
    index = value;
  }
  const exact = roleFor(key)?.index;
  const dashIndex = (exact ?? hash(`${key}\0line`)) % CHART_COLOUR_SPEC.lineDashes.length;
  const symbolIndex = (exact ?? hash(`${key}\0symbol`)) % CHART_COLOUR_SPEC.symbols.length;
  const style = freeze({
    color: colour, index, pattern,
    lineDash: key === 'consumption' ? [7, 2] : [...CHART_COLOUR_SPEC.lineDashes[dashIndex]],
    symbol: CHART_COLOUR_SPEC.symbols[symbolIndex],
  });
  if (styleCache.size >= CACHE_LIMIT) styleCache.delete(styleCache.keys().next().value);
  styleCache.set(cacheKey, style);
  return style;
}

export function chartColour(key, { mode = 'light' } = {}) {
  return resolve(normalise(key), checkMode(mode)).color;
}

/** Colour plus the pattern, line dash and marker that also identify the series. */
export function chartSeriesStyle(key, { mode = 'light' } = {}) {
  const style = resolve(normalise(key), checkMode(mode));
  return { ...style, lineDash: [...style.lineDash] };
}

/** Colour for a numbered theme slot (1 to 24). */
export function chartSlotColour(slot, { mode = 'light' } = {}) {
  // Slots 1 to 9 keep their energy role mapping, in role index order.
  const roles = Object.entries(CHART_COLOUR_SPEC.roles).sort((a, b) => a[1].index - b[1].index).map(([role]) => role);
  if (!Number.isInteger(slot) || slot < 1 || slot > 24) throw new RangeError('Chart slots run from 1 to 24');
  return slot <= roles.length ? chartColour(roles[slot - 1], { mode }) : CATEGORICAL[(slot - roles.length - 1) % CATEGORICAL.length].hex;
}
