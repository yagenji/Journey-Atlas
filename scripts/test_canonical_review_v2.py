#!/usr/bin/env python3
"""Offline regression tests for safe canonical unpublished Country reviews."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import canonical_review_v2 as review


class CanonicalReviewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "data/countries").mkdir(parents=True)
        (self.root / "ops/country-production").mkdir(parents=True)
        self.country_path = self.root / "data/countries/example.json"
        self.state_path = self.root / "ops/country-production/example.json"
        self.country = {"schemaVersion": 2, "publicationPipelineVersion": 2, "slug": "example",
                        "region": "CENTRAL AMERICA", "map": {"bounds": {"north": 11.4, "south": 7.85}},
                        "travelTrivia": [{"icon": "mountain"}], "signatureFacts": [{"icon": "nature"}]}
        self.state = {"productionProtocolId": "2.0", "publication": {"atlasPublished": False},
                      "finalApproval": {"state": "PENDING"}, "hero": {"state": "APPROVED"},
                      "scenes": [{"state": "APPROVED"} for _ in range(8)],
                      "taste": [{"state": "APPROVED"} for _ in range(4)],
                      "sceneBatchReview": {"approval": "APPROVED"},
                      "tasteBatchReview": {"approval": "APPROVED"},
                      "assetHandoff": {"state": "PASS", "verifiedRasterCount": 13},
                      "reviewPreview": {"state": "DONE", "browserQa": "PASS",
                                        "url": "https://example.invalid/reviews/example/countries/example/"}}
        self.put(self.root / "data/atlas-destinations.json",
                 {"destinations": [{"slug": "example", "iso2": "CR", "atlasPublished": False}]})
        self.put(self.root / "data/region-taxonomy.json",
                 {"regions": [{"labelEn": "CENTRAL AMERICA", "iso2": ["CR"]}]})
        self.put(self.country_path, self.country)
        self.put(self.state_path, self.state)
        self.root_patch = patch.object(review, "ROOT", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temp.cleanup()

    @staticmethod
    def put(path, payload):
        path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")

    def test_staging_does_not_publish_or_approve(self):
        review.prepare("example")
        data = review.read(self.country_path)
        state = review.read(self.state_path)
        self.assertEqual(data["region"], "CENTRAL AMERICA / 10°N")
        self.assertEqual(data["travelTrivia"][0]["icon"], "landscape")
        self.assertEqual(data["signatureFacts"][0]["icon"], "leaf")
        self.assertEqual(state["reviewDeployment"]["state"], "DEPLOYING")
        self.assertEqual(state["reviewDeployment"]["productionVerification"], "PENDING")
        self.assertEqual(state["finalApproval"]["state"], "PENDING")
        self.assertIs(review.registry_row("example")["atlasPublished"], False)
        review.verified("example")
        state = review.read(self.state_path)
        self.assertEqual(state["reviewDeployment"]["productionVerification"], "LIVE_BROWSER_QA_PASS")
        self.assertEqual(state["next"]["action"], "REVIEW_CANONICAL_URL")
        self.assertEqual(state["finalApproval"]["state"], "PENDING")

    def test_block_published_and_premature_approval(self):
        self.state["finalApproval"]["state"] = "APPROVED"
        self.put(self.state_path, self.state)
        with self.assertRaisesRegex(ValueError, "final approval"):
            review.prepare("example")
        self.state["finalApproval"]["state"] = "PENDING"
        self.state["publication"]["atlasPublished"] = True
        self.put(self.state_path, self.state)
        with self.assertRaisesRegex(ValueError, "published"):
            review.prepare("example")

    def test_live_qa_cannot_be_recorded_without_staging(self):
        with self.assertRaisesRegex(ValueError, "URL mismatch"):
            review.verified("example")


if __name__ == "__main__":
    unittest.main()