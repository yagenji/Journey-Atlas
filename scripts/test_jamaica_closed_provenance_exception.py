#!/usr/bin/env python3
"""Fail-closed tests for the sole immutable Jamaica legacy-provenance exception."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import jamaica_closed_provenance_exception as ex


class JamaicaExceptionTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        raw = (ex.ROOT / ex.CASE_PATH).read_bytes()
        policy = json.loads(raw)
        images = self.root / "assets/images/jamaica/approved"
        images.mkdir(parents=True)
        for i, (key, row) in enumerate(policy["assets"].items()):
            data = f"independently-identified-existing-image-{key}-{i}".encode()
            (images / row["filename"]).write_bytes(data)
            row["gitBlobSha"] = ex.blob_sha(data)
        manifest = self.root / ex.CASE_PATH
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps(policy))
        self.patch = patch.object(ex, "CASE_GIT_BLOB", ex.blob_sha(manifest.read_bytes()))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        contents = [f"assets/images/jamaica/approved/{row['filename']}" for row in policy['assets'].values()]
        country = {"hero": {"image": contents[0]},
                   "scenes": [{"image": x} for x in contents[1:9]],
                   "taste": {"items": [{"image": x} for x in contents[9:]]}}
        dest = self.root / "data/countries/jamaica.json"
        dest.parent.mkdir(parents=True)
        dest.write_text(json.dumps(country))
        self.state = {"slug":"jamaica",
                      "closedProvenanceException":{"id":ex.CASE_ID,"status":"APPLIED","sourceCommit":"34cf8a3db3dfbd3d1df2102b4f73df2268110862","authorizationDate":"2026-09-19"},
                      "hero":{"state":"APPROVED","approvedGenerationId":policy['assets']['HERO']['generationId'],"asset":contents[0]},
                      "scenes":[{"id":k,"state":"NOT_STARTED","asset":None} for k in ex.SCENE_IDS],
                      "taste":[{"id":k,"state":"NOT_STARTED","asset":None} for k in ex.FOOD_IDS],
                      "sceneBatchReview":{"approval":"PENDING","rounds":[]},
                      "tasteBatchReview":{"approval":"PENDING","rounds":[]},
                      "assetHandoff":{"state":"PASS","mode":"USER_HANDOFF","verifiedRasterCount":13,"verifiedAt":"2026-09-19T10:00:00+09:00"}}

    def test_exact_original_case_passes(self):
        self.assertEqual(ex.validate(self.state, self.root), [])

    def test_other_country_fails(self):
        edited=copy.deepcopy(self.state);edited['slug']='cuba'
        self.assertTrue(ex.validate(edited,self.root))

    def test_asset_swap_fails(self):
        file=self.root/'assets/images/jamaica/approved/negril-west-end.webp'
        file.write_bytes(b'changed raster')
        self.assertIn('S01: original raster bytes missing or changed',ex.validate(self.state,self.root))

    def test_policy_change_fails_even_if_manifest_claims_new_bytes(self):
        path=self.root/ex.CASE_PATH
        path.write_text(path.read_text()+'\n')
        self.assertIn('Pinned Jamaica exception policy is missing or has changed',ex.validate(self.state,self.root))

    def test_faked_generation_id_fails(self):
        edited=copy.deepcopy(self.state)
        edited['scenes'][0]['approvedGenerationId']='a-made-up-id'
        self.assertTrue(any('no unverified generation ID' in x for x in ex.validate(edited,self.root)))

    def test_fabricated_batch_approval_fails(self):
        edited=copy.deepcopy(self.state)
        edited['sceneBatchReview']={'approval':'APPROVED','rounds':[]}
        self.assertTrue(any('historical batch approvals' in x for x in ex.validate(edited,self.root)))

    def test_missing_real_handoff_fails(self):
        edited=copy.deepcopy(self.state);edited['assetHandoff']['state']='PENDING'
        self.assertTrue(any('real verified USER_HANDOFF PASS' in x for x in ex.validate(edited,self.root)))


if __name__=='__main__':unittest.main()
