#!/usr/bin/env python3
"""Regression checks for idempotent Pipeline v2 review state."""
from __future__ import annotations
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import publication_pipeline_v2 as pipeline

class ReviewIdempotenceTest(unittest.TestCase):
    def test_completed_preview_is_valid_but_not_redeployed_for_state_only_commit(self):
        state = {
            "productionProtocolId": "2.0",
            "hero": {"state": "APPROVED"},
            "scenes": [{"state": "APPROVED"} for _ in range(8)],
            "taste": [{"state": "APPROVED"} for _ in range(4)],
            "sceneBatchReview": {"approval": "APPROVED"},
            "tasteBatchReview": {"approval": "APPROVED"},
            "assetHandoff": {"state": "PASS", "verifiedRasterCount": 13},
            "finalApproval": {"state": "PENDING"},
            "publication": {"state": "DRAFT", "atlasPublished": False},
        }
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','-C',str(root),'config','user.email','qa@example.invalid'],check=True)
            subprocess.run(['git','-C',str(root),'config','user.name','QA'],check=True)
            country = root/'data/countries/example.json'
            country.parent.mkdir(parents=True)
            country.write_text(json.dumps({'slug':'example'}))
            subprocess.run(['git','-C',str(root),'add','.'],check=True)
            subprocess.run(['git','-C',str(root),'commit','-qm','reviewed source'],check=True)
            reviewed = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
            state['reviewPreview']={'state':'DONE','browserQa':'PASS','url':'https://example.invalid/reviews/example/', 'sourceCommit':reviewed}
            with patch.object(pipeline, 'ROOT', root), patch.object(pipeline, 'is_active', return_value=True):
                self.assertEqual(pipeline.review_ready_errors('example',state),[])
                self.assertFalse(pipeline.review_needed('example',state))
                (root/'ops').mkdir()
                (root/'ops/state.txt').write_text('state only')
                subprocess.run(['git','-C',str(root),'add','.'],check=True)
                subprocess.run(['git','-C',str(root),'commit','-qm','reconcile state'],check=True)
                self.assertFalse(pipeline.review_needed('example',state))
                country.write_text(json.dumps({'slug':'example','updated':True}))
                subprocess.run(['git','-C',str(root),'add','.'],check=True)
                subprocess.run(['git','-C',str(root),'commit','-qm','revise country'],check=True)
                self.assertTrue(pipeline.review_needed('example',state))
                state['publication']['atlasPublished']=True
                self.assertIn('Country is already published',pipeline.review_ready_errors('example',state))
                self.assertFalse(pipeline.review_needed('example',state))

if __name__=='__main__':
    unittest.main()
