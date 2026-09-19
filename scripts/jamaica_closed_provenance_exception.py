#!/usr/bin/env python3
"""One closed, user-authorized Jamaica publication exception, not a generation waiver.

The ordinary approval machine remains authoritative for every other Country.
This exception never synthesizes image-generation IDs, approvals or batch ledgers.
It validates the preserved exact raster bytes and their distinct identity before
permitting this one Country to proceed through normal page-review/publication QA.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "jamaica-preserve-13-20260919"
CASE_PATH = "ops/closed-country-publication-exceptions/jamaica.json"
# Pin the exact central-policy document as well as each raster. A modified
# case file cannot silently enlarge the already-authorized historical scope.
CASE_GIT_BLOB = "2423c65327d3fcd18574c5002cea11dbb06c0f98"
SCENE_IDS = tuple(f"S{x:02d}" for x in range(1, 9))
FOOD_IDS = tuple(f"FOOD{x:02d}" for x in range(1, 5))
ALL_IDS = ("HERO", *SCENE_IDS, *FOOD_IDS)


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(state: dict[str, Any], root: Path | None = None) -> list[str]:
    """Return precise errors; no implicit fallback or special case for other slugs."""
    base = root or ROOT
    slug = state.get("slug")
    if slug != "jamaica":
        return ["Closed Jamaica exception cannot be used by another Country"]
    record = state.get("closedProvenanceException")
    if not isinstance(record, dict) or record != {
        "id": CASE_ID,
        "status": "APPLIED",
        "sourceCommit": "34cf8a3db3dfbd3d1df2102b4f73df2268110862",
        "authorizationDate": "2026-09-19",
    }:
        return ["Closed Jamaica exception requires its exact explicit authorization record"]
    manifest = base / CASE_PATH
    if not manifest.is_file() or blob_sha(manifest.read_bytes()) != CASE_GIT_BLOB:
        return ["Pinned Jamaica exception policy is missing or has changed"]
    try:
        policy = _load(manifest)
        country = _load(base / "data/countries/jamaica.json")
    except (OSError, ValueError, TypeError) as exc:
        return [f"Jamaica exception source cannot be parsed: {exc}"]
    errors: list[str] = []
    if (policy.get("schemaVersion") != 1 or policy.get("id") != CASE_ID
            or policy.get("slug") != "jamaica" or policy.get("status") != "CLOSED_HISTORICAL_CASE"
            or policy.get("authorizedBy") != "USER_EXPLICIT"):
        errors.append("Unexpected Jamaica closed-case identity or authorization")
    items = policy.get("assets")
    if not isinstance(items, dict) or tuple(items) != ALL_IDS:
        return errors + ["Jamaica case must list exactly HERO, S01-S08 and FOOD01-FOOD04 in order"]
    scenes, food = state.get("scenes"), state.get("taste")
    country_scenes = country.get("scenes")
    country_food = (country.get("taste") or {}).get("items")
    if (not isinstance(scenes, list) or len(scenes) != 8 or
            not isinstance(food, list) or len(food) != 4 or
            not isinstance(country_scenes, list) or len(country_scenes) != 8 or
            not isinstance(country_food, list) or len(country_food) != 4):
        return errors + ["Jamaica source and State must retain exactly eight Scenes and four Taste items"]
    hero = state.get("hero") or {}
    if (hero.get("state") != "APPROVED" or
            hero.get("approvedGenerationId") != items["HERO"]["generationId"] or
            hero.get("asset") != country.get("hero", {}).get("image")):
        errors.append("Original approved Hero generation and asset must remain unchanged")
    for kind, records, names in (("SCENE", scenes, SCENE_IDS), ("TASTE", food, FOOD_IDS)):
        for original, key in zip(records, names):
            if original.get("id") != key or original.get("state") != "NOT_STARTED":
                errors.append(f"{kind} {key}: original generation State must remain explicitly unrecovered")
            if original.get("approvedGenerationId") or original.get("candidateGenerationId"):
                errors.append(f"{kind} {key}: no unverified generation ID may be added")
    for key in ("sceneBatchReview", "tasteBatchReview"):
        batch = state.get(key) or {}
        if batch.get("approval") != "PENDING" or batch.get("rounds") != []:
            errors.append(f"{key}: historical batch approvals must not be fabricated")
    expected = {"HERO": country["hero"]["image"]}
    expected.update({k: x["image"] for k, x in zip(SCENE_IDS, country_scenes)})
    expected.update({k: x["image"] for k, x in zip(FOOD_IDS, country_food)})
    observed_hashes: list[str] = []
    for key in ALL_IDS:
        row = items[key]
        filename = row.get("filename")
        recorded_sha = row.get("gitBlobSha")
        if not isinstance(filename, str) or not re.fullmatch(r"[a-z0-9-]+\.webp", filename):
            errors.append(f"{key}: invalid closed-case filename")
            continue
        relative = f"assets/images/jamaica/approved/{filename}"
        if expected.get(key) != relative:
            errors.append(f"{key}: Country JSON image reference does not match closed case")
        if not isinstance(recorded_sha, str) or not re.fullmatch(r"[a-f0-9]{40}", recorded_sha):
            errors.append(f"{key}: invalid Git blob SHA")
            continue
        asset = base / relative
        if not asset.is_file() or blob_sha(asset.read_bytes()) != recorded_sha:
            errors.append(f"{key}: original raster bytes missing or changed")
        observed_hashes.append(recorded_sha)
        if key in SCENE_IDS and row.get("generationId") is not None:
            errors.append(f"{key}: unknown original Scene generation ID must remain null")
        if key == "HERO" and row.get("generationId") != "91cc1acf-ce3d-4fb5-b4bf-9596070b4d94":
            errors.append("HERO: exact verified original generation ID changed")
        if key in FOOD_IDS and (not isinstance(row.get("generationId"), str) or not row["generationId"]):
            errors.append(f"{key}: known Taste generation ID may not be erased")
    if len(set(observed_hashes)) != 13:
        errors.append("Existing thirteen raster assets are not unique")
    # Physical user handoff/QA is independent of unrecoverable generation metadata.
    handoff = state.get("assetHandoff") or {}
    if (handoff.get("state") != "PASS" or handoff.get("verifiedRasterCount") != 13 or
            handoff.get("mode") != "USER_HANDOFF" or not handoff.get("verifiedAt")):
        errors.append("Original thirteen raster bytes need a real verified USER_HANDOFF PASS")
    return errors


def applies(state: dict[str, Any], root: Path | None = None) -> bool:
    return not validate(state, root)


if __name__ == "__main__":
    import sys
    state = _load(ROOT / "ops/country-production/jamaica.json")
    problems = validate(state)
    print("Jamaica closed provenance case:", "PASS" if not problems else "FAIL")
    for problem in problems:
        print("-", problem)
    sys.exit(bool(problems))
