"""Multi-parent review routes and polar map anchors must remain consistent."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_region_pages as region


class GreenlandRegion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/regions/denmark/greenland.json').read_text())
        cls.svg = (ROOT / cls.data['map']['svg']).read_text()

    def test_published_canonical_parent_and_content(self):
        page, canonical, published = region.render_region(self.data,
            site_url='https://atlas.yagenji.com/', version='test')
        self.assertTrue(published)
        self.assertEqual(canonical, 'https://atlas.yagenji.com/countries/denmark/greenland/')
        self.assertIn('<meta name="robots" content="index,follow">', page)
        self.assertIn('デンマークに戻る', page)
        self.assertNotIn('BACK TO UNITED KINGDOM', page)
        self.assertEqual(page.count('class="scene-card region-scene"'), 8)
        self.assertEqual(page.count('class="taste-card region-taste"'), 4)

    def test_season_icons_exist_and_air_routes_are_absent(self):
        for season in self.data['seasons']:
            self.assertIn(season['icon'], region.ICON_IDS)
        with self.assertRaisesRegex(ValueError, 'Unknown atlas icon'):
            region.icon('snowflake')
        page, _, _ = region.render_region(self.data,
            site_url='https://atlas.yagenji.com/', version='test')
        self.assertNotIn('id="region-routes-title"', page)
        self.assertEqual(self.data['nextRoutes'], [])

    def test_region_culture_receives_cross_section_content_qa(self):
        import validate_country_editorial_v2 as editorial
        import validate_country_quality_v5 as quality
        self.assertEqual(editorial.validate_data(self.data, 'greenland.json', force=True), [])
        self.assertEqual(quality.validate_data(self.data, 'greenland.json', force=True), [])
        duplicate = copy.deepcopy(self.data)
        duplicate['culture'][0]['topicKey'] = duplicate['signatureFacts'][0]['topicKey']
        self.assertTrue(editorial.validate_data(duplicate, 'greenland.json', force=True))
        self.assertTrue(quality.validate_data(duplicate, 'greenland.json', force=True))

    def test_source_coordinates_and_callouts_are_distinct(self):
        positions = []
        for i, scene in enumerate(self.data['scenes'], 1):
            anchor = region.interactive_map_position(scene['coordinates'], i, self.svg, self.data['map']['bounds'])
            label = region.region_scene_map_position(scene, i, self.svg, self.data['map'])
            self.assertTrue(all(0 <= p <= 100 for p in anchor + label))
            positions.append(label)
        # Separating close west-coast and southern anchors must survive mobile scaling.
        for a, b in [(0, 2), (4, 5)]:
            x1, y1 = positions[a]; x2, y2 = positions[b]
            self.assertGreater(((12*(x1-x2))**2+(7.6*(y1-y2))**2)**.5, 100)

    def test_tampered_polar_coordinates_are_rejected(self):
        coords = copy.deepcopy(self.data['scenes'][0]['coordinates'])
        coords['latitude'] += .02
        with self.assertRaisesRegex(ValueError, 'coordinates disagree'):
            region.interactive_map_position(coords, 1, self.svg, self.data['map']['bounds'])
        broken = self.svg.replace('data-x="518.563"', 'data-x="nan"')
        with self.assertRaisesRegex(ValueError, 'projected marker position'):
            region.interactive_map_position(self.data['scenes'][0]['coordinates'], 1, broken, self.data['map']['bounds'])


if __name__ == '__main__':
    unittest.main()
