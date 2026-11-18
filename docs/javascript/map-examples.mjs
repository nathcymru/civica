import * as maplibregl from 'maplibre-gl';
import { osm } from '@versatiles/style';

// Documentation only. Locations are invented at public Cardiff Bay landmarks;
// they are never read from Home Assistant, geolocation, accounts or a tracker.
export const MAP_RECORDS = Object.freeze([
  { id: 'a', label: 'A — example bicycle', place: 'Near the Senedd', coordinates: [-3.1633, 51.4637], accuracy: 30 },
  { id: 'b', label: 'B — example tool case', place: 'Near the Pierhead Building', coordinates: [-3.1638, 51.4632], accuracy: null },
  { id: 'c', label: 'Example tablet', place: 'Not supplied', coordinates: null, accuracy: null },
]);
const CENTER = [-3.1638, 51.4635];
const BOUNDS = [[-3.182, 51.452], [-3.143, 51.475]];
const ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>';

// The GOV.UK map example colours (docs/data/govuk-brand-colours.json,
// pages.maps.example), unchanged and the same in light and dark mode:
// land Black tint 95% with a Black tint 80% outline, sea Teal tint 95%,
// coastal areas Teal tint 80%, labels Black, and data points in Accent green
// with a Primary green outline. GOV.UK gives no road or building colours, so
// roads are White with Black tint 80% casings and buildings Black tint 80%,
// both from the GOV.UK Neutrals. They never follow the household's theme colour.
export const MAP_ROLES = Object.freeze({
  land: '#F3F3F3', outline: '#CECECE', water: '#F3F9F9', coast: '#D0E6E7',
  surface: '#FFFFFF', structure: '#CECECE', ink: '#0B0C0C', point: '#66F39E', pointOutline: '#0F7A52',
});

export function mapStyle(tilejson) {
  const roles = MAP_ROLES;
  const colors = Object.fromEntries(osm.colorKeys.map(key => {
    let color = roles.land;
    if (/^(water|glacier|labelWater)$/.test(key)) color = key === 'labelWater' ? roles.ink : roles.water;
    else if (/^label/.test(key)) color = key === 'labelHalo' ? roles.surface : roles.ink;
    else if (/^(road|transit|boundary|building)/.test(key)) color = /Bg$/.test(key) || key === 'building' || /^boundary|^transit/.test(key) ? roles.structure : roles.surface;
    return [key, color];
  }));
  const style = osm({ theme: 'muted', colors, urls: { osm: tilejson }, text: { language: 'local', transform: 'none' } });
  // MapLibre renders local fonts when glyphs is absent. Do not request a second
  // font/icon service. Keep source place names, roads, water and building labels.
  delete style.glyphs;
  delete style.sprite;
  style.projection = { type: 'mercator' };
  style.transition = { duration: 0, delay: 0 };
  style.layers = style.layers.filter(layer => layer.type !== 'symbol' || (layer.layout?.['text-field'] && !['pois', 'public_transport', 'addresses'].includes(layer['source-layer'])));
  for (const layer of style.layers) {
    if (layer.type === 'symbol') {
      delete layer.layout['icon-image'];
      layer.layout['text-font'] = ['Arial'];
      const nativeSize = layer.layout['text-size'];
      layer.layout['text-size'] = typeof nativeSize === 'number' ? Math.max(14, nativeSize) : 14;
      layer.paint ??= {};
      layer.paint['text-opacity'] = 1;
      layer.paint['text-color'] = roles.ink;
      layer.paint['text-halo-color'] = roles.surface;
      layer.paint['text-halo-width'] = 1.5;
    }
    if (layer.type === 'line' && /^boundary/.test(layer.id)) layer.paint['line-width'] = 1;
    // Rivers and streams are lines, so Teal tint 95% would vanish on the land.
    if (layer.type === 'line' && /^water-(river|canal|stream|ditch)$/.test(layer.id)) layer.paint['line-color'] = roles.coast;
  }
  // Coastal areas are a Teal tint 80% band along every water edge, and the
  // land keeps its 1px Black tint 80% outline on top of that band.
  const edge = (layer, suffix, paint) => ({ id: `${layer.id}-${suffix}`, type: 'line', source: layer.source, 'source-layer': layer['source-layer'], ...(layer.filter ? { filter: layer.filter } : {}), paint });
  style.layers = style.layers.flatMap(layer => layer.type === 'fill' && /^water-(ocean|area)/.test(layer.id)
    ? [layer, edge(layer, 'coast', { 'line-color': roles.coast, 'line-width': 4 }), edge(layer, 'land-outline', { 'line-color': roles.outline, 'line-width': 1 })]
    : [layer]);
  for (const source of Object.values(style.sources)) source.attribution = ATTRIBUTION;
  return style;
}

// A geographic uncertainty boundary: 30 metres, unlike a decorative SVG ring.
function accuracyPolygon([longitude, latitude], metres) {
  const radius = metres / 6371008.8;
  const lat = latitude * Math.PI / 180;
  const lon = longitude * Math.PI / 180;
  const coordinates = Array.from({ length: 65 }, (_, index) => {
    const bearing = 2 * Math.PI * index / 64;
    const nextLat = Math.asin(Math.sin(lat) * Math.cos(radius) + Math.cos(lat) * Math.sin(radius) * Math.cos(bearing));
    const nextLon = lon + Math.atan2(Math.sin(bearing) * Math.sin(radius) * Math.cos(lat), Math.cos(radius) - Math.sin(lat) * Math.sin(nextLat));
    return [nextLon * 180 / Math.PI, nextLat * 180 / Math.PI];
  });
  return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [coordinates] } };
}

export function initialiseMapExample(root) {
  if (root.dataset.mapInitialised) return;
  root.dataset.mapInitialised = 'true';
  const load = root.querySelector('[data-map-load]');
  const stop = root.querySelector('[data-map-stop]');
  const canvas = root.querySelector('[data-map-canvas]');
  const status = root.querySelector('[data-map-status]');
  const selected = root.querySelector('[data-map-selected]');
  let map, config, generation = 0, timer, selectedId = 'a';
  const markers = [];
  const navigation = [...root.querySelectorAll('[data-map-command],[data-map-select]')];
  function inform(message, state) { status.textContent = message; root.dataset.mapState = state; }
  function clearMap() {
    generation += 1;
    clearTimeout(timer);
    markers.splice(0).forEach(marker => marker.remove());
    map?.remove(); map = undefined;
    root.mapExample = undefined;
    navigation.forEach(button => button.disabled = true);
    stop.disabled = true;
    canvas.hidden = true;
  }
  function select(id) {
    const record = MAP_RECORDS.find(record => record.id === id && record.coordinates);
    if (!record) return;
    selectedId = id;
    root.querySelectorAll('[data-map-select]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mapSelect === id)));
    selected.textContent = `Selected: ${record.label}. ${record.place}. ${record.accuracy ? `Reported accuracy: ${record.accuracy} metres.` : 'Accuracy not supplied.'} This is an invented observation.`;
    if (map) map.jumpTo({ center: record.coordinates });
  }
  function addAccuracy() {
    if (!map || map.getSource('example-accuracy')) return;
    map.addSource('example-accuracy', { type: 'geojson', data: accuracyPolygon(MAP_RECORDS[0].coordinates, 30) });
    map.addLayer({ id: 'example-accuracy-halo', type: 'line', source: 'example-accuracy', paint: { 'line-color': MAP_ROLES.surface, 'line-width': 5 } });
    map.addLayer({ id: 'example-accuracy-outline', type: 'line', source: 'example-accuracy', paint: { 'line-color': MAP_ROLES.ink, 'line-width': 1.5, 'line-dasharray': [3, 3] } });
  }
  async function start() {
    clearMap();
    const current = generation;
    load.disabled = true;
    inform('Loading OpenStreetMap. The example location records remain available below.', 'loading');
    try {
      const response = await fetch(root.dataset.mapConfig);
      if (!response.ok) throw new Error('Map configuration unavailable');
      config = await response.json();
      if (current !== generation) return;
      if (typeof config.tilejson !== 'string' || !config.tilejson.startsWith('https://')) throw new Error('Invalid map provider configuration');
      canvas.hidden = false;
      maplibregl.setWorkerCount(1);
      maplibregl.setWorkerUrl(new URL(`./maplibre-gl-worker.mjs?v=${maplibregl.getVersion()}`, import.meta.url).href);
      map = new maplibregl.Map({ container: canvas, style: mapStyle(config.tilejson), center: CENTER, zoom: 15.5, minZoom: 12, maxZoom: 18, maxBounds: BOUNDS,
        attributionControl: { compact: false }, dragRotate: false, pitchWithRotate: false, touchPitch: false, scrollZoom: false, fadeDuration: 0, renderWorldCopies: false,
        prefetchZoomDelta: 0, maxTileCacheSize: 32, transformRequest: url => ({ url, referrerPolicy: 'strict-origin-when-cross-origin' }) });
      map.touchZoomRotate.disableRotation();
      map.keyboard.disableRotation();
      map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: 'metric' }), 'bottom-left');
      map.getCanvas().setAttribute('aria-label', 'OpenStreetMap of Cardiff Bay with invented device markers. Use arrow keys to pan, plus and minus to zoom, or use the location records below.');
      map.getCanvas().setAttribute('aria-describedby', root.querySelector('[data-map-instructions]').id);
      root.mapExample = { map, records: MAP_RECORDS };
      let hadError = false;
      map.on('error', () => { hadError = true; clearTimeout(timer); inform('Some or all OpenStreetMap data could not load. The unchanged location records remain available below. You can close the map or try loading it again.', 'error'); load.disabled = false; });
      map.on('style.load', addAccuracy);
      map.once('load', () => {
        clearTimeout(timer);
        navigation.forEach(button => button.disabled = false);
        if (!hadError) inform('OpenStreetMap loaded. Device positions and observations are invented; map features come from OpenStreetMap contributors.', 'ready');
        select(selectedId);
        root.dispatchEvent(new CustomEvent('civica-map-ready', { detail: { map }, bubbles: true }));
      });
      for (const record of MAP_RECORDS.filter(record => record.coordinates)) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `civica-map-demo__marker civica-map-demo__marker--${record.id}`;
        button.dataset.mapSelect = record.id;
        button.textContent = record.id.toUpperCase();
        if (record.id === 'b') button.innerHTML = '<svg viewBox="0 0 40 40" aria-hidden="true" focusable="false"><path d="M20 1 39 20 20 39 1 20Z"/><text x="20" y="27">B</text></svg>';
        button.setAttribute('aria-label', `Select ${record.label}; ${record.place}`);
        button.setAttribute('aria-pressed', String(record.id === selectedId));
        button.addEventListener('click', () => select(record.id));
        markers.push(new maplibregl.Marker({ element: button }).setLngLat(record.coordinates).addTo(map));
      }
      stop.disabled = false;
      timer = setTimeout(() => { if (current !== generation) return; clearMap(); load.disabled = false; inform('OpenStreetMap did not finish loading. No location record was changed. Read the complete table or try loading the map again.', 'error'); }, 15000);
    } catch {
      if (current !== generation) return;
      clearMap();
      load.disabled = false;
      inform('OpenStreetMap could not be opened in this browser. No location record was changed. The complete text alternative remains below.', 'error');
    }
  }
  load.addEventListener('click', start);
  stop.addEventListener('click', () => { clearMap(); load.disabled = false; inform('Map closed. No further map tiles are requested; the location records are unchanged.', 'closed'); load.focus(); });
  root.querySelectorAll('[data-map-select]').forEach(button => button.addEventListener('click', () => select(button.dataset.mapSelect)));
  root.querySelectorAll('[data-map-command]').forEach(button => button.addEventListener('click', () => {
    if (!map) return;
    const action = button.dataset.mapCommand;
    if (action === 'reset') map.jumpTo({ center: CENTER, zoom: 15.5 });
    else map.jumpTo({ zoom: Math.min(18, Math.max(12, map.getZoom() + (action === 'in' ? 1 : -1))) });
  }));
  new ResizeObserver(() => map?.resize()).observe(canvas);
  window.addEventListener('pagehide', clearMap, { once: true });
  load.disabled = false;
}

if (typeof document !== 'undefined') document.querySelectorAll('[data-map-example]').forEach(initialiseMapExample);
