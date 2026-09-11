#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
V7_PATH = HERE / "country_production_state_v7.py"
POLICY_PATH = ROOT / "ops" / "country-production-policy.json"

spec = importlib.util.spec_from_file_location("journey_atlas_state_v7", V7_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {V7_PATH}")
v7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v7)
legacy = v7.legacy

PROTOCOL_ID = "2.0"
POST_VISUAL_PHASES = {"ASSET_QA", "IMPLEMENTATION", "QA", "REVIEW", "PUBLISH", "COMPLETE"}
PREVISUAL_CHECKS = [
    "countryJsonEditorialComplete",
    "finalExpectedImagePathsDeclared",
    "sceneCoordinatesFinal",
    "mapBuiltAndQaPassed",
    "taxonomyComplete",
    "relatedCountriesComplete",
    "nextRoutesResolved",
    "travelScaleComplete",
    "signatureFactsComplete",
    "sourcesComplete",
    "editorialQaV2Passed",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def protocol_policy() -> dict[str, Any]:
    return load_json(POLICY_PATH)


def protocol_execution_policy() -> dict[str, Any]:
    return {
        "heroApproval": "INDIVIDUAL",
        "sceneApproval": "BATCH_ONLY",
        "tasteApproval": "BATCH_ONLY",
        "autoContinueImageRounds": True,
        "userPromptBetweenSceneTargets": False,
        "userPromptBetweenTasteTargets": False,
        "runtimeBoundaryCreatesApprovalGate": False,
        "roundIntentPersistsAcrossTurnBoundary": True,
        "waitForStateOnlyCI": False,
        "assetDeliveryMode": "USER_HANDOFF",
        "repositoryMaterializationOwner": "USER",
        "batchMaterialization": True,
        "autoPostVisualPipeline": True,
        "postVisualPipeline": "SINGLE_PASS",
        "singleReviewIntegration": True,
    }


def new_state(destination: dict[str, Any]) -> dict[str, Any]:
    state = v7.new_state(destination)
    state["productionProtocolRef"] = "main:ops/country-production-policy.json"
    state["productionProtocolId"] = PROTOCOL_ID
    state["executionPolicy"] = protocol_execution_policy()
    state["preVisualBuild"] = {
        "state": "NOT_STARTED",
        "checks": {key: "PENDING" for key in PREVISUAL_CHECKS},
    }
    state["assetHandoff"] = {
        "mode": "USER_HANDOFF",
        "state": "PENDING",
        "expectedRasterCount": 13,
        "verifiedRasterCount": 0,
        "verifiedAt": None,
    }
    state["productionMetrics"] = {
        "perImageApprovalPrompts": 0,
        "sceneBatchReviews": 0,
        "tasteBatchReviews": 0,
        "assetHandoffs": 0,
        "reviewPackageIntegrations": 0,
        "browserQaCycles": 0,
        "tasteBatchApprovedAt": None,
        "canonicalReviewReadyAt": None,
    }
    state["next"] = legacy.derive_next(state)
    return state


def all_visuals_approved(state: dict[str, Any]) -> bool:
    hero_ok = isinstance(state.get("hero"), dict) and state["hero"].get("state") == "APPROVED"
    scenes = state.get("scenes") if isinstance(state.get("scenes"), list) else []
    taste = state.get("taste") if isinstance(state.get("taste"), list) else []
    scene_ok = len(scenes) == 8 and all(isinstance(item, dict) and item.get("state") == "APPROVED" for item in scenes)
    taste_ok = len(taste) == 4 and all(isinstance(item, dict) and item.get("state") == "APPROVED" for item in taste)
    scene_review = state.get("sceneBatchReview") if isinstance(state.get("sceneBatchReview"), dict) else {}
    taste_review = state.get("tasteBatchReview") if isinstance(state.get("tasteBatchReview"), dict) else {}
    return hero_ok and scene_ok and taste_ok and scene_review.get("approval") == "APPROVED" and taste_review.get("approval") == "APPROVED"


def interaction_for_next(next_action: dict[str, Any]) -> dict[str, Any]:
    action = next_action.get("action")
    asset = next_action.get("asset")
    if action in {"GENERATE_SCENE", "RECONCILE_GENERATION"} and (str(asset).startswith("S") if asset else action == "RECONCILE_GENERATION"):
        return {
            "userGate": False,
            "promptUser": False,
            "autoContinue": True,
            "continueUntil": "SCENE_BATCH_BOUNDARY",
            "interpretUserMessageAsApproval": False,
        }
    if action == "GENERATE_FOOD" or (action == "RECONCILE_GENERATION" and str(asset).startswith("FOOD")):
        return {
            "userGate": False,
            "promptUser": False,
            "autoContinue": True,
            "continueUntil": "TASTE_BATCH_BOUNDARY",
            "interpretUserMessageAsApproval": False,
        }
    if action in {"BATCH_REVIEW_SCENES", "WAIT_SCENE_BATCH_REVIEW"}:
        return {"userGate": True, "gateType": "SCENE_BATCH", "promptUser": True, "autoContinue": False}
    if action in {"BATCH_REVIEW_TASTE", "WAIT_TASTE_BATCH_REVIEW"}:
        return {"userGate": True, "gateType": "TASTE_BATCH", "promptUser": True, "autoContinue": False}
    if action == "WAIT_HERO_APPROVAL":
        return {"userGate": True, "gateType": "HERO", "promptUser": True, "autoContinue": False}
    if action == "REVIEW_CANONICAL_URL":
        return {"userGate": True, "gateType": "CANONICAL_PAGE", "promptUser": True, "autoContinue": False}
    if action == "HANDOFF_APPROVED_IMAGES_TO_USER":
        return {
            "userGate": False,
            "operationalHandoff": True,
            "promptUser": True,
            "approvalRequested": False,
            "expectedRasterCount": 13,
        }
    return {"userGate": False, "promptUser": False, "autoContinue": True}


def protocol_next(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("productionProtocolId") != PROTOCOL_ID:
        raise ValueError(f"State is not protocol {PROTOCOL_ID}")

    if all_visuals_approved(state):
        handoff = state.get("assetHandoff") if isinstance(state.get("assetHandoff"), dict) else {}
        if handoff.get("state") != "PASS":
            nxt = {"action": "HANDOFF_APPROVED_IMAGES_TO_USER", "asset": "ALL_13_RASTERS"}
            return {"next": nxt, "interaction": interaction_for_next(nxt)}

    nxt = legacy.derive_next(state)
    return {"next": nxt, "interaction": interaction_for_next(nxt)}


def validate_protocol_state(state: dict[str, Any], filename: str) -> list[str]:
    errors: list[str] = []
    if state.get("productionProtocolId") != PROTOCOL_ID:
        return errors

    execution = state.get("executionPolicy") if isinstance(state.get("executionPolicy"), dict) else {}
    expected_execution = protocol_execution_policy()
    for key, expected in expected_execution.items():
        if execution.get(key) != expected:
            errors.append(f"{filename}: executionPolicy.{key} must be {expected!r}")

    previsual = state.get("preVisualBuild") if isinstance(state.get("preVisualBuild"), dict) else {}
    checks = previsual.get("checks") if isinstance(previsual.get("checks"), dict) else {}
    phase = state.get("phase")
    if phase != "CONTENT":
        if previsual.get("state") != "PASS":
            errors.append(f"{filename}: protocol 2 requires preVisualBuild PASS before leaving CONTENT")
        missing = [key for key in PREVISUAL_CHECKS if checks.get(key) != "PASS"]
        if missing:
            errors.append(f"{filename}: preVisualBuild checks not PASS: {', '.join(missing)}")
        map_state = state.get("map") if isinstance(state.get("map"), dict) else {}
        if map_state.get("state") != "APPROVED":
            errors.append(f"{filename}: protocol 2 requires Map APPROVED before Hero generation starts")

    handoff = state.get("assetHandoff") if isinstance(state.get("assetHandoff"), dict) else {}
    if handoff.get("mode") != "USER_HANDOFF":
        errors.append(f"{filename}: assetHandoff.mode must be USER_HANDOFF")
    if handoff.get("expectedRasterCount") != 13:
        errors.append(f"{filename}: assetHandoff.expectedRasterCount must be 13")
    if phase in POST_VISUAL_PHASES:
        if handoff.get("state") != "PASS":
            errors.append(f"{filename}: asset handoff must PASS before phase {phase}")
        if handoff.get("verifiedRasterCount") != 13:
            errors.append(f"{filename}: phase {phase} requires 13 verified raster assets")

    metrics = state.get("productionMetrics") if isinstance(state.get("productionMetrics"), dict) else {}
    per_image_prompts = metrics.get("perImageApprovalPrompts")
    if isinstance(per_image_prompts, int) and per_image_prompts != 0:
        errors.append(f"{filename}: protocol 2 forbids per-image approval prompts; recorded {per_image_prompts}")

    return errors


def validate_all() -> list[str]:
    errors: list[str] = []
    for path in sorted(v7.STATE_DIR.glob("*.json")):
        try:
            state = load_json(path)
        except Exception as exc:
            errors.append(f"{path.name}: cannot read JSON: {exc}")
            continue
        errors.extend(validate_protocol_state(state, path.name))
    return errors


def cmd_init(slug: str) -> int:
    path = legacy.state_path(slug)
    if path.exists():
        print(f"State already exists: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    registry = legacy.registry_map()
    destination = registry.get(slug)
    if destination is None:
        print(f"Unknown destination slug: {slug}", file=sys.stderr)
        return 1
    if destination.get("atlasPublished"):
        print(f"Refusing to initialize already-published slug: {slug}", file=sys.stderr)
        return 1
    state = new_state(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created Country production protocol {PROTOCOL_ID} State: {path.relative_to(ROOT)}")
    return 0


def cmd_next(slug: str) -> int:
    path = legacy.state_path(slug)
    if not path.exists():
        print(f"Missing state: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    state = load_json(path)
    payload = {"slug": slug, "phase": state.get("phase"), **protocol_next(state)}
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def print_errors(errors: list[str]) -> int:
    if not errors:
        print("Country production protocol 2 validation: PASS")
        return 0
    print("Country production protocol 2 validation: FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


def self_test() -> int:
    state = new_state({"slug": "test-slug", "nameEn": "Test Slug"})
    assert state["productionProtocolId"] == PROTOCOL_ID
    assert state["executionPolicy"]["sceneApproval"] == "BATCH_ONLY"
    assert state["executionPolicy"]["userPromptBetweenSceneTargets"] is False
    assert state["assetHandoff"]["mode"] == "USER_HANDOFF"

    state["phase"] = "SCENES_INITIAL"
    state["preVisualBuild"]["state"] = "PASS"
    state["preVisualBuild"]["checks"] = {key: "PASS" for key in PREVISUAL_CHECKS}
    state["map"]["state"] = "APPROVED"
    state["hero"] = {"state": "APPROVED", "asset": "hero.webp", "contentId": "hero", "approvedGenerationId": "hero-g"}
    state["scenes"][0]["contentId"] = "scene-1"
    result = protocol_next(state)
    assert result["next"] == {"action": "GENERATE_SCENE", "asset": "S01"}
    assert result["interaction"]["userGate"] is False
    assert result["interaction"]["continueUntil"] == "SCENE_BATCH_BOUNDARY"
    print("Country production protocol 2 self-test passed")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: country_production_protocol_v2.py init <slug> | next <slug> | validate | self-test", file=sys.stderr)
        return 2
    if args[0] == "init" and len(args) == 2:
        return cmd_init(args[1])
    if args[0] == "next" and len(args) == 2:
        return cmd_next(args[1])
    if args[0] == "validate" and len(args) == 1:
        return print_errors(validate_all())
    if args[0] == "self-test" and len(args) == 1:
        return self_test()
    print("Invalid arguments", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
