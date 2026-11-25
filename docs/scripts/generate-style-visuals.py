#!/usr/bin/env python3
"""Generate docs/data/style-visual-examples.yml: original Civica pictures for
the Illustration, Icons and images, and Layout and spacing pages.
Run from the repository root: python3 docs/scripts/generate-style-visuals.py
Pass --check to fail if the YAML differs from what this script writes.

Every colour comes from docs/data/govuk-brand-colours.json by its ID. Each
picture names the palette for its channel (Web-app colours for guidance
pages and dashboards, the app palette for app screens, the social palette for
social posts) and the script stops if a picture uses a colour outside it, or
if any text in a picture is below 4.5:1 against the colour behind it.
Home Assistant subjects only; all households, rooms and readings are invented."""
import json
import sys
from html import escape

import yaml

DATA = json.load(open('docs/data/govuk-brand-colours.json'))
C = DATA['colours']
PAGES = DATA['pages']
GROUP = lambda page: {i for group in PAGES[page]['palette'] for i in group['colours']}
PALETTES = {
    'web': GROUP('web') | GROUP('app') | GROUP('illustrations'),
    'app': GROUP('app'),
    'social': GROUP('social'),
}
FONT = 'Roboto,Helvetica Neue,Helvetica,Arial,sans-serif'


def luminance(hex_value):
    channels = [int(hex_value[at:at + 2], 16) / 255 for at in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    high, low = sorted([luminance(a), luminance(b)], reverse=True)
    return (high + 0.05) / (low + 0.05)


class Picture:
    """Collects the colours a picture uses and checks each against its palette."""

    def __init__(self, palette):
        self.palette_name = palette
        self.palette = PALETTES[palette]
        self.used = []

    def c(self, colour_id):
        if colour_id not in self.palette:
            raise SystemExit(f'{colour_id} is not in the {self.palette_name} palette')
        if colour_id not in self.used:
            self.used.append(colour_id)
        return C[colour_id]['hex']

    def text(self, x, y, words, size, ink, behind, weight=400, anchor='start'):
        ratio = contrast(C[ink]['hex'], C[behind]['hex'])
        if ratio < 4.5:
            raise SystemExit(f'"{words}": {C[ink]["name"]} on {C[behind]["name"]} is {ratio:.2f}:1, below 4.5:1')
        self.c(behind)
        return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{self.c(ink)}"'
                + (f' text-anchor="{anchor}"' if anchor != 'start' else '') + f'>{escape(words)}</text>')

    def names(self):
        return ', '.join(C[i]['name'] for i in self.used)


def svg(tid, title, desc, body, width=800, height=500):
    # An empty desc gives a title-only picture, whose title is the whole alt text.
    labels = f'{tid}-t {tid}-d' if desc else f'{tid}-t'
    described = f'<desc id="{tid}-d">{escape(desc)}</desc>' if desc else ''
    return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="{labels}" style="display:block;width:100%;height:auto;font-family:{FONT}">'
            f'<title id="{tid}-t">{escape(title)}</title>{described}{body}</svg>')


VERDICT = {'do': ('Do', '#0F7A52'), 'dont': ('Do not', '#CA3535')}


def figure(tid, p, title, desc, body, caption, note, width=800, height=500, verdict=None, extra='', colours=True):
    """A picture with its caption: a bold summary, what to notice, and the
    colours it uses. A do or do-not picture starts its caption with Do or
    Do not, and has a coloured rule above it that repeats the word."""
    markup = svg(tid, title, desc, body, width, height)
    lead = ''
    rule = ''
    if verdict:
        word, colour = VERDICT[verdict]
        lead = f'{word}: '
        rule = f'border-top:5px solid {colour};padding-top:10px;'
    return (f'<figure style="margin:0;{rule}" aria-labelledby="{tid}-c">{markup}'
            f'<figcaption class="govuk-body-s" id="{tid}-c" style="margin-top:10px"><strong>{escape(lead + caption)}</strong>'
            f'<br>{escape(note)}' + (f' Colours: {escape(p.names())}.' if colours else '') + f'</figcaption>{extra}</figure>')


def grid(items, minimum=280, width=960):
    return (f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax({minimum}px,1fr));gap:30px 20px;max-width:{width}px">'
            + ''.join(items) + '</div>')


def lead(paragraph, body):
    return f'<p class="govuk-body">{escape(paragraph)}</p>' + body


# Icons on a 24-unit grid, in one colour, in the manner of the icons Home
# Assistant uses. These are original shapes, not copies of an icon set. The
# shapes are shared with docs/scripts/generate-web-app-examples.py.
ICONS = {
    'bulb': '<path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" fill="{c}"/><rect x="8.5" y="18.5" width="7" height="2" fill="{c}"/>',
    'thermometer': '<rect x="9.5" y="2.5" width="5" height="12" rx="2.5" fill="none" stroke="{c}" stroke-width="2"/><circle cx="12" cy="17.5" r="4" fill="{c}"/><rect x="11" y="8" width="2" height="8" fill="{c}"/>',
    'drop': '<path d="M12 2.5S5 10.5 5 15a7 7 0 0 0 14 0c0-4.5-7-12.5-7-12.5z" fill="{c}"/>',
    'door': '<rect x="6" y="2.5" width="12" height="19" fill="none" stroke="{c}" stroke-width="2"/><circle cx="15" cy="12" r="1.3" fill="{c}"/>',
    'door-open': '<path d="M5 21.5V2.5h14v19" fill="none" stroke="{c}" stroke-width="2"/><path d="M5 2.5l8 3v18l-8-2z" fill="{c}"/>',
    'search': '<circle cx="10" cy="10" r="6.5" fill="none" stroke="{c}" stroke-width="2.2"/><path d="M15 15l6 6" stroke="{c}" stroke-width="2.4" stroke-linecap="round"/>',
    'plug': '<rect x="5" y="7" width="14" height="9" rx="2" fill="{c}"/><rect x="8" y="2" width="2" height="5" fill="{c}"/><rect x="14" y="2" width="2" height="5" fill="{c}"/><rect x="11" y="16" width="2" height="6" fill="{c}"/>',
    'circle': '<circle cx="12" cy="12" r="8" fill="{c}"/>',
    'zoom': '<circle cx="10" cy="10" r="6.5" fill="none" stroke="{c}" stroke-width="2.2"/><path d="M15 15l6 6M7 10h6M10 7v6" stroke="{c}" stroke-width="2.2" stroke-linecap="round"/>',
}


def icon(p, name, cx, cy, colour, size=24):
    shape = ICONS[name].replace('{c}', p.c(colour))
    return f'<g transform="translate({cx - size / 2:g} {cy - size / 2:g}) scale({size / 24:g})">{shape}</g>'


# Shared scene parts: flat colour, simple shapes, no outlines.
def person(p, x, y, body, skin, hair, scale=1.0, lean=0, build=1.0, headscarf=False):
    """A standing figure whose feet are at (x, y). lean tilts it in degrees."""
    s = scale
    w = 70 * s * build
    h = 150 * s
    head = 26 * s
    parts = (f'<rect x="{x - w / 2:g}" y="{y - h:g}" width="{w:g}" height="{h:g}" rx="{w / 2.4:g}" fill="{p.c(body)}"/>'
             f'<circle cx="{x:g}" cy="{y - h - head + 4 * s:g}" r="{head:g}" fill="{p.c(skin)}"/>')
    if headscarf:
        parts += f'<path d="M{x - head - 4 * s:g} {y - h + 8 * s:g}a{head + 4 * s:g} {head + 4 * s:g} 0 1 1 {2 * (head + 4 * s):g} 0z" fill="{p.c(hair)}"/>' \
                 f'<circle cx="{x:g}" cy="{y - h - head + 8 * s:g}" r="{head * 0.62:g}" fill="{p.c(skin)}"/>'
    else:
        parts += f'<path d="M{x - head:g} {y - h - head + 2 * s:g}a{head:g} {head:g} 0 0 1 {2 * head:g} 0q{-head:g} {-14 * s:g} {-2 * head:g} 0z" fill="{p.c(hair)}"/>'
    if lean:
        return f'<g transform="rotate({lean} {x:g} {y:g})">{parts}</g>'
    return parts


def arm(p, x1, y1, x2, y2, colour, width=22):
    return f'<path d="M{x1:g} {y1:g}L{x2:g} {y2:g}" stroke="{p.c(colour)}" stroke-width="{width}" stroke-linecap="round"/>'


def hand(p, cx, cy, skin, size=1.0):
    return f'<circle cx="{cx:g}" cy="{cy:g}" r="{13 * size:g}" fill="{p.c(skin)}"/>'


def thermostat(p, cx, cy, r, ring, face, display):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{p.c(ring)}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.72:g}" fill="{p.c(face)}"/>'
            f'<rect x="{cx - r * 0.38:g}" y="{cy - r * 0.18:g}" width="{r * 0.76:g}" height="{r * 0.36:g}" fill="{p.c(display)}"/>')


def radiator(p, x, y, w, h, colour, gap):
    fins = ''.join(f'<rect x="{x + n * w / 6 + 4:g}" y="{y}" width="{w / 6 - 8:g}" height="{h}" rx="6" fill="{p.c(colour)}"/>' for n in range(6))
    return fins + f'<rect x="{x}" y="{y + h / 2 - 3:g}" width="{w}" height="6" fill="{p.c(colour)}"/>'


def window(p, x, y, w, h, glass, bars):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{p.c(glass)}"/>'
            f'<path d="M{x + w / 2:g} {y}V{y + h}M{x} {y + h / 2:g}H{x + w}" stroke="{p.c(bars)}" stroke-width="8"/>')


def sofa(p, x, y, w, colour, cushion):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="70" rx="22" fill="{p.c(colour)}"/>'
            f'<rect x="{x + 20}" y="{y + 30}" width="{w - 40}" height="50" rx="14" fill="{p.c(cushion)}"/>'
            f'<rect x="{x - 10}" y="{y + 30}" width="40" height="70" rx="18" fill="{p.c(colour)}"/>'
            f'<rect x="{x + w - 30}" y="{y + 30}" width="40" height="70" rx="18" fill="{p.c(colour)}"/>')


def sensor(p, cx, cy, colour, light, size=34):
    return (f'<rect x="{cx - size / 2:g}" y="{cy - size / 2:g}" width="{size}" height="{size}" rx="{size / 4:g}" fill="{p.c(colour)}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{size / 6:g}" fill="{p.c(light)}"/>')


def room(p, wall, floor, floor_y=400):
    return (f'<rect width="800" height="500" fill="{p.c(wall)}"/>'
            f'<rect y="{floor_y}" width="800" height="{500 - floor_y}" fill="{p.c(floor)}"/>')


examples = {}
ARTWORK = {
    'creator': 'Civica project; original SVG markup',
    'licence': 'MIT, original project documentation code under LICENSE',
    'source': 'docs/data/style-visual-examples.yml',
    'provenance': 'Original drawings generated by docs/scripts/generate-style-visuals.py from the Civica colour data. All artwork is drawn for Civica.',
    'intended_background': 'Each picture carries its own background.',
    'alternative_text_decision': 'Each picture is an SVG image with a title and a description that says what it shows; the caption says what to notice and lists its colours. The page text carries the full rule, so the picture is a visual aid.',
    'review_status': 'Source checks only; rendered review at desktop width and 320px is recorded by the illustrator handover.',
}


def add(key, title, description, html, purpose, height=520):
    examples[key] = {'title': title, 'description': description, 'height': height, 'html': html,
                     'artwork': dict(ARTWORK, purpose=purpose)}


# ---------------------------------------------------------------------------
# Illustration: in the Companion app. An app screen uses the app palette, so
# skin tones come from the oranges (the app palette has no browns).
def phone_frame(p, inner, behind='white'):
    return (f'<rect x="0" y="0" width="360" height="620" rx="44" fill="{p.c("black")}"/>'
            f'<rect x="12" y="12" width="336" height="596" rx="34" fill="{p.c(behind)}"/>'
            f'<clipPath id="CLIP"><rect x="12" y="12" width="336" height="596" rx="34"/></clipPath><g clip-path="url(#CLIP)">{inner}</g>')


def app_screen(tid, heading, lines, button, scene, scene_desc, title_words):
    p = Picture('app')
    inner = (f'<rect x="12" y="12" width="336" height="110" fill="{p.c("blue")}"/>'
             + p.text(36, 96, title_words, 22, 'white', 'blue', 700)
             + f'<rect x="12" y="122" width="336" height="250" fill="{p.c("blue-tint-95")}"/>'
             + scene(p)
             + p.text(36, 418, heading, 22, 'black', 'white', 700)
             + ''.join(p.text(36, 452 + n * 26, line, 16, 'black', 'white') for n, line in enumerate(lines))
             + f'<rect x="36" y="{470 + len(lines) * 26}" width="288" height="52" fill="{p.c("blue")}"/>'
             + p.text(180, 503 + len(lines) * 26, button, 17, 'white', 'blue', 700, 'middle'))
    body = phone_frame(p, inner).replace('CLIP', f'{tid}-clip')
    desc = (f'A Home Assistant Companion app screen titled {title_words}. An illustration fills the top of the screen: {scene_desc} '
            f'Under it, as text on the screen, the heading {heading}, a short instruction and a {button} button.')
    return p, svg(tid, f'Companion app screen: {heading}', desc, body, 360, 620)


def scene_heating(p):
    return (f'<rect x="12" y="330" width="336" height="42" fill="{p.c("blue-tint-80")}"/>'
            + window(p, 50, 160, 110, 120, 'blue-tint-50', 'blue-tint-95')
            + radiator(p, 50, 290, 110, 44, 'blue-shade-25', None)
            + thermostat(p, 250, 220, 46, 'blue', 'white', 'teal-accent')
            + '<path d="M250 150v-14M198 170l-10-10M302 170l10-10" stroke="' + p.c('blue-accent') + '" stroke-width="8" stroke-linecap="round"/>')


def scene_sensor(p):
    return (f'<rect x="12" y="330" width="336" height="42" fill="{p.c("blue-tint-80")}"/>'
            f'<rect x="150" y="150" width="120" height="180" fill="{p.c("blue-shade-25")}"/>'
            f'<rect x="160" y="160" width="100" height="170" fill="{p.c("blue-tint-50")}"/>'
            f'<circle cx="245" cy="250" r="7" fill="{p.c("blue-shade-50")}"/>'
            + person(p, 80, 336, 'yellow', 'orange-tint-50', 'black', 0.82)
            + arm(p, 94, 240, 128, 222, 'yellow', 18)
            + sensor(p, 155, 214, 'blue', 'teal-accent', 26)
            + f'<rect x="168" y="203" width="12" height="22" rx="3" fill="{p.c("blue")}"/>'
            + hand(p, 134, 222, 'orange-tint-50', 0.8))


p1, phone1 = app_screen('ill-app-heating', 'Heating at night', ['The hall thermostat drops to 16 °C', 'at 10:30pm and warms up at 6am.'],
                        'Set the schedule', scene_heating,
                        'a hall with a window, a radiator under it and a round thermostat on the wall, highlighted in Accent teal.', 'Heating')
p2, phone2 = app_screen('ill-app-sensor', 'Fit the back door sensor', ['Stick the sensor on the frame and', 'the magnet on the door, side by side.'],
                        'Next step', scene_sensor,
                        'a person in yellow holds a door sensor up to the frame of the back door.', 'Add device')
phones = ('<div style="display:flex;flex-wrap:wrap;gap:20px;justify-content:center">'
          + ''.join(f'<figure style="margin:0;flex:1 1 220px;max-width:300px" aria-labelledby="{tid}-c">{markup}'
                    f'<figcaption class="govuk-body-s" id="{tid}-c" style="margin-top:10px"><strong>{escape(cap)}</strong><br>{escape(note)} Colours: {escape(pp.names())}.</figcaption></figure>'
                    for tid, markup, cap, note, pp in [
                        ('ill-app-heating', phone1, 'A step in a heating guide', 'The illustration sits above the text, and the times are written in the text, not in the drawing.', p1),
                        ('ill-app-sensor', phone2, 'A step in adding a device', 'The drawing shows where the sensor goes. The instruction under it says the same in words.', p2)])
          + '</div>')
add('illustration-companion-app', 'Illustrations in the Companion app',
    'Two original Companion app screens for an invented household, each with an illustration above its heading, instruction and button.',
    lead('These screens are drawings for an invented household, not screenshots.', phones),
    'Show how an illustration sits above its text on a Companion app screen.', 900)


# ---------------------------------------------------------------------------
# Illustration: on social media. 4:5 posts in the social palette, with a
# short headline. The headline is set in the post picture, so the post text
# must repeat it.
def social_tile(tid, bg, headline, art, art_desc, ink='white'):
    p = Picture('social')
    body = f'<rect width="400" height="500" fill="{p.c(bg)}"/>' + art(p)
    body += ''.join(p.text(32, 380 + n * 40, line, 32, ink, bg, 700) for n, line in enumerate(headline))
    words = ' '.join(headline)
    desc = f'A social media post on {C[bg]["name"]}. {art_desc} Under it, the headline: {words}'
    return p, svg(tid, f'Social post: {words}', desc, body, 400, 500)


def art_solar(p):
    return (f'<circle cx="300" cy="90" r="54" fill="{p.c("yellow")}"/>'
            f'<path d="M60 300L180 200L300 300Z" fill="{p.c("blue-shade-50")}"/>'
            f'<rect x="80" y="290" width="200" height="40" fill="{p.c("blue-shade-50")}"/>'
            f'<path d="M140 228L196 228L236 268L180 268Z" fill="{p.c("teal-accent")}"/>')


def art_leak(p):
    return (f'<rect x="70" y="250" width="260" height="80" rx="10" fill="{p.c("white")}"/>'
            f'<rect x="250" y="70" width="20" height="150" fill="{p.c("white")}"/>'
            f'<rect x="230" y="70" width="80" height="20" fill="{p.c("white")}"/>'
            f'<path d="M180 160S150 200 150 220a30 30 0 0 0 60 0c0-20-30-60-30-60z" fill="{p.c("teal-accent")}"/>'
            + sensor(p, 110, 300, 'teal-shade-50', 'teal-accent', 36))


def art_routine(p):
    return (f'<rect x="60" y="80" width="280" height="240" fill="{p.c("purple-shade-50")}"/>'
            f'<circle cx="250" cy="150" r="36" fill="{p.c("yellow-tint-80")}"/>'
            f'<circle cx="266" cy="138" r="32" fill="{p.c("purple-shade-50")}"/>'
            f'<rect x="90" y="250" width="220" height="70" rx="16" fill="{p.c("purple-tint-50")}"/>'
            f'<path d="M110 250V200h40v50" fill="{p.c("purple-tint-80")}"/>'
            f'<circle cx="130" cy="190" r="18" fill="{p.c("yellow")}"/>')


tiles = [
    ('ill-social-solar', 'blue', ['Track your solar', 'panels today'], art_solar, 'A blue house with a solar panel in Accent teal under a yellow sun.',
     'A guide to the energy dashboard', 'Primary blue is the base, and the solar panel is the one accent.'),
    ('ill-social-leak', 'teal-shade-25', ['Get a warning', 'before a leak'], art_leak, 'A white sink with a water drop in Accent teal and a leak sensor on the floor beside it.',
     'A guide to leak sensors', 'Shades of one colour keep the post calm, and the accent marks the water.'),
    ('ill-social-night', 'purple-shade-25', ['A calmer', 'bedtime routine'], art_routine, 'A bedroom at night with a moon in the window and a bedside lamp glowing yellow.',
     'A post about a bedtime routine', 'A warm lamp beside cool purples makes the focal point.'),
]
tile_figures = []
for tid, bg, headline, art, art_desc, cap, note in tiles:
    pp, markup = social_tile(tid, bg, headline, art, art_desc)
    tile_figures.append(f'<figure style="margin:0" aria-labelledby="{tid}-c">{markup}<figcaption class="govuk-body-s" id="{tid}-c" style="margin-top:10px">'
                        f'<strong>{escape(cap)}</strong><br>{escape(note)} Colours: {escape(pp.names())}.</figcaption></figure>')
add('illustration-social', 'Illustrations in social posts',
    'Three original social posts, each with an illustration and a short headline, in the social palette.',
    lead('These posts are drawings for invented guides. Repeat the headline in the text of the post, so that everyone gets it.', grid(tile_figures, 200)),
    'Show how an illustration and a short headline work together in a social post.', 640)


# ---------------------------------------------------------------------------
# Illustration: building a composition, adding detail, showing movement.
def composition():
    items = []
    p = Picture('web')
    body = (room(p, 'blue-tint-80', 'blue-tint-50')
            + f'<rect x="420" y="90" width="200" height="310" fill="{p.c("blue-shade-25")}"/><rect x="436" y="106" width="168" height="294" fill="{p.c("blue-tint-50")}"/>'
            + f'<circle cx="590" cy="260" r="9" fill="{p.c("blue-shade-50")}"/>'
            + thermostat(p, 420, 230, 62, 'blue', 'white', 'teal-accent')
            + f'<rect x="150" y="160" width="140" height="100" fill="{p.c("white")}"/><rect x="164" y="174" width="112" height="72" fill="{p.c("blue-tint-50")}"/>')
    items.append(figure('ill-comp-overlap', p, 'Overlap: a thermostat in front of a door frame',
                        'A hall. A round thermostat overlaps the edge of a door frame, so it sits in front of it. A small picture hangs on the wall to the left.',
                        body, 'Overlap', 'The thermostat overlaps the door frame, which brings it forward without an outline.'))
    p = Picture('web')
    body = (room(p, 'white', 'blue-tint-80', 430)
            + sensor(p, 690, 80, 'blue', 'teal-accent', 54)
            + '<path d="M650 120A60 60 0 0 1 650 40" fill="none" stroke="' + p.c('teal-accent') + '" stroke-width="10" stroke-linecap="round" transform="rotate(-45 690 80)"/>'
            + f'<path d="M100 430h60l-8-60h-44z" fill="{p.c("blue-shade-25")}"/><ellipse cx="130" cy="350" rx="18" ry="30" fill="{p.c("blue")}"/>')
    items.append(figure('ill-comp-space', p, 'Space: a motion sensor in the corner of a plain room',
                        'A plain white room with a motion sensor high in the top right corner and one small plant on the floor. Most of the picture is empty wall.',
                        body, 'Space', 'The plain wall around the sensor keeps the scene calm and leads the eye to it.'))
    p = Picture('web')
    body = (f'<rect width="800" height="500" fill="{p.c("blue-tint-95")}"/>'
            f'<rect x="270" y="30" width="260" height="440" rx="36" fill="{p.c("blue-shade-50")}"/>'
            f'<rect x="286" y="62" width="228" height="376" rx="10" fill="{p.c("white")}"/>'
            + thermostat(p, 400, 230, 80, 'blue', 'blue-tint-95', 'teal-accent')
            + f'<rect x="320" y="350" width="160" height="40" fill="{p.c("blue-tint-80")}"/>'
            + arm(p, 650, 317, 760, 360, 'purple', 40)
            + f'<rect x="490" y="300" width="160" height="34" rx="17" fill="{p.c("orange-tint-50")}"/><circle cx="640" cy="317" r="30" fill="{p.c("orange-tint-50")}"/>')
    items.append(figure('ill-comp-frame', p, 'Frame: a phone screen around a thermostat dial',
                        'A large phone fills the middle of the picture. On its screen is a round thermostat dial. A finger reaches in from the right and touches the edge of the screen.',
                        body, 'Frame', 'The phone is the larger shape that frames the dial, so the eye goes to the action inside it.'))
    return items


def detail():
    items = []
    p = Picture('web')
    body = (room(p, 'blue-tint-80', 'blue-tint-50')
            + sofa(p, 60, 300, 260, 'blue-tint-50', 'blue-tint-80')
            + f'<rect x="500" y="250" width="90" height="90" rx="10" fill="{p.c("white")}"/>'
            + f'<rect x="522" y="272" width="46" height="46" rx="8" fill="{p.c("blue")}"/><circle cx="545" cy="295" r="9" fill="{p.c("teal-accent")}"/>'
            + arm(p, 700, 420, 600, 300, 'green', 34)
            + f'<rect x="560" y="286" width="54" height="22" rx="11" fill="{p.c("brown")}"/><circle cx="604" cy="300" r="18" fill="{p.c("brown")}"/>')
    items.append(figure('ill-detail-action', p, 'Protect the action: a hand pressing a smart plug',
                        'A hand reaches in from the right to press the button on a smart plug in a wall socket. A sofa is in the background on the left, well away from the hand.',
                        body, 'Protect the action', 'The sofa sets the room, but nothing covers the hand or the plug button.'))
    p = Picture('web')
    body = (room(p, 'blue-tint-80', 'blue-tint-50')
            + f'<rect x="250" y="40" width="300" height="360" fill="{p.c("white")}"/>'
            + f'<rect x="250" y="40" width="20" height="360" fill="{p.c("blue-tint-50")}"/>'
            + f'<path d="M550 40L610 20V420L550 400Z" fill="{p.c("white")}"/><path d="M550 40V400" stroke="{p.c("blue-tint-50")}" stroke-width="4"/>'
            + f'<rect x="320" y="80" width="160" height="200" fill="{p.c("blue")}"/>'
            + f'<rect x="350" y="110" width="100" height="40" fill="{p.c("teal-accent")}"/>'
            + f'<rect x="345" y="280" width="16" height="120" fill="{p.c("blue-shade-50")}"/><rect x="439" y="280" width="16" height="120" fill="{p.c("blue-shade-50")}"/>'
            + f'<circle cx="400" cy="210" r="18" fill="{p.c("blue-shade-50")}"/>')
    items.append(figure('ill-detail-familiar', p, 'Make it familiar: a boiler in a kitchen cupboard',
                        'An open kitchen cupboard with a blue boiler inside. The boiler has a display highlighted in Accent teal and 2 pipes running down from it.',
                        body, 'Make it familiar', 'A boiler in a cupboard says straight away that this is a kitchen in a home.'))
    p = Picture('web')
    body = (room(p, 'white', 'blue-tint-80')
            + f'<rect x="70" y="80" width="150" height="320" fill="{p.c("blue-tint-95")}"/>'
            + ''.join(f'<rect x="80" y="{100 + n * 75}" width="130" height="10" fill="{p.c("blue-tint-80")}"/>'
                      f'<rect x="{90 + n * 12}" y="{50 + n * 75 + 15}" width="22" height="45" fill="{p.c("blue-tint-80")}"/>' for n in range(1, 4))
            + sofa(p, 320, 300, 320, 'blue-tint-95', 'blue-tint-80')
            + sensor(p, 480, 170, 'blue', 'teal-accent', 60))
    items.append(figure('ill-detail-context', p, 'Add context quietly: a living room behind a sensor',
                        'A living room with a pale bookshelf and a pale sofa. Above the sofa, a temperature sensor on the wall is the only strong colour.',
                        body, 'Add context quietly', 'The bookshelf and sofa are in pale tints, so the sensor stays the focal point.'))
    return items


def movement():
    items = []
    p = Picture('web')
    body = (room(p, 'blue-tint-80', 'blue-tint-50', 440)
            + f'<rect width="800" height="30" fill="{p.c("white")}"/>'
            + f'<ellipse cx="470" cy="38" rx="46" ry="14" fill="{p.c("blue")}"/><circle cx="470" cy="40" r="6" fill="{p.c("teal-accent")}"/>'
            + '<g transform="rotate(14 340 440)">'
            + person(p, 340, 440, 'orange', 'brown-tint-50', 'black', 1.25)
            + arm(p, 356, 280, 368, 70, 'orange', 26)
            + hand(p, 368, 58, 'brown-tint-50') + '</g>')
    items.append(figure('ill-move-diagonal', p, 'Tilt along a diagonal: reaching up to a smoke alarm',
                        'A person leans forward on a diagonal and reaches up to test a smoke alarm on the ceiling.',
                        body, 'Tilt along a diagonal', 'The body and arm follow one diagonal line up to the alarm, which shows effort.'))
    p = Picture('web')
    body = (room(p, 'blue-tint-80', 'blue-tint-50', 440)
            + f'<rect x="560" y="110" width="170" height="330" fill="{p.c("blue-shade-25")}"/>'
            + f'<path d="M560 110L660 140V470L560 440Z" fill="{p.c("blue")}"/>'
            + '<g transform="rotate(16 380 440)">'
            + f'<path d="M370 360L320 436M392 360L440 436" stroke="{p.c("teal-shade-50")}" stroke-width="28" stroke-linecap="round"/>'
            + person(p, 380, 380, 'teal', 'brown', 'black-tint-50', 1.0)
            + arm(p, 398, 270, 452, 300, 'teal', 22)
            + f'<rect x="452" y="282" width="22" height="38" rx="4" fill="{p.c("blue-shade-50")}"/>' + hand(p, 452, 304, 'brown', 0.8) + '</g>')
    items.append(figure('ill-move-line', p, 'Follow a line of movement: hurrying out of the front door',
                        'A person with grey hair strides towards an open front door, leaning forward with a phone in hand.',
                        body, 'Follow a line of movement', 'The forward lean and the long stride say the person is in a hurry.'))
    p = Picture('web')
    body = (room(p, 'white', 'blue-tint-80', 440)
            + window(p, 80, 80, 200, 200, 'blue-tint-50', 'white')
            + f'<path d="M80 70H140Q190 180 210 300H90Z" fill="{p.c("yellow")}"/>'
            + f'<rect x="500" y="110" width="170" height="330" fill="{p.c("blue-shade-25")}"/>'
            + f'<path d="M670 110L760 140V470L670 440Z" fill="{p.c("blue")}"/>'
            + person(p, 400, 440, 'blue-shade-50', 'brown-tint-25', 'brown', 1.15, 10, 1.2))
    items.append(figure('ill-move-details', p, 'Match the details: a draught through the open door',
                        'A person walks right towards an open door. The curtain at the window on the left blows to the right, the same way as the person and the door.',
                        body, 'Match the details', 'The curtain, the door and the person all move the same way, so the scene reads as one moment.'))
    return items


add('illustration-composition', 'Building a composition',
    'Three original scenes that show overlap, space and framing in a Home Assistant illustration.',
    grid(composition()), 'Show the 3 composition techniques: overlap, space and frame.')
add('illustration-detail', 'Adding detail',
    'Three original scenes that show how to protect the action, make a scene familiar and add context quietly.',
    grid(detail()), 'Show the 3 ways to add detail without hiding the action.')
add('illustration-movement', 'Showing movement',
    'Three original scenes that show a diagonal, a line of movement and matching details.',
    grid(movement()), 'Show the 3 ways to suggest movement in a still illustration.')


# ---------------------------------------------------------------------------
# Illustration: characters, hands and objects.
def people_items():
    items = []
    p = Picture('web')
    wheel = (f'<circle cx="150" cy="390" r="56" fill="none" stroke="{p.c("black-tint-25")}" stroke-width="12"/>'
             f'<rect x="110" y="300" width="100" height="24" fill="{p.c("black-tint-25")}"/>'
             f'<rect x="185" y="230" width="18" height="90" fill="{p.c("black-tint-25")}"/>')
    seated = (f'<rect x="115" y="210" width="72" height="110" rx="30" fill="{p.c("purple")}"/>'
              f'<rect x="130" y="300" width="100" height="28" rx="14" fill="{p.c("purple-shade-50")}"/>'
              f'<rect x="210" y="300" width="26" height="100" rx="13" fill="{p.c("purple-shade-50")}"/>'
              f'<circle cx="150" cy="180" r="28" fill="{p.c("brown")}"/>'
              f'<path d="M122 178a28 28 0 0 1 56 0q-28-14-56 0z" fill="{p.c("black")}"/>')
    stick = f'<path d="M402 260L420 446" stroke="{p.c("brown-tint-25")}" stroke-width="10" stroke-linecap="round"/>'
    body = (f'<rect width="800" height="500" fill="{p.c("blue-tint-95")}"/><rect y="446" width="800" height="54" fill="{p.c("blue-tint-80")}"/>'
            + wheel + seated
            + person(p, 350, 446, 'green', 'brown-tint-50', 'black-tint-80', 1.25, 0, 1.0)
            + stick + arm(p, 380, 280, 402, 262, 'green', 20)
            + person(p, 500, 446, 'yellow', 'brown-tint-25', 'brown', 0.8)
            + person(p, 650, 446, 'blue', 'orange-shade-50', 'blue-shade-50', 1.35, 0, 1.35, True))
    items.append(figure('ill-people-characters', p, 'Characters: 4 members of one household',
                        'Four people in a row: a person in a wheelchair, an older person with grey hair and a walking stick, a child, and a tall adult with a broad build wearing a headscarf. Their skin tones range from light to dark.',
                        body, 'Characters', 'Ages, skin tones, builds and disabilities vary, and no face has features.'))
    p = Picture('web')
    body = (f'<rect width="800" height="500" fill="{p.c("blue-tint-80")}"/>'
            f'<rect x="200" y="120" width="260" height="260" rx="20" fill="{p.c("white")}"/>'
            f'<rect x="250" y="170" width="160" height="160" rx="16" fill="{p.c("blue")}"/>'
            f'<circle cx="330" cy="250" r="30" fill="{p.c("blue-tint-95")}"/><circle cx="330" cy="250" r="12" fill="{p.c("teal-accent")}"/>'
            f'<rect x="330" y="232" width="200" height="36" rx="18" fill="{p.c("brown-tint-50")}"/>'
            f'<rect x="440" y="210" width="190" height="130" rx="60" fill="{p.c("brown-tint-50")}"/>'
            f'<rect x="470" y="268" width="120" height="30" rx="15" fill="{p.c("brown-tint-25")}"/>'
            f'<rect x="600" y="230" width="220" height="110" fill="{p.c("blue-shade-25")}"/>')
    items.append(figure('ill-people-hands', p, 'Hands: a finger on the button of a smart plug',
                        'A hand reaches in from the right. Its index finger points at and touches the button in the middle of a smart plug in a wall socket.',
                        body, 'Hands and gestures', 'The finger touches the right control, the plug button, and nothing else.'))
    p = Picture('web')
    body = (room(p, 'blue-tint-80', 'blue-tint-50', 420)
            + radiator(p, 90, 300, 260, 100, 'white', None)
            + window(p, 110, 60, 220, 200, 'blue-tint-95', 'white')
            + thermostat(p, 560, 200, 90, 'blue', 'white', 'teal-accent'))
    items.append(figure('ill-people-objects', p, 'Objects: a thermostat with only its dial and display',
                        'A hall wall with a window and a radiator under it. Beside them, a large round thermostat shows only its outer dial, its face and a display.',
                        body, 'Objects and props', 'The thermostat keeps its dial and display and loses its screws, buttons and logo.'))
    return items


add('illustration-people-objects', 'People, hands and objects',
    'Three original scenes: a varied household, a hand pressing a smart plug button, and a simplified thermostat.',
    grid(people_items()), 'Show inclusive characters, a correct gesture and a simplified device.')


# ---------------------------------------------------------------------------
# Icons and images: one illustration of a physical task, pressing and holding
# a door sensor's pairing button until its light flashes. Three equal panels
# of the same device in one SVG, so the set reads as one sequence. Used on the
# Illustrations page and, with its alt text, on the Alt text page. The same
# drawing is also written as a standalone SVG file, registered in
# docs/data/illustration-assets.json.
# The alt text is one sentence, in the SVG title. The steps are in the caption,
# so the alt text does not repeat them.
PAIRING_ALT = 'The pairing button is the round white button on the front of the door sensor, with a small light above it.'
PAIRING_STEPS = '1. Find the round pairing button. 2. Press and hold it. 3. Keep holding until the light above it flashes.'
PAIRING_FILE = 'docs/source/images/illustration-door-sensor-pairing.svg'


def pairing_body(p, tid):
    body = f'<rect width="960" height="400" fill="{p.c("white")}"/>'
    for n in range(3):
        ox = n * 330
        body += (f'<clipPath id="{tid}-clip-{n + 1}"><rect x="{ox}" width="300" height="400"/></clipPath>'
                 f'<rect x="{ox}" width="300" height="400" fill="{p.c("blue-tint-80")}"/>'
                 f'<circle cx="{ox + 40}" cy="40" r="24" fill="{p.c("blue")}"/>'
                 + p.text(ox + 40, 49, str(n + 1), 26, 'white', 'blue', 700, 'middle')
                 + f'<rect x="{ox + 90}" y="90" width="120" height="250" rx="24" fill="{p.c("blue")}"/>'
                 f'<circle cx="{ox + 150}" cy="260" r="30" fill="{p.c("white")}"/>')
        if n < 2:
            # Unlit: an unfilled ring in Blue tint 80%, visible on the Primary blue body.
            body += f'<circle cx="{ox + 150}" cy="160" r="12" fill="none" stroke="{p.c("blue-tint-80")}" stroke-width="4"/>'
        else:
            body += (f'<circle cx="{ox + 150}" cy="160" r="14" fill="{p.c("teal-accent")}"/>'
                     f'<path d="M{ox + 150} 136V116M{ox + 129} 145l-14-14M{ox + 171} 145l14-14M{ox + 124} 160h-18M{ox + 176} 160h18"'
                     f' stroke="{p.c("teal-accent")}" stroke-width="8" stroke-linecap="round"/>')
        if n > 0:
            body += (f'<g clip-path="url(#{tid}-clip-{n + 1})">'
                     f'<rect x="{ox + 150}" y="242" width="130" height="36" rx="18" fill="{p.c("brown")}"/>'
                     f'<rect x="{ox + 250}" y="214" width="120" height="110" rx="50" fill="{p.c("brown")}"/></g>')
    return body


def pairing_steps(tid='img-pairing', drawing_note=True):
    # drawing_note=False gives the caption for the Alt text page: the steps
    # only, as the text a dashboard would show beside the picture.
    p = Picture('web')
    body = pairing_body(p, tid)
    note = PAIRING_STEPS + (' The 3 pictures show the same device in the same colours.' if drawing_note else '')
    return figure(tid, p, PAIRING_ALT, '', body, 'Pairing a door sensor in 3 steps', note, 960, 400, colours=drawing_note)


def pairing_file():
    p = Picture('web')
    tid = 'door-sensor-pairing'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 400" role="img" aria-labelledby="{tid}-t" font-family="{FONT}">'
            f'<title id="{tid}-t">{escape(PAIRING_ALT)}</title>'
            f'{pairing_body(p, tid)}</svg>\n')


add('images-pairing-steps', 'Pairing a door sensor',
    'An original illustration in 3 steps: a fingertip presses and holds the pairing button on a door sensor until its light flashes.',
    '<div style="max-width:720px">' + pairing_steps() + '</div>',
    'Show a physical task as a short set of pictures of the same device, with the steps in text.', 420)
add('images-pairing-steps-alt', 'Pairing a door sensor, with its steps',
    'The door sensor pairing illustration with only its 3 steps under it, as a dashboard would show them beside the picture.',
    '<div style="max-width:720px">' + pairing_steps('img-pairing-alt', False) + '</div>',
    'Show an illustration with its steps in text beside it, so its alt text gives only what the picture shows.', 420)


# ---------------------------------------------------------------------------
# Illustration: things to avoid, as do and do-not pairs.
def avoid_pairs():
    items = []
    # 1. Flat colour, or gradients and outlines.
    for verdict in ('do', 'dont'):
        p = Picture('web')
        tid = f'ill-avoid-flat-{verdict}'
        if verdict == 'do':
            body = (room(p, 'blue-tint-80', 'blue-tint-50') + thermostat(p, 400, 220, 110, 'blue', 'white', 'teal-accent'))
            title, desc, cap, note = ('Flat thermostat', 'A round thermostat in flat Primary blue and White, with an Accent teal display, on a plain wall.',
                                      'use flat colour and simple shapes', 'Two circles and a rectangle in flat colour.')
        else:
            body = (f'<defs><radialGradient id="{tid}-g" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="{p.c("blue-tint-80")}"/><stop offset="1" stop-color="{p.c("blue-shade-50")}"/></radialGradient></defs>'
                    + room(p, 'blue-tint-80', 'blue-tint-50')
                    + f'<ellipse cx="420" cy="350" rx="120" ry="20" fill="{p.c("black-tint-50")}"/>'
                    + f'<circle cx="400" cy="220" r="110" fill="url(#{tid}-g)" stroke="{p.c("black")}" stroke-width="12"/>'
                    + f'<circle cx="400" cy="220" r="78" fill="{p.c("white")}" stroke="{p.c("black")}" stroke-width="8"/>'
                    + f'<rect x="358" y="200" width="84" height="40" fill="{p.c("teal-accent")}" stroke="{p.c("black")}" stroke-width="6"/>')
            title, desc, cap, note = ('Shaded thermostat', 'The same thermostat with a gradient, heavy black outlines and a drop shadow.',
                                      'add gradients, heavy outlines or shadows', 'The shading and outlines make it look like a different style.')
        items.append(figure(tid, p, title, desc, body, cap, note, verdict=verdict))
    # 2. One focal point, or a crowded scene.
    for verdict in ('do', 'dont'):
        p = Picture('web')
        tid = f'ill-avoid-focus-{verdict}'
        body = room(p, 'blue-tint-80', 'blue-tint-50') + sofa(p, 260, 310, 280, 'blue-tint-50', 'blue-tint-95')
        if verdict == 'do':
            body += sensor(p, 400, 170, 'blue', 'teal-accent', 64)
            title, desc, cap, note = ('One focal point', 'A living room with a sofa and one temperature sensor on the wall above it.',
                                      'keep one clear focal point', 'The sensor is the only strong shape on the wall.')
        else:
            body += (sensor(p, 400, 170, 'blue', 'teal-accent', 64)
                     + window(p, 60, 60, 150, 160, 'yellow', 'orange')
                     + f'<circle cx="640" cy="110" r="50" fill="{p.c("magenta")}"/><rect x="600" y="200" width="90" height="120" fill="{p.c("green")}"/>'
                     + f'<rect x="250" y="60" width="90" height="60" fill="{p.c("red")}"/><rect x="470" y="60" width="80" height="80" rx="40" fill="{p.c("orange")}"/>'
                     + f'<rect x="80" y="300" width="100" height="100" fill="{p.c("purple")}"/>')
            title, desc, cap, note = ('Crowded room', 'The same room filled with brightly coloured pictures, lamps and boxes, so the sensor is hard to find.',
                                      'fill the scene with objects that compete', 'The sensor is lost among bright shapes.')
        items.append(figure(tid, p, title, desc, body, cap, note, verdict=verdict))
    # 3. A neutral device, or a drawn state the picture cannot know.
    for verdict in ('do', 'dont'):
        p = Picture('web')
        tid = f'ill-avoid-state-{verdict}'
        body = (room(p, 'blue-tint-80', 'blue-tint-50')
                + f'<rect x="300" y="80" width="200" height="320" fill="{p.c("blue-shade-25")}"/><rect x="316" y="96" width="168" height="304" fill="{p.c("blue-tint-50")}"/>'
                + sensor(p, 530, 200, 'blue', 'blue', 44))
        if verdict == 'do':
            title, desc, cap, note = ('Neutral door sensor', 'A door with a sensor on its frame. The sensor has no status light.',
                                      'show a neutral scene', 'The text beside it says whether the door is open.')
        else:
            body += (f'<circle cx="610" cy="130" r="40" fill="{p.c("green")}"/>'
                     f'<path d="M592 130l13 13 24-26" fill="none" stroke="{p.c("white")}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>')
            title, desc, cap, note = ('Door sensor with a green tick', 'The same door and sensor with a large green tick beside it, as if the door were confirmed closed.',
                                      'draw a state the picture cannot know', 'A drawn tick looks like a real reading, but the drawing never changes.')
        items.append(figure(tid, p, title, desc, body, cap, note, verdict=verdict))
    # 4. Words beside the picture, or words inside it.
    for verdict in ('do', 'dont'):
        p = Picture('web')
        tid = f'ill-avoid-text-{verdict}'
        body = room(p, 'blue-tint-80', 'blue-tint-50') + thermostat(p, 400, 200, 100, 'blue', 'white', 'teal-accent')
        if verdict == 'do':
            title, desc, cap, note = ('Thermostat without words', 'A thermostat on a wall, with no words in the picture.',
                                      'put the instruction in text beside the picture', 'The instruction is in the caption and the page, where it can be read aloud and resized.')
        else:
            body += (f'<rect x="120" y="340" width="560" height="110" fill="{p.c("white")}"/>'
                     + p.text(400, 388, 'Turn the dial to 19 °C', 36, 'black', 'white', 700, 'middle')
                     + p.text(400, 428, 'and press to confirm', 28, 'black', 'white', 400, 'middle'))
            title, desc, cap, note = ('Thermostat with an instruction drawn in', 'The same thermostat with the words Turn the dial to 19 °C and press to confirm drawn into the picture.',
                                      'put words or values inside the image', 'Words in a picture cannot be resized, translated or read by every screen reader.')
        items.append(figure(tid, p, title, desc, body, cap, note, verdict=verdict))
    return items


add('illustration-do-dont', 'Things to avoid in an illustration',
    'Four pairs of original drawings, each a do and a do not: flat colour, one focal point, a neutral scene and words beside the picture.',
    grid(avoid_pairs(), 280, 680), 'Show what to do and what to avoid, as pairs of the same scene.', 1600)


# ---------------------------------------------------------------------------
# Icons and images: tiles with an icon, a name and a state.
def tile(p, x, y, name, state, icon_name, icon_colour, icon_bg, w=360):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="84" fill="{p.c("white")}" stroke="{p.c("black-tint-80")}" stroke-width="2"/>'
            f'<circle cx="{x + 44}" cy="{y + 42}" r="26" fill="{p.c(icon_bg)}"/>'
            + icon(p, icon_name, x + 44, y + 42, icon_colour, 30)
            + p.text(x + 88, y + 36, name, 20, 'black', 'white', 700)
            + p.text(x + 88, y + 64, state, 18, 'black-tint-25', 'white'))


def icon_examples():
    p = Picture('web')
    rows = [('Hallway lamp', 'On', 'bulb', 'yellow-shade-50', 'yellow-tint-80'),
            ('Front door', 'Closed', 'door', 'blue', 'blue-tint-80'),
            ('Back door', 'Open', 'door-open', 'blue', 'blue-tint-80'),
            ('Kitchen temperature', '19.5 °C', 'thermometer', 'blue', 'blue-tint-80'),
            ('Bathroom leak sensor', 'Leak detected', 'drop', 'red', 'red-tint-80'),
            ('Desk plug', 'Unavailable', 'plug', 'black-tint-25', 'black-tint-95')]
    cards = []
    for n, row in enumerate(rows):
        tid = f'img-icon-tile-{n + 1}'
        card = f'<rect width="400" height="104" fill="{p.c("blue-tint-95")}"/>' + tile(p, 10, 10, *row, w=380)
        cards.append(svg(tid, f'Tile card: {row[0]}, {row[1]}', f'A Tile card with a {ICON_WORDS[row[2]]} icon, the name {row[0]} and the state {row[1]}.', card, 400, 104))
    tid = 'img-icon-tiles'
    markup = ('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px">' + ''.join(cards) + '</div>')
    return (f'<figure style="margin:0;max-width:820px" aria-labelledby="{tid}-c">{markup}'
            f'<figcaption class="govuk-body-s" id="{tid}-c" style="margin-top:10px"><strong>Icons with a name and a state</strong>'
            f'<br>The open and closed doors keep different icons, the leak keeps its red, and every state is written out. Colours: {escape(p.names())}.</figcaption></figure>')


ICON_WORDS = {'bulb': 'bulb', 'door': 'closed door', 'door-open': 'open door', 'thermometer': 'thermometer', 'drop': 'red drop', 'plug': 'grey plug'}


add('images-icon-examples', 'Icons on a dashboard',
    'Six drawn Tile cards for an invented household, each with an icon, a name and a state.',
    lead('These cards are drawings for an invented household. The icons are drawn in the manner of Home Assistant icons; they are not the icons themselves.', icon_examples()),
    'Show device icons with their visible names and states.', 420)


def icon_pairs():
    items = []
    # 1. Name and state, or an icon alone.
    p = Picture('web')
    body = f'<rect width="400" height="160" fill="{p.c("blue-tint-95")}"/>' + tile(p, 20, 38, 'Hallway lamp', 'On', 'bulb', 'yellow-shade-50', 'yellow-tint-80')
    items.append(figure('img-pair-label-do', p, 'Lamp tile with its name and state', 'A Tile card with a bulb icon, the name Hallway lamp and the state On.',
                        body, 'show an icon with its name and state', 'People can tell which lamp it is and that it is on.', 400, 160, 'do'))
    p = Picture('web')
    body = (f'<rect width="400" height="160" fill="{p.c("blue-tint-95")}"/><rect x="20" y="38" width="84" height="84" fill="{p.c("white")}" stroke="{p.c("black-tint-80")}" stroke-width="2"/>'
            f'<circle cx="62" cy="80" r="26" fill="{p.c("yellow-tint-80")}"/>' + icon(p, 'bulb', 62, 80, 'yellow-shade-50', 30))
    items.append(figure('img-pair-label-dont', p, 'Lamp icon on its own', 'A card with only a bulb icon. There is no name and no state.',
                        body, 'show an icon on its own', 'A yellow bulb does not say which light it is, or whether it is on, off or unavailable.', 400, 160, 'dont'))
    # 2. Native state icons, or one shape for everything.
    p = Picture('web')
    body = (f'<rect width="400" height="160" fill="{p.c("blue-tint-95")}"/>'
            + ''.join(f'<circle cx="{70 + n * 130}" cy="80" r="40" fill="{p.c("blue-tint-80")}"/>' + icon(p, name, 70 + n * 130, 80, 'blue', 44)
                      for n, name in enumerate(['door', 'door-open', 'thermometer'])))
    items.append(figure('img-pair-native-do', p, 'Closed door, open door and thermometer icons', 'Three icons: a closed door, an open door and a thermometer, each a different shape.',
                        body, 'keep native and state icons', 'An open and a closed door look different even without colour.', 400, 160, 'do'))
    p = Picture('web')
    body = (f'<rect width="400" height="160" fill="{p.c("blue-tint-95")}"/>'
            + ''.join(f'<circle cx="{70 + n * 130}" cy="80" r="40" fill="{p.c("blue-tint-80")}"/>' + icon(p, 'circle', 70 + n * 130, 80, 'blue', 44) for n in range(3)))
    items.append(figure('img-pair-native-dont', p, 'Three identical dot icons', 'Three identical blue dots in place of the door and thermometer icons.',
                        body, 'replace every icon with one shape', 'The dashboard looks neat, but nobody can tell the devices apart.', 400, 160, 'dont'))
    # 3. One icon for one meaning, or one icon for 2 actions.
    p = Picture('web')
    body = (f'<rect width="400" height="160" fill="{p.c("blue-tint-95")}"/>'
            f'<rect x="20" y="50" width="360" height="60" fill="{p.c("white")}" stroke="{p.c("black")}" stroke-width="2"/>'
            + icon(p, 'search', 52, 80, 'black', 28) + p.text(80, 87, 'Search entities', 20, 'black-tint-25', 'white'))
    items.append(figure('img-pair-meaning-do', p, 'Search field with a magnifying glass', 'A search field with a magnifying glass icon and the hint Search entities.',
                        body, 'use one icon for one meaning', 'The magnifying glass only ever means search.', 400, 160, 'do'))
    p = Picture('web')
    body = (f'<rect width="400" height="160" fill="{p.c("blue-tint-95")}"/>'
            + ''.join(f'<rect x="{30 + n * 190}" y="40" width="150" height="80" fill="{p.c("white")}" stroke="{p.c("black-tint-80")}" stroke-width="2"/>'
                      + icon(p, 'search', 105 + n * 190, 80, 'black', 40) for n in range(2)))
    items.append(figure('img-pair-meaning-dont', p, 'Two buttons with the same magnifying glass', 'Two icon-only buttons with the same magnifying glass. One searches and the other zooms the camera image.',
                        body, 'use one icon for 2 actions', 'People cannot tell search from zoom.', 400, 160, 'dont'))
    # 4. Keep meaningful colour, or recolour to the theme.
    p = Picture('web')
    body = f'<rect width="400" height="160" fill="{p.c("blue-tint-95")}"/>' + tile(p, 20, 38, 'Bathroom leak', 'Leak detected', 'drop', 'red', 'red-tint-80')
    items.append(figure('img-pair-colour-do', p, 'Leak sensor tile in red', 'A Tile card for the bathroom leak sensor with a red drop icon and the state Leak detected.',
                        body, 'keep colours that carry meaning', 'The red warning colour and the words both say there is a leak.', 400, 160, 'do'))
    p = Picture('web')
    body = f'<rect width="400" height="160" fill="{p.c("blue-tint-95")}"/>' + tile(p, 20, 38, 'Bathroom leak', 'Leak detected', 'drop', 'blue', 'blue-tint-80')
    items.append(figure('img-pair-colour-dont', p, 'Leak sensor tile in the theme blue', 'The same Tile card with the drop icon recoloured to the theme blue.',
                        body, 'recolour every icon to the theme colour', 'The leak looks like any other reading at a glance.', 400, 160, 'dont'))
    return items


add('images-icon-do-dont', 'Choosing icons: do and do not',
    'Four pairs of drawn icons and Tile cards for an invented household, each a do and a do not.',
    grid(icon_pairs(), 280, 680), 'Show what to do and what to avoid when choosing icons.', 1200)


# ---------------------------------------------------------------------------
# Icons and images: a floor plan with sensors marked by shape and colour,
# and the same facts as a visible list.
def floor_plan():
    p = Picture('web')
    wall = p.c('black')
    rooms = [(40, 40, 320, 220, 'Living room', 'blue-tint-95'), (360, 40, 220, 220, 'Kitchen', 'white'),
             (40, 260, 200, 200, 'Bedroom', 'white'), (240, 260, 200, 200, 'Hall', 'blue-tint-95'), (440, 260, 140, 200, 'Bathroom', 'white')]
    body = f'<rect width="800" height="500" fill="{p.c("white")}"/>'
    for x, y, w, h, name, fill in rooms:
        body += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{p.c(fill)}" stroke="{wall}" stroke-width="8"/>'
    # Door gaps, drawn over the walls in the floor colour of the rooms.
    for x, y, w, h, fill in [(140, 256, 60, 8, 'white'), (420, 256, 60, 8, 'white'), (236, 360, 8, 60, 'white'), (436, 360, 8, 60, 'white'), (300, 456, 70, 8, 'blue-tint-95')]:
        body += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{p.c(fill)}"/>'
    for x, y, w, h, name, fill in rooms:
        body += p.text(x + 18, y + 36, name, 24, 'black', fill, 700)
    # Markers: circle temperature, square door contact, triangle motion, diamond leak.
    temp, door, motion, leak = 'blue', 'purple', 'teal-shade-25', 'red'
    body += f'<circle cx="300" cy="200" r="16" fill="{p.c(temp)}"/><circle cx="190" cy="410" r="16" fill="{p.c(temp)}"/>'
    body += f'<rect x="318" y="432" width="32" height="32" fill="{p.c(door)}"/>'
    body += f'<path d="M340 290l18 32h-36z" fill="{p.c(motion)}"/>'
    body += f'<path d="M520 410l18 18-18 18-18-18z" fill="{p.c(leak)}"/>'
    # Key, beside the plan.
    key = [('circle', temp, 'Temperature sensor'), ('square', door, 'Door contact'), ('triangle', motion, 'Motion sensor'), ('diamond', leak, 'Leak sensor')]
    body += p.text(610, 70, 'Key', 20, 'black', 'white', 700)
    for n, (shape, colour, label) in enumerate(key):
        y = 110 + n * 50
        hexv = p.c(colour)
        mark = {'circle': f'<circle cx="626" cy="{y}" r="13" fill="{hexv}"/>',
                'square': f'<rect x="613" y="{y - 13}" width="26" height="26" fill="{hexv}"/>',
                'triangle': f'<path d="M626 {y - 14}l15 27h-30z" fill="{hexv}"/>',
                'diamond': f'<path d="M626 {y - 15}l15 15-15 15-15-15z" fill="{hexv}"/>'}[shape]
        body += mark + p.text(648, y + 6, label, 16, 'black', 'white')
    desc = ('Floor plan of an invented flat with 5 rooms: living room and kitchen across the top; bedroom, hall and bathroom along the bottom. '
            'Temperature sensors in the living room and the bedroom, a door contact on the front door in the hall, a motion sensor in the hall and a leak sensor in the bathroom. '
            'A key on the right gives each sensor its own shape.')
    listing = ('<p class="govuk-body" style="margin:20px 0 5px"><strong>Sensors in the flat</strong></p><ul class="govuk-list govuk-list--bullet">'
               '<li>Living room: temperature sensor</li><li>Bedroom: temperature sensor</li>'
               '<li>Hall: door contact on the front door, and a motion sensor</li><li>Bathroom: leak sensor</li><li>Kitchen: no sensors</li></ul>')
    return figure('img-floor-plan', p, 'Floor plan of the Patel household flat', desc, body, 'A floor plan with its sensors listed in text',
                  'Each sensor type has its own shape as well as its own colour, the room names are part of the drawing so they stay sharp, and the list under the plan gives the same facts as a Markdown card would.',
                  extra=listing)


add('images-floor-plan', 'A floor plan with a text alternative',
    'A drawn floor plan of an invented flat, with its sensors marked by shape and colour and listed in text below.',
    lead('This plan is a drawing of an invented household, the Patels. It is not a real home.', floor_plan()),
    'Show a floor plan whose meaning is also given in visible text.', 820)


# ---------------------------------------------------------------------------
# Layout: the same dashboard at mobile, tablet and wall panel widths.
SECTIONS = [('Alerts', 2), ('Heating', 3), ('Lights', 3), ('Energy', 2)]


def section_block(p, x, y, w, name, cards, full=False):
    h = 48 + cards * 44
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{p.c("blue-tint-80")}"/>'
           + p.text(x + 14, y + 30, name, 18, 'black', 'blue-tint-80', 700))
    for n in range(cards):
        if full and n:
            continue
        out += f'<rect x="{x + 12}" y="{y + 44 + n * 44}" width="{w - 24}" height="34" fill="{p.c("white")}"/>'
    if full:
        out += f'<rect x="{x + 12}" y="{y + 88}" width="{w - 24}" height="{h - 100}" fill="{p.c("white")}"/>'
    return out, h


def screens():
    items = []
    # Mobile: one column.
    p = Picture('web')
    body = (f'<rect width="360" height="900" rx="40" fill="{p.c("black")}"/><rect x="12" y="12" width="336" height="876" rx="30" fill="{p.c("white")}"/>'
            f'<rect x="12" y="12" width="336" height="80" fill="{p.c("blue")}"/>' + p.text(36, 66, 'Home', 20, 'white', 'blue', 700))
    y = 108
    for name, cards in SECTIONS:
        block, h = section_block(p, 28, y, 304, name, cards)
        body += block
        y += h + 24
    items.append(figure('layout-mobile', p, 'Mobile layout: 4 sections in one column',
                        'A phone showing the Home dashboard. The sections Alerts, Heating, Lights and Energy are stacked one under another, each the full width of the screen.',
                        body, 'Mobile, under 768px', 'One column. Alerts is first, and the sections stack.', 360, 900))
    # Tablet: two columns.
    p = Picture('web')
    body = (f'<rect width="640" height="900" rx="36" fill="{p.c("black")}"/><rect x="20" y="20" width="600" height="860" rx="16" fill="{p.c("white")}"/>'
            f'<rect x="20" y="20" width="600" height="70" fill="{p.c("blue")}"/>' + p.text(44, 66, 'Home', 20, 'white', 'blue', 700))
    col = (600 - 32 - 32 - 32) / 2
    y = 116
    for row in (SECTIONS[:2], SECTIONS[2:]):
        heights = []
        for n, (name, cards) in enumerate(row):
            block, h = section_block(p, 52 + n * (col + 32), y, col, name, cards)
            body += block
            heights.append(h)
        y += max(heights) + 24
    items.append(figure('layout-tablet', p, 'Tablet layout: 2 sections side by side',
                        'A tablet held upright showing the Home dashboard. Alerts and Heating are side by side in the first row, and Lights and Energy in the second.',
                        body, 'Tablet, 768px to 1023px', 'Two columns. Alerts and Heating come first.', 640, 900))
    # Wall panel: three columns, Energy across the full width.
    p = Picture('web')
    body = (f'<rect width="1000" height="640" rx="24" fill="{p.c("black")}"/><rect x="24" y="24" width="952" height="592" fill="{p.c("white")}"/>'
            f'<rect x="24" y="24" width="952" height="70" fill="{p.c("blue")}"/>' + p.text(52, 70, 'Home', 20, 'white', 'blue', 700))
    col = (952 - 64 - 64) / 3
    heights = []
    for n, (name, cards) in enumerate(SECTIONS[:3]):
        block, h = section_block(p, 56 + n * (col + 32), 120, col, name, cards)
        body += block
        heights.append(h)
    block, h = section_block(p, 56, 120 + max(heights) + 24, 952 - 64, 'Energy', 3, True)
    body += block
    items.append(figure('layout-wall', p, 'Wall panel layout: 3 sections in a row, Energy below',
                        'A wall panel in landscape showing the Home dashboard. Alerts, Heating and Lights are side by side in one row, and Energy spans the full width below them.',
                        body, 'Wall panel, 1024px and over', 'Three columns. Energy spans the width below, so its graph has room.', 1000, 640))
    return items


scr = screens()
layout_html = (f'<div style="display:flex;flex-wrap:wrap;gap:30px 40px;align-items:flex-end;max-width:720px">'
               f'<div style="flex:0 1 200px">{scr[0]}</div><div style="flex:0 1 356px">{scr[1]}</div></div>'
               f'<div style="max-width:720px;margin-top:30px">{scr[2]}</div>')
add('layout-screen-sizes', 'One dashboard at 3 screen sizes',
    'Diagrams of the same invented household dashboard on a phone, a tablet and a wall panel, with the sections in the same order.',
    lead('These are diagrams of an invented household dashboard, not screenshots.', layout_html),
    'Show the section order of one dashboard at mobile, tablet and wall panel widths.', 1500)


# Layout: the 12-column grid inside a section, drawn to scale (a 500px section).
def section_grid():
    p = Picture('web')
    s = 1.0
    col, gap, row = (500 - 11 * 8) / 12 * s, 8 * s, 56 * s
    x0, y0 = 30, 50
    width = 500 * s
    body = f'<rect width="560" height="400" fill="{p.c("white")}"/>'
    for n in range(12):
        x = x0 + n * (col + gap)
        body += f'<rect x="{x:.1f}" y="{y0 - 10}" width="{col:.1f}" height="{4 * row + 3 * gap + 20:.1f}" fill="{p.c("blue-tint-95")}"/>'
        body += p.text(round(x + col / 2, 1), y0 - 20, str(n + 1), 16, 'black-tint-25', 'white', 400, 'middle')
    layout = [[(12, 'Heading: 12')], [(6, 'Tile: 6'), (6, 'Tile: 6')], [(4, '4'), (4, '4'), (4, '4')], [(3, '3'), (3, '3'), (3, '3'), (3, '3')]]
    fills = ['blue-shade-25', 'blue', 'blue-tint-25', 'blue-tint-50']
    inks = ['white', 'white', 'black', 'black']
    for r, cards in enumerate(layout):
        y = y0 + r * (row + gap)
        start = 0
        for span, label in cards:
            x = x0 + start * (col + gap)
            w = span * col + (span - 1) * gap
            body += f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{row:.1f}" fill="{p.c(fills[r])}"/>'
            body += p.text(round(x + w / 2, 1), round(y + row / 2 + 7, 1), label, 20, inks[r], fills[r], 700, 'middle')
            start += span
    by = y0 + 4 * row + 3 * gap + 50
    body += f'<path d="M{x0} {by:.1f}h{width:.1f}M{x0} {by - 10:.1f}v20M{x0 + width:.1f} {by - 10:.1f}v20" stroke="{p.c("black")}" stroke-width="2"/>'
    body += p.text(x0 + width / 2, round(by + 30, 1), '500px section', 18, 'black', 'white', 700, 'middle')
    return figure('layout-grid', p, 'The 12-column grid inside a section',
                  'A section drawn to scale at 500px wide, with its 12 numbered columns shaded behind 4 rows of cards: a heading across all 12 columns, 2 Tile cards of 6 columns, 3 cards of 4 columns and 4 cards of 3 columns.',
                  body, 'Card widths in a 12-column section', 'Each row adds up to 12 columns. The section is drawn to scale at its widest, 500px, with 56px rows and 8px gaps.', 560, 400)


add('layout-section-grid', 'The 12-column section grid',
    'A to-scale diagram of a Home Assistant section, with cards of 12, 6, 4 and 3 columns.',
    '<div style="max-width:600px">' + section_grid() + '</div>', 'Show how card widths fill the 12-column grid of a section.', 620)


# Layout: the Civica spacing scale, as bars drawn at 4 times their size.
def spacing_scale():
    p = Picture('web')
    steps = [(1, 5), (2, 10), (3, 15), (4, 20), (5, 25), (6, 30), (7, 40), (8, 50), (9, 60)]
    h = 40 + len(steps) * 48
    body = f'<rect width="460" height="{h}" fill="{p.c("white")}"/>'
    body += p.text(30, 30, 'Unit', 16, 'black-tint-25', 'white', 700) + p.text(110, 30, 'Value', 16, 'black-tint-25', 'white', 700)
    for n, (unit, px) in enumerate(steps):
        y = 50 + n * 48
        body += p.text(30, y + 22, str(unit), 18, 'black', 'white', 700)
        body += p.text(110, y + 22, f'{px}px', 18, 'black', 'white')
        body += f'<rect x="200" y="{y}" width="{px * 4}" height="30" fill="{p.c("blue")}"/>'
    return figure('layout-spacing', p, 'The Civica spacing scale',
                  'Nine bars, one for each unit of the spacing scale, growing from 5px for unit 1 to 60px for unit 9. Each bar is drawn at 4 times its size.',
                  body, 'Spacing units 1 to 9', 'The bars are drawn at 4 times their real size, so that the small steps are visible. Every value is a multiple of 5px.', 460, h)


add('layout-spacing-scale', 'The Civica spacing scale',
    'Bars that compare the 9 units of the Civica spacing scale.',
    '<div style="max-width:460px">' + spacing_scale() + '</div>', 'Show the relative size of each step of the spacing scale.', 560)


class Literal(str):
    pass


yaml.add_representer(Literal, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|'))
for ex in examples.values():
    ex['html'] = Literal(ex['html'].replace('><', '>\n<') + '\n')
TARGET = 'docs/data/style-visual-examples.yml'
text = ('# Generated by docs/scripts/generate-style-visuals.py from docs/data/govuk-brand-colours.json.\n'
        '# Edit the script and run it again rather than editing this file.\n'
        + yaml.dump({'examples': examples}, sort_keys=False, allow_unicode=True, width=10000))
OUTPUTS = {TARGET: text, PAIRING_FILE: pairing_file()}
if '--check' in sys.argv:
    for path, content in OUTPUTS.items():
        with open(path, encoding='utf-8') as current:
            if current.read() != content:
                sys.exit(f'{path} is out of date. Run python3 docs/scripts/generate-style-visuals.py.')
    print('Style visual examples are current.')
else:
    for path, content in OUTPUTS.items():
        with open(path, 'w', encoding='utf-8') as out:
            out.write(content)
    print('written', ', '.join(examples), 'and', PAIRING_FILE)
