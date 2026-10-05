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
    if taste_count == 0:
        audit["hiddenRequired"] = [
            selector for selector in audit.get("hiddenRequired", [])
            if selector != "#taste-section"
        ]
    return audit


qa.wait_for_country = wait_for_country
qa.collect_dom_audit = collect_dom_audit


if __name__ == "__main__":
    raise SystemExit(qa.main())
