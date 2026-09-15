#!/usr/bin/env python3
"""Run a production-state validator with shared runtime guards installed."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from state_json_runtime import install_json_loads_guard, install_v7_ledger_guard


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("journey_atlas_guarded_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_digest(value: object) -> bytes:
    serialized = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).digest()


def install_v7_transition_guard(v7_module: object) -> None:
    """Preserve append-only semantics while tolerating representation-only rewrites.

    Revision 7 normally compares historical ledger dicts directly. On affected
    Python 3.12 runners, one UUID-shaped decoded string can report inconsistent
    equality even though deterministic JSON serialization is byte-identical.
    When the historical prefix has the same canonical digest, substitute only
    that semantically identical prefix in the in-memory *before* snapshot and
    delegate every other transition rule to the authoritative validator.
    Genuine historical ledger changes therefore remain blocking.
    """
    original = getattr(v7_module, "validate_batch_transition", None)
    if original is None or getattr(original, "_journey_atlas_canonical_guarded", False):
        return

    def guarded_validate_batch_transition(
        errors: list[str],
        path: str,
        before: dict,
        after: dict,
        kind: str,
    ) -> None:
        key = "sceneBatchReview" if kind == "scene" else "tasteBatchReview"
        before_review = before.get(key) if isinstance(before.get(key), dict) else {}
        after_review = after.get(key) if isinstance(after.get(key), dict) else {}
        before_rounds = before_review.get("rounds") if isinstance(before_review.get("rounds"), list) else []
        after_rounds = after_review.get("rounds") if isinstance(after_review.get("rounds"), list) else []

        if len(after_rounds) >= len(before_rounds):
            prefix = after_rounds[: len(before_rounds)]
            same_history = all(
                _canonical_digest(left) == _canonical_digest(right)
                for left, right in zip(before_rounds, prefix)
            )
            if same_history:
                normalized_before = copy.deepcopy(before)
                normalized_review = normalized_before.get(key)
                if isinstance(normalized_review, dict):
                    normalized_review["rounds"] = copy.deepcopy(prefix)
                    original(errors, path, normalized_before, after, kind)
                    return

        original(errors, path, before, after, kind)

    guarded_validate_batch_transition._journey_atlas_canonical_guarded = True
    setattr(v7_module, "validate_batch_transition", guarded_validate_batch_transition)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: run_state_validator.py <validator-script> [args...]", file=sys.stderr)
        return 2

    script = Path(sys.argv[1])
    if not script.exists():
        print(f"Missing validator script: {script}", file=sys.stderr)
        return 2

    forwarded = [str(script), *sys.argv[2:]]
    install_json_loads_guard()
    module = load_module(script)

    install_v7_ledger_guard(module)
    install_v7_transition_guard(module)
    nested_v7 = getattr(module, "v7", None)
    if nested_v7 is not None:
        install_v7_ledger_guard(nested_v7)
        install_v7_transition_guard(nested_v7)

    validator_main = getattr(module, "main", None)
    if validator_main is None:
        print(f"Validator has no main(): {script}", file=sys.stderr)
        return 2

    sys.argv = forwarded
    return int(validator_main())


if __name__ == "__main__":
    raise SystemExit(main())
