#!/usr/bin/env python3
"""Remove only independently classified Salvadoran self-land from staged context.

The production SVG adds seven missing domestic island rings as a second target.
GSHHG still supplies the neighboring mainland and genuinely foreign Gulf islands
to the preview. This module never invents shorelines or touches target paths.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import Polygon

SVG = '{http://www.w3.org/2000/svg}'
SOURCE_SHA = '28290dca64d3f04a3bc25e5ef1ac7f871d295eb239d21e8b4baf4fcb9eae44dc'
RAW_SHA = 'f6db6273cb5dd97de10ab783e8f415d3552da6035f8cc98c907d66d505ad223f'
ORIGINAL_TARGET_SHA = '8bb899b75af9b1563788a8ee25acfd685ff5d972133a5f3fcd1eeffe7eb4fab8'
ISLAND_TARGET_SHA = '76e90ff71a8128eef75d6b43c31a8e4735b702f95f146472794a419d6c25e0f6'
CONTEXT_SHA = 'f40407c6b5601bea95ec8e52a6514974dc2297684c3a004d48d540014d7ce017'
DOMESTIC_NEW = (0, 1, 2, 3, 4, 5, 19)
DOMESTIC_OVERLAP = (16, 17)
REMOVE = set(DOMESTIC_NEW + DOMESTIC_OVERLAP)
POINTS = re.compile(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)')
RINGS = re.compile(r'M\s*[^M]+?Z')


def sha(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def polygon(ring: str) -> Polygon:
    result = Polygon([(float(x), float(y)) for x, y in POINTS.findall(ring)])
    if result.is_empty or not result.is_valid:
        raise ValueError('Invalid source island geometry')
    return result


def reconcile(svg: str, source: Path, resolution: str = 'i') -> str:
    if resolution != 'i' or hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Unreviewed El Salvador source/resolution')
    if sha(svg) != RAW_SHA:
        raise ValueError('Unreviewed generated El Salvador candidate')
    root = ET.fromstring(svg)
    targets = [p for p in root.iter(SVG + 'path') if p.get('fill') == 'url(#land)']
    if root.get('viewBox') != '0 0 1200 760' or len(targets) != 2:
        raise ValueError('Approved El Salvador targets changed')
    if [sha(p.get('d', '')) for p in targets] != [ORIGINAL_TARGET_SHA, ISLAND_TARGET_SHA]:
        raise ValueError('Protected El Salvador geometry changed')
    context = root.find(f".//{SVG}g[@id='geographic-context']/{SVG}path")
    if context is None or sha(context.get('d', '')) != CONTEXT_SHA:
        raise ValueError('GSHHG foreign context changed')
    rings = RINGS.findall(context.get('d', ''))
    if len(rings) != 22:
        raise ValueError('Unexpected El Salvador source ring count')
    expected_domestic = RINGS.findall(targets[1].get('d', ''))
    if [rings[i] for i in DOMESTIC_NEW] != expected_domestic:
        raise ValueError('New protected islands differ from source coastline')
    protected = [polygon(r) for r in RINGS.findall(targets[0].get('d', ''))]
    for index in DOMESTIC_OVERLAP:
        footprint = polygon(rings[index])
        fraction = sum(footprint.intersection(p).area for p in protected) / footprint.area
        if fraction < 0.85:
            raise ValueError('Self-island overlap changed; needs individual review')
    retained = ' '.join(r for i, r in enumerate(rings) if i not in REMOVE)
    old = 'd="' + context.get('d', '') + '"'
    if svg.count(old) != 1:
        raise ValueError('Context path is not unique')
    result = svg.replace(old, 'd="' + retained + '"', 1)
    ET.fromstring(result)
    return result
