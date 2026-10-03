#!/usr/bin/env python3
"""Sharded read-only audit that produces lake-normalized SVG candidates as artifacts."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import normalize_country_map_lakes as lakes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 0 <= args.shard < args.shards:
        parser.error("invalid shard")

    args.output.mkdir(parents=True, exist_ok=True)
    registry = json.loads((ROOT / "data/atlas-destinations.json").read_text(encoding="utf-8"))
    destinations = registry["destinations"]
    candidates = []
    for item in destinations:
        country_path = ROOT / "data/countries" / f"{item['slug']}.json"
        if not country_path.exists():
            continue
        try:
            config = json.loads(country_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        relative = (config.get("map") or {}).get("svg")
        if isinstance(relative, str) and relative.endswith(".svg") and (ROOT / relative).exists():
            candidates.append((item["slug"], country_path, config, relative))

    selected = [entry for index, entry in enumerate(candidates) if index % args.shards == args.shard]
    records = []
    for slug, country_path, config, relative in selected:
        source_path = ROOT / relative
        source = source_path.read_text(encoding="utf-8")
        record = {"slug": slug, "svg": relative, "published": bool(next(d for d in destinations if d["slug"] == slug).get("atlasPublished"))}
        records.append(record)
        try:
            result, report = lakes.normalize(source, config, "i")
            ET.fromstring(result)
            record.update(status="changed" if report.get("changed") else "pass", **report)
            if report.get("changed"):
                target = args.output / "normalized" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(result, encoding="utf-8")
                # The candidate must rasterize at the canonical product size.
                import cairosvg
                png = args.output / "previews" / f"{slug}.png"
                png.parent.mkdir(parents=True, exist_ok=True)
                cairosvg.svg2png(bytestring=result.encode("utf-8"), write_to=str(png), output_width=1200, output_height=760)
        except Exception as exc:
            record.update(status="unsupported", reason=(type(exc).__name__ + ": " + str(exc))[:500])

    summary = {
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "shard": args.shard,
        "shards": args.shards,
        "registry_count": len(destinations),
        "audited_count": len(candidates),
        "selected_count": len(selected),
        "counts": dict(sorted(Counter(record["status"] for record in records).items())),
        "countries": records,
    }
    (args.output / "lake-report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("LAKE NORMALIZATION", json.dumps({key: summary[key] for key in ("git_sha", "shard", "audited_count", "selected_count", "counts")}, ensure_ascii=False))
    for record in records:
        if record["status"] != "pass":
            print("LAKE", record["slug"], record["status"], record.get("missing_lakes", ""), record.get("reason", ""))


if __name__ == "__main__":
    main()
