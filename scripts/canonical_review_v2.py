#!/usr/bin/env python3
"""Guard a v2 Country's pre-approval integration into its canonical review URL.

This script does not publish a Country. A PASS here is not user approval.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "https://atlas.yagenji.com/countries/{slug}/"
ICON_REPLACEMENTS = {"mountain": "landscape", "nature": "leaf"}


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict[str, Any], *, compact: bool = False) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":") if compact else None,
                         indent=None if compact else 2)
    path.write_text(payload + "\n", encoding="utf-8")


def paths(slug: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("Invalid canonical Country slug")
    return ROOT / "data/countries" / f"{slug}.json", ROOT / "ops/country-production" / f"{slug}.json"


def registry_row(slug: str) -> dict[str, Any]:
    registry = read(ROOT / "data/atlas-destinations.json")
    rows = [row for row in registry.get("destinations", []) if row.get("slug") == slug]
    if len(rows) != 1:
        raise ValueError(f"{slug}: canonical registry must contain exactly one row")
    return rows[0]


def validate_source(slug: str, country: dict[str, Any], state: dict[str, Any]) -> None:
    if country.get("schemaVersion") != 2 or country.get("publicationPipelineVersion") != 2:
        raise ValueError(f"{slug}: not a v2 review Country")
    if country.get("slug") != slug or state.get("productionProtocolId") != "2.0":
        raise ValueError(f"{slug}: Country / Production State identity mismatch")
    if registry_row(slug).get("atlasPublished") is not False:
        raise ValueError(f"{slug}: review cannot change the publication registry")
    if (state.get("publication") or {}).get("atlasPublished") is not False:
        raise ValueError(f"{slug}: review cannot use a published Production State")
    if (state.get("finalApproval") or {}).get("state") == "APPROVED":
        raise ValueError(f"{slug}: final approval is a separate, later gate")
    hero = state.get("hero") or {}
    if hero.get("state") != "APPROVED":
        raise ValueError(f"{slug}: Hero not approved")
    for key, size in (("scenes", 8), ("taste", 4)):
        items = state.get(key) or []
        if len(items) != size or any(item.get("state") != "APPROVED" for item in items):
            raise ValueError(f"{slug}: {key} not fully approved")
    for key in ("sceneBatchReview", "tasteBatchReview"):
        if (state.get(key) or {}).get("approval") != "APPROVED":
            raise ValueError(f"{slug}: {key} has no batch approval")
    handoff = state.get("assetHandoff") or {}
    if handoff.get("state") != "PASS" or handoff.get("verifiedRasterCount") != 13:
        raise ValueError(f"{slug}: 13-raster handoff not verified")
    preview = state.get("reviewPreview") or {}
    if preview.get("state") != "DONE" or preview.get("browserQa") != "PASS":
        raise ValueError(f"{slug}: existing review QA has not passed")


def normalize_metadata(slug: str, country: dict[str, Any]) -> list[str]:
    """Repair only verified mechanical contract mismatches, never imagery/content."""
    import normalize_country_region_labels as region

    tax = read(ROOT / "data/region-taxonomy.json")
    iso2 = registry_row(slug).get("iso2")
    expected = region.expected_region_by_iso2(tax).get(iso2)
    if not expected:
        raise ValueError(f"{slug}: no authoritative taxonomy region")
    changes: list[str] = []
    normalized = region.normalized_region(country, expected)
    if country.get("region") != normalized:
        country["region"] = normalized
        changes.append("region label")
    # These two explicit aliases were found to reference nonexistent sprite IDs.
    # Do not silently replace any other missing icon; fail the normal icon audit.
    for section in ("travelTrivia", "signatureFacts"):
        for index, item in enumerate(country.get(section) or []):
            old = item.get("icon")
            if old in ICON_REPLACEMENTS:
                item["icon"] = ICON_REPLACEMENTS[old]
                changes.append(f"{section}[{index}].icon")
    return changes


def prepare(slug: str) -> None:
    country_path, state_path = paths(slug)
    country, state = read(country_path), read(state_path)
    validate_source(slug, country, state)
    existing = state.get("reviewDeployment") or {}
    if existing.get("state") == "DONE" and existing.get("productionVerification") == "LIVE_BROWSER_QA_PASS":
        print(f"{slug}: canonical review already verified; no change")
        return
    changes = normalize_metadata(slug, country)
    if changes:
        write(country_path, country, compact=True)
    state["reviewDeployment"] = {
        "state": "DEPLOYING",
        "url": CANONICAL.format(slug=slug),
        "productionVerification": "PENDING",
        "atlasPublished": False,
    }
    state["next"] = {"action": "VERIFY_CANONICAL_REVIEW", "asset": None}
    write(state_path, state)
    print(f"{slug}: staged unpublished canonical review; corrected {', '.join(changes) or 'no metadata'}")


def verified(slug: str) -> None:
    country_path, state_path = paths(slug)
    country, state = read(country_path), read(state_path)
    validate_source(slug, country, state)
    deployment = state.get("reviewDeployment") or {}
    if deployment.get("url") != CANONICAL.format(slug=slug):
        raise ValueError(f"{slug}: canonical URL mismatch")
    if deployment.get("state") != "DEPLOYING" or deployment.get("atlasPublished") is not False:
        raise ValueError(f"{slug}: canonical review deployment was not safely staged")
    deployment.update({"state": "DONE", "productionVerification": "LIVE_BROWSER_QA_PASS",
                       "browserQa": "PASS", "verifiedAt": datetime.now(timezone.utc).isoformat()})
    state["reviewDeployment"] = deployment
    state["next"] = {"action": "REVIEW_CANONICAL_URL", "asset": None}
    write(state_path, state)
    print(f"{slug}: canonical live QA recorded; final approval remains pending")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verified"))
    parser.add_argument("slug")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.slug)
    else:
        verified(args.slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())