#!/usr/bin/env python3
"""Every Country map credits the geographic datasets it is drawn from
(data/map-data-sources.json: sources + countries)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = json.loads((ROOT / "data" / "map-data-sources.json").read_text(encoding="utf-8"))
REGISTRY = PAYLOAD["sources"]
CREDITS = PAYLOAD["countries"]

# OpenStreetMap / ODbL / CC BY data named in these maps' provenance is used only
# to cross-check scope or confirm an island position; it is not drawn.
NOT_DRAWN = {
    "comoros",      # geoBoundaries COM ADM0: scope cross-check
    "elsalvador",   # geoBoundaries SLV ADM0: island ownership classification only
    "fiji",         # OSM way: Sawa-i-Lau centre position only
    "haiti",        # geoBoundaries HTI ADM0: identity cross-check
    "micronesia",   # OSM/GeoNames: island positions only
    "trinidadtobago",  # geoBoundaries TTO ADM0: component cross-check
    "vanuatu",      # geoBoundaries VUT ADM0: extent cross-check
}


def countries():
    for path in sorted((ROOT / "data" / "countries").glob("*.json")):
        yield json.loads(path.read_text(encoding="utf-8"))


def provenance(country: dict) -> str:
    map_data = country["map"]
    text = str(map_data.get("source") or "")
    if map_data["svg"].endswith(".svg"):
        svg = (ROOT / map_data["svg"]).read_text(encoding="utf-8")
        text += " ".join(re.findall(r"<metadata>(.*?)</metadata>|<desc>(.*?)</desc>|<!--(.*?)-->", svg, re.S).__str__())
    return text


class MapCreditsTest(unittest.TestCase):
    def test_every_map_lists_known_sources(self):
        used = set()
        for country in countries():
            with self.subTest(slug=country["slug"]):
                credits = CREDITS.get(country["slug"])
                self.assertIsInstance(credits, list)
                self.assertTrue(credits, "credits must name at least one dataset")
                self.assertEqual(len(credits), len(set(credits)))
                for source_id in credits:
                    self.assertIn(source_id, REGISTRY)
                used.update(credits)
        self.assertEqual(set(REGISTRY) - used, set(), "registry entries no map uses")
        slugs = {country["slug"] for country in countries()}
        self.assertEqual(set(CREDITS), slugs, "credits must cover exactly the Country files")

    def test_registry_entries_are_complete(self):
        for source_id, source in REGISTRY.items():
            with self.subTest(source=source_id):
                self.assertTrue(source.get("label"))
                self.assertTrue(source.get("url", "").startswith("https://"))
                if source.get("licenseUrl"):
                    self.assertTrue(source["licenseUrl"].startswith("https://"))

    def test_openstreetmap_data_is_credited(self):
        for country in countries():
            slug = country["slug"]
            if slug in NOT_DRAWN:
                continue
            if re.search(r"OpenStreetMap|ODbL", provenance(country)):
                with self.subTest(slug=slug):
                    self.assertIn("osm", CREDITS[slug])

    def test_cc_by_data_is_credited(self):
        for country in countries():
            slug = country["slug"]
            if slug in NOT_DRAWN:
                continue
            if re.search(r"CC BY \d|Creative Commons Attribution", provenance(country)):
                with self.subTest(slug=slug):
                    licences = [REGISTRY[i].get("license", "") for i in CREDITS[slug]]
                    self.assertTrue(any(l.startswith("CC BY") for l in licences), licences)

    def test_no_non_commercial_gadm_geometry(self):
        for country in countries():
            with self.subTest(slug=country["slug"]):
                self.assertNotIn("GADM", provenance(country))

    def test_no_restricted_licences(self):
        # GPL (copyleft on the derived map) and amCharts geodata (licensed for
        # use inside amCharts software only) were replaced on 2026-10-28.
        for source_id, source in REGISTRY.items():
            with self.subTest(source=source_id):
                self.assertFalse(source.get("license", "").startswith("GPL"))
                self.assertNotIn("amcharts", source["url"].lower())

    def test_about_page_credits_are_current(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_about_map_credits.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
