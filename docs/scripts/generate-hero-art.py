#!/usr/bin/env python3
"""Generate the coloured section hero artwork.

Each hero in docs/data/page-illustrations.yml has a `colour` (a palette family).
The base artwork is drawn in four blues; this script copies it with those blues
swapped for the same four steps of the chosen family, so every section hero has
its own palette colour. It also checks that white text on the hero panel passes
4.5:1. Run from the repository root:
  python3 docs/scripts/generate-hero-art.py
  python3 docs/scripts/generate-hero-art.py --check
"""
import json, os, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COLOURS = json.load(open(f'{ROOT}/docs/data/govuk-brand-colours.json'))['colours']
PAGES = yaml.safe_load(open(f'{ROOT}/docs/data/page-illustrations.yml'))
OUT = f'{ROOT}/docs/source/images/hero'


def hex_of(key):
    return COLOURS[key]['hex'].upper()


def luminance(h):
    channels = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_on_white(h):
    return 1.05 / (luminance(h) + 0.05)


def panel(family):
    """The darkest-but-one step that gives white text 4.5:1."""
    for key in (f'{family}-shade-25', f'{family}-shade-50'):
        if key in COLOURS and contrast_on_white(hex_of(key)) >= 4.5:
            return hex_of(key)
    raise SystemExit(f'No hero panel colour for {family} reaches 4.5:1 with white text')


def swaps(family):
    return {
        '#103E65': hex_of(f'{family}-shade-50') if f'{family}-shade-50' in COLOURS else panel(family),
        '#1D70B8': hex_of(family),
        '#8EB8DC': hex_of(f'{family}-tint-50'),
        '#F3F6F9': hex_of(f'{family}-tint-95'),
    }


def main(check):
    os.makedirs(OUT, exist_ok=True)
    bad = []
    for path, spec in PAGES.items():
        family = spec.get('colour')
        if not family:
            continue
        panel(family)
        if family == 'blue':
            continue
        source = open(f"{ROOT}/docs/source/images/{spec['asset']}").read()
        for old, new in swaps(family).items():
            source = source.replace(old, new).replace(old.lower(), new)
        target = f"{OUT}/{family}-{spec['asset']}"
        if check:
            if not os.path.exists(target) or open(target).read() != source:
                bad.append(target)
        else:
            open(target, 'w').write(source)
    if bad:
        print('Out of date:\n' + '\n'.join(bad), file=sys.stderr)
        sys.exit(1)


main('--check' in sys.argv)
