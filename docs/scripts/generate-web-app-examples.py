#!/usr/bin/env python3
"""Generate docs/data/web-app-colour-examples.yml: a Civica Home Assistant
dashboard in a desktop browser (web palette), and the Home Assistant Companion
app showing the same frontend at phone width (app palette). Each picture is
drawn as Home Assistant looks with the Civica theme in light mode.
Run from the repository root: python3 docs/scripts/generate-web-app-examples.py
Pass --check to fail if the YAML differs from what this script writes.
Every colour comes from docs/data/govuk-brand-colours.json by its ID. The script
stops if a picture uses a colour outside its palette, or if any text in a
picture is below 4.5:1 against the colour behind it."""
import json
import math
import sys
from html import escape

import yaml

DATA = json.load(open('docs/data/govuk-brand-colours.json'))
C = DATA['colours']
PALETTES = {page: {i for group in DATA['pages'][page]['palette'] for i in group['colours']} for page in ('web', 'app')}
FONT = 'Roboto,Helvetica Neue,Helvetica,Arial,sans-serif'


def luminance(hex_value):
    channels = [int(hex_value[at:at + 2], 16) / 255 for at in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    high, low = sorted([luminance(a), luminance(b)], reverse=True)
    return (high + 0.05) / (low + 0.05)


class Picture:
    """Collects the colours a picture uses, in order, and checks each one
    against the palette the picture is for."""

    def __init__(self, palette):
        self.palette = palette
        self.used = []

    def c(self, colour_id):
        if colour_id not in self.palette:
            raise SystemExit(f'{colour_id} is not in the GOV.UK {self.palette_name()} palette')
        if colour_id not in self.used:
            self.used.append(colour_id)
        return C[colour_id]['hex']

    def palette_name(self):
        return 'web' if self.palette is PALETTES['web'] else 'app'

    def text(self, x, y, words, size, ink, behind, weight=400, anchor='start'):
        ratio = contrast(C[ink]['hex'], C[behind]['hex'])
        if ratio < 4.5:
            raise SystemExit(f'“{words}”: {C[ink]["name"]} on {C[behind]["name"]} is {ratio:.2f}:1, below 4.5:1')
        self.c(behind)
        return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{self.c(ink)}"'
                + (f' text-anchor="{anchor}"' if anchor != 'start' else '') + f'>{escape(words)}</text>')

    def names(self):
        return [C[i]['name'] for i in self.used]


def svg(tid, title, desc, body, width=960, height=640, style=''):
    return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="{tid}-t {tid}-d" style="display:block;width:100%;height:auto;{style}font-family:{FONT}">'
            f'<title id="{tid}-t">{escape(title)}</title><desc id="{tid}-d">{escape(desc)}</desc>{body}</svg>')


def figure(tid, markup, caption, picture, notice):
    """The caption names only the colours the reader is told to notice."""
    missing = [i for i in notice if i not in picture.used]
    if missing:
        raise SystemExit(f'{tid}: caption names colours the picture does not use: {missing}')
    used = ', '.join(C[i]['name'] for i in notice)
    return (f'<figure style="margin:0 0 30px" aria-labelledby="{tid}-c">{markup}'
            f'<figcaption class="govuk-body-s" id="{tid}-c" style="margin-top:10px"><strong>{escape(caption)}</strong><br>Colours: {escape(used)}.</figcaption></figure>')


def block(paragraph, items):
    return f'<p class="govuk-body">{escape(paragraph)}</p><div style="max-width:720px">' + ''.join(items) + '</div>'


def phones(*pictures):
    """Phone pictures side by side on a wide screen, one above the other on a
    narrow one, so that each stays readable at 320px."""
    return ('<div style="display:flex;flex-wrap:wrap;gap:20px;justify-content:center">'
            + ''.join(f'<div style="flex:1 1 250px;max-width:340px">{picture}</div>' for picture in pictures) + '</div>')


# Icons, drawn on a 24-unit grid in one colour with simple shapes, in the
# manner of the line and solid icons Home Assistant uses.
ICONS = {
    'menu': '<path d="M3 6h18M3 12h18M3 18h18" fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round"/>',
    'search': '<circle cx="10" cy="10" r="6.5" fill="none" stroke="{c}" stroke-width="2.2"/><path d="M15 15l6 6" stroke="{c}" stroke-width="2.4" stroke-linecap="round"/>',
    'assist': '<path d="M4 4h16v12H9l-5 4z" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"/><circle cx="8.5" cy="10" r="1.4" fill="{c}"/><circle cx="12" cy="10" r="1.4" fill="{c}"/><circle cx="15.5" cy="10" r="1.4" fill="{c}"/>',
    'dots': '<circle cx="12" cy="5" r="2" fill="{c}"/><circle cx="12" cy="12" r="2" fill="{c}"/><circle cx="12" cy="19" r="2" fill="{c}"/>',
    'dashboard': '<rect x="3" y="3" width="8" height="10" fill="{c}"/><rect x="13" y="3" width="8" height="6" fill="{c}"/><rect x="13" y="11" width="8" height="10" fill="{c}"/><rect x="3" y="15" width="8" height="6" fill="{c}"/>',
    'bolt': '<path d="M14 2L5 14h6l-1.5 8L19 10h-6z" fill="{c}"/>',
    'map': '<path d="M12 2.5a7 7 0 0 0-7 7c0 5.2 7 12.5 7 12.5s7-7.3 7-12.5a7 7 0 0 0-7-7z" fill="none" stroke="{c}" stroke-width="2"/><circle cx="12" cy="9.5" r="2.6" fill="{c}"/>',
    'logbook': '<rect x="3" y="4" width="4" height="4" fill="{c}"/><rect x="3" y="10" width="4" height="4" fill="{c}"/><rect x="3" y="16" width="4" height="4" fill="{c}"/><path d="M10 6h11M10 12h11M10 18h11" stroke="{c}" stroke-width="2"/>',
    'history': '<rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="{c}" stroke-width="2"/><path d="M8 17v-5M12 17V8M16 17v-3" stroke="{c}" stroke-width="2.2"/>',
    'todo': '<rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="{c}" stroke-width="2"/><path d="M7 12l3.5 3.5L17 9" fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
    'cog': '<path d="M10.3 2h3.4l.5 2.6 1.9.8 2.2-1.5 2.4 2.4-1.5 2.2.8 1.9 2.6.5v3.4l-2.6.5-.8 1.9 1.5 2.2-2.4 2.4-2.2-1.5-1.9.8-.5 2.6h-3.4l-.5-2.6-1.9-.8-2.2 1.5-2.4-2.4 1.5-2.2-.8-1.9L2 13.7v-3.4l2.6-.5.8-1.9-1.5-2.2 2.4-2.4 2.2 1.5 1.9-.8z" fill="{c}"/><circle cx="12" cy="12" r="3.4" fill="{bg}"/>',
    'bell': '<path d="M6 17v-6a6 6 0 0 1 12 0v6l2 2H4z" fill="{c}"/><circle cx="12" cy="21" r="2" fill="{c}"/>',
    'bulb': '<path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" fill="{c}"/><rect x="8.5" y="18.5" width="7" height="2" fill="{c}"/>',
    'lamp': '<path d="M8 3h8l3 8H5z" fill="{c}"/><rect x="11" y="11" width="2" height="9" fill="{c}"/><rect x="7" y="20" width="10" height="2" fill="{c}"/>',
    'thermometer': '<rect x="9.5" y="2.5" width="5" height="12" rx="2.5" fill="none" stroke="{c}" stroke-width="2"/><circle cx="12" cy="17.5" r="4" fill="{c}"/><rect x="11" y="8" width="2" height="8" fill="{c}"/>',
    'drop': '<path d="M12 2.5S5 10.5 5 15a7 7 0 0 0 14 0c0-4.5-7-12.5-7-12.5z" fill="{c}"/>',
    'window': '<rect x="4" y="3" width="16" height="18" fill="none" stroke="{c}" stroke-width="2"/><path d="M12 3v18M4 12h16" stroke="{c}" stroke-width="2"/>',
    'flame': '<path d="M12 2c.5 4 6 6.5 6 12a6 6 0 0 1-12 0c0-3 1.5-5 3-6.5 0 2 .8 3.2 2 3.7C11 8 10.5 5 12 2z" fill="{c}"/>',
    'lock': '<path d="M7 10V7a5 5 0 0 1 10 0v3" fill="none" stroke="{c}" stroke-width="2.2"/><rect x="5" y="10" width="14" height="11" rx="1.5" fill="{c}"/>',
    'account': '<circle cx="12" cy="8" r="4.5" fill="{c}"/><path d="M3.5 21a8.5 6.5 0 0 1 17 0z" fill="{c}"/>',
    'door': '<rect x="6" y="2.5" width="12" height="19" fill="none" stroke="{c}" stroke-width="2"/><circle cx="15" cy="12" r="1.3" fill="{c}"/>',
    'calendar': '<rect x="3.5" y="5" width="17" height="16" rx="1.5" fill="none" stroke="{c}" stroke-width="2"/><path d="M3.5 10h17M8 3v4M16 3v4" stroke="{c}" stroke-width="2"/>',
    'chevron-right': '<path d="M9 5l7 7-7 7" fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
    'chevron-down': '<path d="M6 9l6 6 6-6" fill="none" stroke="{c}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    'plus': '<path d="M12 5v14M5 12h14" stroke="{c}" stroke-width="2.4" stroke-linecap="round"/>',
    'minus': '<path d="M5 12h14" stroke="{c}" stroke-width="2.4" stroke-linecap="round"/>',
    'devices': '<rect x="2" y="4" width="15" height="11" rx="1" fill="none" stroke="{c}" stroke-width="2"/><path d="M6 19h7" stroke="{c}" stroke-width="2"/><rect x="16" y="9" width="6" height="11" rx="1" fill="{c}"/>',
    'robot': '<rect x="4" y="7" width="16" height="13" rx="2" fill="{c}"/><path d="M12 3v4" stroke="{c}" stroke-width="2"/><circle cx="12" cy="3" r="1.6" fill="{c}"/><circle cx="9" cy="13" r="1.8" fill="{bg}"/><circle cx="15" cy="13" r="1.8" fill="{bg}"/>',
    'sofa': '<rect x="6" y="5" width="12" height="8" rx="1.5" fill="{c}"/><rect x="2" y="10" width="20" height="8" rx="2" fill="{c}"/><rect x="4" y="18" width="2" height="3" fill="{c}"/><rect x="18" y="18" width="2" height="3" fill="{c}"/>',
    'info': '<circle cx="12" cy="12" r="9" fill="none" stroke="{c}" stroke-width="2"/><path d="M12 11v6" stroke="{c}" stroke-width="2.2"/><circle cx="12" cy="7.5" r="1.4" fill="{c}"/>',
}


def icon(p, name, cx, cy, colour, size=24, behind='white'):
    """An icon centred on (cx, cy). behind is the colour that shows through
    any cut-out, such as the hole in the cog."""
    shape = ICONS[name].replace('{c}', p.c(colour)).replace('{bg}', p.c(behind))
    return f'<g transform="translate({cx - size / 2:g} {cy - size / 2:g}) scale({size / 24:g})">{shape}</g>'


def status_icons(p, right, y, colour):
    ink = p.c(colour)
    bars = ''.join(f'<rect x="{right - 66 + n * 5}" y="{y - 3 - n * 3}" width="3" height="{3 + n * 3}" fill="{ink}"/>' for n in range(4))
    wifi = f'<path d="M{right - 41} {y - 7}a9 9 0 0 1 14 0M{right - 38} {y - 3}a5 5 0 0 1 8 0" fill="none" stroke="{ink}" stroke-width="2.2" stroke-linecap="round"/><circle cx="{right - 34}" cy="{y}" r="1.6" fill="{ink}"/>'
    battery = f'<rect x="{right - 22}" y="{y - 10}" width="20" height="11" rx="3" fill="none" stroke="{ink}" stroke-width="1.5"/><rect x="{right - 20}" y="{y - 8}" width="14" height="7" rx="1.5" fill="{ink}"/>'
    return bars + wifi + battery


# The Civica lock-up, as the Civica companion puts it in the sidebar: the
# supplied brand/civica/core/lockup-white.svg geometry, unchanged and scaled.
def lockup(p, x, y, width):
    ink = p.c('white')
    k = width / 1180
    return (f'<g transform="translate({x} {y}) scale({k:.5f})"><g transform="translate(10,2)">'
            f'<path d="M52 120 L128 56 L166 88 V58 Q166 46 178 46 H188 Q200 46 200 58 V116 L208 122 Q218 130 218 144 V198 Q218 218 198 218 H58 Q38 218 38 198 V144 Q38 130 52 120 Z" fill="none" stroke="{ink}" stroke-width="22" stroke-linejoin="round" stroke-linecap="round"/>'
            + ''.join(f'<circle cx="{cx}" cy="{cy}" r="15" fill="{ink}"/>' for cy in (136, 180) for cx in (88, 128, 168))
            + f'</g><text x="290" y="186" font-family="Roboto, Helvetica Neue, Helvetica, Arial, Liberation Sans, Arimo, sans-serif" font-weight="700" font-size="178" fill="{ink}">Civica</text></g>')


# Home Assistant parts, in the colours the Civica theme sets in light mode:
# app-header-background-color Primary blue with White text, White page,
# sidebar and cards, card-border and divider Black tint 80%, primary text
# Black, secondary text and sidebar icons Black tint 25%, link Blue shade 10%.
# Two theme values are not palette colours, so the nearest one stands in:
# the selected sidebar row (#E8EEF3) is Black tint 95% and its text (#19578D)
# Blue shade 25%. Home Assistant's own device colours, which Civica does not
# set, are drawn with the nearest palette colour: amber for a light that is on
# as Primary yellow, orange for heating as Primary orange, each with its tint
# for the icon circle.
def toolbar(p, x, y, w, items, tabs=None, title=None, menu=True, actions=('search', 'assist', 'dots')):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="56" fill="{p.c("blue")}"/>'
    left = x + 16
    if menu:
        out += icon(p, 'menu', x + 26, y + 28, 'white')
        left = x + 58
    if tabs:
        for label, width, current in tabs:
            out += p.text(left + width / 2, y + 34, label, 15, 'white', 'blue', 700 if current else 400, 'middle')
            if current:
                out += f'<rect x="{left}" y="{y + 52}" width="{width}" height="4" fill="{p.c("white")}"/>'
            left += width
    if title:
        out += p.text(left, y + 35, title, 20, 'white', 'blue')
    right = x + w - 26
    for name in reversed(actions):
        out += icon(p, name, right, y + 28, 'white')
        right -= 38
    return out


def switch(p, right, cy, on):
    x = right - 48
    if on:
        return (f'<rect x="{x}" y="{cy - 14}" width="48" height="28" rx="14" fill="{p.c("blue")}"/>'
                f'<circle cx="{x + 34}" cy="{cy}" r="10" fill="{p.c("white")}"/>')
    return (f'<rect x="{x + 1}" y="{cy - 13}" width="46" height="26" rx="13" fill="{p.c("white")}" stroke="{p.c("black")}" stroke-width="2"/>'
            f'<circle cx="{x + 14}" cy="{cy}" r="8" fill="{p.c("black")}"/>')


def card(p, x, y, w, h):
    return f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" fill="{p.c("white")}" stroke="{p.c("black-tint-80")}"/>'


def entities_card(p, x, y, w, rows):
    """An entities card: an icon, the name and a switch on each row."""
    out = card(p, x, y, w, 16 + 48 * len(rows))
    for n, (name, glyph, on) in enumerate(rows):
        cy = y + 32 + n * 48
        out += icon(p, glyph, x + 28, cy, 'black') + p.text(x + 60, cy + 5, name, 15, 'black', 'white') + switch(p, x + w - 16, cy, on)
    return out


def tile(p, x, y, w, name, state, glyph, colour='black-tint-25', tint='black-tint-80'):
    """A tile card: the icon in a tinted circle, the name and the state."""
    return (card(p, x, y, w, 56) + f'<circle cx="{x + 28}" cy="{y + 28}" r="18" fill="{p.c(tint)}"/>' + icon(p, glyph, x + 28, y + 28, colour, 20, tint)
            + p.text(x + 56, y + 25, name, 15, 'black', 'white', 700) + p.text(x + 56, y + 44, state, 14, 'black-tint-25', 'white'))


def badge(p, x, y, w, glyph, label):
    return (f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="35" rx="17.5" fill="{p.c("white")}" stroke="{p.c("black-tint-80")}"/>'
            + icon(p, glyph, x + 20, y + 18, 'black-tint-25', 18) + p.text(x + 36, y + 23, label, 14, 'black', 'white', 700))


def heading(p, x, y, words):
    return p.text(x, y, words, 18, 'black', 'white', 700)


def sidebar_rows(p, x, y, w, rows, selected, gap=44):
    out = ''
    for n, (glyph, label) in enumerate(rows):
        cy = y + 20 + n * gap
        current = label == selected
        if current:
            out += f'<rect x="{x + 6}" y="{cy - 20}" width="{w - 12}" height="40" rx="4" fill="{p.c("black-tint-95")}"/>'
        behind = 'black-tint-95' if current else 'white'
        out += icon(p, glyph, x + 28, cy, 'blue-shade-25' if current else 'black-tint-25', 22, behind)
        out += p.text(x + 60, cy + 5, label, 15, 'blue-shade-25' if current else 'black', behind, 700 if current else 400)
    return out


def sidebar(p, x, y, w, h, selected, rows, foot=140):
    """Home Assistant's sidebar with the Civica theme and companion: the menu
    row in the theme colour with the Civica lock-up, then the panels, then
    Settings, Notifications and the user's profile."""
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{p.c("white")}"/>'
           f'<rect x="{x}" y="{y}" width="{w}" height="56" fill="{p.c("blue")}"/>' + icon(p, 'menu', x + 28, y + 28, 'white')
           + lockup(p, x + 52, y + 14, 120)
           + sidebar_rows(p, x, y + 64, w, rows, selected))
    bottom = y + h - foot
    out += (f'<rect x="{x}" y="{bottom}" width="{w}" height="1" fill="{p.c("black-tint-80")}"/>'
            + sidebar_rows(p, x, bottom + 6, w, [('cog', 'Settings'), ('bell', 'Notifications')], selected)
            + f'<circle cx="{x + 28}" cy="{bottom + 114}" r="15" fill="{p.c("blue-tint-80")}"/>'
            + p.text(x + 28, bottom + 119, 'AM', 12, 'black', 'blue-tint-80', 700, 'middle')
            + p.text(x + 60, bottom + 119, 'Alex Morgan', 15, 'black', 'white'))
    return out + f'<rect x="{x + w - 1}" y="{y + 56}" width="1" height="{h - 56}" fill="{p.c("black-tint-80")}"/>'


PANELS = [('dashboard', 'Overview'), ('bolt', 'Energy'), ('map', 'Map'), ('logbook', 'Logbook'), ('history', 'History')]


def thermostat(p, x, y, w):
    """A thermostat card in heat mode: the dial shows the target temperature
    and its buttons. Heat is Home Assistant's orange, drawn as Primary orange."""

    cx, cy, r = x + w / 2, y + 112, 72
    out = card(p, x, y, w, 210) + p.text(cx, y + 26, 'Thermostat', 15, 'black', 'white', 700, 'middle')

    def point(angle):
        return cx + r * math.cos(math.radians(angle)), cy + r * math.sin(math.radians(angle))
    (sx, sy), (tx, ty), (ex, ey) = point(135), point(270), point(405)
    out += (f'<path d="M{sx:.1f} {sy:.1f}A{r} {r} 0 1 1 {ex:.1f} {ey:.1f}" fill="none" stroke="{p.c("orange-tint-80")}" stroke-width="14" stroke-linecap="round"/>'
            f'<path d="M{sx:.1f} {sy:.1f}A{r} {r} 0 0 1 {tx:.1f} {ty:.1f}" fill="none" stroke="{p.c("orange")}" stroke-width="14" stroke-linecap="round"/>'
            f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="4" fill="{p.c("white")}"/>'
            + p.text(cx, cy - 26, 'Heating', 13, 'black-tint-25', 'white', anchor='middle')
            + p.text(cx, cy + 10, '21 °C', 32, 'black', 'white', anchor='middle')
            + icon(p, 'thermometer', cx - 30, cy + 29, 'black-tint-25', 14) + p.text(cx - 20, cy + 34, '19.5 °C', 13, 'black-tint-25', 'white'))
    for bx, glyph in ((cx - 22, 'minus'), (cx + 22, 'plus')):
        out += f'<circle cx="{bx}" cy="{cy + 64}" r="15" fill="{p.c("white")}" stroke="{p.c("black-tint-50")}"/>' + icon(p, glyph, bx, cy + 64, 'black', 16)
    return out


def phone(p, tid, inner, top='blue'):
    """A phone outline in Black tint 50% on a 380 by 760 picture. Its screen
    is clipped to the outline; the status bar is in the colour given."""
    ink = 'white' if top == 'blue' else 'black'
    return (f'<rect width="380" height="760" fill="{p.c("white")}"/>'
            f'<defs><clipPath id="{tid}"><rect x="10" y="10" width="360" height="740" rx="40"/></clipPath></defs>'
            f'<g clip-path="url(#{tid})"><rect x="10" y="10" width="360" height="740" fill="{p.c("white")}"/>'
            f'<rect x="10" y="10" width="360" height="44" fill="{p.c(top)}"/>' + p.text(44, 38, '9:41', 15, ink, top, 700) + status_icons(p, 346, 38, ink)
            + inner + f'<rect x="130" y="734" width="120" height="5" rx="2.5" fill="{p.c("black")}"/></g>'
            f'<rect x="10" y="10" width="360" height="740" rx="40" fill="none" stroke="{p.c("black-tint-50")}" stroke-width="3"/>')


HOME_TABS = [('Home', 58, True), ('Upstairs', 80, False), ('Garden', 70, False)]


def home_view(p, top):
    """The Home view of the dashboard at phone width, from the toolbar down."""
    return (toolbar(p, 10, top, 360, None, tabs=HOME_TABS, actions=('search', 'dots'))
            + badge(p, 92, top + 70, 96, 'thermometer', '9.5 °C') + badge(p, 196, top + 70, 92, 'bolt', '1.2 kW')
            + heading(p, 26, top + 140, 'Living room')
            + entities_card(p, 22, top + 152, 336, [('Main light', 'bulb', True), ('Lamp', 'lamp', False)])
            + heading(p, 26, top + 290, 'Kitchen')
            + tile(p, 22, top + 302, 164, 'Temperature', '20.5 °C', 'thermometer') + tile(p, 194, top + 302, 164, 'Humidity', '48 %', 'drop')
            + tile(p, 22, top + 366, 336, 'Window', 'Closed', 'window')
            + card(p, 22, top + 430, 336, 80) + p.text(38, top + 462, 'Bins go out on Thursday.', 15, 'black', 'white')
            + p.text(38, top + 490, 'See the bin calendar', 15, 'blue-shade-10', 'white') + f'<rect x="38" y="{top + 493}" width="131" height="1.5" fill="{p.c("blue-shade-10")}"/>')


examples = {}

# 1. Web palette example: the Home view of a dashboard in a desktop browser.
p = Picture(PALETTES['web'])
body = (f'<rect width="800" height="540" fill="{p.c("white")}"/>'
        # Browser: window controls and the address bar.
        f'<rect width="800" height="44" fill="{p.c("black-tint-95")}"/>'
        + ''.join(f'<circle cx="{cx}" cy="22" r="6" fill="{p.c("black-tint-80")}"/>' for cx in (20, 40, 60))
        + f'<rect x="84" y="9" width="700" height="26" rx="13" fill="{p.c("white")}"/>'
        + p.text(102, 27, 'home.morgan.example:8123/lovelace/home', 13, 'black-tint-25', 'white')
        + sidebar(p, 0, 44, 200, 496, 'Overview', PANELS)
        + toolbar(p, 200, 44, 600, None, tabs=HOME_TABS, menu=False)
        + badge(p, 398, 112, 96, 'thermometer', '9.5 °C') + badge(p, 504, 112, 92, 'bolt', '1.2 kW')
        + heading(p, 216, 184, 'Living room') + heading(p, 508, 184, 'Kitchen')
        + entities_card(p, 216, 198, 276, [('Main light', 'bulb', True), ('Lamp', 'lamp', False)])
        + thermostat(p, 216, 318, 276)
        + tile(p, 508, 198, 276, 'Temperature', '20.5 °C', 'thermometer')
        + tile(p, 508, 262, 276, 'Humidity', '48 %', 'drop')
        + tile(p, 508, 326, 276, 'Window', 'Closed', 'window')
        + card(p, 508, 390, 276, 80) + p.text(524, 422, 'Bins go out on Thursday.', 15, 'black', 'white')
        + p.text(524, 450, 'See the bin calendar', 15, 'blue-shade-10', 'white') + f'<rect x="524" y="453" width="131" height="1.5" fill="{p.c("blue-shade-10")}"/>'
        + f'<rect x="0.5" y="0.5" width="799" height="539" fill="none" stroke="{p.c("black-tint-80")}"/>')
web_desc = ('A desktop browser shows a Home Assistant dashboard with the Civica theme and companion on a White background. '
            'On the left is Home Assistant’s sidebar: a Primary blue row with the menu icon and the Civica logo in White, which the Civica companion adds, then Overview, which is selected, on a Black tint 95% row with its icon and name in Blue shade 25%, Energy, Map, Logbook and History, and at the bottom Settings, Notifications and the user Alex Morgan. '
            'The Primary blue toolbar has the view tabs Home, Upstairs and Garden in White, with Home underlined, and Search, Assist and menu icons. '
            'The Home view has 2 badges, 9.5 °C and 1.2 kW, and 2 sections. Living room has an entities card where Main light is on, with a Primary blue switch, and Lamp is off, and a thermostat card heating to 21 °C with a current temperature of 19.5 °C on a Primary orange dial. '
            'Kitchen has tiles for Temperature 20.5 °C, Humidity 48 % and Window Closed, and a card that says bins go out on Thursday with a link to the bin calendar in Blue shade 10%. '
            'Cards are White with Black tint 80% borders, text is Black and secondary text Black tint 25%.')
web = figure('web-dashboard',
             '<div role="region" aria-label="Dashboard drawing, which scrolls sideways on a narrow screen" tabindex="0" style="overflow-x:auto">'
             + svg('web-dashboard', 'Web palette example: a Home Assistant dashboard in a desktop browser', web_desc, body, 800, 540, 'min-width:600px;')
             + '</div>',
             'A drawing of a dashboard, not a screenshot: the household, web address, rooms and readings are invented.', p,
             ['white', 'blue', 'black-tint-80', 'black', 'black-tint-25', 'blue-shade-10'])
examples['web-colour-dashboard'] = {
    'title': 'A Home Assistant dashboard in the web palette',
    'description': 'A Home Assistant dashboard with the Civica theme and companion in a desktop browser: Home Assistant’s sidebar, the Primary blue toolbar with view tabs, and White cards with quiet borders on a White background.',
    'height': 700,
    'html': '<section aria-labelledby="web-dashboard-h"><h2 class="govuk-heading-m" id="web-dashboard-h">Web palette example</h2>' + block(
        'A Home Assistant dashboard with the Civica theme and companion in a desktop browser. Notice the White background and cards, the Primary blue toolbar with the view tabs in White, '
        'Black tint 80% card borders, Black text with secondary text and sidebar icons in Black tint 25%, and the link in Blue shade 10%. '
        'The switch that is on is Primary blue. The heating dial uses Home Assistant’s own orange for heating, drawn in the nearest palette colour, Primary orange. '
        'The theme colours for the selected sidebar row, #E8EEF3 and #19578D, are not palette colours either, so the row is drawn as Black tint 95% with Blue shade 25% text.', [web]) + '</section>',
}

# 2. Mobile web header: the same dashboard in a phone browser.
p = Picture(PALETTES['app'])
inner = (f'<rect x="10" y="54" width="360" height="48" fill="{p.c("white")}"/>'
         f'<rect x="26" y="58" width="328" height="38" rx="19" fill="{p.c("black-tint-95")}"/>'
         + icon(p, 'lock', 100, 77, 'black', 14, 'black-tint-95') + p.text(114, 83, 'home.morgan.example', 16, 'black', 'black-tint-95')
         + home_view(p, 102))
mobile_desc = ('A phone browser at home.morgan.example shows the same Home Assistant dashboard. The Primary blue toolbar has the menu icon, the view tabs Home, Upstairs and Garden in White with Home underlined, and Search and menu icons. '
               'Below it on a White background are the badges 9.5 °C and 1.2 kW, a Living room card with Main light on, with a Primary blue switch, and Lamp off, and Kitchen tiles for Temperature 20.5 °C, Humidity 48 % and Window Closed, and a card about bin day with a link.')
mobile = figure('mobile-web', '<div style="max-width:340px;margin:0 auto">' + svg('mobile-web', 'Mobile web header: a Home Assistant dashboard in a phone browser', mobile_desc, phone(p, 'mobile-web-clip', inner, 'white'), 380, 760) + '</div>',
                'A drawing of a phone browser, not a screenshot: the household, web address and readings are invented.', p, ['blue', 'white'])
examples['app-colour-mobile-web-header'] = {
    'title': 'The Primary blue toolbar on the mobile web',
    'description': 'A Home Assistant dashboard in a phone browser: the Primary blue toolbar with the menu icon and view tabs in White.',
    'height': 900,
    'html': '<section aria-labelledby="mobile-web-h"><h2 class="govuk-heading-m" id="mobile-web-h">Mobile web header</h2>' + block(
        'A Home Assistant dashboard in a phone browser. Notice that the Primary blue toolbar keeps the menu icon and the view tabs in White, as on a desktop.', [mobile]) + '</section>',
}


# 3. App header: 4 Companion app screens, 2 to a picture.
def logbook_screen(p):
    out = (toolbar(p, 10, 54, 360, None, title='Logbook', actions=('dots',))
           + f'<rect x="23" y="125" width="334" height="54" fill="{p.c("white")}" stroke="{p.c("black")}" stroke-width="2"/>'
           + p.text(38, 146, 'Period', 12, 'black-tint-25', 'white') + p.text(38, 168, 'Today', 16, 'black', 'white')
           + icon(p, 'calendar', 334, 152, 'black', 22)
           + p.text(26, 214, 'Wednesday 18 November', 15, 'black', 'white', 700))
    for n, (glyph, what, when) in enumerate([
            ('bulb', 'Kitchen light turned on', '18:42'), ('lock', 'Front door was locked', '18:40'),
            ('flame', 'Heating changed to Heat', '18:30'), ('account', 'Alex arrived home', '18:28'),
            ('lamp', 'Lamp turned off', '17:55'), ('door', 'Back door was closed', '17:50'),
            ('window', 'Kitchen window was closed', '17:31')]):
        y = 248 + n * 62
        out += icon(p, glyph, 40, y + 4, 'black-tint-25', 22) + p.text(66, y, what, 15, 'black', 'white') + p.text(66, y + 21, when, 13, 'black-tint-25', 'white')
    return out


def settings_screen(p):
    out = toolbar(p, 10, 54, 360, None, title='Settings', actions=('search', 'dots')) + card(p, 14, 122, 352, 8 + 72 * 7)
    for n, (glyph, colour, name, hint) in enumerate([
            ('devices', 'blue-shade-25', 'Devices & services', 'Integrations, entities and helpers'),
            ('robot', 'green-tint-25', 'Automations & scenes', 'Automations, scenes and scripts'),
            ('sofa', 'orange', 'Areas, labels & zones', 'Manage areas, labels and zones'),
            ('dashboard', 'magenta', 'Dashboards', 'Organise your dashboards'),
            ('account', 'orange-shade-25', 'People', 'Manage who can use your home'),
            ('cog', 'purple', 'System', 'Backups, logs and restart'),
            ('info', 'black-tint-25', 'About', 'Version and credits')]):
        y = 126 + n * 72
        out += (f'<rect x="30" y="{y + 16}" width="40" height="40" rx="8" fill="{p.c(colour)}"/>' + icon(p, glyph, 50, y + 36, 'white', 22, colour)
                + p.text(84, y + 32, name, 15, 'black', 'white') + p.text(84, y + 52, hint, 13, 'black-tint-25', 'white')
                + icon(p, 'chevron-right', 344, y + 36, 'black-tint-25', 18))
    return out


def shopping_screen(p):
    out = (toolbar(p, 10, 54, 360, None, title='Shopping list', actions=('dots',)) + icon(p, 'chevron-down', 206, 82, 'white', 20)
           + f'<rect x="23" y="125" width="334" height="50" fill="{p.c("white")}" stroke="{p.c("black")}" stroke-width="2"/>'
           + p.text(38, 156, 'Add item', 16, 'black-tint-25', 'white') + icon(p, 'plus', 334, 150, 'black', 22))
    for n, item in enumerate(['Milk', 'Bread', 'AA batteries', 'Light bulbs']):
        y = 214 + n * 50
        out += f'<rect x="27" y="{y - 11}" width="22" height="22" rx="2" fill="{p.c("white")}" stroke="{p.c("black")}" stroke-width="2"/>' + p.text(66, y + 6, item, 16, 'black', 'white')
    out += f'<rect x="10" y="414" width="360" height="1" fill="{p.c("black-tint-80")}"/>' + p.text(26, 446, 'Completed', 15, 'black', 'white', 700)
    for n, (item, width) in enumerate([('Washing-up liquid', 128), ('Bin bags', 60)]):
        y = 484 + n * 50
        out += (f'<rect x="26" y="{y - 12}" width="24" height="24" rx="2" fill="{p.c("blue")}"/>'
                f'<path d="M31 {y}l5 5 9-10" fill="none" stroke="{p.c("white")}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
                + p.text(66, y + 6, item, 16, 'black-tint-25', 'white') + f'<rect x="66" y="{y}" width="{width}" height="1.5" fill="{p.c("black-tint-25")}"/>')
    return out


header_figures = []
for tid, screens, caption, desc in [
    ('app-header-1', [('home', 'Home view'), ('logbook', 'Logbook')],
     'The Home view and Logbook. A drawing of the Companion app, not a screenshot: the household, rooms and events are invented.',
     ['The Companion app shows the Home view of the dashboard. Under a Primary blue status bar, the Primary blue toolbar has the menu icon, the view tabs Home, Upstairs and Garden in White with Home underlined, and Search and menu icons. '
      'Below are the badges 9.5 °C and 1.2 kW, a Living room card with Main light on and Lamp off, Kitchen tiles for Temperature, Humidity and Window, and a card about bin day.',
      'The Companion app shows Logbook. The Primary blue toolbar has the menu icon and the title Logbook in White. Below are a Period field set to Today and the events for Wednesday 18 November, '
      'from Kitchen light turned on at 18:42 to Kitchen window was closed at 17:31.']),
    ('app-header-2', [('settings', 'Settings'), ('shopping', 'Shopping list')], 'Settings and a shopping list.',
     ['The Companion app shows Settings. The Primary blue toolbar has the menu icon, the title Settings in White, and Search and menu icons. '
      'Below is a card listing Devices & services, Automations & scenes, Areas, labels & zones, Dashboards, People, System and About, each with a coloured icon and a short description.',
      'The Companion app shows a to-do list. The Primary blue toolbar has the menu icon and the title Shopping list in White. Below are an Add item field, 4 items to buy with empty checkboxes, '
      'and 2 completed items, Washing-up liquid and Bin bags, with Primary blue ticked checkboxes.']),
]:
    p = Picture(PALETTES['app'])
    draw = {'home': lambda p: home_view(p, 54), 'logbook': logbook_screen, 'settings': settings_screen, 'shopping': shopping_screen}
    pictures = [svg(f'{tid}{suffix}', f'App header: {label}', text, phone(p, f'{tid}{suffix}-clip', draw[kind](p)), 380, 760)
                for (kind, label), text, suffix in zip(screens, desc, ('', 'b'))]
    header_figures.append(figure(tid, phones(*pictures), caption, p, ['blue', 'white']))
examples['app-colour-header'] = {
    'title': 'The Primary blue toolbar in Companion app screens',
    'description': 'Four Companion app screens, each starting with the Primary blue toolbar.',
    'height': 1700,
    'html': '<section aria-labelledby="app-header-h"><h2 class="govuk-heading-m" id="app-header-h">App header</h2>' + block(
        'Four screens of the Companion app, which shows the Home Assistant frontend: the Home view of a dashboard, Logbook, Settings and a shopping list. '
        'Notice that every screen starts with the same Primary blue toolbar, with the menu icon and the view tabs or the screen’s title in White, so people always know where they are.', header_figures) + '</section>',
}

# 4. Examples: tinted tile icons, and the tinted row in the sidebar.
p = Picture(PALETTES['app'])
upstairs = (toolbar(p, 10, 54, 360, None, tabs=[('Home', 58, False), ('Upstairs', 80, True), ('Garden', 70, False)], actions=('search', 'dots'))
            + heading(p, 26, 196, 'Bedroom')
            + tile(p, 22, 208, 164, 'Bedside lamp', 'On · 40 %', 'lamp', 'yellow', 'yellow-tint-80')
            + tile(p, 194, 208, 164, 'Ceiling light', 'Off', 'bulb')
            + tile(p, 22, 272, 336, 'Heating', 'Heat · 19 °C', 'flame', 'orange', 'orange-tint-80')
            + tile(p, 22, 336, 164, 'Window', 'Closed', 'window') + tile(p, 194, 336, 164, 'Humidity', '52 %', 'drop')
            + heading(p, 26, 434, 'Office')
            + tile(p, 22, 446, 164, 'Desk lamp', 'On · 70 %', 'lamp', 'yellow', 'yellow-tint-80')
            + tile(p, 194, 446, 164, 'Spotlights', 'Off', 'bulb')
            + tile(p, 22, 510, 336, 'Temperature', '20 °C', 'thermometer')
            # A guide annotation, not Home Assistant UI: an Accent yellow label
            # with a Black border, pointing up at the menu icon.
            + f'<path d="M26 128L36 113L46 128" fill="{p.c("yellow-accent")}" stroke="{p.c("black")}" stroke-width="2" stroke-linejoin="round"/>'
            + f'<rect x="20" y="127" width="206" height="38" rx="19" fill="{p.c("yellow-accent")}" stroke="{p.c("black")}" stroke-width="2"/>'
            + f'<rect x="28" y="125" width="16" height="4" fill="{p.c("yellow-accent")}"/>'
            + p.text(123, 152, 'Tap to open the menu', 16, 'black', 'yellow-accent', 700, 'middle'))
drawer = (f'<rect x="10" y="54" width="360" height="696" fill="{p.c("black-tint-50")}"/>'
          + f'<rect x="274" y="54" width="96" height="56" fill="{p.c("blue-shade-25")}"/>'
          + sidebar(p, 10, 54, 264, 696, 'Overview', PANELS + [('todo', 'To-do lists')], 172))
examples_pictures = [
    svg('app-examples', 'App examples: tiles with tinted icons', 'The Companion app shows the Upstairs view under the Primary blue toolbar. '
        'A guide annotation, which is not part of the app, points at the menu icon: an Accent yellow label with a Black border that says Tap to open the menu in Black. Each tile has its icon in a tinted circle: '
        'Bedside lamp and Desk lamp are on, with yellow icons on Yellow tint 80%; Heating is heating, with an orange icon on Orange tint 80%; Ceiling light, Spotlights and the sensors have Black tint 25% icons on Black tint 80%. '
        'The tiles themselves stay White with Black tint 80% borders.', phone(p, 'app-examples-clip', upstairs), 380, 760),
    svg('app-examples-b', 'App examples: the sidebar with a tinted row', 'The Companion app shows Home Assistant’s sidebar, opened from the menu icon, over the dimmed dashboard. '
        'It starts with a Primary blue row with the menu icon and the Civica logo in White, which appears when the Civica companion is installed. Overview, the open dashboard, is on a Black tint 95% row with its icon and name in Blue shade 25%. '
        'Below are Energy, Map, Logbook, History and To-do lists, then Settings, Notifications and the user Alex Morgan.', phone(p, 'app-examples-b-clip', drawer), 380, 760),
]
example_figure = figure('app-examples', phones(*examples_pictures),
                        'A drawing of the Companion app, not a screenshot: the household, rooms and readings are invented, and the Accent yellow label is a guide annotation, not part of the app.', p,
                        ['yellow-accent', 'yellow-tint-80', 'black-tint-80', 'black-tint-95', 'blue-shade-25'])
examples['app-colour-examples'] = {
    'title': 'Tinted tile icons and menu rows in Companion app screens',
    'description': 'Two Companion app screens: tiles that tint only their icon circle, and the sidebar with a tinted row for the open dashboard.',
    'height': 900,
    'html': '<section aria-labelledby="app-examples-h"><h2 class="govuk-heading-m" id="app-examples-h">Examples</h2>' + block(
        'Two Companion app screens: the Upstairs view of a dashboard, and the sidebar opened from the menu icon. '
        'Notice the Accent yellow guide label, an App palette colour, with Black text and a Black border, pointing at the menu icon. '
        'Notice too that each tile tints only its icon circle, Yellow tint 80% for a light that is on and Black tint 80% for one that is off, '
        'and that the sidebar marks the open dashboard with a Black tint 95% row and Blue shade 25% text. The tints add structure without filling whole cards. '
        'The sidebar’s Primary blue row with the Civica logo appears when the Civica companion is installed. '
        'Home Assistant’s own amber for lights and orange for heating, and the theme’s #E8EEF3 and #19578D for the open dashboard’s sidebar row, are not palette colours, so they are drawn with the nearest palette colours.', [example_figure]) + '</section>',
}


for ex in examples.values():
    ex['artwork'] = {
        'creator': 'Civica project; original SVG markup',
        'licence': 'MIT, original project documentation code under LICENSE',
        'source': 'docs/data/web-app-colour-examples.yml',
        'provenance': 'Original drawings of the Home Assistant frontend with the Civica theme in light mode and an invented household, generated by docs/scripts/generate-web-app-examples.py from docs/data/govuk-brand-colours.json; the layout follows Home Assistant’s own sidebar, toolbar and cards, and the colours follow themes/civica.yaml, with the nearest palette colour where a theme or Home Assistant value is not a palette colour. The only identity device is the supplied Civica lock-up (brand/civica/core/lockup-white.svg), unchanged and scaled, where the Civica companion puts it in the sidebar. No Home Assistant, government or other third-party artwork, screenshot or icon file is copied; the icons are drawn with simple shapes.',
        'purpose': 'Show the Civica web and app palettes in drawings of a Home Assistant dashboard and Companion app screens; they are not screenshots of Civica, Home Assistant or the Companion app.',
        'intended_background': 'Each picture carries its own background; every text pair reaches at least 4.5:1, checked when the script runs.',
        'alternative_text_decision': 'Each picture is an SVG image with a title and a description that names what it shows and its colours; the caption names the colours to notice. The page text gives the guidance, so the page works without the pictures.',
        'review_status': 'Source checks only; integrated rendered review is recorded separately.',
    }


class Literal(str):
    pass


yaml.add_representer(Literal, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|'))
for ex in examples.values():
    ex['html'] = Literal(ex['html'].replace('><', '>\n<') + '\n')
TARGET = 'docs/data/web-app-colour-examples.yml'
text = ('# Generated by docs/scripts/generate-web-app-examples.py from docs/data/govuk-brand-colours.json.\n'
        '# Edit the script and run it again rather than editing this file.\n'
        + yaml.dump({'examples': examples}, sort_keys=False, allow_unicode=True, width=10000))
if '--check' in sys.argv:
    try:
        with open(TARGET, encoding='utf-8') as current:
            if current.read() != text:
                sys.exit(f'{TARGET} is out of date. Run python3 docs/scripts/generate-web-app-examples.py.')
    except FileNotFoundError:
        sys.exit(f'{TARGET} is missing. Run python3 docs/scripts/generate-web-app-examples.py.')
    print('Web-app colour examples are current.')
else:
    with open(TARGET, 'w', encoding='utf-8') as out:
        out.write(text)
    print('written', ', '.join(examples))
