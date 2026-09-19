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

import add_country_map_context_legacy as legacy
from filter_duplicate_target_context import remove_target_land_context

ROOT = Path(__file__).resolve().parents[1]


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
    if removed:
        args.output.write_text(filtered, encoding="utf-8")
    print(f"Created existing-Country preview: {args.output}; excluded {removed} duplicate target-land rings")


if __name__ == "__main__":
    main()
