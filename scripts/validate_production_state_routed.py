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
import json.decoder
import json.scanner
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


class PurePythonJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_string = json.decoder.py_scanstring
        self.scan_once = json.scanner.py_make_scanner(self)


def s03_values(state: dict):
    scenes = {str(item.get("id")): item for item in state.get("scenes", []) if isinstance(item, dict)}
    item_id = scenes.get("S03", {}).get("approvedGenerationId")
    ledger_id = state.get("sceneBatchReview", {}).get("rounds", [{}])[0].get("approvedGenerations", {}).get("S03")
    return item_id, ledger_id


def validate() -> list[str]:
    errors: list[str] = []
    registry = legacy.registry_map()

    for path in sorted(STATE_DIR.glob("*.json")):
        try:
            text = path.read_text(encoding="utf-8")
            state = json.loads(text)
        except Exception as exc:
            errors.append(f"{path.name}: cannot parse JSON: {exc}")
            continue

        if state.get("productionProtocolId") == protocol2.PROTOCOL_ID:
            if path.name == "unitedarabemirates.json":
                default_item, default_ledger = s03_values(state)
                pure_state = json.loads(text, cls=PurePythonJSONDecoder)
                pure_item, pure_ledger = s03_values(pure_state)
                print("UAE_JSON_DIAGNOSTIC default=", len(default_item), len(default_ledger), default_item == default_ledger)
                print("UAE_JSON_DIAGNOSTIC pure_python=", len(pure_item), len(pure_ledger), pure_item == pure_ledger)
                print("UAE_JSON_DIAGNOSTIC pure_hex=", pure_item.encode("utf-8").hex(), pure_ledger.encode("utf-8").hex())
            errors.extend(v7.validate_state_dict(state, path.name))
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
