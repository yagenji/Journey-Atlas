#!/usr/bin/env python3
"""Report actual legacy SVG structures that need a reviewed common-map adapter."""
import json
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'
SLUGS = ('cambodia','maldives','norway','antiguabarbuda','bahrain','japan',
         'qatar','singapore','hong-kong','brunei','myanmarburma','russia',
         'bangladesh','indonesia','malaysia')
results = []
for slug in SLUGS:
    country = json.loads((ROOT / 'data/countries' / (slug + '.json')).read_text())
    config = country['map']
    source = (ROOT / config['svg']).read_text(encoding='utf-8')
    root = ET.fromstring(source)
    parents = {child: parent for parent in root.iter() for child in parent}
    paths = list(root.iter(NS+'path'))
    groups = list(root.iter(NS+'g'))
    def inherited_fill(p):
        while p is not None:
            if 'fill' in p.attrib:
                return p.attrib['fill']
            p = parents.get(p)
        return None
    def chain(p):
        parts = []
        while p is not None:
            if p.get('transform'):
                parts.append(p.get('transform'))
            p = parents.get(p)
        return parts
    record = {'slug':slug,'svg':config['svg'],
              'projection':root.get('data-map-projection'),
              'bounds':config.get('bounds'),
              'regions':[{'id':r['id'],'bounds':r['bounds'],'rect':r['rect']} for r in config.get('regions',[])],
              'path_count':len(paths),
              'explicit_fills':dict(Counter(p.get('fill','<inherited>') for p in paths)),
              'effective_fills':dict(Counter(inherited_fill(p) or '<none>' for p in paths)),
              'land_path_transforms':list(dict.fromkeys(tuple(chain(p)) for p in paths if inherited_fill(p)=='url(#land)'))[:5],
              'region_groups':[{'id':g.get('data-map-region'),'transform':g.get('transform'),
                                'clip':g.get('clip-path'),'children':len(g),
                                'child_types':dict(Counter(ch.tag.rsplit('}',1)[-1] for ch in g))}
                               for g in groups if g.get('data-map-region')],
              'root_groups':[{'fill':g.get('fill'),'transform':g.get('transform'),
                              'paths':len(list(g.iter(NS+'path')))}
                             for g in groups if g.get('fill') or g.get('transform')][:6],
              'map_style':root.get('data-map-style'),
              'has_sea_gradient':bool(re.search(r'<linearGradient\b[^>]*\bid="sea"',source)),
              'svg_bytes':len(source.encode())}
    results.append(record)
output=Path('/tmp/journey-atlas-map-context-real-previews/diagnostics.json')
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
for r in results:
    print('STRUCTURE',r['slug'],r['projection'],r['path_count'],r['effective_fills'],
          'regions',[(g['id'],g['children']) for g in r['region_groups']],
          'transforms',r['land_path_transforms'][:2])
