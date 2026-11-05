"""Opted-in callouts align interaction with artwork without moving real anchors."""
import copy
import json
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_region_pages as region


class RegionMapCallouts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/regions/unitedkingdom/wales.json').read_text())
        cls.svg = (ROOT / cls.data['map']['svg']).read_text()

    def test_hits_align_with_visible_numbered_circles(self):
        root = ET.fromstring(self.svg)
        for i, scene in enumerate(self.data['scenes'], 1):
            x, y = region.region_scene_map_position(scene, i, self.svg, self.data['map'])
            circle = root.find(f'.//*[@id="scene-marker-{i}"]/{{http://www.w3.org/2000/svg}}circle')
            self.assertAlmostEqual(x * 12, float(circle.get('cx')), places=4)
            self.assertAlmostEqual(y * 7.6, float(circle.get('cy')), places=4)

    def test_callout_still_rejects_incorrect_real_coordinates(self):
        scene = copy.deepcopy(self.data['scenes'][4])
        scene['coordinates']['latitude'] += .01
        with self.assertRaisesRegex(ValueError, 'coordinates disagree'):
            region.region_scene_map_position(scene, 5, self.svg, self.data['map'])

    def test_callouts_require_explicit_opt_in(self):
        svg = self.svg.replace('data-map-callouts="true"', '')
        x, y = region.region_scene_map_position(self.data['scenes'][4], 5, svg, self.data['map'])
        node = ET.fromstring(svg).find('.//*[@id="scene-marker-5"]')
        self.assertAlmostEqual(x * 12, float(node.get('data-x')), places=4)
        self.assertAlmostEqual(y * 7.6, float(node.get('data-y')), places=4)

    def test_outside_canvas_callout_is_rejected(self):
        root = ET.fromstring(self.svg)
        root.find('.//*[@id="scene-marker-5"]').set('data-label-x', '1201')
        svg = ET.tostring(root, encoding='unicode')
        with self.assertRaisesRegex(ValueError, 'outside the canvas'):
            region.region_scene_map_position(self.data['scenes'][4], 5, svg, self.data['map'])


if __name__ == '__main__':
    unittest.main()
