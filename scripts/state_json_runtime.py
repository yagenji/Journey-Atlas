#!/usr/bin/env python3
"""Stable runtime guard for Revision 7 immutable batch-ledger validation.

The guard preserves the Revision 7 ledger contract while avoiding hashed/string
membership for asset and Generation IDs. Exact text identity is checked with
hmac.compare_digest over UTF-8 bytes. No Country, asset, or Generation ID is
special-cased, and genuine ledger omissions remain blocking errors.
"""

from __future__ import annotations

import hmac
import json
from typing import Any, Iterable


def _text_equal(left: Any, right: Any) -> bool:
    if not isinstance(left, str) or not isinstance(right, str):
        return False
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def _contains_text(values: Iterable[Any], target: str) -> bool:
    return any(_text_equal(value, target) for value in values)


def _unique_text_list(values: list[Any]) -> bool:
    for index, value in enumerate(values):
        if not isinstance(value, str):
            return False
        if any(_text_equal(value, later) for later in values[index + 1 :]):
            return False
    return True


def _same_text_members(left: list[Any], right: list[Any]) -> bool:
    if len(left) != len(right):
        return False
    if not _unique_text_list(left) or not _unique_text_list(right):
        return False
    return all(_contains_text(right, value) for value in left if isinstance(value, str))


def _find_item(items: list[dict[str, Any]], asset_id: str) -> dict[str, Any]:
    for item in items:
        if isinstance(item, dict) and _text_equal(item.get("id"), asset_id):
            return item
    return {}


def _generation_covered(rounds: list[Any], asset_id: str, generation_id: str) -> bool:
    for entry in rounds:
        if not isinstance(entry, dict):
            continue
        approved = entry.get("approvedGenerations")
        if not isinstance(approved, dict):
            continue
        for approved_asset_id, approved_generation_id in approved.items():
            if _text_equal(approved_asset_id, asset_id) and _text_equal(
                approved_generation_id, generation_id
            ):
                return True
    return False


def stable_text_fingerprint(value: Any) -> int | None:
    """Compatibility helper retained for existing callers."""
    if not isinstance(value, str):
        return None
    encoded = value.encode("utf-8")
    return int(encoded.hex(), 16) if encoded else 0


def same_text_fingerprint(left: Any, right: Any) -> bool:
    return _text_equal(left, right)


def canonicalize_json_strings(value: Any) -> Any:
    return value


_original_loads = json.loads


def canonical_loads(payload: str | bytes | bytearray, *args: Any, **kwargs: Any) -> Any:
    return _original_loads(payload, *args, **kwargs)


def install_json_loads_guard() -> None:
    """Compatibility no-op kept for older callers."""
    if json.loads is not canonical_loads:
        json.loads = canonical_loads


def install_v7_ledger_guard(v7_module: Any) -> None:
    """Install a semantically equivalent, digest-safe Revision 7 ledger validator."""
    original = getattr(v7_module, "validate_ledger", None)
    if original is None or getattr(original, "_journey_atlas_digest_guarded", False):
        return

    def guarded_validate_ledger(
        errors: list[str],
        filename: str,
        state: dict[str, Any],
        kind: str,
        ids: list[str],
        items: list[dict[str, Any]],
    ) -> None:
        key = "sceneBatchReview" if kind == "scene" else "tasteBatchReview"
        label = "Scene" if kind == "scene" else "Taste"
        review = state.get(key)
        if not isinstance(review, dict):
            errors.append(f"{filename}: revision 7 requires {key} object")
            return
        if review.get("approval") not in {"PENDING", "APPROVED"}:
            errors.append(f"{filename}: {key}.approval must be PENDING or APPROVED")

        rounds = review.get("rounds")
        if not isinstance(rounds, list):
            errors.append(f"{filename}: {key}.rounds must be a list")
            return

        expected_round_number = 1
        for idx, entry in enumerate(rounds):
            prefix = f"{filename}: {key}.rounds[{idx}]"
            if not isinstance(entry, dict):
                errors.append(f"{prefix} must be an object")
                continue
            if entry.get("round") != expected_round_number:
                errors.append(f"{prefix}.round must be {expected_round_number}")
            expected_round_number += 1
            if entry.get("reviewBoundary") is not True:
                errors.append(f"{prefix}.reviewBoundary must be true")
            if not isinstance(entry.get("approvedAt"), str) or not entry.get("approvedAt"):
                errors.append(f"{prefix}.approvedAt is required")

            scope = entry.get("scope")
            approved = entry.get("approvedGenerations")
            regenerate = entry.get("regenerate")
            if (
                not isinstance(scope, list)
                or not _unique_text_list(scope)
                or any(
                    not isinstance(asset_id, str) or not _contains_text(ids, asset_id)
                    for asset_id in scope
                )
            ):
                errors.append(f"{prefix}.scope must contain unique valid {label} ids")
                continue
            if not isinstance(approved, dict):
                errors.append(f"{prefix}.approvedGenerations must be an object")
                continue
            if not isinstance(regenerate, list) or not _unique_text_list(regenerate):
                errors.append(f"{prefix}.regenerate must be a unique-id list")
                continue

            approved_ids = list(approved.keys())
            if any(
                isinstance(asset_id, str) and _contains_text(regenerate, asset_id)
                for asset_id in approved_ids
            ):
                errors.append(f"{prefix}: approvedGenerations and regenerate must be disjoint")
            if not _same_text_members(approved_ids + regenerate, scope):
                errors.append(
                    f"{prefix}: approvedGenerations + regenerate must exactly partition scope"
                )

            for approved_asset_id, generation_id in approved.items():
                if not isinstance(approved_asset_id, str) or not _contains_text(
                    ids, approved_asset_id
                ):
                    errors.append(f"{prefix}: invalid approved id {approved_asset_id}")
                if not isinstance(generation_id, str) or not generation_id:
                    errors.append(
                        f"{prefix}: approved generation id for {approved_asset_id} is required"
                    )

        for asset_id in ids:
            item = _find_item(items, asset_id)
            if item.get("state") == "APPROVED":
                generation_id = item.get("approvedGenerationId")
                if not isinstance(generation_id, str) or not generation_id:
                    errors.append(
                        f"{filename}: APPROVED {label} {asset_id} requires approvedGenerationId"
                    )
                elif not _generation_covered(rounds, asset_id, generation_id):
                    errors.append(
                        f"{filename}: APPROVED {label} {asset_id} generation {generation_id} is not covered by immutable batch ledger"
                    )
            if item.get("userApprovedAt") is not None:
                errors.append(
                    f"{filename}: revision 7 forbids per-item userApprovedAt on {label} {asset_id}; approval provenance belongs in {key}.rounds"
                )

        if review.get("approval") == "APPROVED" and not all(
            _find_item(items, asset_id).get("state") == "APPROVED" for asset_id in ids
        ):
            errors.append(
                f"{filename}: {key}.approval cannot be APPROVED until all {label} assets are APPROVED"
            )

    guarded_validate_ledger._journey_atlas_digest_guarded = True
    v7_module.validate_ledger = guarded_validate_ledger


def self_test() -> None:
    good = "3ddb4693-70c8-41b9-b2ab-b2e2c5e22529"
    other = "81f620d7-f5d9-4f21-8548-8c7f48ac907e"
    assert _text_equal(good, good)
    assert not _text_equal(good, other)
    assert _same_text_members(["S01", "S02"], ["S02", "S01"])
    assert not _same_text_members(["S01", "S02"], ["S01", "S03"])
    assert _generation_covered(
        [{"approvedGenerations": {"S03": good}}], "S03", good
    )
    assert not _generation_covered(
        [{"approvedGenerations": {"S03": good}}], "S03", other
    )


if __name__ == "__main__":
    self_test()
    print("State JSON runtime guard self-test passed")
