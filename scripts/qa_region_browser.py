#!/usr/bin/env python3
"""Browser QA for canonical sub-Country Region pages using the shared Country driver.

Runs for only relevant parents when QA_PARENT_SLUGS is set, otherwise for all
reviewable Regions. No per-Country workflows or temporary QA configuration.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import qa_published_browser as country_qa

ROOT = Path(__file__).resolve().parents[1]
REGIONS = ROOT / "data" / "regions"
BASE_URL = os.environ.get("QA_BASE_URL", "https://atlas.yagenji.com").rstrip("/")
OUT = Path(os.environ.get("QA_OUT_DIR", "qa-browser-output")) / "regions"


def main() -> int:
    parents = {slug.strip() for slug in os.environ.get("QA_PARENT_SLUGS", "").split(",") if slug.strip()}
    regions = []
    for path in sorted(REGIONS.glob("*/*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not parents or payload["parentSlug"] in parents:
            regions.append(payload)
    if not regions:
        print("No Region pages in requested Browser QA scope.")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    driver = country_qa.make_driver()
    try:
        for region in regions:
            parent, slug = region["parentSlug"], region["slug"]
            relative = f"/countries/{parent}/{slug}/"
            canonical = f"{BASE_URL}{relative}"
            expected_robots = "index,follow" if region.get("regionPublished") else "noindex,follow"
            for label, viewport in country_qa.VIEWPORTS.items():
                try:
                    country_qa.set_viewport(driver, viewport)
                    driver.get(f"{BASE_URL}{relative}")
                    WebDriverWait(driver, 35).until(lambda d: d.execute_script("return document.readyState") == "complete")
                    WebDriverWait(driver, 35).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".region-scene")) == 8)
                    WebDriverWait(driver, 35).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".region-taste")) == 4)
                    country_qa.scroll_entire_page(driver)
                    audit = driver.execute_script("""
                        const main = document.querySelector('main.region-page');
                        return {
                            hasMain: !!main,
                            title: document.querySelector('h1')?.innerText.trim(),
                            scenes: document.querySelectorAll('.region-scene').length,
                            tastes: document.querySelectorAll('.region-taste').length,
                            imageCount: main ? main.querySelectorAll('img').length : 0,
                            broken: main ? [...main.querySelectorAll('img')]
                                .filter(im => !im.complete || im.naturalWidth < 1 || !im.hasAttribute('alt'))
                                .map(im => im.currentSrc || im.src) : [],
                            overflow: document.documentElement.scrollWidth - window.innerWidth,
                            robots: document.querySelector('meta[name="robots"]')?.content,
                            canonical: document.querySelector('link[rel="canonical"]')?.href,
                            duplicateIds: [...document.querySelectorAll('[id]')].map(e => e.id)
                                .filter((id, i, all) => id && all.indexOf(id) !== i),
                            missingLabels: [...document.querySelectorAll('[aria-labelledby]')]
                                .flatMap(e => (e.getAttribute('aria-labelledby') || '').split(/\\s+/))
                                .filter(id => id && !document.getElementById(id)),
                        };
                    """)
                    problems = []
                    if audit["title"] != region["nameEn"]: problems.append("incorrect h1")
                    if audit["scenes"] != 8 or audit["tastes"] != 4: problems.append("incomplete editorial image cards")
                    if audit["imageCount"] != 14 or audit["broken"]: problems.append(f"broken/missing images: {audit['broken']}")
                    if audit["overflow"] > 2: problems.append(f"horizontal overflow: {audit['overflow']}px")
                    if audit["robots"] != expected_robots: problems.append("robots mismatch")
                    if audit["canonical"] != canonical: problems.append("canonical mismatch")
                    if audit["duplicateIds"] or audit["missingLabels"]: problems.append("duplicate IDs or missing accessibility labels")
                    if not audit["hasMain"]: problems.append("Region main missing")
                    safe = f"{parent}-{slug}-{label}"
                    country_qa.full_page_screenshot(driver, OUT / f"{safe}.jpg")
                    if problems:
                        failures.append(f"{safe}: {'; '.join(problems)}")
                        print("FAIL", safe, problems)
                    else:
                        print("PASS", safe, f"14 images, overflow={audit['overflow']}")
                except Exception as exc:
                    failures.append(f"{parent}/{slug} {label}: {exc}")
                    print("FAIL", parent, slug, label, repr(exc))
    finally:
        driver.quit()
    if failures:
        for failure in failures:
            country_qa.annotate("error", "Region browser QA", failure)
        return 1
    print(f"Region Browser QA PASS: {len(regions)} Region(s), 3 viewports each")
    return 0


if __name__ == "__main__":
    sys.exit(main())