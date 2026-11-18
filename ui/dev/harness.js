// The standalone fixture supplies the same readiness boundary as real HA.
if (!customElements.get('home-assistant')) customElements.define('home-assistant', class extends HTMLElement {});
await import('../dist/civica-ui.js');
const palettes = await fetch('../../design-system/palettes.json').then(r => r.json());
const source = await fetch('../../design-system/themes.json').then(r => r.json());
// Filled from the same generated values as the installed theme, not a hand-
// maintained visual approximation. Normalise the machine contract here only.
const themes = source.themes || source;
const app = document.querySelector('home-assistant');
app.attachShadow({mode:'open'});
app.hass = { themes: { themes, theme: 'civica Blue', darkMode: false }, selectedTheme: { theme: 'civica Blue', dark: false } };
window.events = [];
function paint() {
  const theme = themes[app.hass.selectedTheme.theme];
  const vars = { ...theme, ...theme.modes?.[app.hass.selectedTheme.dark ? 'dark' : 'light'] };
  for (const [key, value] of Object.entries(vars)) if (typeof value === 'string' || typeof value === 'number') document.documentElement.style.setProperty(`--${key}`, String(value));
  app.hass.themes.theme = app.hass.selectedTheme.theme;
  app.hass.themes.darkMode = app.hass.selectedTheme.dark;
  // Every GOV.UK theme colour uses the same white lock-up on its masthead.
  if (palettes.palettes.some(palette => app.hass.themes.theme === `civica ${palette.name}`)) document.querySelector('header img').src = '../../brand/civica/core/lockup-white.svg';
  document.querySelector('civica-theme-settings').hass = app.hass;
}
document.addEventListener('settheme', e => { window.events.push(e.detail); app.hass.selectedTheme = { ...app.hass.selectedTheme, ...e.detail }; paint(); });
document.getElementById('mode').onclick = e => { app.hass.selectedTheme.dark = !app.hass.selectedTheme.dark; e.target.textContent = app.hass.selectedTheme.dark ? 'Use light mode' : 'Use dark mode'; paint(); };
paint();
// Expose the fixture before the slower card import, so tests never see the
// enabled control without it.
window.fixture = { app, themes, paint };
await import('../../card/dist/civica-house-lighting-card.js');
const card = document.createElement('govuk-house-lighting-card');
card.setConfig({type:'custom:govuk-house-lighting-card', image:'../../card/assets/floorplan.png'});
card.hass = {states:{},entities:{},devices:{},callService:async()=>{}};
document.getElementById('lighting').append(card);
