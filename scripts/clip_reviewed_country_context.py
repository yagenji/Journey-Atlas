#!/usr/bin/env python3
"""Clip reviewed neighboring land to the complement of approved country silhouettes.

The OSM and administrative source polygons are not shifted or redrawn. Only
portions beneath the EXACT approved national paths are hidden in the SVG.
Draft existing-map migration PR only; never alters Country JSON or main.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

SVG = '{http://www.w3.org/2000/svg}'
EXPECTED = {
    'macau': (1, '44bdca23d43ee30484e9fcf911a2b373c86030c54638edbe0810875d60d35eb1'),
    'singapore': (5, '237292bac3e9c90204fa4e2169d588deb3709916c823dac254cd4383f69121a5'),
}


def national_paths(source: str) -> list[str]:
    root = ET.fromstring(source)
    parents = {child: parent for parent in root.iter() for child in parent}
    paths = []
    for node in root.iter(SVG + 'path'):
        parent = node
        while parent is not None and 'fill' not in parent.attrib:
            parent = parents.get(parent)
        if parent is not None and parent.get('fill') == 'url(#land)':
            paths.append(node.attrib['d'])
    return paths


def apply(slug: str, repo: Path) -> None:
    relative = f'assets/images/{slug}/map-atlas-v1.svg'
    path = repo / relative
    source = path.read_text(encoding='utf-8')
    main = subprocess.check_output(['git', 'show', f'origin/main:{relative}'], cwd=repo).decode()
    original = national_paths(source)
    count, digest = EXPECTED[slug]
    assert original == national_paths(main), f'{slug}: national paths differ from main'
    assert len(original) == count
    assert hashlib.sha256('\n'.join(original).encode()).hexdigest() == digest
    assert 'id="foreign-land-only"' not in source
    assert source.count('<g id="geographic-context">') == 1
    assert source.count('</defs>') == 1
    assert ET.fromstring(source).get('viewBox') == '0 0 1200 760'

    # An even-odd canvas rectangle minus the original country rings is an
    # exact display-only cutout; no guessed border or new coastline is drawn.
    d = 'M 0,0 L 1200,0 L 1200,760 L 0,760 Z ' + ' '.join(original)
    clip = ('<clipPath id="foreign-land-only" clipPathUnits="userSpaceOnUse">'
            '<path d="' + d + '" clip-rule="evenodd" fill-rule="evenodd"/>'
            '</clipPath>')
    changed = source.replace('</defs>', clip + '</defs>', 1).replace(
        '<g id="geographic-context">',
        '<g id="geographic-context" clip-path="url(#foreign-land-only)">', 1)
    root = ET.fromstring(changed)
    assert national_paths(changed) == original
    assert root.find(".//*[@id='foreign-land-only']") is not None
    assert next(node for node in root.iter(SVG + 'g') if node.get('id') == 'geographic-context').get('clip-path') == 'url(#foreign-land-only)'
    render = cairosvg.svg2png(bytestring=changed.encode(), output_width=1200, output_height=760)
    with Image.open(BytesIO(render)) as image:
        image.load()
        assert image.size == (1200, 760)
    path.write_text(changed, encoding='utf-8')
    print(slug, 'original national paths unchanged', count,
          'exact context exclusion', 'decoded 1200x760',
          'sha256', hashlib.sha256(changed.encode()).hexdigest())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    args = parser.parse_args()
    for slug in EXPECTED:
        apply(slug, args.repo.resolve())


if __name__ == '__main__':
    main()
