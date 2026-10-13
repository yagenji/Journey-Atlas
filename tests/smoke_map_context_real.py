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
sys.path.insert(0, str(ROOT / "scripts"))
import add_country_border_context as border_context  # noqa: E402

TARGET_BORDER_REFRESH = {"unitedkingdom": "GBR"}


def targets(svg: str):
    root = ET.fromstring(svg)
    return [(node.attrib.copy(), node.text) for node in root.iter(NS + "path")
            if node.attrib.get("fill") == "url(#land)"]


for slug in ("iceland", "portugal", "unitedstates", "kuwait", "qatar", "unitedkingdom"):
    country_file = ROOT / "data" / "countries" / f"{slug}.json"
    country = json.loads(country_file.read_text(encoding="utf-8"))
    source_file = ROOT / country["map"]["svg"]
    assert source_file.is_file(), source_file
    original_bytes = source_file.read_bytes()
    source = original_bytes.decode("utf-8")
    output = OUTPUT / f"{slug}.svg"
    original_root = ET.fromstring(source)
    already_context = original_root.find(f".//*[@id='geographic-context']") is not None
    if slug in TARGET_BORDER_REFRESH:
        assert already_context, f"Expected reviewed context before border refresh: {slug}"
        refreshed = border_context.replace_borders(
            source,
            country["map"]["bounds"],
            target_iso3=TARGET_BORDER_REFRESH[slug],
        )
        output.write_text(refreshed, encoding="utf-8")
        action = "refresh-target-adjacent-borders"
    elif already_context:
        # An individually reviewed source is itself the preview. Never try to insert
        # context twice or regenerate/alter its approved target and adjacent land.
        output.write_bytes(original_bytes)
        action = "preserve-reviewed-existing-context"
    else:
        command = [sys.executable, str(ROOT / "scripts" / "add_country_map_context.py"),
                   "--country-json", str(country_file), "--input", str(source_file),
                   "--output", str(output)]
        subprocess.run(command, check=True)
        action = "generate-preview-context"
    preview_bytes = output.read_bytes()
    preview = preview_bytes.decode("utf-8")
    if already_context and slug not in TARGET_BORDER_REFRESH:
        assert preview_bytes == original_bytes, f"Reviewed context changed: {slug}"
    assert targets(source) == targets(preview), f"Approved geometry changed: {slug}"
    root = ET.fromstring(preview)
    assert root.attrib["viewBox"] == "0 0 1200 760"
    assert root.find(f".//*[@id='geographic-context']") is not None, f"Missing context: {slug}"
    if slug in TARGET_BORDER_REFRESH:
        assert preview.count('id="context-national-borders"') == 1, f"Border layer count changed: {slug}"
        assert f"target-adjacent {TARGET_BORDER_REFRESH[slug]} lines omitted" in preview
    png = cairosvg.svg2png(bytestring=preview_bytes, output_width=1200, output_height=760)
    with Image.open(io.BytesIO(png)) as image:
        image.load()
        assert image.size == (1200, 760)
        assert image.getbbox() is not None
    (OUTPUT / f"{slug}.png").write_bytes(png)
    REPORT.append({"slug": slug, "map": str(country["map"]["svg"]),
                   "regions": [region["id"] for region in country["map"].get("regions", [])],
                   "source_bytes": len(original_bytes),
                   "preview_bytes": len(preview_bytes),
                   "approved_paths": len(targets(source)), "png_bytes": len(png),
                   "action": action,
                   "status": "PARSE_DECODE_TARGET_GEOMETRY_PASS; visual QA still required"})

REPORT_FILE = OUTPUT / "report.json"
REPORT_FILE.write_text(json.dumps({"basemap_data_version": version("basemap-data"),
                                   "basemap_data_license": metadata("basemap-data").get("License"),
                                   "checks": REPORT}, ensure_ascii=False, indent=2), encoding="utf-8")
print(REPORT_FILE.read_text(encoding="utf-8"))
