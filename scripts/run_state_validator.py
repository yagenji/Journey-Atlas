#!/usr/bin/env python3
"""Run a production-state validator with canonical JSON string decoding."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

from state_json_runtime import install_json_loads_guard


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: run_state_validator.py <validator-script> [args...]", file=sys.stderr)
        return 2

    script = Path(sys.argv[1])
    if not script.exists():
        print(f"Missing validator script: {script}", file=sys.stderr)
        return 2

    install_json_loads_guard()
    sys.argv = [str(script), *sys.argv[2:]]
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
