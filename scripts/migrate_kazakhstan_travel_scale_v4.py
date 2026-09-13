#!/usr/bin/env python3
import json
from pathlib import Path

path = Path('data/countries/kazakhstan.json')
data = json.loads(path.read_text(encoding='utf-8'))
if data.get('contentQaVersion') != 3:
    raise SystemExit(f"expected Kazakhstan contentQaVersion 3, got {data.get('contentQaVersion')!r}")
items = data.get('travelScale', {}).get('items', [])
if len(items) != 3:
    raise SystemExit(f"expected 3 travelScale items, got {len(items)}")
data['contentQaVersion'] = 4
for item, duration in zip(items, ['4〜5日', '7〜9日', '12日以上']):
    item['duration'] = duration
path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print('Kazakhstan migrated to Content QA v4 with day-based Travel Scale')
