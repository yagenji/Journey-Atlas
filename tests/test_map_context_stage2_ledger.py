#!/usr/bin/env python3
"""Fail closed unless the Stage 2 review ledger covers the exact current roster."""
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from stage_map_context_rollout import derive_roster, protected_target_paths  # noqa: E402
from xml.etree import ElementTree as ET

LEDGER=ROOT/'ops/map-context-stage2-review.json'


class Stage2ReviewLedgerTest(unittest.TestCase):
    def test_use_rendered_target_is_protected(self):
        # Hong Kong once rendered its land through <use href="#land-shape">; keep
        # protecting that pattern with a fixture now that the map draws one path.
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760">'
               '<g id="land-shape"><path d="M 0,0 L 10,0 L 10,10 Z"/></g>'
               '<use href="#land-shape" fill="url(#land)" filter="url(#shadow)"/>'
               '<use href="#land-shape" fill="url(#land)"/></svg>')
        signatures = protected_target_paths(ET.fromstring(svg))
        self.assertEqual(len(signatures), 1)
        self.assertTrue(signatures[0].startswith('use:land-shape:'))
        self.assertIn('<ns0:path', signatures[0])

    def test_hong_kong_target_is_one_protected_path(self):
        config = json.loads((ROOT / 'data/countries/hong-kong.json').read_text(encoding='utf-8'))
        root = ET.parse(ROOT / config['map']['svg']).getroot()
        signatures = protected_target_paths(root)
        self.assertEqual(len(signatures), 1)
        self.assertTrue(signatures[0].startswith('path:'))

    def test_ledger_covers_exact_selected_roster(self):
        ledger=json.loads(LEDGER.read_text(encoding='utf-8'))
        self.assertEqual(ledger['stage'],'2')
        self.assertEqual(ledger['stageStatus'],'COMPLETE')
        self.assertFalse(ledger['promotionEligible'])
        self.assertEqual(ledger['canonicalRegistryCount'],201)

        entries=ledger['entries']
        self.assertEqual(len(entries),ledger['selectedRosterCount'])
        self.assertEqual(len({e['slug'] for e in entries}),len(entries))
        self.assertTrue(all(e['status']=='PASS' for e in entries))
        self.assertTrue(all(e['promotionEligible'] is False for e in entries))

        roster=derive_roster()
        roster_slugs={item['slug'] for item in roster}
        ledger_slugs={entry['slug'] for entry in entries}
        self.assertEqual(ledger_slugs,roster_slugs)
        self.assertEqual(len(roster),ledger['selectedRosterCount'])

        modes={}
        for entry in entries:
            modes[entry['reviewMode']]=modes.get(entry['reviewMode'],0)+1
            country=json.loads(
                (ROOT/'data/countries'/f"{entry['slug']}.json").read_text(encoding='utf-8')
            )
            self.assertTrue(country['map']['source'].strip())
            self.assertTrue((ROOT/country['map']['svg']).is_file())

        self.assertEqual(modes,{
            'individual-source-review':29,
            'existing-context-source-review':5,
            'common-source-exact-clip-review':75,
        })
        self.assertEqual(ledger['counts']['total'],len(entries))
        self.assertEqual(ledger['counts']['individualSourceReview'],29)
        self.assertEqual(ledger['counts']['existingContextSourceReview'],5)
        self.assertEqual(ledger['counts']['commonSourceExactClipReview'],75)


if __name__=='__main__':
    unittest.main()
