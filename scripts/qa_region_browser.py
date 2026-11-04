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
                            sectionCounts: {
                                profile: document.querySelectorAll('.country-facts-strip .fact-list > div').length,
                                signature: document.querySelectorAll('.signature-facts__grid article').length,
                                encounters: document.querySelectorAll('.encounter-list article').length,
                                culture: document.querySelectorAll('.atlas-extras__grid article').length,
                                trivia: document.querySelectorAll('.travel-trivia__grid article').length,
                                duration: document.querySelectorAll('.travel-scale__item').length,
                                seasons: document.querySelectorAll('.season-list article').length,
                                transport: document.querySelectorAll('.travel-planning__block--transport').length,
                                personas: document.querySelectorAll('.persona-list article').length,
                                notes: document.querySelectorAll('.tip-list article').length,
                                nextRoutes: document.querySelectorAll('.next-route-card').length,
                            },
                            sharedCountryLayout: !!document.querySelector('.region-country-page .hero')
                                && !!document.querySelector('.region-country-page .atlas-panel .map-column')
                                && !!document.querySelector('.region-country-page .atlas-panel .scenes-column'),
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
                    if not audit["sharedCountryLayout"]:
                        problems.append("shared Country layout missing")
                    expected_sections = {
                        "profile": len(region.get("profile") or []),
                        "signature": len(region.get("signatureFacts") or []),
                        "encounters": len(region.get("encounters") or []),
                        "culture": len(region.get("culture") or []),
                        "trivia": len(region.get("travelTrivia") or []),
                        "duration": len((region.get("travelScale") or {}).get("items") or []),
                        "seasons": len(region.get("seasons") or []),
                        "transport": 1 if region.get("transport") else 0,
                        "personas": len(region.get("forWhom") or []),
                        "notes": len(region.get("notes") or []),
                        "nextRoutes": len(region.get("nextRoutes") or []),
                    }
                    for section, expected_count in expected_sections.items():
                        actual_count = audit["sectionCounts"][section]
                        if actual_count != expected_count:
                            problems.append(f"{section} count mismatch: {actual_count}/{expected_count}")

                    # Interactions are part of Country parity: a screenshot PASS
                    # alone cannot prove map/card selection or personal saves.
                    interactions = driver.execute_script("""
                        const hits = [...document.querySelectorAll('.region-map-hit')];
                        const cards = [...document.querySelectorAll('.region-scene')];
                        const testId = hits[1]?.dataset.scene;
                        const target = cards.find(c => c.dataset.scene === testId);
                        const mapPositions = hits.map(h => ({x:h.style.left, y:h.style.top}));
                        hits[1]?.click();
                        const mapSelect = !!target && target.getAttribute('aria-pressed') === 'true'
                            && hits[1].getAttribute('aria-pressed') === 'true';
                        cards[2]?.dispatchEvent(new KeyboardEvent('keydown',
                            {key:'Enter', bubbles:true, cancelable:true}));
                        const keyboardSelect = cards[2]?.getAttribute('aria-pressed') === 'true'
                            && hits[2]?.getAttribute('aria-pressed') === 'true';
                        const sceneHeart = target?.querySelector('[data-ja-scene-save]');
                        const heroHeart = document.querySelector('[data-ja-hero-save]');
                        const sceneKey = 'journey-atlas:scene:' + arguments[0].slug + ':' + testId;
                        let oldSave = null, favoriteSave = false, favoriteRestore = false;
                        if (sceneHeart) {
                            oldSave = localStorage.getItem(sceneKey);
                            if (oldSave !== null) { sceneHeart.click(); }
                            sceneHeart.click();
                            const stored = JSON.parse(localStorage.getItem(sceneKey) || 'null');
                            favoriteSave = stored?.kind === 'region'
                                && stored?.parentSlug === arguments[0].parentSlug
                                && stored?.href === 'countries/' + arguments[0].parentSlug
                                    + '/' + arguments[0].slug + '/#scene-' + testId;
                            sceneHeart.click();
                            favoriteRestore = localStorage.getItem(sceneKey) === null;
                            if (oldSave !== null) localStorage.setItem(sceneKey,oldSave);
                        }
                        const wish = document.querySelector('#region-wish-button');
                        const wishKey = 'journey-atlas:region-wish:' + arguments[0].parentSlug
                            + ':' + arguments[0].slug;
                        let wishSave = false, wishRestore = false, oldWish = null;
                        if (wish) {
                            oldWish = localStorage.getItem(wishKey);
                            if (oldWish !== null) wish.click();
                            wish.click();
                            const value = JSON.parse(localStorage.getItem(wishKey) || 'null');
                            wishSave = value?.slug === arguments[0].slug
                                && value?.href === 'countries/' + arguments[0].parentSlug
                                    + '/' + arguments[0].slug + '/';
                            wish.click();
                            wishRestore = localStorage.getItem(wishKey) === null;
                            if (oldWish !== null) localStorage.setItem(wishKey, oldWish);
                        }
                        return {hits:hits.length, mapPositions, mapSelect, keyboardSelect,
                            sceneHeart:!!sceneHeart,heroHeart:!!heroHeart,
                            favoriteSave,favoriteRestore,wishSave,wishRestore,
                            related:document.querySelectorAll('.region-related-card[href]').length};
                    """, {"slug": slug, "parentSlug": parent})
                    if interactions["hits"] != 8 or any(not p["x"] or not p["y"] for p in interactions["mapPositions"]):
                        problems.append("incomplete map hit targets")
                    for check in ("mapSelect", "keyboardSelect", "sceneHeart", "heroHeart",
                                  "favoriteSave", "favoriteRestore", "wishSave", "wishRestore"):
                        if not interactions[check]:
                            problems.append(f"Region interaction failed: {check}")
                    if interactions["related"] != len(region.get("relatedCountries") or []):
                        problems.append("Region related destination links mismatch")
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