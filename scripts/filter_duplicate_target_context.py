#!/usr/bin/env python3
"""Preview-only removal of duplicated target land from geographic context.

GSHHG surrounding context also contains the featured country itself. On small
islands a different coastline vintage produces pale wedges around the approved
silhouette. Exclude only context rings overwhelmingly covered by the target
land-gradient mask. Unrecognized compound paths and holes remain untouched.
This migration-only adapter does not change the new-Country generator.
"""
from __future__ import annotations

from io import BytesIO
import re
from xml.etree import ElementTree as ET

import cairosvg
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon

SVG = '{http://www.w3.org/2000/svg}'
GRADIENT = re.compile(r'<linearGradient\b(?=[^>]*\bid="land")[^>]*>.*?</linearGradient>', re.DOTALL)
COLOR = re.compile(r'stop-color="#[0-9a-fA-F]{6}"')
RING = re.compile(r'M\s+-?(?:\d+(?:\.\d*)?|\.\d+),-?(?:\d+(?:\.\d*)?|\.\d+)(?:\s+L\s+-?(?:\d+(?:\.\d*)?|\.\d+),-?(?:\d+(?:\.\d*)?|\.\d+)){2,}\s+Z\s*\Z')
POINT = re.compile(r'(-?(?:\d+(?:\.\d*)?|\.\d+)),(-?(?:\d+(?:\.\d*)?|\.\d+))')
THRESHOLD = 0.80
MIN_PIXELS = 250


def _approved_target_mask(svg: str):
    match = GRADIENT.search(svg)
    if not match:
        return None
    highlighted, count = COLOR.subn('stop-color="#ff0000"', match.group())
    if count < 2:
        return None
    recolored = svg[:match.start()] + highlighted + svg[match.end():]
    data = cairosvg.svg2png(bytestring=recolored.encode(), output_width=1200, output_height=760)
    with Image.open(BytesIO(data)) as image:
        image.load()
        pixels = np.asarray(image.convert('RGB'))
    mask = (pixels[:, :, 0] > 230) & (pixels[:, :, 1] < 60) & (pixels[:, :, 2] < 60)
    return mask if int(mask.sum()) >= MIN_PIXELS else None


def _rings(path_data: str):
    parts = ['M ' + part.strip() for part in re.findall(r'M\s*([^M]+)', path_data)]
    if not parts or not all(RING.fullmatch(part) for part in parts):
        return None
    polygons = []
    for part in parts:
        coords = [(float(x), float(y)) for x, y in POINT.findall(part)]
        polygon = Polygon(coords)
        if not polygon.is_valid or polygon.is_empty:
            return None
        polygons.append(polygon)
    if len(polygons) > 200:
        return None
    # Hole rings must never be removed independently of their exterior.
    for idx, polygon in enumerate(polygons):
        if any(other.within(polygon) for j, other in enumerate(polygons) if j != idx):
            return None
    return parts


def remove_target_land_context(svg: str):
    """Return (preview SVG, removed ring count); leave approved paths intact."""
    root = ET.fromstring(svg)
    if root.tag != SVG + 'svg' or root.get('viewBox') != '0 0 1200 760':
        raise ValueError('Only 1200x760 SVG can be assessed')
    parent = {child: node for node in root.iter() for child in node}
    context_paths = []
    for path in root.iter(SVG + 'path'):
        if path.get('data-map-context-region') is not None:
            context_paths.append(path)
            continue
        node = parent.get(path)
        while node is not None:
            if node.get('id') == 'geographic-context':
                context_paths.append(path)
                break
            node = parent.get(node)
    if not context_paths:
        return svg, 0
    candidates = [(path, _rings(path.get('d', ''))) for path in context_paths if path.get('d')]
    candidates = [(path, rings) for path, rings in candidates if rings is not None]
    if not candidates:
        return svg, 0
    target = _approved_target_mask(svg)
    if target is None:
        return svg, 0
    changed = 0
    for path, rings in candidates:
        d = path.get('d', '')
        retained = []
        for ring in rings:
            coordinates = [(float(x), float(y)) for x, y in POINT.findall(ring)]
            image = Image.new('1', (1200, 760))
            ImageDraw.Draw(image).polygon(coordinates, fill=1)
            footprint = np.asarray(image, dtype=bool)
            area = int(footprint.sum())
            if area >= MIN_PIXELS and float((footprint & target).sum()) / area >= THRESHOLD:
                changed += 1
            else:
                retained.append(ring)
        if len(retained) == len(rings):
            continue
        # Substitute the unique generated context attribute, never an original path.
        old = 'd="' + d + '"'
        if svg.count(old) != 1:
            raise ValueError('Context path is not unique; refusing SVG mutation')
        svg = svg.replace(old, 'd="' + ' '.join(retained) + '"', 1)
    ET.fromstring(svg)
    return svg, changed
