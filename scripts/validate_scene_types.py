#!/usr/bin/env python3
"""Every named Hero and Scene carries 1-2 scene types from data/scene-taxonomy.json.

The scene index on the top page and the similar-scene suggestions on Country
pages are built from these types, so a Scene added without one would silently
drop out of both. Run with --list to print the types for one page.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "data/scene-taxonomy.json"


def load_types() -> dict[str, str]:
    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    types: dict[str, str] = {}
    groups = set()
    for group in taxonomy["groups"]:
        if group["id"] in groups:
            raise ValueError(f"Duplicate scene type group: {group['id']}")
        groups.add(group["id"])
        for item in group["types"]:
            if item["id"] in types:
                raise ValueError(f"Duplicate scene type: {item['id']}")
            types[item["id"]] = item["label"]
    return types


def pages():
    for path in sorted((ROOT / "data/countries").glob("*.json")):
        yield path
    for path in sorted((ROOT / "data/regions").glob("*/*.json")):
        yield path


def entries(data: dict):
    hero = data.get("hero") or {}
    if str(hero.get("name") or "").strip():
        yield "hero", hero
    for scene in data.get("scenes") or []:
        if str(scene.get("name") or "").strip():
            yield scene.get("id", "?"), scene


def check(path: Path, types: dict[str, str]) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    for scene_id, entry in entries(data):
        value = entry.get("sceneTypes")
        where = f"{path.relative_to(ROOT)} {scene_id}"
        if not isinstance(value, list) or not 1 <= len(value) <= 2:
            problems.append(f"{where}: needs sceneTypes with 1-2 types")
            continue
        if len(set(value)) != len(value):
            problems.append(f"{where}: repeated scene type")
        unknown = [item for item in value if item not in types]
        if unknown:
            problems.append(f"{where}: unknown scene type {unknown}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Country or Region JSON (default: all)")
    args = parser.parse_args()
    types = load_types()
    targets = [path.resolve() for path in args.paths] or list(pages())
    problems = [problem for path in targets for problem in check(path, types)]
    for problem in problems:
        print(f"ERROR: {problem}")
    if problems:
        print(f"{len(problems)} scene type problem(s). Types are listed in data/scene-taxonomy.json.")
        return 1
    print(f"Scene types OK ({len(targets)} page(s), {len(types)} types).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
