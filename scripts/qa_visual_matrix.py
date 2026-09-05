#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "data" / "country-renewal-status.json"
COUNTRY_DIR = ROOT / "data" / "countries"
BASE_URL = os.environ.get("QA_BASE_URL", "http://127.0.0.1:4173").rstrip("/")
OUT = Path(os.environ.get("QA_VISUAL_OUT_DIR", "qa-visual-matrix"))
RAW = OUT / "raw"
SCENE_SHEETS = OUT / "scene-sheets"
OUT.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)
SCENE_SHEETS.mkdir(parents=True, exist_ok=True)

def load_countries():
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    rows = []
    for row in status.get("countries", []):
        if not row.get("published"):
            continue
        slug = row["slug"]
        data = json.loads((COUNTRY_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        rows.append((slug, data.get("nameJa") or slug))
    return rows

def make_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--lang=ja-JP")
    driver_path = shutil.which("chromedriver")
    return webdriver.Chrome(service=Service(driver_path) if driver_path else Service(), options=options)

def set_viewport(driver, width, height, mobile=False):
    driver.set_window_size(width, height)
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1,
        "mobile": mobile, "screenWidth": width, "screenHeight": height
    })

def wait_page(driver):
    wait = WebDriverWait(driver, 35)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".scene-card")) == 8)
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".taste-card")) == 4)
    time.sleep(0.7)

def capture(driver, selector, path):
    el = driver.find_element(By.CSS_SELECTOR, selector)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.25)
    el.screenshot(str(path))

def fit_image(img, box_w, box_h):
    img = img.convert("RGB")
    ratio = min(box_w / img.width, box_h / img.height)
    size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
    return img.resize(size, Image.Resampling.LANCZOS)

def contact_sheet(items, path, cols=4, tile_w=320, tile_h=220, label_h=30, bg=(244,242,236)):
    rows = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * tile_w, rows * tile_h), bg)
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for i, (label, img_path) in enumerate(items):
        x = (i % cols) * tile_w
        y = (i // cols) * tile_h
        draw.rectangle([x, y, x + tile_w - 1, y + tile_h - 1], outline=(190,190,185))
        draw.text((x + 8, y + 7), label, fill=(30,30,30), font=font)
        img = Image.open(img_path)
        fitted = fit_image(img, tile_w - 12, tile_h - label_h - 10)
        px = x + (tile_w - fitted.width) // 2
        py = y + label_h + (tile_h - label_h - fitted.height) // 2
        canvas.paste(fitted, (px, py))
    canvas.save(path, quality=88)

def make_scene_sheet(slug, name, scene_paths):
    tile_w, tile_h, cols, label_h = 260, 190, 4, 24
    rows = 2
    canvas = Image.new("RGB", (tile_w * cols, tile_h * rows + 30), (244,242,236))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((8,8), f"{name} / {slug}", fill=(25,25,25), font=font)
    for i, p in enumerate(scene_paths):
        img = Image.open(p)
        fitted = fit_image(img, tile_w - 10, tile_h - label_h - 8)
        x = (i % cols) * tile_w
        y = 30 + (i // cols) * tile_h
        draw.text((x+6,y+4), f"S{i+1:02d}", fill=(30,30,30), font=font)
        px = x + (tile_w - fitted.width)//2
        py = y + label_h + (tile_h-label_h-fitted.height)//2
        canvas.paste(fitted,(px,py))
    out = SCENE_SHEETS / f"{slug}.jpg"
    canvas.save(out, quality=88)
    return out

def make_taste_sheet(slug, name, taste_paths):
    tile_w, tile_h, cols, label_h = 320, 260, 2, 24
    rows = 2
    canvas = Image.new("RGB", (tile_w * cols, tile_h * rows + 30), (244,242,236))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((8,8), f"{name} / {slug}", fill=(25,25,25), font=font)
    for i, p in enumerate(taste_paths):
        img = Image.open(p)
        fitted = fit_image(img, tile_w - 10, tile_h - label_h - 8)
        x = (i % cols) * tile_w
        y = 30 + (i // cols) * tile_h
        draw.text((x+6,y+4), f"FOOD{i+1:02d}", fill=(30,30,30), font=font)
        px = x + (tile_w - fitted.width)//2
        py = y + label_h + (tile_h-label_h-fitted.height)//2
        canvas.paste(fitted,(px,py))
    out = OUT / "taste-sheets" / f"{slug}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=88)
    return out

def main():
    countries = load_countries()
    maps = []
    scene_overview = []
    taste_overview = []

    # Build Scene / Taste matrices directly from the approved production assets.
    for slug, name in countries:
        data = json.loads((COUNTRY_DIR / f"{slug}.json").read_text(encoding="utf-8"))

        scene_paths = [ROOT / item["image"] for item in data.get("scenes", [])]
        sp = make_scene_sheet(slug, name, scene_paths)
        scene_overview.append((f"{name} / {slug}", sp))

        taste_paths = [ROOT / item["image"] for item in data.get("taste", {}).get("items", [])]
        tp = make_taste_sheet(slug, name, taste_paths)
        taste_overview.append((f"{name} / {slug}", tp))

    contact_sheet(scene_overview, OUT / "04-scenes-contact.jpg", cols=2, tile_w=620, tile_h=420)
    contact_sheet(taste_overview, OUT / "05-taste-contact.jpg", cols=3, tile_w=420, tile_h=360)

    # Map needs the rendered Country page because labels and markers are runtime UI.
    driver = make_driver()
    try:
        for slug, name in countries:
            url = f"{BASE_URL}/countries/{slug}/?visual-audit={int(time.time())}"
            print(f"CAPTURE MAP {slug}", flush=True)
            set_viewport(driver, 1440, 1000, False)
            driver.get(url)
            wait_page(driver)
            mp = RAW / f"{slug}-map.png"
            capture(driver, "#country-map-art", mp)
            maps.append((f"{name} / {slug}", mp))
    finally:
        driver.quit()

    contact_sheet(maps, OUT / "03-map-contact.jpg", cols=4, tile_w=360, tile_h=250)

    manifest = {
        "baseUrl": BASE_URL,
        "countries": [{"slug": s, "nameJa": n} for s,n in countries],
        "phase": "scenes-map-taste",
        "outputs": ["03-map-contact.jpg", "04-scenes-contact.jpg", "05-taste-contact.jpg"]
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
