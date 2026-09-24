#!/usr/bin/env python3
"""Promote the reviewed Stage 2 map-context staging set into production SVG assets.

This script is intentionally separate from Stage 2. It mutates only map SVG files
already enumerated in the exact Stage 2 manifest, never Country JSON, Production
State, publication settings, images, index/sitemap, or unrelated assets.

Run only after explicit Stage 3 authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged-dir", required=True, type=Path)
    parser.add_argument("--authorize-stage3", action="store_true",
                        help="Required acknowledgement of explicit Stage 3 authorization")
    args = parser.parse_args()
    if not args.authorize_stage3:
        parser.error("Stage 3 promotion requires --authorize-stage3")

    staged_dir = args.staged_dir.resolve()
    manifest_path = staged_dir / "manifest.json"
    if not manifest_path.is_file():
        parser.error("Missing Stage 2 manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries") or []
    if not entries or manifest.get("selectedCount") != len(entries):
        raise RuntimeError("Invalid Stage 2 manifest")
    if any(e.get("geographicQaStatus") != "PASS" for e in entries):
        raise RuntimeError("Stage 3 cannot promote a non-PASS Stage 2 entry")

    changed = []
    preserved = []
    for entry in entries:
        slug = entry["slug"]
        map_ref = entry["mapRef"]
        source = (ROOT / map_ref).resolve()
        staged = (staged_dir / f"{slug}.svg").resolve()
        if ROOT.resolve() not in source.parents or source.suffix != ".svg":
            raise RuntimeError(f"Unsafe production map path: {slug} / {map_ref}")
        if not source.is_file() or not staged.is_file():
            raise RuntimeError(f"Missing source/staged map: {slug}")
        if sha256(source) != entry["sourceSha256"]:
            raise RuntimeError(f"Production map changed since Stage 2 staging: {slug}")
        if sha256(staged) != entry["stagedSha256"]:
            raise RuntimeError(f"Staged map changed since manifest creation: {slug}")

        action = entry["action"]
        if action in ("preserve-existing-context", "preserve-no-foreign-land"):
            if entry["sourceSha256"] != entry["stagedSha256"]:
                raise RuntimeError(f"Preserve action has differing staged bytes: {slug}")
            preserved.append(slug)
            continue
        if action not in ("stage-context-preview", "stage-existing-context-exact-clip"):
            raise RuntimeError(f"Unknown Stage 3 action: {slug} / {action}")

        shutil.copyfile(staged, source)
        if sha256(source) != entry["stagedSha256"]:
            raise RuntimeError(f"Promoted map SHA mismatch: {slug}")
        changed.append(slug)

    print(json.dumps({
        "stage": 3,
        "status": "PROMOTED_TO_BRANCH_WORKTREE",
        "selectedCount": len(entries),
        "changedCount": len(changed),
        "preservedCount": len(preserved),
        "changed": changed,
        "preserved": preserved,
        "publicationChanged": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
