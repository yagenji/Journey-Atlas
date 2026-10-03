#!/usr/bin/env python3
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import add_country_border_context as borders  # noqa: E402


class CountryBorderContextTest(unittest.TestCase):
    BOUNDS = {"west": 10.0, "south": 40.0, "east": 12.0, "north": 42.0}
    SVG = (
        '<svg viewBox="0 0 1200 760" data-map-projection="local-equirectangular-fit-v1">'
        '<defs><linearGradient id="land"/></defs><rect width="1200" height="760"/>'
        '<path d="M100,100 L200,100 L200,200 Z" fill="url(#land)"/></svg>'
    )

    def _dataset(self, coordinates, properties=None):
        return self._features_dataset([{
            "type": "Feature",
            "properties": properties or {},
            "geometry": {"type": "LineString", "coordinates": coordinates},
        }])

    def _features_dataset(self, features):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".geojson", delete=False, encoding="utf-8")
        json.dump({"type": "FeatureCollection", "features": features}, tmp)
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return Path(tmp.name)

    def test_clips_projected_border_to_canvas_and_places_it_below_target(self):
        dataset = self._dataset([[0.0, 41.0], [11.0, 41.0], [20.0, 41.0]])
        result = borders.add_borders(self.SVG, self.BOUNDS, dataset=dataset)
        self.assertIn('id="context-national-borders"', result)
        self.assertLess(result.index('id="context-national-borders"'), result.index('fill="url(#land)"'))
        group = result[result.index('id="context-national-borders"'):result.index("</g>")]
        coords = [(float(x), float(y)) for x, y in re.findall(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", group)]
        self.assertTrue(coords)
        self.assertTrue(all(-0.2 <= x <= 1200.2 and -0.2 <= y <= 760.2 for x, y in coords))

    def test_no_visible_land_boundary_leaves_svg_unchanged(self):
        dataset = self._dataset([[30.0, 10.0], [31.0, 11.0]])
        self.assertEqual(self.SVG, borders.add_borders(self.SVG, self.BOUNDS, dataset=dataset))

    def test_target_iso_omits_only_target_adjacent_boundary(self):
        dataset = self._features_dataset([
            {
                "type": "Feature",
                "properties": {"ADM0_A3_L": "GBR", "ADM0_A3_R": "IRL"},
                "geometry": {"type": "LineString", "coordinates": [[10.2, 40.4], [10.4, 40.6]]},
            },
            {
                "type": "Feature",
                "properties": {"ADM0_A3_L": "AAA", "ADM0_A3_R": "BBB"},
                "geometry": {"type": "LineString", "coordinates": [[11.2, 41.4], [11.4, 41.6]]},
            },
        ])
        all_lines = borders.make_border_path(self.BOUNDS, dataset=dataset)
        filtered = borders.make_border_path(self.BOUNDS, dataset=dataset, target_iso3="GBR")
        self.assertGreater(all_lines.count("M"), filtered.count("M"))
        self.assertEqual(1, filtered.count("M"))

    def test_replace_borders_preserves_target_geometry(self):
        dataset = self._features_dataset([
            {
                "type": "Feature",
                "properties": {"ADM0_A3_L": "GBR", "ADM0_A3_R": "IRL"},
                "geometry": {"type": "LineString", "coordinates": [[10.2, 40.4], [10.4, 40.6]]},
            },
            {
                "type": "Feature",
                "properties": {"ADM0_A3_L": "AAA", "ADM0_A3_R": "BBB"},
                "geometry": {"type": "LineString", "coordinates": [[11.2, 41.4], [11.4, 41.6]]},
            },
        ])
        initial = borders.add_borders(self.SVG, self.BOUNDS, dataset=dataset)
        target = '<path d="M100,100 L200,100 L200,200 Z" fill="url(#land)"/>'
        replaced = borders.replace_borders(
            initial,
            self.BOUNDS,
            dataset=dataset,
            target_iso3="GBR",
        )
        self.assertIn(target, replaced)
        self.assertEqual(1, replaced.count('id="context-national-borders"'))
        self.assertIn("target-adjacent GBR lines omitted", replaced)
        group = replaced[replaced.index('id="context-national-borders"'):replaced.index("</g>")]
        self.assertEqual(1, group.count("M"))


if __name__ == "__main__":
    unittest.main()
