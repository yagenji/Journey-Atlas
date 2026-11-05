"""Region map anchors must keep geography separate from readable callouts."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_region_pages as region


class RegionMapPositions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/regions/unitedkingdom/northern-ireland.json').read_text())
        cls.svg = (ROOT / cls.data['map']['svg']).read_text()

    def test_northern_coast_callouts_are_separate_from_real_anchors(self):
        positions = [region.region_scene_map_position(s, i, self.svg, self.data['map'])
                     for i, s in enumerate(self.data['scenes'], 1)]
        self.assertEqual(len(set(positions)), 8)
        # These northern-coast places are close together geographically, but
        # their numbered hit targets must not overlap at the desktop map width.
        for i, j in [(0, 2), (0, 7), (2, 7), (0, 1), (1, 2)]:
            x1, y1 = positions[i]; x2, y2 = positions[j]
            distance = ((x1-x2)**2 + ((y1-y2)*760/1200)**2)**.5
            self.assertGreater(distance * 12, 27)

    def test_changed_scene_coordinates_are_rejected(self):
        coords = copy.deepcopy(self.data['scenes'][0]['coordinates'])
        coords['latitude'] += .02
        with self.assertRaisesRegex(ValueError, 'coordinates disagree'):
            region.interactive_map_position(coords, 1, self.svg, self.data['map']['bounds'])

    def test_changed_projection_bounds_are_rejected(self):
        bounds = dict(self.data['map']['bounds'], west=-9)
        with self.assertRaisesRegex(ValueError, 'projection'):
            region.interactive_map_position(self.data['scenes'][0]['coordinates'], 1, self.svg, bounds)

    def test_scotland_uses_verified_admin_boundary_and_real_map_anchors(self):
        data = json.loads((ROOT / 'data/regions/unitedkingdom/scotland.json').read_text())
        svg = (ROOT / data['map']['svg']).read_text()
        self.assertIn('data-map-projection="local-equirectangular-fit-v1"', svg)
        self.assertIn('id="scotland-land"', svg)
        self.assertIn('id="rockall-inset"', svg)
        self.assertIn('data-latitude="57.59705"', svg)
        self.assertIn('シェトランド諸島', svg)
        self.assertIn('ロッコール島は、実際の位置関係・縮尺と異なる別枠表示', data['map']['insetNote'])
        self.assertIn('ONSvisual', data['map']['source'])
        self.assertIn('Natural Earth', data['map']['source'])
        for i, scene in enumerate(data['scenes'], 1):
            actual = region.interactive_map_position(
                scene['coordinates'], i, svg, data['map']['bounds'])
            self.assertTrue(0 <= actual[0] <= 100)
            self.assertTrue(0 <= actual[1] <= 100)
        bad = copy.deepcopy(data['scenes'][0]['coordinates'])
        bad['longitude'] += .02
        with self.assertRaisesRegex(ValueError, 'coordinates disagree'):
            region.interactive_map_position(bad, 1, svg, data['map']['bounds'])

    def test_region_labels_and_review_state(self):
        page, canonical, published = region.render_region(self.data,
            site_url='https://atlas.yagenji.com/', version='test')
        self.assertFalse(published)
        self.assertEqual(canonical, 'https://atlas.yagenji.com/countries/unitedkingdom/northern-ireland/')
        self.assertIn('noindex,follow', page)
        self.assertIn('TASTE OF NORTHERN IRELAND', page)
        self.assertIn('北アイルランドの景色の地図', page)
        self.assertNotIn('スコットランドの景色の地図', page)
        self.assertNotIn('DATA SOURCES', page)
        self.assertNotIn('参考資料', page)
        scotland = json.loads((ROOT / 'data/regions/unitedkingdom/scotland.json').read_text())
        self.assertEqual('href="countries/unitedkingdom/scotland/"' in page,
                         scotland.get('regionPublished') is True)


if __name__ == '__main__':
    unittest.main()
