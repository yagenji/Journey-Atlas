"""Run focused Brunei and Monaco review-only previews in the existing preflight.

Never substitutes generated land into the published map or marks geographic QA PASS.
"""
from __future__ import annotations
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/tmp/journey-atlas-map-context-real-previews/priority-review')


class PriorityGeographyReview(unittest.TestCase):
    def _run(self,slug,script):
        folder=OUT/slug
        folder.mkdir(parents=True,exist_ok=True)
        subprocess.run([sys.executable,str(ROOT/'scripts'/script),
                        '--repo',str(ROOT),'--output-dir',str(folder)],
                       cwd=ROOT,check=True,timeout=240)
        report=json.loads((folder/'report.json').read_text())
        self.assertIn('HOLD', report['status'])
        self.assertTrue((folder/(slug+'-reviewed.png' if slug=='brunei' else 'monaco-current.png')).is_file())
        return report

    def test_brunei_malaysia_source_and_original_path(self):
        result=self._run('brunei','review_brunei_malaysia.py')
        self.assertTrue(result['nationalPathsIdentical'])
        self.assertGreater(result['domesticIslandRemovedFromForeignContextSvgPx2'],400)
        self.assertEqual(result['decodedSize'],[1200,760])

    def test_monaco_latest_osm_french_context_and_original_path(self):
        result=self._run('monaco','review_monaco_france.py')
        self.assertEqual(result['protectedPaths'],1)
        self.assertEqual(result['fullRaster'],[1200,760])
        self.assertGreater(result['contextRingCount'],0)


if __name__=='__main__':unittest.main()
