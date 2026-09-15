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


def _debug_s03_source(path: Path) -> None:
    data = path.read_bytes()
    needle = b"3ddb4693-70c8-41b9-b2ab-b2e2c5e22529"
    positions: list[int] = []
    cursor = 0
    while True:
        pos = data.find(needle, cursor)
        if pos < 0:
            break
        positions.append(pos)
        cursor = pos + 1
    print("S03_RAW_EXACT_COUNT", len(positions), "POSITIONS", positions)
    cursor = 0
    fragments: list[str] = []
    while True:
        pos = data.find(b"3ddb", cursor)
        if pos < 0:
            break
        fragments.append(data[max(0, pos - 16):pos + 64].hex())
        cursor = pos + 1
    print("S03_RAW_FRAGMENTS", fragments)


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
            if path.name == "unitedarabemirates.json" and any("S03 generation" in error for error in v7_errors):
                _debug_s03_source(path)
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
