#!/usr/bin/env python3
"""Focused, browser-rendered QA for the homepage's public discovery interactions."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

from qa_published_browser import VIEWPORTS, make_driver, set_viewport

BASE = os.environ.get("QA_BASE_URL", "https://atlas.yagenji.com").rstrip("/")
OUT = Path(os.environ.get("QA_OUT_DIR", "qa-browser-output")) / "top"
EXPECTED = {
    "england": "countries/unitedkingdom/england/",
    "scotland": "countries/unitedkingdom/scotland/",
    "wales": "countries/unitedkingdom/wales/",
    "northern-ireland": "countries/unitedkingdom/northern-ireland/",
    "hong-kong": "countries/hong-kong/",
    "macau": "countries/macau/",
}


def check(driver, viewport):
    errors = []
    set_viewport(driver, viewport)
    driver.get(BASE + "/?qa=top-200")
    wait = WebDriverWait(driver, 40)
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#country-rail .country-card")) == 200)
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#country-detail-regions a")) == 6)

    cards = driver.find_elements(By.CSS_SELECTOR, "#country-rail .country-card")
    slugs = [card.get_attribute("data-slug") for card in cards]
    if any(slug in ("hong-kong", "macau") for slug in slugs):
        errors.append("Hong Kong and Macau appeared among the 200 parent cards")

    links = driver.find_elements(By.CSS_SELECTOR, "#country-detail-regions a")
    for slug, href in EXPECTED.items():
        if not any(link.get_attribute("href").endswith("/" + href) for link in links):
            errors.append("Missing detail link: " + slug)

    if driver.find_element(By.ID, "country-count").text.strip() != "200 DESTINATIONS":
        errors.append("TOP parent count is not 200")

    query = driver.find_element(By.ID, "country-search")
    for label, slug in (("イングランド", "england"), ("マカオ", "macau")):
        query.clear()
        query.send_keys(label)
        wait.until(lambda d: any(
            el.get_attribute("data-slug") == slug
            for el in d.find_elements(By.CSS_SELECTOR, "#country-grid .country-card")
        ))
    query.clear()
    query.send_keys(Keys.ESCAPE)

    # One horizontal-page-scroll test per viewport, allowing minor pixel rounding.
    sizes = driver.execute_script(
        "return [document.documentElement.scrollWidth, document.documentElement.clientWidth]"
    )
    if sizes[0] > sizes[1] + 3:
        offenders = driver.execute_script("""
          return Array.from(document.querySelectorAll('body *')).filter(e => {
            const rect = e.getBoundingClientRect();
            const style = getComputedStyle(e);
            return style.display !== 'none' && rect.width && rect.right > innerWidth + 3;
          }).slice(0, 25).map(e => ({
            tag:e.tagName.toLowerCase(), cls:String(e.className).slice(0,100),
            id:e.id, right:Math.round(e.getBoundingClientRect().right),
            width:Math.round(e.getBoundingClientRect().width)
          }));
        """)
        errors.append("Horizontal overflow: " + str(sizes) + " offenders=" + repr(offenders))

    console = driver.get_log("browser")
    severe = [entry["message"] for entry in console
              if entry.get("level") == "SEVERE"
              and "favicon" not in entry.get("message", "").lower()]
    if severe:
        errors.append("Console errors: " + repr(severe[:4]))

    return errors


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    driver = make_driver()
    results = {}
    try:
        for label, config in VIEWPORTS.items():
            try:
                errors = check(driver, config)
            except Exception as exc:
                errors = [type(exc).__name__ + ": " + str(exc)[:350]]
            results[label] = {"pass": not errors, "errors": errors}
            driver.save_screenshot(str(OUT / (label + ".png")))
            print(("PASS" if not errors else "FAIL") + " TOP " + label + ": " + repr(errors), flush=True)
    finally:
        driver.quit()
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(item["pass"] for item in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
