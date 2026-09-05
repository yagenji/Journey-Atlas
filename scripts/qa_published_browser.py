#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import math
import os
import shutil
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "data" / "country-renewal-status.json"
COUNTRY_DIR = ROOT / "data" / "countries"
BASE_URL = os.environ.get("QA_BASE_URL", "https://atlas.yagenji.com").rstrip("/")
OUT = Path(os.environ.get("QA_OUT_DIR", "qa-browser-output"))
OUT.mkdir(parents=True, exist_ok=True)

def load_countries() -> list[tuple[str, str]]:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    requested = {x.strip() for x in os.environ.get("QA_SLUGS", "").split(",") if x.strip()}
    countries: list[tuple[str, str]] = []
    for row in status.get("countries", []):
        slug = row.get("slug")
        if not slug or not row.get("published"):
            continue
        if requested and slug not in requested:
            continue
        data = json.loads((COUNTRY_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        countries.append((slug, data.get("nameJa") or slug))
    # Temporary review-only QA: include Serbia without changing publication state.
    review_slug = "serbia"
    if review_slug not in {slug for slug, _ in countries}:
        review_path = COUNTRY_DIR / f"{review_slug}.json"
        if review_path.exists():
            review_data = json.loads(review_path.read_text(encoding="utf-8"))
            countries.append((review_slug, review_data.get("nameJa") or review_slug))

    if requested:
        found = {slug for slug, _ in countries}
        missing = sorted(requested - found)
        if missing:
            raise SystemExit(f"QA_SLUGS contains non-published or unknown countries: {', '.join(missing)}")
    return countries

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 1000, "mobile": False},
    "tablet": {"width": 834, "height": 1112, "mobile": False},
    "mobile": {"width": 390, "height": 844, "mobile": True},
}

EXPECTED_COUNTS = {
    "#facts > div": 6,
    "#signature-facts > article": 3,
    ".scene-card": 8,
    "#encounters > article": 8,
    "#atlas-extras-grid > article": 6,
    "#travel-trivia-grid > article": 5,
    ".taste-card": 4,
    ".travel-scale__item": 3,
    "#seasons > article": 4,
    "#personas > article": 3,
    "#tips > article": 3,
}

CRITICAL_VISIBLE = [
    ".hero",
    ".country-facts-strip",
    "#signature-facts-section",
    "#country-map-art",
    ".scenes-column",
    "#atlas-extras-section",
    "#taste-section",
    "#travel-trivia-section",
    ".travel-planning",
    "#travel-scale-section",
    "#transport",
    "#personas",
    "#tips",
    "#related",
]

def make_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--lang=ja-JP")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver_path = shutil.which("chromedriver")
    service = Service(driver_path) if driver_path else Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(45)
    driver.set_script_timeout(30)
    return driver

def set_viewport(driver: webdriver.Chrome, cfg: dict) -> None:
    driver.set_window_size(cfg["width"], cfg["height"])
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": cfg["width"],
            "height": cfg["height"],
            "deviceScaleFactor": 1,
            "mobile": bool(cfg["mobile"]),
            "screenWidth": cfg["width"],
            "screenHeight": cfg["height"],
        },
    )
    driver.execute_cdp_cmd(
        "Emulation.setTouchEmulationEnabled",
        {"enabled": bool(cfg["mobile"]), "maxTouchPoints": 5 if cfg["mobile"] else 1},
    )

def wait_for_country(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 35)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".scene-card")) == 8)
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".taste-card")) == 4)
    wait.until(lambda d: len((d.find_element(By.CSS_SELECTOR, ".hero h1").text or "").strip()) > 0)
    time.sleep(0.5)

def scroll_entire_page(driver: webdriver.Chrome) -> None:
    # Trigger all lazy map/image/background loading exactly as a user scrolling the page would.
    height = int(driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"))
    viewport = max(300, int(driver.execute_script("return window.innerHeight")))
    step = max(250, int(viewport * 0.72))
    y = 0
    while y < height:
        driver.execute_script("window.scrollTo(0, arguments[0])", y)
        time.sleep(0.12)
        height = max(height, int(driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")))
        y += step
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(0.8)
    driver.execute_script("window.scrollTo(0, 0)")
    time.sleep(0.4)

def full_page_screenshot(driver: webdriver.Chrome, path: Path) -> None:
    metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
    content = metrics.get("cssContentSize") or metrics.get("contentSize")
    width = max(1, math.ceil(content["width"]))
    height = max(1, math.ceil(content["height"]))
    try:
        result = driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {
                "format": "jpeg",
                "quality": 72,
                "fromSurface": True,
                "captureBeyondViewport": True,
                "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1},
            },
        )
        path.write_bytes(base64.b64decode(result["data"]))
    except WebDriverException:
        path.with_name(path.stem + "-viewport.jpg").write_bytes(driver.get_screenshot_as_png())

def background_image_check(driver: webdriver.Chrome) -> list[dict]:
    script = r"""
const done = arguments[arguments.length - 1];
const urls = new Set();
for (const el of document.querySelectorAll('.media-slot, .hero-art, .scene-image')) {
  const bg = getComputedStyle(el).backgroundImage || '';
  for (const m of bg.matchAll(/url\(["']?(.*?)["']?\)/g)) {
    if (m[1]) urls.add(m[1]);
  }
}
const values = [...urls];
if (!values.length) { done([]); return; }
Promise.all(values.map(src => new Promise(resolve => {
  const im = new Image();
  im.onload = () => resolve({src, ok:true, width:im.naturalWidth, height:im.naturalHeight});
  im.onerror = () => resolve({src, ok:false, width:0, height:0});
  im.src = src;
}))).then(done);
"""
    return driver.execute_async_script(script)

def collect_dom_audit(driver: webdriver.Chrome, viewport: dict) -> dict:
    return driver.execute_script(
        r"""
const expected = arguments[0];
const critical = arguments[1];
const viewport = arguments[2];
const visible = el => {
  if (!el) return false;
  const s = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return s.display !== 'none' && s.visibility !== 'hidden' && !el.hidden && r.width > 0 && r.height > 0;
};
const textName = el => (el.getAttribute('aria-label') || el.getAttribute('title') || el.innerText || el.textContent || '').trim();

const counts = {};
for (const [sel, n] of Object.entries(expected)) counts[sel] = document.querySelectorAll(sel).length;

const criticalVisible = {};
for (const sel of critical) criticalVisible[sel] = visible(document.querySelector(sel));

const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
const duplicateIds = [...new Set(ids.filter((id, i) => id && ids.indexOf(id) !== i))];

const badAriaLabels = [];
for (const el of document.querySelectorAll('[aria-labelledby]')) {
  const refs = (el.getAttribute('aria-labelledby') || '').trim().split(/\s+/).filter(Boolean);
  const missing = refs.filter(id => !document.getElementById(id));
  if (missing.length) badAriaLabels.push({tag: el.tagName, refs, missing});
}

const imgFailures = [...document.images]
  .filter(img => visible(img) && (!img.complete || img.naturalWidth < 1 || img.naturalHeight < 1))
  .map(img => ({src: img.currentSrc || img.src, alt: img.alt, cls:String(img.className || '')}));

const missingBackgroundMedia = [...document.querySelectorAll('.hero-art, .scene-image')]
  .filter(el => !el.classList.contains('has-image'))
  .map(el => ({cls:String(el.className || ''), scene:el.closest('.scene-card')?.dataset?.scene || null}));

const mapBase = document.querySelector('#country-map-art .map-base');
const mapImageLoaded = !!(mapBase && mapBase.complete && mapBase.naturalWidth > 0 && mapBase.naturalHeight > 0);

const badImgAlt = [...document.images]
  .filter(img => !img.hasAttribute('alt'))
  .map(img => img.currentSrc || img.src);

const badRoleImg = [...document.querySelectorAll('[role="img"]')]
  .filter(el => !((el.getAttribute('aria-label') || '').trim()))
  .map(el => ({tag: el.tagName, cls: el.className}));

const interactives = [...document.querySelectorAll('a[href],button,[role="button"],input,select,textarea,[tabindex]')]
  .filter(visible);
const unnamedInteractive = interactives
  .filter(el => !textName(el))
  .map(el => ({tag:el.tagName, role:el.getAttribute('role'), cls:el.className, href:el.getAttribute('href')}));
const positiveTabindex = interactives
  .filter(el => Number(el.getAttribute('tabindex')) > 0)
  .map(el => ({tag:el.tagName, cls:el.className, tabindex:el.getAttribute('tabindex')}));

const unfocusable = interactives
  .filter(el => {
    if (el.disabled) return false;
    const prev = document.activeElement;
    el.focus({preventScroll:true});
    const ok = document.activeElement === el;
    if (prev && prev.focus) prev.focus({preventScroll:true});
    return !ok;
  })
  .slice(0,30)
  .map(el => ({tag:el.tagName, role:el.getAttribute('role'), cls:el.className}));

const headings = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(visible).map(el => ({
  level:Number(el.tagName.slice(1)),
  text:(el.innerText || '').trim().replace(/\s+/g,' ').slice(0,120)
}));
const headingJumps = [];
for (let i=1;i<headings.length;i++) {
  if (headings[i].level > headings[i-1].level + 1) headingJumps.push({from:headings[i-1],to:headings[i]});
}

const overflow = {
  scrollWidth: document.documentElement.scrollWidth,
  innerWidth: window.innerWidth,
  delta: document.documentElement.scrollWidth - window.innerWidth,
};
const overflowOffenders = [...document.querySelectorAll('main *, header *, footer *')]
  .filter(visible)
  .map(el => {
    const r = el.getBoundingClientRect();
    return {el, r};
  })
  .filter(x => x.r.left < -2 || x.r.right > window.innerWidth + 2)
  .slice(0,40)
  .map(x => ({tag:x.el.tagName, cls:String(x.el.className || ''), left:Math.round(x.r.left), right:Math.round(x.r.right), width:Math.round(x.r.width), text:(x.el.innerText||'').trim().replace(/\s+/g,' ').slice(0,80)}));

const clippedText = [...document.querySelectorAll('h1,h2,h3,h4,p,small,b,strong,dt,dd')]
  .filter(visible)
  .filter(el => {
    const s = getComputedStyle(el);
    if (s.overflow === 'visible') return false;
    return el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2;
  })
  .slice(0,40)
  .map(el => ({tag:el.tagName, cls:String(el.className || ''), text:(el.innerText||'').trim().replace(/\s+/g,' ').slice(0,100), sw:el.scrollWidth,cw:el.clientWidth,sh:el.scrollHeight,ch:el.clientHeight}));

const hero = document.querySelector('.hero');
const heroTitle = document.querySelector('.hero h1');
const header = document.querySelector('header');
const heroRect = hero ? hero.getBoundingClientRect() : null;
const titleRect = heroTitle ? heroTitle.getBoundingClientRect() : null;
const headerRect = header ? header.getBoundingClientRect() : null;

const map = document.querySelector('#country-map-art');
const mapRect = map ? map.getBoundingClientRect() : null;
const mapSvg = map ? map.querySelector('svg') : null;

const hiddenRequired = ['#signature-facts-section','#atlas-extras-section','#taste-section','#travel-trivia-section','#travel-scale-section']
  .filter(sel => {
    const el=document.querySelector(sel);
    return !el || el.hidden || !visible(el);
  });

const sceneRoles = [...document.querySelectorAll('.scene-card')].map(el => ({
  role:el.getAttribute('role'), tabindex:el.getAttribute('tabindex'), ariaLabel:el.getAttribute('aria-label'), ariaPressed:el.getAttribute('aria-pressed')
}));

return {
  href: location.href,
  title: document.title,
  viewport: {innerWidth:window.innerWidth, innerHeight:window.innerHeight, requested:viewport},
  h1: (heroTitle?.innerText || '').trim(),
  countryJa: (document.querySelector('.country-ja')?.innerText || '').trim(),
  counts,
  criticalVisible,
  duplicateIds,
  badAriaLabels,
  imgFailures,
  missingBackgroundMedia,
  badImgAlt,
  badRoleImg,
  unnamedInteractive,
  positiveTabindex,
  unfocusable,
  headings,
  headingJumps,
  overflow,
  overflowOffenders,
  clippedText,
  hiddenRequired,
  sceneRoles,
  map: {
    hasSvg: !!mapSvg,
    hasMapImage: !!mapBase,
    imageLoaded: mapImageLoaded,
    hasMapClass: !!map?.classList.contains('has-map'),
    width: mapRect ? Math.round(mapRect.width) : 0,
    height: mapRect ? Math.round(mapRect.height) : 0,
  },
  hero: {
    width: heroRect ? Math.round(heroRect.width) : 0,
    height: heroRect ? Math.round(heroRect.height) : 0,
    titleTop: titleRect ? Math.round(titleRect.top) : null,
    titleBottom: titleRect ? Math.round(titleRect.bottom) : null,
    headerBottom: headerRect ? Math.round(headerRect.bottom) : null,
    titleHeaderOverlap: !!(titleRect && headerRect && titleRect.top < headerRect.bottom && titleRect.bottom > headerRect.top),
  },
};
""",
        EXPECTED_COUNTS,
        CRITICAL_VISIBLE,
        viewport,
    )

def assert_audit(audit: dict, bg_checks: list[dict], browser_errors: list[dict]) -> list[str]:
    errors: list[str] = []
    for sel, expected in EXPECTED_COUNTS.items():
        actual = audit["counts"].get(sel)
        if actual != expected:
            errors.append(f"{sel}: expected {expected}, got {actual}")
    for sel, ok in audit["criticalVisible"].items():
        if not ok:
            errors.append(f"critical section not visible: {sel}")
    if audit["duplicateIds"]:
        errors.append(f"duplicate ids: {audit['duplicateIds']}")
    if audit["badAriaLabels"]:
        errors.append(f"broken aria-labelledby refs: {audit['badAriaLabels']}")
    if audit["imgFailures"]:
        errors.append(f"image load failures after full scroll: {audit['imgFailures']}")
    if audit["missingBackgroundMedia"]:
        errors.append(f"hero/scene lazy backgrounds missing after full scroll: {audit['missingBackgroundMedia']}")
    if audit["badImgAlt"]:
        errors.append(f"img missing alt attribute: {audit['badImgAlt'][:5]}")
    if audit["badRoleImg"]:
        errors.append(f"role=img missing aria-label: {audit['badRoleImg'][:5]}")
    if audit["unnamedInteractive"]:
        errors.append(f"interactive elements without accessible name: {audit['unnamedInteractive'][:5]}")
    if audit["positiveTabindex"]:
        errors.append(f"positive tabindex found: {audit['positiveTabindex'][:5]}")
    if audit["unfocusable"]:
        errors.append(f"visible interactive elements not focusable: {audit['unfocusable'][:5]}")
    if audit["headingJumps"]:
        errors.append(f"heading hierarchy jump: {audit['headingJumps'][:3]}")
    if audit["overflow"]["delta"] > 2:
        errors.append(f"horizontal overflow {audit['overflow']['delta']}px; offenders={audit['overflowOffenders'][:8]}")
    if audit["clippedText"]:
        errors.append(f"clipped text candidates: {audit['clippedText'][:8]}")
    if audit["hiddenRequired"]:
        errors.append(f"required sections hidden: {audit['hiddenRequired']}")
    if (not audit["map"]["hasMapImage"] or not audit["map"]["imageLoaded"] or not audit["map"]["hasMapClass"]
            or audit["map"]["width"] < 200 or audit["map"]["height"] < 120):
        errors.append(f"map render invalid: {audit['map']}")
    if any(x.get("role") != "button" or x.get("tabindex") != "0" or not x.get("ariaLabel") for x in audit["sceneRoles"]):
        errors.append("scene cards do not expose consistent button/tabindex/accessibility semantics")
    bad_bg = [x for x in bg_checks if not x.get("ok")]
    if bad_bg:
        errors.append(f"background image load failures: {bad_bg[:8]}")
    severe = []
    for entry in browser_errors:
        level = str(entry.get("level", "")).upper()
        message = entry.get("message", "")
        if level == "SEVERE" and "favicon" not in message.lower():
            severe.append(message)
    if severe:
        errors.append(f"browser console severe errors: {severe[:6]}")
    return errors

def main() -> int:
    countries = load_countries()
    results = []
    failures = []
    driver = make_driver()
    try:
        for slug, name_ja in countries:
            for vp_name, vp in VIEWPORTS.items():
                set_viewport(driver, vp)
                url = f"{BASE_URL}/countries/{slug}/?qa=responsive-{int(time.time())}"
                print(f"QA {slug} {vp_name}: {url}", flush=True)
                try:
                    driver.get(url)
                    wait_for_country(driver)
                    scroll_entire_page(driver)
                    audit = collect_dom_audit(driver, vp)
                    bg_checks = background_image_check(driver)
                    browser_logs = driver.get_log("browser")
                    errors = assert_audit(audit, bg_checks, browser_logs)
                    if audit.get("countryJa") != name_ja:
                        errors.append(f"Japanese country subtitle mismatch: expected {name_ja!r}, got {audit.get('countryJa')!r}")

                    row = {
                        "slug": slug,
                        "nameJa": name_ja,
                        "viewport": vp_name,
                        "url": url,
                        "audit": audit,
                        "backgroundImages": bg_checks,
                        "browserLogs": browser_logs,
                        "errors": errors,
                    }
                    results.append(row)
                    if errors:
                        screenshot = OUT / f"{slug}-{vp_name}.jpg"
                        full_page_screenshot(driver, screenshot)
                        row["screenshot"] = str(screenshot)
                        failures.append({"slug": slug, "viewport": vp_name, "errors": errors})
                        print(f"FAIL {slug} {vp_name}: " + " | ".join(errors), flush=True)
                    else:
                        print(f"PASS {slug} {vp_name}", flush=True)
                except Exception as exc:
                    try:
                        screenshot = OUT / f"{slug}-{vp_name}-exception.png"
                        screenshot.write_bytes(driver.get_screenshot_as_png())
                    except Exception:
                        pass
                    err = f"{type(exc).__name__}: {exc}"
                    failures.append({"slug": slug, "viewport": vp_name, "errors": [err]})
                    results.append({"slug": slug, "nameJa": name_ja, "viewport": vp_name, "url": url, "errors": [err]})
                    print(f"EXCEPTION {slug} {vp_name}: {err}", flush=True)
    finally:
        driver.quit()

    report = {
        "baseUrl": BASE_URL,
        "countries": [x[0] for x in countries],
        "viewports": VIEWPORTS,
        "results": results,
        "failures": failures,
        "pass": not failures,
    }
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pass": not failures, "failureCount": len(failures), "failures": failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
