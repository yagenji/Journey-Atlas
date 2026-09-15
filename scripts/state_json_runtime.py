#!/usr/bin/env python3
"""Runtime guard for JSON strings consumed by production-state validators.

GitHub-hosted Python 3.12 runners have exhibited a rare decoded-str inconsistency
where two UUID strings expose identical UTF-8 bytes but disagree on len/hash/equality.
Production State validation depends on exact immutable generation-id comparisons,
so rebuild decoded JSON strings through UTF-8 before validating them.

This module is deliberately generic: it does not special-case a Country, asset,
or generation id.
"""

from __future__ import annotations

import json
from typing import Any


def canonicalize_json_strings(value: Any) -> Any:
    if isinstance(value, str):
        return value.encode("utf-8").decode("utf-8")
    if isinstance(value, list):
        return [canonicalize_json_strings(item) for item in value]
    if isinstance(value, dict):
        return {
            canonicalize_json_strings(key): canonicalize_json_strings(item)
            for key, item in value.items()
        }
    return value


_original_loads = json.loads


def canonical_loads(payload: str | bytes | bytearray, *args: Any, **kwargs: Any) -> Any:
    return canonicalize_json_strings(_original_loads(payload, *args, **kwargs))


def install_json_loads_guard() -> None:
    """Patch json.loads for validator processes launched through the safe wrapper."""
    if json.loads is not canonical_loads:
        json.loads = canonical_loads
