#!/usr/bin/env python3
"""Verify real JOURNEY LENS photos on live ATLAS, including lazy-loaded photos."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ATLAS = "https://atlas.yagenji.com"
LENS = "https://journey.yagenji.com"
OUT = Path("qa-lens-photo-output")
OUT.mkdir(exist_ok=True)


def request(url: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JOURNEY-ATLAS-Lens-photo-QA/1.0", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=25) as response:
            head = response.read(24)
            return {"url": url, "status": response.status, "finalUrl": response.url,
                    "contentType": response.headers.get("Content-Type"),
                    "cors": response.headers.get("Access-Control-Allow-Origin"),
                    "bytesRead": len(head), "jpegHeader": head.startswith(b"\xff\xd8\xff")}
    except Exception as exc:
        return {"url": url, "error": f"{type(exc).__name__}: {exc}"}


def browser() -> webdriver.Chrome:
    opts = Options()
    for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--window-size=1440,1000"):
        opts.add_argument(arg)
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=opts)


def home(driver: webdriver.Chrome) -> dict:
    driver.get(ATLAS + "/")
    try:
        WebDriverWait(driver, 30).until(lambda d: d.execute_script(
            "return !!document.querySelector('.lens-card,.lens-rail__error')"))
    except Exception:
        pass
    driver.execute_script("document.querySelector('.lens-world')?.scrollIntoView({block:'center',behavior:'instant'})")
    try:
        WebDriverWait(driver, 30).until(lambda d: d.execute_script(
            "const a=[...document.querySelectorAll('.lens-card img')].slice(0,3);return a.length>0&&a.every(i=>i.complete)"))
    except Exception:
        pass
    output = driver.execute_script("""
      const images=[...document.querySelectorAll('.lens-card img')].slice(0,6);
      return {cards:document.querySelectorAll('.lens-card').length,
        error:document.querySelector('.lens-rail__error')?.textContent||null,
        images:images.map(i=>({url:i.currentSrc||i.src,complete:i.complete,width:i.naturalWidth,height:i.naturalHeight}))};
    """)
    output["consoleErrors"] = [x["message"] for x in driver.get_log("browser") if x["level"] in ("SEVERE", "WARNING")][-20:]
    driver.save_screenshot(str(OUT / "home-lens-visible.png"))
    return output


def country(driver: webdriver.Chrome) -> dict:
    driver.get(ATLAS + "/countries/guatemala/")
    try:
        WebDriverWait(driver, 30).until(lambda d: d.execute_script(
            "return !!document.querySelector('#country-lens-bridge:not([hidden])')"))
    except Exception:
        pass
    driver.execute_script("document.querySelector('#country-lens-bridge')?.scrollIntoView({block:'center',behavior:'instant'})")
    output = driver.execute_async_script(r"""
      const done=arguments[arguments.length-1];
      const section=document.querySelector('#country-lens-bridge');
      const thumb=document.querySelector('#country-lens-thumb');
      const bg=thumb?getComputedStyle(thumb).backgroundImage:'';
      const match=bg.match(/url\(["']?(.*?)["']?\)/);
      if(!match){done({sectionHidden:section?.hidden,background:bg,photo:null});return;}
      const im=new Image();let ended=false;
      const finish=ok=>{if(ended)return;ended=true;done({sectionHidden:section?.hidden,background:bg,photo:{url:im.src,ok,width:im.naturalWidth,height:im.naturalHeight}})};
      im.onload=()=>finish(true);im.onerror=()=>finish(false);im.src=match[1];setTimeout(()=>finish(false),15000);
    """)
    output["consoleErrors"] = [x["message"] for x in driver.get_log("browser") if x["level"] in ("SEVERE", "WARNING")][-20:]
    driver.save_screenshot(str(OUT / "guatemala-lens-visible.png"))
    return output


def main() -> int:
    checks = [request(LENS + "/rss.xml?lens_photo_qa=2"), request(LENS + "/uploads/DSC04709_tilal.jpg?lens_photo_qa=2"), request(ATLAS + "/countries/guatemala/?lens_photo_qa=2")]
    driver = browser()
    try:
        home_result = home(driver)
        country_result = country(driver)
    finally:
        driver.quit()
    photo_results = [request(x["url"] + "?lens_photo_qa=2") for x in home_result.get("images", [])[:3]]
    checks.extend([home_result, country_result, {"homepagePhotoRequests": photo_results}])
    print(json.dumps(checks, ensure_ascii=False, indent=2, default=str), flush=True)
    (OUT / "results.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2, default=str) + "\n")
    rss, photo, page = checks[:3]
    ok = (rss.get("status") == 200 and rss.get("cors") in ("*", ATLAS)
          and photo.get("status") == 200 and photo.get("contentType", "").startswith("image/")
          and page.get("status") == 200 and home_result.get("cards", 0) > 0
          and all(x.get("width", 0) > 0 for x in home_result.get("images", [])[:3])
          and country_result.get("sectionHidden") is False and (country_result.get("photo") or {}).get("ok"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
