#!/usr/bin/env python3
"""JOURNEY ATLAS Publication Pipeline v2 helpers.

This module is deliberately opt-in. A Country is active only when its Country
JSON has ``publicationPipelineVersion: 2``. Existing Countries without that
field continue through the legacy Protocol 2 publication path unchanged.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
STATE_DIR = ROOT / "ops" / "country-production"
REGISTRY_PATHS = [
    ROOT / "data" / "atlas-destinations.json",
]
STATUS_PATH = ROOT / "data" / "country-renewal-status.json"
THEME_PATH = ROOT / "data" / "theme-taxonomy.json"
JST = timezone(timedelta(hours=9))


def now_iso() -> str:
    return datetime.now(JST).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], *, compact: bool = False) -> None:
    if compact:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def paths_for_slug(slug: str) -> tuple[Path, Path]:
    return COUNTRY_DIR / f"{slug}.json", STATE_DIR / f"{slug}.json"


def country_for_slug(slug: str) -> dict[str, Any]:
    country_path, _ = paths_for_slug(slug)
    if not country_path.exists():
        raise ValueError(f"Missing Country JSON: {country_path.relative_to(ROOT)}")
    return load_json(country_path)


def state_for_slug(slug: str) -> dict[str, Any]:
    _, state_path = paths_for_slug(slug)
    if not state_path.exists():
        raise ValueError(f"Missing Production State: {state_path.relative_to(ROOT)}")
    return load_json(state_path)


def is_active(slug: str) -> bool:
    try:
        return country_for_slug(slug).get("publicationPipelineVersion") == 2
    except ValueError:
        return False


def all_visuals_approved(state: dict[str, Any]) -> bool:
    hero = state.get("hero") if isinstance(state.get("hero"), dict) else {}
    scenes = state.get("scenes") if isinstance(state.get("scenes"), list) else []
    taste = state.get("taste") if isinstance(state.get("taste"), list) else []
    scene_review = state.get("sceneBatchReview") if isinstance(state.get("sceneBatchReview"), dict) else {}
    taste_review = state.get("tasteBatchReview") if isinstance(state.get("tasteBatchReview"), dict) else {}
    return (
        hero.get("state") == "APPROVED"
        and len(scenes) == 8
        and all(isinstance(item, dict) and item.get("state") == "APPROVED" for item in scenes)
        and len(taste) == 4
        and all(isinstance(item, dict) and item.get("state") == "APPROVED" for item in taste)
        and scene_review.get("approval") == "APPROVED"
        and taste_review.get("approval") == "APPROVED"
    )


def review_ready_errors(slug: str, state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not is_active(slug):
        errors.append("publicationPipelineVersion is not 2")
    if state.get("productionProtocolId") != "2.0":
        errors.append("productionProtocolId must be 2.0")
    if not all_visuals_approved(state):
        errors.append("Hero + 8 Scenes + 4 Taste assets must be batch-approved")
    handoff = state.get("assetHandoff") if isinstance(state.get("assetHandoff"), dict) else {}
    if handoff.get("state") != "PASS" or handoff.get("verifiedRasterCount") != 13:
        errors.append("assetHandoff must PASS with 13 verified rasters")
    publication = state.get("publication") if isinstance(state.get("publication"), dict) else {}
    if publication.get("atlasPublished") is True:
        errors.append("Country is already published")
    return errors


def review_needed(slug: str, state: dict[str, Any]) -> bool:
    """Only re-review if the target's material changed after its validated preview.

    State reconciliation and approval-only commits are not a reason to
    redeploy or rerun Browser QA. Unknown/expired source commits fail
    open toward a fresh QA, never toward an unverified publication.
    """
    if (state.get("finalApproval") or {}).get("state") == "APPROVED":
        return False
    if (state.get("publication") or {}).get("atlasPublished") is True:
        return False
    preview = state.get("reviewPreview") or {}
    if preview.get("state") != "DONE" or preview.get("browserQa") != "PASS" or not preview.get("url"):
        return True
    source = preview.get("sourceCommit")
    if not isinstance(source, str) or not source:
        return True
    paths = [
        f"data/countries/{slug}.json",
        f"assets/images/{slug}",
        "data/theme-taxonomy.json",
        "data/atlas-destinations.json",
        "data/country-renewal-status.json",
    ]
    try:
        subprocess.run(["git", "cat-file", "-e", f"{source}^{{commit}}"],
                       cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        diff = subprocess.run(["git", "diff", "--quiet", source, "HEAD", "--", *paths],
                              cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        return True
    return diff.returncode != 0


def publish_ready_errors(slug: str, state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not is_active(slug):
        errors.append("publicationPipelineVersion is not 2")
    if state.get("productionProtocolId") != "2.0":
        errors.append("productionProtocolId must be 2.0")
    preview = state.get("reviewPreview") if isinstance(state.get("reviewPreview"), dict) else {}
    preview_verified = preview.get("state") == "DONE" and preview.get("browserQa") == "PASS" and bool(preview.get("url"))
    deployment = state.get("reviewDeployment") or {}
    publication = state.get("publication") or {}
    # A Country reviewed on its verified canonical noindex URL has no branch preview.
    canonical_verified = (
        state.get("phase") in {"REVIEW", "COMPLETE"}
        and state.get("contentRef") == "main" and state.get("stateRef") == "main"
        and (state.get("qa") or {}).get("state") == "PASS"
        and deployment.get("state") == "DONE"
        and deployment.get("url") == f"https://atlas.yagenji.com/countries/{slug}/"
        and (
            deployment.get("productionVerification") == "LIVE_BROWSER_QA_PASS"
            or deployment.get("prePublicationReviewVerification") == "LIVE_BROWSER_QA_PASS"
        )
        and (publication.get("atlasPublished") is False or publication.get("pipelineVersion") == 2)
    )
    if not (preview_verified or canonical_verified):
        errors.append("verified review preview or canonical noindex Browser QA required")
    approval = state.get("finalApproval") if isinstance(state.get("finalApproval"), dict) else {}
    if approval.get("state") != "APPROVED":
        errors.append("finalApproval must be APPROVED")
    return errors


def increment_metric(state: dict[str, Any], key: str, amount: int = 1) -> None:
    metrics = state.setdefault("productionMetrics", {})
    current = metrics.get(key, 0)
    metrics[key] = (current if isinstance(current, int) else 0) + amount


def reconcile_review(slug: str, source_commit: str, review_url: str, run_id: str | None) -> None:
    _, state_path = paths_for_slug(slug)
    state = state_for_slug(slug)
    errors = review_ready_errors(slug, state)
    # Idempotent success if another run already reconciled this exact preview.
    preview = state.get("reviewPreview") if isinstance(state.get("reviewPreview"), dict) else {}
    if preview.get("state") == "DONE" and preview.get("browserQa") == "PASS":
        if preview.get("sourceCommit") == source_commit and preview.get("url") == review_url:
            print(f"{slug}: review preview already reconciled")
            return
    if errors:
        raise ValueError("; ".join(errors))

    timestamp = now_iso()
    state["publicationPipelineVersion"] = 2
    state["implementation"] = {
        **(state.get("implementation") if isinstance(state.get("implementation"), dict) else {}),
        "state": "DONE",
        "completedAt": timestamp,
        "sharedTemplate": True,
        "countrySpecificCss": False,
    }
    state["qa"] = {
        **(state.get("qa") if isinstance(state.get("qa"), dict) else {}),
        "state": "PASS",
        "productionState": "CI_GATED",
        "sourceCommit": source_commit,
        "checks": [
            "publication-v2-targeted-validation",
            "publication-v2-image-audit",
            "publication-v2-desktop-tablet-mobile-browser-qa",
        ],
    }
    state["phase"] = "QA"
    state["reviewPreview"] = {
        "mode": "TARGETED_COUNTRY_BRANCH_PREVIEW",
        "state": "DONE",
        "url": review_url,
        "browserQa": "PASS",
        "deployedAt": timestamp,
        "sourceCommit": source_commit,
        "runId": int(run_id) if run_id and str(run_id).isdigit() else run_id,
        "pipelineVersion": 2,
    }
    metrics = state.setdefault("productionMetrics", {})
    increment_metric(state, "reviewPreviewDeployments")
    increment_metric(state, "browserQaCycles")
    metrics["canonicalReviewReadyAt"] = timestamp
    state["next"] = {"action": "REVIEW_CANONICAL_URL", "asset": None}
    state["stateRevision"] = int(state.get("stateRevision") or 0) + 1
    state["updatedAt"] = timestamp
    write_json(state_path, state)
    print(f"{slug}: review preview reconciled -> REVIEW_CANONICAL_URL")


def update_registry_published(slug: str) -> int:
    state = state_for_slug(slug)
    hero = state.get("hero") if isinstance(state.get("hero"), dict) else {}
    hero_asset = hero.get("asset")
    if not isinstance(hero_asset, str) or not hero_asset.startswith("assets/images/"):
        raise ValueError(f"{slug}: approved Hero asset path is missing from Production State")

    updated = 0
    for path in REGISTRY_PATHS:
        payload = load_json(path)
        changed = False
        for row in payload.get("destinations", []):
            if isinstance(row, dict) and row.get("slug") == slug:
                row["atlasPublished"] = True
                row["href"] = f"countries/{slug}/"
                if path.name == "atlas-destinations.json":
                    row["image"] = hero_asset
                changed = True
                updated += 1
                break
        if changed:
            write_json(path, payload, compact=True)
    return updated


def finalize(slug: str) -> None:
    _, state_path = paths_for_slug(slug)
    state = state_for_slug(slug)
    errors = publish_ready_errors(slug, state)
    if errors:
        raise ValueError("; ".join(errors))

    registry_updates = update_registry_published(slug)
    if registry_updates == 0:
        raise ValueError(f"{slug}: destination registry row not found")

    publication = state.get("publication") if isinstance(state.get("publication"), dict) else {}
    if publication.get("state") == "PUBLISHED" and publication.get("atlasPublished") is True:
        print(f"{slug}: terminal publication state already prepared; registry reconciled")
        return

    timestamp = now_iso()
    production_url = f"https://atlas.yagenji.com/countries/{slug}/"
    state["publicationPipelineVersion"] = 2
    state["contentRef"] = "main"
    state["stateRef"] = "main"
    state["phase"] = "COMPLETE"
    state["implementation"] = {
        **(state.get("implementation") if isinstance(state.get("implementation"), dict) else {}),
        "state": "DONE",
    }
    state["qa"] = {
        **(state.get("qa") if isinstance(state.get("qa"), dict) else {}),
        "state": "PASS",
        "productionState": "CI_GATED",
    }
    previous_review = state.get("reviewDeployment") or {}
    state["reviewDeployment"] = {
        "state": "DONE",
        "url": production_url,
        "productionVerification": "CI_GATED",
        "pipelineVersion": 2,
        **({"prePublicationReviewVerification": "LIVE_BROWSER_QA_PASS",
            "prePublicationReviewVerifiedAt": previous_review.get("verifiedAt"),
            "prePublicationReviewBasis": previous_review.get("verificationBasis")}
           if previous_review.get("productionVerification") == "LIVE_BROWSER_QA_PASS" else {}),
    }
    state["publication"] = {
        "state": "PUBLISHED",
        "atlasPublished": True,
        "productionVerification": "CI_GATED",
        "requestedAt": timestamp,
        "publishedUrl": production_url,
        "robots": "index,follow",
        "sitemapListed": True,
        "linkedFromRegistry": True,
        "pipelineVersion": 2,
        "note": "Publication Pipeline v2 terminal metadata is committed before the serialized merge. Live Cloudflare verification remains authoritative after merge.",
    }
    state["next"] = {"action": "NONE", "asset": None}
    state["stateRevision"] = int(state.get("stateRevision") or 0) + 1
    state["updatedAt"] = timestamp
    write_json(state_path, state)
    print(f"{slug}: terminal publication metadata prepared")


def snapshot_shared(slug: str, output: Path) -> None:
    snapshot: dict[str, Any] = {"registryRows": {}, "statusRow": None, "themes": []}
    for path in REGISTRY_PATHS:
        payload = load_json(path)
        row = next((row for row in payload.get("destinations", []) if isinstance(row, dict) and row.get("slug") == slug), None)
        if row is not None:
            snapshot["registryRows"][path.name] = row

    if STATUS_PATH.exists():
        payload = load_json(STATUS_PATH)
        snapshot["statusRow"] = next(
            (row for row in payload.get("countries", []) if isinstance(row, dict) and row.get("slug") == slug),
            None,
        )

    if THEME_PATH.exists():
        taxonomy = load_json(THEME_PATH)
        snapshot["themes"] = [
            theme.get("id")
            for theme in taxonomy.get("themes", [])
            if isinstance(theme, dict) and slug in (theme.get("examples") or [])
        ]

    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{slug}: shared metadata snapshot saved to {output}")


def restore_shared(slug: str, snapshot_path: Path) -> None:
    snapshot = load_json(snapshot_path)
    rows_by_name = snapshot.get("registryRows") if isinstance(snapshot.get("registryRows"), dict) else {}
    for path in REGISTRY_PATHS:
        saved = rows_by_name.get(path.name)
        if not isinstance(saved, dict):
            continue
        payload = load_json(path)
        rows = payload.setdefault("destinations", [])
        for index, row in enumerate(rows):
            if isinstance(row, dict) and row.get("slug") == slug:
                rows[index] = saved
                break
        else:
            rows.append(saved)
        write_json(path, payload, compact=True)

    saved_status = snapshot.get("statusRow")
    if isinstance(saved_status, dict) and STATUS_PATH.exists():
        payload = load_json(STATUS_PATH)
        rows = payload.setdefault("countries", [])
        for index, row in enumerate(rows):
            if isinstance(row, dict) and row.get("slug") == slug:
                rows[index] = saved_status
                break
        else:
            rows.append(saved_status)
        write_json(STATUS_PATH, payload, compact=True)

    wanted_themes = set(snapshot.get("themes") or [])
    if THEME_PATH.exists():
        payload = load_json(THEME_PATH)
        for theme in payload.get("themes", []):
            if not isinstance(theme, dict):
                continue
            examples = [item for item in (theme.get("examples") or []) if item != slug]
            if theme.get("id") in wanted_themes:
                examples.append(slug)
            theme["examples"] = examples
        write_json(THEME_PATH, payload)
    print(f"{slug}: shared metadata restored")


def status(slug: str) -> dict[str, Any]:
    active = is_active(slug)
    payload: dict[str, Any] = {"slug": slug, "active": active, "pipelineVersion": 2 if active else None}
    if not active:
        return payload
    state = state_for_slug(slug)
    payload.update(
        {
            "reviewReady": not review_ready_errors(slug, state),
            "publishReady": not publish_ready_errors(slug, state),
            "phase": state.get("phase"),
            "reviewPreview": state.get("reviewPreview"),
            "finalApproval": state.get("finalApproval"),
            "publication": state.get("publication"),
        }
    )
    return payload


def self_test() -> int:
    dummy = {
        "productionProtocolId": "2.0",
        "hero": {"state": "APPROVED"},
        "scenes": [{"state": "APPROVED"} for _ in range(8)],
        "taste": [{"state": "APPROVED"} for _ in range(4)],
        "sceneBatchReview": {"approval": "APPROVED"},
        "tasteBatchReview": {"approval": "APPROVED"},
        "assetHandoff": {"state": "PASS", "verifiedRasterCount": 13},
        "reviewPreview": {"state": "NOT_STARTED", "browserQa": "NOT_STARTED", "url": None},
        "finalApproval": {"state": "PENDING"},
        "publication": {"state": "DRAFT", "atlasPublished": False},
    }
    assert all_visuals_approved(dummy)
    dummy["scenes"][0]["state"] = "REGENERATE"
    assert not all_visuals_approved(dummy)
    dummy["scenes"][0]["state"] = "APPROVED"
    assert all_visuals_approved(dummy)
    print("Publication Pipeline v2 helper self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("status", "review-needed", "assert-review-ready", "assert-publish-ready", "finalize"):
        p = sub.add_parser(name)
        p.add_argument("slug")

    p = sub.add_parser("reconcile-review")
    p.add_argument("slug")
    p.add_argument("--source-commit", required=True)
    p.add_argument("--review-url", required=True)
    p.add_argument("--run-id")

    p = sub.add_parser("snapshot-shared")
    p.add_argument("slug")
    p.add_argument("output")

    p = sub.add_parser("restore-shared")
    p.add_argument("slug")
    p.add_argument("snapshot")

    sub.add_parser("self-test")
    args = parser.parse_args()

    try:
        if args.command == "status":
            print(json.dumps(status(args.slug), ensure_ascii=False))
        elif args.command == "review-needed":
            needed = review_needed(args.slug, state_for_slug(args.slug))
            print(f"{args.slug}: review {'required' if needed else 'already current'}")
            return 0 if needed else 2
        elif args.command == "assert-review-ready":
            errors = review_ready_errors(args.slug, state_for_slug(args.slug))
            if errors:
                raise ValueError("; ".join(errors))
            print(f"{args.slug}: review-ready")
        elif args.command == "assert-publish-ready":
            errors = publish_ready_errors(args.slug, state_for_slug(args.slug))
            if errors:
                raise ValueError("; ".join(errors))
            print(f"{args.slug}: publish-ready")
        elif args.command == "reconcile-review":
            reconcile_review(args.slug, args.source_commit, args.review_url, args.run_id)
        elif args.command == "finalize":
            finalize(args.slug)
        elif args.command == "snapshot-shared":
            snapshot_shared(args.slug, Path(args.output))
        elif args.command == "restore-shared":
            restore_shared(args.slug, Path(args.snapshot))
        elif args.command == "self-test":
            return self_test()
    except ValueError as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())