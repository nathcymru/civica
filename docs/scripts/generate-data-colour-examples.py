#!/usr/bin/env python3
"""Generate the data-colour-categorical and data-colour-quantitative examples in
docs/data/data-colour-examples.yml: a line chart and two heatmaps of synthetic
Home Assistant data in the Civica chart colours.
Run from the repository root: python3 docs/scripts/generate-data-colour-examples.py
Pass --check to fail if the YAML differs from what this script writes.
The other examples in the file are not touched.

Colours: the line chart takes civica-chart-1 to civica-chart-4 from
themes/civica.yaml, in order, as a History graph card does. The heatmaps use
the listed steps of the chart scale families on the Chart colours page. Every
hex value is read from docs/data/govuk-brand-colours.json by its ID; nothing
is calculated or blended."""
import json
import re
import sys
from html import escape

import yaml

TARGET = 'docs/data/data-colour-examples.yml'
RECORD = json.load(open('docs/data/govuk-brand-colours.json', encoding='utf-8'))
C = RECORD['colours']
CHARTS = RECORD['pages']['charts']
hexof = lambda i: C[i]['hex']
name = lambda i: C[i]['name']
FONT = 'Roboto,Helvetica Neue,Helvetica,Arial,sans-serif'
MINUS = '−'
CHART_IDS = [item['colour'] for item in CHARTS['categorical'] if 'role' not in item]
SCALE_IDS = {scale['title']: scale['colours'] for scale in CHARTS['sequential']}
GRID = 'black-tint-80'
SURFACES = {
    # Card backgrounds of the Civica theme: White, and the dark-mode card colour.
    'light': {'surface': '#FFFFFF', 'label': 'black', 'title': 'Light mode'},
    'dark': {'surface': '#24282B', 'label': 'white', 'title': 'Dark mode'},
}


def theme_chart_colours(count):
    """civica-chart-1 to civica-chart-N from the first (light) block of themes/civica.yaml."""
    found = {}
    for line in open('themes/civica.yaml', encoding='utf-8'):
        match = re.match(r'\s*"civica-chart-(\d+)": "(#[0-9A-F]{6})"', line)
        if match and int(match.group(1)) not in found:
            found[int(match.group(1))] = match.group(2)
        if len(found) >= count and all(n in found for n in range(1, count + 1)):
            break
    ids = []
    for n in range(1, count + 1):
        colour = next(i for i in CHART_IDS if hexof(i) == found[n])
        ids.append(colour)
    return ids


def luminance(hex_value):
    channels = [int(hex_value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(one, two):
    a, b = sorted([luminance(one), luminance(two)], reverse=True)
    return (a + 0.05) / (b + 0.05)


def ink_for(fill):
    """Black or White text, whichever passes 4.5:1 on the fill (asserted)."""
    for ink in ('black', 'white'):
        if contrast(hexof(ink), fill) >= 4.5:
            return ink
    raise SystemExit(f'No text colour reaches 4.5:1 on {fill}')


def text(x, y, value, fill, size=12, anchor='start', weight=None):
    bold = f' font-weight="{weight}"' if weight else ''
    return f'<text x="{fmt(x)}" y="{fmt(y)}" text-anchor="{anchor}" font-size="{size}"{bold} fill="{fill}">{escape(value)}</text>'


def fmt(number):
    return f'{number:.2f}'.rstrip('0').rstrip('.')


def table(label, caption, head, rows):
    out = [f'<div class="civica-table-scroll" role="region" tabindex="0" aria-label="{escape(label)}"><table class="govuk-table">',
           f'<caption class="govuk-table__caption govuk-table__caption--m">{escape(caption)}</caption>',
           '<thead class="govuk-table__head"><tr class="govuk-table__row">']
    out += [f'<th scope="col" class="govuk-table__header">{escape(cell)}</th>' for cell in head]
    out.append('</tr></thead><tbody class="govuk-table__body">')
    for row in rows:
        out.append('<tr class="govuk-table__row">' + f'<th scope="row" class="govuk-table__header">{escape(row[0])}</th>'
                   + ''.join(f'<td class="govuk-table__cell">{escape(cell)}</td>' for cell in row[1:]) + '</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)


def colours_used(items):
    out = ['<h3 class="govuk-heading-s">Colours used</h3><ul class="govuk-list" data-chart-colours>']
    for colour, token, role in items:
        prefix = f'<code>{token}</code>, ' if token else ''
        out.append(f'<li data-chart-colour="{colour}" data-hex="{hexof(colour)}"><span aria-hidden="true" style="display:inline-block;width:24px;height:24px;margin-right:8px;vertical-align:middle;border:1px solid #0B0C0C;background:{hexof(colour)};"></span>'
                   f'{prefix}{escape(name(colour))} <code>{hexof(colour)}</code>: {escape(role)}</li>')
    out.append('</ul>')
    return ''.join(out)


# ---------------------------------------------------------------------------
# 1. Categorical: relative humidity in 4 rooms, as a native History graph card
#    draws it with the Civica theme: solid lines, colour by entity position,
#    a legend of coloured circles and names under the plot, a gap where an
#    entity has no reading. No dashes, markers or end labels.
# ---------------------------------------------------------------------------
TIMES = ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00']
ROOMS = [
    # entity ID, name, values (None: no reading)
    ('sensor.kitchen_humidity', 'Kitchen', [52, 51, 50, 58, 55, 53, 66, 59]),
    ('sensor.living_room_humidity', 'Living room', [47, 46, None, None, 44, 45, 48, 46]),
    ('sensor.bedroom_humidity', 'Bedroom', [56, 59, 61, 54, 50, 49, 50, 53]),
    ('sensor.bathroom_humidity', 'Bathroom', [63, 61, 60, 82, 68, 64, 62, 74]),
]
chart_ids = theme_chart_colours(len(ROOMS))
# The viewBox is 228 wide so that 12-unit text renders at 12px or more when the
# picture is 228px wide or wider (the embedded example at a 320px viewport is
# about 238px wide). max-width keeps it near the size of a dashboard card.
WIDTH, HEIGHT, FONT_SIZE = 228, 236, 12
X0, X1, YTOP, YBOT, VMIN, VMAX = 26, 214, 24, 164, 30, 90
xat = lambda index: X0 + index * (X1 - X0) / (len(TIMES) - 1)
yat = lambda value: YBOT - (value - VMIN) * (YBOT - YTOP) / (VMAX - VMIN)


def no_data_label(values, ink):
    """'No data' centred under the gap, in the empty band between two grid lines
    below every reading, so it never sits on a grid line or a series line."""
    gaps = [i for i, value in enumerate(values) if value is None]
    if not gaps:
        return ''
    lowest = min(value for _, _, series in ROOMS for value in series if value is not None)
    band = max(v for v in range(VMIN, VMAX, 10) if v + 10 <= lowest)
    if any(value is not None and value < band + 10 for _, _, series in ROOMS for value in series):
        raise SystemExit('No empty grid band for the No data label')
    middle = (xat(gaps[0] - 1) + xat(gaps[-1] + 1)) / 2
    baseline = (yat(band) + yat(band + 10)) / 2 + FONT_SIZE / 3
    return text(middle, baseline, 'No data', ink, size=FONT_SIZE, anchor='middle')


def line_chart(mode):
    look = SURFACES[mode]
    ink = hexof(look['label'])
    grid = hexof(GRID)
    tid = f'categorical-{mode}'
    parts = [f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="{look["surface"]}"/>']
    parts.append(text(4, 12, '%', ink, size=FONT_SIZE))
    for value in range(VMIN, VMAX + 1, 10):
        parts.append(f'<line x1="{X0}" y1="{fmt(yat(value))}" x2="{X1}" y2="{fmt(yat(value))}" stroke="{grid}" stroke-width="1"/>')
        parts.append(text(X0 - 4, yat(value) + 4, str(value), ink, size=FONT_SIZE, anchor='end'))
    for index, time in enumerate(TIMES):
        if index % 2 == 0:
            parts.append(text(xat(index), YBOT + 18, time, ink, size=FONT_SIZE, anchor='middle'))
    for index, (key, label, values) in enumerate(ROOMS):
        colour = hexof(chart_ids[index])
        d, pen = [], 'M'
        for i, value in enumerate(values):
            if value is None:
                pen = 'M'
                continue
            d.append(f'{pen}{fmt(xat(i))} {fmt(yat(value))}')
            pen = 'L'
        data_values = ','.join('' if value is None else str(value) for value in values)
        parts.append(f'<path data-series="{key}" data-values="{data_values}" d="{" ".join(d)}" fill="none" stroke="{colour}" stroke-width="2" stroke-linejoin="round"/>')
        parts.append(no_data_label(values, ink))
    # Legend under the plot, as the card draws it: a circle in the series
    # colour and the entity name, two to a row so it fits at 320px.
    for index, (key, label, _) in enumerate(ROOMS):
        lx, ly = (6 if index % 2 == 0 else 118), YBOT + 42 + (index // 2) * 22
        parts.append(f'<circle data-legend="{key}" cx="{lx + 6}" cy="{ly - 4}" r="6" fill="{hexof(chart_ids[index])}"/>')
        parts.append(text(lx + 18, ly, label, ink, size=FONT_SIZE))
    last = {label: values[-1] for _, label, values in ROOMS}
    desc = ('Four solid lines, one for each room, named in the legend under the chart. '
            'Bathroom humidity jumps to 82% at 09:00 and 74% at 21:00, and the kitchen peaks at 66% at 18:00. '
            'The living room line has a gap at 06:00 and 09:00, where the sensor sent no reading. '
            f'At 21:00 the bathroom reads {last["Bathroom"]}%, the kitchen {last["Kitchen"]}%, the bedroom {last["Bedroom"]}% and the living room {last["Living room"]}%. '
            'The table below gives every reading.')
    svg = (f'<svg role="img" aria-labelledby="{tid}-title {tid}-desc" viewBox="0 0 {WIDTH} {HEIGHT}" '
           f'style="display:block;width:100%;max-width:360px;height:auto;font-family:{FONT};" data-chart="{tid}" data-chart-mode="{mode}">'
           f'<title id="{tid}-title">History graph of relative humidity in four rooms over one day, {look["title"].lower()}</title>'
           f'<desc id="{tid}-desc">{escape(desc)}</desc><g aria-hidden="true">{"".join(parts)}</g></svg>')
    return (f'<figure style="margin:0 0 30px;"><figcaption class="govuk-heading-s">{look["title"]}: relative humidity, 12 November 2026 (%)</figcaption>'
            f'{svg}</figure>')


def categorical():
    reading = lambda value: 'Not supplied' if value is None else str(value)
    rows = [[time] + [reading(values[i]) for _, _, values in ROOMS] for i, time in enumerate(TIMES)]
    used = [(chart_ids[i], f'civica-chart-{i + 1}', label) for i, (_, label, _) in enumerate(ROOMS)]
    used += [(GRID, None, 'grid lines'), ('black', None, 'labels in light mode'), ('white', None, 'labels in dark mode')]
    HARD_IN_DARK = 'blue-shade-50'
    low = {mode: [f'{name(colour)} ({contrast(hexof(colour), look["surface"]):.1f}:1)' for colour in chart_ids if contrast(hexof(colour), look['surface']) < 3]
           for mode, look in SURFACES.items()}
    if low['light']:
        raise SystemExit(f'Hard to see in light mode: {low["light"]}')
    # The Chart colours page names Blue shade 50% (1.2:1 on the dark card) and
    # Primary blue (2.9:1); chart_data records both. Keep this guard so the page stays true.
    if HARD_IN_DARK not in chart_ids or contrast(hexof(HARD_IN_DARK), SURFACES['dark']['surface']) >= 1.5:
        raise SystemExit('Blue shade 50% is no longer the hard-to-see series in dark mode; rewrite the Chart colours page')
    html = ''.join([
        '<section aria-labelledby="categorical-heading">',
        '<h2 class="govuk-heading-m" id="categorical-heading">A History graph card with the Civica theme</h2>',
        '<p class="govuk-body"><strong>Synthetic data.</strong> '
        'Relative humidity from 4 room sensors every 3 hours on 12 November 2026, Europe/London, '
        'drawn in light and dark mode.</p>',
        line_chart('light'),
        line_chart('dark'),
        table('Relative humidity readings', 'Relative humidity every 3 hours, 12 November 2026 (%)', ['Time'] + [room[1] for room in ROOMS], rows),
        '<p class="govuk-body">Entity IDs: ' + ', '.join(f'<code>{key}</code>' for key, *_ in ROOMS) + '.</p>',
        colours_used(used),
        '</section>',
    ])
    record = {
        'classification': 'Synthetic documentation data; not readings from a Home Assistant instance',
        'card': 'History graph card as drawn with the Civica theme: solid lines, legend under the plot, no dashes, markers or end labels',
        'measure': 'Relative humidity',
        'unit': '%',
        'time_zone': 'Europe/London',
        'date': '2026-11-12',
        'times': Flow(TIMES),
        'colour_order': 'civica-chart-1 to civica-chart-4 from themes/civica.yaml, by entity position',
        'series': [{'key': key, 'label': label, 'theme_colour': f'civica-chart-{i + 1}', 'colour_id': chart_ids[i], 'hex': hexof(chart_ids[i]),
                    'values': Flow(values)}
                   for i, (key, label, values) in enumerate(ROOMS)],
        'surfaces': {mode: look['surface'] for mode, look in SURFACES.items()},
        'contrast_on_dark_card': {f'civica-chart-{i + 1}': round(contrast(hexof(colour), SURFACES['dark']['surface']), 1) for i, colour in enumerate(chart_ids)},
        'missing': 'No reading: a gap in the line, “No data” under the gap and “Not supplied” in the table.',
    }
    return {
        'title': 'Four humidity sensors in a History graph card, in light and dark mode',
        'description': 'A History graph card of synthetic relative humidity in four rooms over one day, coloured civica-chart-1 to civica-chart-4 by entity position, with a legend, a gap for missing readings and a matching table.',
        'height': 1500,
        'html': html,
        'chart_data': record,
        'colour_reference': {
            'reviewed_on': '2026-11-18',
            'classification': 'Civica chart palette, categorical colours by entity position; the same in light and dark mode',
            'generator': 'docs/scripts/generate-data-colour-examples.py',
            'source': CHARTS['url'],
            'colours': [{'id': colour, 'name': name(colour), 'hex': hexof(colour), 'role': role, **({'theme_colour': token} if token else {})}
                        for colour, token, role in used],
        },
    }


# ---------------------------------------------------------------------------
# 2. Quantitative: two heatmaps of rooms by day.
# ---------------------------------------------------------------------------
DAYS = [('Mon', 'Monday 9'), ('Tue', 'Tuesday 10'), ('Wed', 'Wednesday 11'), ('Thu', 'Thursday 12'),
        ('Fri', 'Friday 13'), ('Sat', 'Saturday 14'), ('Sun', 'Sunday 15')]
SEQUENTIAL = {
    'id': 'sequential',
    'family': 'Blues',
    'unit': 'kWh',
    'measure': 'Energy used each day',
    'minimum': 0, 'maximum': 2.0,
    'boundary_rule': 'A value on a boundary goes in the higher step; 2.0 kWh is in the top step.',
    'steps': [
        {'colour': 'blue-tint-80', 'from': 0.0, 'to': 0.4, 'label': 'Under 0.4'},
        {'colour': 'blue-tint-50', 'from': 0.4, 'to': 0.8, 'label': '0.4 to 0.8'},
        {'colour': 'blue-tint-25', 'from': 0.8, 'to': 1.2, 'label': '0.8 to 1.2'},
        {'colour': 'blue', 'from': 1.2, 'to': 1.6, 'label': '1.2 to 1.6'},
        {'colour': 'blue-shade-50', 'from': 1.6, 'to': 2.0, 'label': '1.6 to 2.0'},
    ],
    'rows': [
        ('Living room', [1.42, 1.18, 1.35, 1.27, 1.64, 1.96, 1.83]),
        ('Study', [1.71, 1.88, 1.52, 1.79, 1.12, 0.31, 0.24]),
        ('Bedroom', [0.46, 0.41, 0.52, 0.44, 0.49, 0.63, 0.58]),
        ('Hall', [0.18, 0.16, 0.21, 0.17, 0.22, 0.27, 0.25]),
        ('Garage', [0.0, 0.0, None, 0.0, 0.04, 0.92, 0.0]),
    ],
}
DIVERGENT = {
    'id': 'divergent',
    'family': 'Blues and Reds, with Black tint 95% from the Neutrals at the centre',
    'unit': '°C',
    'measure': 'Average temperature while the heating was scheduled on, minus the 20 °C target',
    'minimum': -2.5, 'centre': 0, 'maximum': 2.5, 'target_temperature': 20,
    'boundary_rule': 'A value on a boundary goes in the step nearer the centre.',
    'steps': [
        {'colour': 'blue', 'from': -2.5, 'to': -1.5, 'label': f'{MINUS}2.5 to {MINUS}1.5'},
        {'colour': 'blue-tint-50', 'from': -1.5, 'to': -0.5, 'label': f'{MINUS}1.5 to {MINUS}0.5'},
        {'colour': 'black-tint-95', 'from': -0.5, 'to': 0.5, 'label': f'{MINUS}0.5 to +0.5'},
        {'colour': 'red-tint-50', 'from': 0.5, 'to': 1.5, 'label': '+0.5 to +1.5'},
        {'colour': 'red', 'from': 1.5, 'to': 2.5, 'label': '+1.5 to +2.5'},
    ],
    'rows': [
        ('Living room', [0.4, 0.2, -0.3, 0.6, 1.1, 1.7, 1.2]),
        ('Kitchen', [0.9, 1.3, 0.7, 1.6, 2.1, 0.8, 0.3]),
        ('Bedroom', [-1.8, -1.6, -1.2, -2.2, -1.4, -0.9, -1.1]),
        ('Study', [-0.6, -0.2, -0.8, 0.1, -1.7, -2.3, -2.1]),
        ('Hall', [-0.4, -0.7, -0.2, None, -0.9, -0.3, 0.0]),
    ],
}


def step_for(scale, value):
    if value is None:
        return None
    if value < scale['minimum'] or value > scale['maximum']:
        raise SystemExit(f'{scale["id"]}: {value} is outside this scale')
    steps = scale['steps']
    if scale['id'] == 'sequential':
        for step in reversed(steps):
            if value >= step['from']:
                return step
    # Divergent: a value on a boundary goes in the step nearer the centre.
    for step in steps:
        if (value < 0 and step['from'] <= value < step['to']) or (value > 0 and step['from'] < value <= step['to']) or (value == 0 and step['from'] < 0 < step['to']):
            return step
    raise SystemExit(f'{value}: no step')


def signed(value, scale):
    if value is None:
        return 'Not supplied'
    if scale['id'] == 'sequential':
        return f'{value:.2f}'
    if value == 0:
        return '0.0'
    return (MINUS if value < 0 else '+') + f'{abs(value):.1f}'


# Each room's name sits on its own line above its row of cells, so the picture
# is only 232 wide: 12-unit text renders at 12px or more down to a 232px-wide
# picture (the embedded example at a 320px viewport is about 238px wide).
HEAT_LEFT, HEAT_CELL, HEAT_ROW_LABEL, HEAT_CELL_HEIGHT, HEAT_TOP = 4, 32, 16, 28, 20
HEAT_WIDTH = HEAT_LEFT * 2 + len(DAYS) * HEAT_CELL
HEAT_ROW = HEAT_ROW_LABEL + HEAT_CELL_HEIGHT
HEAT_HEIGHT = HEAT_TOP + 5 * HEAT_ROW + 22 + 12 + 3 * 24 + 6


def heatmap(scale):
    tid = f'heatmap-{scale["id"]}'
    ink = hexof('black')
    grid = hexof(GRID)
    gx, cw, ch, gy = HEAT_LEFT, HEAT_CELL, HEAT_CELL_HEIGHT, HEAT_TOP
    parts = [f'<rect x="0" y="0" width="{HEAT_WIDTH}" height="{HEAT_HEIGHT}" fill="#FFFFFF"/>']
    for index, (short, _) in enumerate(DAYS):
        parts.append(text(gx + index * cw + cw / 2, 14, short, ink, anchor='middle'))
    for r, (room, values) in enumerate(scale['rows']):
        parts.append(text(gx, gy + r * HEAT_ROW + 12, room, ink))
        y = gy + r * HEAT_ROW + HEAT_ROW_LABEL
        for c, value in enumerate(values):
            x = gx + c * cw
            step = step_for(scale, value)
            day = DAYS[c][1]
            if step is None:
                parts.append(f'<rect data-room="{room}" data-day="{day}" data-value="missing" x="{x}" y="{y}" width="{cw}" height="{ch}" fill="#FFFFFF" stroke="{grid}" stroke-width="1"/>')
                parts.append(f'<path d="M{x + 9} {y + 6} L{x + cw - 9} {y + ch - 6} M{x + cw - 9} {y + 6} L{x + 9} {y + ch - 6}" fill="none" stroke="{ink}" stroke-width="1.5"/>')
                continue
            fill = hexof(step['colour'])
            parts.append(f'<rect data-room="{room}" data-day="{day}" data-value="{value}" data-step="{step["colour"]}" x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{fill}" stroke="{grid}" stroke-width="1"/>')
            parts.append(text(x + cw / 2, y + ch / 2 + 4, signed(value, scale), hexof(ink_for(fill)), size=12, anchor='middle'))
    ky = gy + len(scale['rows']) * HEAT_ROW + 22
    parts.append(text(gx, ky, f'Key ({scale["unit"]})', ink, weight=700))
    keys = [(step['colour'], step['label']) for step in scale['steps']] + [(None, 'Not supplied')]
    for index, (colour, label) in enumerate(keys):
        kx, kyy = gx + (index % 2) * (HEAT_WIDTH // 2), ky + 12 + (index // 2) * 24
        if colour is None:
            parts.append(f'<rect x="{kx}" y="{kyy}" width="16" height="16" fill="#FFFFFF" stroke="{grid}" stroke-width="1"/>')
            parts.append(f'<path d="M{kx + 3} {kyy + 3} L{kx + 13} {kyy + 13} M{kx + 13} {kyy + 3} L{kx + 3} {kyy + 13}" fill="none" stroke="{ink}" stroke-width="1.5"/>')
        else:
            parts.append(f'<rect data-key="{colour}" x="{kx}" y="{kyy}" width="16" height="16" fill="{hexof(colour)}" stroke="{grid}" stroke-width="1"/>')
        parts.append(text(kx + 22, kyy + 12, label, ink))
    return tid, ''.join(parts)


def heatmap_figure(scale, caption, title, desc):
    tid, body = heatmap(scale)
    svg = (f'<svg role="img" aria-labelledby="{tid}-title {tid}-desc" viewBox="0 0 {HEAT_WIDTH} {HEAT_HEIGHT}" '
           f'style="display:block;width:100%;max-width:360px;height:auto;font-family:{FONT};" data-chart="{tid}">'
           f'<title id="{tid}-title">{escape(title)}</title><desc id="{tid}-desc">{escape(desc)}</desc><g aria-hidden="true">{body}</g></svg>')
    return f'<figure style="margin:0 0 30px;"><figcaption class="govuk-heading-s">{escape(caption)}</figcaption>{svg}</figure>'


def heatmap_table(scale, label, caption):
    rows = [[room] + [signed(value, scale) for value in values] for room, values in scale['rows']]
    return table(label, caption, ['Room'] + [long for _, long in DAYS], rows)


def quantitative():
    seq, div = SEQUENTIAL, DIVERGENT
    seq_desc = ('A grid of 5 rooms by 7 days. Each cell is shaded from light blue for little energy to dark blue for more, and shows its value. '
                'The living room and the study use the most, up to 1.96 kWh; the hall uses the least. '
                'The garage used 0.00 kWh on 5 days and has no reading for Wednesday, shown as a crossed empty cell. The table below gives every value.')
    div_desc = ('A grid of 5 rooms by 7 days. Blue cells were colder than the 20 °C target, red cells warmer and grey cells within half a degree of it; darker means further from the target. '
                'Every cell shows its signed difference. The bedroom was below target all week, down to −2.2 °C; the kitchen was above it, up to +2.1 °C. '
                'The hall has no reading for Thursday, shown as a crossed empty cell. The table below gives every value.')
    used = [(step['colour'], None, f'{step["label"]} kWh') for step in seq['steps']]
    used += [(step['colour'], None, f'{step["label"]} °C difference') for step in div['steps']]
    used += [(GRID, None, 'cell outlines'), ('black', None, 'labels and values on pale cells'), ('white', None, 'values on dark cells')]
    html = ''.join([
        '<section aria-labelledby="quantitative-heading">',
        '<h2 class="govuk-heading-m" id="quantitative-heading">A week of room readings as two heatmaps</h2>',
        '<p class="govuk-body"><strong>Synthetic data.</strong> '
        'Daily readings for 5 rooms, Monday 9 to Sunday 15 November 2026, Europe/London; each cell prints its value.</p>',
        '<section class="c-data-colour-reference" aria-labelledby="sequential-heading">',
        '<h3 class="govuk-heading-m" id="sequential-heading">An amount: energy used each day, 0 to 2 kWh</h3>',
        '<p class="govuk-body">Five steps of Blues, 0.4 kWh each. A value on a boundary goes in the higher step.</p>',
        heatmap_figure(seq, 'Energy used each day by room, 9 to 15 November 2026 (kWh)', 'Heatmap of energy used each day by room in kilowatt-hours', seq_desc),
        heatmap_table(seq, 'Daily energy use by room', 'Energy used each day by room, 9 to 15 November 2026 (kWh)'),
        '</section>',
        '<section class="c-data-colour-reference" aria-labelledby="divergent-heading">',
        '<h3 class="govuk-heading-m" id="divergent-heading">A difference: temperature against a 20 °C target</h3>',
        '<p class="govuk-body">Each cell is the room’s <strong>average temperature while the heating was scheduled on, minus the 20 °C target</strong>. '
        'Blues are below the target, reds above it and Black tint 95% within half a degree. A value on a boundary goes in the step nearer the centre.</p>',
        heatmap_figure(div, 'Difference from the 20 °C target by room, 9 to 15 November 2026 (°C)', 'Heatmap of each room’s daily temperature difference from a 20 °C target', div_desc),
        heatmap_table(div, 'Daily difference from the heating target by room', 'Difference from the 20 °C target by room, 9 to 15 November 2026 (°C)'),
        '</section>',
        colours_used(used),
        '</section>',
    ])

    def scale_record(scale):
        rows = [{'room': room, 'values': Flow(values), 'colour_ids': Flow(step and step['colour'] for step in (step_for(scale, value) for value in values))}
                for room, values in scale['rows']]
        keep = {k: v for k, v in scale.items() if k not in ('rows', 'steps')}
        keep['steps'] = [{**step, 'name': name(step['colour']), 'hex': hexof(step['colour'])} for step in scale['steps']]
        keep['scale_family_ids'] = sorted({step['colour'] for step in scale['steps']} & set(sum(SCALE_IDS.values(), [])))
        keep['days'] = [f'{day} November 2026' for _, day in DAYS]
        keep['rows'] = rows
        return keep

    return {
        'title': 'Sequential and divergent heatmaps with explicit missing data',
        'description': 'Two heatmaps of synthetic Home Assistant data for 5 rooms over a week: daily energy on a 5-step Blues scale, and the difference from a 20 °C target on a Blues and Reds scale with a neutral centre. Every cell shows its value, missing readings are crossed, and matching tables give every value.',
        'height': 2300,
        'html': html,
        'colour_reference': {
            'reviewed_on': '2026-11-18',
            'classification': 'Civica chart palette, listed scale steps only; nothing interpolated',
            'generator': 'docs/scripts/generate-data-colour-examples.py',
            'source': CHARTS['url'],
            'time_zone': 'Europe/London',
            'period_start': '2026-11-09',
            'period_end': '2026-11-15',
            'data_classification': 'Synthetic documentation data; not readings from a Home Assistant instance',
            'sequential': scale_record(seq),
            'divergent': scale_record(div),
            'missing': 'No mapped colour: a crossed empty cell, the key entry “Not supplied” and “Not supplied” in the table.',
            'text_contrast': 'Black on the pale steps and White on the dark steps, each at least 4.5:1, chosen by the generator.',
            'colours': [{'id': colour, 'name': name(colour), 'hex': hexof(colour), 'role': role} for colour, _, role in used],
        },
    }


# ---------------------------------------------------------------------------
class Literal(str):
    pass


class Flow(list):
    pass


class Dumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


Dumper.add_representer(Literal, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|'))
Dumper.add_representer(tuple, lambda dumper, data: dumper.represent_list(list(data)))
Dumper.add_representer(Flow, lambda dumper, data: dumper.represent_sequence('tag:yaml.org,2002:seq', list(data), flow_style=True))


def block(key, example):
    example = dict(example)
    example['html'] = Literal(example['html'].replace('><', '>\n<'))
    dumped = yaml.dump({key: example}, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=10000)
    return ''.join('  ' + line if line.strip() else line for line in dumped.splitlines(True))


current = open(TARGET, encoding='utf-8').read()
generated = {'data-colour-categorical': categorical(), 'data-colour-quantitative': quantitative()}
text_out = current
for key, example in generated.items():
    pattern = re.compile(rf'^  {re.escape(key)}:\n(?:    .*\n|\n)*', re.M)
    if not pattern.search(text_out):
        sys.exit(f'{TARGET}: {key} not found')
    text_out = pattern.sub(lambda _: block(key, example), text_out, count=1)
HEADER = ('# data-colour-categorical and data-colour-quantitative are generated by\n'
          '# docs/scripts/generate-data-colour-examples.py: edit the script and run it again.\n'
          '# The other examples were written by a one-off script; every colour is from\n'
          '# docs/data/govuk-brand-colours.json. Never hand-edit a colour.\n')
text_out = HEADER + re.sub(r'\A(?:#.*\n)+', '', text_out)
if '--check' in sys.argv:
    if current != text_out:
        sys.exit(f'{TARGET} is out of date. Run python3 docs/scripts/generate-data-colour-examples.py.')
    print('Data colour examples are current.')
else:
    with open(TARGET, 'w', encoding='utf-8') as out:
        out.write(text_out)
    print('written', ', '.join(generated))
