#!/usr/bin/env python3
"""Remote browser QA for JOURNEY ATLAS map pages.

This is temporary release QA tooling for map-quality-v2. It verifies the actual
Cloudflare branch preview and production pages rather than treating CI success
as visual completion.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

TARGETS = {
    "branch": "https://map-quality-v2.journey-atlas.pages.dev",
    "production": "https://journey-atlas.pages.dev",
}
COUNTRIES = ("sweden", "finland")
VIEWPORTS = {
    "desktop": {"width": 1440, "height": 1000},
    "mobile": {"width": 390, "height": 844},
}
OUT = Path("runtime-map-qa")


def screenshot_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(exist_ok=True)
    results: list[dict] = []
    failures: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        for target_name, base_url in TARGETS.items():
            for country in COUNTRIES:
                for viewport_name, viewport in VIEWPORTS.items():
                    context = browser.new_context(
                        viewport=viewport,
                        device_scale_factor=1,
                    )
                    page = context.new_page()
                    console_errors: list[str] = []
                    request_failures: list[str] = []
                    page.on(
                        "console",
                        lambda message, errors=console_errors: (
                            errors.append(message.text)
                            if message.type == "error"
                            else None
                        ),
                    )
                    page.on(
                        "requestfailed",
                        lambda request, failed=request_failures: failed.append(
                            f"{request.url} :: {request.failure}"
                        ),
                    )

                    url = f"{base_url}/countries/{country}/"
                    response = page.goto(url, wait_until="networkidle", timeout=60_000)
                    status = response.status if response else None

                    page.wait_for_selector(".country-page", timeout=30_000)
                    map_art = page.locator("#country-map-art")
                    map_art.scroll_into_view_if_needed()
                    page.wait_for_selector("#country-map-art img.map-base", timeout=30_000)
                    page.wait_for_function(
                        """() => {
                            const img = document.querySelector('#country-map-art img.map-base');
                            return img && img.complete && img.naturalWidth > 0;
                        }""",
                        timeout=30_000,
                    )
                    page.wait_for_timeout(500)

                    map_info = page.locator("#country-map-art img.map-base").evaluate(
                        """async (img) => {
                            const source = img.currentSrc || img.src;
                            const text = await (await fetch(source, {cache: 'no-store'})).text();
                            const viewBox = (text.match(/viewBox=["']([^"']+)["']/) || [null, null])[1];
                            return {
                                source,
                                naturalWidth: img.naturalWidth,
                                naturalHeight: img.naturalHeight,
                                viewBox,
                                loaded: img.complete && img.naturalWidth > 0
                            };
                        }"""
                    )

                    scene_markers = page.locator("#map-markers .map-marker").count()
                    capital_markers = page.locator("#map-markers .map-capital-marker").count()
                    hero_markers = page.locator("#map-markers .map-hero-marker").count()
                    overflow = page.evaluate(
                        "() => document.documentElement.scrollWidth - window.innerWidth"
                    )

                    screenshot = OUT / f"{target_name}-{country}-{viewport_name}.png"
                    map_art.screenshot(path=str(screenshot))

                    row = {
                        "target": target_name,
                        "country": country,
                        "viewport": viewport_name,
                        "url": url,
                        "status": status,
                        "map": map_info,
                        "sceneMarkers": scene_markers,
                        "capitalMarkers": capital_markers,
                        "heroMarkers": hero_markers,
                        "horizontalOverflowPx": overflow,
                        "consoleErrors": console_errors,
                        "requestFailures": request_failures,
                        "screenshot": screenshot.name,
                        "screenshotSha256": screenshot_sha(screenshot),
                    }
                    results.append(row)

                    prefix = f"{target_name}/{country}/{viewport_name}"
                    if status != 200:
                        failures.append(f"{prefix}: HTTP {status}")
                    if not map_info["loaded"]:
                        failures.append(f"{prefix}: map SVG did not load")
                    if not map_info["source"].endswith("map-atlas-v2.svg"):
                        failures.append(f"{prefix}: unexpected map asset {map_info['source']}")
                    if map_info["viewBox"] != "0 0 1200 760":
                        failures.append(f"{prefix}: SVG viewBox is {map_info['viewBox']}")
                    if scene_markers != 8:
                        failures.append(f"{prefix}: scene marker count={scene_markers}")
                    if capital_markers != 1:
                        failures.append(f"{prefix}: capital marker count={capital_markers}")
                    if hero_markers != 1:
                        failures.append(f"{prefix}: hero marker count={hero_markers}")
                    if overflow > 1:
                        failures.append(f"{prefix}: horizontal overflow={overflow}px")
                    if console_errors:
                        failures.append(f"{prefix}: console errors={console_errors}")
                    if request_failures:
                        failures.append(f"{prefix}: request failures={request_failures}")

                    context.close()

        browser.close()

    for country in COUNTRIES:
        for viewport in VIEWPORTS:
            branch = next(
                row for row in results
                if row["target"] == "branch"
                and row["country"] == country
                and row["viewport"] == viewport
            )
            production = next(
                row for row in results
                if row["target"] == "production"
                and row["country"] == country
                and row["viewport"] == viewport
            )
            branch["matchesProductionScreenshot"] = (
                branch["screenshotSha256"] == production["screenshotSha256"]
            )

    report = {
        "targets": TARGETS,
        "countries": COUNTRIES,
        "viewports": VIEWPORTS,
        "results": results,
        "failures": failures,
    }
    (OUT / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for row in results:
        print(
            row["target"],
            row["country"],
            row["viewport"],
            f"HTTP={row['status']}",
            f"viewBox={row['map']['viewBox']}",
            f"markers={row['sceneMarkers']}+{row['capitalMarkers']}+{row['heroMarkers']}",
            f"overflow={row['horizontalOverflowPx']}px",
            f"console={len(row['consoleErrors'])}",
            f"requests={len(row['requestFailures'])}",
        )
    if failures:
        print("Runtime map QA failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Runtime map QA passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
