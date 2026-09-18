#!/usr/bin/env python3
"""Stage map-context rollout for the current completed Country roster.

Read-only with respect to production assets. The command derives its roster from
the canonical destination registry plus Country Production State, generates each
map into a new staging directory, and records source/output hashes in a manifest.
It never changes Country JSON, Production State, publication flags, or source SVGs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def derive_roster() -> list[dict]:
    registry = load_json(ROOT / "data/atlas-destinations.json")
    destinations = registry["destinations"]
    if len(destinations) != registry["count"] or len({d["slug"] for d in destinations}) != len(destinations):
        raise RuntimeError("Canonical destination registry count/uniqueness invalid")
    roster = []
    for entry in destinations:
        slug = entry["slug"]
        country_file = ROOT / "data" / "countries" / f"{slug}.json"
        state_file = ROOT / "ops" / "country-production" / f"{slug}.json"
        state = load_json(state_file) if state_file.exists() else None
        phase = state.get("phase") if state else None
        published = bool(entry.get("atlasPublished"))
        completed_unpublished = not published and phase == "COMPLETE"
        if not (published or completed_unpublished):
            continue
        if published and state is not None and phase != "COMPLETE":
            raise RuntimeError(f"Published Country is not COMPLETE in Production State: {slug} ({phase})")
        if not country_file.exists():
            raise RuntimeError(f"Selected Country missing Country JSON: {slug}")
        country = load_json(country_file)
        map_ref = country.get("map", {}).get("svg")
        if not isinstance(map_ref, str) or not map_ref.endswith(".svg") or ".." in Path(map_ref).parts:
            raise RuntimeError(f"Selected Country has unsafe/non-SVG map ref: {slug}")
        source = ROOT / map_ref
        if not source.is_file():
            raise RuntimeError(f"Selected Country missing source map: {slug} -> {map_ref}")
        roster.append({"slug": slug, "published": published, "phase": phase,
                       "country_file": country_file, "source": source, "map_ref": map_ref})
    return roster


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--resolution", choices=("c", "l", "i", "h", "f"), default="i")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    root = ROOT.resolve()
    if output == root or root in output.parents:
        parser.error("Staging output must be outside the repository so production assets cannot be overwritten")
    if output.exists() and any(output.iterdir()):
        parser.error("Staging output directory must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    roster = derive_roster()
    manifest = {
        "schemaVersion": 1,
        "sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "registryCount": load_json(ROOT / "data/atlas-destinations.json")["count"],
        "selectedCount": len(roster),
        "resolution": args.resolution,
        "entries": [],
    }
    dispatcher = ROOT / "scripts" / "add_country_map_context_existing.py"
    for item in roster:
        slug = item["slug"]
        source = item["source"]
        staged = output / f"{slug}.svg"
        source_text = source.read_text(encoding="utf-8")
        if 'id="geographic-context"' in source_text and all(c in source_text for c in ("#eaf2f4", "#dcebf0", "#d0e3eb")):
            staged.write_bytes(source.read_bytes())
            action = "preserve-existing-context"
        else:
            command = [sys.executable, str(dispatcher), "--country-json", str(item["country_file"]),
                       "--input", str(source), "--output", str(staged), "--resolution", args.resolution]
            subprocess.run(command, cwd=ROOT, check=True, timeout=240)
            action = "stage-context-preview"
        manifest["entries"].append({
            "slug": slug,
            "published": item["published"],
            "phase": item["phase"],
            "mapRef": item["map_ref"],
            "action": action,
            "sourceSha256": sha256(source),
            "stagedSha256": sha256(staged),
            "stagedBytes": staged.stat().st_size,
        })
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Staged {len(roster)} Country maps outside the repository: {output}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
