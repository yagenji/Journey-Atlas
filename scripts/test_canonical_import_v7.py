#!/usr/bin/env python3
"""Historical regression: squash-import a reviewed, still-unpublished Country."""
from __future__ import annotations

import copy
import unittest

import country_production_state_v7 as v7
import validate_canonical_import_v7 as audit

BASE = "1485178e6393c6fbd32435a10e0ac5b07b02f44d"
IMPORTED = "c8652fc2d946a71cf40caa784f82813720318e6d"
PATH = "ops/country-production/costarica.json"


class CanonicalImportAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = v7.git_json(IMPORTED, PATH)
        assert isinstance(cls.original, dict), "historical Costa Rica state is missing"

    def test_audited_real_import(self):
        valid = audit.canonical_import(IMPORTED, PATH, self.original)
        if not valid:
            source = self.original["reviewPreview"].get("sourceCommit")
            prior = v7.git_json(source, PATH) if source else None
            self.fail(
                "historical canonical import rejected: "
                f"source={source} sourcePresent={isinstance(prior, dict)} "
                f"sourceStateErrors={v7.validate_state_dict(prior, PATH) if prior else 'missing'} "
                f"importedStateErrors={v7.validate_state_dict(self.original, PATH)} "
                f"approvedFieldsUnchanged="
                f"{all(self.original.get(key) == (prior or {}).get(key) for key in ('hero', 'scenes', 'taste', 'sceneBatchReview', 'tasteBatchReview', 'recoveryMigrations', 'assetHandoff'))} "
                f"assetTreesEqual={audit.immutable_assets(source, 'costarica') == audit.immutable_assets(IMPORTED, 'costarica') if source else False} "
                f"importedAssetCount={len([x for x in audit.immutable_assets(IMPORTED, 'costarica') if '/approved/' in x])}"
            )
        self.assertEqual(audit.validate_range(BASE, IMPORTED), [])

    def test_source_provenance_is_not_optional(self):
        state = copy.deepcopy(self.original)
        state["reviewPreview"].pop("sourceCommit")
        self.assertFalse(audit.canonical_import(IMPORTED, PATH, state))

    def test_false_approval_cannot_be_imported(self):
        state = copy.deepcopy(self.original)
        state["scenes"][0]["approvedGenerationId"] = "fabricated-generation"
        self.assertFalse(audit.canonical_import(IMPORTED, PATH, state))

    def test_publication_gate_cannot_be_bypassed(self):
        state = copy.deepcopy(self.original)
        state["finalApproval"]["state"] = "APPROVED"
        self.assertFalse(audit.canonical_import(IMPORTED, PATH, state))
        state = copy.deepcopy(self.original)
        state["publication"]["atlasPublished"] = True
        self.assertFalse(audit.canonical_import(IMPORTED, PATH, state))

    def test_review_must_be_on_canonical_noindex_route(self):
        state = copy.deepcopy(self.original)
        state["reviewDeployment"]["url"] = "https://example.com/false-review"
        self.assertFalse(audit.canonical_import(IMPORTED, PATH, state))
        state = copy.deepcopy(self.original)
        state["reviewPreview"]["browserQa"] = "FAIL"
        self.assertFalse(audit.canonical_import(IMPORTED, PATH, state))

    def test_regular_initializer_still_rejects_preapproval(self):
        state = copy.deepcopy(self.original)
        state["reviewDeployment"] = {"state": "NOT_STARTED"}
        self.assertFalse(audit.canonical_import(IMPORTED, PATH, state))
        errors = v7.validate_transition(None, state, PATH)
        self.assertTrue(any("cannot initialize with APPROVED scenes" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
