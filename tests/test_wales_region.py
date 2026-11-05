"""Finished Wales handoff: image integrity, review status and close map anchors."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_region_pages as region


class WalesRegion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/regions/unitedkingdom/wales.json').read_text())
        cls.svg = (ROOT / cls.data['map']['svg']).read_text()

    def test_complete_approved_image_set(self):
        items = [self.data['hero'], *self.data['scenes'], *self.data['taste']['items']]
        self.assertEqual(len(items), 13)
        hashes = set()
        for item in items:
            path = ROOT / item['image']
            hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
            with Image.open(path) as image:
                image.load()
                self.assertEqual(image.size, (1536, 1024))
                self.assertEqual(image.format, 'WEBP')
        self.assertEqual(len(hashes), 13)

    def test_unpublished_shared_page(self):
        page, canonical, published = region.render_region(self.data,
            site_url='https://atlas.yagenji.com/', version='test')
        self.assertFalse(published)
        self.assertEqual(canonical, 'https://atlas.yagenji.com/countries/unitedkingdom/wales/')
        self.assertIn('noindex,follow', page)
        self.assertEqual(page.count('class="scene-card region-scene"'), 8)
        self.assertEqual(page.count('class="taste-card region-taste"'), 4)
        self.assertEqual(len(self.data['culture']), 6)
        self.assertEqual(len(self.data['travelTrivia']), 5)
        self.assertTrue(all(len(item.get('points', [])) == 2 for item in self.data['culture']))
        self.assertIn('北西部の別枠拡大図', page)

    def test_inset_keeps_real_anchors_and_separates_nearby_places(self):
        root = ET.fromstring(self.svg)
        self.assertIsNotNone(root.find('.//*[@id="wales-northwest-detail"]'))
        projected = []
        for i, scene in enumerate(self.data['scenes'], 1):
            actual = region.interactive_map_position(scene['coordinates'], i, self.svg, self.data['map']['bounds'])
            displayed = region.region_scene_map_position(scene, i, self.svg, self.data['map'])
            if scene['id'] in self.data['map']['regions'][0]['sceneIds']:
                self.assertNotEqual(actual, displayed)
                projected.append(displayed)
            else:
                self.assertEqual(actual, displayed)
        (x, y), (xx, yy) = projected
        self.assertGreater(((12*(x-xx))**2 + (7.6*(y-yy))**2)**.5, 27)
        altered = copy.deepcopy(self.data['scenes'][4])
        altered['coordinates']['latitude'] += .01
        with self.assertRaisesRegex(ValueError, 'coordinates disagree'):
            region.region_scene_map_position(altered, 5, self.svg, self.data['map'])

    def test_all_source_keys_resolve(self):
        def visit(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in ('sourceKey', 'coordinateSourceKey'):
                        self.assertIn(child, self.data['sources'])
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(self.data)


if __name__ == '__main__':
    unittest.main()
