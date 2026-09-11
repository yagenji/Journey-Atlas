#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATHS = [
    ROOT / "data" / "atlas-destinations.json",
    ROOT / "data" / "atlas-destinations-editorial.json",
]
DEFAULT_MAX_PREVIEWS = 8


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def published_slugs() -> set[str]:
    result: set[str] = set()
    for path in REGISTRY_PATHS:
        payload = load_json(path, {})
        for row in payload.get("destinations", []):
            if isinstance(row, dict) and row.get("atlasPublished") and isinstance(row.get("slug"), str):
                result.add(row["slug"])
    return result


def review_index(root: Path) -> Path:
    return root / "reviews" / "index.json"


def normalize_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    entries = payload.get("previews") if isinstance(payload, dict) else []
    if not isinstance(entries, list):
        return []
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        slug = entry.get("slug")
        if not isinstance(slug, str) or not slug or slug in seen:
            continue
        seen.add(slug)
        normalized.append(entry)
    return normalized


def write_landing(root: Path, entries: list[dict[str, Any]]) -> None:
    links = "\n".join(
        f'<li><a href="{entry["reviewUrl"]}">{entry["slug"]}</a></li>'
        for entry in entries
        if isinstance(entry.get("reviewUrl"), str)
    )
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.html").write_text(
        "<!doctype html>\n"
        '<html lang="ja"><head><meta charset="utf-8">'
        '<meta name="robots" content="noindex,nofollow">'
        "<title>JOURNEY ATLAS Reviews</title></head><body>"
        "<h1>JOURNEY ATLAS Reviews</h1><ul>"
        f"{links}</ul></body></html>\n",
        encoding="utf-8",
    )


def stage_preview(
    root: Path,
    source: Path,
    slug: str,
    review_url: str,
    source_sha: str,
    max_previews: int,
) -> dict[str, Any]:
    if not source.exists() or not (source / "countries" / slug / "index.html").exists():
        raise FileNotFoundError(f"Targeted preview package is incomplete for {slug}: {source}")

    reviews_dir = root / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    index_path = review_index(root)
    payload = load_json(index_path, {"schemaVersion": 1, "previews": []})
    entries = normalize_entries(payload)

    published = published_slugs()
    entries = [entry for entry in entries if entry.get("slug") not in published or entry.get("slug") == slug]

    target_dir = reviews_dir / slug
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source, target_dir)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    current = {
        "slug": slug,
        "reviewUrl": review_url,
        "sourceSha": source_sha,
        "updatedAt": now,
    }
    entries = [entry for entry in entries if entry.get("slug") != slug]
    entries.insert(0, current)
    entries.sort(key=lambda item: str(item.get("updatedAt", "")), reverse=True)
    kept = entries[:max_previews]
    kept_slugs = {entry["slug"] for entry in kept}

    for child in reviews_dir.iterdir():
        if not child.is_dir():
            continue
        if child.name not in kept_slugs:
            shutil.rmtree(child)

    output = {
        "schemaVersion": 1,
        "updatedAt": now,
        "maxPreviews": max_previews,
        "previews": kept,
    }
    write_json(index_path, output)
    write_landing(root, kept)
    return output


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        source = temp_root / "dist"
        (source / "countries" / "alpha").mkdir(parents=True)
        (source / "countries" / "alpha" / "index.html").write_text("alpha", encoding="utf-8")
        (source / "data").mkdir(parents=True)
        site = temp_root / "site"
        result = stage_preview(
            site,
            source,
            "alpha",
            "https://example.test/reviews/alpha/countries/alpha/",
            "abc123",
            2,
        )
        assert result["previews"][0]["slug"] == "alpha"
        assert (site / "reviews" / "alpha" / "countries" / "alpha" / "index.html").exists()
        assert (site / "reviews" / "index.json").exists()
        assert (site / "index.html").exists()
    print("Review preview site manager self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    stage = sub.add_parser("stage")
    stage.add_argument("--root", required=True)
    stage.add_argument("--source", required=True)
    stage.add_argument("--slug", required=True)
    stage.add_argument("--review-url", required=True)
    stage.add_argument("--source-sha", required=True)
    stage.add_argument("--max-previews", type=int, default=DEFAULT_MAX_PREVIEWS)

    sub.add_parser("self-test")
    args = parser.parse_args()

    if args.command == "self-test":
        return self_test()

    result = stage_preview(
        Path(args.root),
        Path(args.source),
        args.slug,
        args.review_url,
        args.source_sha,
        args.max_previews,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
