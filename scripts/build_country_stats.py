#!/usr/bin/env python3
"""Build data/country-stats.json: population and area of the 200 Country pages,
parsed from each page's facts (人口・面積). Used by マイアトラス for
「世界の人口の◯％」「陸地の◯％」. Fails loudly if a value cannot be read."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def japanese_number(text):
    """'14億6,400万' → 1464000000, '27万4,200' → 274200, '8,509,379.576' → 8509379.576."""
    text = text.replace(',', '').replace('，', '')
    total = 0.0
    for unit, scale in (('億', 1e8), ('万', 1e4)):
        if unit in text:
            head, text = text.split(unit, 1)
            total += float(head) * scale
    if text:
        total += float(text)
    return total


def lead(value, unit):
    value = value.split('（')[0]
    match = re.search(r'([0-9][0-9,.億万]*)\s*' + re.escape(unit), value)
    if not match:
        raise ValueError(value)
    return japanese_number(match.group(1))


def main():
    registry = json.loads((ROOT / 'data/atlas-destinations.json').read_text(encoding='utf-8'))
    detail = set(registry['detailRegionSlugs'])
    stats, errors = {}, []
    for item in registry['destinations']:
        slug = item['slug']
        if slug in detail:
            continue
        page = json.loads((ROOT / f'data/countries/{slug}.json').read_text(encoding='utf-8'))
        facts = {fact['label']: fact['value'] for fact in page.get('facts', [])}
        try:
            people = 0 if slug == 'antarctica' else lead(facts['人口'], '人')
            area = lead(facts['面積'], 'km')
        except (KeyError, ValueError) as error:
            errors.append(f'{slug}: {error}')
            continue
        stats[slug] = {'population': round(people), 'areaKm2': round(area, 2)}
    if errors or len(stats) != 200:
        sys.exit('country stats: ' + '; '.join(errors) + f' ({len(stats)} parsed)')
    out = {
        'note': '各Country Pageの人口・面積（facts）から生成。scripts/build_country_stats.py',
        'totals': {'population': sum(s['population'] for s in stats.values()),
                   'areaKm2': round(sum(s['areaKm2'] for s in stats.values()))},
        'countries': stats,
    }
    (ROOT / 'data/country-stats.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('country stats:', len(stats), out['totals'])


if __name__ == '__main__':
    main()
