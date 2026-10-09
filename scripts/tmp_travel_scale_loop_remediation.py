#!/usr/bin/env python3
"""Temporary one-shot Travel Scale route-loop remediation for the 202-destination audit."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY = ROOT / "data" / "atlas-destinations.json"
ARROW_RE = re.compile(r"\s*[→➡➜]\s*")


def clean_node(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    return re.sub(r"[。．.!！?？、,;；:：]+$", "", value).strip()


def semantic_key(value: str) -> str:
    value = clean_node(value)
    value = re.sub(r"（.*?）", "", value)
    value = re.sub(r"\([^)]*\)", "", value)
    value = value.replace("滞在", "").replace("周辺", "").replace("中心部", "")
    return value.strip()


def make_loop(route: str) -> tuple[str, bool]:
    route = route.strip()
    if not route:
        return route, False

    if re.search(r"[→➡➜]", route):
        nodes = [clean_node(x) for x in ARROW_RE.split(route) if clean_node(x)]
        if len(nodes) < 2:
            return route, False
        first = nodes[0]
        first_key = semantic_key(first)
        # Already returns to the same base somewhere after departure, including
        # alternatives such as "A → B → A、または...".
        later = " ".join(semantic_key(x) for x in nodes[1:])
        if first_key and first_key in later:
            return route, False
        # A broad region/block is not a usable return point. Leave these for
        # explicit editorial review rather than inventing a destination.
        if any(word in first for word in ("周遊", "地域", "各地", "方面", "本土", "北部", "南部", "東部", "西部", "中央部", "市街地")):
            return route, False
        return f"{route} → {first}", True

    # Convert simple place lists into an actual route and close the loop.
    if "＋" in route:
        parts = [clean_node(x) for x in route.split("＋") if clean_node(x)]
        if 2 <= len(parts) <= 6 and all(len(x) <= 32 for x in parts):
            return " → ".join(parts + [parts[0]]), True

    return route, False


def rewrite_text(text: str) -> tuple[str, bool]:
    m = re.search(r"(例[:：]\s*)(.+?)(。|$)", text)
    if not m:
        return text, False
    route = m.group(2).strip()
    new_route, changed = make_loop(route)
    if not changed:
        return text, False
    return text[: m.start(2)] + new_route + text[m.end(2) :], True


def replace_json_string_once(raw: str, old: str, new: str, start: int) -> tuple[str, int]:
    old_token = json.dumps(old, ensure_ascii=False)
    new_token = json.dumps(new, ensure_ascii=False)
    idx = raw.find(old_token, start)
    if idx < 0:
        raise RuntimeError("Could not locate Travel Scale text token for targeted replacement")
    return raw[:idx] + new_token + raw[idx + len(old_token):], idx + len(new_token)


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    slugs = [row["slug"] for row in registry.get("destinations", []) if row.get("atlasPublished")]
    changed_files = 0
    changed_items = 0
    skipped = []

    for slug in slugs:
        path = COUNTRY_DIR / f"{slug}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        items = ((data.get("travelScale") or {}).get("items") or [])
        replacements: list[tuple[str, str]] = []
        for index, item in enumerate(items, 1):
            old = item.get("text") if isinstance(item, dict) else None
            if not isinstance(old, str):
                continue
            new, changed = rewrite_text(old)
            if changed:
                replacements.append((old, new))
            else:
                m = re.search(r"例[:：]\s*(.+)$", old)
                if m:
                    route = m.group(1).strip()
                    first_sentence = route.split("。", 1)[0]
                    nodes = [clean_node(x) for x in ARROW_RE.split(first_sentence) if clean_node(x)] if re.search(r"[→➡➜]", first_sentence) else []
                    if not nodes or (len(nodes) >= 2 and semantic_key(nodes[0]) not in " ".join(semantic_key(x) for x in nodes[1:])):
                        skipped.append((slug, index, route))

        if not replacements:
            continue
        raw = path.read_text(encoding="utf-8")
        travel_pos = raw.find('"travelScale"')
        if travel_pos < 0:
            raise RuntimeError(f"{slug}: travelScale token missing")
        cursor = travel_pos
        for old, new in replacements:
            raw, cursor = replace_json_string_once(raw, old, new, cursor)
        path.write_text(raw, encoding="utf-8")
        changed_files += 1
        changed_items += len(replacements)

    print(f"TRAVEL_SCALE_REMEDIATION changed_files={changed_files} changed_items={changed_items}")
    print(f"TRAVEL_SCALE_REMEDIATION_REVIEW remaining={len(skipped)}")
    for row in skipped:
        print("REVIEW|" + "|".join(str(x).replace("\n", " ") for x in row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
