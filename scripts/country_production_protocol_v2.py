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
COUNTRY_DIR = ROOT / "data" / "countries"

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
    # Protocol 2 keeps the Country branch authoritative through final page
    # review. The legacy REVIEW phase requires main authority, so the pre-main
    # review gate is represented explicitly here while phase remains QA.
    state["reviewPreview"] = {
        "mode": "TARGETED_COUNTRY_BRANCH_PREVIEW",
        "state": "NOT_STARTED",
        "url": None,
        "browserQa": "NOT_STARTED",
        "deployedAt": None,
    }
    state["productionMetrics"] = {
        "perImageApprovalPrompts": 0,
        "sceneBatchReviews": 0,
        "tasteBatchReviews": 0,
        "assetHandoffs": 0,
        "reviewPackageIntegrations": 0,
        "reviewPreviewDeployments": 0,
        "preCanonicalMainIntegrations": 0,
        "productionIntegrations": 0,
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
    if action in {"OPEN_REVIEW_PR_FOR_TARGETED_PREVIEW", "FINALIZE_REVIEW_PR_FOR_PUBLICATION"}:
        return {"userGate": False, "promptUser": False, "autoContinue": True}
    return {"userGate": False, "promptUser": False, "autoContinue": True}


def protocol_next(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("productionProtocolId") != PROTOCOL_ID:
        raise ValueError(f"State is not protocol {PROTOCOL_ID}")

    if all_visuals_approved(state):
        handoff = state.get("assetHandoff") if isinstance(state.get("assetHandoff"), dict) else {}
        if handoff.get("state") != "PASS":
            nxt = {"action": "HANDOFF_APPROVED_IMAGES_TO_USER", "asset": "ALL_13_RASTERS"}
            return {"next": nxt, "interaction": interaction_for_next(nxt)}

    # Protocol 2 review fast path: open one pre-main review PR after target QA.
    # Opening/synchronizing that PR automatically drives the persistent targeted
    # GitHub Pages preview. The same PR is finalized and serialized for
    # publication after explicit canonical approval; a second PR is forbidden.
    phase = state.get("phase")
    qa = state.get("qa") if isinstance(state.get("qa"), dict) else {}
    preview = state.get("reviewPreview") if isinstance(state.get("reviewPreview"), dict) else None
    final_approval = state.get("finalApproval") if isinstance(state.get("finalApproval"), dict) else {}
    if phase == "QA" and qa.get("state") == "PASS" and preview is not None:
        if preview.get("state") != "DONE" or preview.get("browserQa") != "PASS" or not preview.get("url"):
            nxt = {"action": "OPEN_REVIEW_PR_FOR_TARGETED_PREVIEW", "asset": None}
            return {"next": nxt, "interaction": interaction_for_next(nxt)}
        if final_approval.get("state") != "APPROVED":
            nxt = {"action": "REVIEW_CANONICAL_URL", "asset": None}
            return {"next": nxt, "interaction": interaction_for_next(nxt)}
        nxt = {"action": "FINALIZE_REVIEW_PR_FOR_PUBLICATION", "asset": None}
        return {"next": nxt, "interaction": interaction_for_next(nxt)}

    nxt = legacy.derive_next(state)
    return {"next": nxt, "interaction": interaction_for_next(nxt)}


def generation_id(item: dict[str, Any]) -> str | None:
    for key in ("approvedGenerationId", "candidateGenerationId", "generationId"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def handoff_manifest(slug: str, state: dict[str, Any]) -> dict[str, Any]:
    if not all_visuals_approved(state):
        raise ValueError("All Hero / Scene / Taste assets must be batch-approved before handoff")
    country_path = COUNTRY_DIR / f"{slug}.json"
    if not country_path.exists():
        raise ValueError(f"Missing Country JSON: {country_path.relative_to(ROOT)}")
    country = load_json(country_path)
    country_scenes = country.get("scenes") if isinstance(country.get("scenes"), list) else []
    taste_section = country.get("taste") if isinstance(country.get("taste"), dict) else {}
    country_taste = taste_section.get("items") if isinstance(taste_section.get("items"), list) else []
    state_scenes = state.get("scenes") if isinstance(state.get("scenes"), list) else []
    state_taste = state.get("taste") if isinstance(state.get("taste"), list) else []
    if len(country_scenes) != 8 or len(state_scenes) != 8 or len(country_taste) != 4 or len(state_taste) != 4:
        raise ValueError("Handoff requires exactly Hero + 8 Scenes + 4 Taste items")

    hero = state.get("hero") if isinstance(state.get("hero"), dict) else {}
    hero_path = country.get("hero", {}).get("image") if isinstance(country.get("hero"), dict) else None
    items: list[dict[str, Any]] = [
        {
            "id": "HERO",
            "kind": "HERO",
            "generationId": generation_id(hero),
            "path": hero_path,
        }
    ]
    for state_item, country_item in zip(state_scenes, country_scenes):
        items.append(
            {
                "id": state_item.get("id"),
                "kind": "SCENE",
                "generationId": generation_id(state_item),
                "path": country_item.get("image") if isinstance(country_item, dict) else None,
            }
        )
    for state_item, country_item in zip(state_taste, country_taste):
        items.append(
            {
                "id": state_item.get("id"),
                "kind": "TASTE",
                "generationId": generation_id(state_item),
                "path": country_item.get("image") if isinstance(country_item, dict) else None,
            }
        )

    missing = [item["id"] for item in items if not item.get("generationId") or not item.get("path")]
    if missing:
        raise ValueError(f"Handoff manifest is incomplete for: {', '.join(str(x) for x in missing)}")
    return {
        "slug": slug,
        "mode": "USER_HANDOFF",
        "count": len(items),
        "instruction": "Store each generated raster at its exact path, then report one completion event for batch verification.",
        "items": items,
    }


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

    preview = state.get("reviewPreview")
    if preview is not None:
        if not isinstance(preview, dict):
            errors.append(f"{filename}: reviewPreview must be an object when present")
        else:
            if preview.get("mode") != "TARGETED_COUNTRY_BRANCH_PREVIEW":
                errors.append(f"{filename}: reviewPreview.mode must be TARGETED_COUNTRY_BRANCH_PREVIEW")
            if preview.get("state") not in {"NOT_STARTED", "DONE"}:
                errors.append(f"{filename}: reviewPreview.state must be NOT_STARTED or DONE")
            if preview.get("browserQa") not in {"NOT_STARTED", "PASS", "FAIL"}:
                errors.append(f"{filename}: reviewPreview.browserQa must be NOT_STARTED, PASS or FAIL")
            if preview.get("state") == "DONE":
                url = preview.get("url")
                if not isinstance(url, str) or not url.startswith("https://") or "/countries/" not in url:
                    errors.append(f"{filename}: completed reviewPreview requires an https Country review URL")
                if preview.get("browserQa") != "PASS":
                    errors.append(f"{filename}: completed reviewPreview requires browserQa PASS")

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


def cmd_handoff(slug: str) -> int:
    path = legacy.state_path(slug)
    if not path.exists():
        print(f"Missing state: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    state = load_json(path)
    try:
        manifest = handoff_manifest(slug, state)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
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
    assert state["reviewPreview"]["mode"] == "TARGETED_COUNTRY_BRANCH_PREVIEW"

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

    state["phase"] = "QA"
    state["qa"]["state"] = "PASS"
    state["assetHandoff"] = {
        "mode": "USER_HANDOFF",
        "state": "PASS",
        "expectedRasterCount": 13,
        "verifiedRasterCount": 13,
        "verifiedAt": "2026-09-11T00:00:00+09:00",
    }
    state["hero"]["state"] = "APPROVED"
    for index, item in enumerate(state["scenes"], start=1):
        item["state"] = "APPROVED"
        item["approvedGenerationId"] = f"scene-g-{index}"
    for index, item in enumerate(state["taste"], start=1):
        item["state"] = "APPROVED"
        item["approvedGenerationId"] = f"food-g-{index}"
    state["sceneBatchReview"] = {"approval": "APPROVED", "rounds": []}
    state["tasteBatchReview"] = {"approval": "APPROVED", "rounds": []}
    result = protocol_next(state)
    assert result["next"] == {"action": "OPEN_REVIEW_PR_FOR_TARGETED_PREVIEW", "asset": None}
    assert result["interaction"]["userGate"] is False
    state["reviewPreview"] = {
        "mode": "TARGETED_COUNTRY_BRANCH_PREVIEW",
        "state": "DONE",
        "url": "https://example.test/reviews/test-slug/countries/test-slug/",
        "browserQa": "PASS",
        "deployedAt": "2026-09-11T00:00:00+09:00",
    }
    result = protocol_next(state)
    assert result["next"] == {"action": "REVIEW_CANONICAL_URL", "asset": None}
    assert result["interaction"]["userGate"] is True
    state["finalApproval"]["state"] = "APPROVED"
    result = protocol_next(state)
    assert result["next"] == {"action": "FINALIZE_REVIEW_PR_FOR_PUBLICATION", "asset": None}
    assert result["interaction"]["userGate"] is False

    print("Country production protocol 2 self-test passed")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: country_production_protocol_v2.py init <slug> | next <slug> | handoff <slug> | validate | self-test", file=sys.stderr)
        return 2
    if args[0] == "init" and len(args) == 2:
        return cmd_init(args[1])
    if args[0] == "next" and len(args) == 2:
        return cmd_next(args[1])
    if args[0] == "handoff" and len(args) == 2:
        return cmd_handoff(args[1])
    if args[0] == "validate" and len(args) == 1:
        return print_errors(validate_all())
    if args[0] == "self-test" and len(args) == 1:
        return self_test()
    print("Invalid arguments", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
