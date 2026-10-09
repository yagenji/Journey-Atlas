#!/usr/bin/env python3
"""Temporary one-shot Travel Scale route-loop remediation for the 202-destination audit."""
from __future__ import annotations

import json
import re
from collections import Counter
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
    for word in ("滞在", "周辺", "中心部"):
        value = value.replace(word, "")
    return value.strip()


def first_route_node(text: str) -> str:
    m = re.search(r"例[:：]\s*(.+?)(?:。|$)", text)
    if not m:
        return ""
    route = m.group(1).strip()
    if re.search(r"[→➡➜]", route):
        return semantic_key(ARROW_RE.split(route)[0])
    if "＋" in route:
        return semantic_key(route.split("＋", 1)[0])
    return ""


def returned_to_base(first: str, later: str) -> bool:
    key = semantic_key(first)
    later_key = semantic_key(later)
    if key and key in later_key:
        return True
    # Treat compound gateway labels such as 「香港島・九龍」 as returned when
    # one concrete component appears later in the route.
    for part in re.split(r"[・/／]", key):
        part = part.strip()
        if len(part) >= 2 and part in later_key:
            return True
    return False


def make_loop(route: str, bases: set[str]) -> tuple[str, bool]:
    route = route.strip()
    if not route:
        return route, False

    if re.search(r"[→➡➜]", route):
        nodes = [clean_node(x) for x in ARROW_RE.split(route) if clean_node(x)]
        if len(nodes) < 2:
            return route, False
        first = nodes[0]
        first_key = semantic_key(first)
        later = " ".join(nodes[1:])
        if returned_to_base(first, later):
            return route, False
        # Only auto-close a route when its start is demonstrably a main base:
        # the Country capital, or the same starting point used in >=2 examples.
        # Everything else remains for human editorial review.
        if first_key not in bases:
            return route, False
        return f"{route} → {first}", True

    if "＋" in route:
        parts = [clean_node(x) for x in route.split("＋") if clean_node(x)]
        if 2 <= len(parts) <= 6 and all(len(x) <= 32 for x in parts):
            first_key = semantic_key(parts[0])
            if first_key in bases:
                return " → ".join(parts + [parts[0]]), True

    return route, False


def rewrite_text(text: str, bases: set[str]) -> tuple[str, bool]:
    m = re.search(r"(例[:：]\s*)(.+?)(。|$)", text)
    if not m:
        return text, False
    route = m.group(2).strip()
    new_route, changed = make_loop(route, bases)
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

        first_nodes = [first_route_node(item.get("text", "")) for item in items if isinstance(item, dict)]
        counts = Counter(node for node in first_nodes if node)
        bases = {node for node, count in counts.items() if count >= 2}
        capital = semantic_key(((data.get("capital") or {}).get("nameJa") or ""))
        if capital:
            bases.add(capital)

        replacements: list[tuple[str, str]] = []
        for index, item in enumerate(items, 1):
            old = item.get("text") if isinstance(item, dict) else None
            if not isinstance(old, str):
                continue
            new, changed = rewrite_text(old, bases)
            if changed:
                replacements.append((old, new))
            else:
                m = re.search(r"例[:：]\s*(.+)$", old)
                if m:
                    route = m.group(1).strip()
                    first_sentence = route.split("。", 1)[0]
                    if re.search(r"[→➡➜]", first_sentence):
                        nodes = [clean_node(x) for x in ARROW_RE.split(first_sentence) if clean_node(x)]
                        if len(nodes) >= 2 and not returned_to_base(nodes[0], " ".join(nodes[1:])):
                            skipped.append((slug, index, route))
                    elif "＋" in first_sentence:
                        parts = [clean_node(x) for x in first_sentence.split("＋") if clean_node(x)]
                        if len(parts) >= 2:
                            skipped.append((slug, index, route))
                    else:
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
