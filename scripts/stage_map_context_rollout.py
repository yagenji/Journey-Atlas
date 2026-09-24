#!/usr/bin/env python3
"""Stage map-context rollout for the current completed Country roster.

Read-only with respect to production assets. The command derives its roster from
the canonical destination registry plus Country Production State, generates each
map into a new staging directory, and records source/output hashes in a manifest.
It never changes Country JSON, Production State, publication flags, or source SVGs.

Stage 2 geographic QA is fail-closed: each selected map must preserve its approved
target paths, carry a non-empty target-source record, render surrounding physical
land only through source-pinned context, and exclude the approved target exactly
whenever context remains. Passing Stage 2 does NOT authorize Stage 3 promotion:
promotionEligible remains false until the user explicitly advances the rollout.
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
from apply_exact_target_clip import apply_exact_target_negative_clip

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"

# These Countries were produced after the new-Country surrounding-land spec
# landed on main (#950). They are intentionally outside this legacy migration.
NEW_COUNTRY_CONTEXT_SEPARATE = {'dominica', 'dominicanrepublic', 'stlucia'}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def protected_target_paths(root):
    """Serialize rendered approved target paths; generated context is excluded."""
    parents = {child: parent for parent in root.iter() for child in parent}
    result = []
    for path in root.iter(SVG + "path"):
        cursor = path
        fill = None
        while cursor is not None:
            if "fill" in cursor.attrib:
                fill = cursor.attrib["fill"]
                break
            cursor = parents.get(cursor)
        if fill != "url(#land)":
            continue
        cursor = path
        inside_context = False
        while cursor is not None:
            if cursor.get("id") == "geographic-context":
                inside_context = True
                break
            cursor = parents.get(cursor)
        if not inside_context:
            result.append(ET.tostring(path, encoding="unicode"))
    if not result:
        raise RuntimeError("Approved target path set is empty")
    return result


def validate_stage2_candidate(source_text: str, staged_text: str, map_source: str,
                              action: str, slug: str, review_mode: str) -> dict:
    """Fail closed unless a staged map satisfies the common Stage 2 invariant."""
    source_root = ET.fromstring(source_text)
    staged_root = ET.fromstring(staged_text)
    if source_root.get("viewBox") != "0 0 1200 760" or staged_root.get("viewBox") != "0 0 1200 760":
        raise RuntimeError(f"Stage 2 canvas changed or is noncanonical: {slug}")
    if protected_target_paths(source_root) != protected_target_paths(staged_root):
        raise RuntimeError(f"Stage 2 changed approved target paths: {slug}")
    if not map_source.strip():
        raise RuntimeError(f"Stage 2 target source missing: {slug}")

    contexts = [g for g in staged_root.iter(SVG + "g") if g.get("id") == "geographic-context"]
    context_geometry = False
    clip_id = None
    if contexts:
        if len(contexts) != 1:
            raise RuntimeError(f"Stage 2 context group count invalid: {slug}")
        context = contexts[0]
        context_geometry = any((p.get("d") or "").strip() for p in context.iter(SVG + "path"))
        if context_geometry and review_mode in (
                "common-source-exact-clip-review",
                "existing-context-source-review"):
            clip_ref = context.get("clip-path", "")
            if not (clip_ref.startswith("url(#") and clip_ref.endswith(")")):
                raise RuntimeError(f"Stage 2 context lacks exact target-negative clip: {slug}")
            clip_id = clip_ref[5:-1]
            clips = [node for node in staged_root.iter(SVG + "clipPath") if node.get("id") == clip_id]
            if len(clips) != 1:
                raise RuntimeError(f"Stage 2 context clip target missing/ambiguous: {slug}")
            clip_paths = list(clips[0].iter(SVG + "path"))
            if not clip_paths or not any((p.get("d") or "").strip() for p in clip_paths):
                raise RuntimeError(f"Stage 2 exact clip contains no geometry: {slug}")

    if action == "preserve-no-foreign-land":
        if staged_text != source_text or context_geometry:
            raise RuntimeError(f"Stage 2 no-foreign-land preservation changed source: {slug}")
    elif action in ("stage-context-preview", "stage-existing-context-exact-clip", "preserve-existing-context"):
        if action != "preserve-existing-context" and not contexts:
            raise RuntimeError(f"Stage 2 expected geographic context is missing: {slug}")
    else:
        raise RuntimeError(f"Unknown Stage 2 staging action: {slug} / {action}")

    if action != "preserve-no-foreign-land":
        for color in ("#eaf2f4", "#dcebf0", "#d0e3eb"):
            if color not in staged_text:
                raise RuntimeError(f"Stage 2 shared sea palette missing {color}: {slug}")

    return {
        "targetPathCount": len(protected_target_paths(staged_root)),
        "contextGeometry": context_geometry,
        "contextClipId": clip_id,
        "qaBasis": [
            "target-source-recorded",
            "approved-target-paths-preserved",
            "1200x760-canvas-preserved",
            "source-pinned-surrounding-land",
            ("source-specific-individual-review"
             if review_mode == "individual-source-review"
             else ("exact-target-negative-context" if context_geometry
                   else "no-context-land-in-viewport")),
        ],
    }


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
        if slug in NEW_COUNTRY_CONTEXT_SEPARATE:
            continue
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
        map_source = country.get("map", {}).get("source")
        if not isinstance(map_source, str) or not map_source.strip():
            raise RuntimeError(f"Selected Country missing map source provenance: {slug}")
        roster.append({"slug": slug, "published": published, "phase": phase,
                       "country_file": country_file, "source": source, "map_ref": map_ref,
                       "map_source": map_source.strip()})
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
    ledger = load_json(ROOT / "ops" / "map-context-stage2-review.json")
    ledger_entries = ledger.get("entries") or []
    ledger_by_slug = {entry.get("slug"): entry for entry in ledger_entries}
    roster_slugs = {item["slug"] for item in roster}
    if (ledger.get("stage") != "2" or ledger.get("stageStatus") != "COMPLETE"
            or ledger.get("promotionEligible") is not False
            or len(ledger_by_slug) != len(ledger_entries)
            or set(ledger_by_slug) != roster_slugs):
        raise RuntimeError("Stage 2 review ledger does not match the exact selected roster")
    if any(entry.get("status") != "PASS" or entry.get("promotionEligible") is not False
           for entry in ledger_entries):
        raise RuntimeError("Stage 2 review ledger contains a non-PASS or promotable entry")
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
        review = ledger_by_slug[slug]
        review_mode = review["reviewMode"]
        # Qatar/Kuwait already have source-pinned reviewed context in the Draft
        # branch. Keep that source-specific result; do not layer the common clip.
        if slug in ('qatar', 'kuwait'):
            reviewed = reconcile_gulf_foreign(source_text, source, slug, args.resolution)
            staged.write_text(reviewed, encoding='utf-8')
            action = "stage-context-preview"
        elif 'id="geographic-context"' in source_text and all(c in source_text for c in ("#eaf2f4", "#dcebf0", "#d0e3eb")):
            if review_mode == "existing-context-source-review":
                reviewed = apply_exact_target_negative_clip(source_text)
                staged.write_text(reviewed, encoding='utf-8')
                action = ("preserve-existing-context" if reviewed == source_text
                          else "stage-existing-context-exact-clip")
            else:
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
            # The common-review cohort gets an exact display-space exclusion.
            # Individually source-reviewed maps keep their already-reviewed bytes.
            if review_mode == "common-source-exact-clip-review":
                staged.write_text(
                    apply_exact_target_negative_clip(staged.read_text(encoding='utf-8')),
                    encoding='utf-8'
                )
            if contains_generated_context_geometry(staged):
                action = "stage-context-preview"
            else:
                staged.write_bytes(source.read_bytes())
                action = "preserve-no-foreign-land"
        staged_text = staged.read_text(encoding="utf-8")
        stage2 = validate_stage2_candidate(
            source_text, staged_text, item["map_source"], action, slug, review_mode
        )
        manifest["entries"].append({
            "slug": slug,
            "published": item["published"],
            "phase": item["phase"],
            "mapRef": item["map_ref"],
            "targetSource": item["map_source"],
            "reviewMode": review["reviewMode"],
            "surroundingSource": (
                "Basemap 2.0.0 / GSHHG 2.3.6 WGS84, or the source-pinned "
                "country exception embedded in the staged SVG"
            ),
            "action": action,
            "sourceSha256": sha256(source),
            "stagedSha256": sha256(staged),
            "stagedBytes": staged.stat().st_size,
            **stage2,
            "geographicQaStatus": "PASS",
            # Stage 2 completion is not Stage 3 authorization.
            "promotionEligible": False,
        })
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Staged {len(roster)} Country maps outside the repository: {output}")
    print(f"Manifest: {manifest_path}; all entries Stage 2 geographic QA PASS / Stage 3 NOT PROMOTABLE")


if __name__ == "__main__":
    main()
