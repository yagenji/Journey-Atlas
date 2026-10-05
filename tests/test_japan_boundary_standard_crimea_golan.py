"""Japanese boundary standard: Crimea is Ukraine, the Golan Heights are Syria.

Natural Earth's de facto Admin-0 assigns Crimea to Russia and the Golan Heights
to Israel. Japan does not recognise either, so the Country maps draw them as
Ukraine and Syria, the de facto Crimea line is not a border, and the 1974
Golan ceasefire line is dashed.
"""
import json
import math
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import japan_boundary_standard as jbs  # noqa: E402
import normalize_country_map_lakes as lakes  # noqa: E402


def target_contains(slug: str, lon: float, lat: float) -> bool:
    data = json.loads((ROOT / "data/countries" / f"{slug}.json").read_text(encoding="utf-8"))
    mp = data["map"]
    b = mp["bounds"]
    scale_lon = math.cos(math.radians((b["south"] + b["north"]) / 2))
    pw, ph = (b["east"] - b["west"]) * scale_lon, b["north"] - b["south"]
    scale = min(1200 / pw, 760 / ph)
    ox, oy = (1200 - pw * scale) / 2, (760 - ph * scale) / 2
    point = Point(ox + (lon - b["west"]) * scale_lon * scale, oy + (b["north"] - lat) * scale)
    svg = (ROOT / mp["svg"]).read_text(encoding="utf-8")
    return lakes._target_area(ET.fromstring(svg)).buffer(1.0).contains(point)


class CrimeaGolanTest(unittest.TestCase):
    def test_crimea_is_ukraine(self):
        for lon, lat in ((34.1, 45.0), (33.52, 44.6)):  # central Crimea, Sevastopol
            self.assertTrue(target_contains("ukraine", lon, lat))
        self.assertFalse(target_contains("russia", 34.1, 45.0))

    def test_golan_heights_are_syria(self):
        self.assertTrue(target_contains("syria", 35.78, 33.0))
        self.assertFalse(target_contains("israel", 35.78, 33.0))

    def test_de_facto_crimea_line_is_not_a_border(self):
        line = LineString([(33.6, 46.1), (34.0, 46.0)])
        self.assertTrue(jbs.is_excluded_boundary_line(line, {
            "FEATURECLA": "Disputed (please verify)", "FCLASS_JP": "Claim boundary",
            "ADM0_LEFT": "Russia", "ADM0_RIGHT": "Ukraine"}))

    def test_golan_ceasefire_line_is_dashed(self):
        for slug in ("israel", "syria", "jordan", "lebanon"):
            with self.subTest(slug=slug):
                svg = (ROOT / json.loads((ROOT / "data/countries" / f"{slug}.json").read_text(encoding="utf-8"))["map"]["svg"]).read_text(encoding="utf-8")
                self.assertIn('data-boundary="undetermined"', svg)


if __name__ == "__main__":
    unittest.main()
