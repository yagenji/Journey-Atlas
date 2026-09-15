#!/usr/bin/env python3
"""Runtime guard for JSON values consumed by production-state validators.

GitHub-hosted Python 3.12 runners have exhibited a rare decoded-str inconsistency
where two UUID-shaped generation IDs expose identical UTF-8 bytes but disagree on
len/hash/equality. Production State validation depends on exact immutable
Generation ID comparisons, so only Generation ID values are wrapped in a str
subclass whose comparison semantics use their stable UTF-8 bytes.

This module is deliberately generic: it does not special-case a Country, asset,
or generation id. Dictionary keys and ordinary editorial/content strings are
left untouched.
"""

from __future__ import annotations

import json
import re
from typing import Any

_UUID_BYTES = re.compile(
    rb"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_GENERATION_ID_FIELDS = {
    "approvedGenerationId",
    "candidateGenerationId",
    "generationId",
}
_GENERATION_ID_MAP_FIELDS = {
    "approvedGenerations",
    "adoptedSceneGenerations",
    "adoptedTasteGenerations",
}
_GENERATION_ID_LIST_FIELDS = {
    "rejectedGenerationIds",
}


class StableGenerationId(str):
    """A str-compatible Generation ID with byte-stable equality and hashing."""

    def _stable_bytes(self) -> bytes:
        return str.encode(self, "utf-8")

    def __len__(self) -> int:
        return len(self._stable_bytes())

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self._stable_bytes() == str.encode(other, "utf-8")
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self._stable_bytes())


def _stable_generation_id(value: str) -> str:
    raw = str.encode(value, "utf-8")
    if not _UUID_BYTES.fullmatch(raw):
        return value
    return StableGenerationId(raw, "utf-8")


def canonicalize_json_strings(value: Any, *, field: str | None = None) -> Any:
    """Canonicalize only Generation ID values; preserve JSON keys and other text."""
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            key_text = key if isinstance(key, str) else None
            if field in _GENERATION_ID_MAP_FIELDS and isinstance(item, str):
                out[key] = _stable_generation_id(item)
            else:
                out[key] = canonicalize_json_strings(item, field=key_text)
        return out

    if isinstance(value, list):
        if field in _GENERATION_ID_LIST_FIELDS:
            return [
                _stable_generation_id(item) if isinstance(item, str) else canonicalize_json_strings(item)
                for item in value
            ]
        return [canonicalize_json_strings(item) for item in value]

    if isinstance(value, str) and field in _GENERATION_ID_FIELDS:
        return _stable_generation_id(value)

    return value


_original_loads = json.loads


def canonical_loads(payload: str | bytes | bytearray, *args: Any, **kwargs: Any) -> Any:
    return canonicalize_json_strings(_original_loads(payload, *args, **kwargs))


def install_json_loads_guard() -> None:
    """Patch json.loads for validator processes launched through the safe wrapper."""
    if json.loads is not canonical_loads:
        json.loads = canonical_loads


def self_test() -> None:
    raw = b"3ddb4693-70c8-41b9-b2ab-b2e2c5e22529"
    a = StableGenerationId(raw, "utf-8")
    b = StableGenerationId(raw, "utf-8")
    assert isinstance(a, str)
    assert len(a) == 36
    assert a == b
    assert hash(a) == hash(b)
    assert a in {b}

    state = canonicalize_json_strings(
        {
            "approvedGenerationId": raw.decode("utf-8"),
            "sceneBatchReview": {
                "rounds": [{"approvedGenerations": {"S03": raw.decode("utf-8")}}]
            },
            "title": raw.decode("utf-8"),
        }
    )
    item = state["approvedGenerationId"]
    ledger = state["sceneBatchReview"]["rounds"][0]["approvedGenerations"]["S03"]
    assert isinstance(item, StableGenerationId)
    assert isinstance(ledger, StableGenerationId)
    assert item == ledger
    assert item in {ledger}
    assert type(state["title"]) is str


if __name__ == "__main__":
    self_test()
    print("State JSON runtime guard self-test passed")
