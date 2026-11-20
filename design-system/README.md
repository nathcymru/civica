# Civica design tokens

`palettes.json` is the canonical, human- and machine-readable list of theme colours. It holds seven colours from the GOV.UK colour palette: Primary blue, green, teal, purple, magenta and red, and Black. Each value is copied from `docs/data/govuk-brand-colours.json`, the record of the GOV.UK Brand Guidelines colour pages. These are the GOV.UK primary colours that pass 4.5:1 contrast with white text. Primary orange, yellow and brown are not offered because white text on them falls below 4.5:1.

The ten palettes supplied on 11 November 2026, with their Vivid and Muted tones, were replaced by these theme colours on 18 November 2026. Their supplied artwork is kept unchanged in `brand/civica/themes/` as a record.

`themes.json` is generated, resolved Home Assistant theme data for previews and automated checks. Each entry contains common variables and separate `modes.light` and `modes.dark` objects. Merge a mode over its common variables when using it in a browser preview; do not apply the `modes` object as CSS.

Run `npm run generate:themes` after editing theme colour data or `scripts/generate-themes.mjs`. The generator writes the default `civica` entry and one entry per theme colour to `themes/civica.yaml`, and a compatibility-only `govuk` entry to `themes/govuk.yaml`. Use `node scripts/generate-themes.mjs --check` to detect stale generated files and `node --test test/themes.test.mjs` to check the colour contracts.

## Selection contract

- Theme colour IDs are stable, lower-case strings, for example `teal`.
- There are no tones. The theme colour is independent of Home Assistant's `light`, `dark` and automatic mode preference.
- Native theme names use the form `civica {colour name}`, for example `Civica Teal`. `civica` is the same as `Civica Blue`.
- `govuk` is a migration alias for Blue. It does not use official branding.
- Light mode uses the exact theme colour on a white canvas. Links use GOV.UK link blue `#1A65A6` with every theme colour. Dark mode derives lighter interaction colours and uses neutral dark surfaces. It keeps the exact theme colour as `civica-brand-primary`, the app header and sidebar masthead colour.

## Roles and controlled adaptations

Brand colour changes must not change the meaning of errors, warnings, success, unavailable devices or chart series. The error and success base colours are `#CA3535` and `#0F7A52`, following the current GOV.UK Frontend 6.6 values. Secondary light text is `#484949`. Warning text uses dark ochre `#8A6100` so it remains readable on light surfaces; warning bands use yellow `#FFDD00` with ink text. This is a Civica adaptation, not an official new GOV.UK token.

The `civica-danger-fill`, `civica-success-fill`, `civica-warning-fill` and `civica-notice-fill` tokens have explicit `civica-on-*` foregrounds. Use those pairs for persistent banners and destructive buttons. Do not assume white text is readable on `error-color` in dark mode: that variable is an accessible lighter text/icon colour.

For custom controls, combine `ha-color-focus` yellow with `civica-focus-text` ink. Many native HA controls expose only one outline colour; `wa-focus-ring-color` is therefore ink on light surfaces and yellow on dark surfaces. The companion scopes yellow focus to the dark brand masthead. Yellow alone on a white canvas is not an adequate focus indicator.

Square card, field, button and dialog corners follow the service design language. Native circle and pill tokens are retained for radio buttons, switches, avatars and gauges. Dialog widths and heights are not forced globally: users must still be able to read and scroll long dialogs at zoomed and mobile sizes.

Charts use the six GOV.UK categorical chart colours, the same in light and dark mode and with every theme colour. Colour alone does not tell series apart: each series also gets a stable pattern, line dash and marker, and direct labels, units and alternative tables remain necessary. A theme cannot add these to native charts. The theme's 24 numbered chart slots repeat the six colours. For charts with many series, follow the [chart rules](https://nathcymru.github.io/civica/components/charts.html); never drop native series.

## Compatibility evidence

The generator covers modern HA semantic tokens, legacy/MDC tokens, switches, forms, buttons, native panel/table backgrounds, cards, the app header and sidebar. The upstream implementation was read at Home Assistant frontend commit [`e32bc0696ebefde323f5b791269ad0c57f3f99d9`](https://github.com/home-assistant/frontend/tree/e32bc0696ebefde323f5b791269ad0c57f3f99d9), dated 6 November 2026. The exact sources are listed in `upstream-sources.json`.

Home Assistant's [frontend documentation](https://www.home-assistant.io/integrations/frontend/) distinguishes supported variables from compatibility variables that can change between releases. A successful token test is not a live browser acceptance test. Check native screens and third-party cards against the documented acceptance matrix after each HA frontend update.
