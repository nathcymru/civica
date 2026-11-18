#!/usr/bin/env python3
"""Generate docs/data/illustration-colour-examples.yml: original Home Assistant
illustrations that follow the compositions on the GOV.UK illustrations colour page.
Run from the repository root: python3 docs/scripts/generate-illustration-examples.py
Pass --check to fail if the YAML differs from what this script writes.
Every colour comes from docs/data/govuk-brand-colours.json by its ID."""
import json
import sys
from html import escape

import yaml

C = json.load(open('docs/data/govuk-brand-colours.json'))['colours']
hexof = lambda i: C[i]['hex']
name = lambda i: C[i]['name']


def svg(tid, title, desc, body, width=800, height=500):
    return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="{tid}-t {tid}-d" style="display:block;width:100%;height:auto">'
            f'<title id="{tid}-t">{escape(title)}</title><desc id="{tid}-d">{escape(desc)}</desc>{body}</svg>')


def figure(tid, markup, caption, colours, used=None):
    used = used or 'Colours: ' + ', '.join(dict.fromkeys(name(c) for c in colours)) + '.'
    return (f'<figure style="margin:0" aria-labelledby="{tid}-c">{markup}'
            f'<figcaption class="govuk-body-s" id="{tid}-c" style="margin-top:10px"><strong>{escape(caption)}</strong><br>{escape(used)}</figcaption></figure>')


def grid(items, minimum=280):
    return f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax({minimum}px,1fr));gap:20px;max-width:960px">' + ''.join(items) + '</div>'


def block(items):
    return grid(items)


HOUSE = 'M220 250 L400 110 L580 250 L580 430 L220 430 Z'
examples = {}

# 1. Applying colour: Primary blue as the base, accents for the key component.
# The sensor and its signal sit on the Primary blue wall, so that both accents
# reach 3:1 against what is behind them.
body = (f'<rect width="800" height="500" fill="{hexof("white")}"/>'
        f'<path d="{HOUSE}" fill="{hexof("blue")}"/>'
        f'<rect x="360" y="330" width="80" height="100" fill="{hexof("blue-shade-50")}"/>'
        f'<rect x="260" y="280" width="70" height="60" fill="{hexof("blue-shade-50")}"/><rect x="470" y="280" width="70" height="60" fill="{hexof("blue-shade-50")}"/>'
        f'<path d="M364.6 264.6A50 50 0 0 1 435.4 264.6M339.9 239.9A85 85 0 0 1 460.1 239.9" fill="none" stroke="{hexof("blue-accent")}" stroke-width="14" stroke-linecap="round"/>'
        f'<circle cx="400" cy="300" r="22" fill="{hexof("teal-accent")}"/><circle cx="400" cy="300" r="9" fill="{hexof("blue-shade-50")}"/>')
applying = [figure('ill-applying', svg('ill-applying', 'Illustration: a connected home',
                                       'A Primary blue house with Blue shade 50% windows and door, on White. On the front wall, a sensor is highlighted in Accent teal, with Accent blue signal arcs above it.', body),
                   'Primary blue as the base, accents for the sensor', ['blue', 'blue-shade-50', 'teal-accent', 'blue-accent', 'white'])]
examples['illustration-colour-applying'] = {
    'title': 'A connected home in Primary blue with accents',
    'description': 'An original Home Assistant illustration that uses Primary blue as its base, with Accent teal and Accent blue highlighting a sensor and its signal.',
    'height': 440,
    'html': block(applying),
}

# 2. Colour pairing: two complementary colours overlap; shades of one colour.
body = (f'<defs><clipPath id="ill-pairing-sun"><circle cx="560" cy="200" r="150"/></clipPath></defs>'
        f'<rect width="800" height="500" fill="{hexof("white")}"/>'
        f'<circle cx="560" cy="200" r="150" fill="{hexof("yellow")}"/>'
        f'<path d="{HOUSE}" fill="{hexof("blue")}"/>'
        f'<path d="{HOUSE}" fill="{hexof("blue-shade-25")}" clip-path="url(#ill-pairing-sun)"/>')
pairing = [figure('ill-pairing-overlap', svg('ill-pairing-overlap', 'Illustration: sun over a house',
                                             'A Primary yellow sun overlaps a Primary blue house, on White. Where they overlap, the house is Blue shade 25%.', body),
                  'Complementary colours: where they overlap, the blue is darker', ['yellow', 'blue', 'blue-shade-25', 'white'])]
shades = ['blue-tint-80', 'blue-tint-50', 'blue', 'blue-shade-25', 'blue-shade-50']
body = (f'<rect width="800" height="500" fill="{hexof(shades[0])}"/>'
        f'<path d="M0 360 Q200 280 400 330 T800 310 L800 500 L0 500 Z" fill="{hexof(shades[1])}"/>'
        f'<path d="{HOUSE}" fill="{hexof(shades[2])}"/>'
        f'<path d="M190 260 L400 95 L610 260 L580 260 L400 125 L220 260 Z" fill="{hexof(shades[3])}"/>'
        f'<rect x="360" y="330" width="80" height="100" fill="{hexof(shades[4])}"/>'
        f'<rect x="260" y="280" width="70" height="60" fill="{hexof(shades[4])}"/><rect x="470" y="280" width="70" height="60" fill="{hexof(shades[4])}"/>')
pairing.append(figure('ill-pairing-shades', svg('ill-pairing-shades', 'Illustration: a house in 5 shades of blue',
                                                'A house drawn in 5 shades of blue, from the lightest sky to the darkest door: Blue tint 80% sky, Blue tint 50% hill, Primary blue house, Blue shade 25% roof and Blue shade 50% door and windows.', body),
                      '5 shades of one colour, from sky to door', shades))
examples['illustration-colour-pairing'] = {
    'title': 'Colour pairing in a Home Assistant illustration',
    'description': 'Two original illustrations: a yellow sun overlapping a blue house, and a house drawn in 5 shades of blue.',
    'height': 440,
    'html': block(pairing),
}

# 3. Using contrast: the scene palette in front of greys and blues, and a scene
# with a warm and cool focal point, shown again in greyscale to test it. The
# person in yellow stands in front of the dark window and the person in blue in
# front of the White wall, so each body keeps its edge without colour.
stripes = ['black-tint-95', 'black-tint-80', 'black-tint-50', 'blue-tint-80', 'blue-tint-50', 'blue-shade-25']
scene_colours = ['white', 'blue-shade-50', 'yellow', 'blue', 'brown-tint-50', 'brown']
body = (''.join(f'<rect x="{round(n * 800 / 6)}" width="{round(800 / 6) + 1}" height="500" fill="{hexof(s)}"/>' for n, s in enumerate(stripes))
        + f'<rect x="90" y="170" width="620" height="160" rx="80" fill="{hexof("blue-shade-50")}"/>'
        + ''.join(f'<circle cx="{200 + n * 100}" cy="250" r="40" fill="{hexof(c)}"/>' for n, c in enumerate([c for c in scene_colours if c != 'blue-shade-50'])))
palette_figure = figure('ill-contrast-palette', svg('ill-contrast-palette', 'Illustration: a palette in front of greys and blues',
                                                     'The 6 colours of the plant sensor scene, as a Blue shade 50% palette holding circles of White, Primary yellow, Primary blue, Brown tint 50% and Primary brown, in front of stripes of Black tint 95%, Black tint 80%, Black tint 50%, Blue tint 80%, Blue tint 50% and Blue shade 25%.', body),
                        'The scene palette against greys and blues', stripes + scene_colours)


def scene(filter_attr=''):
    ink = hexof('blue-shade-50')
    return (f'<g{filter_attr}>'
            f'<rect width="800" height="500" fill="{hexof("white")}"/>'
            f'<rect x="60" y="40" width="320" height="460" fill="{ink}"/>'
            f'<path d="M220 40V500M60 230H380" stroke="{hexof("white")}" stroke-width="10"/>'
            # Person in yellow, in front of the window.
            f'<rect x="120" y="285" width="170" height="240" rx="70" fill="{hexof("yellow")}"/>'
            f'<circle cx="205" cy="215" r="46" fill="{hexof("brown-tint-50")}"/>'
            f'<path d="M159 210a46 46 0 0 1 92 0q-46-24-92 0z" fill="{hexof("brown")}"/>'
            f'<path d="M265 320L392 368" stroke="{hexof("yellow")}" stroke-width="38" stroke-linecap="round"/>'
            # Person in blue, in front of the wall, with a broader build.
            f'<rect x="500" y="270" width="220" height="260" rx="100" fill="{hexof("blue")}"/>'
            f'<circle cx="610" cy="200" r="50" fill="{hexof("brown")}"/>'
            f'<circle cx="610" cy="138" r="22" fill="{ink}"/><path d="M560 195a50 50 0 0 1 100 0q-50-26-100 0z" fill="{ink}"/>'
            f'<path d="M530 320L488 368" stroke="{hexof("blue")}" stroke-width="38" stroke-linecap="round"/>'
            # Plant with a soil moisture sensor, held between them against the wall.
            f'<ellipse cx="418" cy="282" rx="16" ry="38" transform="rotate(-30 418 282)" fill="{ink}"/>'
            f'<ellipse cx="462" cy="282" rx="16" ry="38" transform="rotate(30 462 282)" fill="{ink}"/>'
            f'<ellipse cx="440" cy="260" rx="15" ry="42" fill="{ink}"/>'
            f'<rect x="478" y="236" width="16" height="100" rx="6" fill="{ink}"/><circle cx="486" cy="250" r="6" fill="{hexof("yellow")}"/>'
            f'<path d="M395 330H485L471 410H409Z" fill="{ink}"/>'
            f'<circle cx="400" cy="368" r="20" fill="{hexof("brown-tint-50")}"/><circle cx="482" cy="368" r="20" fill="{hexof("brown")}"/>'
            '</g>')


scene_desc = ('2 people hold a potted plant with a soil moisture sensor between them. One wears Primary yellow and stands in front of a Blue shade 50% window with White glazing bars; '
              'the other wears Primary blue and stands in front of the White wall. Their skin is Brown tint 50% and Primary brown. The leaves, the pot and the sensor are Blue shade 50%, and the sensor has a Primary yellow light.')
contrast = [palette_figure,
            figure('ill-contrast-scene', svg('ill-contrast-scene', 'Illustration: 2 people with a plant sensor', scene_desc, scene()),
                   'Warm and cool contrast draws the eye to the plant', scene_colours),
            figure('ill-contrast-grey', svg('ill-contrast-grey', 'Illustration: the same scene in greyscale',
                                            'The same scene with its colour removed. The person in yellow stays light against the dark window, and the person in blue stays darker than the White wall.',
                                            '<defs><filter id="ill-contrast-greyscale"><feColorMatrix type="saturate" values="0"/></filter></defs>' + scene(' filter="url(#ill-contrast-greyscale)"')),
                   'The same scene in greyscale, as a check', [], 'Colours: the same 6, with colour removed by a greyscale filter.')]
examples['illustration-colour-contrast'] = {
    'title': 'Contrast in a Home Assistant illustration',
    'description': 'Original illustrations: a palette in front of greys and blues, 2 people setting up a plant sensor in yellow and blue, and the same scene in greyscale.',
    'height': 800,
    'html': block(contrast),
}

for ex in examples.values():
    ex['artwork'] = {
        'creator': 'civica project; original SVG markup',
        'licence': 'MIT, original project documentation code under LICENSE',
        'source': 'docs/data/illustration-colour-examples.yml',
        'provenance': 'Original illustrations generated by docs/scripts/generate-illustration-examples.py from docs/data/govuk-brand-colours.json. Compositions follow the GOV.UK illustrations colour examples; no GOV.UK artwork, marks or imagery are copied.',
        'purpose': 'Show how to apply, pair and contrast GOV.UK colours in a Home Assistant illustration.',
        'intended_background': 'Each illustration carries its own background.',
        'alternative_text_decision': 'Each illustration is an SVG image with a title and a description that names what it shows and its colours; the caption lists the colours.',
        'review_status': 'Source checks only; integrated rendered review is recorded separately.',
    }


class Literal(str):
    pass


yaml.add_representer(Literal, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|'))
for ex in examples.values():
    ex['html'] = Literal(ex['html'].replace('><', '>\n<') + '\n')
TARGET = 'docs/data/illustration-colour-examples.yml'
text = ('# Generated by docs/scripts/generate-illustration-examples.py from docs/data/govuk-brand-colours.json.\n'
        '# Edit the script and run it again rather than editing this file.\n'
        + yaml.dump({'examples': examples}, sort_keys=False, allow_unicode=True, width=10000))
if '--check' in sys.argv:
    with open(TARGET, encoding='utf-8') as current:
        if current.read() != text:
            sys.exit(f'{TARGET} is out of date. Run python3 docs/scripts/generate-illustration-examples.py.')
    print('Illustration colour examples are current.')
else:
    with open(TARGET, 'w', encoding='utf-8') as out:
        out.write(text)
    print('written', ', '.join(examples))
