"""Finished Wales handoff: image integrity, publication status and close map anchors."""
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

    def test_published_shared_page(self):
        page, canonical, published = region.render_region(self.data,
            site_url='https://atlas.yagenji.com/', version='test')
        self.assertTrue(published)
        self.assertEqual(canonical, 'https://atlas.yagenji.com/countries/unitedkingdom/wales/')
        self.assertIn('content="index,follow"', page)
        self.assertEqual(page.count('class="scene-card region-scene"'), 8)
        self.assertEqual(page.count('class="taste-card region-taste"'), 4)
        self.assertEqual(len(self.data['culture']), 6)
        self.assertEqual(len(self.data['travelTrivia']), 5)
        self.assertTrue(all(len(item.get('points', [])) == 2 for item in self.data['culture']))
        self.assertNotIn('region-map-detail-mobile', page)
        self.assertNotIn('map-inset-note', page)

    def test_callouts_keep_real_anchors_without_an_inset(self):
        root = ET.fromstring(self.svg)
        self.assertIsNone(root.find('.//*[@id="wales-northwest-detail"]'))
        self.assertNotIn('data-map-inset-standard', root.attrib)
        projected = []
        for i, scene in enumerate(self.data['scenes'], 1):
            actual = region.interactive_map_position(scene['coordinates'], i, self.svg, self.data['map']['bounds'])
            displayed = region.region_scene_map_position(scene, i, self.svg, self.data['map'])
            if scene.get('mapOffset'):
                self.assertNotEqual(actual, displayed)
                node = root.find(f'.//*[@id="scene-marker-{i}"]')
                self.assertIsNotNone(node.find('{http://www.w3.org/2000/svg}path'))
                self.assertIsNotNone(node.find('{http://www.w3.org/2000/svg}circle'))
            else:
                self.assertEqual(actual, displayed)
            projected.append(displayed)
        # A 290px-wide map covers a narrow phone after the shared page padding.
        for i, (x, y) in enumerate(projected):
            for xx, yy in projected[i+1:]:
                gap = ((12*(x-xx))**2 + (7.6*(y-yy))**2)**.5
                self.assertGreater(gap * 290 / 1200, 27)
        altered = copy.deepcopy(self.data['scenes'][4])
        altered['coordinates']['latitude'] += .01
        with self.assertRaisesRegex(ValueError, 'coordinates disagree'):
            region.region_scene_map_position(altered, 5, self.svg, self.data['map'])

    def test_callout_drift_and_excessive_offsets_are_rejected(self):
        scene = copy.deepcopy(self.data['scenes'][4])
        scene['mapOffset'] = {'x': 6, 'y': 0}
        with self.assertRaisesRegex(ValueError, 'exceeds 60'):
            region.region_scene_map_position(scene, 5, self.svg, self.data['map'])
        scene['mapOffset'] = {'x': 0, 'y': 0}
        with self.assertRaisesRegex(ValueError, 'label coordinates disagree'):
            region.region_scene_map_position(scene, 5, self.svg, self.data['map'])

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
