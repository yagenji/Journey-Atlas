#!/usr/bin/env python3
"""Audit published Country Pages with optional legacy renewal metadata.

This script does not rewrite country content. The legacy renewal registry is
treated as optional metadata for Countries that were tracked by the old renewal
process; newly produced Countries are not required to add renewal-state rows.

The audit also prints every Signature Fact so horizontal editorial review can
compare all published Countries on the same basis. Heuristic flags are review
cues only; they do not fail publication by themselves.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "data" / "country-renewal-status.json"
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRIES = [
    ROOT / "data" / "atlas-destinations.json",
]
THEMES = ROOT / "data" / "theme-taxonomy.json"

HERITAGE_TERMS = ("世界遺産", "unesco", "world heritage")
HERITAGE_DETAIL_TERMS = (
    "登録", "構成資産", "構成要素", "ha", "ヘクタール", "km²", "平方キロ",
    "標高", "高さ", "長さ", "面積", "年", "件",
)
PROFILE_TERMS = ("人口密度", "人口", "国土面積", "面積", "population density", "population", "area")
FOREST_TERMS = ("森林", "樹林", "forest", "woodland")
TOPIC_NOISE = {
    "count", "counts", "number", "numbers", "share", "rate", "ratio", "percent",
    "percentage", "stat", "stats", "fact", "facts", "trivia", "history", "background",
    "overview", "story", "system", "culture", "context", "figure", "figures", "country",
    "national", "detail", "details", "today", "current",
}


def published_slugs() -> list[str]:
    out, seen = [], set()
    for path in REGISTRIES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("destinations", []):
            slug = item.get("slug")
            if item.get("atlasPublished") and slug and slug not in seen:
                seen.add(slug)
                out.append(slug)
    return out


def theme_counts() -> dict[str, list[str]]:
    data = json.loads(THEMES.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for theme in data.get("themes", []):
        label = theme.get("label") or theme.get("id") or "theme"
        for slug in theme.get("examples", []):
            out.setdefault(slug, []).append(label)
    return out


def clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def first_number(value: object) -> float | None:
    match = re.search(r"(\d[\d,]*(?:\.\d+)?)", clean(value))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def percentages(value: str) -> list[float]:
    return [float(part) for part in re.findall(r"(\d+(?:\.\d+)?)\s*%", value)]


def topic_tokens(value: object) -> set[str]:
    raw = {part for part in re.split(r"[-_\s]+", clean(value).lower()) if part and part not in TOPIC_NOISE}
    normalized: set[str] = set()
    if "world" in raw and "heritage" in raw:
        normalized.add("worldheritage")
        raw.discard("world")
        raw.discard("heritage")
    aliases = {
        "unesco": "worldheritage",
        "woodland": "forest",
        "forests": "forest",
        "nomadic": "nomad",
        "nomads": "nomad",
    }
    normalized.update(aliases.get(part, part) for part in raw)
    return {part for part in normalized if len(part) >= 3}


def cross_section_topic_keys(data: dict, section: str) -> list[tuple[str, set[str]]]:
    out: list[tuple[str, set[str]]] = []
    items = data.get(section, [])
    if not isinstance(items, list):
        return out
    for item in items:
        if not isinstance(item, dict):
            continue
        key = clean(item.get("topicKey"))
        tokens = topic_tokens(key)
        if key and tokens:
            out.append((key, tokens))
    return out


def signature_flags(data: dict, item: dict) -> list[str]:
    label = clean(item.get("label"))
    value = clean(item.get("value"))
    note = clean(item.get("note"))
    topic = clean(item.get("topicKey"))
    haystack = " ".join((topic, label, value, note)).lower()
    flags: list[str] = []

    heritage = any(term.lower() in haystack for term in HERITAGE_TERMS)
    if heritage:
        count = first_number(value)
        exceptional_count = item.get("exceptionalHeritageCount") is True and count is not None and count >= 25
        if exceptional_count:
            flags.append("HERITAGE_EXCEPTION_REVIEW")
        elif any(term.lower() in haystack for term in HERITAGE_DETAIL_TERMS):
            flags.append("HERITAGE_DESCRIPTION")
        else:
            flags.append("HERITAGE_RELATED")

    if any(term.lower() in haystack for term in PROFILE_TERMS) and item.get("exceptionalScale") is not True:
        flags.append("PROFILE_STAT")

    if any(term.lower() in haystack for term in FOREST_TERMS):
        pcts = percentages(" ".join((value, note)))
        extreme = bool(pcts) and all(pct <= 10 or pct >= 70 for pct in pcts)
        if item.get("exceptionalShare") is not True or not extreme:
            flags.append("FOREST_SHARE")

    sig_tokens = topic_tokens(topic)
    if sig_tokens:
        for section in ("atlasExtras", "travelTrivia"):
            for other_key, other_tokens in cross_section_topic_keys(data, section):
                shared = sig_tokens & other_tokens
                if not shared:
                    continue
                union = sig_tokens | other_tokens
                jaccard = len(shared) / max(1, len(union))
                subset = sig_tokens <= other_tokens or other_tokens <= sig_tokens
                strong_single = len(shared) == 1 and subset and len(next(iter(shared))) >= 5
                if len(shared) >= 2 or jaccard >= 0.60 or strong_single:
                    flags.append(f"TOPIC_OVERLAP:{section}:{other_key}")
                    break

    if not re.search(r"\d", value):
        flags.append("NO_NUMERIC_VALUE")
    return flags


def signature_rows(slug: str, data: dict) -> list[dict]:
    rows: list[dict] = []
    items = data.get("signatureFacts", [])
    if not isinstance(items, list):
        return rows
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        rows.append({
            "slug": slug,
            "index": index,
            "topicKey": clean(item.get("topicKey")),
            "label": clean(item.get("label")),
            "value": clean(item.get("value")),
            "note": clean(item.get("note")),
            "interestReason": clean(item.get("interestReason")),
            "flags": signature_flags(data, item),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    status = json.loads(STATUS.read_text(encoding="utf-8"))
    status_rows = status.get("countries", [])
    status_slugs = [row.get("slug") for row in status_rows]
    published = published_slugs()

    errors = []
    missing = sorted(set(published) - set(status_slugs))
    extra = sorted(set(status_slugs) - set(published))
    duplicates = sorted({slug for slug in status_slugs if status_slugs.count(slug) > 1 and slug})
    # New Country production no longer writes legacy renewal-state rows.
    # Missing legacy metadata is informational, not a publication failure.
    if extra:
        errors.append(f"renewal status contains non-published countries: {', '.join(extra)}")
    if duplicates:
        errors.append(f"renewal status contains duplicate slugs: {', '.join(duplicates)}")

    themes = theme_counts()
    rows = []
    signature_audit: list[dict] = []
    by_status = {row["slug"]: row for row in status_rows if row.get("slug")}
    for slug in published:
        path = COUNTRY_DIR / f"{slug}.json"
        if not path.exists():
            errors.append(f"published Country JSON missing: {slug}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        visible_facts = [f for f in data.get("facts", []) if f.get("label") != "地域"]
        row = {
            "slug": slug,
            "auditState": by_status.get(slug, {}).get("auditState") or "N/A",
            "renewalClass": by_status.get(slug, {}).get("renewalClass") or "N/A",
            "hardImageGate": bool(by_status.get(slug, {}).get("hardImageGate")),
            "visibleFacts": len(visible_facts),
            "scenes": len(data.get("scenes", [])),
            "encounters": len(data.get("encounters", [])),
            "beyond": len(data.get("atlasExtras", [])),
            "trivia": len(data.get("travelTrivia", [])),
            "themes": len(themes.get(slug, [])),
            "hasHero": bool(data.get("hero", {}).get("image")),
            "hasMap": bool(data.get("map", {}).get("svg")),
            "sourcesVerifiedAt": data.get("sourcesVerifiedAt"),
        }
        rows.append(row)
        signature_audit.extend(signature_rows(slug, data))

    if args.json:
        print(json.dumps(
            {
                "published": len(published),
                "rows": rows,
                "signatureFacts": signature_audit,
                "legacyUntracked": missing,
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        print(f"Published Country renewal audit: {len(published)} country page(s)")
        for row in rows:
            print(
                f"{row['slug']:<16} audit={row['auditState']:<7} class={row['renewalClass']:<12} "
                f"gate={'Y' if row['hardImageGate'] else 'N'} facts={row['visibleFacts']} scenes={row['scenes']} "
                f"enc={row['encounters']} beyond={row['beyond']} trivia={row['trivia']} themes={row['themes']}"
            )

        print(f"Signature Facts horizontal audit: {len(signature_audit)} item(s)")
        for item in signature_audit:
            flags = ",".join(item["flags"]) if item["flags"] else "-"
            note = item["note"].replace("\n", " ")
            reason = item["interestReason"].replace("\n", " ")
            print(
                f"SIG|{item['slug']}|{item['index']}|{item['label']}|{item['value']}|"
                f"flags={flags}|note={note}|interestReason={reason}"
            )

        flagged = [item for item in signature_audit if item["flags"]]
        print(f"Signature Facts heuristic review candidates: {len(flagged)} item(s)")
        for item in flagged:
            print(
                f"SIG_REVIEW|{item['slug']}|{item['index']}|{item['label']}|{item['value']}|"
                f"{','.join(item['flags'])}"
            )

        if missing:
            print("Legacy renewal metadata not required for:")
            for slug in missing:
                print(f"- {slug}")
        if errors:
            print("Registry errors:")
            for error in errors:
                print(f"- {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
