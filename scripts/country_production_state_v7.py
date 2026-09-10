#!/usr/bin/env python3
"""Revision 7 guardrails for JOURNEY ATLAS Country production state.

This module supplements the legacy state inspector with revision-7-specific
initialization, static validation, and per-commit transition validation.

Revision 7 goals:
- different targets may continue in the same assistant turn after reconciliation;
- Scene/Taste approvals occur only at a batch boundary, including REGEN rounds;
- every APPROVED Scene/Taste generation is covered by an immutable batch ledger;
- late backfilling of batch approval records is rejected by transition validation;
- target reservation is bound to contentId + generation-context epoch.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LEGACY_PATH = HERE / "country_production_state.py"
POLICY_PATH = ROOT / "ops" / "image-generation-policy.json"
STATE_DIR = ROOT / "ops" / "country-production"

spec = importlib.util.spec_from_file_location("journey_atlas_country_state_legacy", LEGACY_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {LEGACY_PATH}")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)

SCENE_IDS = [f"S{i:02d}" for i in range(1, 9)]
FOOD_IDS = [f"FOOD{i:02d}" for i in range(1, 5)]
ACTIVE_IMAGE_PHASES = {
    "HERO",
    "SCENES_INITIAL", "SCENES_REVIEW", "SCENES_REGEN",
    "TASTE_INITIAL", "TASTE_REVIEW", "TASTE_REGEN",
}
SCENE_PHASES = {"SCENES_INITIAL", "SCENES_REVIEW", "SCENES_REGEN"}
TASTE_PHASES = {"TASTE_INITIAL", "TASTE_REVIEW", "TASTE_REGEN"}
SCENE_BOUNDARY_ACTIONS = {"BATCH_REVIEW_SCENES", "WAIT_SCENE_BATCH_REVIEW"}
TASTE_BOUNDARY_ACTIONS = {"BATCH_REVIEW_TASTE", "WAIT_TASTE_BATCH_REVIEW"}
ALLOWED_CONTAMINATION_REASONS = {
    "COLLAGE_OR_MULTIPANEL",
    "PREVIOUS_ASSET_REPEAT",
    "WRONG_TARGET_CARRYOVER",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def central_revision() -> int | None:
    if not POLICY_PATH.exists():
        return None
    value = load_json(POLICY_PATH).get("revision")
    return value if isinstance(value, int) else None


def v7_snapshot() -> dict[str, Any]:
    return {
        "revision": 7,
        "sceneMode": "ONE_TARGET_ONE_STANDALONE_IMAGE",
        "tasteMode": "ONE_TARGET_ONE_STANDALONE_IMAGE",
        "sceneReview": "BATCH_ONLY",
        "tasteReview": "BATCH_ONLY",
        "mandatoryNoAddedText": True,
        "rejectTypographyImmediately": True,
        "rejectCollageImmediately": True,
        "rejectPreviousAssetRepeatImmediately": True,
        "candidateVisualQaRequired": True,
        "batchPerceptualDuplicateGate": True,
        "preGenerationReservationRequired": True,
        "reconcileBeforeNextGeneration": True,
        "maxSameAssetGenerationsPerTurn": 1,
        "differentTargetSameTurnContinuation": True,
        "reservationBlocksOnlyUnreconciledTarget": True,
        "freshTextToImageRequired": True,
        "previousImageReferenceForbidden": True,
        "repeatFailureRequiresRenderPacketRefresh": True,
        "singleFrameContractRequired": True,
        "collageFailureContaminatesContext": True,
        "repeatFailureContaminatesContext": True,
        "wrongTargetCarryoverContaminatesContext": True,
        "contextResetRequiresSeparateTurn": True,
        "batchLanguageForbiddenInGenerationTurn": True,
        "multiTargetPromptForbidden": True,
        "maxConsecutiveHardFailuresPerPromptSeries": 2,
        "requireRenderPacketRefreshAfterLimit": True,
        "approvedAssetRegeneration": False,
        "runtimeContinuation": "TO_BATCH_BOUNDARY",
        "batchApprovalProvenanceRequired": True,
        "regenBatchApprovalRequired": True,
        "allPriorCountryAssetComparisonRequired": True,
        "targetEpochBindingRequired": True,
    }


def new_state(destination: dict[str, Any]) -> dict[str, Any]:
    state = legacy.new_state(destination)
    state["imageGenerationPolicy"] = v7_snapshot()
    state["sceneBatchReview"] = {"approval": "PENDING", "rounds": []}
    state["tasteBatchReview"] = {"approval": "PENDING", "rounds": []}
    state["generationContext"] = {
        "state": "CLEAN",
        "epoch": 1,
        "lastResetAt": None,
        "lastFailureAsset": None,
        "lastFailureReason": None,
    }
    state["next"] = legacy.derive_next(state)
    return state


def item_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in items if isinstance(item, dict) and item.get("id")}


def ledger_rounds(state: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    key = "sceneBatchReview" if kind == "scene" else "tasteBatchReview"
    review = state.get(key)
    if not isinstance(review, dict):
        return []
    rounds = review.get("rounds")
    return rounds if isinstance(rounds, list) else []


def validate_ledger(
    errors: list[str],
    filename: str,
    state: dict[str, Any],
    kind: str,
    ids: list[str],
    items: list[dict[str, Any]],
) -> None:
    key = "sceneBatchReview" if kind == "scene" else "tasteBatchReview"
    label = "Scene" if kind == "scene" else "Taste"
    review = state.get(key)
    if not isinstance(review, dict):
        errors.append(f"{filename}: revision 7 requires {key} object")
        return
    if review.get("approval") not in {"PENDING", "APPROVED"}:
        errors.append(f"{filename}: {key}.approval must be PENDING or APPROVED")

    rounds = review.get("rounds")
    if not isinstance(rounds, list):
        errors.append(f"{filename}: {key}.rounds must be a list")
        return

    covered: dict[str, set[str]] = {asset_id: set() for asset_id in ids}
    expected_round_number = 1
    for idx, entry in enumerate(rounds):
        prefix = f"{filename}: {key}.rounds[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if entry.get("round") != expected_round_number:
            errors.append(f"{prefix}.round must be {expected_round_number}")
        expected_round_number += 1
        if entry.get("reviewBoundary") is not True:
            errors.append(f"{prefix}.reviewBoundary must be true")
        if not isinstance(entry.get("approvedAt"), str) or not entry.get("approvedAt"):
            errors.append(f"{prefix}.approvedAt is required")

        scope = entry.get("scope")
        approved = entry.get("approvedGenerations")
        regenerate = entry.get("regenerate")
        if not isinstance(scope, list) or len(scope) != len(set(scope)) or any(x not in ids for x in scope):
            errors.append(f"{prefix}.scope must contain unique valid {label} ids")
            continue
        if not isinstance(approved, dict):
            errors.append(f"{prefix}.approvedGenerations must be an object")
            continue
        if not isinstance(regenerate, list) or len(regenerate) != len(set(regenerate)):
            errors.append(f"{prefix}.regenerate must be a unique-id list")
            continue
        approved_ids = set(approved.keys())
        regen_ids = set(regenerate)
        scope_ids = set(scope)
        if approved_ids & regen_ids:
            errors.append(f"{prefix}: approvedGenerations and regenerate must be disjoint")
        if approved_ids | regen_ids != scope_ids:
            errors.append(f"{prefix}: approvedGenerations + regenerate must exactly partition scope")
        for asset_id, generation_id in approved.items():
            if asset_id not in ids:
                errors.append(f"{prefix}: invalid approved id {asset_id}")
            if not isinstance(generation_id, str) or not generation_id:
                errors.append(f"{prefix}: approved generation id for {asset_id} is required")
            elif asset_id in covered:
                covered[asset_id].add(generation_id)

    by_id = item_map(items)
    for asset_id in ids:
        item = by_id.get(asset_id, {})
        if item.get("state") == "APPROVED":
            generation_id = item.get("approvedGenerationId")
            if not isinstance(generation_id, str) or not generation_id:
                errors.append(f"{filename}: APPROVED {label} {asset_id} requires approvedGenerationId")
            elif generation_id not in covered.get(asset_id, set()):
                errors.append(
                    f"{filename}: APPROVED {label} {asset_id} generation {generation_id} is not covered by immutable batch ledger"
                )
        if item.get("userApprovedAt") is not None:
            errors.append(
                f"{filename}: revision 7 forbids per-item userApprovedAt on {label} {asset_id}; approval provenance belongs in {key}.rounds"
            )

    if review.get("approval") == "APPROVED" and not all(by_id.get(asset_id, {}).get("state") == "APPROVED" for asset_id in ids):
        errors.append(f"{filename}: {key}.approval cannot be APPROVED until all {label} assets are APPROVED")


def validate_state_dict(state: dict[str, Any], filename: str) -> list[str]:
    errors: list[str] = []
    phase = state.get("phase")
    revision = state.get("imageGenerationPolicy", {}).get("revision")
    central = central_revision()

    if phase in ACTIVE_IMAGE_PHASES and central == 7 and revision != 7:
        errors.append(
            f"{filename}: active image phase must use central image policy revision 7, got {revision!r}"
        )

    if revision != 7:
        return errors

    snapshot = state.get("imageGenerationPolicy")
    expected = v7_snapshot()
    if not isinstance(snapshot, dict):
        errors.append(f"{filename}: revision 7 requires imageGenerationPolicy object")
    else:
        for key, value in expected.items():
            if snapshot.get(key) != value:
                errors.append(
                    f"{filename}: revision 7 imageGenerationPolicy.{key} must be {value!r}, got {snapshot.get(key)!r}"
                )

    context = state.get("generationContext")
    if not isinstance(context, dict):
        errors.append(f"{filename}: revision 7 requires generationContext")
    else:
        if context.get("state") not in {"CLEAN", "CONTAMINATED"}:
            errors.append(f"{filename}: generationContext.state must be CLEAN or CONTAMINATED")
        if not isinstance(context.get("epoch"), int) or context.get("epoch", 0) < 1:
            errors.append(f"{filename}: generationContext.epoch must be a positive integer")
        if context.get("state") == "CONTAMINATED":
            if context.get("lastFailureReason") not in ALLOWED_CONTAMINATION_REASONS:
                errors.append(
                    f"{filename}: revision 7 contaminated context requires one of {sorted(ALLOWED_CONTAMINATION_REASONS)}"
                )
            if state.get("next") != {"action": "RESET_GENERATION_CONTEXT", "asset": None}:
                errors.append(f"{filename}: contaminated context must route NEXT to RESET_GENERATION_CONTEXT")

    scenes = state.get("scenes") if isinstance(state.get("scenes"), list) else []
    taste = state.get("taste") if isinstance(state.get("taste"), list) else []
    scene_by_id = item_map(scenes)
    taste_by_id = item_map(taste)

    if phase in {"SCENES_INITIAL", "SCENES_REVIEW"}:
        approved = [asset_id for asset_id in SCENE_IDS if scene_by_id.get(asset_id, {}).get("state") == "APPROVED"]
        if approved:
            errors.append(f"{filename}: {phase} cannot contain APPROVED Scenes before batch review: {approved}")
    if phase in {"TASTE_INITIAL", "TASTE_REVIEW"}:
        approved = [asset_id for asset_id in FOOD_IDS if taste_by_id.get(asset_id, {}).get("state") == "APPROVED"]
        if approved:
            errors.append(f"{filename}: {phase} cannot contain APPROVED Taste items before batch review: {approved}")

    validate_ledger(errors, filename, state, "scene", SCENE_IDS, scenes)
    validate_ledger(errors, filename, state, "taste", FOOD_IDS, taste)

    # Revision 7 reservation-to-target synchronization.
    generating: list[tuple[str, dict[str, Any]]] = []
    hero = state.get("hero") if isinstance(state.get("hero"), dict) else {}
    if hero.get("state") == "GENERATING":
        generating.append(("HERO", hero))
    generating.extend((str(x.get("id")), x) for x in scenes if isinstance(x, dict) and x.get("state") == "GENERATING")
    generating.extend((str(x.get("id")), x) for x in taste if isinstance(x, dict) and x.get("state") == "GENERATING")
    if len(generating) > 1:
        errors.append(f"{filename}: revision 7 permits only one unreconciled GENERATING target at a time")
    for asset_id, item in generating:
        reservation = item.get("generationReservation")
        if not isinstance(reservation, dict):
            errors.append(f"{filename}: GENERATING {asset_id} requires generationReservation")
            continue
        if reservation.get("contentId") != item.get("contentId"):
            errors.append(f"{filename}: {asset_id} reservation contentId must match Render Packet target")
        if reservation.get("asset") != asset_id:
            errors.append(f"{filename}: {asset_id} reservation.asset must match target id")
        if reservation.get("generationContextEpoch") != (context or {}).get("epoch"):
            errors.append(f"{filename}: {asset_id} reservation epoch must match generationContext.epoch")
        if state.get("next") != {"action": "RECONCILE_GENERATION", "asset": asset_id}:
            errors.append(f"{filename}: unreconciled {asset_id} must own NEXT until reconciliation")

    return errors


def validate_all() -> list[str]:
    errors: list[str] = []
    if central_revision() != 7:
        errors.append(f"central image policy must be revision 7, got {central_revision()!r}")
    if not STATE_DIR.exists():
        return errors + ["production state directory is missing"]
    for path in sorted(STATE_DIR.glob("*.json")):
        try:
            state = load_json(path)
        except Exception as exc:
            errors.append(f"{path.name}: cannot parse JSON: {exc}")
            continue
        errors.extend(validate_state_dict(state, path.name))
    return errors


def git_text(commit: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def git_json(commit: str, path: str) -> dict[str, Any] | None:
    text = git_text(commit, path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def changed_state_paths(commit: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit, "--", "ops/country-production"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".json")]


def first_parent(commit: str) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", f"{commit}^1"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def validate_batch_transition(
    errors: list[str],
    path: str,
    before: dict[str, Any],
    after: dict[str, Any],
    kind: str,
) -> None:
    ids = SCENE_IDS if kind == "scene" else FOOD_IDS
    items_key = "scenes" if kind == "scene" else "taste"
    review_key = "sceneBatchReview" if kind == "scene" else "tasteBatchReview"
    boundary_actions = SCENE_BOUNDARY_ACTIONS if kind == "scene" else TASTE_BOUNDARY_ACTIONS
    label = "Scene" if kind == "scene" else "Taste"

    before_items = item_map(before.get(items_key) if isinstance(before.get(items_key), list) else [])
    after_items = item_map(after.get(items_key) if isinstance(after.get(items_key), list) else [])
    before_rounds = ledger_rounds(before, kind)
    after_rounds = ledger_rounds(after, kind)

    # Existing ledger history is immutable. This makes late backfill/modification detectable.
    if len(after_rounds) < len(before_rounds) or after_rounds[: len(before_rounds)] != before_rounds:
        errors.append(f"{path}: revision 7 {review_key}.rounds history is immutable and append-only")
        return

    appended = after_rounds[len(before_rounds) :]
    changed_approvals: dict[str, str] = {}
    for asset_id in ids:
        b = before_items.get(asset_id, {})
        a = after_items.get(asset_id, {})
        b_gid = b.get("approvedGenerationId") if b.get("state") == "APPROVED" else None
        a_gid = a.get("approvedGenerationId") if a.get("state") == "APPROVED" else None
        if a_gid and a_gid != b_gid:
            changed_approvals[asset_id] = a_gid

    if not appended and changed_approvals:
        errors.append(
            f"{path}: {label} approvals {sorted(changed_approvals)} changed without a new batch-review ledger round"
        )
        return

    if not appended:
        return
    if len(appended) != 1:
        errors.append(f"{path}: add at most one {label} batch-review round per commit transition")
        return

    previous_next = legacy.derive_next(before)
    if previous_next.get("action") not in boundary_actions:
        errors.append(
            f"{path}: {label} batch ledger may be appended only at a true batch boundary; previous NEXT was {previous_next}"
        )
        return

    entry = appended[0]
    if not isinstance(entry, dict):
        errors.append(f"{path}: appended {label} batch round must be an object")
        return
    scope = entry.get("scope") if isinstance(entry.get("scope"), list) else []
    approved = entry.get("approvedGenerations") if isinstance(entry.get("approvedGenerations"), dict) else {}
    regenerate = entry.get("regenerate") if isinstance(entry.get("regenerate"), list) else []

    expected_scope = [asset_id for asset_id in ids if before_items.get(asset_id, {}).get("state") != "APPROVED"]
    if set(scope) != set(expected_scope) or len(scope) != len(expected_scope):
        errors.append(
            f"{path}: {label} batch round scope must equal all and only unapproved targets at the boundary; expected {expected_scope}, got {scope}"
        )

    if set(approved.keys()) != set(changed_approvals.keys()):
        errors.append(
            f"{path}: {label} batch ledger approvedGenerations must exactly match approvals created in the same transition"
        )
    for asset_id, generation_id in changed_approvals.items():
        if approved.get(asset_id) != generation_id:
            errors.append(f"{path}: {label} {asset_id} ledger generation id does not match approvedGenerationId")

    expected_regen = set(expected_scope) - set(changed_approvals.keys())
    if set(regenerate) != expected_regen:
        errors.append(
            f"{path}: {label} batch regenerate list must be exactly {sorted(expected_regen)}, got {sorted(regenerate)}"
        )
    for asset_id in expected_regen:
        if after_items.get(asset_id, {}).get("state") != "REGENERATE":
            errors.append(f"{path}: {label} {asset_id} rejected at batch review must be REGENERATE")
    for asset_id in changed_approvals:
        if after_items.get(asset_id, {}).get("state") != "APPROVED":
            errors.append(f"{path}: {label} {asset_id} approved in batch ledger must be APPROVED")

    # Previously approved assets are outside this round and must remain immutable.
    for asset_id in ids:
        if asset_id in expected_scope:
            continue
        b = before_items.get(asset_id, {})
        a = after_items.get(asset_id, {})
        if b.get("state") == "APPROVED" and (
            a.get("state") != "APPROVED" or a.get("approvedGenerationId") != b.get("approvedGenerationId")
        ):
            errors.append(f"{path}: previously batch-approved {label} {asset_id} changed inside another batch round")


def validate_transition(before: dict[str, Any] | None, after: dict[str, Any] | None, path: str) -> list[str]:
    errors: list[str] = []
    if after is None:
        return errors
    errors.extend(validate_state_dict(after, Path(path).name))
    if after.get("imageGenerationPolicy", {}).get("revision") != 7:
        return errors
    if before is None:
        # New revision-7 State must not begin with pre-approved Scene/Taste assets.
        for key in ("scenes", "taste"):
            items = after.get(key) if isinstance(after.get(key), list) else []
            if any(isinstance(x, dict) and x.get("state") == "APPROVED" for x in items):
                errors.append(f"{path}: new revision 7 State cannot initialize with APPROVED {key}")
        return errors

    # Migration from an older revision may add v7 metadata, but may not create new approvals.
    if before.get("imageGenerationPolicy", {}).get("revision") != 7:
        for kind, key, ids in (("scene", "scenes", SCENE_IDS), ("taste", "taste", FOOD_IDS)):
            b = item_map(before.get(key) if isinstance(before.get(key), list) else [])
            a = item_map(after.get(key) if isinstance(after.get(key), list) else [])
            for asset_id in ids:
                if b.get(asset_id, {}).get("state") != "APPROVED" and a.get(asset_id, {}).get("state") == "APPROVED":
                    errors.append(f"{path}: revision migration cannot create new {kind} approval")
        return errors

    validate_batch_transition(errors, path, before, after, "scene")
    validate_batch_transition(errors, path, before, after, "taste")
    return errors


def validate_range(base: str, head: str) -> list[str]:
    errors: list[str] = []
    result = subprocess.run(
        ["git", "rev-list", "--reverse", "--ancestry-path", f"{base}..{head}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    for commit in commits:
        parent = first_parent(commit)
        for path in changed_state_paths(commit):
            before = git_json(parent, path) if parent else None
            after = git_json(commit, path)
            transition_errors = validate_transition(before, after, path)
            errors.extend(f"{commit[:8]} {message}" for message in transition_errors)
    return errors


def print_errors(errors: list[str], heading: str) -> int:
    if not errors:
        print(f"{heading}: PASS")
        return 0
    print(f"{heading}: FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


def cmd_init(slug: str) -> int:
    path = legacy.state_path(slug)
    if path.exists():
        print(f"State already exists: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    registry = legacy.registry_map()
    destination = registry.get(slug)
    if destination is None:
        print(f"Unknown destination slug: {slug}", file=sys.stderr)
        return 1
    if destination.get("atlasPublished"):
        print(f"Refusing to initialize already-published slug: {slug}", file=sys.stderr)
        return 1
    state = new_state(destination)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created revision-7 State: {path.relative_to(ROOT)}")
    return 0


def self_test() -> int:
    state = new_state({"slug": "test-slug", "nameEn": "Test Slug"})
    assert state["imageGenerationPolicy"]["revision"] == 7
    assert state["imageGenerationPolicy"]["differentTargetSameTurnContinuation"] is True
    assert state["imageGenerationPolicy"]["runtimeContinuation"] == "TO_BATCH_BOUNDARY"
    assert state["sceneBatchReview"] == {"approval": "PENDING", "rounds": []}
    assert state["tasteBatchReview"] == {"approval": "PENDING", "rounds": []}
    assert state["next"] == {"action": "COMPLETE_CONTENT_DESIGN", "asset": None}
    print("Revision 7 initializer contract self-test passed")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: country_production_state_v7.py init <slug> | validate | validate-range <base> <head> | next <slug> | self-test", file=sys.stderr)
        return 2
    command = args[0]
    if command == "init" and len(args) == 2:
        return cmd_init(args[1])
    if command == "validate" and len(args) == 1:
        return print_errors(validate_all(), "Revision 7 state validation")
    if command == "validate-range" and len(args) == 3:
        return print_errors(validate_range(args[1], args[2]), "Revision 7 transition validation")
    if command == "next" and len(args) == 2:
        path = legacy.state_path(args[1])
        if not path.exists():
            print(f"Missing state: {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        state = load_json(path)
        print(json.dumps({"slug": args[1], "phase": state.get("phase"), "next": legacy.derive_next(state)}, ensure_ascii=False))
        return 0
    if command == "self-test" and len(args) == 1:
        return self_test()
    print("Invalid arguments", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
