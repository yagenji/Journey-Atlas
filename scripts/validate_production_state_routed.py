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
            v7_errors = v7.validate_state_dict(state, path.name)
            if path.name == "unitedarabemirates.json" and v7_errors:
                scenes = {str(item.get("id")): item for item in state.get("scenes", []) if isinstance(item, dict)}
                rounds = state.get("sceneBatchReview", {}).get("rounds", [])
                direct_covered = {asset_id: set() for asset_id in v7.SCENE_IDS}
                for entry in rounds:
                    for asset_id, generation_id in (entry.get("approvedGenerations") or {}).items():
                        if asset_id in direct_covered:
                            direct_covered[asset_id].add(generation_id)
                item_id = scenes.get("S03", {}).get("approvedGenerationId")
                ledger_id = next(iter(direct_covered.get("S03", set())), None)
                probe_errors: list[str] = []
                v7.validate_ledger(probe_errors, path.name, state, "scene", v7.SCENE_IDS, state.get("scenes", []))
                print("UAE_LEDGER_DIAGNOSTIC scene_ids=", repr(v7.SCENE_IDS))
                print("UAE_LEDGER_DIAGNOSTIC item=", repr(item_id), "type=", type(item_id).__name__, "len=", len(item_id) if isinstance(item_id, str) else None, "hex=", item_id.encode("utf-8").hex() if isinstance(item_id, str) else None, "hash=", hash(item_id) if isinstance(item_id, str) else None)
                print("UAE_LEDGER_DIAGNOSTIC ledger=", repr(ledger_id), "type=", type(ledger_id).__name__, "len=", len(ledger_id) if isinstance(ledger_id, str) else None, "hex=", ledger_id.encode("utf-8").hex() if isinstance(ledger_id, str) else None, "hash=", hash(ledger_id) if isinstance(ledger_id, str) else None)
                print("UAE_LEDGER_DIAGNOSTIC equality=", item_id == ledger_id)
                print("UAE_LEDGER_DIAGNOSTIC membership=", item_id in direct_covered.get("S03", set()))
                print("UAE_LEDGER_DIAGNOSTIC probe_errors=", repr(probe_errors))
                print("UAE_LEDGER_DIAGNOSTIC v7_module=", str(Path(v7.__file__).resolve()))
            errors.extend(v7_errors)
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
