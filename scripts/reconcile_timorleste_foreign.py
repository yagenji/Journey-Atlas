#!/usr/bin/env python3
"""Build source-aligned Indonesian context for the Timor-Leste migration preview.

The approved Timor-Leste SVG uses Natural Earth 1:10m for the western land
border/Oecusse and GSHHS for its coast.  Generic GSHHG context therefore mixes
coast/border vintages on the shared Timor island.  This migration-only adapter
uses the pinned sibling Indonesia polygon from the same Natural Earth 4.1.0
collection for foreign land, then clips it against the exact approved target.
It never changes the protected Timor-Leste path.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import box, shape

import add_country_map_context as maps

SVG = '{http://www.w3.org/2000/svg}'
SOURCE_GIT_BLOB = 'c108c5336a385e029e36f979abc4e874396ebfd8'
FIXTURE_GIT_BLOB = '7f6ec78f4d397d4c23b28ae1ddd222ac7458f687'
SOURCE_COMMIT = '5120290da88f3f205f74aa55f3c8fa1f19d1bc8b'
SOURCE_COMPONENTS = [1, 10, 129, 131, 135]
EXPECTED_BOUNDS = {
    'north': -8,
    'south': -9.58,
    'west': 123.95,
    'east': 127.42,
}
CLIP_ID = 'timorleste-foreign-only'


def git_blob_sha(raw: bytes) -> str:
    header = f'blob {len(raw)}\0'.encode('ascii')
    return hashlib.sha1(header + raw).hexdigest()


def target_paths(root):
    return [node for node in root.iter(SVG + 'path') if node.get('fill') == 'url(#land)']


def reconcile(source_text: str, source: Path, country_file: Path, fixture: Path,
              resolution: str = 'i') -> str:
    if resolution != 'i':
        raise ValueError('Timor-Leste migration QA is pinned to the reviewed intermediate-resolution workflow')
    if git_blob_sha(source.read_bytes()) != SOURCE_GIT_BLOB:
        raise ValueError('Unreviewed Timor-Leste approved SVG')
    if git_blob_sha(fixture.read_bytes()) != FIXTURE_GIT_BLOB:
        raise ValueError('Unreviewed Timor-Leste Indonesia source fixture')

    country = json.loads(country_file.read_text(encoding='utf-8'))
    config = country['map']
    if config.get('bounds') != EXPECTED_BOUNDS:
        raise ValueError('Timor-Leste map bounds changed')
    if 'Natural Earth 1:10m' not in config.get('source', ''):
        raise ValueError('Timor-Leste approved source identity changed')

    payload = json.loads(fixture.read_text(encoding='utf-8'))
    props = payload.get('properties', {})
    if (props.get('sourceCommit') != SOURCE_COMMIT
            or props.get('naturalEarthVersion') != '4.1.0'
            or props.get('sourceComponentIndices') != SOURCE_COMPONENTS
            or props.get('license') != 'Natural Earth public domain'):
        raise ValueError('Timor-Leste Indonesia fixture provenance changed')

    bounds = tuple(float(config['bounds'][key]) for key in ('west', 'south', 'east', 'north'))
    foreign = shape(payload['geometry']).intersection(box(*maps.canvas_bounds(bounds)))
    if foreign.is_empty or not foreign.is_valid:
        raise ValueError('Invalid/empty Timor-Leste Indonesian context')
    context_path = maps.make_context_path(foreign, bounds, 0.003)
    if not context_path:
        raise ValueError('Timor-Leste Indonesian context path is empty')

    original = ET.fromstring(source_text)
    approved = target_paths(original)
    if original.get('viewBox') != '0 0 1200 760' or len(approved) != 1:
        raise ValueError('Unexpected Timor-Leste SVG structure')
    target_d = approved[0].get('d', '')
    if not target_d:
        raise ValueError('Missing Timor-Leste protected target geometry')

    result = maps.add_context(source_text, bounds, context_path, resolution)
    old_comment = '<!-- Geographic context: GSHHS via Basemap; resolution=i; WGS84; canvas-fit bounds. -->'
    source_note = (
        '<!-- Geographic context: Indonesia from Natural Earth 1:10m v4.1.0 via '
        'LonnyGomes/CountryGeoJSONCollection IDN.geojson commit ' + SOURCE_COMMIT +
        '; selected source components 1,10,129,131,135; public domain; '
        'approved Timor-Leste target unchanged. -->'
    )
    if result.count(old_comment) != 1:
        raise ValueError('Unexpected generated context provenance marker')
    result = result.replace(old_comment, source_note, 1)

    clip = (
        '<clipPath id="' + CLIP_ID + '" clipPathUnits="userSpaceOnUse">'
        '<path d="M 0,0 H 1200 V 760 H 0 Z ' + target_d +
        '" fill-rule="evenodd"/></clipPath>'
    )
    if result.count('</defs>') != 1:
        raise ValueError('Unexpected Timor-Leste defs structure')
    result = result.replace('</defs>', clip + '</defs>', 1)
    marker = '<g id="geographic-context">'
    if result.count(marker) != 1:
        raise ValueError('Unexpected Timor-Leste context group')
    result = result.replace(marker, '<g id="geographic-context" clip-path="url(#' + CLIP_ID + ')">', 1)

    rendered = ET.fromstring(result)
    if [node.get('d') for node in target_paths(rendered)] != [target_d]:
        raise ValueError('Protected Timor-Leste target changed')
    context = rendered.find(".//*[@id='geographic-context']")
    if context is None or context.get('clip-path') != f'url(#{CLIP_ID})':
        raise ValueError('Timor-Leste exact target exclusion missing')
    return result
