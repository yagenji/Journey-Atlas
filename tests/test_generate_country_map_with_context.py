#!/usr/bin/env python3
"""Guard the new map wrapper against implicit changes to in-flight Countries."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import generate_country_map_with_context as wrapper


class WrapperTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.country = Path(self.temp.name) / 'country.json'
        self.country.write_text(json.dumps({'map': {'bounds': {'west': 44.45, 'south': 38.05, 'east': 50.72, 'north': 42.12}}}), encoding='utf8')
        self.output = Path(self.temp.name) / 'new-preview.svg'

    def arguments(self, *extra):
        return ['generate_country_map_with_context.py', '--country-json', str(self.country),
                '--output', str(self.output), '--source', 'natural-earth',
                '--dataset', 'coast.geojson', '--country-name', 'Azerbaijan', *extra]

    def test_wrapper_uses_json_bounds_and_targeted_source(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" '
               'data-map-projection="local-equirectangular-fit-v1">'
               '<g id="geographic-context"><path d=""/></g>'
               '<path d="M 0,0 L 10,0 L 10,10 L 0,10 Z" fill="url(#land)"/></svg>')
        def run(command, *, check):
            if 'add_country_map_context.py' in command[1]:
                self.output.write_text(svg, encoding='utf8')
        with patch.object(sys, 'argv', self.arguments()), patch.object(wrapper.subprocess, 'run', side_effect=run) as subprocess_run:
            wrapper.main()
        self.assertEqual(subprocess_run.call_count, 2)
        generating = subprocess_run.call_args_list[0].args[0]
        context = subprocess_run.call_args_list[1].args[0]
        self.assertEqual(generating[generating.index('--bounds') + 1:generating.index('--bounds') + 5],
                         ['44.45', '38.05', '50.72', '42.12'])
        self.assertIn('generate_country_map.py', generating[1])
        self.assertIn('add_country_map_context.py', context[1])
        self.assertEqual(context[context.index('--output') + 1], str(self.output))
        self.assertEqual(self.output.read_text(), svg)

    def test_rejects_uncertain_geometry_and_region_overwrites(self):
        with patch.object(sys, 'argv', self.arguments('--bounds', '0', '0', '1', '1')):
            with self.assertRaises(SystemExit):
                wrapper.main()
        data = json.loads(self.country.read_text())
        data['map']['regions'] = [{'id': 'inset'}]
        self.country.write_text(json.dumps(data))
        with patch.object(sys, 'argv', self.arguments()):
            with self.assertRaises(SystemExit):
                wrapper.main()
        data['map'].pop('regions')
        self.country.write_text(json.dumps(data))
        self.output.write_text('approved and untouchable')
        with patch.object(sys, 'argv', self.arguments()):
            with self.assertRaises(SystemExit):
                wrapper.main()
        self.assertEqual(self.output.read_text(), 'approved and untouchable')


if __name__ == '__main__':
    unittest.main()
