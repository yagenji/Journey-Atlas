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
        "scenes": [
            {"id": "S01", "state": "APPROVED", "approvedGenerationId": generation},
        ],
        "taste": [],
        "sceneBatchReview": {
            "approval": "APPROVED",
            "rounds": [
                {
                    "round": 1,
                    "reviewBoundary": True,
                    "scope": ["S01"],
                    "approvedGenerations": {"S01": generation},
                    "regenerate": [],
                    "approvedAt": "2026-09-16T11:34:00+09:00",
                }
            ],
        },
        "recoveryMigrations": [
            {
                "id": "test-scene-recovery",
                "type": "USER_APPROVED_EXISTING_BATCH_RECOVERY",
                "kind": "SCENE",
                "reasonCode": "ORCHESTRATION_STATE_DESYNC_WITH_POLICY_WAIVER",
                "scope": ["S01"],
                "recoveredGenerations": {"S01": generation},
                "authorizedBy": "USER_EXPLICIT",
                "authorizedAt": "2026-09-16T11:34:00+09:00",
                "preserveExistingImages": True,
                "status": "APPLIED",
            }
        ],
        "visualPolicyWaivers": [
            {
                "id": "test-scene-waiver",
                "type": "USER_APPROVED_VISUAL_POLICY_WAIVER",
                "violationCode": "PREVIOUS_IMAGE_REFERENCE_USED",
                "kind": "SCENE",
                "scope": ["S01"],
                "generations": {"S01": generation},
                "authorizedBy": "USER_EXPLICIT",
                "authorizedAt": "2026-09-16T11:34:00+09:00",
                "userInstruction": "Keep the already approved scene; do not regenerate it.",
                "preserveExistingImages": True,
                "regenerationRequired": False,
                "hardVisualQa": {
                    "targetIdentity": "PASS",
                    "previousAssetRepeat": "PASS",
                    "collageTypography": "PASS",
                },
                "stateDesynchronized": True,
                "recoveryMigrationId": "test-scene-recovery",
                "status": "APPLIED",
            }
        ],
    }


def test_good_applied_waiver() -> None:
    state = base_state()
    errors = waiver.validate_state_dict(state, "test.json")
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
    generation = "scene-generation-1"
    state["scenes"][0] = {"id": "S01", "state": "REVIEW_CANDIDATE", "candidateGenerationId": generation}
    state["sceneBatchReview"] = {"approval": "PENDING", "rounds": []}
    state["recoveryMigrations"][0]["status"] = "STAGED"
    state["visualPolicyWaivers"][0]["status"] = "STAGED"
    errors = waiver.validate_state_dict(state, "test.json")
    assert not errors, errors


def main() -> int:
    test_good_applied_waiver()
    test_hard_visual_failure_is_rejected()
    test_unknown_violation_is_rejected()
    test_applied_generation_must_be_in_batch_ledger()
    test_staged_candidate_contract()
    print("Visual policy waiver tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
