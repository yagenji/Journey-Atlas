"""History and present status share one section across both Region renderers."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_region_pages as region


class RegionHistory(unittest.TestCase):
    def test_seven_region_records_have_sourced_history_and_six_facts(self):
        paths = [*sorted((ROOT / 'data/regions').glob('*/*.json')),
                 ROOT / 'data/countries/hong-kong.json', ROOT / 'data/countries/macau.json']
        self.assertEqual(len(paths), 13)
        for path in paths:
            with self.subTest(region=path.stem):
                data = json.loads(path.read_text())
                facts = data.get('profile', data.get('facts'))
                self.assertEqual(len(facts), 6)
                self.assertFalse({'地域', '位置づけ'} & {x['label'] for x in facts})
                self.assertIn('主な宗教', [x['label'] for x in facts])
                history = data['historyContext']
                self.assertTrue(history['text'])
                self.assertTrue(history['sourceKeys'])
                for key in history['sourceKeys']:
                    self.assertIn('https://', data['sources'][key])
                    self.assertTrue(data['sourceDates'][key])
                if 'profile' in data:
                    page, _, _ = region.render_region(data, site_url='https://atlas.yagenji.com/', version='test')
                    self.assertEqual(page.count('class="region-history"'), 1)
                    self.assertIn(history['text'], page)
                    self.assertLess(page.index('id="region-facts-title"'), page.index('class="region-history"'))
                    self.assertLess(page.index('class="region-history"'), page.index('class="signature-facts"'))
                    self.assertNotIn('autonomy', [item.get('topicKey') for item in data['culture']])

    def test_region_history_escapes_authored_html(self):
        data = json.loads((ROOT / 'data/regions/denmark/greenland.json').read_text())
        data['historyContext']['text'] = '<script>alert(1)</script>'
        page, _, _ = region.render_region(data, site_url='https://atlas.yagenji.com/', version='test')
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
        self.assertNotIn('<script>alert(1)</script>', page)
