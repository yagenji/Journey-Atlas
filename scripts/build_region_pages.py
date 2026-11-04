#!/usr/bin/env python3
"""Build canonical sub-Country pages with the shared JOURNEY ATLAS Country layout.

Region data and approved image assets stay independent of the 202-destination
registry. Region pages remain noindex and undiscoverable until published.
"""
from __future__ import annotations

import html
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / 'data' / 'regions'
TEMPLATE = ROOT / 'region.html'


# Any Region CSS/JS edit must produce a new URL, even when the Country
# data version stays unchanged. This prevents a 24-hour stale visual/UI cache.
REGION_RUNTIME_ASSETS = (
    'assets/css/site-nav.css',
    'assets/css/country.css',
    'assets/css/region.css',
    'assets/css/atlas-personal.css',
    'assets/js/site-nav.js',
    'assets/js/header-scroll.js',
    'assets/js/atlas-personal.js',
    'assets/js/region-interactions.js',
)


def region_asset_version() -> str:
    digest = hashlib.sha256()
    for relative in REGION_RUNTIME_ASSETS:
        digest.update(relative.encode('utf-8'))
        digest.update(b'\0')
        digest.update((ROOT / relative).read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()[:16]



def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def approved_image(value: str, version: str) -> str:
    if not re.fullmatch(r'assets/images/[a-z0-9/_-]+/approved/[a-z0-9_-]+\.webp', value):
        raise ValueError(f'Unsafe or non-approved image path: {value}')
    if not (ROOT / value).is_file():
        raise FileNotFoundError(value)
    return f'{esc(value)}?v={esc(version)}'


def render_image(path: str, alt: str, version: str, *, eager: bool = False) -> str:
    loading = 'eager' if eager else 'lazy'
    priority = ' fetchpriority="high"' if eager else ' fetchpriority="low"'
    return (f'<img src="{approved_image(path, version)}" alt="{esc(alt)}" '
            f'loading="{loading}" decoding="async"{priority}>')


def icon(name: str) -> str:
    if not re.fullmatch(r'[a-z0-9-]+', name):
        raise ValueError(f'Unsafe icon name: {name}')
    return (f'<svg class="ui-icon" aria-hidden="true" viewBox="0 0 24 24">'
            f'<use href="assets/icons/atlas-icons.svg#{name}"></use></svg>')



def interactive_map_position(coords: dict, marker_index: int, svg: str) -> tuple[float, float]:
    """Calibrated placement over the approved map's numbered points.

    Check that each number embedded in the approved SVG still matches its
    source Scene coordinates. The overlay adds interaction, not geography.
    """
    point = re.search(
        rf'<g id="text_{marker_index}">\s*<!--\s*{marker_index}\s*-->\s*<g[^>]*?'
        rf'transform="translate\(([0-9.]+) ([0-9.]+)\)',
        svg,
    )
    if point is None:
        raise ValueError(f'Approved map is missing Scene label {marker_index}')
    latitude, longitude = coords['latitude'], coords['longitude']
    mercator_y = math.log(math.tan(math.pi / 4 + math.radians(latitude) / 2))
    px = 42.04571769282578 * longitude + 588.6427115953087
    py = -2409.042178193165 * mercator_y + 3286.625337833689
    if abs(px - float(point.group(1))) > 1 or abs(py - float(point.group(2))) > 1:
        raise ValueError(f'Scene {marker_index}: approved SVG and real coordinates disagree')
    return 100 * (px + 2.7) / 864, 100 * (py - 2.8) / 547.2


def render_region(data: dict, *, site_url: str, version: str) -> tuple[str, str, bool]:
    parent, slug = data['parentSlug'], data['slug']
    if not all(re.fullmatch(r'[a-z0-9-]+', value) for value in (parent, slug)):
        raise ValueError('Unsafe region/parent slug')
    if parent != 'unitedkingdom':
        raise ValueError('The current Region pilot must stay under the United Kingdom')
    if data['schemaVersion'] != 1 or len(data['scenes']) != 8 or len(data['taste']['items']) != 4:
        raise ValueError('Region requires schemaVersion=1, exactly 8 Scenes and 4 Taste')
    if len({s['id'] for s in data['scenes']}) != 8:
        raise ValueError('Duplicate Scene identifiers')
    for item in [data['hero'], *data['scenes']]:
        coords = item['coordinates']
        if not (-90 <= coords['latitude'] <= 90 and -180 <= coords['longitude'] <= 180):
            raise ValueError(f'Invalid coordinates: {item}')
    for item in [data['hero'], *data['scenes'], *data['taste']['items']]:
        approved_image(item['image'], version)
    if not (ROOT / data['map']['svg']).is_file():
        raise FileNotFoundError(data['map']['svg'])

    map_svg_text = (ROOT / data['map']['svg']).read_text(encoding='utf-8')
    title = f"{data['nameJa']} | {data['nameEn']} — JOURNEY ATLAS"
    canonical = urljoin(site_url, f'countries/{parent}/{slug}/')
    published = data.get('regionPublished') is True
    hero = data['hero']
    result: list[str] = []

    # Hero uses the exact shared Country section hierarchy and typography.
    result.append('<article class="country-page region-country-page">')
    result.append('<section class="hero" aria-labelledby="region-title">'
        '<div class="hero-art media-slot has-image" role="img" '
        f'aria-label="表紙の景色：{esc(hero["name"])}">'
        + render_image(hero['image'], f'{hero["name"]}を描いた景観イメージ', version, eager=True)
        + '</div><div class="hero-copy page-shell">'
        '<p class="region">EUROPE / UNITED KINGDOM</p>'
        f'<h1 id="region-title">{esc(data["nameEn"])}</h1>'
        f'<p class="country-ja">{esc(data["nameJa"])}</p>'
        f'<p class="hero-lead">{esc(hero["lead"])}</p></div></section>')
    result.append('<aside class="hero-caption" id="hero-caption" aria-label="表紙の景色">'
        '<div class="hero-caption__inner page-shell">'
        '<div class="hero-caption__body">'
        f'<p class="hero-caption__name">{esc(hero["name"])}</p>'
        f'<p class="hero-caption__local">{esc(hero["location"])}</p>'
        f'<p class="hero-caption__text">{esc(hero["description"])}</p>'
        '</div></div></aside>')
    result.append('<div class="atlas-body page-shell">')

    facts_icons = ['globe', 'landmark', 'users', 'map', 'language', 'coin']
    facts = ''.join('<div>' + icon(facts_icons[i] if i < len(facts_icons) else 'info')
        + f'<dt>{esc(item["label"])}</dt><dd>{esc(item["value"])}</dd></div>'
        for i, item in enumerate(data['profile']))
    result.append('<section class="country-facts-strip" aria-labelledby="region-facts-title">'
        '<div class="country-facts-strip__head"><span class="section-kicker-en">REGION PROFILE</span>'
        '<h2 id="region-facts-title">基本情報</h2></div>'
        f'<dl class="fact-list">{facts}</dl></section>')

    # Distinctive numbers use the existing shared Signature Facts band.
    signature = data.get('signatureFacts', [])
    if signature:
        result.append('<section class="signature-facts" aria-labelledby="region-signature-title">'
            '<div class="signature-facts__head"><span class="section-kicker-en">SIGNATURE FACTS</span>'
            '<h2 id="region-signature-title">この地域を知る数字</h2></div>'
            '<div class="signature-facts__grid">')
        for item in signature:
            result.append('<article><div class="signature-fact__label">'
                + icon(item.get('icon', 'spark'))
                + f'<span>{esc(item["label"])}</span></div>'
                f'<strong>{esc(item["value"])}</strong><p>{esc(item["note"])}</p></article>')
        result.append('</div></section>')

    # Standard Country map-left / eight-Scene-right panel and card formatting.
    result.append('<section class="atlas-panel" aria-labelledby="region-scenery-title">'
        '<div class="map-column"><div class="panel-title-wrap"><div class="panel-title-copy">'
        '<span class="section-kicker-en">TRAVEL MAP</span>'
        '<h2 class="panel-title">旅の地図</h2></div></div>'
        '<div class="map-frame"><div class="map-art has-map" id="country-map-art" '
        'role="group" aria-label="スコットランドの景色の地図">'
        f'<img class="map-base" src="{esc(data["map"]["svg"])}" '
        'alt="実在する海岸線と景色8地点、Hero地点を示すスコットランドの地図" '
        'loading="lazy" decoding="async">'
        '<div class="region-map-hits" id="region-map-hits">'
        + ''.join(
            '<button type="button" class="region-map-hit" '
            f'data-scene="{esc(scene["id"])}" '
            f'style="left:{interactive_map_position(scene["coordinates"], index, map_svg_text)[0]:.5f}%;'
            f'top:{interactive_map_position(scene["coordinates"], index, map_svg_text)[1]:.5f}%" '
            f'aria-label="{index} {esc(scene["name"])}を選択" aria-pressed="false"></button>'
            for index, scene in enumerate(data['scenes'], 1)
        )
        + '</div></div></div>'
        '<div class="map-legend map-legend--below" aria-label="地図記号の説明">'
        '<span><i class="map-legend__scene" aria-hidden="true">1</i>景色の番号</span>'
        '<span><i class="map-legend__hero" aria-hidden="true"></i>Heroの場所</span></div>'
        '<div class="encounter-strip"><span class="section-kicker-en">ENCOUNTERS</span>'
        f'<h3>{esc(data["nameJa"])}で出会えるもの</h3><div class="encounter-list">'
        + ''.join('<article>' + icon(item.get('icon', 'compass')) + f'<b>{esc(item["title"])}</b></article>'
                  for item in data.get('encounters', []))
        + '</div></div>'
        '</div><div class="scenes-column">'
        '<div class="scenes-heading"><div class="scenes-title-wrap">'
        '<span class="section-kicker-en">SCENERY</span>'
        '<h2 id="region-scenery-title">この地域で見たい景色 <b>8</b>選</h2>'
        '</div><p class="scenes-intro">実在する場所を題材に制作した景観イメージです。現地写真ではありません。</p></div>'
        '<div class="scene-grid" id="scene-cards">')
    for i, scene in enumerate(data['scenes'], 1):
        number = str(i)
        result.append(f'<article class="scene-card region-scene" data-scene="{esc(scene["id"])}" '
            f'id="scene-{esc(scene["id"])}" role="button" tabindex="0" aria-pressed="false" '
            f'aria-label="{number} {esc(scene["name"])}を選択">'
            '<div class="scene-image media-slot" role="img" '
            f'aria-label="景色 {number}：{esc(scene["name"])}">'
            + render_image(scene['image'], f'{scene["name"]}の景観イメージ', version)
            + f'<b aria-hidden="true">{number}</b></div>'
            f'<div class="scene-copy"><strong>{number}</strong><div>'
            f'<h3>{esc(scene["name"])}</h3><small>{esc(scene["nameLocal"])}</small>'
            f'<p>{esc(scene["description"])}</p></div></div></article>')
    result.append('</div></div></section>')

    result.append('<section class="atlas-extras" aria-labelledby="region-culture-title">'
        '<div class="atlas-extras__head"><div>'
        '<p class="atlas-extras__kicker">BEYOND THE SCENERY</p>'
        '<h2 id="region-culture-title">景色の向こうへ</h2></div>'
        '<p class="atlas-extras__intro">景色だけでは見えない、この地域の暮らしや文化、歴史の輪郭をたどる。</p></div>'
        '<div class="atlas-extras__grid">')
    for item in data['culture']:
        result.append('<article class="atlas-extra"><span class="atlas-extra__theme">'
            + icon(item.get('icon', 'culture'))
            + f'{esc(item.get("themeEn", "CULTURE"))} / {esc(item.get("themeJa", "文化"))}</span>'
            f'<h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p>'
            + ('<ul>' + ''.join(f'<li>{esc(point)}</li>' for point in item.get('points', [])) + '</ul>'
               if item.get('points') else '') + '</article>')
    result.append('</div></section>')

    result.append('<section class="taste-section" aria-labelledby="region-taste-title">'
        '<div class="taste-section__head"><div><span class="section-kicker-en">TASTE OF SCOTLAND</span>'
        f'<h2 id="region-taste-title">{esc(data["taste"]["title"])}</h2></div></div>'
        '<div class="taste-grid">')
    for item in data['taste']['items']:
        result.append('<article class="taste-card region-taste"><div class="taste-card__image media-slot">'
            + render_image(item['image'], f'{item["name"]}の料理イメージ', version)
            .replace('<img ', '<img class="taste-card__img" ', 1)
            + '</div><div class="taste-card__copy">'
            f'<h3>{esc(item["name"])}</h3><small>{esc(item["nameLocal"])}</small>'
            f'<p>{esc(item["text"])}</p></div></article>')
    result.append('</div></section>')

    trivia = data.get('travelTrivia', [])
    if trivia:
        result.append('<section class="travel-trivia" aria-labelledby="region-trivia-title">'
            '<div class="travel-trivia__head"><div>'
            '<span class="travel-trivia__kicker">TRAVEL TRIVIA</span>'
            '<h2 id="region-trivia-title">知っていると旅が少し楽しくなること</h2></div>'
            '<p class="travel-trivia__intro">現地で見つけたり、試したり、人に話したくなる小さな知識を集めた。</p></div>'
            '<div class="travel-trivia__grid">')
        for item in trivia:
            result.append('<article class="travel-trivia__item"><div class="travel-trivia__meta">'
                + icon(item.get('icon', 'spark'))
                + f'<span>{esc(item["categoryEn"])} / {esc(item["categoryJa"])}</span></div>'
                f'<h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></article>')
        result.append('</div></section>')

    result.append('<section class="travel-guidance" aria-label="旅のヒント">'
        '<section class="travel-guidance__block" aria-labelledby="region-for-whom-title">'
        '<span class="section-kicker-en">FOR WHOM</span>'
        '<h2 id="region-for-whom-title">こんな人に</h2><div class="persona-list">')
    for item in data['forWhom']:
        result.append('<article>' + icon('traveler')
            + f'<div><h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></div></article>')
    result.append('</div></section><section class="travel-guidance__block" '
        'aria-labelledby="region-travel-notes-title">'
        '<span class="section-kicker-en">TRAVEL NOTES</span>'
        '<h2 id="region-travel-notes-title">知っておきたいこと</h2><div class="tip-list">')
    for item in data['notes']:
        result.append('<article>' + icon('note')
            + f'<div><h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></div></article>')
    result.append('</div></section></section>')

    result.append('<section class="travel-planning" aria-labelledby="region-when-title">'
        '<div class="travel-planning__head"><span class="section-kicker-en">WHEN TO GO</span>'
        '<h2 id="region-when-title">旅するなら</h2></div>'
        '<div class="travel-planning__content">')
    travel_scale = data.get('travelScale', {})
    if travel_scale.get('items'):
        result.append('<section class="travel-scale travel-planning__block travel-planning__block--days" '
            'aria-labelledby="region-days-title"><div class="travel-scale__head"><span class="travel-planning__label">DURATION</span>'
            f'<h3 id="region-days-title">{esc(travel_scale.get("title", "旅の目安日程"))}</h3>'
            f'<p>{esc(travel_scale.get("intro", ""))}</p></div><div class="travel-scale__grid">')
        for item in travel_scale['items']:
            result.append('<article class="travel-scale__item"><span class="travel-scale__icon">'
                + icon(item.get('icon', 'calendar')) + '</span><div>'
                f'<strong>{esc(item["duration"])}</strong><h4>{esc(item["title"])}</h4>'
                f'<p>{esc(item["text"])}</p></div></article>')
        result.append('</div></section>')
    result.append('<section class="travel-planning__block travel-planning__block--season" '
        'aria-labelledby="region-season-title"><span class="travel-planning__label">SEASON</span>'
        '<h3 id="region-season-title">季節</h3>')
    windows = data.get('bestSeason', {}).get('windows', [])
    if windows:
        result.append('<div class="season-best"><span class="season-best__tag">おすすめの時期</span>'
            '<dl>' + ''.join(f'<div><dt>{esc(w["label"])}</dt><dd>{esc(w["reason"])}</dd></div>'
                             for w in windows) + '</dl></div>')
    result.append('<div class="season-list">')
    for item in data['seasons']:
        result.append('<article style="--season-color:' + esc(item.get('color', '#73966f')) + '">'
            + icon(item.get('icon', 'calendar'))
            + f'<div><b>{esc(item["months"])}</b><p>{esc(item["text"])}</p></div></article>')
    result.append('</div></section>')
    transport = data.get('transport') or {}
    if transport:
        result.append('<section class="travel-planning__block travel-planning__block--transport" '
            'aria-labelledby="region-transport-title">'
            '<span class="travel-planning__label">TRANSPORT</span>'
            '<h3 id="region-transport-title">移動</h3><div class="transport">'
            '<span class="transport-icon">' + icon(transport.get('icon', 'road')) + '</span>'
            '<div><small>移動</small>'
            f'<h4>{esc(transport["title"])}</h4><p>{esc(transport["text"])}</p></div></div></section>')
    result.append('</div></section>')

    if data.get('nextRoutes'):
        result.append('<section class="next-routes-section" aria-labelledby="region-routes-title">'
            '<div class="next-routes__head"><div>'
            '<span class="section-kicker-en">NEXT ROUTES</span>'
            '<h2 id="region-routes-title">隣の地域へ旅をつなぐ</h2></div>'
            '<p>この地域から旅を続けやすい、代表的な周遊ルート。</p>'
            '</div><div class="next-routes__grid">')
        for route in data['nextRoutes']:
            result.append('<article class="next-route-card"><div class="next-route-card__country">'
                f'<span class="next-route-card__flag" aria-hidden="true">{esc(route.get("flag", ""))}</span><div>'
                f'<strong>{esc(route["countryEn"])}</strong>'
                f'<small>{esc(route["countryJa"])}</small></div></div>'
                f'<p class="next-route-card__path">{esc(route["path"])}</p>'
                f'<p class="next-route-card__description">{esc(route["description"])}</p></article>')
        result.append('</div></section>')


    # Shared Country footer: next destinations and wishlist in one section.
    related = data.get('relatedCountries') or []
    result.append('<section class="journey-footer region-journey-footer" aria-labelledby="region-next-title">')
    if related:
        result.append('<div class="related-wrap region-related">'
            '<span class="section-kicker-en">NEXT DESTINATIONS</span>'
            f'<h2 id="region-next-title">{esc(data["nameJa"])}が気になったなら</h2>'
            '<div class="related-grid">')
        for item in related:
            href = item.get('href', '')
            if not re.fullmatch(r'countries/[a-z0-9-]+/', href):
                raise ValueError(f'Unsafe related Country URL: {href}')
            result.append(f'<a class="related-card is-open" href="{esc(href)}" '
                f'aria-label="{esc(item["nameJa"])}のJOURNEY ATLASを見る">'
                '<div class="related-country">'
                f'<span class="related-flag" aria-hidden="true">{esc(item.get("flag","◌"))}</span>'
                '<div class="related-copy">'
                f'<h3>{esc(item["nameEn"])}</h3><b>{esc(item["nameJa"])}</b>'
                f'<p>{esc(item.get("reason","国ページを見る"))}</p>'
                '<small class="related-status">EXPLORE →</small></div></div></a>')
        result.append('</div></div>')
    result.append('<div class="wish-wrap region-wish-wrap">'
        '<button class="wish-button" id="region-wish-button" type="button" aria-pressed="false">'
        '<span class="wish-icon" aria-hidden="true">♡</span>'
        '<strong>この地域に行きたい</strong>'
        '<small>このブラウザに保存します</small></button>'
        '<p class="wish-status" id="region-wish-status" role="status"></p>'
        '</div></section>')

    result.append('<nav class="region-back" aria-label="イギリス全体のページへ戻る">'
        '<div class="region-back__copy">'
        '<span class="region-back__label">EXPLORE UNITED KINGDOM</span>'
        '<p>イギリス全体の景色と地図も見る</p></div>'
        f'<a href="countries/{esc(parent)}/"><span aria-hidden="true">←</span> イギリスへ戻る</a></nav>')
    result.append('<details class="region-sources"><summary>DATA SOURCES / 参考資料</summary><ul>'
        + ''.join(f'<li><a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(key)}</a></li>'
                  for key, url in data['sources'].items()) + '</ul></details>')
    result.append('</div></article>')

    page = TEMPLATE.read_text(encoding='utf-8')
    replacements = {
        '{{ROBOTS}}': 'index,follow' if published else 'noindex,follow',
        '{{DESCRIPTION}}': esc(data['seo']['description']),
        '{{CANONICAL}}': esc(canonical),
        '{{TITLE}}': esc(title),
        '{{OG_IMAGE}}': esc(urljoin(site_url, f'{hero["image"]}?v={version}')),
        '{{ASSET_VERSION}}': esc(region_asset_version()),
        '{{CONTENT}}': '\n'.join(result),
    }
    for token, value in replacements.items():
        if token not in page:
            raise ValueError(f'Region HTML template field missing: {token}')
        page = page.replace(token, value)
    if '{{' in page or '}}' in page:
        raise ValueError('Unreplaced template tokens')
    return page, canonical, published


def generate_region_pages(*, site_url: str, version: str,
                          parents: set[str] | None = None) -> list[str]:
    published_urls: list[str] = []
    for path in sorted(DATA_ROOT.glob('*/*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        if parents is not None and data['parentSlug'] not in parents:
            continue
        page, canonical, published = render_region(data, site_url=site_url, version=version)
        output = ROOT / 'countries' / data['parentSlug'] / data['slug'] / 'index.html'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(page, encoding='utf-8')
        if published:
            published_urls.append(canonical)
    return published_urls


if __name__ == '__main__':
    for url in generate_region_pages(site_url='https://atlas.yagenji.com/', version='local'):
        print('Published:', url)
    print('Built reviewable Region pages')