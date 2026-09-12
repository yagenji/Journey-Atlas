#!/usr/bin/env python3
"""JOURNEY ATLAS image-policy 7.2 guardrails.

Patch 7.2 closes production regressions observed during Philippines / Singapore /
Thailand / Vietnam / Brunei production:
- Taste composition distinguishes integral dish components from decoration;
- Taste candidates require explicit background / prop / dish QA;
- an initial Taste round attempts every target before any failed target is retried;
- TASTE_REGEN cannot begin before a real Taste batch-review ledger round;
- repeat / wrong-target failures require an immediate Render Packet refresh.

This module supplements Revision 7 rather than replacing it.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
POLICY_PATH = ROOT / "ops" / "image-generation-policy.json"
STATE_DIR = ROOT / "ops" / "country-production"
V7_PATH = SCRIPTS / "country_production_state_v7.py"

spec = importlib.util.spec_from_file_location("journey_atlas_v7_for_v72", V7_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {V7_PATH}")
v7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v7)
legacy = v7.legacy

TASTE_PHASES = {"TASTE_INITIAL", "TASTE_REVIEW", "TASTE_REGEN"}
ACTIVE_TASTE_STATES = {"NOT_STARTED", "GENERATING", "REGENERATE", "REVIEW_CANDIDATE"}
IMMEDIATE_REFRESH_FAILURES = {"PREVIOUS_ASSET_REPEAT", "WRONG_TARGET_CARRYOVER"}
BACKGROUND_STYLE = "PLAIN_PALE_BEIGE_OR_WARM_IVORY"
TASTE_QA_REQUIRED = (
    "targetIdentity",
    "dishIdentity",
    "singleDish",
    "integralComponentsOnly",
    "plainBackground",
    "decorativePropsAbsent",
    "previousAssetRepeat",
    "collageTypography",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def central_policy() -> dict[str, Any]:
    return load_json(POLICY_PATH)


def policy_is_72() -> bool:
    policy = central_policy()
    return policy.get("revision") == 7 and policy.get("patch") == 2 and policy.get("policyId") == "7.2"


def prompt_refresh_required(item: dict[str, Any]) -> bool:
    """Revision-7.2 retry guard.

    A repeat or wrong-target carryover must never be retried from the same prompt
    family. Other failures keep the existing two-hard-failure credit guard.
    """
    if item.get("state") != "REGENERATE":
        return False
    if item.get("lastFailureReason") in IMMEDIATE_REFRESH_FAILURES:
        return True
    count = item.get("promptSeriesRejectCount", 0)
    return isinstance(count, int) and count >= 2


def install_legacy_patch(target_legacy: Any) -> None:
    """Make legacy derive_next use the 7.2 immediate-refresh rule."""
    target_legacy.prompt_refresh_required = prompt_refresh_required


# Apply locally so this module's own use of v7.legacy is 7.2-aware.
install_legacy_patch(legacy)


def _item_map(items: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        return {}
    return {
        str(item.get("id")): item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _review_rounds(state: dict[str, Any]) -> list[dict[str, Any]]:
    review = state.get("tasteBatchReview")
    if not isinstance(review, dict):
        return []
    rounds = review.get("rounds")
    return [x for x in rounds if isinstance(x, dict)] if isinstance(rounds, list) else []


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)


def validate_taste_render_packet(item: dict[str, Any], owner: str) -> list[str]:
    errors: list[str] = []
    packet = item.get("renderPacket")
    if not isinstance(packet, dict):
        return [f"{owner}: image policy 7.2 requires a Taste renderPacket"]

    if packet.get("kind") != "TASTE":
        errors.append(f"{owner}: Taste renderPacket.kind must be TASTE")
    if packet.get("contentId") != item.get("contentId"):
        errors.append(f"{owner}: Taste renderPacket.contentId must match the target contentId")
    if not isinstance(packet.get("identity"), str) or not packet.get("identity", "").strip():
        errors.append(f"{owner}: Taste renderPacket.identity is required")

    required_true = {
        "independentGeneration": True,
        "forbidPreviousAssetReuse": True,
        "singleDishOnly": True,
        "cleanNeutralBackground": True,
        "singleFrameOnly": True,
        "forbidCollage": True,
        "forbidPanels": True,
        "forbidGrid": True,
        "forbidContactSheet": True,
        "forbidMontage": True,
        "forbidInsetImages": True,
        "integralAccompanimentsOnly": True,
        "decorativePropsForbidden": True,
        "plainBackgroundRequired": True,
    }
    for key, expected in required_true.items():
        if packet.get(key) is not expected:
            errors.append(f"{owner}: Taste renderPacket.{key} must be true under image policy 7.2")

    if packet.get("backgroundStyle") != BACKGROUND_STYLE:
        errors.append(
            f"{owner}: Taste renderPacket.backgroundStyle must be {BACKGROUND_STYLE!r}"
        )

    accompaniments = packet.get("integralAccompaniments")
    if not _string_list(accompaniments):
        errors.append(
            f"{owner}: Taste renderPacket.integralAccompaniments must be a list of named integral food components; use [] when none"
        )
    elif len({x.strip().casefold() for x in accompaniments}) != len(accompaniments):
        errors.append(f"{owner}: integralAccompaniments must not contain duplicates")

    serving_elements = packet.get("integralServingElements")
    if not _string_list(serving_elements):
        errors.append(
            f"{owner}: Taste renderPacket.integralServingElements must be a list; use [] when no wrapper/vessel/presentation element is integral to the dish"
        )
    elif len({x.strip().casefold() for x in serving_elements}) != len(serving_elements):
        errors.append(f"{owner}: integralServingElements must not contain duplicates")

    # This is the core semantic distinction requested by the project owner:
    # named integral components are allowed; styling/decorative props are not.
    decorative = packet.get("decorativeProps")
    if decorative != []:
        errors.append(f"{owner}: Taste renderPacket.decorativeProps must be []")

    return errors


def validate_taste_candidate(item: dict[str, Any], owner: str) -> list[str]:
    if item.get("state") != "REVIEW_CANDIDATE":
        return []
    errors: list[str] = []
    generation_id = item.get("candidateGenerationId")
    if not isinstance(generation_id, str) or not generation_id:
        errors.append(f"{owner}: Taste REVIEW_CANDIDATE requires candidateGenerationId")
    qa = item.get("candidateVisualQa")
    if not isinstance(qa, dict):
        return errors + [f"{owner}: Taste REVIEW_CANDIDATE requires candidateVisualQa"]
    for check in TASTE_QA_REQUIRED:
        if qa.get(check) != "PASS":
            errors.append(f"{owner}: candidateVisualQa.{check} must be PASS under image policy 7.2")
    return errors


def validate_state_dict(state: dict[str, Any], filename: str) -> list[str]:
    errors: list[str] = []
    if not policy_is_72():
        return errors
    if state.get("imageGenerationPolicy", {}).get("revision") != 7:
        return errors

    phase = state.get("phase")
    if phase not in TASTE_PHASES:
        return errors

    taste = state.get("taste") if isinstance(state.get("taste"), list) else []
    for item in taste:
        if not isinstance(item, dict) or item.get("state") not in ACTIVE_TASTE_STATES:
            continue
        asset_id = str(item.get("id") or "UNKNOWN")
        owner = f"{filename}: {asset_id}"
        errors.extend(validate_taste_render_packet(item, owner))
        errors.extend(validate_taste_candidate(item, owner))

    if phase == "TASTE_REGEN" and not _review_rounds(state):
        errors.append(
            f"{filename}: image policy 7.2 forbids TASTE_REGEN before the first Taste batch-review boundary"
        )

    return errors


def validate_transition(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    path: str,
) -> list[str]:
    if after is None or not policy_is_72():
        return []
    errors = validate_state_dict(after, Path(path).name)
    if before is None:
        return errors
    if after.get("imageGenerationPolicy", {}).get("revision") != 7:
        return errors

    before_phase = before.get("phase")
    after_phase = after.get("phase")
    before_rounds = _review_rounds(before)
    after_rounds = _review_rounds(after)

    # Vietnam regression: do not leave the initial round for REGEN until the
    # first real batch review has been recorded.
    if before_phase == "TASTE_INITIAL" and after_phase == "TASTE_REGEN":
        if len(after_rounds) <= len(before_rounds):
            errors.append(
                f"{path}: image policy 7.2 forbids entering TASTE_REGEN before appending the initial Taste batch-review round"
            )

    before_items = _item_map(before.get("taste"))
    after_items = _item_map(after.get("taste"))

    # A failed target in TASTE_INITIAL is parked as REGENERATE. Remaining
    # NOT_STARTED targets are attempted first. Retrying the failed target before
    # the round boundary recreates one-by-one Taste production.
    if before_phase == "TASTE_INITIAL" and after_phase == "TASTE_INITIAL":
        unattempted_after = {
            asset_id
            for asset_id, item in after_items.items()
            if item.get("state") == "NOT_STARTED"
        }
        if unattempted_after:
            for asset_id, after_item in after_items.items():
                before_item = before_items.get(asset_id, {})
                rejected_before = before_item.get("rejectedGenerationIds")
                rejected_after = after_item.get("rejectedGenerationIds")
                before_count = len(rejected_before) if isinstance(rejected_before, list) else 0
                after_count = len(rejected_after) if isinstance(rejected_after, list) else 0
                retrying_failed_target = (
                    after_item.get("state") == "GENERATING"
                    and (
                        before_item.get("state") == "REGENERATE"
                        or after_count > before_count
                    )
                )
                if retrying_failed_target:
                    errors.append(
                        f"{path}: {asset_id} was retried before the initial Taste round attempted all targets; continue to {sorted(unattempted_after)} first"
                    )

    # Thailand / Brunei regression: repeat or wrong-target carryover may not be
    # sent straight back to GENERATING from the same prompt series.
    for asset_id, before_item in before_items.items():
        if before_item.get("state") != "REGENERATE":
            continue
        if before_item.get("lastFailureReason") not in IMMEDIATE_REFRESH_FAILURES:
            continue
        after_item = after_items.get(asset_id, {})
        before_series = before_item.get("promptSeries", 1)
        after_series = after_item.get("promptSeries", before_series)
        if after_item.get("state") == "GENERATING" and (
            not isinstance(after_series, int)
            or not isinstance(before_series, int)
            or after_series <= before_series
        ):
            errors.append(
                f"{path}: {asset_id} repeat/wrong-target failure requires Render Packet refresh and promptSeries increment before regeneration"
            )
        if before_item.get("lastFailureReason") != after_item.get("lastFailureReason"):
            # Clearing the failure marker is valid only as part of a prompt-family refresh.
            if (
                not isinstance(after_series, int)
                or not isinstance(before_series, int)
                or after_series <= before_series
            ):
                errors.append(
                    f"{path}: {asset_id} cannot clear {before_item.get('lastFailureReason')} without a promptSeries increment"
                )

    return errors


def _git_json(commit: str | None, path: str) -> dict[str, Any] | None:
    if not commit:
        return None
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _first_parent(commit: str) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", f"{commit}^1"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _changed_state_paths(commit: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit, "--", "ops/country-production"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".json")]


def validate_all() -> list[str]:
    errors: list[str] = []
    if not policy_is_72():
        policy = central_policy()
        return [
            f"central image policy must be revision 7 patch 2 / policyId 7.2, got revision={policy.get('revision')!r} patch={policy.get('patch')!r} policyId={policy.get('policyId')!r}"
        ]
    for path in sorted(STATE_DIR.glob("*.json")):
        try:
            state = load_json(path)
        except Exception as exc:
            errors.append(f"{path.name}: cannot parse JSON: {exc}")
            continue
        errors.extend(validate_state_dict(state, path.name))
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
        parent = _first_parent(commit)
        for path in _changed_state_paths(commit):
            before = _git_json(parent, path)
            after = _git_json(commit, path)
            for message in validate_transition(before, after, path):
                errors.append(f"{commit[:8]} {message}")
    return errors


def self_test() -> int:
    assert policy_is_72(), "central policy is not 7.2"
    assert prompt_refresh_required({
        "state": "REGENERATE",
        "promptSeriesRejectCount": 1,
        "lastFailureReason": "PREVIOUS_ASSET_REPEAT",
    }) is True
    assert prompt_refresh_required({
        "state": "REGENERATE",
        "promptSeriesRejectCount": 1,
        "lastFailureReason": "WRONG_TARGET_CARRYOVER",
    }) is True
    assert prompt_refresh_required({
        "state": "REGENERATE",
        "promptSeriesRejectCount": 1,
        "lastFailureReason": "BACKGROUND_PROPS",
    }) is False
    print("Image policy 7.2 self-test passed")
    return 0


def print_errors(errors: list[str], heading: str) -> int:
    if not errors:
        print(f"{heading}: PASS")
        return 0
    print(f"{heading}: FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


def main() -> int:
    args = sys.argv[1:]
    if args == ["validate"]:
        return print_errors(validate_all(), "Image policy 7.2 state validation")
    if len(args) == 3 and args[0] == "validate-range":
        return print_errors(validate_range(args[1], args[2]), "Image policy 7.2 transition validation")
    if args == ["self-test"]:
        return self_test()
    print("Usage: image_policy_v72.py validate | validate-range <base> <head> | self-test", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
