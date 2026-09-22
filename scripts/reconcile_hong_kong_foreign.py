"""Source-pinned Hong Kong/Shenzhen neighbor reconciliation for legacy maps only.

The coastline is derived from a dated OSM natural=coastline snapshot; only the
mainland component is shown, not an invented inland political border. The
original 18 approved land-only paths and all Country JSON stay byte identical.
"""
from __future__ import annotations
import base64
import hashlib
import re
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'
APPROVED_SHA = '1259c39687bdc062882664cb6310745354d4c8c97126342751ab2549fe81172f'
RAW_CONTEXT_SHA = '270fbe81e517c5e59b8627cefa1a5007f4bbbf09898b9a8233c2a3a3686eaf08'
PINNED_MAINLAND_SHA = 'd24687d3784f5d032cadd42d6cd359e86eaf697926358c4638a1b36fb0b2e3f9'
OSM_SNAPSHOT_SHA = 'e573259c14d2b016bbe762c4fd3c46877cd65b5e256fb2e0ef45489448285b7d'
DATA_PATH = Path(__file__).resolve().parents[1] / 'assets/images/hong-kong/shenzhen-osm-mainland-v1.b85'


def pinned_mainland_path() -> str:
    """Decode signed delta/LEB128 0.1-SVG-pixel vertices from pinned ODbL asset."""
    packed = DATA_PATH.read_text(encoding='ascii').strip()
    if not packed or len(packed) != 4480:
        raise ValueError('Pinned Shenzhen vector missing or altered')
    payload = zlib.decompress(base64.b85decode(packed))
    values = []
    offset = 0
    while offset < len(payload):
        value = shift = 0
        while True:
            if offset >= len(payload) or shift > 28:
                raise ValueError('Invalid pinned Shenzhen delta geometry')
            octet = payload[offset]
            offset += 1
            value |= (octet & 127) << shift
            if not octet & 128:
                break
            shift += 7
        values.append((value >> 1) ^ -(value & 1))
    if len(values) != 3884:
        raise ValueError('Pinned Shenzhen vertex count changed')
    x = y = 0
    points = []
    for dx, dy in zip(values[::2], values[1::2]):
        x += dx
        y += dy
        if not (0 <= x <= 12000 and 0 <= y <= 7600):
            raise ValueError('Shenzhen coast leaves reviewed viewport')
        points.append((x / 10, y / 10))
    if points[0] != points[-1]:
        raise ValueError('Shenzhen source mainland is not closed')
    path = 'M ' + ' L '.join(f'{xx:.1f},{yy:.1f}' for xx, yy in points) + ' Z'
    if hashlib.sha256(path.encode()).hexdigest() != PINNED_MAINLAND_SHA:
        raise ValueError('Shenzhen mainland geometry hash mismatch')
    return path


def reconcile(svg: str, source_path: Path, resolution: str) -> str:
    if resolution != 'i' or hashlib.sha256(source_path.read_bytes()).hexdigest() != APPROVED_SHA:
        raise ValueError('Approved Hong Kong SVG or source resolution changed')
    source = ET.fromstring(source_path.read_bytes())
    target = ET.fromstring(svg)
    src_group = source.find('.//*[@id="land-shape"]')
    dst_group = target.find('.//*[@id="land-shape"]')
    if src_group is None or dst_group is None or target.get('viewBox') != '0 0 1200 760':
        raise ValueError('Approved HK path/layout or canvas changed')
    before = [dict(p.attrib) for p in src_group.iter(NS + 'path')]
    after = [dict(p.attrib) for p in dst_group.iter(NS + 'path')]
    if len(before) != 18 or before != after or any(not p.get('d') for p in before):
        raise ValueError('Protected Hong Kong land paths are not unchanged')
    context = target.find('.//*[@id="geographic-context"]')
    source_context = list(context.iter(NS + 'path')) if context is not None else []
    if len(source_context) != 1 or hashlib.sha256(source_context[0].get('d', '').encode()).hexdigest() != RAW_CONTEXT_SHA:
        raise ValueError('Existing HK GSHHG context changed: re-review geography')
    old = source_context[0].get('d')
    new = pinned_mainland_path()
    if svg.count('d="' + old + '"') != 1 or svg.count('</defs>') != 1:
        raise ValueError('Unexpected HK context SVG markup')
    # Exclude all original approved HK land from added foreign mainland, keeping
    # contiguous Shenzhen land where the independent OSM coastline supports it.
    clip = ('<clipPath id="hong-kong-foreign-only" clipPathUnits="userSpaceOnUse">'
            '<path fill-rule="evenodd" clip-rule="evenodd" d="'
            'M 0,0 L 1200,0 L 1200,760 L 0,760 Z '
            + ' '.join(p['d'] for p in before) + '"/></clipPath>')
    output = svg.replace('</defs>', clip + '</defs>', 1)
    group = '<g id="geographic-context">'
    note = ('<desc>Shenzhen and Pearl River Delta mainland coast: OpenStreetMap '
            'natural=coastline, contributors, ODbL 1.0; Overpass source snapshot '
            'SHA-256 ' + OSM_SNAPSHOT_SHA + '; WGS84; 0.6 SVG-px source-line '
            'simplification, fixed 1200x760 projection. Approved Hong Kong '
            'national paths unchanged. https://www.openstreetmap.org/copyright</desc>')
    if output.count(group) != 1:
        raise ValueError('HK context group changed')
    output = output.replace(group, group + note, 1)
    output = output.replace('d="' + old + '"',
                            'clip-path="url(#hong-kong-foreign-only)" d="' + new + '"', 1)
    checked = ET.fromstring(output)
    checked_group = checked.find('.//*[@id="land-shape"]')
    if [dict(p.attrib) for p in checked_group.iter(NS + 'path')] != before:
        raise ValueError('HK national silhouette changed during neighbor patch')
    return output
