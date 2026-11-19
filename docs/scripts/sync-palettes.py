#!/usr/bin/env python3
"""Publish the canonical palette reference without maintaining a second specification."""
from pathlib import Path
import json
import sys
root = Path(__file__).resolve().parents[2]
source = root / 'design-system/palettes.json'
data = json.loads(source.read_text())
# The Colour index. Theme colours come from design-system/palettes.json, which
# takes each value from docs/data/govuk-brand-colours.json. The page text is
# kept here; only the theme colour table, the preview options and the default
# preview status are generated.
TEMPLATE = """---
title: Colour
description: The civica colour palette, the theme colours a household can choose, the rules for every colour choice, and which page covers each palette.
group: "Colour"
nav_order: 0
no_contents: true
last_reviewed_on: 2026-11-18
review_in: 3 months
ai_instructions: "Start here for any colour question. civica has one colour palette, with a page for each job (web, app, social, print, charts, maps, illustrations). The household chooses one theme colour (the colour of the header, buttons and highlights) from seven primary colours that pass 4.5:1 with white text. This page owns what the theme colour changes and keeps; Change theme colours owns how to choose it and the Home Assistant theme names. Chart, map, error, warning and success colours never change with the theme colour; links in dark mode, the on state, switches and sliders do. With the Red or Green theme colour, buttons share a colour with error or success messages; Web colours explains how to keep them apart. Never convey meaning by colour alone. Maintenance of colour records is on Maintain the system. The rules anchored bg-col-01, bg-col-03, bg-col-06 and bg-col-08 are on this page; do not show rule IDs or name outside sources in page text. Rules WG-001, WG-081."
ai_related:
  - path: "/styles/colour-web.html"
    title: "Web colours"
    relationship: "Owns the web palette and the functional colours (text, links, focus, error, success, brand)."
  - path: "/styles/chart-colour.html"
    title: "Chart colours"
    relationship: "Owns chart colours and the chart and map scale rule."
  - path: "/get-started/colour-settings.html"
    title: "Change theme colours"
    relationship: "Owns how a household changes the theme colour in Home Assistant, and the theme names."
  - path: "/community/index.html"
    title: "Maintain the system"
    relationship: "Owns where colour values live and how to regenerate themes and example pictures."
---

# Colour

civica has one colour palette. Each page under [Choose the palette for the job](#choose-the-palette-for-the-job) gives the part of it for one job, such as dashboards, charts or maps. Never use colour alone to give meaning: add a label, an icon, a pattern or text. Test every pair of colours you combine, as [Test combinations and keep another cue](#bg-col-03) explains.

## Palette overview

Each colour family has a primary colour, lighter tints for backgrounds and highlights, darker shades for text and contrast, and on some pages a bright accent for small highlights. The [Blues on Web colours](colour-web.html#blues) show a whole family.

## Choose the palette for the job

- [Web colours](colour-web.html): web pages, Home Assistant dashboards and the functional colours for text, links, focus, errors and success.
- [App colours](colour-web.html#app-colours): the Home Assistant Companion app, including dark mode blues.
- [Social colours](colour-social.html): social media graphics and promotional tiles, with the companion colour set.
- [Print colours](colour-print.html): printed material, with CMYK and Pantone references.
- [Chart colours](chart-colour.html): charts, with a stable colour and pattern for each series.
- [Map colours](colour-maps.html): base maps, Home Assistant zones and locations.
- [Illustration colours](colour-illustrations.html): choosing, pairing and contrasting colours in an illustration.

## Theme colour

Each household chooses one theme colour in their Home Assistant profile, with [the civica colour controls](../get-started/colour-settings.html). It colours the header, buttons, selected navigation and highlights.

The 7 choices are the primary colours that pass 4.5:1 contrast with white text, so white text stays readable on every one:

| Theme colour | Palette colour | Hex |
| --- | --- | --- |
@@ROWS@@

Primary orange, yellow and brown are not offered: white text on them falls below 4.5:1.

The theme colour also sets the colour of links in dark mode, entities that are on, switches and sliders. Everything else stays the same whatever the household chooses: text, focus, error, warning and success colours, links in light mode (`#1A65A6`), and every chart, map and illustration colour.

With the Red or Green theme colour, buttons and highlights share a colour with error or success messages. [Choose a colour by its job](colour-web.html#bg-col-02) explains how to keep their meaning clear.

## Try a theme colour

Pick a colour to see it in the header of a household dashboard. Notice that the temperature and the status message keep their colours whatever you pick. In Home Assistant the theme colour also colours buttons, switches and sliders, which this preview does not show. The preview changes only this example, not your Home Assistant.

<div class="c-demo" data-palette-demo>
<div class="c-demo__header"><strong>Morgan household</strong></div>
<label for="palette-preview">Theme colour</label>
<select id="palette-preview">
@@OPTIONS@@
</select>
<p>Living room temperature: <strong>21 °C</strong></p>
<p class="c-status">All monitored devices are available.</p>
@@STATUS@@
</div>

## Light and dark modes

The theme colour does not change Home Assistant’s light, dark or automatic mode. In dark mode, surfaces are dark neutrals and interactive colours are lighter tints of the theme colour, tested against those surfaces. The header keeps the exact theme colour.

## Colour rules

These rules apply to every colour choice. [Web colours](colour-web.html#colour-roles-in-home-assistant) covers the job of each interface colour, borders and device states, and [Chart colours](chart-colour.html#bg-col-07) covers chart and map scales.

<h3 id="bg-col-01">Keep the theme colour separate from names and logos</h3>

Choosing a theme colour changes only the interface colours. It must not add a logo or replace a household name. Keep a family crest or business logo in its own colours, and choose a background that suits it rather than recolouring it.

[Project identity](brand.html) covers the civica logo and promotion. [Personalise your home](../get-started/personalisation.html) covers a family name, crest or business logo inside a home.

Notice that only the header colour changes. The household name and the failure message stay the same, and the words, not the colour, say that the sensor is unavailable.

<%= example('bg-colour-role-separation') %>

<h3 id="bg-col-03">Test combinations and keep another cue</h3>

Test the real text and background pair, not the swatches on their own. Normal text needs 4.5:1 contrast and large text needs 3:1. Control boundaries and meaningful graphics, such as a chart line or a map marker, need 3:1. A quiet divider does not count as a control boundary.

Always give a second cue: words for a status, a checked or current state for a selection, and a name with a pattern or shape for a chart series. For example, show “Front door locked” as text as well as a green icon. Test focus on the surface it really sits on, including a dark header. A colour-blindness simulator helps a review, but it does not prove that everyone can tell every pair apart. The [accessibility requirements](../accessibility/index.html) give the full criteria.

<h3 id="bg-col-06">Check every theme colour and mode</h3>

The theme colour and light or dark mode are separate choices, so a component can appear in 14 combinations: 7 theme colours in 2 modes. Use the dark colours the theme provides, keep the exact theme colour on the header, and do not lighten a colour by making it transparent.

Let forced-colour modes, such as Windows contrast themes, use system colours for text, links, focus and controls. Keep borders, labels and symbols so that the meaning survives when fills disappear, and avoid a blanket `forced-color-adjust: none`. Check real native dialogs, dense settings tables and editors, not only spacious examples.

<h3 id="bg-col-08">Use the palette for where the colour appears</h3>

Dashboards need calm colour, because people use them every day. A release graphic or other social media post takes its colours from [Social colours](colour-social.html). Do not use social colours or accent animations as a second theme in the interface.

For print, the CMYK and Pantone values on [Print colours](colour-print.html) are references, not measured matches, so check a printed proof. Never change a screen colour to match a paint or print sample. Illustrations take their colours from [Illustration colours](colour-illustrations.html).

<h2 id="maintain-the-tokens">Maintain the colour records</h2>

For maintainers: [Maintain the colour records](../community/index.html#maintain-colour-records) explains where the colour values live and how to regenerate the themes and example pictures after a change.
"""
rows = '\n'.join(f"| {p['name']} | {p['govukName']} | `{p['primary']['hex']}` |" for p in data['palettes'])
options = '\n'.join(f'<option data-palette-id="{p["id"]}" data-primary="{p["primary"]["hex"]}">{p["name"]}</option>' for p in data['palettes'])
default = [p for p in data['palettes'] if p['id'] == data['defaultPalette']][0]
status = f'<p role="status">{default["name"]} preview. This choice affects this example only.</p>'
page_content = TEMPLATE.replace('@@ROWS@@', rows).replace('@@OPTIONS@@', options).replace('@@STATUS@@', status)
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
