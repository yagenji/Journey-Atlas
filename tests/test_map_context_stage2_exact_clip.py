#!/usr/bin/env python3
"""Regression coverage for the Stage 2 exact target-negative clip."""
import json
import subprocess
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SVG='{http://www.w3.org/2000/svg}'
sys.path.insert(0,str(ROOT/'scripts'))

from apply_exact_target_clip import CLIP_ID  # noqa: E402


def approved_paths(root):
    parents={child:parent for parent in root.iter() for child in parent}
    result=[]
    for node in root.iter(SVG+'path'):
        cursor=node
        while cursor is not None and 'fill' not in cursor.attrib:
            cursor=parents.get(cursor)
        if cursor is not None and cursor.get('fill')=='url(#land)':
            result.append(ET.tostring(node,encoding='unicode'))
    return result


class ExactTargetClipPipelineTest(unittest.TestCase):
    def test_representative_existing_maps_preserve_targets_and_clip_context(self):
        # canonical, path-matrix, legacy, many-target island country, multi-region
        for slug in ('germany','estonia','maldives','japan','unitedstates'):
            with self.subTest(slug=slug):
                country_file=ROOT/'data/countries'/f'{slug}.json'
                country=json.loads(country_file.read_text(encoding='utf-8'))
                source=ROOT/country['map']['svg']
                original=ET.parse(source).getroot()
                before=approved_paths(original)
                self.assertTrue(before)

                with tempfile.TemporaryDirectory() as tmp:
                    output=Path(tmp)/f'{slug}.svg'
                    completed=subprocess.run([
                        sys.executable,str(ROOT/'scripts/add_country_map_context_existing.py'),
                        '--country-json',str(country_file),'--input',str(source),
                        '--output',str(output),'--resolution','i',
                    ],cwd=ROOT,capture_output=True,text=True,timeout=240)
                    self.assertEqual(completed.returncode,0,completed.stderr or completed.stdout)
                    text=output.read_text(encoding='utf-8')
                    root=ET.fromstring(text)
                    self.assertEqual(approved_paths(root),before)
                    context=root.find(".//*[@id='geographic-context']")
                    self.assertIsNotNone(context)

                    if any((p.get('d') or '').strip() for p in context.iter(SVG+'path')):
                        # Explicit reviewed exception clips may use a dedicated ID;
                        # all ordinary candidates must use the common exact clip.
                        clip_ref=context.get('clip-path','')
                        self.assertTrue(clip_ref)
                        if clip_ref==f'url(#{CLIP_ID})':
                            clip=root.find(f".//*[@id='{CLIP_ID}']")
                            self.assertIsNotNone(clip)
                            cut=clip.find(SVG+'path')
                            self.assertIsNotNone(cut)
                            self.assertEqual(cut.get('clip-rule'),'evenodd')
                            self.assertTrue((cut.get('d') or '').startswith(
                                'M 0,0 L 1200,0 L 1200,760 L 0,760 Z '
                            ))

                    with Image.open(BytesIO(cairosvg.svg2png(
                        bytestring=text.encode('utf-8'),output_width=1200,output_height=760
                    ))) as png:
                        png.load()
                        self.assertEqual(png.size,(1200,760))


if __name__=='__main__':
    unittest.main()
