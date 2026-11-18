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


def section(sid, heading, lead, items):
    return (f'<section aria-labelledby="{sid}-h"><h2 class="govuk-heading-m" id="{sid}-h">{escape(heading)}</h2>'
            f'<p class="govuk-body">{escape(lead)}</p>' + grid(items) + '</section>')


HOUSE = 'M220 250 L400 110 L580 250 L580 430 L220 430 Z'
examples = {}

# 1. Applying colour: Primary blue as the base, accents for one key component.
body = (f'<rect width="800" height="500" fill="{hexof("white")}"/>'
        f'<path d="{HOUSE}" fill="{hexof("blue")}"/>'
        f'<rect x="360" y="330" width="80" height="100" fill="{hexof("blue-shade-50")}"/>'
        f'<rect x="260" y="280" width="70" height="60" fill="{hexof("blue-shade-50")}"/><rect x="470" y="280" width="70" height="60" fill="{hexof("blue-shade-50")}"/>'
        f'<path d="M640 150a60 60 0 0 1 60 60M640 110a100 100 0 0 1 100 100" fill="none" stroke="{hexof("blue-accent")}" stroke-width="16" stroke-linecap="round"/>'
        f'<circle cx="640" cy="210" r="22" fill="{hexof("teal-accent")}"/>'
        f'<circle cx="400" cy="230" r="34" fill="{hexof("teal-accent")}"/><circle cx="400" cy="230" r="14" fill="{hexof("blue-shade-50")}"/>')
applying = [figure('ill-applying', svg('ill-applying', 'Illustration: a connected home',
                                       'A Primary blue house with Blue shade 50% windows and door. A sensor on the front of the house is highlighted in Accent teal, and Accent blue signal arcs come from an Accent teal hub beside it.', body),
                   'Primary blue as the base, accents for the key component', ['blue', 'blue-shade-50', 'teal-accent', 'blue-accent', 'white'])]
examples['illustration-colour-applying'] = {
    'title': 'A connected home in Primary blue with accents',
    'description': 'An original Home Assistant illustration that uses Primary blue as its base and Accent teal and Accent blue to highlight a sensor and its signal.',
    'height': 640,
    'html': section('ill-applying', 'Applying colour', 'Primary blue is the base of the illustration. Accent teal and Accent blue highlight the sensor, which is the key component.', applying),
}

# 2. Colour pairing: two complementary colours overlap; five shades of one colour.
body = (f'<defs><clipPath id="ill-pairing-sun"><circle cx="560" cy="200" r="150"/></clipPath></defs>'
        f'<rect width="800" height="500" fill="{hexof("white")}"/>'
        f'<circle cx="560" cy="200" r="150" fill="{hexof("yellow")}"/>'
        f'<path d="{HOUSE}" fill="{hexof("blue")}"/>'
        f'<path d="{HOUSE}" fill="{hexof("blue-shade-25")}" clip-path="url(#ill-pairing-sun)"/>')
pairing = [figure('ill-pairing-overlap', svg('ill-pairing-overlap', 'Illustration: sun over a house',
                                             'A Primary yellow sun overlaps a Primary blue house. Where they overlap, the house is Blue shade 25%.', body),
                  'Complementary colours: where they overlap, the blue is darker', ['yellow', 'blue', 'blue-shade-25', 'white'])]
shades = ['blue-tint-80', 'blue-tint-50', 'blue', 'blue-shade-25', 'blue-shade-50']
body = (f'<rect width="800" height="500" fill="{hexof(shades[0])}"/>'
        f'<path d="M0 360 Q200 280 400 330 T800 310 L800 500 L0 500 Z" fill="{hexof(shades[1])}"/>'
        f'<path d="{HOUSE}" fill="{hexof(shades[2])}"/>'
        f'<path d="M190 260 L400 95 L610 260 L580 260 L400 125 L220 260 Z" fill="{hexof(shades[3])}"/>'
        f'<rect x="360" y="330" width="80" height="100" fill="{hexof(shades[4])}"/>'
        f'<rect x="260" y="280" width="70" height="60" fill="{hexof(shades[4])}"/><rect x="470" y="280" width="70" height="60" fill="{hexof(shades[4])}"/>'
        + ''.join(f'<rect x="{40 + n * 50}" y="450" width="40" height="30" fill="{hexof(s)}" stroke="{hexof("blue-shade-50")}" stroke-width="2"/>' for n, s in enumerate(shades)))
pairing.append(figure('ill-pairing-shades', svg('ill-pairing-shades', 'Illustration: a house in five shades of blue',
                                                'A house drawn in 5 shades of blue, from the lightest sky to the darkest door: Blue tint 80% sky, Blue tint 50% hill, Primary blue house, Blue shade 25% roof and Blue shade 50% door and windows. A key of the 5 shades sits in the corner.', body),
                      '5 shades of one colour separate the foreground from the background', shades))
examples['illustration-colour-pairing'] = {
    'title': 'Colour pairing in a Home Assistant illustration',
    'description': 'Two original illustrations: a yellow sun overlapping a blue house, and a house drawn in 5 shades of blue.',
    'height': 640,
    'html': section('ill-pairing', 'Colour pairing', 'Complementary colours keep key elements distinct. Shades of one colour separate the foreground from the background, so that the image does not look flat.', pairing),
}

# 3. Using contrast: a palette in front of greys and blues, and a scene with a
# warm and cool focal point, shown again in greyscale to test it.
stripes = ['black-tint-95', 'black-tint-80', 'black-tint-50', 'blue-tint-80', 'blue-tint-50', 'blue-shade-25']
scene_colours = ['white', 'blue-tint-80', 'blue-shade-50', 'yellow', 'blue', 'brown-tint-50']
body = (''.join(f'<rect x="{round(n * 800 / 6)}" width="{round(800 / 6) + 1}" height="500" fill="{hexof(s)}"/>' for n, s in enumerate(stripes))
        + f'<rect x="70" y="170" width="660" height="160" rx="80" fill="{hexof("white")}" stroke="{hexof("blue-shade-50")}" stroke-width="4"/>'
        + ''.join(f'<circle cx="{150 + n * 100}" cy="250" r="40" fill="{hexof(c)}" stroke="{hexof("blue-shade-50")}" stroke-width="4"/>' for n, c in enumerate(scene_colours)))
palette_figure = figure('ill-contrast-palette', svg('ill-contrast-palette', 'Illustration: a palette in front of greys and blues',
                                                     'The 6 colours of the illustration below, White, Blue tint 80%, Blue shade 50%, Primary yellow, Primary blue and Brown tint 50%, as circles on a White palette, in front of stripes of Black tint 95%, Black tint 80%, Black tint 50%, Blue tint 80%, Blue tint 50% and Blue shade 25%.', body),
                        'Check the palette against greys and blues', stripes + scene_colours)


def scene(filter_attr=''):
    ink = hexof('blue-shade-50')
    skin = hexof('brown-tint-50')
    return (f'<g{filter_attr}>'
            f'<rect width="800" height="500" fill="{hexof("white")}"/>'
            f'<rect x="130" y="30" width="540" height="440" fill="{hexof("blue-tint-80")}" stroke="{ink}" stroke-width="12"/>'
            f'<path d="M400 30V470M130 220H670" stroke="{ink}" stroke-width="8"/>'
            # Person in yellow.
            f'<rect x="185" y="270" width="170" height="260" rx="70" fill="{hexof("yellow")}"/>'
            f'<circle cx="270" cy="205" r="48" fill="{skin}"/>'
            f'<path d="M222 200a48 48 0 0 1 96 0q-48-26-96 0z" fill="{ink}"/>'
            f'<path d="M320 300L372 352" stroke="{hexof("yellow")}" stroke-width="40" stroke-linecap="round"/>'
            # Person in blue.
            f'<rect x="445" y="270" width="170" height="260" rx="70" fill="{hexof("blue")}"/>'
            f'<circle cx="530" cy="205" r="48" fill="{skin}"/>'
            f'<circle cx="530" cy="146" r="22" fill="{ink}"/><path d="M482 200a48 48 0 0 1 96 0q-48-26-96 0z" fill="{ink}"/>'
            f'<path d="M480 300L428 352" stroke="{hexof("blue")}" stroke-width="40" stroke-linecap="round"/>'
            # Plant, pot and soil moisture sensor, held between them.
            f'<ellipse cx="378" cy="282" rx="16" ry="38" transform="rotate(-30 378 282)" fill="{ink}"/>'
            f'<ellipse cx="422" cy="282" rx="16" ry="38" transform="rotate(30 422 282)" fill="{ink}"/>'
            f'<ellipse cx="400" cy="262" rx="15" ry="42" fill="{ink}"/>'
            f'<rect x="412" y="286" width="14" height="54" rx="4" fill="{hexof("white")}" stroke="{ink}" stroke-width="4"/>'
            f'<path d="M355 330H445L432 410H368Z" fill="{ink}"/>'
            f'<circle cx="368" cy="362" r="20" fill="{skin}"/><circle cx="432" cy="362" r="20" fill="{skin}"/>'
            '</g>')


scene_desc = ('2 people framed by a window hold a potted plant with a soil moisture sensor between them. '
              'One wears Primary yellow and the other Primary blue, in front of a Blue tint 80% sky, with Blue shade 50% hair, window frame and pot, Brown tint 50% skin and a White sensor.')
contrast = [palette_figure,
            figure('ill-contrast-scene', svg('ill-contrast-scene', 'Illustration: 2 people with a plant sensor', scene_desc, scene()),
                   'Warm and cool contrast makes a focal point', scene_colours),
            figure('ill-contrast-grey', svg('ill-contrast-grey', 'Illustration: the same scene in greyscale',
                                            'The same scene with its colour removed. The people, the plant and the window stay distinct.',
                                            '<defs><filter id="ill-contrast-greyscale"><feColorMatrix type="saturate" values="0"/></filter></defs>' + scene(' filter="url(#ill-contrast-greyscale)"')),
                   'The same scene in greyscale, as a check', [], 'Colours: the same 6, with colour removed by a greyscale filter.')]
examples['illustration-colour-contrast'] = {
    'title': 'Contrast in a Home Assistant illustration',
    'description': 'Original illustrations: a palette in front of greys and blues, 2 people setting up a plant sensor in yellow and blue, and the same scene in greyscale.',
    'height': 1250,
    'html': section('ill-contrast', 'Using contrast', 'The yellow and blue clothes are a warm and cool contrast that draws the eye to the plant sensor, while Primary blue stays dominant. The greyscale copy is a quick check that the scene still reads without colour.', contrast),
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
