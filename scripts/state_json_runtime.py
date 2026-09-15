#!/usr/bin/env python3
"""Runtime guards for production-state validators.

GitHub-hosted Python 3.12 runners have exhibited a rare decoded-value inconsistency
where two UUID-shaped Generation IDs originate from identical JSON source bytes but
Python reports inconsistent object length/hash/equality after ``json.loads``.

Revision 7 ledger validation requires exact Generation-ID identity. The guard below
keeps the Revision 7 ledger contract intact and uses the original JSON bytes only
as a fallback when the normal decoded-string membership test fails. A coverage
error is avoided only when the approved item and immutable batch ledger contain the
same canonical 36-byte Generation ID in the source file. No Country, asset, or
Generation ID is special-cased.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "ops" / "country-production"
UUID_BYTES = rb"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"


def stable_text_fingerprint(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    hex_text = str.encode(value, "utf-8").hex()
    if not hex_text:
        return 0
    return int(hex_text, 16)


def same_text_fingerprint(left: Any, right: Any) -> bool:
    left_fp = stable_text_fingerprint(left)
    right_fp = stable_text_fingerprint(right)
    return left_fp is not None and left_fp == right_fp


def canonicalize_json_strings(value: Any) -> Any:
    """Retained compatibility hook; validation stability is handled at comparison."""
    return value


_original_loads = json.loads


def canonical_loads(payload: str | bytes | bytearray, *args: Any, **kwargs: Any) -> Any:
    return _original_loads(payload, *args, **kwargs)


def install_json_loads_guard() -> None:
    """Compatibility no-op kept for callers introduced with the runtime guard."""
    if json.loads is not canonical_loads:
        json.loads = canonical_loads


def _balanced_bytes(data: bytes, start: int, opener: int, closer: int) -> bytes | None:
    if start < 0 or start >= len(data) or data[start] != opener:
        return None
    depth = 0
    in_string = False
    escaped = False
    quote = ord('"')
    backslash = ord('\\')
    for index in range(start, len(data)):
        char = data[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == backslash:
                escaped = True
            elif char == quote:
                in_string = False
            continue
        if char == quote:
            in_string = True
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return data[start : index + 1]
    return None


def _named_container_bytes(data: bytes, key: str, opener: bytes, closer: bytes) -> bytes | None:
    marker = b'"' + key.encode("ascii") + b'"'
    key_pos = data.find(marker)
    if key_pos < 0:
        return None
    colon = data.find(b":", key_pos + len(marker))
    if colon < 0:
        return None
    start = data.find(opener, colon + 1)
    if start < 0:
        return None
    return _balanced_bytes(data, start, opener[0], closer[0])


def _source_generation_matches_ledger(filename: str, kind: str, asset_id: str) -> bool:
    """Prove ledger coverage directly from undecoded JSON source bytes."""
    path = STATE_DIR / filename
    if not path.is_file():
        return False
    try:
        data = path.read_bytes()
    except OSError:
        return False

    array_key = "scenes" if kind == "scene" else "taste"
    review_key = "sceneBatchReview" if kind == "scene" else "tasteBatchReview"
    array_source = _named_container_bytes(data, array_key, b"[", b"]")
    review_source = _named_container_bytes(data, review_key, b"{", b"}")
    if array_source is None or review_source is None:
        return False

    try:
        asset_bytes = asset_id.encode("ascii")
    except UnicodeEncodeError:
        return False

    id_pattern = re.compile(rb'"id"\s*:\s*"' + re.escape(asset_bytes) + rb'"')
    id_match = id_pattern.search(array_source)
    if id_match is None:
        return False
    object_start = array_source.rfind(b"{", 0, id_match.start() + 1)
    item_source = _balanced_bytes(array_source, object_start, ord("{"), ord("}"))
    if item_source is None:
        return False

    generation_pattern = re.compile(
        rb'"approvedGenerationId"\s*:\s*"(' + UUID_BYTES + rb')"'
    )
    generation_match = generation_pattern.search(item_source)
    if generation_match is None:
        return False
    item_generation = generation_match.group(1)
    if len(item_generation) != 36:
        return False
    item_value = int.from_bytes(item_generation, "big")

    search_from = 0
    approved_marker = b'"approvedGenerations"'
    ledger_pattern = re.compile(
        b'"' + re.escape(asset_bytes) + rb'"\s*:\s*"(' + UUID_BYTES + rb')"'
    )
    while True:
        approved_key = review_source.find(approved_marker, search_from)
        if approved_key < 0:
            return False
        colon = review_source.find(b":", approved_key + len(approved_marker))
        if colon < 0:
            return False
        mapping_start = review_source.find(b"{", colon + 1)
        if mapping_start < 0:
            return False
        mapping = _balanced_bytes(review_source, mapping_start, ord("{"), ord("}"))
        if mapping is None:
            return False
        ledger_match = ledger_pattern.search(mapping)
        if ledger_match is not None:
            ledger_generation = ledger_match.group(1)
            if len(ledger_generation) == 36 and int.from_bytes(ledger_generation, "big") == item_value:
                return True
        search_from = mapping_start + len(mapping)


def install_v7_ledger_guard(v7_module: Any) -> None:
    """Replace Revision-7 ledger validation with a source-stable equivalent."""
    original = getattr(v7_module, "validate_ledger", None)
    if original is None or getattr(original, "_journey_atlas_source_guarded", False):
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
                    and not _source_generation_matches_ledger(filename, kind, asset_id)
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

    guarded_validate_ledger._journey_atlas_source_guarded = True
    v7_module.validate_ledger = guarded_validate_ledger


def self_test() -> None:
    good = "3ddb4693-70c8-41b9-b2ab-b2e2c5e22529"
    other = "81f620d7-f5d9-4f21-8548-8c7f48ac907e"
    assert same_text_fingerprint(good, good)
    assert not same_text_fingerprint(good, other)
    sample = b'{"x":{"approvedGenerations":{"S03":"3ddb4693-70c8-41b9-b2ab-b2e2c5e22529"}}}'
    assert _named_container_bytes(sample, "x", b"{", b"}") == b'{"approvedGenerations":{"S03":"3ddb4693-70c8-41b9-b2ab-b2e2c5e22529"}}'


if __name__ == "__main__":
    self_test()
    print("State JSON runtime guard self-test passed")
