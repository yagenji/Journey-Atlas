#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
CONTENT_QA_VERSION = 2
FOREST_LOW_MAX = 10.0
FOREST_HIGH_MIN = 70.0
FOREST_TERMS = ("森林", "樹林", "forest", "woodland")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def validate_travel_scale(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    scale = data.get("travelScale")
    if not isinstance(scale, dict):
        fail(errors, f"{filename}: Content QA v2 requires travelScale object")
        return
    if scale.get("kicker") != "DURATION":
        fail(errors, f"{filename}: travelScale.kicker must be DURATION")
    if scale.get("title") != "旅の目安日程":
        fail(errors, f"{filename}: travelScale.title must be 旅の目安日程")

    items = scale.get("items")
    if not isinstance(items, list) or len(items) != 3:
        fail(errors, f"{filename}: travelScale must contain exactly 3 items")
        return

    expected_icons = ["city", "map", "compass"]
    for index, item in enumerate(items, 1):
        owner = f"{filename}: travelScale.items[{index}]"
        if not isinstance(item, dict):
            fail(errors, f"{owner} must be an object")
            continue
        duration = text(item.get("duration"))
        title = text(item.get("title"))
        body = text(item.get("text"))
        icon = text(item.get("icon"))
        if not duration or "週間" in duration or "日" not in duration:
            fail(errors, f"{owner}.duration must use day notation: {duration!r}")
        if not title:
            fail(errors, f"{owner}.title is required")
        if not body:
            fail(errors, f"{owner}.text is required")
        if icon != expected_icons[index - 1]:
            fail(errors, f"{owner}.icon must be {expected_icons[index - 1]!r}")
        if "例：" not in body:
            fail(errors, f"{owner}.text must include a concrete example introduced by '例：'")
        else:
            example = body.split("例：", 1)[1].strip().rstrip("。")
            if len(example) < 4:
                fail(errors, f"{owner}.text has an empty/too-short example")

    final_duration = text(items[2].get("duration") if isinstance(items[2], dict) else None)
    if not re.fullmatch(r"\d+日以上", final_duration):
        fail(errors, f"{filename}: final travelScale duration must be '○日以上': {final_duration!r}")


def forest_related(item: dict[str, Any]) -> bool:
    haystack = " ".join(
        text(item.get(key)).lower()
        for key in ("topicKey", "label", "value", "note")
    )
    return any(term.lower() in haystack for term in FOREST_TERMS)


def percentages(item: dict[str, Any]) -> list[float]:
    haystack = " ".join(text(item.get(key)) for key in ("value", "note"))
    return [float(match) for match in re.findall(r"(\d+(?:\.\d+)?)\s*%", haystack)]


def validate_signature_facts(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    facts = data.get("signatureFacts")
    if not isinstance(facts, list) or len(facts) != 3:
        fail(errors, f"{filename}: signatureFacts must contain exactly 3 items")
        return

    for index, item in enumerate(facts, 1):
        owner = f"{filename}: signatureFacts[{index}]"
        if not isinstance(item, dict):
            fail(errors, f"{owner} must be an object")
            continue
        for key in ("topicKey", "label", "value", "note"):
            if not text(item.get(key)):
                fail(errors, f"{owner}.{key} is required")

        if not forest_related(item):
            continue
        pcts = percentages(item)
        if not pcts:
            continue
        if item.get("exceptionalShare") is not True:
            fail(
                errors,
                f"{owner}: forest/woodland percentage is not a default Signature Fact. "
                "Use another distinctive number, or set exceptionalShare:true only for an extreme national characteristic.",
            )
            continue
        moderate = [pct for pct in pcts if FOREST_LOW_MAX < pct < FOREST_HIGH_MIN]
        if moderate:
            fail(
                errors,
                f"{owner}: moderate forest/woodland share {moderate} is not distinctive enough for Signature Facts. "
                f"Protocol 2 allows forest share only at <= {FOREST_LOW_MAX:g}% or >= {FOREST_HIGH_MIN:g}%.",
            )


def validate_data(data: dict[str, Any], filename: str, *, force: bool = False) -> list[str]:
    if not force and data.get("contentQaVersion", 1) < CONTENT_QA_VERSION:
        return []
    errors: list[str] = []
    validate_travel_scale(errors, filename, data)
    validate_signature_facts(errors, filename, data)
    return errors


def validate_path(path: Path, *, force: bool = False) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.name}: cannot read JSON: {exc}"]
    return validate_data(data, path.name, force=force)


def main() -> int:
    args = sys.argv[1:]
    force = False
    if args and args[0] == "--force":
        force = True
        args = args[1:]
    paths = [Path(arg) for arg in args] if args else sorted(COUNTRY_DIR.glob("*.json"))
    errors: list[str] = []
    checked = 0
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.name}: cannot read JSON: {exc}")
            continue
        if force or data.get("contentQaVersion", 1) >= CONTENT_QA_VERSION:
            checked += 1
            errors.extend(validate_data(data, path.name, force=True))

    if errors:
        print("Editorial Content QA v2: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Editorial Content QA v2: PASS ({checked} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
