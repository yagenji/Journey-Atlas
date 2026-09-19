import unittest
from unittest.mock import patch
import publication_pipeline_v2 as pipeline

class CanonicalReviewPublicationGate(unittest.TestCase):
    def setUp(self):
        self.base = {"phase":"REVIEW", "contentRef":"main", "stateRef":"main",
                     "productionProtocolId":"2.0", "qa":{"state":"PASS"},
                     "reviewPreview":{"state":"NOT_STARTED","browserQa":"NOT_STARTED","url":None},
                     "reviewDeployment":{"state":"DONE","url":"https://atlas.yagenji.com/countries/grenada/",
                                         "productionVerification":"LIVE_BROWSER_QA_PASS","atlasPublished":False},
                     "publication":{"state":"DRAFT","atlasPublished":False},
                     "finalApproval":{"state":"APPROVED"}}
    @patch.object(pipeline,'is_active',return_value=True)
    def test_verified_canonical_review(self,_active):
        self.assertEqual(pipeline.publish_ready_errors('grenada',self.base),[])
        complete={**self.base,'phase':'COMPLETE',
                  'publication':{'state':'PUBLISHED','atlasPublished':True,'pipelineVersion':2},
                  'reviewDeployment':{**self.base['reviewDeployment'],'productionVerification':'CI_GATED',
                                      'prePublicationReviewVerification':'LIVE_BROWSER_QA_PASS'}}
        self.assertEqual(pipeline.publish_ready_errors('grenada',complete),[])
    @patch.object(pipeline,'is_active',return_value=True)
    def test_unverified_canonical_review_rejected(self,_active):
        for override in ({'productionVerification':'PENDING'}, {'url':'https://atlas.yagenji.com/countries/other/'},
                         {'state':'NOT_STARTED'}):
            state={**self.base,'reviewDeployment':{**self.base['reviewDeployment'],**override}}
            self.assertTrue(pipeline.publish_ready_errors('grenada',state))
    @patch.object(pipeline,'is_active',return_value=True)
    def test_user_approval_remains_required(self,_active):
        state={**self.base,'finalApproval':{'state':'PENDING'}}
        self.assertIn('finalApproval must be APPROVED',pipeline.publish_ready_errors('grenada',state))

if __name__=='__main__': unittest.main()
