#!/usr/bin/env python3
"""Generate docs/data/social-colour-examples.yml: Home Assistant social tiles in
the civica social colours.
Run from the repository root: python3 docs/scripts/generate-social-examples.py
Pass --check to fail if the YAML differs from what this script writes.
Every colour comes from docs/data/govuk-brand-colours.json by its ID."""
import json
import sys
from html import escape

C = json.load(open('docs/data/govuk-brand-colours.json'))['colours']
hexof = lambda i: C[i]['hex']
name = lambda i: C[i]['name']
an = lambda i: ('an ' if name(i)[0] in 'AEIOU' else 'a ') + name(i)
FONT = 'Roboto,Helvetica Neue,Helvetica,Arial,sans-serif'


def lines(text_lines, x, y, size, fill, anchor='middle', weight=700, gap=1.2):
    out = []
    for n, line in enumerate(text_lines):
        out.append(f'<text x="{x}" y="{round(y + n * size * gap)}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(line)}</text>')
    return ''.join(out)


def svg(tid, title, desc, body, bg):
    return (f'<svg viewBox="0 0 1080 1080" role="img" aria-labelledby="{tid}-t {tid}-d" style="display:block;width:100%;height:auto;font-family:{FONT}">'
            f'<title id="{tid}-t">{escape(title)}</title><desc id="{tid}-d">{escape(desc)}</desc>'
            f'<rect width="1080" height="1080" fill="{hexof(bg)}"/>{body}</svg>')


def circle_tile(tid, text, bg, circle, ink, title):
    body = f'<circle cx="540" cy="540" r="400" fill="{hexof(circle)}"/>' + lines(text, 540, 540 - (len(text) - 1) * 48, 80, hexof(ink))
    desc = f'“{" ".join(text)}” in {name(ink)} text, in {an(circle)} circle on {an(bg)} background.'
    return svg(tid, title, desc, body, bg), [ink, circle, bg]


def figure(tid, svg_markup, caption, colours):
    used = ', '.join(dict.fromkeys(name(c) for c in colours))
    return (f'<figure style="margin:0" aria-labelledby="{tid}-c">{svg_markup}'
            f'<figcaption class="govuk-body-s" id="{tid}-c" style="margin-top:10px"><strong>{escape(caption)}</strong><br>Colours: {escape(used)}.</figcaption></figure>')


def grid(items, minimum=220):
    return f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax({minimum}px,1fr));gap:20px;max-width:960px">' + ''.join(items) + '</div>'


examples = {}

# 1. Use colour to reflect tone: inform to inspire.
tone = []
for tid, text, bg, circle, ink, caption in [
    ('tone-1', ['Power cut', 'in your area'], 'black', 'white', 'black', 'Black and white'),
    ('tone-2', ['Your energy use', 'is down', 'this week'], 'blue-shade-50', 'white', 'blue-shade-50', 'Dark shade'),
    ('tone-3', ['Bins go out', 'tonight'], 'blue', 'white', 'blue', 'Primary blue'),
    ('tone-4', ['Get help', 'setting up', 'a new device'], 'blue', 'blue-accent', 'blue-shade-50', 'Tonal colour'),
]:
    markup, used = circle_tile(tid, text, bg, circle, ink, f'Social tile: {" ".join(text)}')
    tone.append(figure(tid, markup, caption, used))
body = lines(['Your first', 'automation'], 540, 480, 110, hexof('blue-shade-50')) + f'<rect x="300" y="700" width="480" height="12" fill="{hexof("blue-shade-50")}"/>'
tone.append(figure('tone-5', svg('tone-5', 'Social tile: Your first automation', '“Your first automation” in Blue shade 50% text, underlined, on an Accent green background.', body, 'green-accent'),
                   'Companion colour', ['blue-shade-50', 'green-accent']))
examples['social-colour-tone'] = {
    'title': 'Social tiles from informative to inspiring',
    'description': 'Five Home Assistant social tiles, from black and white, the most informative, to a companion colour, the most inspiring, in the social colours.',
    'height': 900,
    'html': '<section aria-labelledby="social-tone-h"><h2 class="govuk-heading-m" id="social-tone-h">From informative to inspiring</h2>'
            '<p class="govuk-body">In order: black and white, a dark shade, Primary blue, a tonal colour and a companion colour. The messages are invented examples.</p>'
            + grid(tone) + '</section>',
}

# 2. Tonal colour examples: serious messages in green, red and purple tones.
tonal = []
markup, used = circle_tile('tonal-green', ['Check on a', 'neighbour', 'in the cold'], 'green-tint-95', 'green-tint-80', 'green-shade-50', 'Social tile: Check on a neighbour in the cold')
tonal.append(figure('tonal-green', markup, 'Green tones', used))
body = (f'<circle cx="540" cy="330" r="110" fill="{hexof("red-accent")}"/>'
        f'<rect x="525" y="250" width="30" height="110" fill="{hexof("red-shade-50")}"/><rect x="525" y="380" width="30" height="30" fill="{hexof("red-shade-50")}"/>'
        + lines(['Storm warning:', 'secure the garden'], 540, 620, 84, hexof('red-tint-95')))
tonal.append(figure('tonal-red', svg('tonal-red', 'Social tile: Storm warning: secure the garden',
                                     'An exclamation mark in Red shade 50% inside an Accent red circle, above “Storm warning: secure the garden” in Red tint 95% text, on a Primary red background.', body, 'red'),
                    'Red tones', ['red-tint-95', 'red-shade-50', 'red-accent', 'red']))
body = (lines(['Boiler fault:'], 540, 330, 84, hexof('white'))
        + f'<rect x="240" y="380" width="600" height="130" rx="65" fill="{hexof("purple")}"/>' + lines(['what to do'], 540, 472, 84, hexof('white'))
        + lines(['next'], 540, 610, 84, hexof('white'))
        + f'<path d="M540 700v170M450 790l90 90 90-90" fill="none" stroke="{hexof("purple-accent")}" stroke-width="40" stroke-linecap="round" stroke-linejoin="round"/>')
tonal.append(figure('tonal-purple', svg('tonal-purple', 'Social tile: Boiler fault: what to do next',
                                        '“Boiler fault: what to do next” in White text, with “what to do” in a Primary purple lozenge and an Accent purple arrow below, on a Purple shade 50% background.', body, 'purple-shade-50'),
                    'Purple tones', ['white', 'purple', 'purple-accent', 'purple-shade-50']))
examples['social-colour-tonal'] = {
    'title': 'Serious social tiles in green, red and purple tones',
    'description': 'Three serious Home Assistant social tiles, each in the tints and shades of one colour family.',
    'height': 800,
    'html': '<section aria-labelledby="social-tonal-h"><h2 class="govuk-heading-m" id="social-tonal-h">Tonal colour</h2>'
            '<p class="govuk-body">Three serious posts: checking on a neighbour in the cold, a storm warning and a boiler fault. The messages are invented examples.</p>'
            + grid(tonal) + '</section>',
}

# 3. Companion colour examples.
comp = []
body = (f'<path d="M420 320H660" fill="none" stroke="{hexof("blue")}" stroke-width="20" stroke-linecap="round"/>'
        + ''.join(f'<rect x="{x}" y="{y}" width="56" height="{310 - y}" fill="{hexof("blue")}"/>' for x, y in [(440, 220), (512, 140), (584, 190)])
        + lines(['See where your'], 540, 470, 84, hexof('blue'))
        + f'<rect x="355" y="520" width="370" height="130" rx="65" fill="{hexof("blue")}"/>' + lines(['energy'], 540, 612, 84, hexof('white'))
        + lines(['goes'], 540, 760, 84, hexof('blue')))
comp.append(figure('companion-yellow', svg('companion-yellow', 'Social tile: See where your energy goes',
                                           'A Primary blue bar chart above “See where your energy goes” in large Primary blue text, with “energy” in White on a Primary blue lozenge, on a Primary yellow background.', body, 'yellow'),
                   'Primary blue on Primary yellow', ['blue', 'white', 'yellow']))
body = (f'<path d="M540 500c-90-110-150-170-150-250a150 150 0 0 1 300 0c0 80-60 140-150 250z" fill="{hexof("magenta")}"/><circle cx="540" cy="250" r="55" fill="{hexof("blue-tint-95")}"/>'
        + lines(['Check who', 'is home'], 540, 680, 110, hexof('blue-shade-50')))
comp.append(figure('companion-magenta', svg('companion-magenta', 'Social tile: Check who is home',
                                            'A Primary magenta map pin above “Check who is home” in Blue shade 50% text, on a Blue tint 95% background.', body, 'blue-tint-95'),
                   'Primary magenta on Blue tint 95%', ['magenta', 'blue-shade-50', 'blue-tint-95']))
body = (f'<circle cx="540" cy="320" r="190" fill="{hexof("blue-shade-50")}"/>' + lines(['Step', 'by step'], 540, 305, 72, hexof('green-accent'))
        + lines(['Add a door', 'sensor'], 540, 700, 110, hexof('blue-shade-50')))
comp.append(figure('companion-green', svg('companion-green', 'Social tile: Step by step: add a door sensor',
                                          '“Step by step” in Accent green text inside a Blue shade 50% circle, above “Add a door sensor” in Blue shade 50% text, on an Accent green background.', body, 'green-accent'),
                   'Blue shade 50% on Accent green', ['green-accent', 'blue-shade-50']))
examples['social-colour-companion'] = {
    'title': 'Social tiles with companion colours',
    'description': 'Three Home Assistant social tiles, each built on one of the companion colour pairings.',
    'height': 800,
    'html': '<section aria-labelledby="social-companion-h"><h2 class="govuk-heading-m" id="social-companion-h">Companion colour</h2>'
            '<p class="govuk-body">Three posts that prompt an action: seeing where the household’s energy goes on the Energy dashboard, checking who is home and adding a door sensor. The messages are invented examples.</p>'
            + grid(comp) + '</section>',
}

for ex in examples.values():
    ex['artwork'] = {
        'creator': 'civica project; original SVG markup',
        'licence': 'MIT, original project documentation code under LICENSE',
        'source': 'docs/data/social-colour-examples.yml',
        'provenance': 'Original tiles and invented messages generated by docs/scripts/generate-social-examples.py from docs/data/govuk-brand-colours.json. No third-party artwork, marks or imagery are copied.',
        'purpose': 'Show how the civica social colours set the tone of a Home Assistant social post.',
        'intended_background': 'Each tile carries its own background. Every text pair reaches at least 4.5:1, except Primary blue on Primary yellow (3.84:1), which carries only large words.',
        'alternative_text_decision': 'Each tile is an SVG image with a title and a description that names its message and colours; the caption lists the colours.',
        'review_status': 'Source checks only; integrated rendered review is recorded separately.',
    }

import yaml


class Literal(str):
    pass


yaml.add_representer(Literal, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|'))
for ex in examples.values():
    ex['html'] = Literal(ex['html'].replace('><', '>\n<') + '\n')
TARGET = 'docs/data/social-colour-examples.yml'
text = ('# Generated by docs/scripts/generate-social-examples.py from docs/data/govuk-brand-colours.json.\n'
        '# Edit the script and run it again rather than editing this file.\n'
        + yaml.dump({'examples': examples}, sort_keys=False, allow_unicode=True, width=10000))
if '--check' in sys.argv:
    with open(TARGET, encoding='utf-8') as current:
        if current.read() != text:
            sys.exit(f'{TARGET} is out of date. Run python3 docs/scripts/generate-social-examples.py.')
    print('Social colour examples are current.')
else:
    with open(TARGET, 'w', encoding='utf-8') as out:
        out.write(text)
    print('written', ', '.join(examples))
