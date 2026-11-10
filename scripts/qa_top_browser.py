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
REGION_EXPECTED = {
    "greenland": ("denmark", "グリーンランド", "north-america"),
    "faroe-islands": ("denmark", "フェロー諸島", "europe"),
    "aruba": ("netherlands", "アルバ", "north-america"),
    "curacao": ("netherlands", "キュラソー", "north-america"),
    "sint-maarten": ("netherlands", "シント・マールテン", "north-america"),
    "puerto-rico": ("unitedstates", "プエルトリコ", "north-america"),
    "new-caledonia": ("france", "ニューカレドニア", "oceania"),
    "french-polynesia": ("france", "フランス領ポリネシア", "oceania"),
}

# Each new Region must carry its own territory flag in TOP cards.
REGION_FLAGS = {
    "greenland": "🇬🇱",
    "faroe-islands": "🇫🇴",
    "aruba": "🇦🇼",
    "curacao": "🇨🇼",
    "sint-maarten": "🇸🇽",
    "puerto-rico": "🇵🇷",
    "new-caledonia": "🇳🇨",
    "french-polynesia": "🇵🇫",
}
# Existing verified SVG assets avoid black-flag fallback on some devices.
UK_REGION_FLAG_ASSETS = {
    "england": "england-waved.svg",
    "scotland": "scotland-waved.svg",
    "wales": "wales-waved.svg",
    "northern-ireland": "unitedkingdom-waved.svg",
}

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

    # Discover-first review: verify the real published image and its link on
    # every viewport. This guard is optional so the existing top remains valid
    # if the review candidate is not adopted.
    if driver.find_elements(By.ID, "ja-discover"):
        wait.until(lambda d: d.execute_script("""
          const img = document.querySelector('#ja-discover-image');
          return !!img && img.complete && img.naturalWidth > 0 &&
                 document.querySelector('#ja-discover').classList.contains('is-ready');
        """))
        snapshot = driver.execute_script("""
          const ids = ['ja-discover','scenery','map','lens-world',
                       'ja-find','countries','themes','seasons','my-atlas'];
          return {
            order: ids.map(id => document.getElementById(id)?.compareDocumentPosition(
                    document.getElementById('my-atlas'))),
            names: ids,
            image: document.querySelector('#ja-discover-image').getAttribute('src'),
            country: document.querySelector('#ja-discover-country').textContent.trim(),
            scene: document.querySelector('#ja-discover-scene').textContent.trim(),
            link: document.querySelector('#ja-discover-link').getAttribute('href'),
            count: document.querySelector('#ja-discover-count').textContent.trim(),
            sequence: ids.map(id => [...document.querySelectorAll('main *')].indexOf(
              document.getElementById(id)))
          };
        """)
        if snapshot["sequence"] != sorted(snapshot["sequence"]):
            errors.append("Discover-first section order is incorrect")
        if not snapshot["scene"] or not snapshot["country"] or not snapshot["image"] or not snapshot["link"].startswith("countries/"):
            errors.append("Discover-first image/name/link is incomplete: " + repr(snapshot))
        wait.until(lambda d: not d.find_element(By.ID, "ja-discover-next").get_property("disabled"))
        driver.execute_script("document.getElementById('ja-discover-next').click()")
        wait.until(lambda d: d.find_element(By.ID, "ja-discover-count").text.strip() != snapshot["count"])
        next_row = driver.execute_script("""
          const image = document.querySelector('#ja-discover-image');
          return {country:document.querySelector('#ja-discover-country').textContent.trim(),
            link:document.querySelector('#ja-discover-link').getAttribute('href'),
            image:image.getAttribute('src'),loaded:image.complete && image.naturalWidth > 0};
        """)
        if (next_row["country"] == snapshot["country"] or
                not next_row["link"].startswith("countries/") or
                next_row["image"] == snapshot["image"] or not next_row["loaded"]):
            errors.append("Discover-first next-scenery navigation is inconsistent: " + repr(next_row))

    cards = driver.find_elements(By.CSS_SELECTOR, "#country-rail .country-card")
    slugs = [card.get_attribute("data-slug") for card in cards]
    if any(slug in ("hong-kong", "macau") for slug in slugs):
        errors.append("Hong Kong and Macau appeared among the 200 parent cards")

    # Detail regions remain searchable; the visual link strip is intentionally absent.
    if driver.find_elements(By.CSS_SELECTOR, "#country-detail-regions, .top-subregions"):
        errors.append("Obsolete regional link strip remains on TOP")

    if driver.find_element(By.ID, "country-count").text.strip() != "200 DESTINATIONS":
        errors.append("TOP parent count is not 200")

    # TOP's shared Region runtime index must include all newly published
    # Regions while keeping the canonical 200 parent count intact.
    runtime_regions = driver.execute_async_script("""
      const done = arguments[0];
      (window.JourneyAtlasRegionsPromise || Promise.resolve([])).then(
        items => done(items.map(({slug,href,parentSlug,regionId,flag,flagAsset}) =>
          ({slug,href,parentSlug,regionId,flag,flagAsset}))), () => done([]));
    """)
    indexed = {row["slug"]: row for row in runtime_regions}
    for slug, (parent, _name, region_id) in REGION_EXPECTED.items():
        expected = "countries/" + parent + "/" + slug + "/"
        row = indexed.get(slug)
        if not row or row["href"] != expected or row["parentSlug"] != parent or row["regionId"] != region_id:
            errors.append("TOP Region index mismatch: " + slug + " " + repr(row))

    for slug, flag in REGION_FLAGS.items():
        if indexed.get(slug, {}).get("flag") != flag:
            errors.append("TOP Region emoji flag missing: " + slug)
        if indexed.get(slug, {}).get("flagAsset"):
            errors.append("TOP Region emoji unexpectedly has SVG asset: " + slug)
    for slug, name in UK_REGION_FLAG_ASSETS.items():
        row = indexed.get(slug, {})
        if not row.get("flag") or not row.get("flagAsset", "").endswith("/" + name):
            errors.append("TOP UK Region flag SVG missing: " + slug + " " + repr(row))

    query = driver.find_element(By.ID, "country-search")
    for label, slug in [("イングランド", "england"), ("スコットランド", "scotland"), ("ウェールズ", "wales"), ("北アイルランド", "northern-ireland"), ("マカオ", "macau")] + [
        (row[1], slug) for slug, row in REGION_EXPECTED.items()
    ]:
        query.clear()
        query.send_keys(label)
        wait.until(lambda d: any(
            el.get_attribute("data-slug") == slug
            for el in d.find_elements(By.CSS_SELECTOR, "#country-grid .country-card")
        ))
        if slug in REGION_FLAGS or slug in UK_REGION_FLAG_ASSETS:
            card = driver.find_element(By.CSS_SELECTOR, f'#country-grid .country-card[data-slug="{slug}"]')
            if slug in REGION_FLAGS:
                flag_text = card.find_element(By.CSS_SELECTOR, ".country-card__flag").get_attribute("textContent")
                if flag_text != REGION_FLAGS[slug]:
                    errors.append("Region card missing territory flag: " + slug + " " + repr(flag_text))
            else:
                image = card.find_element(By.CSS_SELECTOR, ".country-card__flag-image")
                if not image.get_attribute("src").endswith("/" + UK_REGION_FLAG_ASSETS[slug]):
                    errors.append("Region card wrong flag artwork: " + slug)
                if not driver.execute_script("return arguments[0].complete && arguments[0].naturalWidth > 0", image):
                    errors.append("Region card flag SVG failed loading: " + slug)
    query.clear()
    query.send_keys(Keys.ESCAPE)

    # Check child Region links in the parent's map area: older Regions have
    # European parents, while Puerto Rico belongs under the United States.
    def map_child_links(region_id):
        driver.execute_script(
            "document.querySelector('[data-map-tab=\"' + arguments[0] + '\"]').click()",
            region_id,
        )
        wait.until(lambda d: bool(d.find_elements(By.CSS_SELECTOR, "#map .map-country-nav__child")))
        return set(driver.execute_script("""
            return [...document.querySelectorAll('#map .map-country-nav__child')]
                .map(el => el.getAttribute('href').split('countries/').pop());
        """))

    europe_links = map_child_links("europe")
    for slug, (parent, _name, _region_id) in REGION_EXPECTED.items():
        if parent == "unitedstates":
            continue
        if parent + "/" + slug + "/" not in europe_links:
            errors.append("TOP map child Region link missing: " + parent + "/" + slug)
    north_america_links = map_child_links("north-america")
    if "unitedstates/puerto-rico/" not in north_america_links:
        errors.append("TOP map child Region link missing: unitedstates/puerto-rico")

    # Theme browsing must include Region destinations without inflating the
    # canonical 200 parent count.
    driver.execute_script('arguments[0].click()', driver.find_element(By.CSS_SELECTOR, '[data-theme="city"]'))
    wait.until(lambda d: not d.find_element(By.ID, "theme-results").get_attribute("hidden"))
    theme_query = driver.find_element(By.ID, "theme-country-search")
    for label, slug in (("イングランド", "england"), ("マカオ", "macau"), ("キュラソー", "curacao")):
        theme_query.clear()
        theme_query.send_keys(label)
        wait.until(lambda d: any(
            el.get_attribute("data-slug") == slug
            for el in d.find_elements(By.CSS_SELECTOR, "#theme-results-grid .country-card")
        ))
        if slug == "curacao":
            flag_text = driver.find_element(
                By.CSS_SELECTOR, '#theme-results-grid [data-slug="curacao"] .country-card__flag'
            ).get_attribute("textContent")
            if flag_text != "🇨🇼":
                errors.append("Curaçao theme card flag missing: " + repr(flag_text))
    theme_query.clear()
    driver.execute_script("arguments[0].click()", driver.find_element(By.ID, "theme-results-clear"))

    # A saved detail region belongs only to the detail subtotal and must not
    # silently mark its parent Country as wished.
    driver.execute_script(
        "localStorage.setItem('journey-atlas:wish:hong-kong', 'true')"
    )
    driver.refresh()
    wait.until(lambda d: "行きたい 1" in d.find_element(
        By.CSS_SELECTOR, ".ja-detail-summary").get_attribute("textContent"))
    summary_text = driver.find_element(By.CSS_SELECTOR, ".ja-mine-summary").get_attribute("textContent")
    if "0 / 200" not in summary_text:
        errors.append("Detail wishlist affected parent 200-count total")
    driver.execute_script(
        "localStorage.removeItem('journey-atlas:wish:hong-kong')"
    )

    driver.execute_script("""
      localStorage.setItem(
        'journey-atlas:region-wish:unitedkingdom:england',
        JSON.stringify({parentSlug:'unitedkingdom',slug:'england',nameJa:'イングランド',
          href:'countries/unitedkingdom/england/'})
      );
    """)
    driver.refresh()
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".ja-detail-summary"))
    wait.until(lambda d: "行きたい 1" in d.find_element(
        By.CSS_SELECTOR, ".ja-detail-summary").get_attribute("textContent"))
    driver.execute_script("arguments[0].click()", driver.find_element(By.ID, "wish-link"))
    wait.until(lambda d: any(
        el.get_attribute("data-slug") == "england"
        for el in d.find_elements(By.CSS_SELECTOR, "#country-grid .country-card")
    ))
    driver.execute_script(
        "localStorage.removeItem('journey-atlas:region-wish:unitedkingdom:england')"
    )

    # Wish-list chips share the region-filter row in all three discovery sections.
    # Exercise live storage reads, facet intersections and URL restoration.
    driver.execute_script("""
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key.startsWith('journey-atlas:wish:') ||
            key.startsWith('journey-atlas:region-wish:')) localStorage.removeItem(key);
      }
    """)
    driver.execute_script("arguments[0].click()", driver.find_element(
        By.CSS_SELECTOR, '[data-theme="city"]'))
    wait.until(lambda d: len(d.find_elements(
        By.CSS_SELECTOR, "#theme-results-grid .country-card")) > 0)
    theme_slugs = [el.get_attribute("data-slug") for el in driver.find_elements(
        By.CSS_SELECTOR, "#theme-results-grid .country-card")]
    theme_slug = next((slug for slug in theme_slugs if slug not in EXPECTED), theme_slugs[0])
    driver.execute_script(
        "localStorage.setItem('journey-atlas:wish:' + arguments[0], 'true')", theme_slug)
    theme_wish = driver.find_element(
        By.CSS_SELECTOR, '#theme-region-tabs [data-wish-filter="theme"]')
    driver.execute_script("arguments[0].click()", theme_wish)
    wait.until(lambda d: d.find_element(
        By.CSS_SELECTOR, '#theme-region-tabs [data-wish-filter="theme"]'
    ).get_attribute("aria-pressed") == "true")
    filtered = [el.get_attribute("data-slug") for el in driver.find_elements(
        By.CSS_SELECTOR, "#theme-results-grid .country-card")]
    if filtered != [theme_slug]:
        errors.append("Theme Wish filter did not intersect the current theme: " + repr(filtered))
    if "twish=1" not in driver.current_url:
        errors.append("Theme Wish selection not persisted in URL")
    other_theme_region = next((el for el in driver.find_elements(
        By.CSS_SELECTOR, "#theme-region-tabs [data-theme-region]"
    ) if el.get_attribute("data-theme-region") != "all" and
        el.find_element(By.TAG_NAME, "span").text == "0"), None)
    if other_theme_region is not None:
        driver.execute_script("arguments[0].click()", other_theme_region)
        if driver.find_elements(By.CSS_SELECTOR, "#theme-results-grid .country-card"):
            errors.append("Theme region and Wish filters were not intersected")
        driver.execute_script("arguments[0].click()", driver.find_element(
            By.CSS_SELECTOR, '#theme-region-tabs [data-theme-region="all"]'))
    driver.refresh()
    wait.until(lambda d: d.find_elements(
        By.CSS_SELECTOR, '#theme-region-tabs [data-wish-filter="theme"][aria-pressed="true"]'))
    if [el.get_attribute("data-slug") for el in driver.find_elements(
        By.CSS_SELECTOR, "#theme-results-grid .country-card")] != [theme_slug]:
        errors.append("Theme Wish filter was lost on page reload")
    driver.execute_script("arguments[0].click()", driver.find_element(
        By.ID, "theme-results-clear"))
    driver.execute_script(
        "localStorage.removeItem('journey-atlas:wish:' + arguments[0])", theme_slug)

    driver.execute_script("arguments[0].click()", driver.find_element(
        By.CSS_SELECTOR, '#season-months [data-season-month="1"]'))
    wait.until(lambda d: len(d.find_elements(
        By.CSS_SELECTOR, "#season-results-grid .country-card")) > 0)
    # Read dynamic result cards in one DOM snapshot; the season grid rerenders
    # when its index and images settle, invalidating retained Selenium elements.
    season_snapshot = driver.execute_script("""
      const cards = [...document.querySelectorAll('#season-results-grid .country-card')];
      return {
        slugs: cards.map(el => el.dataset.slug),
        arubaFlag: document.querySelector(
          '#season-results-grid [data-slug="aruba"] .country-card__flag'
        )?.textContent || null
      };
    """)
    if "aruba" not in season_snapshot["slugs"]:
        errors.append("Published Aruba Region missing from January season discovery")
    elif season_snapshot["arubaFlag"] != "🇦🇼":
        errors.append("Aruba season flag missing: " + repr(season_snapshot["arubaFlag"]))
    season_slug = season_snapshot["slugs"][0]
    driver.execute_script(
        "localStorage.setItem('journey-atlas:wish:' + arguments[0], 'true')", season_slug)
    driver.execute_script("arguments[0].click()", driver.find_element(
        By.CSS_SELECTOR, '#season-region-tabs [data-wish-filter="season"]'))
    filtered = [el.get_attribute("data-slug") for el in driver.find_elements(
        By.CSS_SELECTOR, "#season-results-grid .country-card")]
    if filtered != [season_slug]:
        errors.append("Season Wish filter did not intersect the selected month: " + repr(filtered))
    if "swish=1" not in driver.current_url:
        errors.append("Season Wish selection not persisted in URL")
    other_season_region = next((el for el in driver.find_elements(
        By.CSS_SELECTOR, "#season-region-tabs [data-season-region]"
    ) if el.get_attribute("data-season-region") != "all" and
        el.find_element(By.TAG_NAME, "span").text == "0"), None)
    if other_season_region is not None:
        driver.execute_script("arguments[0].click()", other_season_region)
        if driver.find_elements(By.CSS_SELECTOR, "#season-results-grid .country-card"):
            errors.append("Season region and Wish filters were not intersected")
        driver.execute_script("arguments[0].click()", driver.find_element(
            By.CSS_SELECTOR, '#season-region-tabs [data-season-region="all"]'))
    driver.refresh()
    wait.until(lambda d: d.find_elements(
        By.CSS_SELECTOR, '#season-region-tabs [data-wish-filter="season"][aria-pressed="true"]'))
    if [el.get_attribute("data-slug") for el in driver.find_elements(
        By.CSS_SELECTOR, "#season-results-grid .country-card")] != [season_slug]:
        errors.append("Season Wish filter was lost on page reload")
    driver.execute_script("arguments[0].click()", driver.find_element(
        By.ID, "season-results-clear"))
    driver.execute_script(
        "localStorage.removeItem('journey-atlas:wish:' + arguments[0])", season_slug)

    driver.execute_script("document.getElementById('scenery').scrollIntoView()")
    wait.until(lambda d: len(d.find_elements(
        By.CSS_SELECTOR, "#gallery-grid .gallery-tile")) > 0)
    driver.execute_script("localStorage.setItem('journey-atlas:wish:japan', 'true')")
    driver.execute_script("arguments[0].click()", driver.find_element(
        By.CSS_SELECTOR, '#gallery-region-tabs [data-wish-filter="scenery"]'))
    wait.until(lambda d: len(d.find_elements(
        By.CSS_SELECTOR, "#gallery-grid .gallery-tile")) > 0)
    # Read the tiles in one script call: the gallery re-renders asynchronously.
    gallery_links = driver.execute_script("return [...document.querySelectorAll('#gallery-grid .gallery-tile')].map((tile) => tile.href)")
    if any("/countries/japan/" not in href for href in gallery_links):
        errors.append("Scenery Wish filter displayed a non-wished destination")
    if "gwish=1" not in driver.current_url:
        errors.append("Scenery Wish selection not persisted in URL")
    driver.execute_script(
        "localStorage.setItem('journey-atlas:scene:japan:hero', 'qa-wish-filter')")
    driver.execute_script(
        "localStorage.setItem('journey-atlas:scene:france:hero', 'qa-wish-filter')")
    driver.execute_script("arguments[0].click()", driver.find_element(
        By.ID, "gallery-saved-toggle"))
    wait.until(lambda d: d.find_elements(
        By.CSS_SELECTOR, '#gallery-saved-toggle[aria-pressed="true"]'))
    gallery_links = driver.execute_script("return [...document.querySelectorAll('#gallery-grid .gallery-tile')].map((tile) => tile.href)")
    if not gallery_links or any("/countries/japan/" not in href for href in gallery_links):
        errors.append("Saved scenery and Wish-list filters were not intersected")
    selected_regions = driver.execute_script("""
      return [...document.querySelectorAll('#gallery-grid .gallery-region')]
        .map(el => ({id: el.dataset.galleryRegion,
          count: el.querySelector('.gallery-region__count')?.textContent.trim()}));
    """)
    if selected_regions != [{"id": "asia", "count": "1 景色"}]:
        errors.append("Saved scenery/Wish regional counts incorrect: " + repr(selected_regions))
    # Clearing the Wish filter keeps saved-only mode, grouping Japan and France
    # under their actual regions and counting both even if pagination is active.
    driver.execute_script("arguments[0].click()", driver.find_element(
        By.ID, "gallery-clear"))
    wait.until(lambda d: len(d.find_elements(
        By.CSS_SELECTOR, "#gallery-grid .gallery-region")) == 2)
    saved_regions = driver.execute_script("""
      return [...document.querySelectorAll('#gallery-grid .gallery-region')]
        .map(el => ({id: el.dataset.galleryRegion,
          count: el.querySelector('.gallery-region__count')?.textContent.trim(),
          tiles: el.querySelectorAll('.gallery-tile').length}));
    """)
    expected_regions = [
        {"id": "asia", "count": "1 景色", "tiles": 1},
        {"id": "europe", "count": "1 景色", "tiles": 1}
    ]
    if saved_regions != expected_regions:
        errors.append("Saved scenery not grouped/counted by region: " + repr(saved_regions))
    saved_count_text = driver.find_element(
        By.ID, "gallery-saved-counts").get_attribute("textContent")
    if not all(label in saved_count_text for label in
               ("保存した景色", "2 景色", "アジア", "ヨーロッパ")):
        errors.append("Saved regional count overview incorrect: " + saved_count_text)
    driver.execute_script("arguments[0].click()", driver.find_element(
        By.ID, "gallery-saved-toggle"))
    if driver.find_elements(By.CSS_SELECTOR, "#gallery-grid .gallery-region") or driver.find_element(
            By.ID, "gallery-saved-counts").get_attribute("hidden") is None:
        errors.append("Normal scenery mode retained saved region grouping")
    driver.execute_script("arguments[0].click()", driver.find_element(
        By.ID, "gallery-close"))
    if "gwish=1" in driver.current_url:
        errors.append("Scenery Wish filter not cleared on closing results")
    for key in ("journey-atlas:wish:japan", "journey-atlas:scene:japan:hero",
                "journey-atlas:scene:france:hero"):
        driver.execute_script("localStorage.removeItem(arguments[0])", key)

    # My-map country selector must render grouped region headings, not one flat list.
    driver.get(BASE + "/?map=mine")
    wait.until(lambda d: d.execute_script("return document.querySelector('#my-atlas').open && location.hash === '#my-atlas'"))
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".map-mine__item")) >= 200)
    region_headings = driver.find_elements(By.CSS_SELECTOR, ".map-mine__region-heading")
    region_names = [heading.text for heading in region_headings]
    if not any("アジア" in name for name in region_names) or not any("ヨーロッパ" in name for name in region_names):
        errors.append("My-map country selector is not grouped by atlas region: " + repr(region_names))
    if not all(heading.find_elements(By.CSS_SELECTOR, ".map-mine__region-count") for heading in region_headings):
        errors.append("My-map region visit counts are missing")
    country_check = driver.find_element(By.CSS_SELECTOR, '.map-mine__countries input[data-visited-slug="japan"]')
    if not country_check.is_selected():
        driver.execute_script("arguments[0].click()", country_check)
        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, '.map-mine__countries input[data-visited-slug="japan"]').is_selected())
        driver.execute_script("arguments[0].click()", driver.find_element(By.CSS_SELECTOR, '.map-mine__countries input[data-visited-slug="japan"]'))
    driver.execute_script("localStorage.removeItem('journey-atlas:visited:japan')")

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
