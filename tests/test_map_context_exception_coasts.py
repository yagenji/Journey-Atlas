"""Read-only source-vintage and full-size visual QA for Singapore/Macau PR maps.

Run by the existing map-context preflight. Exports current PR-head PNG/SVG to
its existing priority-review artifact; never edits a production SVG or grants
geographic QA approval based on a successful decode.
"""
from __future__ import annotations

import hashlib
import io
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/tmp/journey-atlas-map-context-real-previews/priority-review')
SVG = '{http://www.w3.org/2000/svg}'
APPROVED = {
    'singapore': (5, '237292bac3e9c90204fa4e2169d588deb3709916c823dac254cd4383f69121a5', 'Singapore Land Authority'),
    'macau': (1, '44bdca23d43ee30484e9fcf911a2b373c86030c54638edbe0810875d60d35eb1', 'Xiangzhou'),
}


def national_paths(root):
    parents = {child: parent for parent in root.iter() for child in parent}
    result = []
    for path in root.iter(SVG+'path'):
        node = path
        while node is not None and 'fill' not in node.attrib:
            node = parents.get(node)
        if node is not None and node.get('fill') == 'url(#land)':
            result.append(path.get('d',''))
    return result


class ExistingExceptionCoastQa(unittest.TestCase):
    def test_actual_branch_sources_render_and_preserve_country(self):
        for slug, (count, digest, source_name) in APPROVED.items():
            with self.subTest(slug=slug):
                path = ROOT/'assets/images'/slug/'map-atlas-v1.svg'
                raw = path.read_bytes()
                root = ET.fromstring(raw)
                self.assertEqual(root.get('viewBox'), '0 0 1200 760')
                original = national_paths(root)
                self.assertEqual(len(original), count)
                self.assertEqual(hashlib.sha256('\n'.join(original).encode()).hexdigest(), digest)
                foreign = root.find('.//*[@id="geographic-context"]')
                self.assertIsNotNone(foreign)
                self.assertEqual(foreign.get('clip-path'), 'url(#foreign-land-only)')
                clip = root.find('.//*[@id="foreign-land-only"]')
                self.assertIsNotNone(clip)
                self.assertEqual([p.get('d') for p in clip.iter(SVG+'path')],
                                 ['M 0,0 L 1200,0 L 1200,760 L 0,760 Z ' + ' '.join(original)])
                note = ''.join(foreign.itertext())
                self.assertIn('OpenStreetMap', note)
                self.assertIn('ODbL', note)
                self.assertIn(source_name, note)
                self.assertEqual(len(list(foreign.iter(SVG+'path'))), 1)
                image = cairosvg.svg2png(bytestring=raw, output_width=1200, output_height=760)
                with Image.open(io.BytesIO(image)) as png:
                    png.load()
                    self.assertEqual(png.size, (1200,760))
                target_dir = OUT/slug
                target_dir.mkdir(parents=True, exist_ok=True)
                (target_dir/(slug+'-current.svg')).write_bytes(raw)
                (target_dir/(slug+'-current.png')).write_bytes(image)
                report = {
                    'status': 'HOLD: independent cross-source coastal alignment still required',
                    'country': slug,
                    'sha256': hashlib.sha256(raw).hexdigest(),
                    'approvedNationalPathSha256': digest,
                    'protectedNationalPathCount': count,
                    'contextSha256': hashlib.sha256(next(foreign.iter(SVG+'path')).get('d','').encode()).hexdigest(),
                    'source': note,
                    'displayOnlyForeignClip': True,
                    'fullRaster': [1200,760],
                }
                (target_dir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
                print(json.dumps(report,ensure_ascii=False), flush=True)


if __name__=='__main__': unittest.main()
