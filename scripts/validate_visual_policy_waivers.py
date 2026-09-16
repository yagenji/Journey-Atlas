#!/usr/bin/env python3
"""Validate narrow post-generation visual-policy waivers.

Normal generation remains governed by ops/image-generation-policy.json.
This validator only accepts the explicit, audited waiver contract defined in
ops/visual-policy-waiver-policy.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "ops" / "visual-policy-waiver-policy.json"
STATE_DIR = ROOT / "ops" / "country-production"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def policy() -> dict[str, Any]:
    return load_json(POLICY_PATH)


def item_for(state: dict[str, Any], kind: str, asset_id: str) -> dict[str, Any] | None:
    if kind == "HERO":
        hero = state.get("hero")
        return hero if asset_id == "HERO" and isinstance(hero, dict) else None
    key = "scenes" if kind == "SCENE" else "taste" if kind == "TASTE" else None
    if key is None:
        return None
    items = state.get(key)
    if not isinstance(items, list):
        return None
    for item in items:
        if isinstance(item, dict) and item.get("id") == asset_id:
            return item
    return None


def ledger_covers(state: dict[str, Any], kind: str, asset_id: str, generation_id: str) -> bool:
    if kind == "HERO":
        return True
    key = "sceneBatchReview" if kind == "SCENE" else "tasteBatchReview"
    review = state.get(key)
    if not isinstance(review, dict):
        return False
    rounds = review.get("rounds")
    if not isinstance(rounds, list):
        return False
    for entry in rounds:
        if not isinstance(entry, dict):
            continue
        approved = entry.get("approvedGenerations")
        if isinstance(approved, dict) and approved.get(asset_id) == generation_id:
            return True
    return False


def recovery_for(state: dict[str, Any], migration_id: str) -> dict[str, Any] | None:
    migrations = state.get("recoveryMigrations")
    if not isinstance(migrations, list):
        return None
    for entry in migrations:
        if isinstance(entry, dict) and entry.get("id") == migration_id:
            return entry
    return None


def validate_waiver(state: dict[str, Any], waiver: dict[str, Any], filename: str) -> list[str]:
    cfg = policy()
    errors: list[str] = []
    prefix = f"{filename}: visualPolicyWaiver {waiver.get('id') or '<missing-id>'}"
    scope_cfg = cfg.get("scope") if isinstance(cfg.get("scope"), dict) else {}
    req = cfg.get("requirements") if isinstance(cfg.get("requirements"), dict) else {}
    contract = cfg.get("stateContract") if isinstance(cfg.get("stateContract"), dict) else {}

    if waiver.get("type") != contract.get("type"):
        errors.append(f"{prefix}: type must be {contract.get('type')!r}")

    violation = waiver.get("violationCode")
    allowed_violations = scope_cfg.get("allowedViolationCodes") or []
    if violation not in allowed_violations:
        errors.append(f"{prefix}: violationCode {violation!r} is not allowed")

    kind = waiver.get("kind")
    if kind not in (scope_cfg.get("allowedKinds") or []):
        errors.append(f"{prefix}: kind {kind!r} is not allowed")

    if waiver.get("authorizedBy") != req.get("userAuthorizationValue"):
        errors.append(f"{prefix}: authorizedBy must be USER_EXPLICIT")
    if not isinstance(waiver.get("authorizedAt"), str) or not waiver.get("authorizedAt"):
        errors.append(f"{prefix}: authorizedAt is required")
    if not isinstance(waiver.get("userInstruction"), str) or not waiver.get("userInstruction", "").strip():
        errors.append(f"{prefix}: userInstruction is required")
    if waiver.get("preserveExistingImages") is not True:
        errors.append(f"{prefix}: preserveExistingImages must be true")
    if waiver.get("regenerationRequired") is not False:
        errors.append(f"{prefix}: regenerationRequired must be false")

    status = waiver.get("status")
    if status not in (contract.get("allowedStatuses") or []):
        errors.append(f"{prefix}: status must be STAGED or APPLIED")

    scope = waiver.get("scope")
    generations = waiver.get("generations")
    if not isinstance(scope, list) or not scope or not all(isinstance(x, str) and x for x in scope) or len(scope) != len(set(scope)):
        errors.append(f"{prefix}: scope must be a non-empty unique string list")
        scope = []
    if not isinstance(generations, dict):
        errors.append(f"{prefix}: generations must be an object")
        generations = {}
    if set(generations.keys()) != set(scope):
        errors.append(f"{prefix}: generations keys must exactly match scope")
    generation_values = [value for value in generations.values() if isinstance(value, str) and value]
    if len(generation_values) != len(generations) or len(set(generation_values)) != len(generation_values):
        errors.append(f"{prefix}: generation IDs must be non-empty and unique")

    # This newly permitted provenance defect is not a new generation mode.
    # Only the four exact, already-generated, user-selected El Salvador outputs qualify.
    if violation == "MULTIPLE_OUTPUTS_ONE_REQUEST":
        case_id = waiver.get("closedHistoricalCaseId")
        cases = cfg.get("closedHistoricalCases") or {}
        case = cases.get(case_id) if isinstance(cases, dict) and isinstance(case_id, str) else None
        if not isinstance(case, dict):
            errors.append(f"{prefix}: closedHistoricalCaseId must identify an existing, exact historical case")
        else:
            if (state.get("slug") != case.get("slug") or kind != case.get("kind")
                    or violation != case.get("violationCode") or scope != case.get("scope")
                    or generations != case.get("generations")):
                errors.append(f"{prefix}: closedHistoricalCaseId does not match exact country, kind, scope and generation IDs")
    elif waiver.get("closedHistoricalCaseId") is not None:
        errors.append(f"{prefix}: closedHistoricalCaseId is reserved for closed historical exceptions")

    qa = waiver.get("hardVisualQa")
    if not isinstance(qa, dict):
        errors.append(f"{prefix}: hardVisualQa is required")
        qa = {}
    for check in req.get("requiredVisualQaPasses") or []:
        if qa.get(check) != "PASS":
            errors.append(f"{prefix}: hardVisualQa.{check} must be PASS")

    state_desync = waiver.get("stateDesynchronized") is True
    migration_id = waiver.get("recoveryMigrationId")
    if state_desync and (not isinstance(migration_id, str) or not migration_id):
        errors.append(f"{prefix}: stateDesynchronized waiver requires recoveryMigrationId")
    if isinstance(migration_id, str) and migration_id:
        migration = recovery_for(state, migration_id)
        if migration is None:
            errors.append(f"{prefix}: recoveryMigrationId {migration_id!r} was not found")
        else:
            if migration.get("type") != "USER_APPROVED_EXISTING_BATCH_RECOVERY":
                errors.append(f"{prefix}: recovery migration has invalid type")
            if migration.get("kind") != kind:
                errors.append(f"{prefix}: recovery migration kind must match waiver kind")
            recovered = migration.get("recoveredGenerations")
            if recovered != generations:
                errors.append(f"{prefix}: recovery migration generations must match waiver generations")
            if set(migration.get("scope") or []) != set(scope):
                errors.append(f"{prefix}: recovery migration scope must match waiver scope")
            if status == "APPLIED" and migration.get("status") != "APPLIED":
                errors.append(f"{prefix}: APPLIED waiver requires APPLIED recovery migration")

    for asset_id in scope:
        generation_id = generations.get(asset_id)
        item = item_for(state, str(kind), asset_id)
        if item is None:
            errors.append(f"{prefix}: target {asset_id} does not exist in Production State")
            continue
        if status == "STAGED":
            if item.get("state") != "REVIEW_CANDIDATE":
                errors.append(f"{prefix}: STAGED target {asset_id} must be REVIEW_CANDIDATE")
            if item.get("candidateGenerationId") != generation_id:
                errors.append(f"{prefix}: STAGED target {asset_id} candidateGenerationId mismatch")
        elif status == "APPLIED":
            if item.get("state") != "APPROVED":
                errors.append(f"{prefix}: APPLIED target {asset_id} must be APPROVED")
            if item.get("approvedGenerationId") != generation_id:
                errors.append(f"{prefix}: APPLIED target {asset_id} approvedGenerationId mismatch")
            if not ledger_covers(state, str(kind), asset_id, str(generation_id)):
                errors.append(f"{prefix}: APPLIED target {asset_id} is not covered by the normal batch ledger")

    return errors


def validate_state_dict(state: dict[str, Any], filename: str) -> list[str]:
    waivers = state.get("visualPolicyWaivers")
    if waivers is None:
        return []
    if not isinstance(waivers, list):
        return [f"{filename}: visualPolicyWaivers must be a list"]
    errors: list[str] = []
    ids: set[str] = set()
    used_closed_cases: set[str] = set()
    for index, waiver in enumerate(waivers):
        if not isinstance(waiver, dict):
            errors.append(f"{filename}: visualPolicyWaivers[{index}] must be an object")
            continue
        waiver_id = waiver.get("id")
        if not isinstance(waiver_id, str) or not waiver_id:
            errors.append(f"{filename}: visualPolicyWaivers[{index}].id is required")
        elif waiver_id in ids:
            errors.append(f"{filename}: duplicate visualPolicyWaiver id {waiver_id}")
        else:
            ids.add(waiver_id)
        if waiver.get("violationCode") == "MULTIPLE_OUTPUTS_ONE_REQUEST":
            case_id = waiver.get("closedHistoricalCaseId")
            if isinstance(case_id, str) and case_id in used_closed_cases:
                errors.append(f"{filename}: duplicate closedHistoricalCaseId {case_id}")
            if isinstance(case_id, str):
                used_closed_cases.add(case_id)
        errors.extend(validate_waiver(state, waiver, filename))
    return errors


def validate_all() -> list[str]:
    if not POLICY_PATH.exists():
        return ["Missing ops/visual-policy-waiver-policy.json"]
    cfg = policy()
    if cfg.get("policyId") != "USER_APPROVED_VISUAL_POLICY_WAIVER_V1":
        return [f"Unexpected visual waiver policyId: {cfg.get('policyId')!r}"]
    errors: list[str] = []
    for path in sorted(STATE_DIR.glob("*.json")):
        try:
            state = load_json(path)
        except Exception as exc:
            errors.append(f"{path.name}: cannot parse JSON: {exc}")
            continue
        errors.extend(validate_state_dict(state, path.name))
    return errors


def main() -> int:
    errors = validate_all()
    if errors:
        print("Visual policy waiver validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Visual policy waiver validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
