#!/usr/bin/env python3
"""Check actual OSM/ODbL attribution for the registry-selected staged maps.

Use the existing disposable preflight's manifest; do not hardcode a Country count,
alter Country data, change source SVGs or add a new workflow.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from qa_published_browser import BASE_URL, VIEWPORTS, make_driver, set_viewport, wait_for_country

MANIFEST = Path('/tmp/journey-atlas-map-context-rollout-stage/manifest.json')
COPYRIGHT = 'https://www.openstreetmap.org/copyright'
NS = '{http://www.w3.org/2000/svg}'
OSM = re.compile(r'OpenStreetMap|\bODbL\b', re.I)
CAPTURE = {'singapore', 'macau', 'bahrain', 'iceland'}
SCREENSHOTS = ROOT / 'qa-map-context-browser-output' / 'source-credit'


def source_provenance(slug: str, map_ref: str) -> tuple[bool, bool]:
    country = json.loads((ROOT / 'data' / 'countries' / f'{slug}.json').read_text(encoding='utf-8'))
    assert country['map']['svg'] == map_ref, f'Map reference changed: {slug}'
    source = str(country['map'].get('source') or '')
    root = ET.parse(ROOT / map_ref).getroot()
    context = next((g for g in root.iter(NS + 'g') if g.get('id') == 'geographic-context'), None)
    desc = next(context.iter(NS + 'desc'), None) if context is not None else None
    metadata = ' '.join(''.join(node.itertext()) for node in root.iter(NS + 'metadata'))
    provenance = ''.join(desc.itertext()) if desc is not None else ''
    has_osm = bool(OSM.search(source + ' ' + provenance + ' ' + metadata))
    return has_osm, bool(OSM.search(source))


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    entries = manifest['entries']
    assert len(entries) == manifest['selectedCount'] and len(entries) == len({row['slug'] for row in entries})
    attribution = {row['slug']: source_provenance(row['slug'], row['mapRef']) for row in entries}
    assert all(slug in attribution for slug in CAPTURE)
    assert attribution['singapore'] == (True, True) and attribution['macau'] == (True, True), attribution
    assert attribution['bahrain'][0] and not attribution['iceland'][0], attribution
    osm_slugs = sorted(slug for slug, (osm, _) in attribution.items() if osm)
    mismatch = sorted(slug for slug in osm_slugs if not attribution[slug][1])
    assert 'antiguabarbuda' in mismatch, 'Historic Antigua source should exercise SVG-provenance fallback'
    print(f'OSM provenance audit: {len(osm_slugs)} of {len(entries)} maps; SVG-only/JSON mismatch: {mismatch}', flush=True)
    samples = osm_slugs + ['iceland']
    driver = make_driver()
    try:
        for slug in samples:
            expected = slug != 'iceland'
            for name, viewport in VIEWPORTS.items():
                set_viewport(driver, viewport)
                driver.get(f'{BASE_URL}/countries/{slug}/')
                wait_for_country(driver)
                driver.execute_script("document.querySelector('#country-map-art').scrollIntoView({block:'center'})")
                WebDriverWait(driver, 35).until(lambda d: d.execute_script("const i=document.querySelector('#country-map-art .map-base');return !!i&&i.complete&&i.naturalWidth>0"))
                if expected:
                    WebDriverWait(driver, 35).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '.map-legend--below .map-legend__source-credit')) == 1)
                credits = driver.find_elements(By.CSS_SELECTOR, '.map-legend--below .map-legend__source-credit')
                assert len(credits) == int(expected), f'{slug}/{name}: credits={len(credits)} expected={expected}'
                if credits:
                    credit = credits[0]
                    assert credit.is_displayed(), f'{slug}/{name}: OSM source link hidden'
                    assert credit.get_attribute('href') == COPYRIGHT, f'{slug}/{name}: wrong credit URL'
                    assert 'OpenStreetMap contributors' in credit.text and 'ODbL 1.0' in credit.text
                    assert driver.execute_script('const e=arguments[0],r=e.getBoundingClientRect();return r.width>60&&r.height>0&&getComputedStyle(e).visibility==="visible"', credit)
                    assert credit.get_attribute('tabindex') is None, f'{slug}/{name}: source link focus order changed'
                if slug in CAPTURE:
                    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
                    driver.find_element(By.CSS_SELECTOR, '.map-column').screenshot(str(SCREENSHOTS / f'{slug}-{name}.png'))
                print(f'SOURCE CREDIT PASS {slug}/{name}: expected={expected}', flush=True)
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
