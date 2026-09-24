#!/usr/bin/env python3
"""Stage 2 guards for the five pre-existing context maps not covered by prior exceptions."""
import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from apply_exact_target_clip import CLIP_ID, apply_exact_target_negative_clip  # noqa: E402

SVG='{http://www.w3.org/2000/svg}'
CASES={
    'cuba': 'GSHHS intermediate-resolution',
    'azerbaijan': 'Caspian coastline: GSHHS intermediate',
    'jamaica': 'Natural Earth 1:10m JAM ADM0',
    'grenada': 'geoBoundaries gbOpen ADM0',
    'stkittsnevis': 'Natural Earth Admin-0 1:10m Saint Kitts and Nevis',
}


def git_blob(raw):
    return hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()


def target_paths(root):
    parents={child:parent for parent in root.iter() for child in parent}
    result=[]
    for path in root.iter(SVG+'path'):
        cursor=path
        while cursor is not None and 'fill' not in cursor.attrib:
            cursor=parents.get(cursor)
        if cursor is not None and cursor.get('fill')=='url(#land)':
            result.append(ET.tostring(path,encoding='unicode'))
    return result


class ExistingContextSourceBackedTest(unittest.TestCase):
    def test_existing_context_maps_are_source_pinned_and_exactly_excluded(self):
        for slug,source_phrase in CASES.items():
            with self.subTest(slug=slug):
                country=json.loads((ROOT/'data/countries'/f'{slug}.json').read_text(encoding='utf-8'))
                source_path=ROOT/country['map']['svg']
                raw=source_path.read_bytes()
                self.assertIn(source_phrase,country['map']['source'])

                source=raw.decode('utf-8')
                original=ET.fromstring(source)
                self.assertEqual(original.get('viewBox'),'0 0 1200 760')
                before=target_paths(original)
                self.assertTrue(before)
                context=original.find(".//*[@id='geographic-context']")
                self.assertIsNotNone(context)
                self.assertTrue(any((p.get('d') or '').strip() for p in context.iter(SVG+'path')))
                for color in ('#eaf2f4','#dcebf0','#d0e3eb'):
                    self.assertIn(color,source)

                staged=apply_exact_target_negative_clip(source)
                rendered=ET.fromstring(staged)
                self.assertEqual(target_paths(rendered),before)
                context=rendered.find(".//*[@id='geographic-context']")
                self.assertIsNotNone(context)
                self.assertTrue(context.get('clip-path'))
                if context.get('clip-path')==f'url(#{CLIP_ID})':
                    clip=rendered.find(f".//*[@id='{CLIP_ID}']")
                    self.assertIsNotNone(clip)
                    cut=clip.find(SVG+'path')
                    self.assertEqual(cut.get('clip-rule'),'evenodd')
                    self.assertTrue((cut.get('d') or '').startswith(
                        'M 0,0 L 1200,0 L 1200,760 L 0,760 Z '
                    ))

                with Image.open(BytesIO(cairosvg.svg2png(
                    bytestring=staged.encode('utf-8'),output_width=1200,output_height=760
                ))) as png:
                    png.load()
                    self.assertEqual(png.size,(1200,760))


if __name__=='__main__':
    unittest.main()
