#!/usr/bin/env python3
"""Validate every revision-7 transition, including audited canonical review imports.

Squash-merging an already approved Country into main adds its State in one commit.
The existing v7 validator correctly forbids a *new* pre-approved initializer;
this wrapper recognizes only the separately reviewed, unpublished v2 import
whose approvals and exact asset bytes are independently present in Git history.
It never grants new approval, skips an ordinary transition, or publishes a page.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import country_production_state_v7 as v7


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=v7.ROOT, text=True).strip()


def immutable_assets(commit: str, slug: str) -> list[str]:
    return sorted(git("ls-tree", "-r", "--full-tree", commit, "--", f"assets/images/{slug}").splitlines())


def approved_items(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [state.get("hero") or {}, *(state.get("scenes") or []), *(state.get("taste") or [])]


def canonical_import(commit: str, path: str, after: dict[str, Any]) -> bool:
    """Return True ONLY for a source-backed, noindex, still-unapproved import."""
    slug = Path(path).stem
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        return False
    preview = after.get("reviewPreview") or {}
    deployment = after.get("reviewDeployment") or {}
    handoff = after.get("assetHandoff") or {}
    publication = after.get("publication") or {}
    source = preview.get("sourceCommit")
    if not (
        after.get("slug") == slug
        and after.get("productionProtocolId") == "2.0"
        and after.get("publicationPipelineVersion") == 2
        and after.get("phase") == "QA"
        and (after.get("finalApproval") or {}).get("state") == "PENDING"
        and publication.get("state") == "DRAFT"
        and publication.get("atlasPublished") is False
        and preview.get("state") == "DONE"
        and preview.get("browserQa") == "PASS"
        and isinstance(source, str)
        and re.fullmatch(r"[0-9a-f]{40}", source)
        and deployment.get("state") == "DEPLOYING"
        and deployment.get("productionVerification") == "PENDING"
        and deployment.get("atlasPublished") is False
        and deployment.get("url") == f"https://atlas.yagenji.com/countries/{slug}/"
        and handoff.get("state") == "PASS"
        and handoff.get("expectedRasterCount") == 13
        and handoff.get("verifiedRasterCount") == 13
        and (after.get("map") or {}).get("state") == "APPROVED"
        and (after.get("preVisualBuild") or {}).get("state") == "PASS"
        and (after.get("sceneBatchReview") or {}).get("approval") == "APPROVED"
        and (after.get("tasteBatchReview") or {}).get("approval") == "APPROVED"
    ):
        return False
    try:
        source_state = v7.git_json(source, path)
        country = v7.git_json(commit, f"data/countries/{slug}.json")
        registry = v7.git_json(commit, "data/atlas-destinations.json")
        if not isinstance(source_state, dict) or not isinstance(country, dict) or not isinstance(registry, dict):
            return False
        rows = [row for row in registry.get("destinations", []) if row.get("slug") == slug]
        if len(rows) != 1 or rows[0].get("atlasPublished") is not False:
            return False
        if country.get("publicationPipelineVersion") != 2 or country.get("slug") != slug:
            return False
        if source_state.get("imageGenerationPolicy", {}).get("revision") != 7:
            return False
        if source_state.get("productionProtocolId") != "2.0":
            return False
        if (source_state.get("finalApproval") or {}).get("state") == "APPROVED":
            return False
        if (source_state.get("publication") or {}).get("atlasPublished") is not False:
            return False
        if v7.validate_state_dict(source_state, path) or v7.validate_state_dict(after, path):
            return False
        if any(item.get("state") != "APPROVED" or not item.get("approvedGenerationId") for item in approved_items(after)):
            return False
        if len(approved_items(after)) != 13 or len(approved_items(source_state)) != 13:
            return False
        # Never accept a fabricated ledger, new image approval, or changed raster.
        for key in ("hero", "scenes", "taste", "sceneBatchReview", "tasteBatchReview", "recoveryMigrations", "assetHandoff"):
            if after.get(key) != source_state.get(key):
                return False
        if immutable_assets(source, slug) != immutable_assets(commit, slug):
            return False
        if len([x for x in immutable_assets(commit, slug) if "/approved/" in x]) != 13:
            return False
    except (subprocess.CalledProcessError, ValueError, TypeError):
        return False
    return True


def validate_range(base: str, head: str) -> list[str]:
    errors: list[str] = []
    for commit in git("rev-list", "--reverse", "--ancestry-path", f"{base}..{head}").splitlines():
        parent = v7.first_parent(commit)
        for path in v7.changed_state_paths(commit):
            before = v7.git_json(parent, path) if parent else None
            after = v7.git_json(commit, path)
            if before is None and isinstance(after, dict) and canonical_import(commit, path, after):
                # The ordinary static validator has already checked every batch ledger.
                errors.extend(f"{commit[:8]} {e}" for e in v7.validate_state_dict(after, Path(path).name))
            else:
                errors.extend(f"{commit[:8]} {e}" for e in v7.validate_transition(before, after, path))
    return errors


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: validate_canonical_import_v7.py BASE_SHA HEAD_SHA", file=sys.stderr)
        return 2
    errors = validate_range(sys.argv[1], sys.argv[2])
    if errors:
        print("Revision 7 transition validation: FAIL")
        for error in errors:
            print("-", error)
        return 1
    print("Revision 7 transition validation: PASS (audited canonical imports)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
