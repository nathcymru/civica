#!/usr/bin/env python3
"""Publish the canonical palette reference without maintaining a second specification."""
from pathlib import Path
import json
import sys
root = Path(__file__).resolve().parents[2]
source = root / 'design-system/palettes.json'
data = json.loads(source.read_text())
# The Colour index. Theme colours come from design-system/palettes.json, which
# takes each value from docs/data/govuk-brand-colours.json (GOV.UK Brand Guidelines).
lines = ['---', 'title: Colour', 'description: How civica uses the GOV.UK colour palette, which colours a household can choose for the theme, and where each palette is documented.', 'group: "Colour"', 'nav_order: 0', 'last_reviewed_on: 2026-11-18', 'review_in: 3 months',
 'ai_instructions: "Start here for any colour question. civica uses the GOV.UK colour palette unchanged. The household chooses one theme colour (the brand colour of the header, buttons and highlights) from seven GOV.UK primary colours that pass 4.5:1 with white text. Web, app and print colours each have an owner page, and chart colours are owned by Chart colours; social, maps and illustrations pages are planned. Chart, map, error, warning and success colours never change with the theme colour; links in dark mode, the on state, switches and sliders do. Primary red and green match the error and success colours. Never convey meaning by colour alone."',
 'ai_related:', '  - path: "/styles/colour-web.html"', '    title: "Web colours"', '    relationship: "Owns the web palette and the functional colours (text, links, focus, error, success, brand)."',
 '  - path: "/get-started/colour-settings.html"', '    title: "Change theme colours"', '    relationship: "Owns how a household changes the theme colour in Home Assistant."',
 '---', '', '# Colour', '',
 'civica uses the GOV.UK colour palette, unchanged. It was designed with accessibility in mind, but you are still responsible for meeting WCAG when you combine colours. Never use colour alone to give meaning: add a label, an icon, a pattern or text.', '',
 '## Palette overview', '', 'The palette has 4 tiers.', '',
 '### Primary', '', 'Blue is the core colour. The other primary colours show tone, emphasis or a difference between things.', '',
 '### Tints', '', 'Tints are lighter versions of a colour, made by adding white. Use them for backgrounds, highlights and space.', '',
 '### Shades', '', 'Shades are darker versions of a colour, made by adding black. Use them for depth, contrast, and for text or emphasis.', '',
 '### Accents', '', 'Use accents sparingly, to highlight something, add energy, or show an action or a status.', '',
 '## Choose the palette for the job', '',
 '- [Web colours](colour-web.html): web pages, Home Assistant dashboards and the functional colours for text, links, focus, errors and success.',
 '- [App colours](colour-app.html): the Home Assistant Companion app, including dark mode blues.',
 '- [Print colours](colour-print.html): printed material, with CMYK and Pantone references.', '',
 '## Theme colour', '',
 'Each household chooses one theme colour. It colours the header, buttons, selected navigation and highlights. Choose it in your profile with [the civica colour controls](../get-started/colour-settings.html).', '',
 'The choices are the GOV.UK primary colours that pass 4.5:1 contrast with white text, so white text and the white lockup stay readable on every one:', '',
 '| Theme colour | GOV.UK colour | Hex | Home Assistant theme |', '| --- | --- | --- | --- |']
for p in data['palettes']:
    lines.append(f"| {p['name']} | {p['govukName']} | `{p['primary']['hex']}` | `civica {p['name']}` |")
lines += ['', 'Primary orange, yellow and brown are not offered: white text on them falls below 4.5:1.', '',
 'The theme colour also sets the colour of links in dark mode, entities that are on, switches and sliders. Text, focus, error, warning and success colours, links in light mode (GOV.UK link blue `#1A65A6`), and every chart, map and illustration colour stay the same whatever the household chooses.', '',
 'Primary red is also the error colour, and Primary green is the success colour. With the Red or Green theme colour, buttons and highlights share a colour with error or success messages. Always give a state in words or with an icon, so that the meaning does not depend on colour.', '',
 '## Try a theme colour', '', 'This demonstration changes only the example. To change Home Assistant, use [the profile colour controls](../get-started/colour-settings.html).', '',
 '<div class="c-demo" data-palette-demo>', '<div class="c-demo__header"><strong>Morgan household</strong></div>', '<label for="palette-preview">Theme colour</label>', '<select id="palette-preview">']
for p in data['palettes']:
    lines.append(f'<option data-palette-id="{p["id"]}" data-primary="{p["primary"]["hex"]}">{p["name"]}</option>')
default=[p for p in data['palettes'] if p['id']==data['defaultPalette']][0]
lines += ['</select>', '<p>This preview uses an invented household name. A logo is optional.</p>', '<p>Living room temperature: <strong>21 °C</strong></p>', '<p class="c-status">All monitored devices are available.</p>', f'<p role="status">{default["name"]} preview. This choice affects this example only.</p>', '</div>', '',
 'The preview changes the theme colour without changing the household name or the meaning of any state. Follow [personalisation](../get-started/personalisation.html) for optional names, crests and logos.', '',
 '## Light and dark modes', '',
 'The theme colour does not change Home Assistant’s light, dark or automatic mode. In dark mode, surfaces are dark neutrals and interactive colours are lighter tints of the theme colour, tested against those surfaces. The header keeps the exact theme colour.', '',
 '## Maintain the tokens', '',
 'GOV.UK values live in `docs/data/govuk-brand-colours.json`. The theme colours live in `design-system/palettes.json`. After changing either, run `node scripts/generate-themes.mjs` and `python3 docs/scripts/sync-palettes.py` from the repository root, and commit the generated files together. Use `--check` on both to detect drift.', '',
 'The default theme is `civica`, which uses Blue. The `govuk` entry is a compatibility alias for Blue. Each theme colour has its own theme, named `civica {colour}`.', '']
page_content = '\n'.join(lines)
example_section = """## Examples

These isolated examples show the theme colour in use. Household values are invented, and the examples do not control a home.

<%= example('local-theme-blue') %>

<%= example('local-theme-purple') %>

"""
position = page_content.index('\n## Choose the palette for the job')
page_content = page_content[:position] + '\n\n' + example_section + page_content[position + 1:]
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
