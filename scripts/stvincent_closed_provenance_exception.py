#!/usr/bin/env python3
"""Closed provenance validation for the exact Saint Vincent 13-raster handoff.

This is a preservation exception for one historical Country build. It never
synthesizes generation UUIDs, image approvals, or batch ledgers. It permits the
already-generated, user-selected raster set to enter normal page QA only when
all thirteen exact delivery blobs are present and the original generation State
remains explicitly unrecovered.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEGACY_CASE_ID = "stvincentgrenadines-preserve-13-20260923"
LEGACY_SOURCE_COMMIT = "ce673cdcfd63a194fcced6912b38c5a0c54fe567"
FINAL_CASE_ID = "stvincentgrenadines-final-13-20260924"
FINAL_SOURCE_COMMIT = "1f308a1953a087f2fe959242a9745691872d5f82"
# Backward-compatible aliases retained for historical tests/importers.
CASE_ID = LEGACY_CASE_ID
SOURCE_COMMIT = LEGACY_SOURCE_COMMIT
SCENE_IDS = tuple(f"S{x:02d}" for x in range(1, 9))
FOOD_IDS = tuple(f"FOOD{x:02d}" for x in range(1, 5))
ALL_IDS = ("HERO", *SCENE_IDS, *FOOD_IDS)

# Final delivery blobs. Six 1536x1024 originals were deterministically resized
# to 1200x800 without cropping after the source handoff; no image was regenerated.
LEGACY_ASSETS = {
    "HERO": ("hero.webp", "4a11bf88e2e71f9831ded5d9cf361586e8e36571"),
    "S01": ("scene-1.webp", "e78952dc4126983ddcfeda5f424654bda83716c4"),
    "S02": ("scene-2.webp", "f4a921557428b642eb264842681f73e58dcefd58"),
    "S03": ("scene-3.webp", "c8e35ae34baa3a1bbe540ff31dbbc54aa7df39b6"),
    "S04": ("scene-4.webp", "dc40b05422820612f0815c860c4d4cfda3280998"),
    "S05": ("scene-5.webp", "936e588801e60ac4a8ea5eb15c583b7fa788e15e"),
    "S06": ("scene-6.webp", "85aca6a4743e1818486aee2021b9d604dd560e77"),
    "S07": ("scene-7.webp", "b741112bece42eaf4ad0adec17e28039156fee31"),
    "S08": ("scene-8.webp", "799e7f593f7c6bfdabf0f69bdad3ff83db7b230a"),
    "FOOD01": ("food-1.webp", "e04dcc68871f35ae7c1d0977f3fad01aaaeab776"),
    "FOOD02": ("food-2.webp", "32569b81b6fb4c870f91d9a2081f881e6a82bd15"),
    "FOOD03": ("food-3.webp", "022b4ecfb60a2fce4fa2a092cb64a7a605cf533d"),
    "FOOD04": ("food-4.webp", "e595f6866b256276b182ed17db7f57f8a42e69b5"),
}

FINAL_ASSETS = {
    "HERO": ("hero.webp", "4a11bf88e2e71f9831ded5d9cf361586e8e36571"),
    "S01": ("scene-1.webp", "11b68d2e58ea2b0922a33630fcaa2fdcf601994e"),
    "S02": ("scene-2.webp", "70e6de5ea071ca583e159f5d074a4e427d46c0e9"),
    "S03": ("scene-3.webp", "5c96c176214489083b82cb3a7b571a69edf87f42"),
    "S04": ("scene-4.webp", "5afb3bcbc48b1dd8f7c86e784f2ccafe6b1b8c0b"),
    "S05": ("scene-5.webp", "3caafc226094e22a83a2745a1418c3b8e135c103"),
    "S06": ("scene-6.webp", "2ed4f1dbda54477e503e24556932f93f3afe25c1"),
    "S07": ("scene-7.webp", "b4c91966bbf9ef18dbc950b598a3a0c3a562aaaf"),
    "S08": ("scene-8.webp", "6478239be33c921eb52dbdbe6e8dca1101965c20"),
    "FOOD01": ("food-1.webp", "d290086294a33d0e0fad57d7baa75a4f79ccefac"),
    "FOOD02": ("food-2.webp", "1b68c5f4ed4451f9437d884f86e1b6dbfa928604"),
    "FOOD03": ("food-3.webp", "c4ef0ef36ebcbf7aa0c1f2f6f2f8fddb139ee50d"),
    "FOOD04": ("food-4.webp", "e2d0fec0669e3f956f7c2ff96d48aee93aa6a690"),
}

CASES = {
    LEGACY_CASE_ID: {
        "sourceCommit": LEGACY_SOURCE_COMMIT,
        "authorizationDate": "2026-09-24",
        "assets": LEGACY_ASSETS,
    },
    FINAL_CASE_ID: {
        "sourceCommit": FINAL_SOURCE_COMMIT,
        "authorizationDate": "2026-09-24",
        "assets": FINAL_ASSETS,
    },
}


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(state: dict[str, Any], root: Path | None = None) -> list[str]:
    base = root or ROOT
    if state.get("slug") != "stvincentgrenadines":
        return ["Closed Saint Vincent exception cannot be used by another Country"]

    record = state.get("closedProvenanceException")
    if not isinstance(record, dict):
        return ["Closed Saint Vincent exception requires its exact authorization record"]
    case = CASES.get(record.get("id"))
    if case is None:
        return ["Closed Saint Vincent exception is not an authorized immutable case"]
    expected_record = {
        "id": record.get("id"),
        "status": "APPLIED",
        "sourceCommit": case["sourceCommit"],
        "authorizationDate": case["authorizationDate"],
    }
    if record != expected_record:
        return ["Closed Saint Vincent exception requires its exact authorization record"]
    assets = case["assets"]

    try:
        country = _load(base / "data/countries/stvincentgrenadines.json")
    except (OSError, ValueError, TypeError) as exc:
        return [f"Saint Vincent Country source cannot be parsed: {exc}"]

    errors: list[str] = []
    if country.get("slug") != "stvincentgrenadines":
        errors.append("Country JSON slug mismatch")

    scenes = state.get("scenes")
    taste = state.get("taste")
    country_scenes = country.get("scenes")
    country_food = (country.get("taste") or {}).get("items")
    if (not isinstance(scenes, list) or len(scenes) != 8 or
            not isinstance(taste, list) or len(taste) != 4 or
            not isinstance(country_scenes, list) or len(country_scenes) != 8 or
            not isinstance(country_food, list) or len(country_food) != 4):
        return errors + ["Source and State must retain exactly eight Scenes and four Taste items"]

    hero = state.get("hero") or {}
    if hero.get("state") != "NOT_STARTED":
        errors.append("HERO: original generation State must remain explicitly unrecovered")
    if hero.get("approvedGenerationId") or hero.get("candidateGenerationId"):
        errors.append("HERO: no unverified generation ID may be added")

    for kind, records, names in (("SCENE", scenes, SCENE_IDS), ("TASTE", taste, FOOD_IDS)):
        for original, key in zip(records, names):
            if original.get("id") != key or original.get("state") != "NOT_STARTED":
                errors.append(f"{kind} {key}: original generation State must remain explicitly unrecovered")
            if original.get("approvedGenerationId") or original.get("candidateGenerationId"):
                errors.append(f"{kind} {key}: no unverified generation ID may be added")

    for key in ("sceneBatchReview", "tasteBatchReview"):
        batch = state.get(key) or {}
        if batch.get("approval") != "PENDING" or batch.get("rounds") != []:
            errors.append(f"{key}: historical batch approvals must not be fabricated")

    expected = {"HERO": country.get("hero", {}).get("image")}
    expected.update({k: x.get("image") for k, x in zip(SCENE_IDS, country_scenes)})
    expected.update({k: x.get("image") for k, x in zip(FOOD_IDS, country_food)})

    observed: list[str] = []
    for key in ALL_IDS:
        filename, recorded_sha = assets[key]
        relative = f"assets/images/stvincentgrenadines/approved/{filename}"
        if expected.get(key) != relative:
            errors.append(f"{key}: Country JSON image reference does not match preserved case")
        path = base / relative
        if not path.is_file():
            errors.append(f"{key}: preserved raster is missing")
            continue
        actual = blob_sha(path.read_bytes())
        if actual != recorded_sha:
            errors.append(f"{key}: preserved delivery raster bytes changed")
        observed.append(actual)

    if len(observed) != 13 or len(set(observed)) != 13:
        errors.append("Existing thirteen raster assets are not all present and unique")

    handoff = state.get("assetHandoff") or {}
    if (handoff.get("mode") != "USER_HANDOFF" or handoff.get("state") != "PASS"
            or handoff.get("verifiedRasterCount") != 13 or not handoff.get("verifiedAt")):
        errors.append("Exact thirteen-raster USER_HANDOFF must be verified")

    return errors


def applies(state: dict[str, Any], root: Path | None = None) -> bool:
    return not validate(state, root)


if __name__ == "__main__":
    import sys
    state = _load(ROOT / "ops/country-production/stvincentgrenadines.json")
    problems = validate(state)
    print("Saint Vincent closed provenance case:", "PASS" if not problems else "FAIL")
    for problem in problems:
        print("-", problem)
    sys.exit(bool(problems))
