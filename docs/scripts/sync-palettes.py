#!/usr/bin/env python3
"""Publish the canonical palette reference without maintaining a second specification."""
from pathlib import Path
import json
import sys
root = Path(__file__).resolve().parents[2]
source = root / 'design-system/palettes.json'
data = json.loads(source.read_text())
# The Colour index. Theme colours come from design-system/palettes.json, which
# takes each value from docs/data/govuk-brand-colours.json.
lines = ['---', 'title: Colour', 'description: The civica colour palette, the theme colours a household can choose, the rules for every colour choice, and which page covers each palette.', 'group: "Colour"', 'nav_order: 0', 'no_contents: true', 'last_reviewed_on: 2026-11-18', 'review_in: 3 months',
 'ai_instructions: "Start here for any colour question. civica has one colour palette, with a page for each job (web, app, social, print, charts, maps, illustrations). The household chooses one theme colour (the colour of the header, buttons and highlights) from seven primary colours that pass 4.5:1 with white text. Web, app and print colours each have an owner page; social, chart, map and illustration colours are owned by Social colours, Chart colours, Map colours and Illustration colours. Chart, map, error, warning and success colours never change with the theme colour; links in dark mode, the on state, switches and sliders do. Primary red and green match the error and success colours. Never convey meaning by colour alone. The rules anchored bg-col-01, bg-col-03, bg-col-06 and bg-col-08 are on this page; do not show rule IDs or name outside sources in page text. Rules WG-001, WG-081."',
 'ai_related:', '  - path: "/styles/colour-web.html"', '    title: "Web colours"', '    relationship: "Owns the web palette and the functional colours (text, links, focus, error, success, brand)."',
 '  - path: "/styles/chart-colour.html"', '    title: "Chart colours"', '    relationship: "Owns chart colours and the chart and map scale rule."',
 '  - path: "/get-started/colour-settings.html"', '    title: "Change theme colours"', '    relationship: "Owns how a household changes the theme colour in Home Assistant."',
 '---', '', '# Colour', '',
 'civica has one colour palette. Each page under [Choose the palette for the job](#choose-the-palette-for-the-job) gives the part of it for one job, such as dashboards, charts or maps. Never use colour alone to give meaning: add a label, an icon, a pattern or text. Test every pair of colours you combine, as [Test combinations and keep another cue](#bg-col-03) explains.', '',
 '## Palette overview', '', 'The palette has 4 tiers.', '',
 '### Primary', '', 'Blue is the core colour. The other primary colours show tone, emphasis or a difference between things.', '',
 '### Tints', '', 'Tints are lighter versions of a colour, made by adding white. Use them for backgrounds, highlights and space.', '',
 '### Shades', '', 'Shades are darker versions of a colour, made by adding black. Use them for depth, contrast, and for text or emphasis.', '',
 '### Accents', '', 'Use accents sparingly, to highlight something, add energy, or show an action or a status.', '',
 '## Choose the palette for the job', '',
 '- [Web colours](colour-web.html): web pages, Home Assistant dashboards and the functional colours for text, links, focus, errors and success.',
 '- [App colours](colour-app.html): the Home Assistant Companion app, including dark mode blues.',
 '- [Social colours](colour-social.html): social media graphics and promotional tiles, with the companion colour set.',
 '- [Print colours](colour-print.html): printed material, with CMYK and Pantone references.',
 '- [Chart colours](chart-colour.html): charts, with a stable colour and pattern for each series.',
 '- [Map colours](colour-maps.html): base maps, Home Assistant zones and locations.',
 '- [Illustration colours](colour-illustrations.html): choosing, pairing and contrasting colours in an illustration.', '',
 '## Theme colour', '',
 'Each household chooses one theme colour in their Home Assistant profile, with [the civica colour controls](../get-started/colour-settings.html). It colours the header, buttons, selected navigation and highlights.', '',
 'The 7 choices are the primary colours that pass 4.5:1 contrast with white text, so white text stays readable on every one:', '',
 '| Theme colour | Palette colour | Hex | Home Assistant theme |', '| --- | --- | --- | --- |']
for p in data['palettes']:
    lines.append(f"| {p['name']} | {p['govukName']} | `{p['primary']['hex']}` | `civica {p['name']}` |")
lines += ['', 'Primary orange, yellow and brown are not offered: white text on them falls below 4.5:1.', '',
 'The theme colour also sets the colour of links in dark mode, entities that are on, switches and sliders. Everything else stays the same whatever the household chooses: text, focus, error, warning and success colours, links in light mode (`#1A65A6`), and every chart, map and illustration colour.', '',
 'Primary red is also the error colour, and Primary green is the success colour. With the Red or Green theme colour, buttons and highlights share a colour with error or success messages. Always give a state in words or with an icon, so that the meaning does not depend on colour.', '',
 '## Try a theme colour', '', 'Pick a colour to see it on an invented household dashboard. Notice that the household name and the device states stay the same whatever you pick. This preview changes only the example, not your Home Assistant.', '',
 '<div class="c-demo" data-palette-demo>', '<div class="c-demo__header"><strong>Morgan household</strong></div>', '<label for="palette-preview">Theme colour</label>', '<select id="palette-preview">']
for p in data['palettes']:
    lines.append(f'<option data-palette-id="{p["id"]}" data-primary="{p["primary"]["hex"]}">{p["name"]}</option>')
default=[p for p in data['palettes'] if p['id']==data['defaultPalette']][0]
lines += ['</select>', '<p>Living room temperature: <strong>21 °C</strong></p>', '<p class="c-status">All monitored devices are available.</p>', f'<p role="status">{default["name"]} preview. This choice affects this example only.</p>', '</div>', '',
 '## Light and dark modes', '',
 'The theme colour does not change Home Assistant’s light, dark or automatic mode. In dark mode, surfaces are dark neutrals and interactive colours are lighter tints of the theme colour, tested against those surfaces. The header keeps the exact theme colour.', '',
 '## Maintain the tokens', '',
 'Colour values live in `docs/data/govuk-brand-colours.json`, and every colour page renders its swatches from it. The theme colours live in `design-system/palettes.json`, and the chart colours and energy roles in `design-system/chart-colours.json`. After changing a value, run `node scripts/generate-themes.mjs` and `python3 docs/scripts/sync-palettes.py` from the repository root, and commit the generated files together. Use `--check` on both to find drift.', '',
 'The social tiles, illustrations and web and app pictures are generated by `docs/scripts/generate-social-examples.py`, `docs/scripts/generate-illustration-examples.py` and `docs/scripts/generate-web-app-examples.py`. Run them again after a colour change rather than editing a picture by hand, and use `--check` to find pictures that are out of date. The working OpenStreetMap example takes its colours from `docs/javascript/map-examples.mjs`. Run `npm run check:colours` after the docs build.', '',
 'The default theme is `civica`, which uses Blue. Each theme colour has its own theme, named `civica {colour}`. The `govuk` theme is an alias for Blue, kept so that existing set-ups still work.', '',
 'Record each rule check in `docs/data/brand-guidance-checklist.json`, with the page or component, the theme and mode, the result and any remaining issue. Check again after a change to a palette, component or renderer.', '']
page_content = '\n'.join(lines)
rules_section = '## Colour rules\n\nThese rules apply to every colour choice. [Web colours](colour-web.html#colour-roles-in-home-assistant) covers the job of each interface colour, borders and device states, and [Chart colours](chart-colour.html#bg-col-07) covers chart and map scales.\n\n<h3 id="bg-col-01">Keep the theme colour separate from names and logos</h3>\n\nChoosing a theme colour changes only the interface colours. It must not add a logo or replace a household name. Keep a family crest or business logo in its own colours, and choose a background that suits it rather than recolouring it.\n\n[Project identity](brand.html) covers the civica logo and promotion. [Personalise your home](../get-started/personalisation.html) covers a family name, crest or business logo inside a home.\n\nThis example shows the same unavailable kitchen sensor with the Green and the Red theme colour. Notice that only the header colour changes. The household name and the failure message stay the same, and the words, not the colour, say that the sensor is unavailable.\n\n<%= example(\'bg-colour-role-separation\') %>\n\n<h3 id="bg-col-03">Test combinations and keep another cue</h3>\n\nTest the real text and background pair, not the swatches on their own. Normal text needs 4.5:1 contrast and large text needs 3:1. Control boundaries and meaningful graphics, such as a chart line or a map marker, need 3:1. A quiet divider does not count as a control boundary.\n\nAlways give a second cue: words for a status, a checked or current state for a selection, and a name with a pattern or shape for a chart series. For example, show “Front door locked” as text as well as a green icon. Test focus on the surface it really sits on, including a dark header. A colour-blindness simulator helps a review, but it does not prove that everyone can tell every pair apart. The [accessibility requirements](../accessibility/index.html) give the full criteria.\n\n<h3 id="bg-col-06">Check every theme colour and mode</h3>\n\nThe theme colour and light or dark mode are separate choices, so a component can appear in 14 combinations: 7 theme colours in 2 modes. Use the dark colours the theme provides, keep the exact theme colour on the header, and do not lighten a colour by making it transparent.\n\nLet forced-colour modes, such as Windows contrast themes, use system colours for text, links, focus and controls. Keep borders, labels and symbols so that the meaning survives when fills disappear, and avoid a blanket `forced-color-adjust: none`. Check real native dialogs, dense settings tables and editors, not only spacious examples.\n\n<h3 id="bg-col-08">Use the palette for where the colour appears</h3>\n\nDashboards need calm colour, because people use them every day. A release graphic or other social media post takes its colours from [Social colours](colour-social.html). Do not use social colours or accent animations as a second theme in the interface.\n\nFor print, the CMYK and Pantone values on [Print colours](colour-print.html) are references, not measured matches, so check a printed proof. Never change a screen colour to match a paint or print sample. Illustrations take their colours from [Illustration colours](colour-illustrations.html).\n\n'
maintain = page_content.index('\n## Maintain the tokens')
page_content = page_content[:maintain] + '\n' + rules_section + page_content[maintain + 1:]
outputs = {
    root/'docs/source/reference/chart-colours.json': (root/'design-system/chart-colours.json').read_text(),
    root/'docs/source/styles/colour.html.md.erb': page_content,
    root/'docs/source/reference/palettes.json': source.read_text(),
    root/'docs/source/reference/upstream-sources.json': (root/'design-system/upstream-sources.json').read_text()
}
check = '--check' in sys.argv
for path, content in outputs.items():
    if check:
        if not path.exists() or path.read_text()!=content:
            raise SystemExit(f'Stale generated documentation: {path.relative_to(root)}')
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content)
print('Palette documentation is current.' if check else 'Updated palette documentation and machine-readable references.')
