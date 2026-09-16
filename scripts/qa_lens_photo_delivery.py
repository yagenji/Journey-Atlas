#!/usr/bin/env python3
"""Diagnose real JOURNEY LENS photos on live ATLAS without changing images or design."""
from __future__ import annotations

import json
import urllib.error
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


def evaluate(driver: webdriver.Chrome, target: str, selector: str, image_script: str) -> dict:
    driver.get(target)
    try:
        WebDriverWait(driver, 35).until(lambda d: d.execute_script(
            "return document.querySelector(arguments[0]) !== null", selector))
    except Exception as exc:
        return {"page": target, "error": f"element unavailable: {exc}", "title": driver.title}
    # Allow the asynchronous external feed and visible image to load.
    try:
        WebDriverWait(driver, 35).until(lambda d: d.execute_script(
            "return !!document.querySelector('.lens-card,.lens-rail__error') || !!document.querySelector('#country-lens-bridge:not([hidden])')"))
    except Exception:
        pass
    result = driver.execute_async_script(image_script)
    result["page"] = target
    result["consoleErrors"] = [x["message"] for x in driver.get_log("browser") if x["level"] in ("SEVERE", "WARNING")][-20:]
    driver.save_screenshot(str(OUT / ("home.png" if target == ATLAS + "/" else "guatemala.png")))
    return result


HOME = r"""
const done=arguments[arguments.length-1];
const cards=[...document.querySelectorAll('.lens-card')];
const imgs=cards.slice(0,6).map(c=>c.querySelector('img'));
const error=document.querySelector('.lens-rail__error')?.textContent||null;
const first=imgs[0];
const finish=()=>done({cards:cards.length,error,images:imgs.map(i=>i?{url:i.currentSrc||i.src,complete:i.complete,width:i.naturalWidth,height:i.naturalHeight}:null)});
if(first&&!first.complete){first.addEventListener('load',finish,{once:true});first.addEventListener('error',finish,{once:true});setTimeout(finish,15000)}else finish();
"""
COUNTRY = r"""
const done=arguments[arguments.length-1];
const section=document.querySelector('#country-lens-bridge');
const thumb=document.querySelector('#country-lens-thumb');
const bg=thumb?getComputedStyle(thumb).backgroundImage:'';
const match=bg.match(/url\(["']?(.*?)["']?\)/);
if(!match){done({sectionHidden:section?.hidden,background:bg,photo:null});return;}
const im=new Image();let ended=false;
const finish=ok=>{if(ended)return;ended=true;done({sectionHidden:section?.hidden,background:bg,photo:{url:im.src,ok,width:im.naturalWidth,height:im.naturalHeight}})};
im.onload=()=>finish(true);im.onerror=()=>finish(false);im.src=match[1];setTimeout(()=>finish(false),15000);
"""


def main() -> int:
    checks = [request(LENS + "/rss.xml?lens_photo_qa=1"), request(LENS + "/uploads/DSC04709_tilal.jpg?lens_photo_qa=1"), request(ATLAS + "/countries/guatemala/?lens_photo_qa=1")]
    driver = browser()
    try:
        checks.append(evaluate(driver, ATLAS + "/", ".lens-rail", HOME))
        checks.append(evaluate(driver, ATLAS + "/countries/guatemala/", "#country-lens-bridge", COUNTRY))
    finally:
        driver.quit()
    print(json.dumps(checks, ensure_ascii=False, indent=2, default=str), flush=True)
    (OUT / "results.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2, default=str) + "\n")
    rss, photo, page, home, country = checks
    ok = (rss.get("status") == 200 and rss.get("cors") in ("*", ATLAS)
          and photo.get("status") == 200 and photo.get("contentType", "").startswith("image/")
          and page.get("status") == 200 and home.get("cards", 0) > 0
          and any(i and i.get("width", 0) > 0 for i in home.get("images", []))
          and country.get("sectionHidden") is False and (country.get("photo") or {}).get("ok"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
