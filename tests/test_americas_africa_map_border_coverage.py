#!/usr/bin/env python3
"""Regression guard for Americas/Africa surrounding-country border context."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Published island / target-separated compositions where the visible map does
# not contain a foreign-vs-foreign land boundary that needs a separate context
# border. Target-vs-neighbour borders remain represented by the target outline.
NO_SEPARATE_CONTEXT_BORDER = {
    "antiguabarbuda",
    "bahamas",
    "barbados",
    "capeverde",
    "comoros",
    "dominica",
    "dominicanrepublic",
    "grenada",
    "haiti",
    "jamaica",
    "saotomeprincipe",
    "seychelles",
    "stkittsnevis",
    "stlucia",
    "stvincentgrenadines",
    "trinidadtobago",
}

REGION_IDS = {"north-america", "south-america", "africa"}


class AmericasAfricaMapBorderCoverageTest(unittest.TestCase):
    def test_published_maps_have_required_surrounding_borders(self):
        taxonomy = json.loads((ROOT / "data/region-taxonomy.json").read_text(encoding="utf-8"))
        registry_raw = json.loads((ROOT / "data/atlas-destinations.json").read_text(encoding="utf-8"))
        registry = registry_raw if isinstance(registry_raw, list) else registry_raw["destinations"]

        regions = {region["id"]: region for region in taxonomy["regions"]}
        scope_iso2 = set()
        for region_id in REGION_IDS:
            scope_iso2.update(regions[region_id]["iso2"])

        scoped = [
            item for item in registry
            if item.get("atlasPublished") and item.get("iso2") in scope_iso2
        ]
        self.assertEqual(73, len(scoped))

        missing = []
        duplicate_groups = []
        wrong_layer_order = []
        out_of_canvas = []

        for item in scoped:
            slug = item["slug"]
            country = json.loads((ROOT / "data/countries" / f"{slug}.json").read_text(encoding="utf-8"))
            svg = (ROOT / country["map"]["svg"]).read_text(encoding="utf-8")

            target_candidates = [
                pos for pos in (
                    svg.find('fill="url(#land)"'),
                    svg.find('fill="url(#country)"'),
                )
                if pos >= 0
            ]
            target_at = min(target_candidates) if target_candidates else -1
            count = svg.count('id="context-national-borders"')

            if count > 1:
                duplicate_groups.append(slug)
                continue

            if count == 1:
                border_at = svg.index('id="context-national-borders"')
                if target_at < 0 or border_at > target_at:
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
                continue

            if slug in NO_SEPARATE_CONTEXT_BORDER:
                continue

            context_at = svg.find('id="geographic-context"')
            context_end = svg.find("</g>", context_at) if context_at >= 0 else -1
            context = svg[context_at:context_end] if context_at >= 0 and context_end > context_at else ""
            if 'stroke="#b6bbaf"' not in context:
                missing.append(slug)
                continue
            if target_at >= 0 and context_at > target_at:
                wrong_layer_order.append(slug)

        self.assertEqual([], missing, f"Missing visible surrounding border context: {missing}")
        self.assertEqual([], duplicate_groups, f"Duplicate border groups: {duplicate_groups}")
        self.assertEqual([], wrong_layer_order, f"Border context must stay below target: {wrong_layer_order}")
        self.assertEqual([], out_of_canvas, f"Border coordinates outside canvas: {out_of_canvas}")


if __name__ == "__main__":
    unittest.main()
