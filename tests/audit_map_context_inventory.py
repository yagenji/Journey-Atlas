#!/usr/bin/env python3
"""Read-only sharded inventory and raster preflight of published Country maps."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import add_country_map_context as ctx

NS = '{http://www.w3.org/2000/svg}'
COLORS = ('#eaf2f4', '#dcebf0', '#d0e3eb')


def target_paths(root):
    return [ET.tostring(p, encoding='unicode') for p in ctx.approved_land_paths(root)[0]]


def status_for(source, config):
    root = ET.fromstring(source)
    if root.tag != NS + 'svg' or root.get('viewBox') != '0 0 1200 760':
        return 'needs_review', 'noncanonical canvas', root
    match = ctx.SEA_GRADIENT.search(source)
    palette = tuple(re.findall(r'stop-color="(#[0-9a-fA-F]{6})"', match.group())) if match else ()
    if palette == COLORS and ('Surrounding land:' in source or 'id="geographic-context"' in source):
        return 'existing_context', 'approved palette and existing context; do not regenerate', root
    bounds = config['map']['bounds']
    b = tuple(float(bounds[k]) for k in ('west', 'south', 'east', 'north'))
    regions = config['map'].get('regions')
    empty = {r['id']: '' for r in regions} if regions else ''
    try:
        ctx.add_context(source, b, empty, 'i', regions)
    except (ValueError, TypeError, KeyError, StopIteration, IndexError) as exc:
        return 'needs_review', str(exc)[:250], root
    return 'previewable', 'preflight checks passed', root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--shard', type=int, required=True)
    parser.add_argument('--shards', type=int, default=4)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-previews', action='store_true')
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
    published = [d for d in destinations if d.get('atlasPublished')]
    selected = [d for idx, d in enumerate(published) if idx % args.shards == args.shard]
    summary = {'git_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'shard': args.shard, 'shards': args.shards, 'registry_count': len(destinations),
               'published_count': len(published), 'selected_count': len(selected),
               'in_flight': {}, 'countries': [], 'counts': {}}
    for slug in ('belize', 'honduras'):
        p = ROOT / 'ops/country-production' / (slug + '.json')
        state = json.loads(p.read_text()) if p.exists() else {}
        entry = next(d for d in destinations if d['slug'] == slug)
        summary['in_flight'][slug] = {'phase': state.get('phase'), 'published': entry['atlasPublished'], 'excluded': True}
    thumbs = []
    for d in selected:
        slug = d['slug']
        record = {'slug': slug, 'published': True}
        summary['countries'].append(record)
        if slug in ('belize', 'honduras'):
            record.update(status='in_flight_hold', reason='excluded until agreed completion gate')
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
            record.update(status=status, reason=reason, svg=relative,
                          input_sha256=hashlib.sha256(source.encode()).hexdigest(),
                          projection=root.get('data-map-projection'),
                          regions=[r['id'] for r in config['map'].get('regions', [])],
                          target_path_count=len(target_paths(root)) if status != 'needs_review' else None)
            if status != 'previewable' or args.no_previews:
                continue
            output_svg = args.output / (slug + '.svg')
            command = [sys.executable, str(ROOT / 'scripts/add_country_map_context.py'),
                       '--country-json', str(country_path), '--input', str(svg_path), '--output', str(output_svg)]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
            if completed.returncode:
                raise RuntimeError('map generation: ' + (completed.stderr or completed.stdout)[-350:])
            result = output_svg.read_text(encoding='utf-8')
            parsed = ET.fromstring(result)
            if target_paths(parsed) != target_paths(root):
                raise AssertionError('approved target path changed')
            if parsed.get('viewBox') != root.get('viewBox'):
                raise AssertionError('canvas changed')
            png = args.output / (slug + '.png')
            cairosvg.svg2png(bytestring=result.encode(), write_to=str(png), output_width=1200, output_height=760)
            with Image.open(png) as img:
                img.load()
                if img.size != (1200, 760):
                    raise AssertionError(f'PNG dimensions {img.size}')
                thumb = ImageOps.contain(img.convert('RGB'), (300, 190))
            thumbs.append((slug, thumb))
            record.update(status='preview_pass', reason='all approved land paths identical; full raster decode passed',
                          output_sha256=hashlib.sha256(result.encode()).hexdigest(), png_bytes=png.stat().st_size)
        except Exception as exc:
            record.update(status='blocked', reason=(type(exc).__name__ + ': ' + str(exc))[:500])
    if thumbs:
        sheet = Image.new('RGB', (1200, ((len(thumbs) + 3) // 4) * 220), '#ffffff')
        draw = ImageDraw.Draw(sheet)
        for idx, (slug, thumb) in enumerate(thumbs):
            x, y = (idx % 4) * 300, (idx // 4) * 220
            sheet.paste(thumb, (x, y))
            draw.text((x + 7, y + 193), slug, fill='#202020')
        sheet.save(args.output / 'contact-sheet.png')
    summary['counts'] = dict(sorted(Counter(r['status'] for r in summary['countries']).items()))
    (args.output / 'report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print('MAP INVENTORY', json.dumps({k: summary[k] for k in ('git_sha','shard','published_count','selected_count','counts')}, ensure_ascii=False))
    for r in summary['countries']:
        if r['status'] not in ('preview_pass','existing_context'):
            print('REVIEW', r['slug'], r['status'], r.get('reason',''))


if __name__ == '__main__':
    main()
