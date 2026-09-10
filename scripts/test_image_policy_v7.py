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


if __name__ == "__main__":
    test_initial_batch_good()
    test_individual_approval_without_batch_fails()
    test_late_batch_backfill_fails()
    test_regen_individual_approval_fails_and_batch_passes()
    test_per_item_user_approval_field_fails()
    print("Revision 7 batch-approval regression tests passed")
