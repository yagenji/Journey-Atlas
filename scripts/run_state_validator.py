#!/usr/bin/env python3
"""Run a production-state validator with shared runtime guards installed."""

from __future__ import annotations

import importlib.util
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
    nested_v7 = getattr(module, "v7", None)
    if nested_v7 is not None:
        install_v7_ledger_guard(nested_v7)

    validator_main = getattr(module, "main", None)
    if validator_main is None:
        print(f"Validator has no main(): {script}", file=sys.stderr)
        return 2

    sys.argv = forwarded
    return int(validator_main())


if __name__ == "__main__":
    raise SystemExit(main())
