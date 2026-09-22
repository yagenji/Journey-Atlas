#!/usr/bin/env python3
"""Review-only Hong Kong/Shenzhen neighboring land from OSM coastline ways.

Fetch a dated ODbL source snapshot on a disposable runner. Never changes
production SVGs; a preview is not geographic approval.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image
from shapely.geometry import LineString, Point, box
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'
SEA = '<rect width="1200" height="760" fill="url(#sea)"/>'
OVERPASS = ('https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter')
FETCH = (22.02, 113.65, 22.72, 114.76)


def project(bounds):
    west, south, east, north = (bounds[k] for k in ('west', 'south', 'east', 'north'))
    factor = math.cos(math.radians((south + north) / 2))
    scale = min(1200 / ((east - west) * factor), 760 / (north - south))
    ox = (1200 - (east - west) * factor * scale) / 2
    oy = (760 - (north - south) * scale) / 2
    return lambda lon, lat: (ox + (lon - west) * factor * scale, oy + (north - lat) * scale)


def request_source():
    south, west, north, east = FETCH
    query = f'[out:json][timeout:150];way["natural"="coastline"]({south},{west},{north},{east});out geom;'
    post = urllib.parse.urlencode({'data': query}).encode()
    errors = []
    for endpoint in OVERPASS:
        try:
            with urllib.request.urlopen(urllib.request.Request(endpoint, data=post,
                    headers={'User-Agent': 'Journey-Atlas-geographic-QA/1.0'}), timeout=180) as response:
                raw = response.read(24_000_001)
            if len(raw) > 24_000_000:
                raise ValueError('Coastline source exceeds size guard')
            parsed = json.loads(raw)
            if len(parsed.get('elements', [])) < 30:
                raise ValueError('Incomplete Shenzhen/Hong Kong coast ways')
            return parsed, endpoint
        except Exception as exc:
            errors.append(f'{endpoint}: {exc!r}')
    raise RuntimeError('No verified coastline snapshot: ' + '; '.join(errors))


def land_faces(source, xy):
    viewport = box(0, 0, 1200, 760)
    raw = [LineString([xy(p['lon'], p['lat']) for p in w['geometry']])
           for w in source['elements'] if w.get('type') == 'way'
           and w.get('tags', {}).get('natural') == 'coastline'
           and len(w.get('geometry', [])) >= 2]
    segments = []
    for line in raw:
        if line.intersects(viewport):
            cropped = line.intersection(viewport)
            if cropped.geom_type == 'LineString':
                segments.append(cropped)
            elif cropped.geom_type == 'MultiLineString':
                segments.extend(cropped.geoms)
    if len(segments) < 5:
        raise RuntimeError('Unexpectedly little coastline inside target frame')
    faces = list(polygonize(unary_union([viewport.boundary, *segments])))
    if not faces:
        raise RuntimeError('No closed geographic faces')
    index = STRtree(faces)
    votes = [Counter() for _ in faces]
    for line in segments:
        for (x, y), (xx, yy) in zip(line.coords, line.coords[1:]):
            length = math.hypot(xx - x, yy - y)
            if length < 1e-5:
                continue
            mx, my = (x + xx) / 2, (y + yy) / 2
            epsilon = 0.0005
            for position, label in (((mx + (yy-y)*epsilon/length,
                                      my-(xx-x)*epsilon/length), 'land'),
                                    ((mx - (yy-y)*epsilon/length,
                                      my+(xx-x)*epsilon/length), 'sea')):
                point = Point(position)
                for candidate in index.query(point):
                    idx = int(candidate)
                    if faces[idx].covers(point):
                        votes[idx][label] += 1
    land = []
    for poly, vote in zip(faces, votes):
        if vote['land'] and vote['sea']:
            raise RuntimeError('Conflicting OSM coast orientation; never guess a land face')
        if vote['land']:
            land.append(poly)
    if not land:
        raise RuntimeError('No classified mainland coast')
    mainland_seed = Point(xy(114.10, 22.565))
    mainland = [poly for poly in land if poly.covers(mainland_seed)]
    if len(mainland) != 1:
        raise RuntimeError('Shenzhen mainland source component not identified uniquely')
    return mainland[0], len(raw), len(segments), len(faces)


def fmt_path(poly):
    polys = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
    parts = []
    for polygon in polys:
        if polygon.is_empty or polygon.area < 0.3:
            continue
        for ring in (polygon.exterior, *polygon.interiors):
            coords = [(round(x, 2), round(y, 2)) for x, y in ring.coords]
            coords = [pt for i, pt in enumerate(coords) if i == 0 or pt != coords[i-1]]
            if len(coords) >= 4:
                parts.append('M ' + ' L '.join(f'{x:.2f},{y:.2f}' for x, y in coords) + ' Z')
    if not parts:
        raise RuntimeError('Empty foreign mainland polygon')
    return ' '.join(parts)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--repo', type=Path, default=ROOT)
    cli.add_argument('--output-dir', type=Path, required=True)
    cli.add_argument('--source-json', type=Path, default=None)
    args = cli.parse_args()
    root = args.repo.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    config = json.loads((root/'data/countries/hong-kong.json').read_text())
    source = (root/config['map']['svg']).read_bytes()
    source_sha = hashlib.sha256(source).hexdigest()
    original = ET.fromstring(source)
    shapes = original.find('.//*[@id="land-shape"]')
    approved = [p.get('d') for p in shapes.iter(SVG+'path')]
    if source_sha != '1259c39687bdc062882664cb6310745354d4c8c97126342751ab2549fe81172f' or len(approved) != 18:
        raise RuntimeError('Approved Hong Kong source changed: re-review required')
    if args.source_json:
        raw = args.source_json.read_bytes()
        data = json.loads(raw)
        endpoint = 'pinned-offline-source'
    else:
        data, endpoint = request_source()
        raw = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        (out/'osm-coastline-ways.json').write_bytes(raw)
    xy = project(config['map']['bounds'])
    mainland, source_ways, used_segments, faces = land_faces(data, xy)
    path = fmt_path(mainland)
    approved_mask = 'M 0,0 L 1200,0 L 1200,760 L 0,760 Z ' + ' '.join(approved)
    clip = ('<clipPath id="reviewed-foreign-land-only" clipPathUnits="userSpaceOnUse">'
            '<path d="'+approved_mask+'" fill-rule="evenodd" clip-rule="evenodd"/>'
            '</clipPath>')
    text = source.decode()
    if text.count('</defs>') != 1 or text.count(SEA) != 1:
        raise RuntimeError('Unexpected approved Hong Kong SVG layout')
    text = text.replace('</defs>', clip+'</defs>', 1)
    note = ('OpenStreetMap natural=coastline ways, ODbL 1.0; '
            'Hong Kong and Shenzhen mainland review only; '
            'source SHA-256 '+hashlib.sha256(raw).hexdigest()+'; '
            'https://www.openstreetmap.org/copyright')
    context = ('<g id="geographic-context" clip-path="url(#reviewed-foreign-land-only)">'
               '<desc>'+note+'</desc><path d="'+path+'" fill="#e4e0ce" '
               'fill-rule="evenodd" stroke="#b6bbaf" stroke-width="1"/>'
               '</g>')
    text = text.replace(SEA, SEA+'\n'+context, 1)
    parsed = ET.fromstring(text)
    updated = [p.get('d') for p in parsed.find('.//*[@id="land-shape"]').iter(SVG+'path')]
    if updated != approved or parsed.get('viewBox') != '0 0 1200 760':
        raise RuntimeError('Approved Hong Kong paths/canvas modified')
    png = cairosvg.svg2png(bytestring=text.encode(), output_width=1200, output_height=760)
    with Image.open(io.BytesIO(png)) as im:
        im.load()
        if im.size != (1200,760):
            raise RuntimeError('Bad full-size PNG')
    (out/'hong-kong.svg').write_text(text)
    (out/'hong-kong.png').write_bytes(png)
    report = {'qaStatus':'HOLD: independent full-size coastline and source-vintage QA required',
              'source_endpoint':endpoint,'retrievedAt':datetime.now(timezone.utc).isoformat(),
              'sourceSha256':hashlib.sha256(raw).hexdigest(),'approvedSvgSha256':source_sha,
              'ways':source_ways,'segments':used_segments,'faces':faces,
              'mainlandSourceAreaSvgPx2':round(mainland.area,2),
              'svgSha256':hashlib.sha256(text.encode()).hexdigest(),
              'targetPathsPreserved':18,'decodedSize':[1200,760]}
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
