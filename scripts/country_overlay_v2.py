#!/usr/bin/env python3
"""Country-only overlay helper for Publication Pipeline v2.

Long-running Country branches may contain stale shared templates/CSS/JS. This
helper keeps only target-Country data/assets/state plus slug-specific shared
metadata, then reapplies them on latest main for review/publish validation.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SHARED_METADATA = {
    "data/atlas-destinations.json",
    "data/atlas-destinations-editorial.json",
    "data/country-renewal-status.json",
    "data/theme-taxonomy.json",
}
FORBIDDEN_SHARED_EXACT = {"country.html", "index.html", "404.html", "_redirects"}
FORBIDDEN_SHARED_PREFIXES = ("assets/css/", "assets/js/", ".github/workflows/", "scripts/")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    else:
        body = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(body + "\n", encoding="utf-8")


def assert_scope(slug: str, base: str, head: str) -> None:
    changed = [p for p in git("diff", "--name-only", f"{base}...{head}").splitlines() if p]
    forbidden: list[str] = []
    for path in changed:
        if path in ALLOWED_SHARED_METADATA:
            continue
        if path in {f"data/countries/{slug}.json", f"ops/country-production/{slug}.json"}:
            continue
        if path.startswith(f"assets/images/{slug}/"):
            continue
        if path in FORBIDDEN_SHARED_EXACT or path.startswith(FORBIDDEN_SHARED_PREFIXES):
            forbidden.append(path)
    if forbidden:
        raise SystemExit(
            "Country PR may not carry shared UI/build/workflow changes; use a separate shared-system PR: "
            + ", ".join(forbidden)
        )
    print(f"{slug}: Country-only branch scope PASS")


def capture(slug: str, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for src in (ROOT / "data/countries" / f"{slug}.json", ROOT / "ops/country-production" / f"{slug}.json"):
        if not src.exists():
            raise SystemExit(f"Missing overlay source: {src.relative_to(ROOT)}")
        dst = out / src.relative_to(ROOT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    img = ROOT / "assets/images" / slug
    if img.exists():
        shutil.copytree(img, out / "assets/images" / slug)

    manifest = {"registryRows": {}, "themes": [], "statusRow": None}
    for name in ("atlas-destinations.json", "atlas-destinations-editorial.json"):
        path = ROOT / "data" / name
        if not path.exists():
            continue
        payload = load(path)
        row = next((r for r in payload.get("destinations", []) if isinstance(r, dict) and r.get("slug") == slug), None)
        if row is not None:
            manifest["registryRows"][name] = row
    theme_path = ROOT / "data/theme-taxonomy.json"
    if theme_path.exists():
        payload = load(theme_path)
        manifest["themes"] = [
            row.get("id") for row in payload.get("themes", [])
            if isinstance(row, dict) and slug in (row.get("examples") or [])
        ]
    status_path = ROOT / "data/country-renewal-status.json"
    if status_path.exists():
        payload = load(status_path)
        manifest["statusRow"] = next(
            (r for r in payload.get("countries", []) if isinstance(r, dict) and r.get("slug") == slug), None
        )
    write(out / "manifest.json", manifest)
    print(f"{slug}: overlay captured")


def apply(slug: str, source: Path) -> None:
    for rel in (Path("data/countries") / f"{slug}.json", Path("ops/country-production") / f"{slug}.json"):
        src = source / rel
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    img = source / "assets/images" / slug
    if img.exists():
        dst = ROOT / "assets/images" / slug
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(img, dst)

    manifest = load(source / "manifest.json")
    for name, saved in (manifest.get("registryRows") or {}).items():
        path = ROOT / "data" / name
        payload = load(path)
        rows = payload.setdefault("destinations", [])
        for index, row in enumerate(rows):
            if isinstance(row, dict) and row.get("slug") == slug:
                rows[index] = saved
                break
        else:
            rows.append(saved)
        write(path, payload, compact=True)

    theme_path = ROOT / "data/theme-taxonomy.json"
    if theme_path.exists():
        payload = load(theme_path)
        wanted = set(manifest.get("themes") or [])
        for row in payload.get("themes", []):
            if not isinstance(row, dict):
                continue
            examples = [value for value in (row.get("examples") or []) if value != slug]
            if row.get("id") in wanted:
                examples.append(slug)
            row["examples"] = examples
        write(theme_path, payload)

    saved_status = manifest.get("statusRow")
    status_path = ROOT / "data/country-renewal-status.json"
    if isinstance(saved_status, dict) and status_path.exists():
        payload = load(status_path)
        rows = payload.setdefault("countries", [])
        for index, row in enumerate(rows):
            if isinstance(row, dict) and row.get("slug") == slug:
                rows[index] = saved_status
                break
        else:
            rows.append(saved_status)
        write(status_path, payload, compact=True)
    print(f"{slug}: overlay applied on latest main")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("assert-scope"); p.add_argument("slug"); p.add_argument("base"); p.add_argument("head")
    p = sub.add_parser("capture"); p.add_argument("slug"); p.add_argument("out")
    p = sub.add_parser("apply"); p.add_argument("slug"); p.add_argument("source")
    args = parser.parse_args()
    if args.command == "assert-scope":
        assert_scope(args.slug, args.base, args.head)
    elif args.command == "capture":
        capture(args.slug, Path(args.out))
    else:
        apply(args.slug, Path(args.source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
