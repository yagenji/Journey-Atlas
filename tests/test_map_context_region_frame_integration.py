#!/usr/bin/env python3
"""Real-map regression for clipped regional context and original SVG parity."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'


def original_paths(root):
    parents = {child: parent for parent in root.iter() for child in parent}
    paths = []
    for path in root.iter(NS + 'path'):
        cursor = path
        generated = any(key.startswith('data-map-context') for key in path.attrib)
        while cursor is not None and not generated:
            if cursor.get('id') == 'geographic-context':
                generated = True
                break
            cursor = parents.get(cursor)
        if not generated:
            paths.append(ET.tostring(path, encoding='unicode'))
    return paths


class RealRegionalFrameTest(unittest.TestCase):
    def test_unframed_real_map_gets_explicit_viewports(self):
        import cairosvg
        from PIL import Image

        country = ROOT / 'data/countries/portugal.json'
        config = json.loads(country.read_text(encoding='utf-8'))
        source = ROOT / config['map']['svg']
        before = ET.fromstring(source.read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory(prefix='map-context-frames-') as directory:
            target = Path(directory) / 'portugal-preview.svg'
            subprocess.run([sys.executable, str(ROOT / 'scripts/add_country_map_context_existing.py'),
                            '--country-json', str(country), '--input', str(source),
                            '--output', str(target)], cwd=ROOT, check=True, capture_output=True, text=True)
            preview = target.read_text(encoding='utf-8')
            after = ET.fromstring(preview)
            self.assertEqual(after.get('viewBox'), '0 0 1200 760')
            self.assertEqual(original_paths(before), original_paths(after))
            regions = config['map']['regions']
            frames = [el for el in after.iter(NS + 'rect') if el.get('data-map-context-frame')]
            self.assertEqual({el.get('data-map-context-frame') for el in frames},
                             {region['id'] for region in regions})
            for region in regions:
                frame = next(el for el in frames if el.get('data-map-context-frame') == region['id'])
                for key in ('x', 'y', 'width', 'height'):
                    self.assertEqual(float(frame.get(key)), float(region['rect'][key]))
                self.assertEqual(frame.get('fill'), 'none')
                self.assertEqual(frame.get('stroke-dasharray'), '5 5')
            png = Path(directory) / 'portugal-preview.png'
            cairosvg.svg2png(bytestring=preview.encode(), write_to=str(png),
                            output_width=1200, output_height=760)
            with Image.open(png) as image:
                image.load()
                self.assertEqual(image.size, (1200, 760))
                self.assertIsNotNone(image.getbbox())


if __name__ == '__main__':
    unittest.main()
