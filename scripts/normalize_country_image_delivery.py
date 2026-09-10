#!/usr/bin/env python3
"""Normalize Country Hero / Scene / Taste delivery without changing visual content.

Policy:
- Hero: keep current aspect ratio, never upscale, cap width at 1536 px when the
  resulting height remains >= the existing HERO_MIN requirement, and deliver as
  high-quality WebP.
- Scene / Taste: for valid 3:2 assets that are at least 1200x800, normalize to
  exactly 1200x800 and deliver as high-quality WebP.
- Already-compliant WebP assets are left byte-for-byte unchanged.
- Maps and unrelated assets are never touched.
- Country JSON references are updated only when an extension changes, using
  literal path replacement so original formatting/order is preserved.
- Published destination registry Hero references are kept exactly aligned with
  Country `hero.image`, again by literal replacement rather than reserialization.

Use --audit to report work without modifying files. Use --apply to write the
normalized assets and synchronize Country/registry image references.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATHS = [
    ROOT / "data" / "atlas-destinations.json",
    ROOT / "data" / "atlas-destinations-editorial.json",
]
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SCENE_TARGET = (1200, 800)
TASTE_TARGET = (1200, 800)
HERO_MAX_WIDTH = 1536
HERO_MIN = (1200, 760)
RATIO_3_2 = 1.5
RATIO_TOLERANCE = 0.015
WEBP_QUALITY = 92


@dataclass(frozen=True)
class AssetUse:
    slug: str
    role: str
    asset: str


@dataclass(frozen=True)
class Plan:
    source: str
    target: str
    roles: tuple[str, ...]
    old_size: tuple[int, int]
    new_size: tuple[int, int]
    old_bytes: int
    reason: str


@dataclass(frozen=True)
class RegistryHeroMismatch:
    registry: Path
    slug: str
    current: str
    expected: str


def reviewable_slugs() -> list[str]:
    slugs: list[str] = []
    seen: set[str] = set()
    for registry_path in REGISTRY_PATHS:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        for item in registry.get("destinations", []):
            slug = item.get("slug")
            if not slug or slug in seen:
                continue
            country_path = COUNTRY_DIR / f"{slug}.json"
            if not country_path.exists():
                continue
            data = json.loads(country_path.read_text(encoding="utf-8"))
            if data.get("schemaVersion") == 2:
                seen.add(slug)
                slugs.append(slug)
    return slugs


def country_uses(slug: str, data: dict) -> list[AssetUse]:
    uses: list[AssetUse] = []
    hero = data.get("hero", {}).get("image")
    if isinstance(hero, str):
        uses.append(AssetUse(slug, "hero", hero))
    for index, scene in enumerate(data.get("scenes", []), 1):
        image = scene.get("image") if isinstance(scene, dict) else None
        if isinstance(image, str):
            uses.append(AssetUse(slug, f"scene:{index}", image))
    taste = data.get("taste", {})
    if isinstance(taste, dict):
        for index, item in enumerate(taste.get("items", []), 1):
            image = item.get("image") if isinstance(item, dict) else None
            if isinstance(image, str):
                uses.append(AssetUse(slug, f"taste:{index}", image))
    return uses


def all_uses(slugs: Iterable[str]) -> dict[str, list[AssetUse]]:
    grouped: dict[str, list[AssetUse]] = {}
    for slug in slugs:
        path = COUNTRY_DIR / f"{slug}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for use in country_uses(slug, data):
            if Path(use.asset).suffix.lower() not in RASTER_SUFFIXES:
                continue
            grouped.setdefault(use.asset, []).append(use)
    return grouped


def published_registry_hero_mismatches() -> list[RegistryHeroMismatch]:
    mismatches: list[RegistryHeroMismatch] = []
    for registry_path in REGISTRY_PATHS:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        for item in registry.get("destinations", []):
            if not item.get("atlasPublished"):
                continue
            slug = item.get("slug")
            if not isinstance(slug, str) or not slug:
                continue
            country_path = COUNTRY_DIR / f"{slug}.json"
            if not country_path.exists():
                continue
            country = json.loads(country_path.read_text(encoding="utf-8"))
            if country.get("schemaVersion") != 2:
                continue
            expected = country.get("hero", {}).get("image")
            current = item.get("image")
            if not isinstance(expected, str) or not expected:
                continue
            if current == expected:
                continue
            if not isinstance(current, str) or not current:
                raise ValueError(f"Published registry image is missing for {slug}: {registry_path.name}")
            mismatches.append(
                RegistryHeroMismatch(
                    registry=registry_path,
                    slug=slug,
                    current=current,
                    expected=expected,
                )
            )
    return mismatches


def sync_published_registry_heroes() -> int:
    mismatches = published_registry_hero_mismatches()
    by_registry: dict[Path, list[RegistryHeroMismatch]] = {}
    for mismatch in mismatches:
        by_registry.setdefault(mismatch.registry, []).append(mismatch)

    updated_count = 0
    for registry_path, entries in by_registry.items():
        text = registry_path.read_text(encoding="utf-8")
        updated = text
        for entry in entries:
            old_token = json.dumps(entry.current, ensure_ascii=False)
            new_token = json.dumps(entry.expected, ensure_ascii=False)
            occurrences = updated.count(old_token)
            if occurrences != 1:
                raise ValueError(
                    f"Refusing ambiguous registry replacement for {entry.slug}: "
                    f"{entry.current!r} occurs {occurrences} times in {registry_path.name}"
                )
            updated = updated.replace(old_token, new_token, 1)
            updated_count += 1
        if updated != text:
            registry_path.write_text(updated, encoding="utf-8")
    return updated_count


def image_info(path: Path) -> tuple[int, int, str]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            fmt = (image.format or path.suffix.lstrip(".")).upper()
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"decode failed for {path}: {exc}") from exc
    return width, height, fmt


def target_for(asset: str, uses: list[AssetUse]) -> tuple[tuple[int, int], str] | None:
    path = ROOT / asset
    if not path.exists():
        raise FileNotFoundError(asset)
    width, height, _fmt = image_info(path)
    roles = {use.role.split(":", 1)[0] for use in uses}
    if len(roles) != 1:
        raise ValueError(f"Asset is reused across incompatible roles: {asset}: {sorted(roles)}")
    role = next(iter(roles))
    suffix = path.suffix.lower()

    if role == "hero":
        new_width, new_height = width, height
        if width > HERO_MAX_WIDTH:
            scale = HERO_MAX_WIDTH / width
            candidate = (HERO_MAX_WIDTH, max(1, round(height * scale)))
            if candidate[0] >= HERO_MIN[0] and candidate[1] >= HERO_MIN[1]:
                new_width, new_height = candidate
        needs_resize = (new_width, new_height) != (width, height)
        needs_format = suffix != ".webp"
        if not needs_resize and not needs_format:
            return None
        reason = "+".join(filter(None, ["resize" if needs_resize else "", "webp" if needs_format else ""]))
        return (new_width, new_height), reason

    if role in {"scene", "taste"}:
        ratio = width / height if height else 0
        target = SCENE_TARGET if role == "scene" else TASTE_TARGET
        valid_for_target = (
            width >= target[0]
            and height >= target[1]
            and math.isclose(ratio, RATIO_3_2, abs_tol=RATIO_TOLERANCE)
        )
        new_size = target if valid_for_target else (width, height)
        needs_resize = new_size != (width, height)
        # Do not churn legacy undersized/irregular assets just for extension.
        needs_format = suffix != ".webp" and valid_for_target
        if not needs_resize and not needs_format:
            return None
        reason = "+".join(filter(None, ["resize" if needs_resize else "", "webp" if needs_format else ""]))
        return new_size, reason

    return None


def build_plan(slugs: list[str]) -> list[Plan]:
    plans: list[Plan] = []
    for asset, uses in sorted(all_uses(slugs).items()):
        target_spec = target_for(asset, uses)
        if not target_spec:
            continue
        new_size, reason = target_spec
        source_path = ROOT / asset
        width, height, _fmt = image_info(source_path)
        target_path = source_path.with_suffix(".webp")
        if target_path != source_path and target_path.exists():
            raise FileExistsError(f"Refusing to overwrite existing target: {target_path.relative_to(ROOT)}")
        plans.append(
            Plan(
                source=asset,
                target=target_path.relative_to(ROOT).as_posix(),
                roles=tuple(sorted(f"{u.slug}:{u.role}" for u in uses)),
                old_size=(width, height),
                new_size=new_size,
                old_bytes=source_path.stat().st_size,
                reason=reason,
            )
        )
    return plans


def webp_save(source: Path, target: Path, size: tuple[int, int]) -> int:
    resampling = getattr(Image, "Resampling", Image)
    with Image.open(source) as image:
        image.load()
        icc = image.info.get("icc_profile")
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
        if image.size != size:
            image = image.resize(size, resampling.LANCZOS)
        save_kwargs: dict[str, object] = {
            "format": "WEBP",
            "quality": WEBP_QUALITY,
            "method": 6,
        }
        if icc:
            save_kwargs["icc_profile"] = icc
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp")
        image.save(tmp, **save_kwargs)
    # Full decode before accepting the replacement.
    with Image.open(tmp) as check:
        check.load()
        if check.size != size or (check.format or "").upper() != "WEBP":
            tmp.unlink(missing_ok=True)
            raise ValueError(f"normalized output verification failed: {target}")
    os.replace(tmp, target)
    return target.stat().st_size


def apply(plans: list[Plan], slugs: list[str]) -> tuple[int, int, int]:
    replacements = {plan.source: plan.target for plan in plans if plan.source != plan.target}
    before = sum(plan.old_bytes for plan in plans)
    after = 0

    for plan in plans:
        source = ROOT / plan.source
        target = ROOT / plan.target
        new_bytes = webp_save(source, target, plan.new_size)
        after += new_bytes
        if target != source:
            source.unlink()

    if replacements:
        for slug in slugs:
            path = COUNTRY_DIR / f"{slug}.json"
            text = path.read_text(encoding="utf-8")
            updated = text
            for old, new in replacements.items():
                quoted_old = json.dumps(old, ensure_ascii=False)
                quoted_new = json.dumps(new, ensure_ascii=False)
                updated = updated.replace(quoted_old, quoted_new)
            if updated != text:
                path.write_text(updated, encoding="utf-8")

    registry_updates = sync_published_registry_heroes()
    return before, after, registry_updates


def human_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB"]
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{value} B"


def print_plan(plans: list[Plan]) -> None:
    by_role: dict[str, int] = {"hero": 0, "scene": 0, "taste": 0}
    total = 0
    for plan in plans:
        if ":hero" in plan.roles[0]:
            by_role["hero"] += 1
        elif ":scene:" in plan.roles[0]:
            by_role["scene"] += 1
        elif ":taste:" in plan.roles[0]:
            by_role["taste"] += 1
        total += plan.old_bytes
        print(
            f"{plan.source} -> {plan.target} | {plan.old_size[0]}x{plan.old_size[1]} -> "
            f"{plan.new_size[0]}x{plan.new_size[1]} | {human_bytes(plan.old_bytes)} | {plan.reason} | "
            f"{', '.join(plan.roles)}"
        )
    print(
        f"PLAN assets={len(plans)} hero={by_role['hero']} scene={by_role['scene']} taste={by_role['taste']} "
        f"source_bytes={human_bytes(total)}"
    )


def audit_delivery(slugs: list[str]) -> list[str]:
    errors: list[str] = []
    for asset, uses in sorted(all_uses(slugs).items()):
        path = ROOT / asset
        width, height, fmt = image_info(path)
        roles = {use.role.split(":", 1)[0] for use in uses}
        if len(roles) != 1:
            errors.append(f"mixed roles: {asset}: {sorted(roles)}")
            continue
        role = next(iter(roles))
        if role == "hero":
            if width > HERO_MAX_WIDTH and round(height * HERO_MAX_WIDTH / width) >= HERO_MIN[1]:
                errors.append(f"oversized hero: {asset} ({width}x{height})")
            if fmt != "WEBP":
                errors.append(f"hero is not WebP: {asset} ({fmt})")
        elif role in {"scene", "taste"}:
            ratio = width / height if height else 0
            if width >= 1200 and height >= 800 and math.isclose(ratio, RATIO_3_2, abs_tol=RATIO_TOLERANCE):
                if (width, height) != (1200, 800):
                    errors.append(f"oversized {role}: {asset} ({width}x{height})")
                if fmt != "WEBP":
                    errors.append(f"{role} is not WebP: {asset} ({fmt})")

    for mismatch in published_registry_hero_mismatches():
        errors.append(
            f"registry hero mismatch: {mismatch.slug}: "
            f"{mismatch.current!r} != {mismatch.expected!r} ({mismatch.registry.name})"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    slugs = reviewable_slugs()
    plans = build_plan(slugs)
    print_plan(plans)

    if args.audit:
        errors = audit_delivery(slugs)
        print(f"AUDIT reviewable_countries={len(slugs)} issues={len(errors)}")
        for error in errors:
            print(f"- {error}")
        return 1 if errors else 0

    before, after, registry_updates = apply(plans, slugs)
    errors = audit_delivery(slugs)
    saved = before - after
    pct = (saved / before * 100) if before else 0.0
    print(
        f"APPLIED assets={len(plans)} before={human_bytes(before)} after={human_bytes(after)} "
        f"saved={human_bytes(saved)} ({pct:.1f}%) registry_updates={registry_updates}"
    )
    if errors:
        print(f"POST-AUDIT issues={len(errors)}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"POST-AUDIT reviewable_countries={len(slugs)} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
