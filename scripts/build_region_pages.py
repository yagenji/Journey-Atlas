#!/usr/bin/env python3
"""Build canonical sub-Country pages with the shared JOURNEY ATLAS Country layout.

Region data and approved image assets stay independent of the 202-destination
registry. Region pages remain noindex and undiscoverable until published.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / 'data' / 'regions'
TEMPLATE = ROOT / 'region.html'


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
    result.append('<aside class="hero-caption" aria-label="表紙の景色">'
        '<div class="hero-caption__inner page-shell">'
        '<p class="hero-caption__label">表紙の景観イメージ</p>'
        '<div class="hero-caption__body">'
        f'<p class="hero-caption__name">{esc(hero["name"])}</p>'
        f'<p class="hero-caption__local">{esc(hero["location"])}</p>'
        '<p class="hero-caption__text">実在する場所を題材に制作したイラストであり、現地写真ではありません。</p>'
        '</div></div></aside>')
    result.append('<div class="atlas-body page-shell">'
        '<nav class="region-breadcrumb" aria-label="パンくずリスト">'
        '<a href="./">JOURNEY ATLAS</a><span aria-hidden="true">/</span>'
        f'<a href="countries/{esc(parent)}/">{esc(data["parentNameJa"])}</a>'
        '<span aria-hidden="true">/</span>'
        f'<span aria-current="page">{esc(data["nameJa"])}</span></nav>')

    facts_icons = ['globe', 'landmark', 'language', 'coin']
    facts = ''.join('<div>' + icon(facts_icons[i] if i < len(facts_icons) else 'info')
        + f'<dt>{esc(item["label"])}</dt><dd>{esc(item["value"])}</dd></div>'
        for i, item in enumerate(data['profile']))
    result.append('<section class="country-facts-strip" aria-labelledby="region-facts-title">'
        '<div class="country-facts-strip__head"><span class="section-kicker-en">REGION PROFILE</span>'
        '<h2 id="region-facts-title">基本情報</h2></div>'
        f'<dl class="fact-list">{facts}</dl></section>')

    # Standard Country map-left / eight-Scene-right panel and card formatting.
    result.append('<section class="atlas-panel" aria-labelledby="region-scenery-title">'
        '<div class="map-column"><div class="panel-title-wrap"><div class="panel-title-copy">'
        '<span class="section-kicker-en">TRAVEL MAP</span>'
        '<h2 class="panel-title">旅の地図</h2></div></div>'
        '<div class="map-frame"><div class="map-art has-map" id="country-map-art" '
        'role="group" aria-label="スコットランドの景色の地図">'
        f'<img class="map-base" src="{esc(data["map"]["svg"])}" '
        'alt="実在する海岸線と景色8地点、Hero地点を示すスコットランドの地図" '
        'loading="lazy" decoding="async"></div></div>'
        '<div class="map-legend map-legend--below" aria-label="地図記号の説明">'
        '<span><i class="map-legend__scene" aria-hidden="true">1</i>景色の番号</span>'
        '<span><i class="map-legend__hero" aria-hidden="true"></i>Heroの場所</span></div>'
        '<p class="region-map-note">GSHHSの実海岸線に基づく地図。構成国境界は推測して描画していません。</p>'
        '</div><div class="scenes-column">'
        '<div class="scenes-heading"><div class="scenes-title-wrap">'
        '<span class="section-kicker-en">SCENERY</span>'
        '<h2 id="region-scenery-title">この地域で見たい景色 <b>8</b>選</h2>'
        '</div><p class="scenes-intro">実在する場所を題材に制作した景観イメージです。現地写真ではありません。</p></div>'
        '<div class="scene-grid">')
    for i, scene in enumerate(data['scenes'], 1):
        number = str(i)
        result.append('<article class="scene-card region-scene">'
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
        '<p class="atlas-extras__intro">景色だけでは見えない、この地域の歴史や文化をたどる。</p></div>'
        '<div class="atlas-extras__grid">')
    for item in data['culture']:
        result.append('<article class="atlas-extra"><span class="atlas-extra__theme">CULTURE / 文化</span>'
            f'<h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></article>')
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
        '<div class="travel-planning__content"><section class="travel-planning__block travel-planning__block--season" '
        'aria-labelledby="region-season-title"><span class="travel-planning__label">SEASON</span>'
        '<h3 id="region-season-title">季節</h3><div class="season-list">')
    for i, item in enumerate(data['seasons']):
        result.append(f'<article>{icon(["sun", "leaf", "snow"][i % 3])}'
            f'<div><b>{esc(item["label"])}</b><p>{esc(item["text"])}</p></div></article>')
    result.append('</div></section></div></section>')

    result.append('<div class="region-back"><div><p class="region-back__label">BACK TO COUNTRY</p>'
        '<p>イギリス全体の8景や地図も見てみる</p></div>'
        f'<a href="countries/{esc(parent)}/">UNITED KINGDOM に戻る</a></div>')
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
        '{{BUILD_VERSION}}': esc(version),
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