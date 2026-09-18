#!/usr/bin/env python3
"""Generate a new single-region Country map with the approved sea/land context.

The legacy generator remains unchanged so in-flight Country work is unaffected.
This wrapper requires a target-country-specific administrative geometry source;
GSHHS coastline alone is not sufficient to distinguish a target country.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source", required=True, choices=("natural-earth", "geoboundaries"))
    parser.add_argument("--context-resolution", default="i", choices=("c", "l", "i", "h", "f"))
    parser.add_argument("--simplify", default=0.003, type=float)
    parser.add_argument("--max-bytes", default=6000000, type=int)
    args, generator_args = parser.parse_known_args()
    if any(arg == "--bounds" or arg.startswith("--bounds=") or arg == "--output" or arg.startswith("--output=") for arg in generator_args):
        parser.error("Bounds and output are authoritative in Country JSON and this wrapper")
    if args.output.exists():
        parser.error("Output must be a new preview file, not an existing production asset")
    if not (0 <= args.simplify <= 0.003):
        parser.error("Simplify must be between zero and 0.003 degrees")
    country = json.loads(args.country_json.read_text(encoding="utf-8"))
    config = country["map"]
    if config.get("regions"):
        parser.error("Multi-region Country maps need a reviewed region-aware generator")
    bounds = config["bounds"]
    script_dir = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="atlas-map-context-") as temporary:
        generated = Path(temporary) / "target.svg"
        command = [
            sys.executable, str(script_dir / "generate_country_map.py"),
            "--source", args.source,
            "--bounds", *(str(bounds[key]) for key in ("west", "south", "east", "north")),
            "--output", str(generated), "--simplify", str(args.simplify),
            *generator_args,
        ]
        subprocess.run(command, check=True)
        subprocess.run([
            sys.executable, str(script_dir / "add_country_map_context.py"),
            "--country-json", str(args.country_json),
            "--input", str(generated), "--output", str(args.output),
            "--resolution", args.context_resolution,
            "--simplify", str(args.simplify), "--max-bytes", str(args.max_bytes),
        ], check=True)


if __name__ == "__main__":
    main()
