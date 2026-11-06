#!/usr/bin/env python3
"""Country browser QA entry point with optional-section awareness.

The renderer intentionally hides Taste when a Country has no authentic Taste
items. Browser QA must validate that contract instead of forcing four cards.
All other checks remain delegated to qa_published_browser.py.
"""
from __future__ import annotations

import json
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import qa_published_browser as qa

_BASE_EXPECTED_COUNTS = dict(qa.EXPECTED_COUNTS)
_BASE_CRITICAL_VISIBLE = list(qa.CRITICAL_VISIBLE)
_ORIGINAL_COLLECT_DOM_AUDIT = qa.collect_dom_audit
_ORIGINAL_ASSERT_AUDIT = qa.assert_audit


def expected_taste_count(driver) -> int:
    path = urlparse(driver.current_url).path
    try:
        slug = path.split("/countries/", 1)[1].split("/", 1)[0]
    except IndexError:
        return 4
    country_path = qa.COUNTRY_DIR / f"{slug}.json"
    if not country_path.exists():
        return 4
    data = json.loads(country_path.read_text(encoding="utf-8"))
    taste = data.get("taste") if isinstance(data.get("taste"), dict) else {}
    items = taste.get("items") if isinstance(taste.get("items"), list) else []
    return len(items)


def wait_for_country(driver) -> None:
    wait = WebDriverWait(driver, 35)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".scene-card")) == 8)
    taste_count = expected_taste_count(driver)
    if taste_count:
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".taste-card")) == taste_count)
    else:
        wait.until(
            lambda d: bool(d.execute_script(
                "const s=document.querySelector('#taste-section'); return !!s && s.hidden === true;"
            ))
        )
    wait.until(lambda d: len((d.find_element(By.CSS_SELECTOR, ".hero h1").text or "").strip()) > 0)


def collect_dom_audit(driver, viewport: dict) -> dict:
    taste_count = expected_taste_count(driver)
    qa.EXPECTED_COUNTS.clear()
    qa.EXPECTED_COUNTS.update(_BASE_EXPECTED_COUNTS)
    qa.EXPECTED_COUNTS[".taste-card"] = taste_count
    qa.CRITICAL_VISIBLE[:] = _BASE_CRITICAL_VISIBLE
    if taste_count == 0:
        qa.CRITICAL_VISIBLE[:] = [selector for selector in qa.CRITICAL_VISIBLE if selector != "#taste-section"]

    audit = _ORIGINAL_COLLECT_DOM_AUDIT(driver, viewport)
    audit["atlasFolio"] = driver.execute_script(
        "return document.querySelector('.atlas-pager__folio')?.textContent?.trim() || null"
    )
    path = urlparse(driver.current_url).path
    audit["atlasFolioSlug"] = path.split("/countries/", 1)[-1].split("/", 1)[0]
    # Check the visit toggle itself, including the exact key My Atlas/map reads.
    audit["visitToggle"] = driver.execute_script("""
        const slug = arguments[0];
        const button = document.querySelector('[data-ja-visited]');
        if (!button) return {mounted:false};
        const key = 'journey-atlas:visited:' + slug;
        const previous = localStorage.getItem(key);
        const before = button.getAttribute('aria-pressed');
        button.click();
        const after = button.getAttribute('aria-pressed');
        const stored = localStorage.getItem(key);
        button.click();
        const restored = button.getAttribute('aria-pressed');
        return {mounted:true,slug:button.dataset.jaVisited,
            before,after,restored,
            storedCorrect:before === 'true' ? stored === null : stored === 'true',
            persisted:localStorage.getItem(key) === previous};
    """, audit["atlasFolioSlug"])

    # China detail destinations must use the same Region layout language as
    # the United Kingdom's four sub-Country pages on every viewport.
    if audit["atlasFolioSlug"] in {"hong-kong", "macau"}:
        audit["chinaRegionLayout"] = driver.execute_script("""
            const region = document.querySelector('.region-country-page');
            const nav = document.querySelector('nav.region-return');
            const sibling = location.pathname.includes('/hong-kong/') ? 'macau' : 'hong-kong';
            return {
                regionClass: !!region && document.querySelector('#app')?.classList.contains('region-page'),
                regionCSS: [...document.styleSheets].some(sheet => sheet.href?.includes('/region.css')),
                profile: document.querySelector('.country-facts-strip__head .section-kicker-en')?.textContent.trim(),
                signature: document.querySelector('#signature-facts-title')?.textContent.trim(),
                scenery: document.querySelector('.scenes-heading h2')?.textContent.trim(),
                routes: document.querySelector('#next-routes-title')?.textContent.trim(),
                wish: document.querySelector('#wish-button strong')?.textContent.trim(),
                parent: !!nav?.querySelector('a[href="countries/china/"]'),
                sibling: !!nav?.querySelector('a[href="countries/' + sibling + '/"]'),
                navGrid: nav ? getComputedStyle(nav).gridTemplateColumns : '',
                overflow: document.documentElement.scrollWidth - window.innerWidth
            };
        """)
    if taste_count == 0:
        audit["hiddenRequired"] = [
            selector for selector in audit.get("hiddenRequired", [])
            if selector != "#taste-section"
        ]
    return audit


def assert_audit(audit: dict, bg_checks: list[dict], browser_errors: list[dict]) -> list[str]:
    errors = _ORIGINAL_ASSERT_AUDIT(audit, bg_checks, browser_errors)
    folio = audit.get("atlasFolio")
    slug = audit.get("atlasFolioSlug")
    visit = audit.get("visitToggle") or {}
    if (not visit.get("mounted") or visit.get("slug") != slug
            or visit.get("after") == visit.get("before")
            or visit.get("restored") != visit.get("before")
            or not visit.get("storedCorrect") or not visit.get("persisted")):
        errors.append(f"Country visit toggle/storage mismatch: {slug} {visit}")
    if slug in {"hong-kong", "macau"}:
        if folio is not None:
            errors.append(f"China detail region {slug} must not be numbered as a Country Page: {folio}")
        layout = audit.get("chinaRegionLayout") or {}
        expected = {
            "regionClass": True,
            "regionCSS": True,
            "profile": "REGION PROFILE",
            "signature": "この地域を知る数字",
            "scenery": "この地域で見たい景色 8選",
            "routes": "隣の地域へ旅をつなぐ",
            "parent": True,
            "sibling": True,
        }
        for key, value in expected.items():
            if layout.get(key) != value:
                errors.append(f"{slug} Region layout {key}: expected {value!r}, got {layout.get(key)!r}")
        if layout.get("wish") not in {"この地域に行きたい", "行きたい地域に保存しました"}:
            errors.append(f"{slug} Region wish-button label differs: {layout.get('wish')!r}")
        if layout.get("overflow", 0) > 2:
            errors.append(f"{slug} Region layout horizontal overflow: {layout['overflow']}px")
    elif not isinstance(folio, str) or not folio.endswith(" / 200"):
        errors.append(f"Country Page folio must use canonical 200 denominator: {slug} {folio!r}")
    return errors


qa.wait_for_country = wait_for_country
qa.collect_dom_audit = collect_dom_audit
qa.assert_audit = assert_audit


if __name__ == "__main__":
    raise SystemExit(qa.main())
