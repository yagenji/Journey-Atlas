"""Protect the exact, display-only border exclusion in two reviewed map SVGs."""
import hashlib
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'
EXPECTED = {
    'macau': (1, '44bdca23d43ee30484e9fcf911a2b373c86030c54638edbe0810875d60d35eb1'),
    'singapore': (5, '237292bac3e9c90204fa4e2169d588deb3709916c823dac254cd4383f69121a5'),
}


class ExactForeignLandClip(unittest.TestCase):
    def test_foreign_context_excludes_original_national_paths(self):
        for slug, (count, expected_digest) in EXPECTED.items():
            with self.subTest(slug=slug):
                root = ET.parse(ROOT / 'assets/images' / slug / 'map-atlas-v1.svg').getroot()
                self.assertEqual(root.get('viewBox'), '0 0 1200 760')
                parents = {child: parent for parent in root.iter() for child in parent}
                national = []
                for node in root.iter(SVG + 'path'):
                    ancestor = node
                    while ancestor is not None and 'fill' not in ancestor.attrib:
                        ancestor = parents.get(ancestor)
                    if ancestor is not None and ancestor.get('fill') == 'url(#land)':
                        national.append(node.get('d', ''))
                self.assertEqual(len(national), count)
                self.assertEqual(hashlib.sha256('\n'.join(national).encode()).hexdigest(), expected_digest)
                clip = root.find(".//*[@id='foreign-land-only']")
                self.assertIsNotNone(clip)
                self.assertEqual(clip.get('clipPathUnits'), 'userSpaceOnUse')
                cut = clip.find(SVG + 'path')
                self.assertEqual(cut.get('clip-rule'), 'evenodd')
                self.assertEqual(cut.get('d'), 'M 0,0 L 1200,0 L 1200,760 L 0,760 Z ' + ' '.join(national))
                context = root.find(".//*[@id='geographic-context']")
                self.assertEqual(context.get('clip-path'), 'url(#foreign-land-only)')


if __name__ == '__main__':
    unittest.main()
