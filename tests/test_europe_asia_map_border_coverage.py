#!/usr/bin/env python3
"""Regression guard for Europe/Asia surrounding-country border context."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# These published maps do not need a separate surrounding-country boundary
# layer: the visible composition contains no foreign-vs-foreign land border.
# Portugal and Qatar show only the target-vs-neighbour land border, already
# represented by the dominant target-country outline; Bahrain is island/inset
# context without an in-frame land boundary. Monaco's only land border (France)
# is the target outline; Natural Earth's line is a straight segment at that scale.
NO_SEPARATE_CONTEXT_BORDER = {
    "bahrain",
    "cyprus",
    "iceland",
    "maldives",
    "malta",
    "monaco",
    "portugal",
    "qatar",
    "srilanka",
    "taiwan",
    "vaticancity",
}


class EuropeAsiaMapBorderCoverageTest(unittest.TestCase):
    def test_published_europe_asia_maps_have_required_context_borders(self):
        taxonomy = json.loads((ROOT / "data/region-taxonomy.json").read_text(encoding="utf-8"))
        registry_raw = json.loads((ROOT / "data/atlas-destinations.json").read_text(encoding="utf-8"))
        registry = registry_raw if isinstance(registry_raw, list) else registry_raw["destinations"]

        regions = {region["id"]: region for region in taxonomy["regions"]}
        scope_iso2 = set(regions["europe"]["iso2"]) | set(regions["asia"]["iso2"])
        scoped = [
            item for item in registry
            if item.get("atlasPublished") and item.get("iso2") in scope_iso2
        ]
        self.assertTrue(scoped)

        missing = []
        out_of_canvas = []
        wrong_layer_order = []
        duplicate_groups = []

        for item in scoped:
            slug = item["slug"]
            country = json.loads((ROOT / "data/countries" / f"{slug}.json").read_text(encoding="utf-8"))
            svg_path = ROOT / country["map"]["svg"]
            svg = svg_path.read_text(encoding="utf-8")

            count = svg.count('id="context-national-borders"')
            if slug in NO_SEPARATE_CONTEXT_BORDER:
                continue
            if count == 0:
                missing.append(slug)
                continue
            if count != 1:
                duplicate_groups.append(slug)
                continue

            border_at = svg.index('id="context-national-borders"')
            target_candidates = [
                pos for pos in (
                    svg.find('fill="url(#land)"'),
                    svg.find('fill="url(#country)"'),
                )
                if pos >= 0
            ]
            target_at = min(target_candidates) if target_candidates else -1
            # Above the target only when lifted over inland water and clipped to the
            # target exterior (normalize_country_map_lakes.raise_borders_above_water).
            clipped = svg[:border_at].rstrip().endswith('<g clip-path="url(#map-borders-target-negative)"><g')
            if target_at < 0 or (border_at > target_at and not clipped):
                wrong_layer_order.append(slug)

            end = svg.find("</g>", border_at)
            self.assertGreater(end, border_at, slug)
            group = svg[border_at:end]
            coords = [
                (float(x), float(y))
                for x, y in re.findall(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", group)
            ]
            if not coords or not all(
                -0.2 <= x <= 1200.2 and -0.2 <= y <= 760.2
                for x, y in coords
            ):
                out_of_canvas.append(slug)

        self.assertEqual([], missing, f"Missing border layer: {missing}")
        self.assertEqual([], duplicate_groups, f"Duplicate border groups: {duplicate_groups}")
        self.assertEqual([], wrong_layer_order, f"Border layer must stay below target or be clipped outside it: {wrong_layer_order}")
        self.assertEqual([], out_of_canvas, f"Border coordinates outside canvas: {out_of_canvas}")


if __name__ == "__main__":
    unittest.main()
