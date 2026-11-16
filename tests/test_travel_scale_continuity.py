"""旅の目安日程は、段と段の間に空白の日数を作らず（例：8〜12日の次は13日〜）、
一つの段の幅は最大3日差（例：7〜10日）までにする。"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANGE = re.compile(r'^(\d+)〜(\d+)日$')
SINGLE = re.compile(r'^(\d+)日$')
OPEN = re.compile(r'^(\d+)日以上$')


def parse(duration):
    for pattern, kind in ((RANGE, 'range'), (SINGLE, 'single'), (OPEN, 'open')):
        m = pattern.match(duration)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if kind == 'range' else (start if kind == 'single' else None)
            return start, end
    return None  # 半日 など、日数で表せない段は対象外


class TravelScaleContinuity(unittest.TestCase):
    def test_tiers_are_continuous_and_end_open(self):
        paths = sorted((ROOT / 'data/countries').glob('*.json')) + sorted((ROOT / 'data/regions').glob('*/*.json'))
        for path in paths:
            items = (json.loads(path.read_text()).get('travelScale') or {}).get('items') or []
            tiers = [parse(item['duration']) for item in items]
            if not tiers or None in tiers:
                continue
            with self.subTest(page=str(path.relative_to(ROOT))):
                for (start, end), (next_start, _) in zip(tiers, tiers[1:]):
                    self.assertIsNotNone(end)
                    self.assertEqual(next_start, end + 1, [i['duration'] for i in items])
                self.assertIsNone(tiers[-1][1], '最後の段は「N日以上」')
                for start, end in tiers[:-1]:
                    self.assertLessEqual(end - start, 3, [i['duration'] for i in items])


if __name__ == '__main__':
    unittest.main()
