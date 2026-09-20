#!/usr/bin/env python3
"""Dispatch preview generation for existing approved Country maps.

Canonical layouts use add_country_map_context.py. A small reviewed set of historic
SVG layouts uses the migration-only legacy adapter. This script never overwrites
production assets; callers must provide a new output path.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import add_country_map_context_legacy as legacy
from filter_duplicate_target_context import remove_target_land_context

ROOT = Path(__file__).resolve().parents[1]


def frame_unframed_region_context(svg: str, regions: list[dict] | None) -> str:
    """Identify clipped neighboring land in otherwise unframed regional maps.

    Migration-only presentation: preserve all approved paths and existing inset
    treatments. A frame marks an existing geographic viewport, not a border.
    """
    if not regions or len(regions) < 2 or 'id="geographic-context"' not in svg:
        return svg
    root = ET.fromstring(svg)
    if not root.get("data-map-projection", "").startswith("multi-region-"):
        return svg
    ns = "{http://www.w3.org/2000/svg}"
    if any(el.tag == ns + "rect" and el.get("stroke") not in (None, "", "none")
           for el in root.iter()):
        return svg  # Preserve existing U.S. and Kuwait inset frames.
    expected = {item["id"] for item in regions}
    drawn = {el.get("data-map-context-region") for el in root.iter()
             if el.get("data-map-context-region")}
    if not drawn:
        return svg  # Legacy composite paths do not expose individual region clips.
    clip_ids = {el.get("id") for el in root.iter() if el.tag == ns + "clipPath"}
    if drawn != expected or any(f"map-context-clip-{key}" not in clip_ids for key in expected):
        raise ValueError("Unframed multi-region context/clip IDs do not match Country JSON")
    outlines = []
    for region in regions:
        rect = region["rect"]
        x, y, w, h = (float(rect[k]) for k in ("x", "y", "width", "height"))
        if not (0 <= x < 1200 and 0 <= y < 760 and w > 0 and h > 0
                and x + w <= 1200 and y + h <= 760):
            raise ValueError("Region frame outside 1200×760 canvas")
        outlines.append(
            f'<rect data-map-context-frame="{region["id"]}" '
            f'x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="5" '
            'fill="none" stroke="#879b9b" stroke-width="1.5" '
            'stroke-dasharray="5 5" opacity=".7"/>'
        )
    if svg.count("</svg>") != 1:
        raise ValueError("Unexpected SVG closing tag")
    result = svg.replace("</svg>",
                         '<g id="geographic-context-region-frames">'
                         + "".join(outlines) + "</g></svg>")
    ET.fromstring(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resolution", choices=("c", "l", "i", "h", "f"), default="i")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Output must be a new separate preview file")
    data = json.loads(args.country_json.read_text(encoding="utf-8"))
    slug = data.get("slug")
    if slug in legacy.LEGACY_SLUGS:
        legacy.generate(args.country_json, args.input, args.output, args.resolution)
    else:
        command = [sys.executable, str(ROOT / "scripts" / "add_country_map_context.py"),
                   "--country-json", str(args.country_json), "--input", str(args.input),
                   "--output", str(args.output), "--resolution", args.resolution]
        subprocess.run(command, cwd=ROOT, check=True)
    preview = args.output.read_text(encoding="utf-8")
    filtered, removed = remove_target_land_context(preview)
    clarified = frame_unframed_region_context(filtered, data.get("map", {}).get("regions"))
    if clarified != preview:
        args.output.write_text(clarified, encoding="utf-8")
    print(f"Created existing-Country preview: {args.output}; excluded {removed} duplicate target-land rings")


if __name__ == "__main__":
    main()
