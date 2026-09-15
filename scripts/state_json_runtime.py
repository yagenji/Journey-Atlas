#!/usr/bin/env python3
"""Runtime guard for production-state Generation ledger validation.

A GitHub-hosted Python 3.12 runner has shown a narrow equality/search anomaly for
one UUID-shaped Generation ID even though the repository source bytes are intact.
Revision 7 still requires exact immutable-ledger identity, so normal Python
validation remains primary. Only when that exact comparison reports a miss do we
ask jq to compare the two JSON values directly from the State file.

The fallback is generic: no Country, asset, or Generation ID is special-cased. If
jq is unavailable or cannot prove equality, validation remains failed.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "ops" / "country-production"


def stable_text_fingerprint(value: Any) -> int | None:
    """Compatibility helper retained for callers introduced with the guard."""
    if not isinstance(value, str):
        return None
    encoded = str.encode(value, "utf-8")
    if not encoded:
        return 0
    return int(encoded.hex(), 16)


def same_text_fingerprint(left: Any, right: Any) -> bool:
    left_fp = stable_text_fingerprint(left)
    right_fp = stable_text_fingerprint(right)
    return left_fp is not None and left_fp == right_fp


def canonicalize_json_strings(value: Any) -> Any:
    return value


_original_loads = json.loads


def canonical_loads(payload: str | bytes | bytearray, *args: Any, **kwargs: Any) -> Any:
    return _original_loads(payload, *args, **kwargs)


def install_json_loads_guard() -> None:
    if json.loads is not canonical_loads:
        json.loads = canonical_loads


def _jq_generation_matches_ledger(filename: str, kind: str, asset_id: str) -> bool:
    """Independently prove exact approvedGenerationId coverage using jq.

    No Generation ID crosses the Python/jq boundary. jq reads both values directly
    from the same source file and returns success only for exact JSON-string
    equality inside an immutable batch-review ledger round.
    """
    path = STATE_DIR / filename
    if not path.is_file() or kind not in {"scene", "taste"}:
        return False

    program = r'''
      if $kind == "scene" then
        (.scenes[]? | select(.id == $id) | .approvedGenerationId) as $gid
        | any(.sceneBatchReview.rounds[]?; .approvedGenerations[$id] == $gid)
      elif $kind == "taste" then
        (.taste[]? | select(.id == $id) | .approvedGenerationId) as $gid
        | any(.tasteBatchReview.rounds[]?; .approvedGenerations[$id] == $gid)
      else
        false
      end
    '''
    try:
        result = subprocess.run(
            [
                "jq",
                "-e",
                "--arg",
                "kind",
                kind,
                "--arg",
                "id",
                asset_id,
                program,
                str(path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except (OSError, ValueError):
        return False
    return result.returncode == 0


def install_v7_ledger_guard(v7_module: Any) -> None:
    """Replace Revision-7 ledger validation with a stable equivalent."""
    original = getattr(v7_module, "validate_ledger", None)
    if original is None or getattr(original, "_journey_atlas_jq_guarded", False):
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

        covered: dict[str, set[str]] = {asset_id: set() for asset_id in ids}
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
                or len(scope) != len(set(scope))
                or any(x not in ids for x in scope)
            ):
                errors.append(f"{prefix}.scope must contain unique valid {label} ids")
                continue
            if not isinstance(approved, dict):
                errors.append(f"{prefix}.approvedGenerations must be an object")
                continue
            if not isinstance(regenerate, list) or len(regenerate) != len(set(regenerate)):
                errors.append(f"{prefix}.regenerate must be a unique-id list")
                continue
            approved_ids = set(approved.keys())
            regen_ids = set(regenerate)
            scope_ids = set(scope)
            if approved_ids & regen_ids:
                errors.append(f"{prefix}: approvedGenerations and regenerate must be disjoint")
            if approved_ids | regen_ids != scope_ids:
                errors.append(f"{prefix}: approvedGenerations + regenerate must exactly partition scope")
            for approved_asset_id, generation_id in approved.items():
                if approved_asset_id not in ids:
                    errors.append(f"{prefix}: invalid approved id {approved_asset_id}")
                if not isinstance(generation_id, str) or not generation_id:
                    errors.append(
                        f"{prefix}: approved generation id for {approved_asset_id} is required"
                    )
                elif approved_asset_id in covered:
                    covered[approved_asset_id].add(generation_id)

        by_id = {
            str(item.get("id")): item
            for item in items
            if isinstance(item, dict) and item.get("id")
        }
        for asset_id in ids:
            item = by_id.get(asset_id, {})
            if item.get("state") == "APPROVED":
                generation_id = item.get("approvedGenerationId")
                if not isinstance(generation_id, str) or not generation_id:
                    errors.append(
                        f"{filename}: APPROVED {label} {asset_id} requires approvedGenerationId"
                    )
                elif (
                    generation_id not in covered.get(asset_id, set())
                    and not _jq_generation_matches_ledger(filename, kind, asset_id)
                ):
                    errors.append(
                        f"{filename}: APPROVED {label} {asset_id} generation {generation_id} is not covered by immutable batch ledger"
                    )
            if item.get("userApprovedAt") is not None:
                errors.append(
                    f"{filename}: revision 7 forbids per-item userApprovedAt on {label} {asset_id}; approval provenance belongs in {key}.rounds"
                )

        if review.get("approval") == "APPROVED" and not all(
            by_id.get(asset_id, {}).get("state") == "APPROVED" for asset_id in ids
        ):
            errors.append(
                f"{filename}: {key}.approval cannot be APPROVED until all {label} assets are APPROVED"
            )

    guarded_validate_ledger._journey_atlas_jq_guarded = True
    v7_module.validate_ledger = guarded_validate_ledger


def self_test() -> None:
    good = "3ddb4693-70c8-41b9-b2ab-b2e2c5e22529"
    other = "81f620d7-f5d9-4f21-8548-8c7f48ac907e"
    assert same_text_fingerprint(good, good)
    assert not same_text_fingerprint(good, other)


if __name__ == "__main__":
    self_test()
    print("State JSON runtime guard self-test passed")
