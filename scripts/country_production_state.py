#!/usr/bin/env python3
"""Validate and inspect JOURNEY ATLAS Country production state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "ops" / "country-production"
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATH = ROOT / "data" / "atlas-destinations.json"

PHASES = {
    "CONTENT", "HERO",
    "SCENES_INITIAL", "SCENES_REVIEW", "SCENES_REGEN",
    "TASTE_INITIAL", "TASTE_REVIEW", "TASTE_REGEN",
    "MAP", "ASSET_QA", "IMPLEMENTATION", "QA", "REVIEW", "PUBLISH", "COMPLETE",
}
ASSET_STATES = {"NOT_STARTED", "REVIEW_CANDIDATE", "REGENERATE", "APPROVED"}
IMPLEMENTATION_STATES = {"NOT_STARTED", "DONE"}
QA_STATES = {"NOT_STARTED", "PASS", "FAIL"}
REVIEW_DEPLOYMENT_STATES = {"NOT_STARTED", "DONE"}
APPROVAL_STATES = {"PENDING", "APPROVED"}
PUBLICATION_STATES = {"DRAFT", "REVIEWABLE", "PUBLISHED"}

SCENE_IDS = [f"S{i:02d}" for i in range(1, 9)]
FOOD_IDS = [f"FOOD{i:02d}" for i in range(1, 5)]

AFTER_HERO = {
    "SCENES_INITIAL", "SCENES_REVIEW", "SCENES_REGEN",
    "TASTE_INITIAL", "TASTE_REVIEW", "TASTE_REGEN",
    "MAP", "ASSET_QA", "IMPLEMENTATION", "QA", "REVIEW", "PUBLISH", "COMPLETE",
}
AFTER_SCENES = {
    "TASTE_INITIAL", "TASTE_REVIEW", "TASTE_REGEN",
    "MAP", "ASSET_QA", "IMPLEMENTATION", "QA", "REVIEW", "PUBLISH", "COMPLETE",
}
AFTER_TASTE = {"MAP", "ASSET_QA", "IMPLEMENTATION", "QA", "REVIEW", "PUBLISH", "COMPLETE"}
AFTER_MAP = {"ASSET_QA", "IMPLEMENTATION", "QA", "REVIEW", "PUBLISH", "COMPLETE"}
AFTER_IMPLEMENTATION = {"QA", "REVIEW", "PUBLISH", "COMPLETE"}
AFTER_QA = {"REVIEW", "PUBLISH", "COMPLETE"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def state_path(slug: str) -> Path:
    return STATE_DIR / f"{slug}.json"


def first_asset(items: list[dict], wanted: str) -> str | None:
    for item in items:
        if item.get("state") == wanted:
            return item.get("id")
    return None


def derive_next(state: dict) -> dict:
    phase = state.get("phase")
    hero = state.get("hero") or {}
    scenes = state.get("scenes") or []
    taste = state.get("taste") or []
    map_state = state.get("map") or {}

    if phase == "CONTENT":
        return {"action": "COMPLETE_CONTENT_DESIGN", "asset": None}

    if phase == "HERO":
        hs = hero.get("state")
        if hs in {"NOT_STARTED", "REGENERATE"}:
            return {"action": "GENERATE_HERO", "asset": "HERO"}
        if hs == "REVIEW_CANDIDATE":
            return {"action": "WAIT_HERO_APPROVAL", "asset": "HERO"}
        if hs == "APPROVED":
            return {"action": "START_SCENES", "asset": None}

    if phase == "SCENES_INITIAL":
        asset = first_asset(scenes, "NOT_STARTED")
        if asset:
            return {"action": "GENERATE_SCENE", "asset": asset}
        return {"action": "BATCH_REVIEW_SCENES", "asset": None}

    if phase == "SCENES_REVIEW":
        return {"action": "WAIT_SCENE_BATCH_REVIEW", "asset": None}

    if phase == "SCENES_REGEN":
        asset = first_asset(scenes, "REGENERATE")
        if asset:
            return {"action": "GENERATE_SCENE", "asset": asset}
        return {"action": "BATCH_REVIEW_SCENES", "asset": None}

    if phase == "TASTE_INITIAL":
        asset = first_asset(taste, "NOT_STARTED")
        if asset:
            return {"action": "GENERATE_FOOD", "asset": asset}
        return {"action": "BATCH_REVIEW_TASTE", "asset": None}

    if phase == "TASTE_REVIEW":
        return {"action": "WAIT_TASTE_BATCH_REVIEW", "asset": None}

    if phase == "TASTE_REGEN":
        asset = first_asset(taste, "REGENERATE")
        if asset:
            return {"action": "GENERATE_FOOD", "asset": asset}
        return {"action": "BATCH_REVIEW_TASTE", "asset": None}

    if phase == "MAP":
        ms = map_state.get("state")
        if ms in {"NOT_STARTED", "REGENERATE"}:
            return {"action": "BUILD_MAP", "asset": "MAP"}
        if ms == "REVIEW_CANDIDATE":
            return {"action": "QA_MAP", "asset": "MAP"}
        if ms == "APPROVED":
            return {"action": "VERIFY_APPROVED_ASSETS", "asset": None}

    if phase == "ASSET_QA":
        return {"action": "VERIFY_APPROVED_ASSETS", "asset": None}

    if phase == "IMPLEMENTATION":
        return {"action": "IMPLEMENT_COUNTRY_PAGE", "asset": None}

    if phase == "QA":
        return {"action": "RUN_COUNTRY_QA", "asset": None}

    if phase == "REVIEW":
        return {"action": "REVIEW_CANONICAL_URL", "asset": None}

    if phase == "PUBLISH":
        return {"action": "PUBLISH_COUNTRY", "asset": None}

    if phase == "COMPLETE":
        return {"action": "NONE", "asset": None}

    return {"action": "INVALID_STATE", "asset": None}


def validate_ids(errors: list[str], filename: str, items: object, expected: list[str], label: str) -> list[dict]:
    if not isinstance(items, list):
        errors.append(f"{filename}: {label} must be a list")
        return []
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    if ids != expected:
        errors.append(f"{filename}: {label} ids must be {expected}, got {ids}")
    for item in items:
        if not isinstance(item, dict):
            errors.append(f"{filename}: {label} contains non-object entry")
            continue
        if item.get("state") not in ASSET_STATES:
            errors.append(f"{filename}: {label} {item.get('id')} has invalid state {item.get('state')!r}")
    return [item for item in items if isinstance(item, dict)]


def all_approved(items: list[dict]) -> bool:
    return bool(items) and all(item.get("state") == "APPROVED" for item in items)


def registry_map() -> dict[str, dict]:
    if not REGISTRY_PATH.exists():
        return {}
    data = load_json(REGISTRY_PATH)
    return {item.get("slug"): item for item in data.get("destinations", []) if item.get("slug")}


def validate_state(path: Path, registry: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    filename = path.name
    try:
        state = load_json(path)
    except Exception as exc:
        return [f"{filename}: cannot parse JSON: {exc}"]

    slug = state.get("slug")
    if path.stem != slug:
        errors.append(f"{filename}: slug {slug!r} does not match filename")
    if state.get("schemaVersion") != 1:
        errors.append(f"{filename}: schemaVersion must be 1")
    if state.get("phase") not in PHASES:
        errors.append(f"{filename}: invalid phase {state.get('phase')!r}")
    if not isinstance(state.get("stateRevision"), int) or state.get("stateRevision", 0) < 1:
        errors.append(f"{filename}: stateRevision must be a positive integer")
    if not isinstance(state.get("contentRef"), str) or not state.get("contentRef"):
        errors.append(f"{filename}: contentRef is required")

    policy = state.get("executionPolicy")
    if policy is not None:
        if not isinstance(policy, dict):
            errors.append(f"{filename}: executionPolicy must be an object")
        else:
            expected_policy = {
                "heroApproval": "INDIVIDUAL",
                "sceneApproval": "BATCH",
                "tasteApproval": "BATCH",
                "autoContinueImageRounds": True,
                "waitForStateOnlyCI": False,
                "batchMaterialization": True,
                "autoPostVisualPipeline": True,
                "singleReviewIntegration": True,
            }
            for key, expected in expected_policy.items():
                if policy.get(key) != expected:
                    errors.append(
                        f"{filename}: executionPolicy.{key} must be {expected!r}, got {policy.get(key)!r}"
                    )

    hero = state.get("hero") if isinstance(state.get("hero"), dict) else {}
    if hero.get("state") not in ASSET_STATES:
        errors.append(f"{filename}: hero has invalid state {hero.get('state')!r}")

    scenes = validate_ids(errors, filename, state.get("scenes"), SCENE_IDS, "scenes")
    taste = validate_ids(errors, filename, state.get("taste"), FOOD_IDS, "taste")

    map_state = state.get("map") if isinstance(state.get("map"), dict) else {}
    if map_state.get("state") not in ASSET_STATES:
        errors.append(f"{filename}: map has invalid state {map_state.get('state')!r}")

    implementation = state.get("implementation") if isinstance(state.get("implementation"), dict) else {}
    qa = state.get("qa") if isinstance(state.get("qa"), dict) else {}
    review = state.get("reviewDeployment") if isinstance(state.get("reviewDeployment"), dict) else {}
    final_approval = state.get("finalApproval") if isinstance(state.get("finalApproval"), dict) else {}
    publication = state.get("publication") if isinstance(state.get("publication"), dict) else {}

    if implementation.get("state") not in IMPLEMENTATION_STATES:
        errors.append(f"{filename}: invalid implementation state")
    if qa.get("state") not in QA_STATES:
        errors.append(f"{filename}: invalid QA state")
    if review.get("state") not in REVIEW_DEPLOYMENT_STATES:
        errors.append(f"{filename}: invalid reviewDeployment state")
    if final_approval.get("state") not in APPROVAL_STATES:
        errors.append(f"{filename}: invalid finalApproval state")
    if publication.get("state") not in PUBLICATION_STATES:
        errors.append(f"{filename}: invalid publication state")
    if not isinstance(publication.get("atlasPublished"), bool):
        errors.append(f"{filename}: publication.atlasPublished must be boolean")

    phase = state.get("phase")
    if phase in AFTER_HERO and hero.get("state") != "APPROVED":
        errors.append(f"{filename}: phase {phase} requires APPROVED hero")
    if phase in AFTER_SCENES and not all_approved(scenes):
        errors.append(f"{filename}: phase {phase} requires all 8 scenes APPROVED")
    if phase in AFTER_TASTE and not all_approved(taste):
        errors.append(f"{filename}: phase {phase} requires all 4 Taste images APPROVED")
    if phase in AFTER_MAP and map_state.get("state") != "APPROVED":
        errors.append(f"{filename}: phase {phase} requires APPROVED map")
    if phase in AFTER_IMPLEMENTATION and implementation.get("state") != "DONE":
        errors.append(f"{filename}: phase {phase} requires implementation DONE")
    if phase in AFTER_QA and qa.get("state") != "PASS":
        errors.append(f"{filename}: phase {phase} requires QA PASS")

    if phase in {"REVIEW", "PUBLISH", "COMPLETE"}:
        if review.get("state") != "DONE":
            errors.append(f"{filename}: phase {phase} requires review deployment DONE")
        expected_url = f"https://atlas.yagenji.com/countries/{slug}/"
        if review.get("url") != expected_url:
            errors.append(f"{filename}: review URL must be {expected_url}")

    if phase == "PUBLISH" and final_approval.get("state") != "APPROVED":
        errors.append(f"{filename}: PUBLISH requires explicit final approval")

    if phase == "COMPLETE":
        if final_approval.get("state") != "APPROVED":
            errors.append(f"{filename}: COMPLETE requires final approval")
        if publication.get("state") != "PUBLISHED" or publication.get("atlasPublished") is not True:
            errors.append(f"{filename}: COMPLETE requires PUBLISHED / atlasPublished:true")
        if qa.get("productionState") != "PASS":
            errors.append(f"{filename}: COMPLETE requires production QA PASS")

    expected_next = derive_next(state)
    if state.get("next") != expected_next:
        errors.append(f"{filename}: next mismatch; expected {expected_next}, got {state.get('next')}")

    registry_entry = registry.get(slug)
    if registry_entry is None:
        errors.append(f"{filename}: slug missing from atlas destination registry")
    else:
        actual_published = bool(registry_entry.get("atlasPublished"))
        if publication.get("atlasPublished") != actual_published:
            errors.append(
                f"{filename}: state atlasPublished={publication.get('atlasPublished')} "
                f"does not match registry={actual_published}"
            )

    # For content already authoritative on main, validate state against actual Country JSON/assets.
    if state.get("contentRef") == "main":
        country_path = COUNTRY_DIR / f"{slug}.json"
        if not country_path.exists():
            errors.append(f"{filename}: contentRef=main but {country_path.relative_to(ROOT)} is missing")
        else:
            country = load_json(country_path)
            if hero.get("state") == "APPROVED" and hero.get("asset") != country.get("hero", {}).get("image"):
                errors.append(f"{filename}: approved hero asset does not match Country JSON")

            country_scenes = country.get("scenes") if isinstance(country.get("scenes"), list) else []
            if len(country_scenes) == 8:
                for state_item, country_item in zip(scenes, country_scenes):
                    if state_item.get("state") == "APPROVED" and state_item.get("asset") != country_item.get("image"):
                        errors.append(f"{filename}: {state_item.get('id')} approved asset does not match Country JSON")

            country_taste = country.get("taste", {}).get("items")
            if isinstance(country_taste, list) and len(country_taste) == 4:
                for state_item, country_item in zip(taste, country_taste):
                    if state_item.get("state") == "APPROVED" and state_item.get("asset") != country_item.get("image"):
                        errors.append(f"{filename}: {state_item.get('id')} approved asset does not match Country JSON")

            if map_state.get("state") == "APPROVED" and map_state.get("asset") != country.get("map", {}).get("svg"):
                errors.append(f"{filename}: approved map asset does not match Country JSON")

        for owner, item in [("hero", hero), ("map", map_state)] + [
            (x.get("id", "scene"), x) for x in scenes
        ] + [(x.get("id", "food"), x) for x in taste]:
            if item.get("state") == "APPROVED":
                asset = item.get("asset")
                if not isinstance(asset, str) or not asset:
                    errors.append(f"{filename}: {owner} APPROVED without asset path")
                elif not (ROOT / asset).exists():
                    errors.append(f"{filename}: {owner} approved asset missing: {asset}")

    return errors


def validate_all() -> list[str]:
    errors: list[str] = []
    registry = registry_map()
    if not STATE_DIR.exists():
        return ["production state directory is missing"]
    paths = sorted(STATE_DIR.glob("*.json"))
    if not paths:
        return ["no Country production state files found"]
    for path in paths:
        errors.extend(validate_state(path, registry))
    return errors


def cmd_validate() -> int:
    errors = validate_all()
    if errors:
        print("Country production state validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    count = len(list(STATE_DIR.glob("*.json")))
    print(f"Country production state validation passed: {count} state file(s)")
    return 0


def cmd_next(slug: str) -> int:
    path = state_path(slug)
    if not path.exists():
        print(f"Missing state: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    state = load_json(path)
    derived = derive_next(state)
    print(json.dumps({"slug": slug, "phase": state.get("phase"), "next": derived}, ensure_ascii=False))
    return 0


def cmd_summary() -> int:
    registry = registry_map()
    rows = []
    for path in sorted(STATE_DIR.glob("*.json")):
        state = load_json(path)
        slug = state.get("slug")
        derived = derive_next(state)
        rows.append({
            "slug": slug,
            "phase": state.get("phase"),
            "publication": state.get("publication", {}).get("state"),
            "atlasPublished": registry.get(slug, {}).get("atlasPublished"),
            "nextAction": derived.get("action"),
            "nextAsset": derived.get("asset"),
            "revision": state.get("stateRevision"),
        })
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] not in {"validate", "next", "summary"}:
        print("Usage: country_production_state.py validate | next <slug> | summary", file=sys.stderr)
        return 2
    if args[0] == "validate":
        return cmd_validate()
    if args[0] == "summary":
        return cmd_summary()
    if len(args) != 2:
        print("Usage: country_production_state.py next <slug>", file=sys.stderr)
        return 2
    return cmd_next(args[1])


if __name__ == "__main__":
    raise SystemExit(main())
