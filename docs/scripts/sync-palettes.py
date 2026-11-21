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
description: The Civica colour palette, the theme colours a household can choose, the rules for every colour choice, and which page covers each palette.
group: "Colour"
nav_order: 0
no_contents: true
last_reviewed_on: 2026-11-19
review_in: 3 months
updated_on: "2026-11-19"
updates:
  - date: "2026-11-19"
    description: "Shortened the page for easier reading: shorter sentences and no repeated text. All colours, examples and links are unchanged."
ai_instructions: "Start here for any colour question. Civica has one colour palette, with a page for each job (web, app, social, print, charts, maps, illustrations). The household chooses one theme colour (the colour of the header, buttons and highlights) from seven primary colours that pass 4.5:1 with white text. This page owns what the theme colour changes and keeps; Change theme colours owns how to choose it and the Home Assistant theme names. Chart, map, error, warning and success colours never change with the theme colour; links in dark mode, the on state, switches and sliders do. With the Red or Green theme colour, buttons share a colour with error or success messages; Web-app colours explains how to keep them apart. Never convey meaning by colour alone. Maintenance of colour records is on Maintain the system. The rules anchored bg-col-01, bg-col-03, bg-col-06 and bg-col-08 are on this page; do not show rule IDs or name outside sources in page text. Rules WG-001, WG-081."
ai_related:
  - path: "/styles/colour-web-app.html"
    title: "Web-app colours"
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

Civica has one colour palette. Each page below covers the part of it for one job, such as dashboards, charts or maps. Never use colour alone to give meaning.

## Palette overview

Each colour family has a primary colour, lighter tints and darker shades. The [Blues on Web-app colours](colour-web-app.html#blues) show a whole family.

## Choose the palette for the job

- [Web-app colours](colour-web-app.html): web pages, dashboards and the functional colours.
- [App colours](colour-web-app.html#app-colours): app-like graphics, including dark mode blues.
- [Social colours](colour-social.html): social media graphics.
- [Print colours](colour-print.html): printed material, with CMYK and Pantone references.
- [Chart colours](chart-colour.html): charts and heatmaps.
- [Map colours](colour-maps.html): maps, zones and locations.
- [Illustration colours](colour-illustrations.html): illustrations.

## Theme colour

Each household chooses one theme colour in their Home Assistant profile, with [the Civica colour controls](../get-started/colour-settings.html). It colours the header, buttons, selected navigation and highlights.

The 7 choices all pass 4.5:1 contrast with white text:

| Theme colour | Palette colour | Hex |
| --- | --- | --- |
@@ROWS@@

Primary orange, yellow and brown are not offered: white text on them falls below 4.5:1.

The theme colour also colours links in dark mode, entities that are on, switches and sliders. These stay the same:

- text, focus, error, warning and success colours
- links in light mode (`#1A65A6`)
- every chart, map and illustration colour

With the Red or Green theme colour, buttons share a colour with error or success messages. [Choose a colour by its job](colour-web-app.html#bg-col-02) explains how to keep them apart.

## Try a theme colour

Pick a colour to see it in a dashboard header. The temperature and status message keep their colours. The preview changes only this example, not your Home Assistant.

<div class="c-demo" data-palette-demo>
<div class="c-demo__header"><strong>Morgan household</strong></div>
<label for="palette-preview">Theme colour</label>
<select id="palette-preview">
@@OPTIONS@@
</select>
<p>Living room temperature: <strong>21°C</strong></p>
<p class="c-status">All monitored devices are available.</p>
@@STATUS@@
</div>

## Light and dark modes

The theme colour does not change the light or dark mode. In dark mode, surfaces are dark neutrals and interactive colours are lighter tints of the theme colour. The header keeps the exact theme colour.

## Colour rules

These rules apply to every colour choice. [Web-app colours](colour-web-app.html#colour-roles-in-home-assistant) covers interface colours and device states. [Chart colours](chart-colour.html#bg-col-07) covers chart and map scales.

<h3 id="bg-col-01">Keep the theme colour separate from names and logos</h3>

A theme colour changes only interface colours. It must not add a logo or replace a household name. Keep a family crest or business logo in its own colours. [Personalise your home](../get-started/personalisation.html) covers names and logos inside a home. [Project identity](brand.html) covers the Civica logo.

In this example only the header colour changes. The household name and failure message stay the same. The words, not the colour, say the sensor is unavailable.

<%= example('bg-colour-role-separation') %>

<h3 id="bg-col-03">Test combinations and keep another cue</h3>

Test the real text and background pair, not the swatches alone. Normal text needs 4.5:1 contrast and large text needs 3:1. Control boundaries and meaningful graphics, such as a chart line or map marker, need 3:1. A quiet divider is not a control boundary.

Always give a second cue, such as words for a status or a pattern for a chart series. Show “Front door locked” as text as well as a green icon. Test focus on its real surface, including a dark header. A colour-blindness simulator helps, but it is not proof. See the [accessibility requirements](../accessibility/index.html).

<h3 id="bg-col-06">Check every theme colour and mode</h3>

A component can appear in 14 combinations: 7 theme colours in 2 modes. Use the dark colours the theme provides. Do not lighten a colour by making it transparent.

Let forced-colour modes, such as Windows contrast themes, use system colours for text, links, focus and controls. Keep borders, labels and symbols so the meaning survives when fills disappear. Avoid a blanket `forced-color-adjust: none`. Check real dialogs and dense settings too.

<h3 id="bg-col-08">Use the palette for where the colour appears</h3>

Keep dashboard colour calm for daily use. Social media posts take their colours from [Social colours](colour-social.html). Never use social colours as a second theme in the interface.

The CMYK and Pantone values on [Print colours](colour-print.html) are references, so check a printed proof. Never change a screen colour to match a paint or print sample.

<h2 id="maintain-the-tokens">Maintain the colour records</h2>

[Maintain the colour records](../community/index.html#maintain-colour-records) explains where colour values live and how to regenerate themes after a change.
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
