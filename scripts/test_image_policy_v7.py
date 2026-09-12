#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("v7", HERE / "country_production_state_v7.py")
assert SPEC and SPEC.loader
v7 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v7)

SPEC72 = importlib.util.spec_from_file_location("v72", HERE / "image_policy_v72.py")
assert SPEC72 and SPEC72.loader
v72 = importlib.util.module_from_spec(SPEC72)
SPEC72.loader.exec_module(v72)
v72.install_legacy_patch(v7.legacy)


def scene(asset_id: str, state: str, generation_id: str | None = None) -> dict:
    item = {
        "id": asset_id,
        "state": state,
        "asset": None,
        "contentId": f"content-{asset_id.lower()}",
    }
    if generation_id:
        if state == "APPROVED":
            item["approvedGenerationId"] = generation_id
        else:
            item["candidateGenerationId"] = generation_id
    return item


def taste_packet(content_id: str, identity: str, accompaniments: list[str] | None = None, serving: list[str] | None = None) -> dict:
    return {
        "kind": "TASTE",
        "contentId": content_id,
        "identity": identity,
        "independentGeneration": True,
        "forbidPreviousAssetReuse": True,
        "noAddedText": True,
        "singleDishOnly": True,
        "cleanNeutralBackground": True,
        "singleFrameOnly": True,
        "forbidCollage": True,
        "forbidPanels": True,
        "forbidGrid": True,
        "forbidContactSheet": True,
        "forbidMontage": True,
        "forbidInsetImages": True,
        "integralAccompanimentsOnly": True,
        "decorativePropsForbidden": True,
        "plainBackgroundRequired": True,
        "backgroundStyle": v72.BACKGROUND_STYLE,
        "integralAccompaniments": list(accompaniments or []),
        "integralServingElements": list(serving or []),
        "decorativeProps": [],
    }


def taste_qa() -> dict:
    return {key: "PASS" for key in v72.TASTE_QA_REQUIRED}


def taste_state() -> dict:
    state = v7.new_state({"slug": "test-slug", "nameEn": "Test Slug"})
    state["phase"] = "TASTE_INITIAL"
    state["hero"] = {
        "state": "APPROVED",
        "asset": "hero.webp",
        "contentId": "hero",
        "approvedGenerationId": "hero-g",
    }
    state["scenes"] = [scene(asset_id, "APPROVED", f"sg{i}") for i, asset_id in enumerate(v7.SCENE_IDS, 1)]
    state["sceneBatchReview"] = {
        "approval": "APPROVED",
        "rounds": [round_entry(1, list(v7.SCENE_IDS), {asset_id: f"sg{i}" for i, asset_id in enumerate(v7.SCENE_IDS, 1)}, [])],
    }
    for i, item in enumerate(state["taste"], 1):
        content_id = f"dish-{i}"
        item["contentId"] = content_id
        item["promptSeries"] = 1
        item["promptSeriesRejectCount"] = 0
        item["rejectedGenerationIds"] = []
        item["renderPacket"] = taste_packet(content_id, f"One serving of dish {i} only")
    state["next"] = v7.legacy.derive_next(state)
    return state


def base_state() -> dict:
    state = v7.new_state({"slug": "test-slug", "nameEn": "Test Slug"})
    state["phase"] = "SCENES_INITIAL"
    state["hero"] = {
        "state": "APPROVED",
        "asset": "hero.webp",
        "contentId": "hero",
        "approvedGenerationId": "hero-g",
    }
    state["scenes"] = [scene(asset_id, "REVIEW_CANDIDATE", f"g{i}") for i, asset_id in enumerate(v7.SCENE_IDS, 1)]
    state["next"] = v7.legacy.derive_next(state)
    assert state["next"] == {"action": "BATCH_REVIEW_SCENES", "asset": None}
    return state


def round_entry(round_number: int, scope: list[str], approved: dict[str, str], regenerate: list[str]) -> dict:
    return {
        "round": round_number,
        "reviewBoundary": True,
        "scope": scope,
        "approvedGenerations": approved,
        "regenerate": regenerate,
        "approvedAt": f"2026-09-10T15:{round_number:02d}:00+09:00",
    }


def reservation(asset_id: str, epoch: int = 1) -> dict:
    return {
        "reservationId": f"{asset_id}-series1-attempt1",
        "asset": asset_id,
        "contentId": f"content-{asset_id.lower()}",
        "promptSeries": 1,
        "generationContextEpoch": epoch,
        "reservedAt": "2026-09-10T15:30:00+09:00",
    }


def test_initial_batch_good() -> None:
    before = base_state()
    after = copy.deepcopy(before)
    after["phase"] = "SCENES_REGEN"
    after["scenes"][0]["state"] = "APPROVED"
    after["scenes"][0]["approvedGenerationId"] = after["scenes"][0].pop("candidateGenerationId")
    for item in after["scenes"][1:]:
        item["state"] = "REGENERATE"
    after["sceneBatchReview"]["rounds"].append(
        round_entry(1, list(v7.SCENE_IDS), {"S01": "g1"}, list(v7.SCENE_IDS[1:]))
    )
    after["next"] = v7.legacy.derive_next(after)
    errors = v7.validate_transition(before, after, "ops/country-production/test-slug.json")
    assert not errors, errors


def test_individual_approval_without_batch_fails() -> dict:
    before = base_state()
    bad = copy.deepcopy(before)
    bad["phase"] = "SCENES_REGEN"
    bad["scenes"][0]["state"] = "APPROVED"
    bad["scenes"][0]["approvedGenerationId"] = bad["scenes"][0].pop("candidateGenerationId")
    for item in bad["scenes"][1:]:
        item["state"] = "REGENERATE"
    bad["next"] = v7.legacy.derive_next(bad)
    errors = v7.validate_transition(before, bad, "ops/country-production/test-slug.json")
    assert any("without a new batch-review ledger round" in error or "not covered by immutable batch ledger" in error for error in errors), errors
    return bad


def test_late_batch_backfill_fails() -> None:
    bad = test_individual_approval_without_batch_fails()
    late = copy.deepcopy(bad)
    late["sceneBatchReview"]["rounds"].append(
        round_entry(1, list(v7.SCENE_IDS), {"S01": "g1"}, list(v7.SCENE_IDS[1:]))
    )
    late["next"] = v7.legacy.derive_next(late)
    errors = v7.validate_transition(bad, late, "ops/country-production/test-slug.json")
    assert any("true batch boundary" in error for error in errors), errors


def test_regen_individual_approval_fails_and_batch_passes() -> None:
    before = v7.new_state({"slug": "test-slug", "nameEn": "Test Slug"})
    before["phase"] = "SCENES_REGEN"
    before["hero"] = {"state": "APPROVED", "asset": "hero.webp", "contentId": "hero", "approvedGenerationId": "hero-g"}
    before["scenes"] = []
    approved_map = {}
    for i, asset_id in enumerate(v7.SCENE_IDS, 1):
        if asset_id == "S08":
            before["scenes"].append(scene(asset_id, "REVIEW_CANDIDATE", "g8-new"))
        else:
            gid = f"g{i}"
            before["scenes"].append(scene(asset_id, "APPROVED", gid))
            approved_map[asset_id] = gid
    before["sceneBatchReview"] = {
        "approval": "PENDING",
        "rounds": [round_entry(1, list(v7.SCENE_IDS), approved_map, ["S08"])],
    }
    before["next"] = v7.legacy.derive_next(before)
    assert before["next"] == {"action": "BATCH_REVIEW_SCENES", "asset": None}

    bad = copy.deepcopy(before)
    bad["scenes"][-1]["state"] = "APPROVED"
    bad["scenes"][-1]["approvedGenerationId"] = bad["scenes"][-1].pop("candidateGenerationId")
    bad["next"] = v7.legacy.derive_next(bad)
    errors = v7.validate_transition(before, bad, "ops/country-production/test-slug.json")
    assert errors, "REGEN individual approval unexpectedly passed"

    good = copy.deepcopy(before)
    good["scenes"][-1]["state"] = "APPROVED"
    good["scenes"][-1]["approvedGenerationId"] = good["scenes"][-1].pop("candidateGenerationId")
    good["sceneBatchReview"]["rounds"].append(round_entry(2, ["S08"], {"S08": "g8-new"}, []))
    good["sceneBatchReview"]["approval"] = "APPROVED"
    good["next"] = v7.legacy.derive_next(good)
    errors = v7.validate_transition(before, good, "ops/country-production/test-slug.json")
    assert not errors, errors


def test_per_item_user_approval_field_fails() -> None:
    state = base_state()
    state["scenes"][0]["userApprovedAt"] = "2026-09-10T15:00:00+09:00"
    errors = v7.validate_state_dict(state, "test-slug.json")
    assert any("forbids per-item userApprovedAt" in error for error in errors), errors


def test_atomic_reconcile_and_reserve_next_passes() -> None:
    before = v7.new_state({"slug": "test-slug", "nameEn": "Test Slug"})
    before["phase"] = "SCENES_INITIAL"
    before["hero"] = {
        "state": "APPROVED",
        "asset": "hero.webp",
        "contentId": "hero",
        "approvedGenerationId": "hero-g",
    }
    for i, item in enumerate(before["scenes"], 1):
        item["contentId"] = f"content-s{i:02d}"
    before["scenes"][0]["state"] = "GENERATING"
    before["scenes"][0]["generationReservation"] = reservation("S01")
    before["next"] = v7.legacy.derive_next(before)
    assert before["next"] == {"action": "RECONCILE_GENERATION", "asset": "S01"}

    after = copy.deepcopy(before)
    current = after["scenes"][0]
    current["state"] = "REVIEW_CANDIDATE"
    current["candidateGenerationId"] = "g-s01"
    current["candidateVisualQa"] = {
        "targetIdentity": "PASS",
        "previousAssetRepeat": "PASS",
        "collageTypography": "PASS",
    }
    current.pop("generationReservation", None)

    nxt = after["scenes"][1]
    nxt["state"] = "GENERATING"
    nxt["generationReservation"] = reservation("S02")
    after["next"] = v7.legacy.derive_next(after)
    assert after["next"] == {"action": "RECONCILE_GENERATION", "asset": "S02"}

    errors = v7.validate_transition(before, after, "ops/country-production/test-slug.json")
    assert not errors, errors


def test_multiple_unreconciled_targets_still_fail() -> None:
    state = v7.new_state({"slug": "test-slug", "nameEn": "Test Slug"})
    state["phase"] = "SCENES_INITIAL"
    state["hero"] = {
        "state": "APPROVED",
        "asset": "hero.webp",
        "contentId": "hero",
        "approvedGenerationId": "hero-g",
    }
    for i, item in enumerate(state["scenes"], 1):
        item["contentId"] = f"content-s{i:02d}"
    state["scenes"][0]["state"] = "GENERATING"
    state["scenes"][0]["generationReservation"] = reservation("S01")
    state["scenes"][1]["state"] = "GENERATING"
    state["scenes"][1]["generationReservation"] = reservation("S02")
    state["next"] = v7.legacy.derive_next(state)
    errors = v7.validate_state_dict(state, "test-slug.json")
    assert any("only one unreconciled GENERATING target" in error for error in errors), errors


def test_central_policy_7_2_contract() -> None:
    policy = v7.load_json(v7.POLICY_PATH)
    assert policy["revision"] == 7
    assert policy["patch"] == 2
    assert policy["policyId"] == "7.2"
    assert policy["throughputGuide"] == "docs/IMAGE_POLICY_REVISION_7_2.md"
    throughput = policy["throughputOptimization"]
    assert throughput["sameTurnAuthoritativeStateCache"] is True
    assert throughput["rereadAfterOwnSuccessfulWrite"] is False
    assert throughput["atomicReconcileAndReserveNext"] is True
    assert throughput["renderPacketsValidatedAtRoundStart"] is True
    assert throughput["contentPlanRereadPerTarget"] is False
    assert throughput["waitForCountryBranchCiBetweenImages"] is False
    assert throughput["countryBranchCiMode"] == "TRANSITION_ONLY"
    assert policy["roundExecution"]["initialTasteRoundMustAttemptEveryTargetBeforeRetry"] is True
    assert policy["novelty"]["repeatFailureRequiresImmediateRenderPacketRefresh"] is True
    assert policy["tasteComposition"]["integralAccompanimentsAllowed"] is True
    assert policy["tasteComposition"]["decorativePropsForbidden"] is True


def test_integral_accompaniment_is_allowed_but_decoration_is_not() -> None:
    state = taste_state()
    item = state["taste"][0]
    item["renderPacket"] = taste_packet(
        item["contentId"],
        "One serving of Brunei ambuyat with its integral cacah dipping sauce",
        accompaniments=["cacah dipping sauce"],
        serving=["small sauce ramekin required for cacah"],
    )
    errors = v72.validate_state_dict(state, "brunei.json")
    assert not errors, errors

    bad = copy.deepcopy(state)
    bad["taste"][0]["renderPacket"]["decorativeProps"] = ["flower", "napkin"]
    errors = v72.validate_state_dict(bad, "brunei.json")
    assert any("decorativeProps must be []" in error for error in errors), errors


def test_taste_candidate_requires_v72_visual_qa() -> None:
    state = taste_state()
    item = state["taste"][0]
    item["state"] = "REVIEW_CANDIDATE"
    item["candidateGenerationId"] = "food-g-1"
    item["candidateVisualQa"] = {
        "targetIdentity": "PASS",
        "previousAssetRepeat": "PASS",
        "collageTypography": "PASS",
    }
    errors = v72.validate_state_dict(state, "test-slug.json")
    assert any("dishIdentity" in error for error in errors), errors
    assert any("plainBackground" in error for error in errors), errors
    assert any("decorativePropsAbsent" in error for error in errors), errors

    item["candidateVisualQa"] = taste_qa()
    errors = v72.validate_state_dict(state, "test-slug.json")
    assert not errors, errors


def test_initial_taste_failure_does_not_retry_before_first_pass_finishes() -> None:
    state = taste_state()
    first = state["taste"][0]
    first["state"] = "REGENERATE"
    first["rejectedGenerationIds"] = ["bad-food-1"]
    first["lastFailureReason"] = "BACKGROUND_PROPS"
    state["next"] = v7.legacy.derive_next(state)
    assert state["next"] == {"action": "GENERATE_FOOD", "asset": "FOOD02"}, state["next"]


def test_vietnam_style_early_taste_regen_transition_fails() -> None:
    before = taste_state()
    for index, item in enumerate(before["taste"], start=1):
        if index == 2:
            item["state"] = "REGENERATE"
            item["rejectedGenerationIds"] = ["bad-food-2"]
            item["lastFailureReason"] = "BACKGROUND_PROPS"
        else:
            item["state"] = "REVIEW_CANDIDATE"
            item["candidateGenerationId"] = f"food-g-{index}"
            item["candidateVisualQa"] = taste_qa()
    before["next"] = v7.legacy.derive_next(before)
    assert before["next"] == {"action": "BATCH_REVIEW_TASTE", "asset": None}

    bad = copy.deepcopy(before)
    bad["phase"] = "TASTE_REGEN"
    bad["next"] = v7.legacy.derive_next(bad)
    errors = v72.validate_transition(before, bad, "ops/country-production/vietnam.json")
    assert any("before appending the initial Taste batch-review round" in error for error in errors), errors


def test_repeat_or_wrong_target_requires_immediate_prompt_refresh() -> None:
    state = taste_state()
    state["phase"] = "TASTE_REGEN"
    approved = {}
    for index, item in enumerate(state["taste"], start=1):
        if index == 1:
            item["state"] = "REGENERATE"
            item["promptSeriesRejectCount"] = 1
            item["rejectedGenerationIds"] = ["repeat-g"]
            item["lastFailureReason"] = "PREVIOUS_ASSET_REPEAT"
        else:
            item["state"] = "APPROVED"
            item["approvedGenerationId"] = f"food-g-{index}"
            approved[item["id"]] = item["approvedGenerationId"]
    state["tasteBatchReview"] = {
        "approval": "PENDING",
        "rounds": [round_entry(1, list(v7.FOOD_IDS), approved, ["FOOD01"])],
    }
    state["next"] = v7.legacy.derive_next(state)
    assert state["next"] == {"action": "REFRESH_RENDER_PACKET", "asset": "FOOD01"}, state["next"]


def test_same_prompt_series_retry_after_repeat_fails() -> None:
    before = taste_state()
    before["phase"] = "TASTE_REGEN"
    first = before["taste"][0]
    first["state"] = "REGENERATE"
    first["promptSeriesRejectCount"] = 1
    first["rejectedGenerationIds"] = ["repeat-g"]
    first["lastFailureReason"] = "WRONG_TARGET_CARRYOVER"
    approved = {}
    for index, item in enumerate(before["taste"][1:], start=2):
        item["state"] = "APPROVED"
        item["approvedGenerationId"] = f"food-g-{index}"
        approved[item["id"]] = item["approvedGenerationId"]
    before["tasteBatchReview"] = {
        "approval": "PENDING",
        "rounds": [round_entry(1, list(v7.FOOD_IDS), approved, ["FOOD01"])],
    }
    before["next"] = v7.legacy.derive_next(before)

    bad = copy.deepcopy(before)
    bad_first = bad["taste"][0]
    bad_first["state"] = "GENERATING"
    bad_first["generationReservation"] = {
        "reservationId": "FOOD01-series1-attempt2",
        "asset": "FOOD01",
        "contentId": bad_first["contentId"],
        "promptSeries": 1,
        "generationContextEpoch": 1,
        "reservedAt": "2026-09-12T00:20:00+09:00",
    }
    bad["next"] = {"action": "RECONCILE_GENERATION", "asset": "FOOD01"}
    errors = v72.validate_transition(before, bad, "ops/country-production/thailand.json")
    assert any("requires Render Packet refresh and promptSeries increment" in error for error in errors), errors


if __name__ == "__main__":
    test_initial_batch_good()
    test_individual_approval_without_batch_fails()
    test_late_batch_backfill_fails()
    test_regen_individual_approval_fails_and_batch_passes()
    test_per_item_user_approval_field_fails()
    test_atomic_reconcile_and_reserve_next_passes()
    test_multiple_unreconciled_targets_still_fail()
    test_central_policy_7_2_contract()
    test_integral_accompaniment_is_allowed_but_decoration_is_not()
    test_taste_candidate_requires_v72_visual_qa()
    test_initial_taste_failure_does_not_retry_before_first_pass_finishes()
    test_vietnam_style_early_taste_regen_transition_fails()
    test_repeat_or_wrong_target_requires_immediate_prompt_refresh()
    test_same_prompt_series_retry_after_repeat_fails()
    print("Revision 7.2 batch, Taste composition and retry regression tests passed")
