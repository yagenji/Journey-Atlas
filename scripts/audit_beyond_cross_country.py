#!/usr/bin/env python3
"""One-shot horizontal editorial audit for Beyond the Scenery (atlasExtras).

This script is intentionally review-oriented: heuristic flags identify candidates,
not automatic FAILs. It prints all items so the final judgment can be made by
reading the Country content. No files are modified.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
DESTINATIONS = ROOT / "data" / "atlas-destinations.json"

NOISE = {
    "the", "and", "of", "in", "at", "to", "a", "an", "for", "from", "with",
    "country", "national", "world", "heritage", "unesco", "site", "sites",
    "city", "town", "village", "region", "area", "land", "landscape", "culture",
    "history", "historic", "traditional", "tradition", "local", "life", "road",
    "mount", "mountain", "lake", "river", "sea", "island", "islands", "park",
}
PRACTICAL_JA = (
    "予約", "入場", "営業時間", "チケット", "現金", "両替", "支払い", "SIM", "eSIM",
    "コンセント", "運転", "左側通行", "右側通行", "レンタカー", "空港", "乗り換え",
    "所要時間", "国境", "ビザ", "査証", "持ち物", "服装", "アクセス", "行き方",
)
PROFILE_JA = (
    "人口", "面積", "首都", "通貨", "公用語", "言語", "人口密度", "国土", "国境を接する",
)
DESIGNATION_JA = ("世界遺産", "ユネスコ", "UNESCO", "登録", "指定", "認定")


def clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def ascii_tokens(value: object) -> set[str]:
    text = clean(value).lower().replace("’", "'")
    parts = re.findall(r"[a-z0-9]+", text)
    return {p for p in parts if len(p) >= 3 and p not in NOISE}


def strong_token_overlap(a: object, b: object) -> bool:
    ta = ascii_tokens(a)
    tb = ascii_tokens(b)
    if not ta or not tb:
        return False
    shared = ta & tb
    if len(shared) >= 2:
        return True
    if len(shared) == 1:
        token = next(iter(shared))
        return len(token) >= 6 and (ta <= tb or tb <= ta)
    return False


def jp_components(value: object) -> set[str]:
    text = clean(value)
    parts = re.split(r"[\s/／・、,（）()\-–—]+", text)
    return {
        p.strip()
        for p in parts
        if len(p.strip()) >= 3 and not re.fullmatch(r"[A-Za-z0-9 .'-]+", p.strip())
    }


def destination_slugs() -> list[str]:
    data = json.loads(DESTINATIONS.read_text(encoding="utf-8"))
    return [row["slug"] for row in data.get("destinations", []) if row.get("slug")]


def scene_overlap(extra: dict, data: dict) -> list[str]:
    hay = " ".join((clean(extra.get("topicKey")), clean(extra.get("title")), clean(extra.get("text"))))
    hits: list[str] = []
    for scene in data.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        sid = clean(scene.get("id"))
        names = [clean(scene.get("name")), clean(scene.get("nameLocal")), clean(scene.get("mapLabel"))]
        if sid and strong_token_overlap(extra.get("topicKey"), sid):
            hits.append(sid)
            continue
        components = set()
        for name in names:
            components |= jp_components(name)
        if any(comp in hay for comp in components):
            hits.append(sid or names[0])
    return sorted(set(hits))


def hero_overlap(extra: dict, data: dict) -> bool:
    hero = data.get("hero", {}) if isinstance(data.get("hero"), dict) else {}
    hay = " ".join((clean(extra.get("topicKey")), clean(extra.get("title")), clean(extra.get("text"))))
    location = clean(hero.get("location"))
    if strong_token_overlap(extra.get("topicKey"), location):
        return True
    return any(comp in hay for comp in jp_components(location))


def section_topic_overlap(extra: dict, data: dict, section: str) -> list[str]:
    key = clean(extra.get("topicKey"))
    hits: list[str] = []
    for other in data.get(section, []):
        if not isinstance(other, dict):
            continue
        other_key = clean(other.get("topicKey"))
        if key and other_key and strong_token_overlap(key, other_key):
            hits.append(other_key)
    return hits


def taste_overlap(extra: dict, data: dict) -> list[str]:
    hay = " ".join((clean(extra.get("title")), clean(extra.get("text"))))
    hits: list[str] = []
    for item in data.get("taste", []):
        if not isinstance(item, dict):
            continue
        names = [clean(item.get(k)) for k in ("name", "nameJa", "nameEn", "title", "dish")]
        for name in names:
            if not name:
                continue
            if any(comp in hay for comp in jp_components(name)):
                hits.append(name)
                break
            if strong_token_overlap(extra.get("topicKey"), name):
                hits.append(name)
                break
    return sorted(set(hits))


def flags_for(extra: dict, data: dict, extras: list[dict]) -> list[str]:
    flags: list[str] = []
    title = clean(extra.get("title"))
    text = clean(extra.get("text"))
    key = clean(extra.get("topicKey"))
    points = extra.get("points")

    if not key:
        flags.append("MISSING_TOPIC_KEY")
    if not clean(extra.get("themeEn")):
        flags.append("MISSING_THEME")
    if len(title) < 8 or len(text) < 30:
        flags.append("THIN_COPY")
    if not isinstance(points, list) or len([p for p in points if clean(p)]) < 2:
        flags.append("THIN_POINTS")

    same_key = sum(1 for item in extras if clean(item.get("topicKey")) == key and key)
    if same_key > 1:
        flags.append("DUPLICATE_TOPIC_KEY")

    sig = section_topic_overlap(extra, data, "signatureFacts")
    tri = section_topic_overlap(extra, data, "travelTrivia")
    if sig:
        flags.append("OVERLAP_SIGNATURE:" + ",".join(sig))
    if tri:
        flags.append("OVERLAP_TRIVIA:" + ",".join(tri))

    scenes = scene_overlap(extra, data)
    if scenes:
        flags.append("SCENE_SUBJECT:" + ",".join(scenes))
    if hero_overlap(extra, data):
        flags.append("HERO_SUBJECT")

    taste = taste_overlap(extra, data)
    if taste:
        flags.append("TASTE_SUBJECT:" + ",".join(taste))

    hay = f"{title} {text}"
    if any(term in hay for term in PRACTICAL_JA):
        flags.append("PRACTICAL_REVIEW")
    if any(term in hay for term in PROFILE_JA):
        flags.append("PROFILE_REVIEW")
    if any(term in hay for term in DESIGNATION_JA):
        if "世界遺産" in title or "ユネスコ" in title or "UNESCO" in title or "登録" in title:
            flags.append("DESIGNATION_LED")
        else:
            flags.append("DESIGNATION_MENTION")
    return flags


def main() -> int:
    slugs = destination_slugs()
    rows: list[dict] = []
    country_issues: list[str] = []

    for slug in slugs:
        path = COUNTRY_DIR / f"{slug}.json"
        if not path.exists():
            country_issues.append(f"MISSING_JSON:{slug}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        extras = data.get("atlasExtras", [])
        if not isinstance(extras, list):
            country_issues.append(f"BAD_ATLAS_EXTRAS:{slug}")
            continue
        if len(extras) != 6:
            country_issues.append(f"COUNT:{slug}:{len(extras)}")
        themes = [clean(x.get("themeEn")) for x in extras if isinstance(x, dict) and clean(x.get("themeEn"))]
        if len(set(themes)) < 3:
            country_issues.append(f"NARROW_THEME_BREADTH:{slug}:{','.join(sorted(set(themes)))}")

        for idx, extra in enumerate(extras, 1):
            if not isinstance(extra, dict):
                rows.append({"slug": slug, "index": idx, "flags": ["BAD_ITEM"]})
                continue
            flags = flags_for(extra, data, [x for x in extras if isinstance(x, dict)])
            rows.append({
                "slug": slug,
                "index": idx,
                "topicKey": clean(extra.get("topicKey")),
                "themeEn": clean(extra.get("themeEn")),
                "title": clean(extra.get("title")),
                "text": clean(extra.get("text")),
                "flags": flags,
            })

    print(f"BEYOND_AUDIT|countries={len(slugs)}|items={len(rows)}")
    print(f"BEYOND_COUNTRY_ISSUES|count={len(country_issues)}")
    for issue in country_issues:
        print(f"BEYOND_COUNTRY|{issue}")

    flagged = [row for row in rows if row["flags"]]
    print(f"BEYOND_FLAGGED|count={len(flagged)}")
    counts = Counter(flag.split(":", 1)[0] for row in flagged for flag in row["flags"])
    for flag, count in sorted(counts.items()):
        print(f"BEYOND_FLAG_COUNT|{flag}|{count}")

    for row in rows:
        flags = ",".join(row["flags"]) if row["flags"] else "-"
        text = row.get("text", "").replace("\n", " ")
        print(
            f"BEYOND|{row['slug']}|{row['index']}|{row.get('themeEn','')}|"
            f"{row.get('topicKey','')}|flags={flags}|title={row.get('title','')}|text={text}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
