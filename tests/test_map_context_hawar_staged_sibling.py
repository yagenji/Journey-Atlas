"""Pin only migration-preview Hawar foreign Qatar land; never approve a whole map."""
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

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import add_country_map_context_legacy as legacy
import add_country_map_context_existing as existing
from filter_duplicate_target_context import remove_target_land_context
from reconcile_bahrain_hawar_sibling import reconcile, PINNED_PATH_SHA

SVG='{http://www.w3.org/2000/svg}'


class HawarSiblingSource(unittest.TestCase):
    def test_source_pinned_hawar_neighbour_and_approved_land_parity(self):
        config=json.loads((ROOT/'data/countries/bahrain.json').read_text())
        source=ROOT/config['map']['svg']
        original=source.read_text()
        if ('id="geographic-context"' in original
                and 'data-map-context-legacy="hawar"' in original
                and 'QAT-ADM0-15585745' in original):
            old=original
            updated=original
        else:
            raw=legacy._loose_multi_region(original,config,'i')
            filtered,_=remove_target_land_context(raw)
            framed=existing.frame_unframed_region_context(filtered,config['map']['regions'])
            old=existing.reconcile_reviewed_bahrain_hawar(framed,'i')
            updated=reconcile(old,source,'i')
        before=ET.fromstring(original)
        after=ET.fromstring(updated)
        approved=lambda root:[dict(p.attrib) for p in root.iter(SVG+'path')
                              if p.get('fill')=='url(#land)']
        self.assertEqual(approved(before),approved(after))
        self.assertEqual(len(approved(after)),2)
        self.assertEqual(after.get('viewBox'),'0 0 1200 760')
        foreign=[p for p in after.iter(SVG+'path') if p.get('data-map-context-legacy')=='hawar']
        self.assertEqual(len(foreign),1)
        self.assertEqual(hashlib.sha256(foreign[0].get('d').encode()).hexdigest(),PINNED_PATH_SHA)
        self.assertEqual(foreign[0].get('d').count('M '),1)
        self.assertIn('QAT-ADM0-15585745',updated)
        self.assertIn('ODbL 1.0',updated)
        with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=updated.encode(),
                             output_width=1200,output_height=760))) as image:
            image.load()
            self.assertEqual(image.size,(1200,760))
        with self.assertRaises(ValueError):
            reconcile(old,source,'l')


if __name__=='__main__':unittest.main()
