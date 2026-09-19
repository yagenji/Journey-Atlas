#!/usr/bin/env python3
"""Temporary QA-only independent coastline overlay; NEVER production land geometry.

Fetch OpenStreetMap natural=coastline ways for Singapore and Macau, project raw
lines to the approved map canvas, and overlay them over a separate GSHHG preview.
Open coastline ways are not filled or closed into invented land polygons.
OSM data is ODbL; this diagnostic does not authorize production redistribution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

SVG = '{http://www.w3.org/2000/svg}'
ENDPOINTS = ('https://overpass-api.de/api/interpreter',
             'https://overpass.kumi.systems/api/interpreter')


def projection(bounds):
    w, s, e, n = bounds
    f = math.cos(math.radians((s + n) / 2))
    k = min(1200 / ((e - w) * f), 760 / (n - s))
    return f, k, (1200 - (e - w) * f * k) / 2, (760 - (n - s) * k) / 2


def checked_config(path):
    obj = json.loads(path.read_text(encoding='utf-8'))
    slug = obj.get('slug')
    if slug not in ('singapore', 'macau'):
        raise ValueError('Only the two held city-scale maps may be diagnosed')
    b = obj['map']['bounds']
    bounds = tuple(float(b[key]) for key in ('west', 'south', 'east', 'north'))
    if not all(map(math.isfinite, bounds)) or not (bounds[0] < bounds[2] and bounds[1] < bounds[3]):
        raise ValueError('Invalid source map bounds')
    return slug, bounds


def fetch_coast(bounds):
    w, s, e, n = bounds
    f, k, x, y = projection(bounds)
    bbox = (w-x/(f*k), s-(760-y-(n-s)*k)/k,
            e+(1200-x-(e-w)*f*k)/(f*k), n+y/k)
    west, south, east, north = bbox
    if not 0 < (east-west)*(north-south) < 0.5:
        raise ValueError('Unexpectedly large coastline request')
    q = f'[out:json][timeout:70];way["natural"="coastline"]({south:.7f},{west:.7f},{north:.7f},{east:.7f});out geom;'
    payload = urllib.parse.urlencode({'data': q}).encode('ascii')
    errors = []
    for endpoint in ENDPOINTS:
        try:
            req = urllib.request.Request(endpoint, data=payload,
                headers={'User-Agent': 'JourneyAtlasMapQA/1.0 (atlas.yagenji.com; preview only)',
                         'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=95) as response:
                raw = response.read(20_000_001)
            if len(raw) > 20_000_000:
                raise ValueError('Overpass response exceeds the 20 MB diagnostic limit')
            obj = json.loads(raw)
            if not isinstance(obj.get('elements'), list):
                raise ValueError('Overpass has no elements list')
            return obj, endpoint, hashlib.sha256(raw).hexdigest()
        except (OSError, ValueError, TimeoutError) as exc:
            errors.append(f'{endpoint}: {type(exc).__name__}: {str(exc)[:100]}')
    raise RuntimeError('; '.join(errors))


def overlay(svg_text, bounds, osm):
    root = ET.fromstring(svg_text)
    if root.get('viewBox') != '0 0 1200 760' or root.find(".//*[@id='geographic-context']") is None:
        raise ValueError('Requires separate canonical GSHHG preview')
    if root.find(".//*[@id='independent-coastline-diagnostic']") is not None:
        raise ValueError('Duplicate diagnostic overlay')
    w, s, e, n = bounds
    f, k, x, y = projection(bounds)
    segments, ways, points = [], 0, 0
    for way in osm['elements']:
        if way.get('type') != 'way' or way.get('tags', {}).get('natural') != 'coastline':
            continue
        drawn = []
        for point in way.get('geometry', []):
            if not isinstance(point, dict) or 'lon' not in point or 'lat' not in point:
                continue
            lon, lat = float(point['lon']), float(point['lat'])
            if not math.isfinite(lon) or not math.isfinite(lat):
                continue
            p = (round(x+(lon-w)*f*k, 2), round(y+(n-lat)*k, 2))
            if not drawn or drawn[-1] != p:
                drawn.append(p)
        if len(drawn) > 1:
            segments.append('M ' + ' L '.join(f'{a:.2f},{b:.2f}' for a, b in drawn))
            ways += 1
            points += len(drawn)
    if ways < 2 or points < 10:
        raise ValueError(f'Independent shoreline has insufficient data: {ways} ways, {points} points')
    g = ET.SubElement(root, SVG+'g', {'id': 'independent-coastline-diagnostic',
        'fill': 'none', 'stroke': '#ca2b40', 'stroke-width': '2', 'opacity': '0.9'})
    ET.SubElement(g, SVG+'path', {'d': ' '.join(segments)})
    return ET.tostring(root, encoding='utf-8'), ways, points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--country-json', required=True, type=Path)
    parser.add_argument('--preview-svg', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--osm-json', type=Path, help='Offline fixture only')
    args = parser.parse_args()
    slug, bounds = checked_config(args.country_json)
    if args.osm_json:
        data = args.osm_json.read_bytes()
        osm, endpoint, source_hash = json.loads(data), 'offline-fixture', hashlib.sha256(data).hexdigest()
    else:
        osm, endpoint, source_hash = fetch_coast(bounds)
    original = args.preview_svg.read_bytes()
    output_svg, ways, points = overlay(original.decode('utf-8'), bounds, osm)
    out = args.output_dir.resolve()
    if out == args.preview_svg.resolve().parent:
        raise ValueError('Diagnostic output cannot be written alongside source preview')
    out.mkdir(parents=True, exist_ok=True)
    (out / f'{slug}-osm-overlay.svg').write_bytes(output_svg)
    import cairosvg
    from PIL import Image
    png = out / f'{slug}-osm-overlay.png'
    cairosvg.svg2png(bytestring=output_svg, write_to=str(png), output_width=1200, output_height=760)
    with Image.open(png) as image:
        image.load()
        if image.size != (1200, 760):
            raise AssertionError('Incorrect diagnostic canvas size')
    report = {'slug': slug, 'source': 'OpenStreetMap coastline ways, ODbL, independent diagnostic only',
        'retrievedUtc': datetime.now(timezone.utc).isoformat(), 'endpoint': endpoint,
        'sourceSha256': source_hash, 'previewSha256': hashlib.sha256(original).hexdigest(),
        'overlaySha256': hashlib.sha256(output_svg).hexdigest(), 'ways': ways, 'points': points,
        'warning': 'Only raw independent coastlines were drawn, NOT land polygons or production geography.'}
    (out / f'{slug}-osm-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('COASTLINE_DIAGNOSTIC', json.dumps(report))


if __name__ == '__main__':
    main()
