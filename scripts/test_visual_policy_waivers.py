#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("waiver", HERE / "validate_visual_policy_waivers.py")
assert SPEC and SPEC.loader
waiver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(waiver)


def base_state() -> dict:
    generation = "scene-generation-1"
    return {
        "hero": {"state": "APPROVED", "approvedGenerationId": "hero-generation"},
        "scenes": [{"id": "S01", "state": "APPROVED", "approvedGenerationId": generation}],
        "taste": [],
        "sceneBatchReview": {"approval": "APPROVED", "rounds": [{
            "round": 1, "reviewBoundary": True, "scope": ["S01"],
            "approvedGenerations": {"S01": generation}, "regenerate": [],
            "approvedAt": "2026-09-16T11:34:00+09:00",
        }]},
        "recoveryMigrations": [{
            "id": "test-scene-recovery", "type": "USER_APPROVED_EXISTING_BATCH_RECOVERY",
            "kind": "SCENE", "reasonCode": "ORCHESTRATION_STATE_DESYNC_WITH_POLICY_WAIVER",
            "scope": ["S01"], "recoveredGenerations": {"S01": generation},
            "authorizedBy": "USER_EXPLICIT", "authorizedAt": "2026-09-16T11:34:00+09:00",
            "preserveExistingImages": True, "status": "APPLIED",
        }],
        "visualPolicyWaivers": [{
            "id": "test-scene-waiver", "type": "USER_APPROVED_VISUAL_POLICY_WAIVER",
            "violationCode": "PREVIOUS_IMAGE_REFERENCE_USED", "kind": "SCENE",
            "scope": ["S01"], "generations": {"S01": generation},
            "authorizedBy": "USER_EXPLICIT", "authorizedAt": "2026-09-16T11:34:00+09:00",
            "userInstruction": "Keep the already approved scene; do not regenerate it.",
            "preserveExistingImages": True, "regenerationRequired": False,
            "hardVisualQa": {"targetIdentity": "PASS", "previousAssetRepeat": "PASS", "collageTypography": "PASS"},
            "stateDesynchronized": True, "recoveryMigrationId": "test-scene-recovery",
            "status": "APPLIED",
        }],
    }


def test_good_applied_waiver() -> None:
    errors = waiver.validate_state_dict(base_state(), "test.json")
    assert not errors, errors


def test_hard_visual_failure_is_rejected() -> None:
    state = base_state()
    state["visualPolicyWaivers"][0]["hardVisualQa"]["targetIdentity"] = "FAIL"
    errors = waiver.validate_state_dict(state, "test.json")
    assert any("targetIdentity must be PASS" in error for error in errors), errors


def test_unknown_violation_is_rejected() -> None:
    state = base_state()
    state["visualPolicyWaivers"][0]["violationCode"] = "COLLAGE_OR_MULTIPANEL"
    errors = waiver.validate_state_dict(state, "test.json")
    assert any("violationCode" in error for error in errors), errors


def test_applied_generation_must_be_in_batch_ledger() -> None:
    state = base_state()
    state["sceneBatchReview"]["rounds"][0]["approvedGenerations"] = {}
    errors = waiver.validate_state_dict(state, "test.json")
    assert any("normal batch ledger" in error for error in errors), errors


def test_staged_candidate_contract() -> None:
    state = base_state()
    state["scenes"][0] = {"id": "S01", "state": "REVIEW_CANDIDATE", "candidateGenerationId": "scene-generation-1"}
    state["sceneBatchReview"] = {"approval": "PENDING", "rounds": []}
    state["recoveryMigrations"][0]["status"] = "STAGED"
    state["visualPolicyWaivers"][0]["status"] = "STAGED"
    errors = waiver.validate_state_dict(state, "test.json")
    assert not errors, errors


def historical_taste_state() -> dict:
    case = waiver.policy()["closedHistoricalCases"]["elsalvador-taste-four-20260916"]
    generations = dict(case["generations"])
    scope = list(case["scope"])
    return {
        "slug": "elsalvador",
        "taste": [{"id": target, "state": "REVIEW_CANDIDATE", "candidateGenerationId": generations[target]} for target in scope],
        "tasteBatchReview": {"approval": "PENDING", "rounds": []},
        "recoveryMigrations": [{
            "id": "elsalvador-taste-recovery", "type": "USER_APPROVED_EXISTING_BATCH_RECOVERY",
            "kind": "TASTE", "scope": scope, "recoveredGenerations": generations,
            "authorizedBy": "USER_EXPLICIT", "status": "STAGED",
        }],
        "visualPolicyWaivers": [{
            "id": "elsalvador-taste-waiver", "type": "USER_APPROVED_VISUAL_POLICY_WAIVER",
            "closedHistoricalCaseId": "elsalvador-taste-four-20260916",
            "violationCode": "MULTIPLE_OUTPUTS_ONE_REQUEST", "kind": "TASTE",
            "scope": scope, "generations": generations,
            "authorizedBy": "USER_EXPLICIT", "authorizedAt": "2026-09-16T17:00:00+09:00",
            "userInstruction": "採用", "preserveExistingImages": True, "regenerationRequired": False,
            "hardVisualQa": {"targetIdentity": "PASS", "previousAssetRepeat": "PASS", "collageTypography": "PASS"},
            "stateDesynchronized": True, "recoveryMigrationId": "elsalvador-taste-recovery", "status": "STAGED",
        }],
    }


def test_closed_historical_taste_waiver() -> None:
    state = historical_taste_state()
    assert not waiver.validate_state_dict(state, "test.json")
    state["slug"] = "another-country"
    assert any("exact country" in e for e in waiver.validate_state_dict(state, "test.json"))
    state = historical_taste_state()
    state["visualPolicyWaivers"][0]["generations"]["FOOD04"] = "another-generation"
    assert any("exact country" in e for e in waiver.validate_state_dict(state, "test.json"))
    state = historical_taste_state()
    state["visualPolicyWaivers"][0]["closedHistoricalCaseId"] = "nonexistent"
    assert any("closedHistoricalCaseId" in e for e in waiver.validate_state_dict(state, "test.json"))


def antigua_closed_state(case_id: str) -> dict:
    case = waiver.policy()["closedHistoricalCases"][case_id]
    kind = case["kind"]
    scope = list(case["scope"])
    generations = dict(case["generations"])
    collection = "scenes" if kind == "SCENE" else "taste"
    review = "sceneBatchReview" if kind == "SCENE" else "tasteBatchReview"
    migration_id = case_id + "-recovery"
    return {
        "slug": case["slug"],
        collection: [{"id": target, "state": "REVIEW_CANDIDATE", "candidateGenerationId": generations[target]} for target in scope],
        review: {"approval": "PENDING", "rounds": []},
        "recoveryMigrations": [{"id": migration_id, "type": "USER_APPROVED_EXISTING_BATCH_RECOVERY",
                                "kind": kind, "scope": scope, "recoveredGenerations": generations, "status": "STAGED"}],
        "visualPolicyWaivers": [{
            "id": case_id + "-waiver", "type": "USER_APPROVED_VISUAL_POLICY_WAIVER",
            "closedHistoricalCaseId": case_id, "violationCode": "MULTIPLE_OUTPUTS_ONE_REQUEST",
            "kind": kind, "scope": scope, "generations": generations,
            "authorizedBy": "USER_EXPLICIT", "authorizedAt": "2026-09-16T19:42:00+09:00",
            "userInstruction": "承認します。", "preserveExistingImages": True, "regenerationRequired": False,
            "hardVisualQa": {"targetIdentity": "PASS", "previousAssetRepeat": "PASS", "collageTypography": "PASS"},
            "stateDesynchronized": True, "recoveryMigrationId": migration_id, "status": "STAGED",
        }],
    }


def test_antigua_closed_cases_require_exact_country_target_and_generation() -> None:
    for case_id in ("antiguabarbuda-scenes-eight-20260916", "antiguabarbuda-taste-four-20260916"):
        state = antigua_closed_state(case_id)
        assert not waiver.validate_state_dict(state, "test.json")
        state["slug"] = "different-country"
        assert any("exact country" in e for e in waiver.validate_state_dict(state, "test.json"))
        state = antigua_closed_state(case_id)
        state["visualPolicyWaivers"][0]["generations"][state["visualPolicyWaivers"][0]["scope"][0]] = "wrong-generation"
        assert any("exact country" in e for e in waiver.validate_state_dict(state, "test.json"))
        state = antigua_closed_state(case_id)
        state["visualPolicyWaivers"][0]["hardVisualQa"]["collageTypography"] = "FAIL"
        assert any("collageTypography must be PASS" in e for e in waiver.validate_state_dict(state, "test.json"))


def main() -> int:
    test_good_applied_waiver()
    test_hard_visual_failure_is_rejected()
    test_unknown_violation_is_rejected()
    test_applied_generation_must_be_in_batch_ledger()
    test_staged_candidate_contract()
    test_closed_historical_taste_waiver()
    test_antigua_closed_cases_require_exact_country_target_and_generation()
    print("Visual policy waiver tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
