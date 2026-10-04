"""Country map line widths must render at the shared standard on the page.

Maps are shown as <img> scaled down from 1200x760, so widths are compared in
viewBox units after applying each element's transforms. `non-scaling-stroke`
would fix widths in screen pixels and make one map's lines look thicker.
"""
import json
import math
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from svgelements import Matrix

ROOT = Path(__file__).resolve().parents[1]
NS = "{http://www.w3.org/2000/svg}"
TARGET_OUTLINE = "#31576a"


def current_maps():
    for path in sorted((ROOT / "data/countries").glob("*.json")):
        svg = (json.loads(path.read_text(encoding="utf-8")).get("map") or {}).get("svg")
        if svg:
            yield path.stem, ROOT / svg.lstrip("/")


def stroked(root):
    """Yield (element, stroke, effective width) for every stroked shape."""
    def walk(el, ctm, width, stroke):
        m = Matrix(el.get("transform")) * ctm if el.get("transform") else ctm
        width = el.get("stroke-width", width)
        stroke = el.get("stroke", stroke)
        if el.tag.replace(NS, "") in {"path", "polyline", "line", "polygon"} and stroke not in (None, "none"):
            scale = math.sqrt(math.hypot(m.a, m.b) * math.hypot(m.c, m.d))
            yield el, stroke.lower(), float(width) * scale
        for child in el:
            if child.tag in (NS + "defs", NS + "clipPath", NS + "mask"):
                continue
            yield from walk(child, m, width, stroke)
    yield from walk(root, Matrix(), "1", None)


class MapStrokeWidthTest(unittest.TestCase):
    def test_no_non_scaling_stroke(self):
        offenders = [slug for slug, svg in current_maps() if "non-scaling-stroke" in svg.read_text(encoding="utf-8")]
        self.assertEqual(offenders, [])

    def test_target_outline_effective_width(self):
        offenders = []
        for slug, svg in current_maps():
            root = ET.fromstring(svg.read_bytes())
            for el, stroke, width in stroked(root):
                if stroke == TARGET_OUTLINE and abs(width - 1.5) > 0.06:
                    offenders.append(f"{slug}: {width:.2f}")
                    break
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
