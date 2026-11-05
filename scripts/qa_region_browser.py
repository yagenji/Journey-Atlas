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
                            regionLabel: document.querySelector('.hero-copy .region')?.innerText.trim(),
                            themes: [...document.querySelectorAll('.hero-copy .country-theme-chip')].map(e => e.textContent.trim()),
                            parentNav: document.querySelector('.region-return a[href="countries/unitedkingdom/"]')?.textContent.trim(),
                            nextRegionName: document.querySelector('.region-return__link--pending strong, .region-return__link--next strong')?.textContent.trim(),
                            nextRegionUnavailable: !!document.querySelector('.region-return__link--pending:not(a)'),
                            nextRegionBadLink: !!document.querySelector('.region-return__link--pending a'),

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
                    if audit["regionLabel"] != region.get("region"):
                        problems.append("incorrect Northern Europe Hero region")
                    if audit["themes"] != ["地球の風景", "街を歩く", "時をたどる"]:
                        problems.append("Country travel theme chips missing or out of order")
                    if not audit["parentNav"]:
                        problems.append("return to United Kingdom missing")
                    if region.get("nextRegion"):
                        expected_name = region["nextRegion"]["nameJa"]
                        if audit["nextRegionName"] != expected_name:
                            problems.append("next Region label incorrect")
                        if audit["nextRegionBadLink"]:
                            problems.append("unavailable next Region has dead link")
                        next_path = REGIONS / region["parentSlug"] / f'{region["nextRegion"]["slug"]}.json'
                        if not next_path.exists() and not audit["nextRegionUnavailable"]:
                            problems.append("missing next Region must be unavailable")

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
                        const hits = [...document.querySelectorAll('#region-map-hits .region-map-hit')];
                        const cards = [...document.querySelectorAll('.region-scene')];
                        const testId = hits[1]?.dataset.scene;
                        const target = cards.find(c => c.dataset.scene === testId);
                        const mapPositions = hits.map(h => ({x:h.style.left, y:h.style.top}));
                        hits[1]?.click();
                        const mapSelect = !!target && target.getAttribute('aria-pressed') === 'true'
                            && hits[1].getAttribute('aria-pressed') === 'true';
                        cards[2]?.dispatchEvent(new KeyboardEvent('keydown',
                            {key:'Enter', bubbles:true, cancelable:true}));
                        let keyboardSelect = cards[2]?.getAttribute('aria-pressed') === 'true'
                            && hits[2]?.getAttribute('aria-pressed') === 'true';
                        cards[3]?.dispatchEvent(new KeyboardEvent('keydown',
                            {key:' ', bubbles:true, cancelable:true}));
                        keyboardSelect = keyboardSelect && cards[3]?.getAttribute('aria-pressed') === 'true'
                            && hits[3]?.getAttribute('aria-pressed') === 'true';
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
                            related:document.querySelectorAll('.region-related .related-card[href]').length};
                    """, {"slug": slug, "parentSlug": parent})
                    if interactions["hits"] != 8 or any(not p["x"] or not p["y"] for p in interactions["mapPositions"]):
                        problems.append("incomplete map hit targets")
                    for check in ("mapSelect", "keyboardSelect", "sceneHeart", "heroHeart",
                                  "favoriteSave", "favoriteRestore", "wishSave", "wishRestore"):
                        if not interactions[check]:
                            problems.append(f"Region interaction failed: {check}")
                    if interactions["related"] != len(region.get("relatedCountries") or []):
                        problems.append("Region related destination links mismatch")
                    if any(route.get("countryEn") == "SCOTLAND" for route in region.get("nextRoutes", [])):
                        saltire = driver.execute_script("""
                            const card = [...document.querySelectorAll('.next-route-card')].find(
                                c => c.querySelector('.next-route-card__country strong')?.textContent.trim() === 'SCOTLAND');
                            const flag = card?.querySelector('.next-route-card__flag svg.region-saltire');
                            return {present:!!flag, blue:!!flag?.querySelector('rect[fill="#0065bd"]'),
                                white:!!flag?.querySelector('path[stroke="#fff"]'),
                                visible:flag ? flag.getBoundingClientRect().width >= 20 : false};
                        """)
                        if not all(saltire.values()):
                            problems.append(f"Scottish Saltire QA failed: {saltire}")
                    if slug == "northern-ireland":
                        journey_picks = driver.execute_script("""
                            return {
                                routes:[...document.querySelectorAll('.next-route-card__country strong')]
                                    .map(n=>n.textContent.trim()),
                                related:[...document.querySelectorAll('.region-related .related-card h3')]
                                    .map(n=>n.textContent.trim()),
                                relatedCount:document.querySelectorAll('.region-related .related-card').length
                            };
                        """)
                        expected_routes = [item["countryEn"] for item in region["nextRoutes"]]
                        if (journey_picks["routes"] != expected_routes or len(expected_routes) != 3
                                or journey_picks["relatedCount"] != 3
                                or journey_picks["related"] != [item["nameEn"] for item in region["relatedCountries"]]
                                or len(region["relatedCountries"]) != 3):
                            problems.append(f"Northern Ireland journey cards mismatch: {journey_picks}")
                    if slug == "northern-ireland":
                        legend_audit = driver.execute_script("""
                            const legend = document.querySelector('.map-legend--below');
                            const capital = document.querySelector('#country-map-art .region-map-capital');
                            return {labels:legend ? [...legend.querySelectorAll(':scope > span')]
                                .map(el => el.textContent.trim()) : [],
                                capital: !!capital,
                                capitalLabel: capital?.getAttribute('aria-label'),
                                capitalDot: !!capital?.querySelector('i'),
                                coordinates: capital ? [Number.parseFloat(capital.style.left),
                                    Number.parseFloat(capital.style.top)] : []};
                        """)
                        expected_legend = ['1景色の番号', '上部の代表画像（Hero）の場所', '首都']
                        if (legend_audit["labels"] != expected_legend
                                or not legend_audit["capital"]
                                or not legend_audit["capitalDot"]
                                or legend_audit["capitalLabel"] != '首府：ベルファスト'
                                or len(legend_audit["coordinates"]) != 2
                                or not all(0 <= n <= 100 for n in legend_audit["coordinates"])):
                            problems.append(f"Northern Ireland map legend/capital failed: {legend_audit}")
                    if (region.get("map") or {}).get("regions"):
                        detail = (region.get("map") or {}).get("regions") or []
                        inset = driver.execute_script("""
                            const img = document.querySelector('#country-map-art .map-base');
                            const art = document.querySelector('#country-map-art');
                            const hits = [...art.querySelectorAll('.region-map-hit')];
                            const note = document.querySelector('.map-inset-note');
                            const zoomButton = document.querySelector('#region-map-zoom-toggle');
                            const frame = document.querySelector('.map-frame');
                            const data = arguments[0], detail = data[0];
                            const minX = 100*detail.rect.x/1200;
                            const maxX = 100*(detail.rect.x+detail.rect.width)/1200;
                            const minY = 100*detail.rect.y/760;
                            const maxY = 100*(detail.rect.y+detail.rect.height)/760;
                            const insetHits = hits.filter(h => {
                                const x = Number.parseFloat(h.style.left), y = Number.parseFloat(h.style.top);
                                return x >= minX && x <= maxX && y >= minY && y <= maxY;
                            });
                            const expected = new Set(detail.sceneIds);
                            const pts = insetHits.map(h => {
                                const r = h.getBoundingClientRect();
                                return {x:r.x+r.width/2, y:r.y+r.height/2};
                            });
                            let minGap = Infinity;
                            for (let i=0;i<pts.length;i++) for (let k=i+1;k<pts.length;k++)
                                minGap = Math.min(minGap, Math.hypot(pts[i].x-pts[k].x,pts[i].y-pts[k].y));
                            const scale = art.getBoundingClientRect().width / 1200;
                            return {hasNote: !!note && note.textContent.includes('別枠表示'),
                                noZoomButton: !zoomButton && !frame.classList.contains('is-zoomed'),
                                insetCount:insetHits.length,
                                insetIds:insetHits.map(h=>h.dataset.scene),
                                expected:[...expected],
                                gapSvgPx:minGap/scale,
                                mapImageLoaded:img?.naturalWidth > 0};
                        """, detail)
                        mobile_inset = driver.execute_script("""
                            const root=document.querySelector('.region-map-detail-mobile');
                            const img=root?.querySelector('img');
                            const mapRoot=document.querySelector('#region-map-hits');
                            if(!root || !mapRoot) return {found:false};
                            const visible=getComputedStyle(root).display!=='none';
                            const buttons=[...root.querySelectorAll('.region-map-hit')];
                            const mainInset=[...mapRoot.querySelectorAll('[data-map-inset="true"]')];
                            const pts=buttons.map(h=>{
                                const r=h.getBoundingClientRect();
                                return {x:r.x+r.width/2,y:r.y+r.height/2};
                            });
                            let minGap=Infinity;
                            for(let i=0;i<pts.length;i++) for(let j=i+1;j<pts.length;j++)
                                minGap=Math.min(minGap,Math.hypot(pts[i].x-pts[j].x,pts[i].y-pts[j].y));
                            const widths=root.getBoundingClientRect();
                            return {found:true,visible,count:buttons.length,
                                ids:buttons.map(b=>b.dataset.scene),
                                hiddenMain:mainInset.every(b=>getComputedStyle(b).display==='none'),
                                loaded:!!img && img.naturalWidth>0,
                                gap:minGap, width:widths.width};
                        """)
                        small = label == "mobile"
                        if not (mobile_inset.get("found") and mobile_inset.get("count") == len(detail[0]["sceneIds"])
                                and set(mobile_inset.get("ids", [])) == set(detail[0]["sceneIds"])
                                and mobile_inset.get("visible") == small
                                and (not small or (mobile_inset.get("hiddenMain")
                                    and mobile_inset.get("gap", 0) >= 27
                                    and mobile_inset.get("width", 0) >= 250))
                                and mobile_inset.get("loaded")):
                            problems.append(f"Region mobile detail failed: {mobile_inset}")
                        if not (len(detail) == 1
                                and detail[0]["rect"]["x"] == 20 and detail[0]["rect"]["y"] == 20
                                and detail[0]["rect"]["x"] + detail[0]["rect"]["width"] < 440
                                and inset.get("hasNote")
                                and inset.get("noZoomButton")
                                and inset.get("mapImageLoaded")
                                and set(inset.get("insetIds", [])) == set(detail[0]["sceneIds"])
                                and (label == "mobile" or inset.get("gapSvgPx", 0) >= 27)):
                            problems.append(f"Region fixed inset map QA failed: {inset}")
                    expected_images = 14 + bool((region.get("map") or {}).get("regions"))
                    if audit["imageCount"] != expected_images or audit["broken"]:
                        problems.append(f"broken/missing images: {audit['broken']} ({audit['imageCount']}/{expected_images})")
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
                        print("PASS", safe, f"{expected_images} images, overflow={audit['overflow']}")
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