#!/usr/bin/env python3
"""One-time bounded patch helper. Remove from final PR after use."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path: str, changes: list[tuple[str, str]]) -> None:
    target = ROOT / path
    text = target.read_text(encoding='utf-8')
    for original, revised in changes:
        count = text.count(original)
        if count != 1:
            raise RuntimeError(f'{path}: expected one exact patch anchor, got {count}: {original[:100]}')
        text = text.replace(original, revised, 1)
    target.write_text(text, encoding='utf-8')
    print('PATCHED',path)


patch('scripts/country_production_state.py', [
    ('import json\nimport sys\n', 'import importlib.util\nimport json\nimport sys\n'),
    ('    slug = state.get("slug")\n    if path.stem != slug:', '''    slug = state.get("slug")
    jamaica_exception_ok = False
    if state.get("closedProvenanceException") is not None:
        if slug != "jamaica":
            errors.append(f"{filename}: Jamaica-only provenance exception used by another Country")
        else:
            helper = ROOT / "scripts/jamaica_closed_provenance_exception.py"
            spec = importlib.util.spec_from_file_location("jamaica_closed_exception_for_state", helper)
            if spec is None or spec.loader is None:
                errors.append(f"{filename}: Jamaica exception validator cannot be loaded")
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                problems = module.validate(state, ROOT)
                errors.extend(f"{filename}: {problem}" for problem in problems)
                jamaica_exception_ok = not problems
    if path.stem != slug:'''),
    ('if phase in AFTER_SCENES and not all_approved(scenes):', 'if phase in AFTER_SCENES and not all_approved(scenes) and not jamaica_exception_ok:'),
    ('if phase in AFTER_TASTE and not all_approved(taste):', 'if phase in AFTER_TASTE and not all_approved(taste) and not jamaica_exception_ok:'),
    ('if phase in AFTER_SCENES:\n            scene_review = state.get("sceneBatchReview")', 'if phase in AFTER_SCENES and not jamaica_exception_ok:\n            scene_review = state.get("sceneBatchReview")'),
    ('if phase in AFTER_TASTE:\n            taste_review = state.get("tasteBatchReview")', 'if phase in AFTER_TASTE and not jamaica_exception_ok:\n            taste_review = state.get("tasteBatchReview")'),
])

patch('scripts/publication_pipeline_v2.py', [
    ('import argparse\nimport json\n', 'import argparse\nimport importlib.util\nimport json\n'),
    ('def review_ready_errors(slug: str, state: dict[str, Any]) -> list[str]:', '''def verified_closed_jamaica_exception(slug: str, state: dict[str, Any]) -> bool:
    """Never bypass publication QA without the immutable, user-authorized 13-asset case."""
    if slug != "jamaica" or state.get("closedProvenanceException") is None:
        return False
    path = ROOT / "scripts/jamaica_closed_provenance_exception.py"
    spec = importlib.util.spec_from_file_location("jamaica_closed_exception_for_publication", path)
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return not module.validate(state, ROOT)


def review_ready_errors(slug: str, state: dict[str, Any]) -> list[str]:'''),
    ('    if not all_visuals_approved(state):\n        errors.append("Hero + 8 Scenes + 4 Taste assets must be batch-approved")', '''    if not (all_visuals_approved(state) or verified_closed_jamaica_exception(slug, state)):
        errors.append("Hero + 8 Scenes + 4 Taste assets must be batch-approved, or match the exact authorized Jamaica closed-provenance exception")'''),
    ('def publish_ready_errors(slug: str, state: dict[str, Any]) -> list[str]:\n    errors: list[str] = []', '''def publish_ready_errors(slug: str, state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state.get("closedProvenanceException") is not None and not verified_closed_jamaica_exception(slug, state):
        errors.append("Exact authorized Jamaica legacy-provenance asset verification failed")'''),
])
