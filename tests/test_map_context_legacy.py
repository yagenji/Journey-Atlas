#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import add_country_map_context_legacy as legacy


class LegacyMapContextTests(unittest.TestCase):
    def test_hong_kong_accepts_shadow_and_visible_use_of_same_land_shape(self):
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" data-map-projection="local-equirectangular-fit-v1">
        <defs><linearGradient id="sea"><stop stop-color="#eef2ef"/><stop stop-color="#e4eceb"/><stop stop-color="#dce7e7"/></linearGradient></defs>
        <rect width="1200" height="760" fill="url(#sea)"/>
        <g id="land-shape"><path d="M0,0 L1,0 L1,1 Z"/></g>
        <use href="#land-shape" fill="url(#land)" filter="url(#shadow)"/>
        <use href="#land-shape" fill="url(#land)"/>
        <use href="#land-shape" fill="#31576a"/>
        </svg>'''
        config = {"map": {"bounds": {"west": 113.7, "south": 22.1, "east": 114.6, "north": 22.7}}}
        with patch.object(legacy, "_simple_context", return_value="ok") as call:
            self.assertEqual(legacy._hong_kong(svg, config, "i"), "ok")
            call.assert_called_once()

    def test_wide_canvas_uses_only_one_world_cycle_and_clips_polar_sideband(self):
        calls = []
        def fake(bounds, resolution):
            calls.append(bounds)
            return None
        with patch.object(legacy.core, "context_geometry", side_effect=fake):
            legacy._split_context_geometry((-210.0, 30.0, 420.0, 110.0), "i")
        self.assertGreaterEqual(len(calls), 2)
        self.assertTrue(all(e - w <= 179.5 + 1e-9 for w, s, e, n in calls))
        self.assertTrue(all(-89 <= s < n <= 89 for w, s, e, n in calls))
        west = min(c[0] for c in calls)
        east = max(c[2] for c in calls)
        self.assertLessEqual(east - west, 360.0)

    def test_wide_canvas_does_not_accept_nonfinite_extent(self):
        with self.assertRaises(ValueError):
            legacy._split_context_geometry((float('nan'), 0, 10, 10), "i")

    def test_legacy_region_sampling_clips_extended_query_to_original_viewport(self):
        bounds = (-61.91, 16.97, -61.66, 17.185)
        with patch.object(legacy, "_split_context_geometry", side_effect=lambda b, r: box(*b)) as sampled:
            actual = legacy._sample_region_beyond_viewport(bounds, "i")
        self.assertTrue(actual.equals(box(*bounds)))
        query = sampled.call_args.args[0]
        self.assertLess(query[0], bounds[0])
        self.assertLess(query[1], bounds[1])
        self.assertGreater(query[2], bounds[2])
        self.assertGreater(query[3], bounds[3])

    def test_legacy_region_rects_still_reject_actual_overlap(self):
        def region(x, y, w, h):
            return {"bounds": {"west": 0, "south": 0, "east": 1, "north": 1},
                    "rect": {"x": x, "y": y, "width": w, "height": h}}
        legacy._validate_region_rects([region(0, 0, 100, 100), region(0, 101, 100, 100)])
        with self.assertRaisesRegex(ValueError, "overlap"):
            legacy._validate_region_rects([region(0, 0, 100, 100), region(50, 50, 100, 100)])

    def test_real_antigua_inset_removes_false_edge_wedge_without_changing_approved_paths(self):
        source = ROOT / "assets/images/antiguabarbuda/map-atlas-v1.svg"
        country = ROOT / "data/countries/antiguabarbuda.json"
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "antigua-preview.svg"
            legacy.generate(country, source, output, "i")
            before = ET.fromstring(source.read_text(encoding="utf-8"))
            after = ET.fromstring(output.read_text(encoding="utf-8"))
            approved = lambda root: [ET.tostring(p) for p in legacy.core.approved_land_paths(root)[0]]
            self.assertTrue(approved(before))
            self.assertEqual(approved(before), approved(after))
            context = after.find(".//*[@id='geographic-context']")
            self.assertIsNotNone(context)
            self.assertNotIn("M 760.0,401.0 L 717.8,395.0", " ".join(p.get("d", "") for p in context))


if __name__ == "__main__":
    unittest.main()
