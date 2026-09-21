"""Regression checks for SVGs individually promoted to the map-context review PR.

These tests only protect reviewed assets; successful CI is not geographic QA or
permission to merge the complete migration. Original national silhouettes must
remain byte-for-byte identical to the approved geometry.
"""
from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"

# SHA-256 of each approved source SVG's national path d, NOT the new context.
APPROVED_LAND_PATH = {
    "andorra": "b2312abc107349cb1c7b3c73f36b93a625d73e0167c57c126783693ab08ff94c",
    "liechtenstein": "7f4164010e7fbc6cdf04a8592af02d28476e573c1014a777d4f134e5ec8cd7b2",
    "sanmarino": "02b7fc2d4e641c09aa2c5471cec88d4e7c65a7dbe696ada6295ce51306067c38",
    "vaticancity": "8cd6677ed4c42a7d2041d918ed5bf69b158c878d7f929896e49b089b877ce973",
    "monaco": "6338d1de050b6cf8ae063e5c6e64cf582500b0f6117f84ad69976690691171fe",
}


class ReviewedMapContextAssets(unittest.TestCase):
    def test_approved_land_path_is_unchanged(self):
        for slug, approved_hash in APPROVED_LAND_PATH.items():
            with self.subTest(country=slug):
                source = (ROOT / "assets/images" / slug / "map-atlas-v1.svg").read_bytes()
                root = ET.fromstring(source)
                self.assertEqual(root.get("viewBox"), "0 0 1200 760")
                target = [p for p in root.iter(SVG + "path") if p.get("fill") == "url(#land)"]
                self.assertEqual(len(target), 1)
                self.assertEqual(hashlib.sha256(target[0].get("d", "").encode()).hexdigest(), approved_hash)
                context = [g for g in root.iter(SVG + "g") if g.get("id") == "geographic-context"]
                self.assertEqual(len(context), 1)
                self.assertTrue(any(p.get("fill") == "#e4e0ce" for p in context[0].iter(SVG + "path")))
                for color in (b"#eaf2f4", b"#dcebf0", b"#d0e3eb"):
                    self.assertIn(color, source)

    def test_landlocked_context_covers_full_canvas_without_a_fake_coast(self):
        for slug in ("andorra", "liechtenstein", "sanmarino", "vaticancity"):
            with self.subTest(country=slug):
                root = ET.parse(ROOT / "assets/images" / slug / "map-atlas-v1.svg").getroot()
                context = next(g for g in root.iter(SVG + "g") if g.get("id") == "geographic-context")
                paths = list(context.iter(SVG + "path"))
                self.assertEqual(len(paths), 1)
                d = paths[0].get("d", "").replace("-0.0", "0.0")
                self.assertEqual(d, "M 0.0,0.0 L 1200.0,0.0 L 1200.0,760.0 L 0.0,760.0 L 0.0,0.0 Z")


if __name__ == "__main__":
    unittest.main()
