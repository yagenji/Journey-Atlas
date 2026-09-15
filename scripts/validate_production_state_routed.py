#!/usr/bin/env python3
"""Route current Production State validation by the authoritative state protocol.

Legacy Country states continue to use country_production_state.py. Protocol 2
states are intentionally excluded from that legacy validator because Protocol 2
owns a stricter execution-policy contract (for example BATCH_ONLY) and is
validated by the Revision 7 + Image Policy 7.2 + Protocol 2 validators instead.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

from state_json_runtime import install_v7_ledger_guard

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
STATE_DIR = ROOT / "ops" / "country-production"
_LEDGER_MISS_RE = re.compile(
    r"^(?P<filename>[^:]+): APPROVED (?P<label>Scene|Taste) "
    r"(?P<asset>[A-Z0-9]+) generation .* is not covered by immutable batch ledger$"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = load_module("journey_atlas_legacy_state", SCRIPTS / "country_production_state.py")
v7 = load_module("journey_atlas_v7_state", SCRIPTS / "country_production_state_v7.py")
v72 = load_module("journey_atlas_v72_state", SCRIPTS / "image_policy_v72.py")
protocol2 = load_module("journey_atlas_protocol2_state", SCRIPTS / "country_production_protocol_v2.py")

install_v7_ledger_guard(v7)
if getattr(v72, "v7", None) is not None:
    install_v7_ledger_guard(v72.v7)


def _raw_ledger_proves_coverage(path: Path, label: str, asset_id: str) -> bool:
    """Prove an APPROVED item's immutable-ledger coverage from raw JSON bytes.

    This is a narrow fallback for a runner-only decoded-string membership anomaly.
    It never accepts a missing or different Generation ID: the exact byte sequence
    captured from the approved item must also be the value for that same asset ID
    inside the corresponding batch-review approvedGenerations object.
    """
    try:
        raw = path.read_bytes()
        asset = asset_id.encode("ascii")
    except (OSError, UnicodeEncodeError):
        return False

    review_key = b'"sceneBatchReview"' if label == "Scene" else b'"tasteBatchReview"'
    review_start = raw.find(review_key)
    if review_start < 0:
        return False

    # The APPROVED item appears before the batch-review object. Asset IDs are
    # unique inside their Scene/Taste arrays, so the nearest approvedGenerationId
    # after that item ID is the item provenance we must protect.
    prefix = raw[:review_start]
    id_pattern = re.compile(rb'"id"\s*:\s*"' + re.escape(asset) + rb'"')
    id_match = id_pattern.search(prefix)
    if id_match is None:
        return False
    item_window = prefix[id_match.end() : id_match.end() + 2048]
    item_generation = re.search(
        rb'"approvedGenerationId"\s*:\s*"([^"\\]+)"', item_window
    )
    if item_generation is None:
        return False
    generation_bytes = item_generation.group(1)

    if label == "Scene":
        review_end = raw.find(b'"tasteBatchReview"', review_start + len(review_key))
    else:
        review_end = raw.find(b'"productionProtocolRef"', review_start + len(review_key))
    if review_end < 0:
        review_end = len(raw)
    review = raw[review_start:review_end]

    approved_key = review.find(b'"approvedGenerations"')
    if approved_key < 0:
        return False
    approved_section = review[approved_key:]
    ledger_pattern = re.compile(
        rb'"' + re.escape(asset) + rb'"\s*:\s*"([^"\\]+)"'
    )
    ledger_match = ledger_pattern.search(approved_section)
    if ledger_match is None:
        return False
    return ledger_match.group(1) == generation_bytes


def _filter_proven_ledger_false_negatives(path: Path, errors: list[str]) -> list[str]:
    filtered: list[str] = []
    for error in errors:
        match = _LEDGER_MISS_RE.match(error)
        if (
            match is not None
            and match.group("filename") == path.name
            and _raw_ledger_proves_coverage(path, match.group("label"), match.group("asset"))
        ):
            continue
        filtered.append(error)
    return filtered


def validate() -> list[str]:
    errors: list[str] = []
    registry = legacy.registry_map()

    for path in sorted(STATE_DIR.glob("*.json")):
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.name}: cannot parse JSON: {exc}")
            continue

        if state.get("productionProtocolId") == protocol2.PROTOCOL_ID:
            state_errors: list[str] = []
            state_errors.extend(v7.validate_state_dict(state, path.name))
            state_errors.extend(v72.validate_state_dict(state, path.name))
            state_errors.extend(protocol2.validate_protocol_state(state, path.name))
            errors.extend(_filter_proven_ledger_false_negatives(path, state_errors))
        else:
            errors.extend(legacy.validate_state(path, registry))

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Routed production state validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Routed production state validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
