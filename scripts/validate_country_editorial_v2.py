#!/usr/bin/env python3
"""JOURNEY ATLAS editorial content validator.

The filename is retained for CI/backward compatibility. Content QA v2 rules remain
valid for existing v2 Countries. Content QA v3 applies to new Countries and adds:
- no numeric stay/day/week counts in Travel Scale;
- canonical topic separation across Signature Facts / Beyond the Scenery / Trivia;
- a conservative near-duplicate text guard across those three sections.
"""
from __future__ import annotations

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
CONTENT_QA_V2 = 2
CONTENT_QA_V3 = 3
FOREST_LOW_MAX = 10.0
FOREST_HIGH_MIN = 70.0
FOREST_TERMS = ("森林", "樹林", "forest", "woodland")
TRAVEL_ICONS = ("city", "map", "compass")
DURATION_COUNT_RE = re.compile(
    r"(?:\d+(?:\.\d+)?|[一二三四五六七八九十百千万数半]+)\s*(?:日|泊|週間|週)"
)
DURATION_WORDS = ("日帰り",)
TOPIC_SUFFIXES = {
    "count", "counts", "number", "numbers", "share", "rate", "ratio", "percent",
    "percentage", "stat", "stats", "fact", "facts", "trivia", "history", "background",
    "overview", "story", "system", "culture", "context", "figure", "figures",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def qa_version(data: dict[str, Any]) -> int:
    value = data.get("contentQaVersion", 1)
    return value if isinstance(value, int) else 1


def validate_common_travel_scale(
    errors: list[str], filename: str, data: dict[str, Any]
) -> list[dict[str, Any]]:
    scale = data.get("travelScale")
    if not isinstance(scale, dict):
        fail(errors, f"{filename}: Content QA requires travelScale object")
        return []
    if scale.get("kicker") != "DURATION":
        fail(errors, f"{filename}: travelScale.kicker must be DURATION")
    if scale.get("title") != "旅の目安日程":
        fail(errors, f"{filename}: travelScale.title must be 旅の目安日程")

    items = scale.get("items")
    if not isinstance(items, list) or len(items) != 3:
        fail(errors, f"{filename}: travelScale must contain exactly 3 items")
        return []

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, 1):
        owner = f"{filename}: travelScale.items[{index}]"
        if not isinstance(item, dict):
            fail(errors, f"{owner} must be an object")
            continue
        duration = text(item.get("duration"))
        title = text(item.get("title"))
        body = text(item.get("text"))
        icon = text(item.get("icon"))
        if not duration:
            fail(errors, f"{owner}.duration is required")
        if not title:
            fail(errors, f"{owner}.title is required")
        if not body:
            fail(errors, f"{owner}.text is required")
        if icon != TRAVEL_ICONS[index - 1]:
            fail(errors, f"{owner}.icon must be {TRAVEL_ICONS[index - 1]!r}")
        if "例：" not in body:
            fail(errors, f"{owner}.text must include a concrete example introduced by '例：'")
        else:
            example = body.split("例：", 1)[1].strip().rstrip("。")
            if len(example) < 4:
                fail(errors, f"{owner}.text has an empty/too-short example")
        normalized.append(item)
    return normalized


def validate_travel_scale_v2(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    items = validate_common_travel_scale(errors, filename, data)
    if len(items) != 3:
        return
    for index, item in enumerate(items, 1):
        duration = text(item.get("duration"))
        if "週間" in duration or "日" not in duration:
            fail(errors, f"{filename}: travelScale.items[{index}].duration must use day notation: {duration!r}")
    final_duration = text(items[2].get("duration"))
    if not re.fullmatch(r"\d+日以上", final_duration):
        fail(errors, f"{filename}: final travelScale duration must be '○日以上': {final_duration!r}")


def contains_forbidden_duration(value: str) -> bool:
    return bool(DURATION_COUNT_RE.search(value)) or any(word in value for word in DURATION_WORDS)


def validate_travel_scale_v3(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    items = validate_common_travel_scale(errors, filename, data)
    for index, item in enumerate(items, 1):
        owner = f"{filename}: travelScale.items[{index}]"
        for key in ("duration", "title", "text"):
            value = text(item.get(key))
            if contains_forbidden_duration(value):
                fail(
                    errors,
                    f"{owner}.{key}: Content QA v3 forbids numeric stay/day/week counts in 旅の目安日程: {value!r}",
                )


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


def canonical_topic_key(value: str) -> str:
    parts = [part for part in re.split(r"[-_\s]+", value.strip().lower()) if part]
    while len(parts) > 1 and parts[-1] in TOPIC_SUFFIXES:
        parts.pop()
    return "-".join(parts)


def item_copy_text(section: str, item: dict[str, Any]) -> str:
    values: list[str] = []
    if section == "signatureFacts":
        keys = ("label", "value", "note")
    elif section == "atlasExtras":
        keys = ("title", "text")
    else:
        keys = ("categoryJa", "title", "text")
    for key in keys:
        value = item.get(key)
        if isinstance(value, str):
            values.append(value)
    if section == "atlasExtras":
        points = item.get("points")
        if isinstance(points, list):
            values.extend(str(point) for point in points if isinstance(point, str))
    return " ".join(values)


def normalize_copy(value: str) -> str:
    value = value.lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[\W_]+", "", value, flags=re.UNICODE)
    return value


def character_ngrams(value: str, n: int = 3) -> set[str]:
    normalized = normalize_copy(value)
    if len(normalized) < n:
        return {normalized} if normalized else set()
    return {normalized[index : index + n] for index in range(len(normalized) - n + 1)}


def near_duplicate(a: str, b: str) -> bool:
    na = normalize_copy(a)
    nb = normalize_copy(b)
    if min(len(na), len(nb)) < 24:
        return False

    shorter, longer = (na, nb) if len(na) <= len(nb) else (nb, na)
    if shorter in longer:
        return True

    if SequenceMatcher(None, na, nb).ratio() >= 0.66:
        return True

    grams_a = character_ngrams(na)
    grams_b = character_ngrams(nb)
    if not grams_a or not grams_b:
        return False
    overlap = len(grams_a & grams_b) / min(len(grams_a), len(grams_b))
    return overlap >= 0.70


def validate_cross_section_topics(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    sections = ("signatureFacts", "atlasExtras", "travelTrivia")
    seen_exact: dict[str, str] = {}
    seen_canonical: dict[str, str] = {}
    records: list[tuple[str, str, str]] = []

    for section in sections:
        items = data.get(section)
        if not isinstance(items, list):
            fail(errors, f"{filename}: Content QA v3 requires {section} list")
            continue
        for index, item in enumerate(items, 1):
            owner = f"{section}[{index}]"
            if not isinstance(item, dict):
                fail(errors, f"{filename}: {owner} must be an object")
                continue
            key = text(item.get("topicKey")).lower()
            if not key:
                fail(errors, f"{filename}: {owner}.topicKey is required for cross-section deduplication")
                continue
            canonical = canonical_topic_key(key)
            prior = seen_exact.get(key)
            if prior and prior.split("[", 1)[0] != section:
                fail(errors, f"{filename}: duplicate topicKey {key!r} across {prior} and {owner}")
            else:
                seen_exact[key] = owner
            prior_canonical = seen_canonical.get(canonical)
            if prior_canonical and prior_canonical.split("[", 1)[0] != section:
                fail(
                    errors,
                    f"{filename}: semantic topic collision {canonical!r} across {prior_canonical} and {owner}; "
                    "数値 / 景色の向こうへ / トリビア must use different subjects, not renamed versions of the same subject.",
                )
            else:
                seen_canonical[canonical] = owner
            records.append((section, owner, item_copy_text(section, item)))

    for i, (section_a, owner_a, copy_a) in enumerate(records):
        for section_b, owner_b, copy_b in records[i + 1 :]:
            if section_a == section_b:
                continue
            if near_duplicate(copy_a, copy_b):
                fail(
                    errors,
                    f"{filename}: near-duplicate copy across {owner_a} and {owner_b}; "
                    "数値 / 景色の向こうへ / トリビア must provide different information value.",
                )


def validate_data(data: dict[str, Any], filename: str, *, force: bool = False) -> list[str]:
    version = qa_version(data)
    if not force and version < CONTENT_QA_V2:
        return []
    errors: list[str] = []
    if version >= CONTENT_QA_V3:
        validate_travel_scale_v3(errors, filename, data)
        validate_signature_facts(errors, filename, data)
        validate_cross_section_topics(errors, filename, data)
    else:
        validate_travel_scale_v2(errors, filename, data)
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
        version = qa_version(data)
        if force or version >= CONTENT_QA_V2:
            checked += 1
            errors.extend(validate_data(data, path.name, force=True))

    if errors:
        print("Editorial Content QA: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Editorial Content QA: PASS ({checked} file(s); v2/v3 routed by contentQaVersion)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
