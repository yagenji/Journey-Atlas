#!/usr/bin/env python3
"""Preview real approved map SVGs on CI, never rewriting the production assets."""
from __future__ import annotations

import io
import json
import subprocess
import sys
from importlib.metadata import metadata, version
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
NS = "{http://www.w3.org/2000/svg}"
OUTPUT = Path("/tmp/journey-atlas-map-context-real-previews")
OUTPUT.mkdir(parents=True, exist_ok=True)
REPORT = []


def targets(svg: str):
    root = ET.fromstring(svg)
    return [(node.attrib.copy(), node.text) for node in root.iter(NS + "path")
            if node.attrib.get("fill") == "url(#land)"]


for slug in ("iceland", "portugal", "unitedstates", "kuwait"):
    country_file = ROOT / "data" / "countries" / f"{slug}.json"
    country = json.loads(country_file.read_text(encoding="utf-8"))
    source_file = ROOT / country["map"]["svg"]
    assert source_file.is_file(), source_file
    source = source_file.read_text(encoding="utf-8")
    output = OUTPUT / f"{slug}.svg"
    command = [sys.executable, str(ROOT / "scripts" / "add_country_map_context.py"),
               "--country-json", str(country_file), "--input", str(source_file),
               "--output", str(output)]
    subprocess.run(command, check=True)
    preview = output.read_text(encoding="utf-8")
    assert targets(source) == targets(preview), f"Approved geometry changed: {slug}"
    root = ET.fromstring(preview)
    assert root.attrib["viewBox"] == "0 0 1200 760"
    assert root.find(f".//*[@id='geographic-context']") is not None, f"Missing context: {slug}"
    png = cairosvg.svg2png(bytestring=preview.encode("utf-8"), output_width=1200, output_height=760)
    with Image.open(io.BytesIO(png)) as image:
        image.load()
        assert image.size == (1200, 760)
        assert image.getbbox() is not None
    (OUTPUT / f"{slug}.png").write_bytes(png)
    REPORT.append({"slug": slug, "map": str(country["map"]["svg"]),
                   "regions": [region["id"] for region in country["map"].get("regions", [])],
                   "source_bytes": len(source.encode("utf-8")),
                   "preview_bytes": len(preview.encode("utf-8")),
                   "approved_paths": len(targets(source)), "png_bytes": len(png),
                   "status": "PARSE_DECODE_TARGET_GEOMETRY_PASS; visual QA still required"})

REPORT_FILE = OUTPUT / "report.json"
REPORT_FILE.write_text(json.dumps({"basemap_data_version": version("basemap-data"),
                                   "basemap_data_license": metadata("basemap-data").get("License"),
                                   "checks": REPORT}, ensure_ascii=False, indent=2), encoding="utf-8")
print(REPORT_FILE.read_text(encoding="utf-8"))
