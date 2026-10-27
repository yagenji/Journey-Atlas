#!/usr/bin/env python3
"""Check map data credits (data/map-data-sources.json) for the registry-selected staged maps.

Use the existing disposable preflight's manifest; do not hardcode a Country count,
alter Country data, change source SVGs or add a new workflow.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from qa_published_browser import BASE_URL, VIEWPORTS, make_driver, set_viewport, wait_for_country

MANIFEST = Path('/tmp/journey-atlas-map-context-rollout-stage/manifest.json')
COPYRIGHT = 'https://www.openstreetmap.org/copyright'
NS = '{http://www.w3.org/2000/svg}'
OSM = re.compile(r'OpenStreetMap', re.I)
CAPTURE = {'singapore', 'macau', 'bahrain', 'iceland'}
SCREENSHOTS = ROOT / 'qa-map-context-browser-output' / 'source-credit'


def source_provenance(slug: str, map_ref: str) -> tuple[bool, bool]:
    """(map draws OpenStreetMap data, registry credits list osm)."""
    country = json.loads((ROOT / 'data' / 'countries' / f'{slug}.json').read_text(encoding='utf-8'))
    assert country['map']['svg'] == map_ref, f'Map reference changed: {slug}'
    registry = json.loads((ROOT / 'data' / 'map-data-sources.json').read_text(encoding='utf-8'))
    credits = registry['countries'].get(slug) or []
    return 'osm' in credits, 'osm' in credits


def capture_supplementary_screenshot(driver, slug: str, viewport: str) -> None:
    """Screenshot is evidence only: renderer timeout must not mask valid credit QA.

    The complete published-Country browser audit above independently captures
    full-page screenshots for all 109 Countries at all three viewports.
    """
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOTS / f'{slug}-{viewport}.png'
    try:
        driver.find_element(By.CSS_SELECTOR, '.map-column').screenshot(str(path))
    except (TimeoutException, WebDriverException) as exc:
        print(f'SUPPLEMENTARY MAP SCREENSHOT: element capture unavailable {slug}/{viewport}: {type(exc).__name__}', flush=True)
        try:
            if driver.save_screenshot(str(path)):
                print(f'SUPPLEMENTARY MAP SCREENSHOT: viewport fallback saved {slug}/{viewport}', flush=True)
            else:
                print(f'SUPPLEMENTARY MAP SCREENSHOT: viewport fallback unavailable {slug}/{viewport}', flush=True)
        except (TimeoutException, WebDriverException) as fallback:
            print(f'SUPPLEMENTARY MAP SCREENSHOT: no capture {slug}/{viewport}: {type(fallback).__name__}', flush=True)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    entries = manifest['entries']
    assert len(entries) == manifest['selectedCount'] and len(entries) == len({row['slug'] for row in entries})
    attribution = {row['slug']: source_provenance(row['slug'], row['mapRef']) for row in entries}
    assert all(slug in attribution for slug in CAPTURE)
    assert attribution['singapore'] == (True, True) and attribution['macau'] == (True, True), attribution
    assert attribution['bahrain'][0] and not attribution['iceland'][0], attribution
    osm_slugs = sorted(slug for slug, (osm, _) in attribution.items() if osm)
    print(f'OSM credit audit: {len(osm_slugs)} of {len(entries)} maps', flush=True)
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
                    WebDriverWait(driver, 35).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '#country-map-art .map-osm-credit')) == 1)
                credits = driver.find_elements(By.CSS_SELECTOR, '#country-map-art .map-osm-credit')
                assert len(credits) == int(expected), f'{slug}/{name}: osm credits={len(credits)} expected={expected}'
                if credits:
                    credit = credits[0]
                    assert credit.is_displayed(), f'{slug}/{name}: OSM credit hidden'
                    assert credit.get_attribute('href') == COPYRIGHT, f'{slug}/{name}: wrong credit URL'
                    assert credit.text == '© OpenStreetMap contributors'
                    # Inside the map frame, in its bottom-right corner.
                    assert driver.execute_script("""const c=arguments[0].getBoundingClientRect(),m=document.querySelector('#country-map-art').getBoundingClientRect();
                      return c.width>60&&c.right<=m.right+0.5&&c.bottom<=m.bottom+0.5&&c.left>m.left+m.width/2&&c.top>m.top+m.height/2""", credit), f'{slug}/{name}: credit outside map corner'
                print(f'SOURCE CREDIT PASS {slug}/{name}: expected={expected}', flush=True)
                if slug in CAPTURE:
                    capture_supplementary_screenshot(driver, slug, name)
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
