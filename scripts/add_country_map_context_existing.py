#!/usr/bin/env python3
"""Dispatch preview generation for existing approved Country maps.

Canonical layouts use add_country_map_context.py. A small reviewed set of historic
SVG layouts uses the migration-only legacy adapter. This script never overwrites
production assets; callers must provide a new output path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import add_country_map_context_legacy as legacy
from filter_duplicate_target_context import remove_target_land_context

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = '{http://www.w3.org/2000/svg}'


def reconcile_reviewed_bahrain_hawar(svg: str, resolution: str) -> str:
    """Keep verified Qatar land, not the GSHHG duplicates of Bahrain's Hawar.

    Native 1200×760 source reconciliation compared all five Hawar GSHHG rings
    with the approved Qatar national path transformed using both Country maps'
    unchanged WGS84 projection/rects. Only rings 1–2 match Qatar: Hausdorff
    distance <=0.21 SVG px and >99.9% polygon overlap. Rings 3–5 do not touch
    Qatar and overlap the approved Hawar shapes (77%, 68%, 12% respectively).
    Exact source/path checks deliberately fail closed if the geometry changes;
    this does NOT authorize editing either country's approved national paths.
    """
    if resolution != 'i':
        raise ValueError('Reviewed Hawar geometry requires intermediate GSHHG resolution')
    digest = lambda value: hashlib.sha256(value.encode('utf-8')).hexdigest()
    qatar = ET.fromstring((ROOT / 'assets/images/qatar/map-atlas-v1.svg').read_text(encoding='utf-8'))
    qatar_land = [p for p in qatar.iter(SVG_NS + 'path') if p.get('fill') == 'url(#land)']
    if (len(qatar_land) != 2 or digest(qatar_land[0].get('d', ''))
            != '4b52e0846f789da8fa8587457b2bb6d566f17f93f81203f032f81d62e47a38bd'):
        raise ValueError('Approved Qatar source changed; recheck Hawar land attribution')
    original = ET.fromstring(svg)
    approved = [p.get('d') for p in original.iter(SVG_NS + 'path') if p.get('fill') == 'url(#land)']
    if (len(approved) != 2 or digest(approved[1])
            != '76260d123f7ff16fa79cb47d81fe6f5363730a77b3592f700e30af17b79e501a'):
        raise ValueError('Approved Bahrain Hawar source changed; recheck geometry')
    pattern = re.compile(r'(<path\s+data-map-context-legacy="hawar"\s+d=")([^"]+)("[^>]*/>)')
    matches = list(pattern.finditer(svg))
    if (len(matches) != 1 or digest(matches[0].group(2))
            != 'fd53b089230739e2a8b38670510635cd4762001c1df28bf6cea21e7adba522ac'):
        raise ValueError('Generated Hawar context changed; independent geographic review needed')
    rings = [part for part in re.split(r'(?=\bM\s)', matches[0].group(2)) if part.strip()]
    verified_qatar = (
        '148f9e7f1adf9f6f7cb2e9a094529822c419b3358783a57046ca05276bda0c0d',
        'fc1b95a745eabc293ffe4a3241daeaca0ff4afc222b39f5afd5cc5c1f5f0f036',
    )
    if len(rings) != 5 or tuple(digest(ring) for ring in rings[:2]) != verified_qatar:
        raise ValueError('Hawar foreign land no longer matches reviewed Qatar source')
    # Replace only generated context's path data, never the national shapes.
    reviewed = svg[:matches[0].start(2)] + ''.join(rings[:2]).strip() + svg[matches[0].end(2):]
    changed = ET.fromstring(reviewed)
    after = [p.get('d') for p in changed.iter(SVG_NS + 'path') if p.get('fill') == 'url(#land)']
    if after != approved:
        raise ValueError('Reviewed Hawar context changed an approved national path')
    return reviewed


def frame_unframed_region_context(svg: str, regions: list[dict] | None) -> str:
    """Frame clipped neighboring land only when region geometry matches JSON.

    Migration-only presentation: preserve approved paths and existing inset
    treatments. Each frame marks the actual context viewport, not a border.
    """
    if not regions or len(regions) < 2 or 'id="geographic-context"' not in svg:
        return svg
    root = ET.fromstring(svg)
    if not root.get("data-map-projection", "").startswith("multi-region-"):
        return svg
    ns = "{http://www.w3.org/2000/svg}"
    if any(el.tag == ns + "rect" and el.get("stroke") not in (None, "", "none")
           for el in root.iter()):
        return svg  # Preserve existing U.S. and Kuwait inset frames.
    context = root.find(".//*[@id='geographic-context']")
    if context is None:
        return svg
    paths = [el for el in context.iter(ns + "path")
             if el.get("data-map-context-region") is not None]
    if not paths:
        return svg  # Legacy composite paths do not expose individual region clips.
    expected = {item["id"] for item in regions}
    drawn = [el.get("data-map-context-region") for el in paths]
    if (len(expected) != len(regions) or len(paths) != len(regions)
            or set(drawn) != expected):
        raise ValueError("Unframed multi-region context/clip IDs do not match Country JSON")
    clips = [el for el in root.iter(ns + "clipPath")]
    outlines = []
    for region in regions:
        identifier = region["id"]
        rect = region["rect"]
        x, y, w, h = (float(rect[k]) for k in ("x", "y", "width", "height"))
        if not (0 <= x < 1200 and 0 <= y < 760 and w > 0 and h > 0
                and x + w <= 1200 and y + h <= 760):
            raise ValueError("Region frame outside 1200×760 canvas")
        clip_id = f"map-context-clip-{identifier}"
        path = next(el for el in paths if el.get("data-map-context-region") == identifier)
        matched = [el for el in clips if el.get("id") == clip_id]
        if (path.get("clip-path") != f"url(#{clip_id})" or len(matched) != 1
                or len(matched[0]) != 1 or matched[0][0].tag != ns + "rect"):
            raise ValueError("Generated region context is not clipped to its declared viewport")
        clip_rect = matched[0][0]
        keys = ("x", "y", "width", "height")
        clip_values = [float(clip_rect.get(k, "nan")) for k in keys]
        if (not all(math.isfinite(value) for value in clip_values)
                or any(abs(actual - float(rect[key])) > 0.01
                       for actual, key in zip(clip_values, keys))):
            raise ValueError("Generated region clip rectangle does not match Country JSON")
        outlines.append(
            f'<rect data-map-context-frame="{identifier}" '
            f'x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="5" '
            'fill="none" stroke="#879b9b" stroke-width="1.5" '
            'stroke-dasharray="5 5" opacity=".7"/>'
        )
    if svg.count("</svg>") != 1:
        raise ValueError("Unexpected SVG closing tag")
    result = svg.replace("</svg>",
                         '<g id="geographic-context-region-frames">'
                         + "".join(outlines) + "</g></svg>")
    ET.fromstring(result)
    return result


def remove_reviewed_portugal_ocean_self_land(svg: str, config: dict, source: Path, resolution: str) -> str:
    """Discard only duplicate own-island GSHHG paths in two ocean-only insets.

    The fixed WGS84 viewports include the Portuguese Azores and Madeira islands,
    not foreign land. Native-size mask review found the added inset context
    overlaps the approved islands (Azores 747/781 px; Madeira 105/153 px);
    the remainder is a source-vintage halo, not independently verified land.
    Keep all original target paths, mainland Spain context and three inset frames.
    This historic-map migration correction fails closed on source/bounds changes.
    """
    original = source.read_bytes()
    git_blob = hashlib.sha1(f'blob {len(original)}\0'.encode() + original).hexdigest()
    if git_blob != '99af7a02646ec33a5ebc093f64bc13edeaaa8646' or resolution != 'i':
        raise ValueError('Portugal approved source or GSHHG resolution changed; re-review ocean insets')
    regions = config.get('map', {}).get('regions') or []
    expected = {
        'mainland': ({'north': 42.3, 'south': 36.8, 'west': -9.7, 'east': -6},
                     {'x': 520, 'y': 35, 'width': 430, 'height': 690}),
        'azores': ({'north': 40, 'south': 36.7, 'west': -31.5, 'east': -24.4},
                   {'x': 40, 'y': 80, 'width': 380, 'height': 260}),
        'madeira': ({'north': 33.2, 'south': 32.4, 'west': -17.4, 'east': -15.6},
                    {'x': 95, 'y': 500, 'width': 300, 'height': 170}),
    }
    if len(regions) != 3 or {r['id']: (r['bounds'], r['rect']) for r in regions} != expected:
        raise ValueError('Portugal region geography changed; review against approved source')
    before = ET.fromstring(svg)
    if before.get('viewBox') != '0 0 1200 760':
        raise ValueError('Portugal map canvas changed')
    approved = [dict(p.attrib) for p in before.iter(SVG_NS + 'path') if p.get('fill') == 'url(#land)']
    if len(approved) != 15:
        raise ValueError('Portugal approved national paths changed')
    paths = [p.get('data-map-context-region') for p in before.iter(SVG_NS + 'path')
             if p.get('data-map-context-region')]
    if sorted(paths) != ['azores', 'madeira', 'mainland']:
        raise ValueError('Portugal context region set changed')
    for identifier in ('azores', 'madeira'):
        pattern = re.compile(r'<path\b(?=[^>]*\bdata-map-context-region="' + identifier + r'")[^>]*/>')
        svg, removed = pattern.subn('', svg)
        if removed != 1:
            raise ValueError(f'Expected one separate generated {identifier} context path')
    after = ET.fromstring(svg)
    if [dict(p.attrib) for p in after.iter(SVG_NS + 'path') if p.get('fill') == 'url(#land)'] != approved:
        raise ValueError('Portugal migration changed approved national land paths')
    retained = [p.get('data-map-context-region') for p in after.iter(SVG_NS + 'path')
                if p.get('data-map-context-region')]
    if retained != ['mainland']:
        raise ValueError('Portugal mainland context was not preserved')
    return svg


def reconcile_reviewed_portugal_spain_coast(svg: str, source: Path, resolution: str) -> str:
    """Use Spain from the *same* pinned Natural Earth 1:10m collection as Portugal.

    The approved Portugal SVG metadata pins PRT.geojson Git blob
    ce02dabb0ea17eba11923f78ed1525d8989c9b58; the separately audited
    Spanish ESP.geojson blob is 01ec685ca5739b63292e01380ff36287413508b5.
    The bundled fixed 1200x760 mainland viewport path was generated by clipping
    ESP to the verified WGS84 viewport and simplifying by 0.003 degrees. Its
    source-matched border prevents the older GSHHG national coast from appearing
    as extra foreign land. Never change any approved Portugal path or inset.
    """
    original = source.read_bytes()
    git_blob = hashlib.sha1(f'blob {len(original)}\0'.encode() + original).hexdigest()
    if git_blob != '99af7a02646ec33a5ebc093f64bc13edeaaa8646' or resolution != 'i':
        raise ValueError('Portugal national source or source resolution changed; re-review Spain context')
    path = (ROOT / 'assets/images/portugal/spain-natural-earth-mainland-context.path').read_text(encoding='utf-8').rstrip('\n')
    if hashlib.sha256(path.encode('utf-8')).hexdigest() != '2c475f224a4bea0b3c83deacc006edf6a121b8e896badd2b10dcfb91f09e7356':
        raise ValueError('Reviewed Natural Earth Spain path changed; recheck source SHA and coast')
    parsed = ET.fromstring(svg)
    approved = [dict(p.attrib) for p in parsed.iter(SVG_NS + 'path') if p.get('fill') == 'url(#land)']
    if parsed.get('viewBox') != '0 0 1200 760' or len(approved) != 15:
        raise ValueError('Portugal approved target/canvas changed')
    pattern = re.compile(r'(<path data-map-context-region="mainland" d=")([^"]+)("[^>]*/>)')
    matches = list(pattern.finditer(svg))
    if len(matches) != 1 or hashlib.sha256(matches[0].group(2).encode()).hexdigest() != '9176ce17b97f65d5285adbad0d22f94f1c533bce06d05c71727a27cf58ffe796':
        raise ValueError('Portugal GSHHG mainland candidate changed; independent geographic review required')
    result = svg[:matches[0].start(2)] + path + svg[matches[0].end(2):]
    context = re.compile(r'(<g id="geographic-context"[^>]*>)')
    provenance = ('<desc>Spain mainland and clipped coastal islands: Natural Earth 1:10m '
                  'LonnyGomes/CountryGeoJSONCollection ESP.geojson, Git blob '
                  '01ec685ca5739b63292e01380ff36287413508b5, public domain. '
                  'Approved Portugal land: same collection PRT.geojson Git blob '
                  'ce02dabb0ea17eba11923f78ed1525d8989c9b58; WGS84; '
                  'viewports and national paths unchanged.</desc>')
    result, count = context.subn(lambda m: m.group(1) + provenance, result, count=1)
    if count != 1:
        raise ValueError('Portugal shared geographic-context group missing')
    updated = ET.fromstring(result)
    if [dict(p.attrib) for p in updated.iter(SVG_NS + 'path') if p.get('fill') == 'url(#land)'] != approved:
        raise ValueError('Spain coast replacement changed approved Portugal geometry')
    if [p.get('data-map-context-region') for p in updated.iter(SVG_NS + 'path') if p.get('data-map-context-region')] != ['mainland']:
        raise ValueError('Portugal unexpected geographic-context regions')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resolution", choices=("c", "l", "i", "h", "f"), default="i")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Output must be a new separate preview file")
    data = json.loads(args.country_json.read_text(encoding="utf-8"))
    slug = data.get("slug")
    if slug in legacy.LEGACY_SLUGS:
        legacy.generate(args.country_json, args.input, args.output, args.resolution)
    else:
        command = [sys.executable, str(ROOT / "scripts" / "add_country_map_context.py"),
                   "--country-json", str(args.country_json), "--input", str(args.input),
                   "--output", str(args.output), "--resolution", args.resolution]
        subprocess.run(command, cwd=ROOT, check=True)
    preview = args.output.read_text(encoding="utf-8")
    filtered, removed = remove_target_land_context(preview)
    clarified = frame_unframed_region_context(filtered, data.get("map", {}).get("regions"))
    if slug == 'bahrain':
        clarified = reconcile_reviewed_bahrain_hawar(clarified, args.resolution)
    if slug == 'portugal':
        clarified = remove_reviewed_portugal_ocean_self_land(clarified, data, args.input, args.resolution)
        clarified = reconcile_reviewed_portugal_spain_coast(clarified, args.input, args.resolution)
    if clarified != preview:
        args.output.write_text(clarified, encoding="utf-8")
    print(f"Created existing-Country preview: {args.output}; excluded {removed} duplicate target-land rings")


if __name__ == "__main__":
    main()
