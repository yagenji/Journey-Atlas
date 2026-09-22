#!/usr/bin/env python3
"""Targeted real-browser source-credit QA on disposable staged Country pages.

The existing published-page browser audit checks that maps load; this checks the
additional OSM/ODbL attribution requirement against actual SVG provenance.
No production assets or publication flags are modified.
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

SAMPLES = ("singapore", "macau", "bahrain", "iceland")
COPYRIGHT = "https://www.openstreetmap.org/copyright"
NS = "{http://www.w3.org/2000/svg}"


def expected_osm(slug: str) -> bool:
    country = json.loads((ROOT / "data" / "countries" / f"{slug}.json").read_text(encoding="utf-8"))
    source = str(country["map"].get("source") or "")
    root = ET.parse(ROOT / country["map"]["svg"]).getroot()
    context = next((g for g in root.iter(NS + "g") if g.get("id") == "geographic-context"), None)
    description = next(context.iter(NS + "desc"), None) if context is not None else None
    provenance = "".join(description.itertext()) if description is not None else ""
    return bool(re.search(r"OpenStreetMap|\bODbL\b", source + " " + provenance, re.I))


def main() -> None:
    expected = {slug: expected_osm(slug) for slug in SAMPLES}
    assert expected["singapore"] and expected["macau"] and expected["bahrain"], expected
    assert not expected["iceland"], expected
    driver = make_driver()
    try:
        for slug in SAMPLES:
            for name, viewport in VIEWPORTS.items():
                set_viewport(driver, viewport)
                driver.get(f"{BASE_URL}/countries/{slug}/")
                wait_for_country(driver)
                driver.execute_script("document.querySelector('#country-map-art').scrollIntoView({block:'center'})")
                WebDriverWait(driver, 35).until(lambda d: d.execute_script("const i=document.querySelector('#country-map-art .map-base');return !!i&&i.complete&&i.naturalWidth>0"))
                if expected[slug]:
                    WebDriverWait(driver, 35).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '.map-legend--below .map-legend__source-credit')) == 1)
                credits = driver.find_elements(By.CSS_SELECTOR, '.map-legend--below .map-legend__source-credit')
                assert len(credits) == int(expected[slug]), f"{slug}/{name}: credits={len(credits)} expected={expected[slug]}"
                if credits:
                    credit = credits[0]
                    assert credit.is_displayed(), f"{slug}/{name}: OSM source link hidden"
                    assert credit.get_attribute('href') == COPYRIGHT, f"{slug}/{name}: wrong credit URL"
                    assert 'OpenStreetMap contributors' in credit.text and 'ODbL 1.0' in credit.text
                    assert driver.execute_script('const e=arguments[0],r=e.getBoundingClientRect();return r.width>60&&r.height>0&&getComputedStyle(e).visibility==="visible"', credit)
                    assert credit.get_attribute('tabindex') is None, f"{slug}/{name}: credit unexpectedly changes focus order"
                print(f"SOURCE CREDIT PASS {slug}/{name}: expected={expected[slug]}", flush=True)
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
