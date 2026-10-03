#!/usr/bin/env python3
"""Read-only sharded inventory, lake-consistency audit, and raster preflight of Country maps."""
import argparse
import hashlib
import io
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import add_country_map_context as ctx
import add_country_map_context_legacy as legacy

NS = '{http://www.w3.org/2000/svg}'
COLORS = ('#eaf2f4', '#dcebf0', '#d0e3eb')
MIN_LAKE_PIXELS = 64
MIN_LAKE_WIDTH = 5
MIN_LAKE_HEIGHT = 5
LAKE_WATER_PASS = 0.78


def original_paths(root):
    """Serialize every original path, excluding generated context descendants."""
    parents = {child: parent for parent in root.iter() for child in parent}
    result = []
    for path in root.iter(NS + 'path'):
        cursor = path
        excluded = any(key.startswith('data-map-context') for key in path.attrib)
        while cursor is not None and not excluded:
            if cursor.attrib.get('id') == 'geographic-context':
                excluded = True
                break
            cursor = parents.get(cursor)
        if not excluded:
            result.append(ET.tostring(path, encoding='unicode'))
    return result


def status_for(source, config):
    root = ET.fromstring(source)
    if root.tag != NS + 'svg' or root.get('viewBox') != '0 0 1200 760':
        return 'needs_review', 'noncanonical canvas', root
    match = ctx.SEA_GRADIENT.search(source)
    palette = tuple(re.findall(r'stop-color="(#[0-9a-fA-F]{6})"', match.group())) if match else ()
    if palette == COLORS and ('Surrounding land:' in source or 'id="geographic-context"' in source):
        return 'existing_context', 'approved palette and existing context; do not regenerate', root
    if config.get('slug') in legacy.LEGACY_SLUGS:
        return 'previewable', 'reviewed migration-only legacy adapter', root
    bounds = config['map']['bounds']
    b = tuple(float(bounds[k]) for k in ('west', 'south', 'east', 'north'))
    regions = config['map'].get('regions')
    empty = {r['id']: '' for r in regions} if regions else ''
    try:
        ctx.add_context(source, b, empty, 'i', regions)
    except (ValueError, TypeError, KeyError, StopIteration, IndexError) as exc:
        return 'needs_review', str(exc)[:250], root
    return 'previewable', 'preflight checks passed', root


def _bounds_tuple(bounds):
    return tuple(float(bounds[key]) for key in ('west', 'south', 'east', 'north'))


def _rect_tuple(rect):
    return tuple(float(rect[key]) for key in ('x', 'y', 'width', 'height'))


def _map_frames(config):
    """Return georeference frames that are safe for the shared local projection."""
    regions = config.get('map', {}).get('regions')
    if regions:
        return [(region['id'], _bounds_tuple(region['bounds']), _rect_tuple(region['rect'])) for region in regions]
    bounds = config.get('map', {}).get('bounds') or {}
    return [('main', _bounds_tuple(bounds), None)]


def _gshhs_lakes(bounds):
    """Return GSHHS level-2 inland-water polygons intersecting the visible canvas bounds."""
    from mpl_toolkits.basemap import Basemap
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union

    west, south, east, north = bounds
    if not (-360 <= west < east <= 360 and east - west <= 180 and -89 <= south < north <= 89):
        raise ValueError('unsupported lake-audit bounds')
    basemap = Basemap(
        projection='cyl',
        llcrnrlon=west,
        llcrnrlat=south,
        urcrnrlon=east,
        urcrnrlat=north,
        resolution='i',
        area_thresh=0.1,
    )
    lakes = []
    for (xs, ys), level in zip(basemap.coastpolygons, basemap.coastpolygontypes):
        if level != 2:
            continue
        poly = Polygon(zip(xs, ys))
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty:
            lakes.append(poly)
    if not lakes:
        return []
    clipped = unary_union(lakes).intersection(box(*bounds))
    return [poly for poly in ctx.mapgen.polygons_from_geometry(clipped) if not poly.is_empty]


def _project_ring(coords, bounds, rect):
    factor, scale, origin_x, origin_y = ctx.frame(bounds, rect)
    west, south, east, north = bounds
    return [
        (
            origin_x + (lon - west) * factor * scale,
            origin_y + (north - lat) * scale,
        )
        for lon, lat in coords
    ]


def _lake_mask(poly, bounds, rect, image_module, image_draw_module):
    mask = image_module.new('L', (ctx.mapgen.WIDTH, ctx.mapgen.HEIGHT), 0)
    draw = image_draw_module.Draw(mask)
    exterior = _project_ring(poly.exterior.coords, bounds, rect)
    if len(exterior) >= 3:
        draw.polygon(exterior, fill=255)
    for interior in poly.interiors:
        ring = _project_ring(interior.coords, bounds, rect)
        if len(ring) >= 3:
            draw.polygon(ring, fill=0)
    return mask


def _is_water_rgb(rgb):
    r, g, b = rgb[:3]
    # Shared sea gradients and the existing explicit lake fill are all cool,
    # pale blue/blue-green. Target/context land is warmer and fails this gate.
    return b >= 214 and g >= 220 and g - r >= 3 and b - r >= 4


def audit_lakes(source, config, cairosvg, image_module, image_draw_module):
    """Audit material GSHHS lakes against the rendered canonical SVG.

    Only lake polygons that remain visibly meaningful at the 1200x760 product
    scale are tested. Tiny water bodies are intentionally ignored.
    """
    frames = _map_frames(config)
    candidates = []
    seen = set()
    for frame_id, bounds, rect in frames:
        visible_bounds = ctx.canvas_bounds(bounds, rect)
        for poly in _gshhs_lakes(visible_bounds):
            mask = _lake_mask(poly, bounds, rect, image_module, image_draw_module)
            bbox = mask.getbbox()
            if bbox is None:
                continue
            width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pixels = int(sum(mask.histogram()[1:]))
            if pixels < MIN_LAKE_PIXELS or width < MIN_LAKE_WIDTH or height < MIN_LAKE_HEIGHT:
                continue
            lon, lat = poly.representative_point().coords[0]
            key = (round(lon, 4), round(lat, 4), frame_id)
            if key in seen:
                continue
            seen.add(key)
            candidates.append({
                'frame': frame_id,
                'longitude': round(lon, 5),
                'latitude': round(lat, 5),
                'pixels': pixels,
                'bbox': [int(v) for v in bbox],
                '_mask': mask,
            })
    if not candidates:
        return {'status': 'no_material_lakes', 'material_count': 0, 'missing_count': 0, 'lakes': []}

    raster = cairosvg.svg2png(
        bytestring=source.encode(),
        output_width=ctx.mapgen.WIDTH,
        output_height=ctx.mapgen.HEIGHT,
    )
    with image_module.open(io.BytesIO(raster)) as opened:
        image = opened.convert('RGB')
        px = image.load()
        for candidate in candidates:
            mask = candidate.pop('_mask')
            bbox = candidate['bbox']
            covered = water = 0
            mp = mask.load()
            for y in range(bbox[1], bbox[3]):
                for x in range(bbox[0], bbox[2]):
                    if not mp[x, y]:
                        continue
                    covered += 1
                    if _is_water_rgb(px[x, y]):
                        water += 1
            coverage = water / covered if covered else 0.0
            candidate['water_fraction'] = round(coverage, 4)
            candidate['status'] = 'pass' if coverage >= LAKE_WATER_PASS else 'missing_or_partial'

    missing = [lake for lake in candidates if lake['status'] != 'pass']
    return {
        'status': 'pass' if not missing else 'review',
        'material_count': len(candidates),
        'missing_count': len(missing),
        'lakes': candidates,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--shard', type=int, required=True)
    parser.add_argument('--shards', type=int, default=4)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-previews', action='store_true')
    parser.add_argument(
        '--scope',
        choices=('published', 'all'),
        default='published',
        help='Audit published registry entries or every Country JSON with a map SVG.',
    )
    args = parser.parse_args()
    if not 0 <= args.shard < args.shards:
        parser.error('invalid shard')
    import cairosvg
    from PIL import Image, ImageOps, ImageDraw
    args.output.mkdir(parents=True, exist_ok=True)
    registry = json.loads((ROOT / 'data/atlas-destinations.json').read_text())
    destinations = registry['destinations']
    if len(destinations) != registry['count'] or len({d['slug'] for d in destinations}) != len(destinations):
        raise SystemExit('Canonical registry count or unique slugs invalid')
    if args.scope == 'published':
        audited = [d for d in destinations if d.get('atlasPublished')]
    else:
        audited = []
        for d in destinations:
            country_path = ROOT / 'data/countries' / (d['slug'] + '.json')
            if not country_path.exists():
                continue
            try:
                country = json.loads(country_path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            svg = (country.get('map') or {}).get('svg')
            if isinstance(svg, str) and svg.endswith('.svg'):
                audited.append(d)
    selected = [d for idx, d in enumerate(audited) if idx % args.shards == args.shard]
    summary = {'git_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'shard': args.shard, 'shards': args.shards, 'scope': args.scope,
               'registry_count': len(destinations), 'published_count': sum(bool(d.get('atlasPublished')) for d in destinations),
               'audited_count': len(audited), 'selected_count': len(selected),
               'production_state': {}, 'countries': [], 'counts': {}, 'lake_counts': {}}
    state_by_slug = {}
    for slug in ('belize', 'honduras'):
        p = ROOT / 'ops/country-production' / (slug + '.json')
        state = json.loads(p.read_text()) if p.exists() else {}
        state_by_slug[slug] = state
        entry = next(d for d in destinations if d['slug'] == slug)
        summary['production_state'][slug] = {'phase': state.get('phase'), 'published': entry['atlasPublished']}
    thumbs = []
    for d in selected:
        slug = d['slug']
        record = {'slug': slug, 'published': bool(d.get('atlasPublished'))}
        summary['countries'].append(record)
        if args.scope == 'published' and slug in state_by_slug and state_by_slug[slug].get('phase') != 'COMPLETE':
            record.update(status='in_flight_hold', reason='published registry entry is not COMPLETE; fail closed')
            continue
        try:
            country_path = ROOT / 'data/countries' / (slug + '.json')
            config = json.loads(country_path.read_text())
            relative = config['map']['svg']
            if not re.fullmatch(r'assets/images/[a-z0-9-]+/[a-zA-Z0-9_./-]+\.svg', relative) or '..' in Path(relative).parts:
                raise ValueError('untrusted or non-SVG map reference')
            svg_path = ROOT / relative
            source = svg_path.read_text(encoding='utf-8')
            status, reason, root = status_for(source, config)
            try:
                lake_audit = audit_lakes(source, config, cairosvg, Image, ImageDraw)
            except Exception as lake_exc:
                lake_audit = {
                    'status': 'unsupported',
                    'material_count': 0,
                    'missing_count': 0,
                    'reason': (type(lake_exc).__name__ + ': ' + str(lake_exc))[:400],
                    'lakes': [],
                }
            record.update(status=status, reason=reason, svg=relative,
                          input_sha256=hashlib.sha256(source.encode()).hexdigest(),
                          projection=root.get('data-map-projection'),
                          regions=[r['id'] for r in config['map'].get('regions', [])],
                          original_path_count=len(original_paths(root)),
                          adapter=('legacy' if slug in legacy.LEGACY_SLUGS else 'canonical'),
                          lake_audit=lake_audit)
            if status != 'previewable' or args.no_previews:
                continue
            output_svg = args.output / (slug + '.svg')
            command = [sys.executable, str(ROOT / 'scripts/add_country_map_context_existing.py'),
                       '--country-json', str(country_path), '--input', str(svg_path), '--output', str(output_svg)]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
            if completed.returncode:
                raise RuntimeError('map generation: ' + (completed.stderr or completed.stdout)[-500:])
            result = output_svg.read_text(encoding='utf-8')
            parsed = ET.fromstring(result)
            if original_paths(parsed) != original_paths(root):
                raise AssertionError('approved/original SVG path geometry changed')
            if parsed.get('viewBox') != root.get('viewBox'):
                raise AssertionError('canvas changed')
            if parsed.find(".//*[@id='geographic-context']") is None:
                raise AssertionError('geographic context missing')
            png = args.output / (slug + '.png')
            cairosvg.svg2png(bytestring=result.encode(), write_to=str(png), output_width=1200, output_height=760)
            with Image.open(png) as img:
                img.load()
                if img.size != (1200, 760):
                    raise AssertionError(f'PNG dimensions {img.size}')
                if img.getbbox() is None:
                    raise AssertionError('empty raster')
                thumb = ImageOps.contain(img.convert('RGB'), (300, 190))
            thumbs.append((slug, thumb))
            record.update(status='preview_pass', reason='all original SVG paths identical; full raster decode passed',
                          output_sha256=hashlib.sha256(result.encode()).hexdigest(), png_bytes=png.stat().st_size)
        except Exception as exc:
            record.update(status='blocked', reason=(type(exc).__name__ + ': ' + str(exc))[:700])
    if thumbs:
        sheet = Image.new('RGB', (1200, ((len(thumbs) + 3) // 4) * 220), '#ffffff')
        draw = ImageDraw.Draw(sheet)
        for idx, (slug, thumb) in enumerate(thumbs):
            x, y = (idx % 4) * 300, (idx // 4) * 220
            sheet.paste(thumb, (x, y))
            draw.text((x + 7, y + 193), slug, fill='#202020')
        sheet.save(args.output / 'contact-sheet.png')
    summary['counts'] = dict(sorted(Counter(r['status'] for r in summary['countries']).items()))
    summary['lake_counts'] = dict(sorted(Counter(
        (r.get('lake_audit') or {}).get('status', 'not_audited') for r in summary['countries']
    ).items()))
    (args.output / 'report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print('MAP INVENTORY', json.dumps(
        {k: summary[k] for k in ('git_sha','shard','scope','audited_count','selected_count','counts','lake_counts')},
        ensure_ascii=False,
    ))
    for r in summary['countries']:
        if r['status'] not in ('preview_pass','existing_context'):
            print('REVIEW', r['slug'], r['status'], r.get('reason',''))
        lake = r.get('lake_audit') or {}
        if lake.get('status') == 'review':
            print('LAKE REVIEW', r['slug'], lake.get('missing_count'), 'of', lake.get('material_count'))


if __name__ == '__main__':
    main()
