#!/usr/bin/env python3
"""Verify a real Cloudflare Grenada publication, not merely GitHub's merge status."""
import json
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

BASE = "https://atlas.yagenji.com/"
EXPECTED = "697042598fff0316488ef77410a248d15fbed23a"
COUNTRY_URL = BASE + "countries/grenada/"


def get(path, *, binary=False):
    url = urljoin(BASE, path)
    request = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "JourneyAtlasPublicationQA/1.0"})
    with urllib.request.urlopen(request, timeout=20) as r:
        body = r.read()
        assert r.status == 200, (url, r.status)
        return body if binary else body.decode("utf-8")


last = None
for attempt in range(72):
    try:
        meta = json.loads(get("build-meta.json?grenada-publication-sha=" + EXPECTED + "-" + str(attempt)))
        observed = meta.get("commit")
        if observed == EXPECTED:
            print("Deployed Cloudflare SHA verified:", observed)
            break
        last = "live build SHA " + repr(observed)
    except Exception as exc:
        last = type(exc).__name__ + ": " + str(exc)
    if attempt % 8 == 0:
        print("Awaiting deployed SHA, observation:", last, flush=True)
    time.sleep(5)
else:
    raise RuntimeError("Could not verify the exact deployed main SHA: " + str(last))


class HeadMeta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots = []
        self.canonical = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            self.robots.append(attrs.get("content", ""))
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs.get("href", ""))

html = get("countries/grenada/?grenada-publication=" + EXPECTED)
assert 'data-country="grenada"' in html, "Country identity marker missing"
p = HeadMeta(); p.feed(html)
assert p.robots and any(x.replace(" ", "").lower() == "index,follow" for x in p.robots), p.robots
assert all("noindex" not in x.lower() for x in p.robots), p.robots
assert COUNTRY_URL in p.canonical, p.canonical
assert "noindex" not in html.lower(), "unexpected noindex on published Country"
print("Production Country HTML, canonical URL, index,follow: PASS")

country = json.loads(get("data/countries/grenada.json?grenada-publication=" + EXPECTED))
assert country.get("slug") == "grenada"
assert len(country.get("scenes", [])) == 8
assert len(country.get("taste", {}).get("items", [])) == 4
assets = [country["hero"]["image"], country["map"]["svg"]]
assets += [x["image"] for x in country["scenes"]]
assets += [x["image"] for x in country["taste"]["items"]]
assert len(assets) == 14 and len(set(assets)) == 14
for asset in assets:
    content = get(asset + "?grenada-publication=" + EXPECTED, binary=True)
    assert len(content) > 1500, (asset, len(content))
print("Live JSON, Hero, 8 scenes, 4 Taste images, and map HTTP 200: PASS")

sitemap = get("sitemap.xml?grenada-publication=" + EXPECTED)
assert COUNTRY_URL in sitemap, "Grenada absent from live sitemap"
print("Live sitemap includes canonical Grenada URL: PASS")

index = get("?grenada-publication=" + EXPECTED)
try:
    registry = json.loads(get("data/atlas-destinations.json?grenada-publication=" + EXPECTED))
    rows = [r for r in registry.get("destinations", []) if r.get("slug") == "grenada"]
    assert len(rows) == 1 and rows[0].get("atlasPublished") is True
    assert rows[0].get("href") == "countries/grenada/"
    print("Live destination registry marks Grenada published with canonical homepage route: PASS")
except urllib.error.HTTPError as exc:
    if exc.code != 404:
        raise
    assert "grenada" in index.lower(), "Grenada absent from homepage and no live registry JSON"
    print("Live homepage references Grenada: PASS; registry JSON is not publicly exported")

print("PRODUCTION VERIFICATION PASS", EXPECTED, COUNTRY_URL, flush=True)
