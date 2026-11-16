"""「知っておきたいこと」は国ページと同じく、詳細地域でも3項目に揃える。"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RegionNotesCount(unittest.TestCase):
    def test_every_region_has_exactly_three_travel_notes(self):
        for path in sorted((ROOT / 'data/regions').glob('*/*.json')):
            with self.subTest(region=path.stem):
                notes = json.loads(path.read_text())['notes']
                self.assertEqual(len(notes), 3)
                for note in notes:
                    self.assertTrue(note['title'] and note['text'])

    def test_every_country_has_exactly_three_tips(self):
        for path in sorted((ROOT / 'data/countries').glob('*.json')):
            data = json.loads(path.read_text())
            if 'tips' in data:
                with self.subTest(country=path.stem):
                    self.assertEqual(len(data['tips']), 3)
