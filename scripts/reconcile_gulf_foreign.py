#!/usr/bin/env python3
"""Protect approved Qatar/Kuwait outlines when staging foreign Gulf land.

Migration-only: source-pinned correction of overlapping *generated* land.
Never alters an approved path, marker, or geography beyond the verified source.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import Polygon
from shapely.ops import unary_union

NS = '{http://www.w3.org/2000/svg}'
PINNED = {
    'qatar': {
        'source': '917fd11a5573a39f548e269c7e5a356fa0227666',
        'target': '4b52e0846f789da8fa8587457b2bb6d566f17f93f81203f032f81d62e47a38bd',
        'context': '1eb8ae7f479dd628743c4af97ad244660dcd056dce41b745af7d15beb5ab1d88',
        'attribute': 'data-map-context-legacy="national-base"',
        'count': 16,
    },
    'kuwait': {
        'source': '00ff2de0134c32372434a55aeee1e308c37d9a4e',
        'target': '0a48897f3bd05acf177440cd6f4b67edf1ab7dac34e1df73bbd2bb31355e3ced',
        'context': '15a39c76a352f102c37be942587e77d06c3bac0617ba856ee2a91e67a92cc553',
        'attribute': 'data-map-context-region="country"',
        'count': 6,
    }
}


def _source_blob(source):
    data = Path(source).read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def _rings(data):
    return [ring.strip() for ring in re.split(r'(?=\bM\s)', data) if ring.strip()]


def _polygon(data):
    points = [tuple(map(float, point)) for point in re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', data)]
    polygon = Polygon(points)
    if len(points) < 4 or not polygon.is_valid or polygon.area <= 1:
        raise ValueError('Unreviewed or invalid map context ring')
    return polygon


def reconcile(svg: str, source: Path, slug: str, resolution: str) -> str:
    """Subtract only already-approved target shape from verified foreign context."""
    if slug not in PINNED or resolution != 'i':
        raise ValueError('Unreviewed Gulf map or source resolution')
    pinned = PINNED[slug]
    if _source_blob(source) != pinned['source']:
        raise ValueError('Approved national source advanced: fresh geographic QA needed')
    before = ET.fromstring(svg)
    paths = [p for p in before.iter(NS+'path') if p.get('fill') == 'url(#land)']
    if (before.get('viewBox') != '0 0 1200 760' or len(paths) != 2
            or hashlib.sha256(paths[0].get('d', '').encode()).hexdigest() != pinned['target']):
        raise ValueError('Unreviewed national geometry or canvas')
    target = paths[0].get('d')
    context = before.find('.//*[@id="geographic-context"]')
    if context is None or len([p for p in context.iter(NS+'path')]) != 1:
        raise ValueError('Unexpected surrounding land structure')
    path = next(context.iter(NS+'path'))
    candidate = path.get('d', '')
    if (pinned['attribute'].split('=')[0] not in path.attrib
            or hashlib.sha256(candidate.encode()).hexdigest() != pinned['context']):
        raise ValueError('Generated context/source changed: no automatic coast edit')
    rings = _rings(candidate)
    if len(rings) != pinned['count']:
        raise ValueError('Generated context ring count changed')

    if slug == 'kuwait':
        # Four whole generated islands overlap the approved Kuwaiti national
        # islands by 100%, 100%, 99.64% and 100% (SVG polygon geometry).
        # Leave the sixth ring: it is NOT verified as domestic.
        approved = unary_union([_polygon(ring) for ring in _rings(target)])
        for ring in rings[1:5]:
            polygon = _polygon(ring)
            if polygon.intersection(approved).area / polygon.area < 0.995:
                raise ValueError('Kuwaiti self-island source no longer matches')
        replacement = ' '.join([rings[0], rings[5]])
    else:
        # Qatar is on a shared mainland: deleting the GSHHG component would
        # delete real Saudi territory. Exclude the protected national target.
        approved = _polygon(target)
        if abs(_polygon(rings[0]).intersection(approved).area - approved.area) > 1:
            raise ValueError('Qatar/Saudi land topology unexpectedly changed')
        replacement = candidate

    mask_id = 'map-context-reviewed-national-exclusion'
    if mask_id in svg or svg.count('</defs>') != 1:
        raise ValueError('Unexpected clipping definitions')
    clip = ('<clipPath id="'+mask_id+'" clipPathUnits="userSpaceOnUse">'
            '<path d="M 0,0 L 1200,0 L 1200,760 L 0,760 Z '
            + target + '" fill-rule="evenodd" clip-rule="evenodd"/>'
            '</clipPath>')
    svg = svg.replace('</defs>', clip+'</defs>', 1)
    if slug == 'kuwait':
        old = 'd="'+candidate+'"'
        if svg.count(old) != 1:
            raise ValueError('Ambiguous context geometry')
        svg = svg.replace(old, 'd="'+replacement+'"', 1)
    old_group = '<g id="geographic-context"'
    if svg.count(old_group) != 1:
        raise ValueError('Unexpected context nesting')
    note = ('<desc>Foreign Gulf land: existing GSHHG intermediate-resolution '
            'source; only the unchanged approved national silhouette is '
            'subtracted from generated context. No new coastline.</desc>')
    svg = svg.replace(old_group,
                      '<g id="geographic-context" clip-path="url(#'+mask_id+')"', 1)
    svg = svg.replace('clip-path="url(#'+mask_id+')">',
                      'clip-path="url(#'+mask_id+')">'+note, 1)
    after = ET.fromstring(svg)
    if ([dict(p.attrib) for p in after.iter(NS+'path') if p.get('fill') == 'url(#land)']
            != [dict(p.attrib) for p in paths]):
        raise ValueError('Approved national path modified')
    return svg
