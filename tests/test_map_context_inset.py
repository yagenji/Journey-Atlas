#!/usr/bin/env python3
"""Keep surrounding land inside the actual opaque zoom inset, under target land."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from add_country_map_context import add_context

NS = "{http://www.w3.org/2000/svg}"
BOUNDS = (46.45, 28.47, 48.5, 30.16)
REGIONS = [
    {"id": "country", "bounds": dict(zip(("west", "south", "east", "north"), BOUNDS)),
     "rect": {"x": 25, "y": 35, "width": 700, "height": 690}},
    {"id": "city", "bounds": {"west": 47.95, "south": 29.35, "east": 48.03, "north": 29.398},
     "rect": {"x": 750, "y": 110, "width": 430, "height": 540}},
]


def fixture(fill="#e7eeee", clip_width=430):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" '
            f'data-map-projection="multi-region-local-equirectangular-fit-v1">'
            f'<defs><linearGradient id="sea"><stop stop-color="#eef2ef"/>'
            f'<stop stop-color="#e4eceb"/><stop stop-color="#dce7e7"/>'
            f'</linearGradient><clipPath id="clip-city"><rect x="750" y="232" '
            f'width="{clip_width}" height="296"/></clipPath></defs>'
            f'<rect width="1200" height="760" fill="url(#sea)"/>'
            f'<g data-map-region="country"><path id="target-country" d="M1 1L2 2Z" '
            f'fill="url(#land)"/></g>'
            f'<g data-map-region="city" clip-path="url(#clip-city)">'
            f'<rect x="750" y="232" width="430" height="296" fill="{fill}"/>'
            f'<path id="target-city" d="M1 1L2 2Z" fill="url(#land)"/></g></svg>')


class OpaqueInsetTest(unittest.TestCase):
    def test_inline_context_after_inset_sea_before_target(self):
        source = fixture()
        output = add_context(source, BOUNDS,
                             {"country": "M 25,35 L 725,35 L 725,725 Z",
                              "city": "M 750,110 L 1180,110 L 1180,650 Z"}, "i", REGIONS)
        root = ET.fromstring(output)
        group = next(node for node in root.iter(NS + "g") if node.get("data-map-region") == "city")
        self.assertEqual(group.get("clip-path"), "url(#clip-city)")
        self.assertEqual([child.tag for child in group], [NS + "rect", NS + "path", NS + "path"])
        self.assertEqual(group[0].get("fill"), "#dcebf0")
        self.assertEqual(group[1].get("data-map-context-region"), "city")
        self.assertEqual(group[2].get("d"), "M1 1L2 2Z")
        self.assertEqual(root.find(f".//*[@id='target-country']").get("d"), "M1 1L2 2Z")
        global_context = root.find(f".//*[@id='geographic-context']")
        self.assertEqual([child.get("data-map-context-region") for child in global_context], ["country"])

    def test_mismatched_background_clip_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "background and clip rectangle differ"):
            add_context(fixture(clip_width=400), BOUNDS, {"country": "x", "city": "y"}, "i", REGIONS)
        with self.assertRaisesRegex(ValueError, "palette requires visual review"):
            add_context(fixture(fill="#123456"), BOUNDS, {"country": "x", "city": "y"}, "i", REGIONS)


if __name__ == "__main__":
    unittest.main()
