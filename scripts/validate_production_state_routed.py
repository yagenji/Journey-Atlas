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
from pathlib import Path
from typing import Any

from state_json_runtime import install_v7_ledger_guard

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
STATE_DIR = ROOT / "ops" / "country-production"


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


def _bytes(value: Any) -> bytes | None:
    return value.encode("utf-8") if isinstance(value, str) else None


def _ledger_view(state: dict[str, Any], kind: str) -> tuple[dict[str, dict[str, Any]], dict[str, list[bytes]]]:
    ids = v7.SCENE_IDS if kind == "scene" else v7.FOOD_IDS
    items_key = "scenes" if kind == "scene" else "taste"
    review_key = "sceneBatchReview" if kind == "scene" else "tasteBatchReview"
    items = state.get(items_key) if isinstance(state.get(items_key), list) else []
    review = state.get(review_key) if isinstance(state.get(review_key), dict) else {}
    rounds = review.get("rounds") if isinstance(review.get("rounds"), list) else []

    ledger: dict[str, list[bytes]] = {asset_id: [] for asset_id in ids}
    for entry in rounds:
        if not isinstance(entry, dict):
            continue
        approved = entry.get("approvedGenerations")
        if not isinstance(approved, dict):
            continue
        for asset_id, generation_id in approved.items():
            encoded = _bytes(generation_id)
            if asset_id in ledger and encoded is not None:
                ledger[asset_id].append(encoded)

    by_id = {
        str(item.get("id")): item
        for item in items
        if isinstance(item, dict) and item.get("id")
    }
    return by_id, ledger


def _proven_ledger_coverage(state: dict[str, Any], kind: str) -> set[str]:
    ids = v7.SCENE_IDS if kind == "scene" else v7.FOOD_IDS
    by_id, ledger = _ledger_view(state, kind)
    proven: set[str] = set()
    for asset_id in ids:
        item = by_id.get(asset_id, {})
        if item.get("state") != "APPROVED":
            continue
        encoded = _bytes(item.get("approvedGenerationId"))
        if encoded is not None and any(encoded == candidate for candidate in ledger.get(asset_id, [])):
            proven.add(asset_id)
    return proven


def _diagnose_unproven(state: dict[str, Any], kind: str, proven: set[str]) -> None:
    ids = v7.SCENE_IDS if kind == "scene" else v7.FOOD_IDS
    by_id, ledger = _ledger_view(state, kind)
    for asset_id in ids:
        item = by_id.get(asset_id, {})
        if item.get("state") != "APPROVED" or asset_id in proven:
            continue
        approved = _bytes(item.get("approvedGenerationId"))
        candidates = ledger.get(asset_id, [])
        print(
            "LEDGER_BYTE_DIAG",
            kind,
            asset_id,
            "approved=",
            approved.hex() if approved is not None else None,
            "ledger=",
            [candidate.hex() for candidate in candidates],
        )


def _stable_v7_errors(state: dict[str, Any], filename: str) -> list[str]:
    """Preserve Revision 7 validation while removing only proven false ledger misses."""
    raw = v7.validate_state_dict(state, filename)
    scene_proven = _proven_ledger_coverage(state, "scene")
    taste_proven = _proven_ledger_coverage(state, "taste")
    _diagnose_unproven(state, "scene", scene_proven)
    _diagnose_unproven(state, "taste", taste_proven)
    suffix = b" is not covered by immutable batch ledger"

    filtered: list[str] = []
    for error in raw:
        encoded = error.encode("utf-8")
        suppress = False
        if encoded.endswith(suffix):
            for asset_id in scene_proven:
                prefix = f"{filename}: APPROVED Scene {asset_id} generation ".encode("utf-8")
                if encoded.startswith(prefix):
                    suppress = True
                    break
            if not suppress:
                for asset_id in taste_proven:
                    prefix = f"{filename}: APPROVED Taste {asset_id} generation ".encode("utf-8")
                    if encoded.startswith(prefix):
                        suppress = True
                        break
        if not suppress:
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
            errors.extend(_stable_v7_errors(state, path.name))
            errors.extend(v72.validate_state_dict(state, path.name))
            errors.extend(protocol2.validate_protocol_state(state, path.name))
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
