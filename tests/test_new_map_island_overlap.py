"""Regression tests for shared new-Country map context duplication."""
import importlib.util
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

WRAPPER = Path(__file__).resolve().parents[1] / 'scripts' / 'generate_country_map_with_context.py'
spec = importlib.util.spec_from_file_location('shared_map_wrapper', WRAPPER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SEA = 'M 100,0 L 110,0 L 110,10 L 100,10 Z'
ISLAND = 'M 0,0 L 10,0 L 10,10 L 0,10 Z'
TARGET = 'M 0.04,0.04 L 9.96,0.04 L 9.96,9.96 L 0.04,9.96 Z'
CONTINENT = 'M 0,0 L 100,0 L 100,10 L 0,10 Z'

def sample(context: str, target: str=TARGET, projection='local-equirectangular-fit-v1'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" '
            f'data-map-projection="{projection}"><g id="geographic-context">'
            f'<path d="{context}" fill="#e4e0ce"/></g><path d="{target}" '
            'fill="url(#land)" /></svg>')

class IslandContextTests(unittest.TestCase):
    def test_isolated_target_duplicate_dropped_neighbors_remain(self):
        svg=sample(ISLAND+' '+SEA)
        clean,count=module.strip_redundant_island_context(svg)
        self.assertEqual(count,1)
        self.assertIn(SEA,clean)
        self.assertNotIn('d="'+ISLAND+' '+SEA+'"',clean)
        self.assertIn('d="'+TARGET+'"',clean)
        self.assertEqual(module.strip_redundant_island_context(clean),(clean,0))

    def test_connected_mainland_not_discarded(self):
        svg=sample(CONTINENT)
        self.assertEqual(module.strip_redundant_island_context(svg),(svg,0))

    def test_distant_context_not_discarded(self):
        svg=sample(SEA)
        self.assertEqual(module.strip_redundant_island_context(svg),(svg,0))

    def test_does_not_touch_target_or_metadata(self):
        svg=sample(ISLAND+' '+SEA)
        clean,count=module.strip_redundant_island_context(svg)
        a=ET.fromstring(svg); b=ET.fromstring(clean)
        ns='{http://www.w3.org/2000/svg}'
        ca=next(n for n in a.iter(ns+'g') if n.get('id')=='geographic-context')
        cb=next(n for n in b.iter(ns+'g') if n.get('id')=='geographic-context')
        ca[0].set('d',cb[0].get('d'))
        self.assertEqual(ET.tostring(a),ET.tostring(b))
        self.assertEqual(count,1)

    def test_fails_closed_for_unsupported_projection(self):
        with self.assertRaises(ValueError):
            module.strip_redundant_island_context(sample(ISLAND,projection='unknown'))

    def test_fails_closed_for_unsupported_path_command(self):
        with self.assertRaises(ValueError):
            module.strip_redundant_island_context(sample('M 0,0 C 0,1 1,2 2,2 Z'))

if __name__ == '__main__':
    unittest.main()
