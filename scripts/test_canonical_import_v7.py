#!/usr/bin/env python3
"""Historical regression: squash-import a reviewed, still-unpublished Country."""
from __future__ import annotations

import copy
import subprocess
import unittest
from unittest import mock

import country_production_state_v7 as v7
import validate_canonical_import_v7 as audit

BASE = "1485178e6393c6fbd32435a10e0ac5b07b02f44d"
IMPORTED = "c8652fc2d946a71cf40caa784f82813720318e6d"
SOURCE = "da4f4bc74b3883dbc0ff5efe5aec768d888db225"
# PR #826's reviewed source is an ancestor of its immutable head. A normal
# checkout of current branches can omit that source after a squash merge.
REVIEW_REF = "refs/pull/826/head"
PATH = "ops/country-production/costarica.json"


class CanonicalImportAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = v7.git_json(IMPORTED, PATH)
        assert isinstance(cls.original, dict), "historical Costa Rica state is missing"
        assert cls.original.get("reviewPreview", {}).get("sourceCommit") == SOURCE, (
            "historical fixture source commit changed; re-audit the approval provenance"
        )
        if v7.git_json(SOURCE, PATH) is None:
            # Fetch only the historical review PR, not every branch/tag again.
            # Fail closed if its pinned source object is still inaccessible.
            fetch = subprocess.run(
                ["git", "fetch", "--no-tags", "--depth=32", "origin", REVIEW_REF],
                cwd=v7.ROOT, capture_output=True, text=True,
            )
            assert fetch.returncode == 0, (
                f"cannot fetch historical review {REVIEW_REF}: {fetch.stderr.strip()}"
            )
            assert isinstance(v7.git_json(SOURCE, PATH), dict), (
                f"historical approved source {SOURCE} is absent after fetching {REVIEW_REF}"
            )

    def test_audited_real_import(self):
        self.assertTrue(audit.canonical_import(IMPORTED, PATH, self.original))
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

    def test_audited_slug_migration_preserves_entire_state(self):
        old_path = "ops/country-production/oldslug.json"
        new_path = "ops/country-production/newslug.json"
        old_state = copy.deepcopy(self.original)
        old_state["slug"] = "oldslug"
        new_state = copy.deepcopy(old_state)
        new_state["slug"] = "newslug"
        registry = {"destinations": [{"slug": "newslug", "atlasPublished": False}]}
        country = {"slug": "newslug", "publicationPipelineVersion": 2}

        def fake_git_json(commit, path):
            if commit == "parent" and path == old_path:
                return old_state
            if commit == "commit" and path == old_path:
                return None
            if commit == "commit" and path == "data/atlas-destinations.json":
                return registry
            if commit == "commit" and path == "data/countries/newslug.json":
                return country
            return None

        def fake_git(*args):
            if args and args[0] == "diff-tree":
                return f"D\t{old_path}\nA\t{new_path}"
            if args and args[0] == "diff":
                return ""
            raise AssertionError(args)

        with (
            mock.patch.object(v7, "first_parent", return_value="parent"),
            mock.patch.object(v7, "git_json", side_effect=fake_git_json),
            mock.patch.object(v7, "validate_state_dict", return_value=[]),
            mock.patch.object(audit, "git", side_effect=fake_git),
        ):
            self.assertTrue(audit.canonical_slug_migration("commit", new_path, new_state))
            changed = copy.deepcopy(new_state)
            changed["taste"][0]["approvedGenerationId"] = "fabricated"
            self.assertFalse(audit.canonical_slug_migration("commit", new_path, changed))



class ClosedProvenanceCanonicalImportTest(unittest.TestCase):
    def state(self):
        return {
            "slug": "stvincentgrenadines",
            "productionProtocolId": "2.0",
            "publicationPipelineVersion": 2,
            "phase": "QA",
            "imageGenerationPolicy": {"revision": 7},
            "finalApproval": {"state": "PENDING"},
            "publication": {"state": "DRAFT", "atlasPublished": False},
            "reviewPreview": {
                "state": "DONE",
                "browserQa": "PASS",
                "sourceCommit": "a" * 40,
            },
            "reviewDeployment": {
                "state": "DEPLOYING",
                "productionVerification": "PENDING",
                "atlasPublished": False,
                "url": "https://atlas.yagenji.com/countries/stvincentgrenadines/",
            },
            "assetHandoff": {
                "state": "PASS",
                "expectedRasterCount": 13,
                "verifiedRasterCount": 13,
            },
            "map": {"state": "APPROVED"},
            "preVisualBuild": {"state": "PASS"},
            "sceneBatchReview": {"approval": "PENDING", "rounds": []},
            "tasteBatchReview": {"approval": "PENDING", "rounds": []},
            "closedProvenanceException": {"id": "exact-case"},
            "hero": {"state": "NOT_STARTED"},
            "scenes": [{"id": f"S{i:02d}", "state": "NOT_STARTED"} for i in range(1, 9)],
            "taste": [{"id": f"FOOD{i:02d}", "state": "NOT_STARTED"} for i in range(1, 5)],
        }

    def test_exact_closed_provenance_import_needs_no_synthetic_uuid_or_batch_approval(self):
        after = self.state()
        source = copy.deepcopy(after)
        country = {"slug": "stvincentgrenadines", "publicationPipelineVersion": 2}
        registry = {"destinations": [{"slug": "stvincentgrenadines", "atlasPublished": False}]}
        assets = [f"100644 blob deadbeef\tassets/images/stvincentgrenadines/approved/{i}.webp" for i in range(13)]

        def fake_json(commit, path):
            if commit == "a" * 40 and path == "ops/country-production/stvincentgrenadines.json":
                return source
            if commit == "import" and path == "data/countries/stvincentgrenadines.json":
                return country
            if commit == "import" and path == "data/atlas-destinations.json":
                return registry
            return None

        with (
            mock.patch.object(v7, "git_json", side_effect=fake_json),
            mock.patch.object(v7, "validate_state_dict", return_value=[]),
            mock.patch.object(audit, "immutable_assets", return_value=assets),
            mock.patch.object(audit, "verified_closed_provenance_exception", return_value=True),
        ):
            self.assertTrue(
                audit.canonical_import(
                    "import", "ops/country-production/stvincentgrenadines.json", after
                )
            )

    def test_closed_provenance_import_fails_closed_without_exact_helper(self):
        after = self.state()
        with mock.patch.object(audit, "verified_closed_provenance_exception", return_value=False):
            self.assertFalse(
                audit.canonical_import(
                    "import", "ops/country-production/stvincentgrenadines.json", after
                )
            )


if __name__ == "__main__":
    unittest.main()
