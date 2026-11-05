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
from xml.etree import ElementTree as ET

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




def region_theme_labels(parent_slug: str) -> list[str]:
    """Use the existing Country taxonomy as the source of Hero travel themes."""
    payload = json.loads((ROOT / 'data/theme-taxonomy.json').read_text(encoding='utf-8'))
    return [
        str(theme['label'])
        for theme in payload.get('themes', [])
        if parent_slug in (theme.get('examples') or []) and theme.get('label')
    ]


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



def recorded_map_position(coords: dict, marker_id: str, svg: str,
                          bounds: dict | None) -> tuple[float, float] | None:
    """Validate geographic anchors and place the interactive dots on real points.

    New maps record real coordinates independently from label offsets. Retain
    the calibrated legacy Scotland projection for its existing approved map.
    """
    if 'data-map-projection="local-equirectangular-fit-v1"' not in svg:
        return None
    if not bounds:
        raise ValueError('Projected Region map requires geographic bounds')
    root = ET.fromstring(svg)
    if root.get('viewBox') != '0 0 1200 760':
        raise ValueError('Region map must use the shared 1200 by 760 canvas')
    node = root.find(f'.//*[@id="{marker_id}"]')
    if node is None:
        raise ValueError(f'Region map is missing {marker_id}')
    lat, lon = coords['latitude'], coords['longitude']
    if any(abs(float(node.get(key, 'nan')) - value) > 0.000001
           or not math.isfinite(float(node.get(key, 'nan')))
           for key, value in [('data-latitude', lat), ('data-longitude', lon)]):
        raise ValueError(f'{marker_id}: SVG and Region coordinates disagree')
    west, south, east, north = (bounds[key] for key in ('west', 'south', 'east', 'north'))
    if not (-180 <= west < east <= 180 and -90 < south < north < 90):
        raise ValueError('Invalid Region map bounds')
    cosine = math.cos(math.radians((south + north) / 2))
    scale = min(1200 / ((east - west) * cosine), 760 / (north - south))
    px = (1200 - (east - west) * cosine * scale) / 2 + (lon - west) * cosine * scale
    py = (760 - (north - south) * scale) / 2 + (north - lat) * scale
    for key, expected in [('data-x', px), ('data-y', py)]:
        recorded = float(node.get(key, 'nan'))
        if not math.isfinite(recorded) or abs(recorded - expected) > 0.01:
            raise ValueError(f'{marker_id}: SVG projection and real coordinates disagree')
    # Use the verified geographic point, never an old callout label offset.
    # The map no longer draws leader lines connecting those old offsets.
    x, y = px, py
    if not (math.isfinite(x) and math.isfinite(y) and 0 <= x <= 1200 and 0 <= y <= 760):
        raise ValueError(f'{marker_id}: map label is outside the canvas')
    return 100 * x / 1200, 100 * y / 760


def interactive_map_position(coords: dict, marker_index: int, svg: str,
                             bounds: dict | None = None) -> tuple[float, float]:
    """Calibrated placement over the approved map's numbered points.

    Check that each number embedded in the approved SVG still matches its
    source Scene coordinates. The overlay adds interaction, not geography.
    """
    recorded = recorded_map_position(coords, f'scene-marker-{marker_index}', svg, bounds)
    if recorded is not None:
        return recorded
    point = re.search(
        rf'<g id="text_{marker_index}"[^>]*>\s*<!--\s*{marker_index}\s*-->\s*<g[^>]*?'
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


def region_hero_map_position(coords: dict, svg: str = '',
                             bounds: dict | None = None) -> tuple[float, float]:
    """Project the real Hero point using the same calibrated Scotland map transform."""
    recorded = recorded_map_position(coords, 'hero-marker', svg, bounds)
    if recorded is not None:
        return recorded
    latitude, longitude = coords['latitude'], coords['longitude']
    mercator_y = math.log(math.tan(math.pi / 4 + math.radians(latitude) / 2))
    px = 42.04571769282578 * longitude + 588.6427115953087
    py = -2409.042178193165 * mercator_y + 3286.625337833689
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
    map_version = hashlib.sha256(map_svg_text.encode('utf-8')).hexdigest()[:16]
    title = f"{data['nameJa']} | {data['nameEn']} — JOURNEY ATLAS"
    canonical = urljoin(site_url, f'countries/{parent}/{slug}/')
    published = data.get('regionPublished') is True
    hero = data['hero']
    # Use the existing Country title sizing, including its tablet breakpoint.
    title_length = len(re.sub(r'\s+', '', data['nameEn'].strip()))
    title_classes = 'hero-title--long' if title_length >= 12 else ''
    if title_length >= 18:
        title_classes += ' hero-title--very-long'
    result: list[str] = []

    # Hero uses the exact shared Country section hierarchy and typography.
    result.append('<article class="country-page region-country-page">')
    result.append('<section class="hero" aria-labelledby="region-title">'
        '<div class="hero-art media-slot has-image" role="img" '
        f'aria-label="表紙の景色：{esc(hero["name"])}">'
        + render_image(hero['image'], f'{hero["name"]}を描いた景観イメージ', version, eager=True)
        + '</div><div class="hero-copy page-shell">'
        f'<p class="region">{esc(data["region"])}</p>'
        f'<h1 id="region-title" class="{title_classes}">{esc(data["nameEn"])}</h1>'
        f'<p class="country-ja">{esc(data["nameJa"])}</p>'
        f'<p class="hero-lead">{esc(hero["lead"])}</p>'
        '<div class="country-theme-context" id="country-theme-context">'
        '<span class="country-theme-context__label">TRAVEL THEMES</span>'
        '<div class="country-theme-context__list" id="country-theme-list">'
        + ''.join(f'<span class="country-theme-chip">{esc(label)}</span>'
                  for label in region_theme_labels(parent))
        + '</div></div></div></section>')
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
        f'role="group" aria-label="{esc(data["nameJa"])}の景色の地図">'
        f'<img class="map-base" src="{esc(data["map"]["svg"])}?v={map_version}" '
        f'alt="{esc(data["nameJa"])}の実海岸線と島々を描いた地図" '
        'loading="lazy" decoding="async">'
        '<div class="region-map-hits" id="region-map-hits">'
        + ''.join(
            '<button type="button" class="region-map-hit map-marker" '
            f'data-scene="{esc(scene["id"])}" '
            f'style="left:{interactive_map_position(scene["coordinates"], index, map_svg_text, data["map"]["bounds"])[0]:.5f}%;'
            f'top:{interactive_map_position(scene["coordinates"], index, map_svg_text, data["map"]["bounds"])[1]:.5f}%" '
            f'aria-label="{index} {esc(scene["name"])}を選択" aria-pressed="false">'
            f'<b aria-hidden="true">{index}</b></button>'
            for index, scene in enumerate(data['scenes'], 1)
        )
        + '</div>'
        + f'<div class="map-hero-marker region-map-hero" aria-hidden="true" '
          f'style="left:{region_hero_map_position(hero["coordinates"], map_svg_text, data["map"]["bounds"])[0]:.5f}%;'
          f'top:{region_hero_map_position(hero["coordinates"], map_svg_text, data["map"]["bounds"])[1]:.5f}%"><span></span></div>'
        + '</div></div>'
        '<div class="map-legend map-legend--below" aria-label="地図記号の説明">'
        '<span><i class="map-legend__scene" aria-hidden="true">1</i>景色の番号</span>'
        '<span><i class="map-legend__hero" aria-hidden="true"></i>Heroの場所</span></div>'
        + ('<button type="button" id="region-map-zoom-toggle" class="region-map-zoom-toggle" '
           'aria-expanded="false" aria-controls="country-map-art">地図を拡大して地点を確認</button>'
           '<p class="region-map-zoom-help" hidden>地図を左右にスクロールして地点を確認できます。</p>'
           if slug == 'northern-ireland' else '')
        + '<div class="encounter-strip"><span class="section-kicker-en">ENCOUNTERS</span>'
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
               if item.get('points') else '')
            + '</article>')
    result.append('</div></section>')

    result.append('<section class="taste-section" aria-labelledby="region-taste-title">'
        f'<div class="taste-section__head"><div><span class="section-kicker-en">TASTE OF {esc(data["nameEn"])}</span>'
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
            f'<p>{esc(data.get("nextRoutesIntro", "ほかの構成国へ続く代表的な周遊の方向。移動手段と運航状況は出発前に確認を。"))}</p>'
            '</div><div class="next-routes__grid">')
        for route in data['nextRoutes']:
            result.append('<article class="next-route-card"><div class="next-route-card__country">'
                f'<span class="next-route-card__flag" aria-hidden="true">{esc(route.get("flag", ""))}</span><div>'
                f'<strong>{esc(route["countryEn"])}</strong>'
                f'<small>{esc(route["countryJa"])}</small></div></div>'
                f'<p class="next-route-card__path">{esc(route["path"])}</p>'
                f'<p class="next-route-card__description">{esc(route["description"])}</p></article>')
        result.append('</div></section>')

    # Match the shared Country journey footer: recommendations and wish side by side.
    related = data.get('relatedCountries') or []
    result.append('<section class="journey-footer region-journey-footer" aria-labelledby="region-related-title">')
    if related:
        result.append('<div class="related-wrap region-related">'
            '<span class="section-kicker-en">NEXT DESTINATIONS</span>'
            f'<h2 id="region-related-title">{esc(data["nameJa"])}が気になったら</h2>'
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

    # Two quiet paths: parent Country and next constituent Region.
    # An unpublished/missing Region is explicitly unavailable, never a dead link.
    result.append('<nav class="region-return" aria-label="イギリスの地域ナビゲーション">'
        f'<a href="countries/{esc(parent)}/" class="region-return__link">'
        '<span class="region-return__arrow" aria-hidden="true">←</span>'
        '<span class="region-return__copy"><small>BACK TO UNITED KINGDOM</small>'
        '<strong>イギリスに戻る</strong>'
        '<span>4つの構成国と8つの景色を見る</span></span>'
        '</a>')
    next_region = data.get('nextRegion')
    if next_region:
        next_slug = next_region.get('slug', '')
        if not re.fullmatch(r'[a-z0-9-]+', next_slug) or next_slug == slug:
            raise ValueError('Invalid next Region slug')
        next_path = DATA_ROOT / parent / f'{next_slug}.json'
        next_published = False
        if next_path.is_file():
            next_data = json.loads(next_path.read_text(encoding='utf-8'))
            next_published = (
                next_data.get('regionPublished') is True
                and next_data.get('parentSlug') == parent
                and next_data.get('slug') == next_slug
            )
        next_name = esc(next_region['nameJa'])
        if next_published:
            result.append(
                f'<a class="region-return__link region-return__link--next" '
                f'href="countries/{esc(parent)}/{esc(next_slug)}/">'
                '<span class="region-return__copy"><small>NEXT REGION</small>'
                f'<strong>{next_name}へ</strong>'
                '<span>次の地域の景色を見る</span></span>'
                '<span class="region-return__arrow" aria-hidden="true">→</span></a>'
            )
        else:
            result.append(
                '<div class="region-return__link region-return__link--pending" '
                f'aria-label="次の地域：{next_name}。詳細ページは準備中">'
                '<span class="region-return__copy"><small>NEXT REGION</small>'
                f'<strong>{next_name}</strong>'
                '<span>詳細ページは準備中</span></span>'
                '<span class="region-return__pending" aria-hidden="true">COMING SOON</span>'
                '</div>'
            )
    result.append('</nav>')
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
