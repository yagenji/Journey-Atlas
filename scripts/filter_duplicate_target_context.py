#!/usr/bin/env python3
"""Preview-only removal of duplicated target land from geographic context.

GSHHG surrounding context also contains the featured country itself. On small
islands a different coastline vintage produces pale wedges around the approved
silhouette. Exclude only context rings overwhelmingly covered by the target
land-gradient mask. Compound paths with holes are handled only when one
isolated landmass is almost entirely covered by a single approved target.
This migration-only adapter does not change the new-Country generator.
"""
from __future__ import annotations

from io import BytesIO
import re
from xml.etree import ElementTree as ET

import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
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


def _isolated_self_land_compound(path, approved_path):
    """Recognize one whole-island exterior plus holes, never shared mainlands.

    This is a conservative preview gate, not a coastline repair: another
    landmass, a nested island, an inset, or a distant mismatched ring fails
    closed rather than guessing which geography to erase.
    """
    if path.get('fill-rule') != 'evenodd' or any(path.get(k) is not None for k in ('transform', 'clip-path', 'data-map-context-region')):
        return 0
    if (approved_path.get('transform') or approved_path.get('clip-path') or approved_path.get('style')
            or approved_path.get('class') or not RING.fullmatch(approved_path.get('d', ''))):
        return 0
    d = path.get('d', '')
    parts = ['M ' + part.strip() for part in re.findall(r'M\s*([^M]+)', d)]
    if not 2 <= len(parts) <= 200 or not all(RING.fullmatch(part) for part in parts):
        return 0
    polygons = [Polygon([(float(x), float(y)) for x, y in POINT.findall(part)]) for part in parts]
    if any(not p.is_valid or p.is_empty for p in polygons):
        return 0
    depths = [sum(i != j and p.within(q) for j, q in enumerate(polygons)) for i, p in enumerate(polygons)]
    if depths.count(0) != 1 or any(depth not in (0, 1) for depth in depths):
        return 0
    # Render the entire even-odd compound, including lakes; do not inspect or
    # remove hole rings separately. No class/style/external geometry is used.
    safe_svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760"><path d="{d}" fill="white" fill-rule="evenodd"/></svg>'
    data = cairosvg.svg2png(bytestring=safe_svg.encode(), output_width=1200, output_height=760)
    with Image.open(BytesIO(data)) as image:
        image.load()
        footprint = np.asarray(image.convert('RGBA').getchannel('A')) >= 128
    approved_svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760"><path d="{approved_path.get("d")}" fill="white" fill-rule="{approved_path.get("fill-rule", "nonzero")}"/></svg>'
    with Image.open(BytesIO(cairosvg.svg2png(bytestring=approved_svg.encode(), output_width=1200, output_height=760))) as image:
        image.load()
        target = np.asarray(image.convert('RGBA').getchannel('A')) >= 128
    area = int(footprint.sum())
    if area < MIN_PIXELS or int((footprint & target).sum()) / area < 0.97:
        return 0
    # A small coast-vintage halo must be adjacent to the approved island.
    # Any detached / distant non-target land makes removal unsafe.
    expanded = np.asarray(Image.fromarray(target.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(23))) > 0
    if np.any(footprint & ~expanded):
        return 0
    return len(parts)


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
    # An isolated single-island compound is an alternative to simple rings,
    # not a generic way of erasing partially overlapping shared landmasses.
    compound = None
    if not candidates and len(context_paths) == 1:
        path = context_paths[0]
        approved = [p for p in root if p.tag == SVG + 'path' and p.get('fill') == 'url(#land)']
        if (parent.get(path) is not None and parent[path].get('id') == 'geographic-context'
                and len(approved) == 1):
            compound = (path, approved[0])
    if not candidates and compound is None:
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
        old = 'd="' + d + '"'
        if svg.count(old) != 1:
            raise ValueError('Context path is not unique; refusing SVG mutation')
        svg = svg.replace(old, 'd="' + ' '.join(retained) + '"', 1)
    if compound is not None:
        path, approved_path = compound
        removed = _isolated_self_land_compound(path, approved_path)
        if removed:
            old = 'd="' + path.get('d', '') + '"'
            if svg.count(old) != 1:
                raise ValueError('Context path is not unique; refusing SVG mutation')
            svg = svg.replace(old, 'd=""', 1)
            changed += removed
    ET.fromstring(svg)
    return svg, changed
