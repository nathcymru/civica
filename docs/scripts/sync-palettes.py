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
 'ai_instructions: "Start here for any colour question. civica uses the GOV.UK colour palette unchanged. The household chooses one theme colour (the brand colour of the header, buttons and highlights) from seven GOV.UK primary colours that pass 4.5:1 with white text. Web, app and print colours each have an owner page; social, chart, map and illustration colours are owned by Social colours, Chart colours, Map colours and Illustration colours. Chart, map, error, warning and success colours never change with the theme colour; links in dark mode, the on state, switches and sliders do. Primary red and green match the error and success colours. Never convey meaning by colour alone. Rules BG-COL-01, BG-COL-03, BG-COL-06 and BG-COL-08 are on this page."',
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
 '- [Social colours](colour-social.html): social media graphics and promotional tiles, with the companion colour set.',
 '- [Print colours](colour-print.html): printed material, with CMYK and Pantone references.',
 '- [Chart colours](chart-colour.html): charts, with a stable colour and pattern for each series.',
 '- [Map colours](colour-maps.html): base maps, Home Assistant zones and locations.',
 '- [Illustration colours](colour-illustrations.html): choosing, pairing and contrasting colours in an illustration.', '',
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
rules_section = '## Colour rules\n\nThese rules apply to every colour choice. Rule IDs BG-COL-01, BG-COL-03, BG-COL-06 and BG-COL-08 moved here from the retired Colour roles and accessibility page, unchanged in meaning. Web colours owns BG-COL-02, BG-COL-04 and BG-COL-05, and Chart colours owns BG-COL-07.\n\n<h2 id="bg-col-01">BG-COL-01: Keep the theme colour and identity roles separate</h2>\n\n**Local requirement: MUST.** Applies to theme selection, household personalisation and separate project identity assets.\n\nUse only the seven [GOV.UK theme colours](#theme-colour). Choosing a theme colour must not add a project logo or replace a household name. Keep a family crest or business logo in its own colours and choose a suitable background rather than recolouring it. For example, switching to Green leaves the “Morgan household” title as it is.\n\ncivica uses the GOV.UK colour palette. That does not make civica an official government service, and GOV.UK’s identity rules do not apply to civica. The [project identity rules](brand.html) cover civica documentation and promotion. Follow [Personalise your home](../get-started/personalisation.html) for a family name, crest or business logo inside a home.\n\n<%= example(\'bg-colour-role-separation\') %>\n\n<h2 id="bg-col-03">BG-COL-03: Test combinations and retain another cue</h2>\n\n**Local requirement: MUST.** Applies to rendered text, controls and meaningful graphical objects.\n\nTest the real foreground and background pair against the [accessibility requirements](../accessibility/index.html). Normal text needs 4.5:1 contrast and large text needs 3:1. Meaningful control boundaries and graphical objects need 3:1 where the WCAG criterion applies. A quiet divider does not replace a visible control boundary.\n\nGive a status words, a selection a checked or current state, and a chart series a name plus a pattern or shape. For example, show “Front door locked” in text as well as a green icon. Test focus on its real surface, including a dark masthead. A colour-blindness simulation helps a review but does not prove that everyone can tell every pair apart.\n\n<h2 id="bg-col-06">BG-COL-06: Review every display context</h2>\n\n**Local requirement: MUST.** Applies to affected components with every theme colour, in both modes and in accessibility contexts.\n\nThe theme colour, and Light or Dark, are independent choices. Use the documented derived dark tokens and keep the exact theme colour on the brand header. Do not make a colour lighter by adding transparency.\n\nLet forced-colour modes use system colours for text, links, focus and controls. Keep borders, labels and symbols if fills disappear, and avoid a blanket `forced-color-adjust: none`. Check real native dialogs, dense settings tables and editors, not only the spacious examples. A documentation preview is not an audit of all fourteen combinations (7 theme colours, 2 modes).\n\n<h2 id="bg-col-08">BG-COL-08: Adapt the output channel without importing identity</h2>\n\n**Local requirement: MUST.** Applies to screen, promotional and print colour output.\n\nDashboard controls need calm colour for repeated use. A release graphic or other social post takes its colours from [Social colours](colour-social.html), and must keep accessible text. Do not use social colours, accent-dot animations or official headers as a second theme in the interface.\n\nFor print, treat the supplied CMYK and RAL or descriptive values as references, not measured matches. Use screen hex in sRGB for the application and check a separate proof for printed material. Never change a screen token to approximate a paint or print sample. Illustration colour follows [Illustration colours](colour-illustrations.html).\n\n'
maintain = page_content.index('\n## Maintain the tokens')
page_content = page_content[:maintain] + '\n' + rules_section + page_content[maintain + 1:]
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
