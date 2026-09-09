#!/usr/bin/env python3
"""Validate and inspect JOURNEY ATLAS Country production state."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "ops" / "country-production"
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATHS = [
    ROOT / "data" / "atlas-destinations.json",
    ROOT / "data" / "atlas-destinations-editorial.json",
]

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
            if hs == "REGENERATE" and prompt_refresh_required(hero):
                return {"action": "REFRESH_RENDER_PACKET", "asset": "HERO"}
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
            item = next((x for x in scenes if x.get("id") == asset), {})
            if prompt_refresh_required(item):
                return {"action": "REFRESH_RENDER_PACKET", "asset": asset}
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
            item = next((x for x in taste if x.get("id") == asset), {})
            if prompt_refresh_required(item):
                return {"action": "REFRESH_RENDER_PACKET", "asset": asset}
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


def collect_generation_ids(hero: dict, scenes: list[dict], taste: list[dict]) -> list[tuple[str, str, str]]:
    refs: list[tuple[str, str, str]] = []
    groups = [("HERO", [hero]), ("SCENE", scenes), ("TASTE", taste)]
    for group, items in groups:
        for item in items:
            asset_id = item.get("id") or "HERO"
            owner = f"{group}:{asset_id}"
            for key in ("approvedGenerationId", "candidateGenerationId"):
                value = item.get(key)
                if isinstance(value, str) and value:
                    refs.append((value, owner, key))
            rejected = item.get("rejectedGenerationIds")
            if isinstance(rejected, list):
                for value in rejected:
                    if isinstance(value, str) and value:
                        refs.append((value, owner, "rejectedGenerationIds"))
    return refs


def validate_generation_id_uniqueness(errors: list[str], filename: str, hero: dict, scenes: list[dict], taste: list[dict]) -> None:
    seen: dict[str, list[tuple[str, str]]] = {}
    for generation_id, owner, field in collect_generation_ids(hero, scenes, taste):
        seen.setdefault(generation_id, []).append((owner, field))
    for generation_id, refs in seen.items():
        if len(refs) > 1:
            errors.append(
                f"{filename}: generation id {generation_id} must appear exactly once, got: {refs}"
            )


def render_packet_valid(item: dict, expected_kind: str) -> bool:
    packet = item.get("renderPacket")
    if not isinstance(packet, dict):
        return False
    if packet.get("kind") != expected_kind:
        return False
    if packet.get("contentId") != item.get("contentId"):
        return False
    if not isinstance(packet.get("identity"), str) or not packet.get("identity").strip():
        return False
    if packet.get("independentGeneration") is not True:
        return False
    if packet.get("forbidPreviousAssetReuse") is not True:
        return False
    if expected_kind in {"HERO", "SCENE"} and packet.get("noAddedText") is not True:
        return False
    if expected_kind == "TASTE":
        if packet.get("singleDishOnly") is not True:
            return False
        if packet.get("cleanNeutralBackground") is not True:
            return False
    return True


def prompt_refresh_required(item: dict) -> bool:
    if item.get("state") != "REGENERATE":
        return False
    count = item.get("promptSeriesRejectCount", 0)
    return isinstance(count, int) and count >= 2


def now_jst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def new_state(destination: dict) -> dict:
    slug = destination["slug"]
    state = {
        "schemaVersion": 1,
        "slug": slug,
        "countryName": destination.get("nameEn", slug).upper(),
        "contentRef": f"country/{slug}",
        "stateRef": f"country/{slug}",
        "phase": "CONTENT",
        "stateRevision": 1,
        "updatedAt": now_jst(),
        "hero": {
            "state": "NOT_STARTED",
            "asset": None,
            "contentId": None,
        },
        "scenes": [
            {
                "id": scene_id,
                "state": "NOT_STARTED",
                "asset": None,
                "contentId": None,
            }
            for scene_id in SCENE_IDS
        ],
        "taste": [
            {
                "id": food_id,
                "state": "NOT_STARTED",
                "asset": None,
                "contentId": None,
            }
            for food_id in FOOD_IDS
        ],
        "map": {
            "state": "NOT_STARTED",
            "asset": None,
        },
        "implementation": {
            "state": "NOT_STARTED",
        },
        "qa": {
            "state": "NOT_STARTED",
            "productionState": "NOT_STARTED",
        },
        "reviewDeployment": {
            "state": "NOT_STARTED",
            "url": None,
        },
        "finalApproval": {
            "state": "PENDING",
        },
        "publication": {
            "state": "DRAFT",
            "atlasPublished": False,
        },
        "executionPolicy": {
            "heroApproval": "INDIVIDUAL",
            "sceneApproval": "BATCH",
            "tasteApproval": "BATCH",
            "autoContinueImageRounds": True,
            "waitForStateOnlyCI": False,
            "batchMaterialization": True,
            "autoPostVisualPipeline": True,
            "singleReviewIntegration": True,
        },
        "imageGenerationPolicy": {
            "revision": 4,
            "sceneMode": "ONE_TARGET_ONE_STANDALONE_IMAGE",
            "tasteMode": "ONE_TARGET_ONE_STANDALONE_IMAGE",
            "sceneReview": "BATCH_ONLY",
            "tasteReview": "BATCH_ONLY",
            "mandatoryNoAddedText": True,
            "rejectTypographyImmediately": True,
            "rejectCollageImmediately": True,
            "rejectPreviousAssetRepeatImmediately": True,
            "candidateVisualQaRequired": True,
            "batchPerceptualDuplicateGate": True,
            "maxConsecutiveHardFailuresPerPromptSeries": 2,
            "requireRenderPacketRefreshAfterLimit": True,
            "approvedAssetRegeneration": False,
            "runtimeContinuation": "AUTO_IF_SUPPORTED",
        },
    }
    state["next"] = derive_next(state)
    return state


def cmd_init(slug: str) -> int:
    path = state_path(slug)
    if path.exists():
        print(f"State already exists: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    registry = registry_map()
    destination = registry.get(slug)
    if destination is None:
        print(f"Unknown destination slug: {slug}", file=sys.stderr)
        return 1
    if destination.get("atlasPublished"):
        print(f"Refusing to initialize new production state for already-published slug: {slug}", file=sys.stderr)
        return 1

    state = new_state(destination)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {path.relative_to(ROOT)}")
    print("Next: complete Content Design, then fill stable contentId + renderPacket before entering image phases.")
    return 0


def registry_map() -> dict[str, dict]:
    registry: dict[str, dict] = {}
    for path in REGISTRY_PATHS:
        if not path.exists():
            continue
        data = load_json(path)
        for item in data.get("destinations", []):
            slug = item.get("slug")
            if slug:
                registry[slug] = item
    return registry


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

    image_policy_revision = state.get("imageGenerationPolicy", {}).get("revision")
    if isinstance(image_policy_revision, int) and image_policy_revision >= 4:
        explicit_state_ref = state.get("stateRef")
        if explicit_state_ref is not None and (
            not isinstance(explicit_state_ref, str) or not explicit_state_ref
        ):
            errors.append(f"{filename}: stateRef must be a non-empty string when present")
        state_ref = explicit_state_ref or state.get("contentRef")
        working_phases = {
            "CONTENT", "HERO",
            "SCENES_INITIAL", "SCENES_REVIEW", "SCENES_REGEN",
            "TASTE_INITIAL", "TASTE_REVIEW", "TASTE_REGEN",
            "MAP", "ASSET_QA", "IMPLEMENTATION", "QA",
        }
        if state.get("phase") in working_phases and state_ref != state.get("contentRef"):
            errors.append(
                f"{filename}: active revision 4 stateRef must match contentRef "
                f"({state_ref!r} != {state.get('contentRef')!r})"
            )
        if state.get("phase") in {"REVIEW", "PUBLISH", "COMPLETE"} and state_ref != "main":
            errors.append(
                f"{filename}: {state.get('phase')} revision 4 stateRef must resolve to 'main'"
            )

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

    image_phases = {
        "HERO",
        "SCENES_INITIAL", "SCENES_REVIEW", "SCENES_REGEN",
        "TASTE_INITIAL", "TASTE_REVIEW", "TASTE_REGEN",
    }
    if state.get("phase") in image_phases:
        image_policy = state.get("imageGenerationPolicy")
        base_image_policy = {
            "sceneMode": "ONE_TARGET_ONE_STANDALONE_IMAGE",
            "tasteMode": "ONE_TARGET_ONE_STANDALONE_IMAGE",
            "sceneReview": "BATCH_ONLY",
            "tasteReview": "BATCH_ONLY",
            "mandatoryNoAddedText": True,
            "rejectTypographyImmediately": True,
            "rejectCollageImmediately": True,
            "rejectPreviousAssetRepeatImmediately": True,
            "maxConsecutiveHardFailuresPerPromptSeries": 2,
            "requireRenderPacketRefreshAfterLimit": True,
            "approvedAssetRegeneration": False,
            "runtimeContinuation": "AUTO_IF_SUPPORTED",
        }
        if not isinstance(image_policy, dict):
            errors.append(
                f"{filename}: active image-production phase requires imageGenerationPolicy revision 3 or 4"
            )
        else:
            revision = image_policy.get("revision")
            if revision not in {3, 4}:
                errors.append(
                    f"{filename}: imageGenerationPolicy.revision must be 3 or 4, got {revision!r}"
                )
            for key, expected in base_image_policy.items():
                if image_policy.get(key) != expected:
                    errors.append(
                        f"{filename}: imageGenerationPolicy.{key} must be "
                        f"{expected!r}, got {image_policy.get(key)!r}"
                    )
            if revision == 4:
                revision4_policy = {
                    "candidateVisualQaRequired": True,
                    "batchPerceptualDuplicateGate": True,
                }
                for key, expected in revision4_policy.items():
                    if image_policy.get(key) != expected:
                        errors.append(
                            f"{filename}: imageGenerationPolicy.{key} must be "
                            f"{expected!r}, got {image_policy.get(key)!r}"
                        )

    hero = state.get("hero") if isinstance(state.get("hero"), dict) else {}
    if hero.get("state") not in ASSET_STATES:
        errors.append(f"{filename}: hero has invalid state {hero.get('state')!r}")

    scenes = validate_ids(errors, filename, state.get("scenes"), SCENE_IDS, "scenes")
    taste = validate_ids(errors, filename, state.get("taste"), FOOD_IDS, "taste")

    # Batch approval is a state-machine rule, not a prose convention.
    phase = state.get("phase")
    if phase in {"SCENES_INITIAL", "SCENES_REVIEW"}:
        approved_ids = [x.get("id") for x in scenes if x.get("state") == "APPROVED"]
        if approved_ids:
            errors.append(
                f"{filename}: {phase} cannot contain APPROVED Scenes before the 8-Scene batch review: {approved_ids}"
            )
    if phase in {"TASTE_INITIAL", "TASTE_REVIEW"}:
        approved_ids = [x.get("id") for x in taste if x.get("state") == "APPROVED"]
        if approved_ids:
            errors.append(
                f"{filename}: {phase} cannot contain APPROVED Taste items before the 4-Taste batch review: {approved_ids}"
            )

    if phase in image_phases:
        active_items: list[tuple[str, dict]] = []
        if phase == "HERO":
            active_items = [("HERO", hero)]
        elif phase.startswith("SCENES"):
            active_items = [("SCENE", x) for x in scenes if x.get("state") in {"NOT_STARTED", "REGENERATE", "REVIEW_CANDIDATE"}]
        elif phase.startswith("TASTE"):
            active_items = [("TASTE", x) for x in taste if x.get("state") in {"NOT_STARTED", "REGENERATE", "REVIEW_CANDIDATE"}]
        for kind, item in active_items:
            owner_id = item.get("id") or "HERO"
            if not isinstance(item.get("contentId"), str) or not item.get("contentId"):
                errors.append(f"{filename}: active {kind} {owner_id} requires contentId")
            if not render_packet_valid(item, kind):
                errors.append(f"{filename}: active {kind} {owner_id} requires a complete renderPacket")
            count = item.get("promptSeriesRejectCount", 0)
            if not isinstance(count, int) or count < 0 or count > 2:
                errors.append(f"{filename}: {kind} {owner_id} promptSeriesRejectCount must be 0..2")
            series = item.get("promptSeries", 1)
            if not isinstance(series, int) or series < 1:
                errors.append(f"{filename}: {kind} {owner_id} promptSeries must be a positive integer")
            if (
                state.get("imageGenerationPolicy", {}).get("revision") == 4
                and item.get("state") == "REVIEW_CANDIDATE"
            ):
                visual_qa = item.get("candidateVisualQa")
                if not isinstance(visual_qa, dict):
                    errors.append(
                        f"{filename}: revision 4 {kind} {owner_id} REVIEW_CANDIDATE requires candidateVisualQa"
                    )
                else:
                    for check in ("targetIdentity", "previousAssetRepeat", "collageTypography"):
                        if visual_qa.get(check) != "PASS":
                            errors.append(
                                f"{filename}: revision 4 {kind} {owner_id} candidateVisualQa.{check} must be PASS"
                            )

    validate_generation_id_uniqueness(errors, filename, hero, scenes, taste)

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

    image_policy_revision = state.get("imageGenerationPolicy", {}).get("revision")
    if isinstance(image_policy_revision, int) and image_policy_revision >= 3:
        if phase in AFTER_SCENES:
            scene_review = state.get("sceneBatchReview")
            if not isinstance(scene_review, dict) or scene_review.get("approval") != "APPROVED":
                errors.append(f"{filename}: revision 3 requires approved sceneBatchReview before leaving Scene production")
        if phase in AFTER_TASTE:
            taste_review = state.get("tasteBatchReview")
            if not isinstance(taste_review, dict) or taste_review.get("approval") != "APPROVED":
                errors.append(f"{filename}: revision 3 requires approved tasteBatchReview before leaving Taste production")
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
    if not args or args[0] not in {"validate", "next", "summary", "init"}:
        print("Usage: country_production_state.py validate | next <slug> | summary | init <slug>", file=sys.stderr)
        return 2
    if args[0] == "validate":
        return cmd_validate()
    if args[0] == "summary":
        return cmd_summary()
    if args[0] == "init":
        if len(args) != 2:
            print("Usage: country_production_state.py init <slug>", file=sys.stderr)
            return 2
        return cmd_init(args[1])
    if len(args) != 2:
        print("Usage: country_production_state.py next <slug>", file=sys.stderr)
        return 2
    return cmd_next(args[1])


if __name__ == "__main__":
    raise SystemExit(main())
