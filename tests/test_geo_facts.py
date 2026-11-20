"""data/geo-facts.json stays consistent with the published pages it describes."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


class GeoFactsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = json.loads((ROOT / "data/geo-facts.json").read_text(encoding="utf-8"))["entries"]
        registry = json.loads((ROOT / "data/atlas-destinations.json").read_text(encoding="utf-8"))
        cls.countries = {item["slug"] for item in registry["destinations"] if item.get("atlasPublished")}

    def test_time_zones_are_real_land_zones(self) -> None:
        for slug, entry in self.entries.items():
            with self.subTest(slug=slug):
                self.assertIn("tz", entry)
                self.assertFalse(entry["tz"].startswith("Etc/"))
                ZoneInfo(entry["tz"])

    def test_links_point_to_published_countries(self) -> None:
        for slug, entry in self.entries.items():
            targets = [item["slug"] for item in entry.get("antipode", [])]
            if entry.get("latitude", {}).get("kind") == "capital":
                targets.append(entry["latitude"]["slug"])
            for target in targets:
                with self.subTest(slug=slug, target=target):
                    self.assertIn(target, self.countries)
                    self.assertNotEqual(target, slug)

    def test_same_latitude_is_within_window(self) -> None:
        for slug, entry in self.entries.items():
            if "latitude" in entry:
                with self.subTest(slug=slug):
                    self.assertLessEqual(abs(entry["latitude"]["lat"] - entry["place"]["lat"]), 0.51)

    def test_antipodes_are_mutual(self) -> None:
        for slug, entry in self.entries.items():
            for item in entry.get("antipode", []):
                other = self.entries.get(item["slug"], {})
                with self.subTest(slug=slug, other=item["slug"]):
                    self.assertTrue(other.get("antipode"), f"{item['slug']} lists no antipode")


if __name__ == "__main__":
    unittest.main()
