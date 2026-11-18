#!/usr/bin/env python3
"""Generate docs/data/web-app-colour-examples.yml: a civica Home Assistant
dashboard in a desktop browser (web palette), and the Home Assistant Companion
app header and example screens (app palette), composed like the GOV.UK Brand
Guidelines web and app colour page pictures.
Run from the repository root: python3 docs/scripts/generate-web-app-examples.py
Pass --check to fail if the YAML differs from what this script writes.
Every colour comes from docs/data/govuk-brand-colours.json by its ID. The script
stops if a picture uses a colour outside its palette, or if any text in a
picture is below 4.5:1 against the colour behind it."""
import json
import sys
from html import escape

import yaml

DATA = json.load(open('docs/data/govuk-brand-colours.json'))
C = DATA['colours']
PALETTES = {page: {i for group in DATA['pages'][page]['palette'] for i in group['colours']} for page in ('web', 'app')}
FONT = 'Arial,Helvetica,sans-serif'


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


def svg(tid, title, desc, body, width=960, height=640):
    return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="{tid}-t {tid}-d" style="display:block;width:100%;height:auto;font-family:{FONT}">'
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


# Small icons, drawn in one colour with simple shapes.
def chevron(p, x, y, colour, size=8, width=2.5):
    return f'<path d="M{x} {y - size}l{size} {size}-{size} {size}" fill="none" stroke="{p.c(colour)}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'


def back(p, x, y, colour, size=10):
    return f'<path d="M{x + size} {y - size}l-{size} {size} {size} {size}" fill="none" stroke="{p.c(colour)}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'


def external(p, x, y, colour):
    return f'<path d="M{x} {y}l12-12M{x + 3} {y - 12}h9v9" fill="none" stroke="{p.c(colour)}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'


def search_icon(p, x, y, colour, r=7):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{p.c(colour)}" stroke-width="2.5"/>'
            f'<path d="M{x + r * 0.7:.1f} {y + r * 0.7:.1f}l{r * 0.8:.1f} {r * 0.8:.1f}" stroke="{p.c(colour)}" stroke-width="2.5" stroke-linecap="round"/>')


def status_icons(p, right, y, colour):
    ink = p.c(colour)
    bars = ''.join(f'<rect x="{right - 66 + n * 5}" y="{y - 3 - n * 3}" width="3" height="{3 + n * 3}" fill="{ink}"/>' for n in range(4))
    wifi = f'<path d="M{right - 41} {y - 7}a9 9 0 0 1 14 0M{right - 38} {y - 3}a5 5 0 0 1 8 0" fill="none" stroke="{ink}" stroke-width="2.2" stroke-linecap="round"/><circle cx="{right - 34}" cy="{y}" r="1.6" fill="{ink}"/>'
    battery = f'<rect x="{right - 22}" y="{y - 10}" width="20" height="11" rx="3" fill="none" stroke="{ink}" stroke-width="1.5"/><rect x="{right - 20}" y="{y - 8}" width="14" height="7" rx="1.5" fill="{ink}"/>'
    return bars + wifi + battery


def thermometer(p, x, y, colour):
    ink = p.c(colour)
    return (f'<rect x="{x - 4}" y="{y - 22}" width="8" height="24" rx="4" fill="none" stroke="{ink}" stroke-width="2.5"/>'
            f'<circle cx="{x}" cy="{y + 6}" r="7" fill="{ink}"/><rect x="{x - 1.5}" y="{y - 12}" width="3" height="14" fill="{ink}"/>')


def bulb(p, x, y, colour):
    ink = p.c(colour)
    return (f'<circle cx="{x}" cy="{y - 6}" r="11" fill="{ink}"/><rect x="{x - 6}" y="{y + 4}" width="12" height="6" fill="{ink}"/>'
            f'<rect x="{x - 4}" y="{y + 12}" width="8" height="3" rx="1.5" fill="{ink}"/>')


def bolt(p, x, y, colour):
    return f'<path d="M{x + 3} {y - 18}l-13 20h9l-4 16 13-20h-9z" fill="{p.c(colour)}"/>'


def lock(p, x, y, colour, k=1):
    ink = p.c(colour)
    return (f'<path d="M{x - 7 * k:g} {y - 4 * k:g}v{-6 * k:g}a{7 * k:g} {7 * k:g} 0 0 1 {14 * k:g} 0v{6 * k:g}" fill="none" stroke="{ink}" stroke-width="{2.5 * k:g}"/>'
            f'<rect x="{x - 10 * k:g}" y="{y - 4 * k:g}" width="{20 * k:g}" height="{16 * k:g}" rx="2" fill="{ink}"/>')


def sofa(p, x, y, colour):
    ink = p.c(colour)
    return (f'<rect x="{x - 12}" y="{y - 10}" width="24" height="10" rx="3" fill="{ink}"/>'
            f'<rect x="{x - 16}" y="{y - 3}" width="32" height="10" rx="3" fill="{ink}"/>'
            f'<rect x="{x - 14}" y="{y + 7}" width="3" height="4" fill="{ink}"/><rect x="{x + 11}" y="{y + 7}" width="3" height="4" fill="{ink}"/>')


def pan(p, x, y, colour):
    ink = p.c(colour)
    return (f'<path d="M{x - 13} {y - 6}h26v8a8 8 0 0 1-8 8h-10a8 8 0 0 1-8-8z" fill="{ink}"/>'
            f'<rect x="{x - 17}" y="{y - 9}" width="34" height="3" rx="1.5" fill="{ink}"/><rect x="{x - 3}" y="{y - 13}" width="6" height="3" rx="1.5" fill="{ink}"/>')


def tree(p, x, y, colour):
    ink = p.c(colour)
    return f'<circle cx="{x}" cy="{y - 6}" r="11" fill="{ink}"/><rect x="{x - 2}" y="{y}" width="4" height="12" fill="{ink}"/>'


def bed(p, x, y, colour):
    ink = p.c(colour)
    return (f'<rect x="{x - 16}" y="{y - 12}" width="4" height="22" fill="{ink}"/><rect x="{x - 12}" y="{y}" width="28" height="6" fill="{ink}"/>'
            f'<rect x="{x - 10}" y="{y - 7}" width="9" height="6" rx="2" fill="{ink}"/><rect x="{x + 12}" y="{y + 6}" width="4" height="4" fill="{ink}"/>')


def history(p, x, y, colour):
    ink = p.c(colour)
    return (f'<path d="M{x - 11} {y + 4}a12 12 0 1 0 1-9" fill="none" stroke="{ink}" stroke-width="2.5" stroke-linecap="round"/>'
            f'<path d="M{x - 14} {y - 9}l3 5 5-3" fill="none" stroke="{ink}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M{x} {y - 6}v7l5 3" fill="none" stroke="{ink}" stroke-width="2.5" stroke-linecap="round"/>')


def home(p, x, y, colour):
    return f'<path d="M{x - 10} {y + 9}v-10l10-8 10 8v10z" fill="none" stroke="{p.c(colour)}" stroke-width="2.2" stroke-linejoin="round"/>'


def cog(p, x, y, colour):
    ink = p.c(colour)
    teeth = ''.join(f'<rect x="{x - 2}" y="{y - 11}" width="4" height="5" fill="{ink}" transform="rotate({n * 45} {x} {y})"/>' for n in range(8))
    return teeth + f'<circle cx="{x}" cy="{y}" r="7" fill="none" stroke="{ink}" stroke-width="2.5"/>'


def bars(p, x, y, widths, colour, height=10, gap=22):
    """Greyed-out text: rounded bars in a Black tint, one per line."""
    return ''.join(f'<rect x="{x}" y="{y + n * gap}" width="{w}" height="{height}" rx="{height / 2}" fill="{p.c(colour)}"/>' for n, w in enumerate(widths) if w)


def grey_card(p, x, y, w, h, lines):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{p.c("black-tint-95")}"/>'
            + bars(p, x + 16, y + 18, lines, 'black-tint-80'))


def phone(p, tid, x, y, w, h, inner):
    """A phone outline in Black tint 50%; its screen is clipped to the outline."""
    return (f'<defs><clipPath id="{tid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="36"/></clipPath></defs>'
            f'<g clip-path="url(#{tid})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{p.c("white")}"/>{inner}</g>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="36" fill="none" stroke="{p.c("black-tint-50")}" stroke-width="3"/>')


examples = {}

# 1. Web palette example: a drawing of a dashboard in a desktop browser.
p = Picture(PALETTES['web'])
body = (f'<rect width="960" height="640" fill="{p.c("blue-tint-50")}"/>'
        f'<rect x="80" y="60" width="800" height="520" rx="10" fill="{p.c("white")}"/>'
        # Browser chrome: tab strip, tab and address bar.
        f'<path d="M80 100v-30a10 10 0 0 1 10-10h780a10 10 0 0 1 10 10v30z" fill="{p.c("black-tint-95")}"/>'
        f'<circle cx="102" cy="80" r="6" fill="{p.c("black-tint-80")}"/><circle cx="122" cy="80" r="6" fill="{p.c("black-tint-80")}"/><circle cx="142" cy="80" r="6" fill="{p.c("black-tint-80")}"/>'
        f'<path d="M165 100v-26a6 6 0 0 1 6-6h208a6 6 0 0 1 6 6v26z" fill="{p.c("white")}"/>'
        f'<rect x="177" y="76" width="16" height="16" rx="3" fill="{p.c("blue")}"/>'
        + p.text(201, 89, 'Overview – Morgan household', 13, 'black-tint-25', 'white')
        + f'<path d="M106 118h-12m5-5-5 5 5 5M118 118h12m-5-5 5 5-5 5" fill="none" stroke="{p.c("black-tint-25")}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
        + f'<rect x="150" y="106" width="715" height="24" rx="12" fill="{p.c("black-tint-95")}"/>'
        + p.text(166, 123, 'home.morgan.example', 13, 'black-tint-25', 'black-tint-95')
        # Primary blue header with the household name.
        + f'<rect x="80" y="136" width="800" height="62" fill="{p.c("blue")}"/>'
        + p.text(120, 175, 'Morgan household', 24, 'white', 'blue', 700)
        + p.text(752, 172, 'Menu', 15, 'white', 'blue', 700)
        + f'<path d="M735 161l5 5 5-5" fill="none" stroke="{p.c("white")}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        + f'<rect x="803" y="152" width="1" height="30" fill="{p.c("white")}"/>' + search_icon(p, 830, 165, 'white')
        # Navigation.
        + f'<rect x="80" y="198" width="800" height="42" fill="{p.c("white")}"/><rect x="80" y="239" width="800" height="1" fill="{p.c("black-tint-80")}"/>'
        + p.text(120, 224, 'Overview', 15, 'blue-shade-10', 'white', 700) + f'<rect x="120" y="234" width="66" height="5" fill="{p.c("blue")}"/>'
        + ''.join(p.text(x, 224, label, 15, 'blue-shade-10', 'white') for x, label in [(212, 'Energy'), (285, 'Map'), (338, 'Logbook'), (420, 'History'), (497, 'Settings')])
        # Content on the template background.
        + f'<rect x="80" y="240" width="800" height="340" fill="{p.c("blue-tint-95")}"/>'
        + p.text(120, 282, 'Overview', 26, 'black', 'blue-tint-95', 700)
        + p.text(120, 306, 'Good evening. Everyone is home.', 15, 'black-tint-25', 'blue-tint-95'))
cards = [(120, 'Living room'), (363, 'Kitchen light'), (606, 'Energy today')]
for x, _ in cards:
    body += f'<rect x="{x}" y="326" width="233" height="140" rx="4" fill="{p.c("white")}" stroke="{p.c("black-tint-80")}"/>'
body += (thermometer(p, 146, 358, 'blue') + p.text(164, 363, 'Living room', 15, 'black', 'white', 700)
         + p.text(136, 412, '21.5 °C', 32, 'black', 'white', 700)
         + p.text(136, 444, 'Heating on until 22:00', 13, 'black-tint-25', 'white'))
body += (bulb(p, 388, 360, 'blue') + p.text(410, 363, 'Kitchen light', 15, 'black', 'white', 700)
         + p.text(379, 412, 'On', 32, 'black', 'white', 700)
         + f'<rect x="530" y="388" width="44" height="24" rx="12" fill="{p.c("blue")}"/><circle cx="562" cy="400" r="9" fill="{p.c("white")}"/>'
         + p.text(379, 444, 'Brightness 80%', 13, 'black-tint-25', 'white'))
body += (bolt(p, 630, 360, 'blue') + p.text(650, 363, 'Energy today', 15, 'black', 'white', 700)
         + p.text(622, 412, '7.8 kWh', 32, 'black', 'white', 700)
         + p.text(622, 444, 'Solar 3.1 kWh, grid 4.7 kWh', 13, 'black-tint-25', 'white'))
body += (f'<rect x="120" y="482" width="719" height="70" rx="4" fill="{p.c("white")}" stroke="{p.c("black-tint-80")}"/>'
         + lock(p, 146, 516, 'blue') + p.text(170, 514, 'Front door', 15, 'black', 'white', 700)
         + p.text(170, 535, 'Locked at 18:42', 13, 'black-tint-25', 'white')
         + p.text(818, 522, 'View logbook', 15, 'blue-shade-10', 'white', anchor='end')
         + f'<rect x="725" y="526" width="93" height="1.5" fill="{p.c("blue-shade-10")}"/>')
web_desc = ('A desktop browser on a Blue tint 50% background shows a dashboard for the Morgan household. '
            'The header is Primary blue with “Morgan household”, Menu and a search icon in White. Below it, a White navigation bar has Overview, Energy, Map, Logbook, History and Settings links in Blue shade 10%, with a Primary blue line under Overview. '
            'On a Blue tint 95% background are an Overview heading and White cards with Black tint 80% borders: Living room 21.5 °C, Kitchen light On with a Primary blue switch, Energy today 7.8 kWh, and Front door Locked with a View logbook link. '
            'The text is Black, with secondary text in Black tint 25%.')
web = figure('web-dashboard', svg('web-dashboard', 'Web palette example: a dashboard in a desktop browser', web_desc, body),
             'A drawing of a dashboard: the household, its web address, rooms and readings are invented.', p,
             ['blue', 'white', 'blue-shade-10', 'black-tint-80', 'black', 'black-tint-25'])
examples['web-colour-dashboard'] = {
    'title': 'A dashboard in the web palette',
    'description': 'A Home Assistant dashboard in a desktop browser, drawn in web palette colours: a Primary blue header, links in the link colour and White cards with quiet borders.',
    'height': 760,
    'html': '<section aria-labelledby="web-dashboard-h"><h2 class="govuk-heading-m" id="web-dashboard-h">Web palette example</h2>' + block('A Home Assistant dashboard in a desktop browser. Copy the Primary blue header with White text, links in Blue shade 10%, White cards with Black tint 80% borders, and Black text with secondary text in Black tint 25%. The Blue tint 95% page background and the Menu button are for web pages: civica dashboards keep a White background and Home Assistant’s own navigation.', [web]) + '</section>',
}

# 2. Mobile web header: the dashboard in a mobile browser, content greyed out.
p = Picture(PALETTES['app'])
inner = (p.text(312, 160, '9:41', 17, 'black', 'white', 700) + status_icons(p, 650, 160, 'black')
         + f'<rect x="292" y="180" width="376" height="40" rx="20" fill="{p.c("black-tint-95")}"/>'
         + lock(p, 400, 199, 'black', 0.7)
         + p.text(418, 207, 'home.morgan.example', 18, 'black', 'black-tint-95')
         + f'<rect x="280" y="232" width="400" height="64" fill="{p.c("blue")}"/>'
         + p.text(296, 272, 'Morgan household', 24, 'white', 'blue', 700)
         + f'<path d="M541 259l6 6 6-6" fill="none" stroke="{p.c("white")}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
         + p.text(562, 270, 'Menu', 17, 'white', 'blue', 700)
         + f'<rect x="626" y="250" width="1" height="28" fill="{p.c("white")}"/>' + search_icon(p, 652, 263, 'white')
         + bars(p, 293, 318, [44], 'black-tint-80', 8) + bars(p, 352, 318, [110], 'black-tint-80', 8)
         + bars(p, 293, 372, [300, 190], 'black-tint-80', 24, 40)
         + bars(p, 293, 470, [90], 'black-tint-80', 12)
         + ''.join(bars(p, 293, y, [18], 'black-tint-80', 3) + bars(p, 338, y - 5, [w], 'black-tint-80', 12) for y, w in [(541, 110), (577, 130), (613, 260)]))
body = f'<rect width="960" height="640" fill="{p.c("white")}"/>' + phone(p, 'mobile-web-clip', 280, 128, 400, 620, inner)
mobile_desc = ('A phone shows a dashboard in a mobile browser, with the address home.morgan.example. The header is Primary blue with “Morgan household”, Menu and a search icon in White. '
               'The page content below the header is greyed out as Black tint 80% bars, so that only the header is in colour.')
mobile = figure('mobile-web', svg('mobile-web', 'Mobile web header: a dashboard on a phone', mobile_desc, body),
                'A drawing of a phone browser: the household name and web address are invented.', p, ['blue', 'white'])
examples['app-colour-mobile-web-header'] = {
    'title': 'The Primary blue header on the mobile web',
    'description': 'A dashboard in a mobile browser: the Primary blue header with the household name in White, and the page content greyed out.',
    'height': 760,
    'html': '<section aria-labelledby="mobile-web-h"><h2 class="govuk-heading-m" id="mobile-web-h">Mobile web header</h2>' + block('A Home Assistant dashboard in a phone browser, with the page content greyed out so that the header stands out. Notice that the Primary blue header keeps the household name in White, as on a desktop.', [mobile]) + '</section>',
}


# 3. App header: 4 Companion app screens, 2 to a picture, content greyed out.
def app_screen(p, tid, x, kind):
    w = 400
    inner = status_icons(p, x + w - 26, 152, 'white')
    if kind == 'home':
        inner = (f'<rect x="{x}" y="128" width="{w}" height="192" fill="{p.c("blue")}"/>' + inner
                 + p.text(x + w / 2, 218, 'Morgan household', 34, 'white', 'blue', 700, 'middle')
                 + f'<rect x="{x + 14}" y="264" width="{w - 28}" height="40" rx="10" fill="{p.c("white")}"/>'
                 + search_icon(p, x + 36, 283, 'black-tint-25') + p.text(x + 54, 291, 'Search', 18, 'black-tint-25', 'white')
                 + grey_card(p, x + 14, 338, w - 28, 72, [210])
                 + bars(p, x + 14, 448, [110], 'black-tint-80', 14)
                 + grey_card(p, x + 14, 478, 178, 140, [40, 0, 0, 100]) + grey_card(p, x + 208, 478, 178, 140, [40, 0, 0, 120]))
    else:
        title, left, right = kind
        inner = (f'<rect x="{x}" y="128" width="{w}" height="152" fill="{p.c("blue")}"/>' + inner
                 + (back(p, x + 12, 200, 'white') + p.text(x + 32, 207, left, 18, 'white', 'blue') if left else '')
                 + (p.text(x + w - 18, 207, right, 18, 'white', 'blue', anchor='end') if right else '')
                 + p.text(x + 16, 262, title, 36, 'white', 'blue', 700)
                 + bars(p, x + 16, 300, [280], 'black-tint-80', 10)
                 + grey_card(p, x + 14, 330, w - 28, 66, [170, 120])
                 + grey_card(p, x + 14, 410, w - 28, 66, [220, 90])
                 + grey_card(p, x + 14, 490, w - 28, 66, [190, 140])
                 + grey_card(p, x + 14, 570, w - 28, 66, [150]))
    return phone(p, tid, x, 128, w, 620, inner)


header_figures = []
for tid, screens, caption, desc in [
    ('app-header-1', [('home'), (('Living room', 'Home', None))], 'A simplified drawing of app screens, not the Companion app’s own layout: the household and room names are invented.',
     'Two app screens, Home and Living room, with a Primary blue header. The Home screen shows “Morgan household” in White above a White search field. '
     'The Living room screen has a White back link to Home and the title “Living room” in White. The content below each header is greyed out in Black tint 95% and Black tint 80%.'),
    ('app-header-2', [(('Energy', 'Home', 'Edit')), (('Settings', None, None))], 'Energy and Settings screens.',
     'Two app screens, Energy and Settings, with a Primary blue header. The Energy screen has a White back link to Home, an Edit link and the title “Energy” in White. '
     'The Settings screen has the title “Settings” in White. The content below each header is greyed out in Black tint 95% and Black tint 80%.'),
]:
    p = Picture(PALETTES['app'])
    body = f'<rect width="960" height="640" fill="{p.c("white")}"/>' + app_screen(p, f'{tid}-a', 65, screens[0]) + app_screen(p, f'{tid}-b', 495, screens[1])
    names = 'Home and Living room screens' if tid == 'app-header-1' else 'Energy and Settings screens'
    header_figures.append(figure(tid, svg(tid, f'App header: {names}', desc, body), caption, p, ['blue', 'white']))
examples['app-colour-header'] = {
    'title': 'The Primary blue header in app screens',
    'description': 'Four app screens with the Primary blue header and the content greyed out.',
    'height': 1300,
    'html': '<section aria-labelledby="app-header-h"><h2 class="govuk-heading-m" id="app-header-h">App header</h2>' + block('Four app screens: Home, Living room, Energy and Settings. Notice that every screen starts with the same Primary blue header with White text, so people always know where they are. The content is greyed out so that the header stands out.', header_figures) + '</section>',
}

# 4. Examples: tinted tiles and menus, with a Primary blue header and one Accent teal badge.
p = Picture(PALETTES['app'])


def tile(p, x, y, w, h, label_lines, icon):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{p.c("blue-tint-95")}" stroke="{p.c("blue-tint-50")}" stroke-width="1.5"/>'
    out += icon(p, x + 26, y + 30, 'blue')
    for n, line in enumerate(label_lines):
        out += p.text(x + 12, y + h - 14 - (len(label_lines) - 1 - n) * 18, line, 15, 'black', 'blue-tint-95', 700)
    return out + chevron(p, x + w - 20, y + h - 19, 'blue', 5, 2)


def tab_bar(p, x, w, current):
    out = f'<rect x="{x}" y="560" width="{w}" height="70" fill="{p.c("white")}"/><rect x="{x}" y="560" width="{w}" height="1" fill="{p.c("black-tint-80")}"/>'
    for n, (label, icon) in enumerate([('Home', home), ('Settings', cog)]):
        cx = x + w * (n * 2 + 1) / 4
        colour = 'blue' if label == current else 'black-tint-25'
        out += icon(p, cx, 584, colour) + p.text(cx, 612, label, 12, colour, 'white', 700 if label == current else 400, 'middle')
    return out


x = 170
w = 300
screen = (f'<rect x="{x}" y="10" width="{w}" height="150" fill="{p.c("blue")}"/>' + p.text(x + 36, 38, '9:41', 14, 'white', 'blue', 700) + status_icons(p, x + w - 30, 38, 'white')
          + p.text(x + w / 2, 72, 'Morgan household', 24, 'white', 'blue', 700, 'middle')
          + f'<rect x="{x + 75}" y="84" width="150" height="24" rx="12" fill="{p.c("teal-accent")}"/>'
          + p.text(x + w / 2, 101, 'Everyone is home', 13, 'blue-shade-50', 'teal-accent', 700, 'middle')
          + f'<rect x="{x + 12}" y="118" width="{w - 24}" height="30" rx="8" fill="{p.c("white")}"/>'
          + search_icon(p, x + 30, 132, 'black-tint-25', 6) + p.text(x + 44, 138, 'Search', 15, 'black-tint-25', 'white')
          + f'<rect x="{x + 12}" y="172" width="{w - 24}" height="48" rx="8" fill="{p.c("blue-tint-95")}" stroke="{p.c("blue-tint-50")}" stroke-width="1.5"/>'
          + history(p, x + 38, 196, 'blue') + p.text(x + 64, 201, 'Logbook', 15, 'black', 'blue-tint-95', 700) + chevron(p, x + w - 32, 196, 'blue', 5, 2)
          + p.text(x + 12, 246, 'Your areas', 16, 'black', 'white', 700) + p.text(x + w - 12, 246, 'Edit', 15, 'blue-shade-10', 'white', anchor='end')
          + tile(p, x + 12, 258, 133, 92, ['Living room'], sofa) + tile(p, x + 155, 258, 133, 92, ['Kitchen'], pan)
          + tile(p, x + 12, 360, 133, 92, ['Bedrooms'], bed) + tile(p, x + 155, 360, 133, 92, ['Garden'], tree)
          + tile(p, x + 12, 462, 133, 92, ['Energy'], bolt)
          + tab_bar(p, x, w, 'Home'))
body = f'<rect width="960" height="640" fill="{p.c("white")}"/>' + phone(p, 'app-examples-a', x, 10, w, 620, screen)


def menu(p, x, y, w, rows):
    """A tinted menu: rows of label and value, divided by Blue tint 50% lines."""
    h = 34 * len(rows)
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{p.c("blue-tint-95")}" stroke="{p.c("blue-tint-50")}" stroke-width="1.5"/>'
    for n, (label, ink, end) in enumerate(rows):
        top = y + n * 34
        if n:
            out += f'<rect x="{x}" y="{top}" width="{w}" height="1" fill="{p.c("blue-tint-50")}"/>'
        out += p.text(x + 12, top + 22, label, 14, ink, 'blue-tint-95')
        if end == 'chevron':
            out += chevron(p, x + w - 18, top + 17, 'blue', 5, 2)
        elif end == 'external':
            out += external(p, x + w - 24, top + 23, 'blue')
        elif end == 'switch':
            out += f'<rect x="{x + w - 52}" y="{top + 7}" width="40" height="20" rx="10" fill="{p.c("blue")}"/><circle cx="{x + w - 22}" cy="{top + 17}" r="7" fill="{p.c("white")}"/>'
        elif end:
            out += p.text(x + w - 12, top + 22, end, 14, 'blue', 'blue-tint-95', anchor='end')
    return out


x = 490
screen = (f'<rect x="{x}" y="10" width="{w}" height="98" fill="{p.c("blue")}"/>' + p.text(x + 36, 38, '9:41', 14, 'white', 'blue', 700) + status_icons(p, x + w - 30, 38, 'white')
          + p.text(x + 14, 92, 'Settings', 30, 'white', 'blue', 700)
          + f'<rect x="{x + 12}" y="122" width="{w - 24}" height="86" rx="8" fill="{p.c("blue-tint-95")}" stroke="{p.c("blue-tint-50")}" stroke-width="1.5"/>'
          + f'<circle cx="{x + 40}" cy="148" r="17" fill="{p.c("blue")}"/>' + p.text(x + 40, 154, 'A', 17, 'white', 'blue', 700, 'middle')
          + p.text(x + 66, 145, 'Alex Morgan', 15, 'black', 'blue-tint-95', 700) + p.text(x + 66, 163, 'Owner', 13, 'black-tint-25', 'blue-tint-95')
          + f'<rect x="{x + 12}" y="174" width="{w - 24}" height="1" fill="{p.c("blue-tint-50")}"/>'
          + p.text(x + 24, 196, 'Manage your account', 14, 'blue-shade-10', 'blue-tint-95') + external(p, x + w - 36, 197, 'blue')
          + p.text(x + 14, 226, 'You might need to sign in again.', 12, 'black-tint-25', 'white')
          + f'<rect x="{x + 12}" y="238" width="{w - 24}" height="34" rx="8" fill="{p.c("blue-tint-95")}" stroke="{p.c("blue-tint-50")}" stroke-width="1.5"/>'
          + p.text(x + 24, 260, 'Sign out', 14, 'red', 'blue-tint-95')
          + menu(p, x + 12, 288, w - 24, [('Notifications', 'black', 'On'), ('Location sharing', 'black', 'chevron'), ('Dark mode', 'black', 'switch')])
          + p.text(x + 14, 408, 'Dark mode follows your phone setting.', 12, 'black-tint-25', 'white')
          + menu(p, x + 12, 422, w - 24, [('App version', 'black', None), ('Help and feedback', 'blue-shade-10', 'external')])
          + p.text(x + w - 24, 444, '2026.11', 14, 'black-tint-25', 'blue-tint-95', anchor='end')
          + tab_bar(p, x, w, 'Settings'))
body += phone(p, 'app-examples-b', x, 10, w, 620, screen)
examples_desc = ('Two app screens. The Home screen has a Primary blue header with “Morgan household” in White, an Accent teal label reading “Everyone is home” in Blue shade 50%, and a White search field. '
                 'Below are tinted tiles in Blue tint 95% with Blue tint 50% borders and Primary blue icons: Logbook, and the areas Living room, Kitchen, Bedrooms, Garden and Energy, with an Edit link. '
                 'The Settings screen has a Primary blue header and tinted menus: an account card for Alex Morgan with a Manage your account link, Sign out in Primary red, Notifications On, Location sharing, a Primary blue Dark mode switch, the app version and a Help and feedback link. '
                 'Each screen has a tab bar with Home and Settings, the current tab in Primary blue.')
example_figure = figure('app-examples', svg('app-examples', 'App examples: tinted tiles and menus in app screens', examples_desc, body),
                        'A simplified drawing of app screens, not the Companion app’s own layout: the household, person, areas and app version are invented.', p,
                        ['blue-tint-95', 'blue-tint-50', 'teal-accent', 'blue'])
examples['app-colour-examples'] = {
    'title': 'Tinted tiles and menus in app screens',
    'description': 'Two app screens with a Primary blue header, an Accent teal badge, and Blue tint 95% tiles and menus.',
    'height': 760,
    'html': '<section aria-labelledby="app-examples-h"><h2 class="govuk-heading-m" id="app-examples-h">Examples</h2>' + block('Two app screens with tinted tiles and menus. Notice the Blue tint 95% tiles and menus with Blue tint 50% borders, which add structure without clutter, and the one Accent teal badge on the Primary blue header.', [example_figure]) + '</section>',
}

for ex in examples.values():
    ex['artwork'] = {
        'creator': 'civica project; original SVG markup',
        'licence': 'MIT, original project documentation code under LICENSE',
        'source': 'docs/data/web-app-colour-examples.yml',
        'provenance': 'Original interface pictures with an invented household, generated by docs/scripts/generate-web-app-examples.py from docs/data/govuk-brand-colours.json. No third-party artwork, screenshots, wordmark or other identity device is copied.',
        'purpose': 'Show the civica web and app palettes in drawings of a dashboard and app screens; they are not screenshots of civica, Home Assistant or the Companion app.',
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
    print('Web and app colour examples are current.')
else:
    with open(TARGET, 'w', encoding='utf-8') as out:
        out.write(text)
    print('written', ', '.join(examples))
