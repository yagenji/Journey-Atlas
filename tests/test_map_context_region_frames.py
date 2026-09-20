#!/usr/bin/env python3
"""Ensure legacy regional viewports cannot masquerade as a land boundary."""
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from add_country_map_context_existing import frame_unframed_region_context

REGIONS = [
    {"id": "mainland", "rect": {"x": 520, "y": 35, "width": 430, "height": 690}},
    {"id": "azores", "rect": {"x": 40, "y": 80, "width": 380, "height": 260}},
    {"id": "madeira", "rect": {"x": 95, "y": 500, "width": 300, "height": 170}},
]
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" '
       'data-map-projection="multi-region-local-equirectangular-fit-v1">'
       '<defs>' + ''.join(f'<clipPath id="map-context-clip-{r["id"]}">'
                        f'<rect x="{r["rect"]["x"]}" y="{r["rect"]["y"]}" '
                        f'width="{r["rect"]["width"]}" height="{r["rect"]["height"]}"/>'
                        '</clipPath>' for r in REGIONS) + '</defs>'
       '<g id="geographic-context">'
       + ''.join(f'<path data-map-context-region="{r["id"]}" '
                 f'clip-path="url(#map-context-clip-{r["id"]})" d="M0 0Z"/>'
                 for r in REGIONS) + '</g>'
       '<path id="approved-land" d="M1 2L3 4Z" fill="url(#land)"/>'
       '<g id="approved-markers"><circle cx="3" cy="4" r="2"/></g></svg>')


class FrameUnframedRegionsTest(unittest.TestCase):
    def test_portugal_style_regions_have_only_context_frames_added(self):
        updated = frame_unframed_region_context(SVG, REGIONS)
        self.assertIn('id="geographic-context-region-frames"', updated)
        self.assertEqual(updated.count('data-map-context-frame='), 3)
        self.assertEqual(updated.split('<g id="geographic-context-region-frames">')[0],
                         SVG.removesuffix('</svg>'))
        before, after = ET.fromstring(SVG), ET.fromstring(updated)
        for ident in ('approved-land', 'approved-markers'):
            self.assertEqual(ET.tostring(before.find(f".//*[@id='{ident}']")),
                             ET.tostring(after.find(f".//*[@id='{ident}']")))
        self.assertEqual(after.attrib['viewBox'], '0 0 1200 760')

    def test_existing_us_and_kuwait_style_frames_are_unchanged(self):
        already_framed = SVG.replace('</svg>',
                                    '<rect x="40" y="80" width="380" height="260" '
                                    'stroke="#879b9b" fill="none"/></svg>')
        self.assertEqual(frame_unframed_region_context(already_framed, REGIONS),
                         already_framed)
        self.assertEqual(frame_unframed_region_context(SVG, None), SVG)
        self.assertEqual(frame_unframed_region_context(SVG.replace(
            'id="geographic-context"', 'id="other"'), REGIONS),
            SVG.replace('id="geographic-context"', 'id="other"'))

    def test_legacy_composite_without_region_context_paths_is_not_reframed(self):
        legacy = SVG.replace('data-map-context-region="mainland"', 'data-legacy-region="mainland"')
        legacy = legacy.replace('data-map-context-region="azores"', 'data-legacy-region="azores"')
        legacy = legacy.replace('data-map-context-region="madeira"', 'data-legacy-region="madeira"')
        self.assertEqual(frame_unframed_region_context(legacy, REGIONS), legacy)

    def test_fail_closed_on_mismatched_region_and_outside_canvas(self):
        with self.assertRaisesRegex(ValueError, 'do not match'):
            frame_unframed_region_context(SVG.replace(
                'data-map-context-region="madeira"',
                'data-map-context-region="unapproved"'), REGIONS)
        invalid = [dict(r) for r in REGIONS]
        invalid[0] = {**invalid[0], 'rect': {**invalid[0]['rect'], 'x': 900}}
        with self.assertRaisesRegex(ValueError, 'outside'):
            frame_unframed_region_context(SVG, invalid)

    def test_incorrect_context_clips_are_never_dressed_as_valid_frames(self):
        with self.assertRaisesRegex(ValueError, 'not clipped'):
            frame_unframed_region_context(SVG.replace(
                'clip-path="url(#map-context-clip-mainland)"',
                'clip-path="url(#map-context-clip-azores)"'), REGIONS)
        with self.assertRaisesRegex(ValueError, 'clip rectangle'):
            frame_unframed_region_context(SVG.replace(
                '<rect x="520" y="35"', '<rect x="521" y="35"'), REGIONS)
        with self.assertRaisesRegex(ValueError, 'clip rectangle'):
            frame_unframed_region_context(SVG.replace(
                '<rect x="520" y="35"', '<rect y="35"'), REGIONS)
        with self.assertRaisesRegex(ValueError, 'clip rectangle'):
            frame_unframed_region_context(SVG.replace(
                '<rect x="520" y="35"', '<rect x="nan" y="35"'), REGIONS)
        with self.assertRaisesRegex(ValueError, 'do not match'):
            frame_unframed_region_context(SVG.replace(
                '<path data-map-context-region="mainland"',
                '<path data-map-context-region="azores"'), REGIONS)

    def test_real_portugal_preview_preserves_approved_paths_and_renders_frames(self):
        """Use the real Country JSON/SVG, not just a synthetic three-region fixture."""
        import json
        import re
        import subprocess
        import tempfile
        from io import BytesIO

        import cairosvg
        from PIL import Image, ImageChops

        repository = Path(__file__).resolve().parents[1]
        country_json = repository / 'data/countries/portugal.json'
        country = json.loads(country_json.read_text(encoding='utf-8'))
        source_path = repository / country['map']['svg']
        original = ET.fromstring(source_path.read_text(encoding='utf-8'))
        namespace = '{http://www.w3.org/2000/svg}'

        with tempfile.TemporaryDirectory(prefix='portugal-map-context-') as directory:
            preview_path = Path(directory) / 'portugal-preview.svg'
            subprocess.run(
                [sys.executable, str(repository / 'scripts/add_country_map_context_existing.py'),
                 '--country-json', str(country_json), '--input', str(source_path),
                 '--output', str(preview_path)],
                cwd=repository, check=True, capture_output=True, text=True, timeout=180)
            preview = preview_path.read_text(encoding='utf-8')
            result = ET.fromstring(preview)
            self.assertEqual(original.get('viewBox'), '0 0 1200 760')
            self.assertEqual(result.get('viewBox'), original.get('viewBox'))

            # Compare every previously approved path, including islands and markers.
            context = result.find(".//*[@id='geographic-context']")
            self.assertIsNotNone(context)
            added_paths = set(context.iter(namespace + 'path'))
            original_paths = [ET.tostring(path) for path in original.iter(namespace + 'path')]
            result_paths = [ET.tostring(path) for path in result.iter(namespace + 'path')
                            if path not in added_paths]
            self.assertEqual(result_paths, original_paths)

            frames = [item for item in result.iter(namespace + 'rect')
                      if item.get('data-map-context-frame')]
            self.assertEqual({frame.get('data-map-context-frame') for frame in frames},
                             {region['id'] for region in country['map']['regions']})
            for frame in frames:
                rect = next(region['rect'] for region in country['map']['regions']
                            if region['id'] == frame.get('data-map-context-frame'))
                for key in ('x', 'y', 'width', 'height'):
                    self.assertEqual(float(frame.get(key)), float(rect[key]))

            frame_markup = re.search(
                r'<g id="geographic-context-region-frames">.*?</g>', preview)
            self.assertIsNotNone(frame_markup)
            unframed = preview.replace(frame_markup.group(), '', 1)
            images = []
            for svg in (unframed, preview):
                with Image.open(BytesIO(cairosvg.svg2png(
                        bytestring=svg.encode('utf-8'), output_width=1200,
                        output_height=760))) as image:
                    image.load()
                    self.assertEqual(image.size, (1200, 760))
                    images.append(image.convert('RGBA'))
            self.assertIsNotNone(ImageChops.difference(*images).getbbox(),
                                 'Region frames must be visible at native size')


if __name__ == '__main__':
    unittest.main()
