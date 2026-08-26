#!/usr/bin/env python3
"""Rebuild Göta Canal / Berg Locks from a modern real-world photographic reference."""
from build_sweden_v5_scenes import ASSET_BY_KEY, build_one

asset = ASSET_BY_KEY["gota-canal"]
asset["queries"] = [
    '"Bergs slussar och Carl Johans slusstrappa"',
    '"Bergs slussar första"',
    'Bergs slussar Göta kanal 2013',
]
asset["preferred"] = ["bergs", "slussar", "carl johans", "första", "göta", "canal"]
asset["reject"] = ["1907", "sjöhistoriska", "museet", "museum", "fo80512", "kmb"]
build_one("gota-canal")
