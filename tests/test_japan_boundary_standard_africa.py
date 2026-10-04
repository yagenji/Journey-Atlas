"""Japanese boundary standard on African Country maps, and borders above lakes.

* Somaliland is not recognised by Japan: no Somaliland-Somalia border line.
* Lines Natural Earth marks unrecognised from Japan's point of view (the
  Moroccan berm in Western Sahara) are not drawn.
* Disputed / indefinite boundaries are dashed (国境未確定): Western Sahara at
  27°40'N, Hala'ib, Abyei, Ilemi, Ethiopia-Somalia.
* Where a map draws lakes, national borders and the target outline stay above
  the water (MAP_QUALITY).
"""
import json
import re
import sys
import unittest
from pathlib import Path

from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import japan_boundary_standard as jbs  # noqa: E402


def current_svg(slug: str) -> str:
    data = json.loads((ROOT / "data/countries" / f"{slug}.json").read_text(encoding="utf-8"))
    return (ROOT / data["map"]["svg"]).read_text(encoding="utf-8")


class JapaneseStandardAfricaTest(unittest.TestCase):
    def test_unrecognised_lines_are_excluded(self):
        line = LineString([(48.0, 9.0), (49.0, 10.0)])
        self.assertTrue(jbs.is_excluded_boundary_line(line, {"ADM0_LEFT": "Somaliland", "ADM0_RIGHT": "Somalia",
                                                             "FEATURECLA": "Disputed (please verify)"}))
        self.assertTrue(jbs.is_excluded_boundary_line(line, {"FEATURECLA": "Line of control (please verify)",
                                                             "FCLASS_JP": "Unrecognized"}))
        self.assertFalse(jbs.is_excluded_boundary_line(line, {"ADM0_LEFT": "Somaliland", "ADM0_RIGHT": "Ethiopia",
                                                              "FEATURECLA": "International boundary (verify)"}))

    def test_disputed_boundaries_are_dashed(self):
        for slug in ("morocco", "algeria", "egypt", "sudan", "southsudan", "ethiopia", "kenya", "somalia"):
            with self.subTest(slug=slug):
                self.assertIn('data-boundary="undetermined"', current_svg(slug))

    def test_no_hand_made_western_sahara_overlays(self):
        for slug in ("morocco", "mauritania"):
            with self.subTest(slug=slug):
                self.assertNotRegex(current_svg(slug), r'id="western-sahara-(clean-mask|border-overlay|morocco-boundary)"')


class BordersAboveWaterTest(unittest.TestCase):
    def test_borders_drawn_after_lakes(self):
        checked = 0
        for path in sorted((ROOT / "data/countries").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            mp = data.get("map") or {}
            if not mp.get("svg") or mp.get("regions") or "AFRICA" not in str(data.get("region", "")).upper():
                continue
            svg = (ROOT / mp["svg"]).read_text(encoding="utf-8")
            water = [m.start() for m in re.finditer(r'<g\b[^>]*\bid="inland-water-auto', svg)]
            borders = svg.find('id="context-national-borders"')
            if not water or borders < 0:
                continue
            checked += 1
            with self.subTest(slug=path.stem):
                self.assertGreater(borders, max(water))
        self.assertGreater(checked, 10)


if __name__ == "__main__":
    unittest.main()
