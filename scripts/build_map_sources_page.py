#!/usr/bin/env python3
"""Generate map-sources/index.html from data/map-data-sources.json.

The page lists every geographic dataset used to draw the Country maps, its
licence and the Countries that use it (the registry's countries map).
Run after changing the registry; the test
tests/test_map_credits.py fails when the committed page is out of date.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "map-data-sources.json"
OUTPUT = ROOT / "map-sources" / "index.html"
# Datasets drawn on most maps: show the count instead of a long Country list.
SUMMARISED = {"naturalearth", "gshhg"}

HEAD = """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <base href="../">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="JOURNEY ATLASの国別地図に使っている地理データと、その利用条件。">
  <title>地図データの出典 — JOURNEY ATLAS</title>
  <link rel="canonical" href="https://atlas.yagenji.com/map-sources/">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="JOURNEY ATLAS">
  <meta property="og:title" content="地図データの出典 — JOURNEY ATLAS">
  <meta property="og:description" content="JOURNEY ATLASの国別地図に使っている地理データと、その利用条件。">
  <meta property="og:url" content="https://atlas.yagenji.com/map-sources/">
  <link rel="icon" href="assets/icons/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=Shippori+Mincho:wght@400;500;600&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/top-preview.css">
  <link rel="stylesheet" href="assets/css/site-info.css?v=20260908-palette-v1">
  <link rel="stylesheet" href="assets/css/site-unify.css?v=20260907-info-header-v3">
  <link rel="stylesheet" href="assets/css/site-footer.css?v=20260908-footer-unify-v1">
</head>
<body class="info-page">
  <header class="top-header shell is-scroll-sticky">
    <a class="brand-block" href="./" aria-label="JOURNEY ATLAS トップへ">
      <span class="wordmark">JOURNEY ATLAS</span>
      <small>行きたい場所と出会う、旅の図鑑。</small>
    </a>
    <nav aria-label="JOURNEY ATLAS メニュー">
      <a href="./#countries">国から探す</a>
      <a href="./#map">地図から探す</a>
      <a href="./#themes">テーマから探す</a>
      <a href="about/">About</a>
      <a href="./#lens-world">JOURNEY LENS</a>
    </nav>
  </header>

  <main class="info-main">
    <header class="info-hero">
      <span class="info-kicker">MAP DATA</span>
      <h1>地図データの出典</h1>
      <p>各国ページの地図は、以下の地理データをもとに、JOURNEY ATLASが投影・単純化・彩色して作成しています。各国ページの地図の下にも、その地図で使ったデータを表示しています。</p>
    </header>
"""

FOOTER = """  </main>

  <footer class="atlas-footer" aria-label="サイトフッター">
    <div class="atlas-footer__inner">
      <nav class="atlas-footer__nav" aria-label="フッターメニュー">
        <a href="about/">このサイトについて</a>
        <a href="faq/">よくある質問</a>
        <a href="privacy/">プライバシーポリシー</a>
        <a href="map-sources/" aria-current="page">地図データの出典</a>
        <a href="mailto:journeylensmy@gmail.com?subject=JOURNEY%20ATLAS%20%E3%81%B8%E3%81%AE%E3%81%94%E9%80%A3%E7%B5%A1">お問い合わせ</a>
      </nav>
      <small class="atlas-footer__copyright">© JOURNEY ATLAS</small>
    </div>
  </footer>
</body>
</html>
"""


def countries(credits: dict[str, list[str]]) -> list[dict]:
    rows = []
    for path in sorted((ROOT / "data" / "countries").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.append({
            "slug": data["slug"],
            "name": data.get("nameJa") or data["slug"],
            "credits": credits.get(data["slug"], []),
        })
    return rows


def render() -> str:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    registry = payload["sources"]
    rows = countries(payload["countries"])
    e = html.escape
    parts = [HEAD]
    for source_id, source in registry.items():
        users = [row for row in rows if source_id in row["credits"]]
        if not users:
            continue
        parts.append('\n    <section class="info-section" id="source-%s">\n' % e(source_id))
        parts.append('      <h2>%s</h2>\n' % e(source["label"]))
        link = '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (e(source["url"]), e(source["url"]))
        parts.append('      <p>提供元：%s</p>\n' % link)
        if source.get("license"):
            licence = e(source["license"])
            if source.get("licenseUrl"):
                licence = '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (e(source["licenseUrl"]), licence)
            parts.append('      <p>利用条件：%s</p>\n' % licence)
        if source.get("detail"):
            parts.append('      <p>使っている部分：%s</p>\n' % e(source["detail"]))
        if source_id in SUMMARISED:
            parts.append('      <p>使っている国・地域：全%dのうち%d</p>\n' % (len(rows), len(users)))
        else:
            names = "、".join(
                '<a href="countries/%s/">%s</a>' % (e(row["slug"]), e(row["name"])) for row in users
            )
            parts.append('      <p>使っている国・地域：%s</p>\n' % names)
        parts.append('    </section>\n')
    parts.append(
        '\n    <section class="info-section" id="source-notes">\n'
        '      <h2>加工と利用条件について</h2>\n'
        '      <p>いずれのデータも、地図の縮尺に合わせて投影・単純化・切り抜きを行い、JOURNEY ATLASの配色で描いています。元データの内容をそのまま再配布するものではありません。</p>\n'
        '      <p>国境の扱いは日本政府の立場に準拠しており、元データの表示と異なる場合があります。</p>\n'
        '    </section>\n'
    )
    parts.append(FOOTER)
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed page is out of date")
    args = parser.parse_args()
    page = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != page:
            raise SystemExit("map-sources/index.html is out of date: run scripts/build_map_sources_page.py")
        print("map-sources/index.html is up to date")
        return
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
