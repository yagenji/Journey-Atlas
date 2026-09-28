"""Qatar/Kuwait source-guarded existing-context corrections; not geographic signoff."""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from reconcile_gulf_foreign import PINNED, reconcile

NS = '{http://www.w3.org/2000/svg}'


def target_paths(root):
    return [dict(p.attrib) for p in root.iter(NS+'path') if p.get('fill') == 'url(#land)']


class GulfForeignSourceReview(unittest.TestCase):
    def review(self, slug):
        config = json.loads((ROOT/'data/countries'/f'{slug}.json').read_text())
        original = ROOT/config['map']['svg']
        source_text = original.read_text(encoding='utf-8')
        original_root = ET.fromstring(source_text)
        self.assertIsNotNone(original_root.find('.//*[@id="geographic-context"]'),
                             'Qatar/Kuwait already have context in the Draft branch')
        current_context = original_root.find('.//*[@id="geographic-context"]')
        if (current_context is not None and
                current_context.get('clip-path') == 'url(#map-context-reviewed-national-exclusion)'):
            updated = source_text
        else:
            updated = reconcile(source_text, original, slug, 'i')
        actual = ET.fromstring(updated)
        self.assertEqual(actual.get('viewBox'), '0 0 1200 760')
        self.assertEqual(target_paths(actual), target_paths(original_root),
                         'Approved national geometry/attributes must be identical')
        context = actual.find('.//*[@id="geographic-context"]')
        self.assertIsNotNone(context)
        self.assertEqual(context.get('clip-path'), 'url(#map-context-reviewed-national-exclusion)')
        clip = actual.find('.//*[@id="map-context-reviewed-national-exclusion"]')
        self.assertIsNotNone(clip)
        self.assertEqual(len(list(clip.iter(NS+'path'))), 1)
        self.assertTrue(clip.find(NS+'path').get('d').endswith(target_paths(original_root)[0]['d']))
        image = cairosvg.svg2png(bytestring=updated.encode(),output_width=1200,output_height=760)
        with Image.open(io.BytesIO(image)) as png:
            png.load()
            self.assertEqual(png.size,(1200,760))
        return updated, context, original

    def test_qatar_preserves_real_shared_saudi_land(self):
        updated, context, source = self.review('qatar')
        path = next(context.iter(NS+'path'))
        self.assertEqual(path.get('data-map-context-legacy'), 'national-base')
        self.assertEqual(hashlib.sha256(path.get('d').encode()).hexdigest(), PINNED['qatar']['context'],
                         'Saudi coastline and other unassigned GSHHG rings must remain intact')
        with self.assertRaisesRegex(ValueError, 'source|Source|Unreviewed'):
            reconcile(updated,source,'qatar','h')

    def test_kuwait_drops_only_four_verified_self_island_rings(self):
        updated, context, source = self.review('kuwait')
        path = next(context.iter(NS+'path'))
        self.assertEqual(path.get('data-map-context-region'), 'country')
        rings = [part for part in re.split(r'(?=\bM\s)', path.get('d')) if part.strip()]
        self.assertEqual(len(rings),2, 'Keep foreign mainland and unassigned sixth ring')
        self.assertIn('map-context-clip-country', updated)
        with self.assertRaisesRegex(ValueError,'source|Source|Unreviewed'):
            reconcile(updated,source,'kuwait','h')

    def test_rejects_unreviewed_source_without_modifying_it(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'changed.svg'
            source.write_text('<svg/>')
            for slug in PINNED:
                with self.subTest(slug=slug), self.assertRaises(ValueError):
                    reconcile('<svg/>',source,slug,'i')
                self.assertEqual(source.read_text(), '<svg/>')


if __name__=='__main__': unittest.main()
