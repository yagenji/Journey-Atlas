#!/usr/bin/env python3
"""Stage map-context rollout for the current completed Country roster.

Read-only with respect to production assets. The command derives its roster from
the canonical destination registry plus Country Production State, generates each
map into a new staging directory, and records source/output hashes in a manifest.
It never changes Country JSON, Production State, publication flags, or source SVGs.

A staged technical preview is NEVER geographic approval or a promotion allowlist.
Every manifest entry is marked geographicQaStatus=HOLD and promotionEligible=false
until separate independent, per-map geography/source/license QA is documented.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from reconcile_gulf_foreign import reconcile as reconcile_gulf_foreign
from reconcile_bahrain_hawar_sibling import reconcile as reconcile_hawar_sibling
from reconcile_elsalvador_foreign import reconcile as reconcile_elsalvador_foreign

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def contains_generated_context_geometry(path: Path) -> bool:
    """Distinguish real generated surrounding land from a palette-only preview.

    The generator sometimes creates an empty geographic-context group where the
    approved viewport contains only its original islands. Do not replace an
    approved map just to recolor the sea; preserve the exact source bytes.
    """
    root = ET.parse(path).getroot()
    context = [g for g in root.iter(SVG + "g") if g.get("id") == "geographic-context"]
    if len(context) != 1:
        raise RuntimeError(f"Expected exactly one generated geographic-context group: {path}")
    return any((node.get("d") or "").strip() for node in context[0].iter(SVG + "path"))


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
        # Qatar/Kuwait already have context in the Draft branch. Their source-
        # pinned fixes operate only on a disposable staged copy.
        if slug in ('qatar', 'kuwait'):
            staged.write_text(reconcile_gulf_foreign(source_text, source, slug, args.resolution),
                              encoding='utf-8')
            action = "stage-context-preview"
        elif 'id="geographic-context"' in source_text and all(c in source_text for c in ("#eaf2f4", "#dcebf0", "#d0e3eb")):
            staged.write_bytes(source.read_bytes())
            action = "preserve-existing-context"
        else:
            command = [sys.executable, str(dispatcher), "--country-json", str(item["country_file"]),
                       "--input", str(source), "--output", str(staged), "--resolution", args.resolution]
            subprocess.run(command, cwd=ROOT, check=True, timeout=240)
            if slug == 'bahrain':
                # The two former GSHHG Qatar rings are poor small-scale coastline
                # triangles. Use source-pinned QAT gbOpen ADM0 from the exact same
                # 2023 series as the unchanged approved Bahrain national paths.
                # This is a Stage② preview only, not a geographic approval.
                staged.write_text(reconcile_hawar_sibling(staged.read_text(encoding='utf-8'),
                                                          source, args.resolution),encoding='utf-8')
            if slug == 'elsalvador':
                staged.write_text(reconcile_elsalvador_foreign(
                    staged.read_text(encoding='utf-8'), source, args.resolution),
                    encoding='utf-8')
            if contains_generated_context_geometry(staged):
                action = "stage-context-preview"
            else:
                staged.write_bytes(source.read_bytes())
                action = "preserve-no-foreign-land"
        manifest["entries"].append({
            "slug": slug,
            "published": item["published"],
            "phase": item["phase"],
            "mapRef": item["map_ref"],
            "action": action,
            "sourceSha256": sha256(source),
            "stagedSha256": sha256(staged),
            "stagedBytes": staged.stat().st_size,
            # A preserved image or a technically valid preview is NOT source-backed
            # geographic QA. Do not infer approvals from the staging action.
            "geographicQaStatus": "HOLD",
            "promotionEligible": False,
        })
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Staged {len(roster)} Country maps outside the repository: {output}")
    print(f"Manifest: {manifest_path}; all entries geographic QA HOLD / NOT PROMOTABLE")


if __name__ == "__main__":
    main()
