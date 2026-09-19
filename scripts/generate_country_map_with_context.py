#!/usr/bin/env python3
"""Generate a new single-region Country map with the approved sea/land context.

The legacy generator remains unchanged so in-flight Country work is unaffected.
This wrapper requires a target-country-specific administrative geometry source;
GSHHS coastline alone is not sufficient to distinguish a target country.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import Polygon
from shapely.ops import unary_union


_SVG_NS = '{http://www.w3.org/2000/svg}'
_SVG_RING = re.compile(r'M\s*([^M]*?)\s*Z', re.S)


def _linear_rings(d: str) -> list[tuple[str, Polygon]]:
    """Parse only the M/L/Z polygons emitted by our shared map generator."""
    chunks = list(_SVG_RING.finditer(d))
    if not chunks or _SVG_RING.sub('', d).strip():
        raise ValueError('Unsupported SVG path in geographic context; review rather than erase land')
    result = []
    for chunk in chunks:
        vertices = []
        for xy in re.split(r'\s*L\s*', chunk.group(1)):
            if not xy.strip():
                continue
            nums = xy.strip().split(',')
            if len(nums) != 2:
                raise ValueError('Unsupported SVG coordinate in geographic context')
            vertices.append((float(nums[0]), float(nums[1])))
        polygon = Polygon(vertices)
        if not polygon.is_valid or polygon.area <= 0:
            raise ValueError('Invalid generated polygon in geographic context')
        result.append((chunk.group(0), polygon))
    return result


def strip_redundant_island_context(svg: str) -> tuple[str, int]:
    """Remove ONLY GSHHS island components >=97% covered by ADM0 target.

    GSHHS and Natural Earth have slightly different coastlines: drawing both
    creates a second silhouette around isolated island Countries. Preserve
    neighboring components and the authoritative ADM0 target path unchanged.
    Connected continental context is intentionally left for separate QA.
    """
    root = ET.fromstring(svg)
    if root.tag != _SVG_NS + 'svg' or root.get('data-map-projection') != 'local-equirectangular-fit-v1':
        raise ValueError('Only canonical single-region map previews can be filtered')
    contexts = [g for g in root.iter(_SVG_NS + 'g') if g.get('id') == 'geographic-context']
    if len(contexts) != 1 or len(contexts[0]) != 1 or contexts[0][0].tag != _SVG_NS + 'path':
        raise ValueError('Unsupported geographic-context structure')
    context_path = contexts[0][0]
    original = context_path.get('d')
    if not original:
        return svg, 0
    target_paths = [p for p in root.iter(_SVG_NS + 'path') if p.get('fill') == 'url(#land)']
    if not target_paths:
        raise ValueError('Target administrative land path is missing')
    target = unary_union([polygon for path in target_paths for _, polygon in _linear_rings(path.get('d', ''))])
    components = _linear_rings(original)
    redundant = []
    for component, polygon in components:
        ratio = polygon.intersection(target).area / polygon.area
        if ratio >= 0.97:
            redundant.append(polygon)
    if not redundant:
        return svg, 0
    omitted, retained = 0, []
    for component, polygon in components:
        if any(polygon.intersection(island).area / polygon.area >= 0.97 for island in redundant):
            omitted += 1
        else:
            retained.append(component)
    replacement = ' '.join(retained)
    search = 'd="' + original + '"'
    if svg.count(search) != 1:
        raise ValueError('Context path could not be replaced uniquely')
    return svg.replace(search, 'd="' + replacement + '"', 1), omitted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--country-json', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source', required=True, choices=('natural-earth', 'geoboundaries'))
    parser.add_argument('--context-resolution', default='i', choices=('c', 'l', 'i', 'h', 'f'))
    parser.add_argument('--simplify', default=0.003, type=float)
    parser.add_argument('--max-bytes', default=6000000, type=int)
    args, generator_args = parser.parse_known_args()
    if any(arg == '--bounds' or arg.startswith('--bounds=') or arg == '--output' or arg.startswith('--output=') for arg in generator_args):
        parser.error('Bounds and output are authoritative in Country JSON and this wrapper')
    if args.output.exists():
        parser.error('Output must be a new preview file, not an existing production asset')
    if not (0 <= args.simplify <= 0.003):
        parser.error('Simplify must be between zero and 0.003 degrees')
    country = json.loads(args.country_json.read_text(encoding='utf-8'))
    config = country['map']
    if config.get('regions'):
        parser.error('Multi-region Country maps need a reviewed region-aware generator')
    bounds = config['bounds']
    script_dir = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='atlas-map-context-') as temporary:
        generated = Path(temporary) / 'target.svg'
        command = [
            sys.executable, str(script_dir / 'generate_country_map.py'),
            '--source', args.source,
            '--bounds', *(str(bounds[key]) for key in ('west', 'south', 'east', 'north')),
            '--output', str(generated), '--simplify', str(args.simplify),
            *generator_args,
        ]
        subprocess.run(command, check=True)
        subprocess.run([
            sys.executable, str(script_dir / 'add_country_map_context.py'),
            '--country-json', str(args.country_json),
            '--input', str(generated), '--output', str(args.output),
            '--resolution', args.context_resolution,
            '--simplify', str(args.simplify), '--max-bytes', str(args.max_bytes),
        ], check=True)
        cleaned, count = strip_redundant_island_context(args.output.read_text(encoding='utf-8'))
        if count:
            args.output.write_text(cleaned, encoding='utf-8')
            print(f'Removed {count} redundant GSHHS island context rings; ADM0 target and neighbors unchanged')


if __name__ == '__main__':
    main()
