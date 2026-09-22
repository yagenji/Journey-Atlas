"""One approved historic HK map, source-matched cross-border geography review."""
from __future__ import annotations
import hashlib
import io
import json
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import add_country_map_context_legacy as legacy
from filter_duplicate_target_context import remove_target_land_context
from reconcile_hong_kong_foreign import pinned_mainland_path, reconcile, PINNED_MAINLAND_SHA

NS='{http://www.w3.org/2000/svg}'


class HongKongSourceReview(unittest.TestCase):
    def test_pinned_osm_shenzhen_matches_source_and_approved_hk_paths(self):
        self.assertEqual(hashlib.sha256(pinned_mainland_path().encode()).hexdigest(),
                         PINNED_MAINLAND_SHA)
        config_path=ROOT/'data/countries/hong-kong.json'
        config=json.loads(config_path.read_text())
        source=ROOT/config['map']['svg']
        original=source.read_text()
        generated=legacy._hong_kong(original,config,'i')
        filtered,_=remove_target_land_context(generated)
        updated=reconcile(filtered,source,'i')
        before=ET.fromstring(original)
        after=ET.fromstring(updated)
        src=before.find('.//*[@id="land-shape"]')
        dst=after.find('.//*[@id="land-shape"]')
        approved=lambda g:[dict(p.attrib) for p in g.iter(NS+'path')]
        self.assertEqual(len(approved(src)),18)
        self.assertEqual(approved(src),approved(dst))
        self.assertEqual(after.get('viewBox'),'0 0 1200 760')
        ctx=after.find('.//*[@id="geographic-context"]')
        self.assertIsNotNone(ctx)
        self.assertIn('OpenStreetMap', ''.join(ctx.itertext()))
        # The clip is generated context, not an extra approved source path.
        self.assertEqual([p.get('d') for p in ctx.findall(NS+'path')],
                         [pinned_mainland_path()])
        clip=ctx.find(NS+'clipPath')
        self.assertIsNotNone(clip)
        self.assertEqual(clip.get('id'),'hong-kong-foreign-only')
        self.assertEqual(len(clip.findall(NS+'path')),1)
        self.assertEqual(clip.find(NS+'path').get('d'),
                         'M 0,0 L 1200,0 L 1200,760 L 0,760 Z '
                         + ' '.join(p['d'] for p in approved(src)))
        # The generated clip must not appear among the original map paths.
        from audit_map_context_inventory import original_paths
        self.assertEqual(original_paths(after),original_paths(before))
        output=cairosvg.svg2png(bytestring=updated.encode(),
                               output_width=1200,output_height=760)
        with Image.open(io.BytesIO(output)) as image:
            image.load()
            self.assertEqual(image.size,(1200,760))


if __name__=='__main__':unittest.main()
