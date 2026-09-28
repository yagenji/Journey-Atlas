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

# Multi-path Singapore target is a source-approved group fill, not a direct path fill.
APPROVED_EXCEPTION_PATHS = {
    "singapore": (5, "237292bac3e9c90204fa4e2169d588deb3709916c823dac254cd4383f69121a5", "Singapore Land Authority"),
    "macau": (1, "44bdca23d43ee30484e9fcf911a2b373c86030c54638edbe0810875d60d35eb1", "Xiangzhou"),
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

    def test_reconciled_shoreline_context_preserves_all_approved_country_paths(self):
        for slug, (count, approved_hash, source_name) in APPROVED_EXCEPTION_PATHS.items():
            with self.subTest(country=slug):
                source = (ROOT / "assets/images" / slug / "map-atlas-v1.svg").read_bytes()
                root = ET.fromstring(source)
                self.assertEqual(root.get("viewBox"), "0 0 1200 760")
                parents = {child: parent for parent in root.iter() for child in parent}
                originals = []
                for node in root.iter(SVG + "path"):
                    ancestor = node
                    while ancestor is not None and "fill" not in ancestor.attrib:
                        ancestor = parents.get(ancestor)
                    if ancestor is not None and ancestor.get("fill") == "url(#land)":
                        originals.append(node.get("d", ""))
                self.assertEqual(len(originals), count)
                self.assertEqual(hashlib.sha256("\n".join(originals).encode()).hexdigest(), approved_hash)
                contexts = [g for g in root.iter(SVG + "g") if g.get("id") == "geographic-context"]
                self.assertEqual(len(contexts), 1)
                self.assertTrue(any(p.get("fill") == "#e4e0ce" for p in contexts[0].iter(SVG + "path")))
                description = "".join(contexts[0].itertext())
                self.assertIn("OpenStreetMap", description)
                self.assertIn(source_name, description)
                for color in (b"#eaf2f4", b"#dcebf0", b"#d0e3eb"):
                    self.assertIn(color, source)

    def test_kuwait_city_inset_has_no_duplicate_national_context(self):
        root = ET.parse(ROOT / "assets/images/kuwait/map-atlas-v1.svg").getroot()
        country = [p.get("d", "") for p in root.iter(SVG + "path") if p.get("fill") == "url(#land)"]
        self.assertEqual(len(country), 2)
        self.assertEqual(hashlib.sha256("\n".join(country).encode()).hexdigest(), "564b9be86b6c43bfe4698e3e1db74ab5014087486f21578f41a141d55b71db38")
        context = [p.get("data-map-context-region") for p in root.iter(SVG + "path") if p.get("data-map-context-region")]
        self.assertEqual(context, ["country"])

    def test_qatar_doha_inset_has_no_duplicate_national_context(self):
        root = ET.parse(ROOT / "assets/images/qatar/map-atlas-v1.svg").getroot()
        self.assertEqual(root.get("viewBox"), "0 0 1200 760")
        country = [p.get("d", "") for p in root.iter(SVG + "path") if p.get("fill") == "url(#land)"]
        self.assertEqual(len(country), 2)
        self.assertEqual(hashlib.sha256("\n".join(country).encode()).hexdigest(), "bceb87afccf7706ddcefa5f03d0c5756779b9b18ca40da173ffe4788e42fdff2")
        context = [p.get("data-map-context-legacy") for p in root.iter(SVG + "path") if p.get("data-map-context-legacy")]
        self.assertEqual(context, ["national-base"])

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
