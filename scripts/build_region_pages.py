#!/usr/bin/env python3
"""Build reviewable Region pages beneath canonical Country routes.

Region pages are editorial extensions, not new atlas destinations. A Region
is indexable/discoverable only when its editorial regionPublished flag is true.
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
    priority = ' fetchpriority="high"' if eager else ''
    return f'<img src="{approved_image(path, version)}" alt="{esc(alt)}" loading="{loading}" decoding="async"{priority}>'


def render_region(data: dict, *, site_url: str, version: str) -> tuple[str, str, bool]:
    parent = data['parentSlug']
    slug = data['slug']
    if not re.fullmatch(r'[a-z0-9-]+', parent) or not re.fullmatch(r'[a-z0-9-]+', slug):
        raise ValueError('Unsafe region/parent slug')
    if parent != 'unitedkingdom':
        raise ValueError('The current Region pilot must stay under the United Kingdom')
    if data['schemaVersion'] != 1 or len(data['scenes']) != 8 or len(data['taste']['items']) != 4:
        raise ValueError('Region requires schemaVersion=1, exactly 8 Scenes and 4 Taste')
    if len({s['id'] for s in data['scenes']}) != 8:
        raise ValueError('Duplicate Scene identifiers')
    for item in [data['hero'], *data['scenes']]:
        p = item['coordinates']
        if not (-90 <= p['latitude'] <= 90 and -180 <= p['longitude'] <= 180):
            raise ValueError(f'Invalid coordinates: {item}')
    for item in [data['hero'], *data['scenes'], *data['taste']['items']]:
        approved_image(item['image'], version)
    if not (ROOT / data['map']['svg']).is_file():
        raise FileNotFoundError(data['map']['svg'])

    title = f"{data['nameJa']} | {data['nameEn']} — JOURNEY ATLAS"
    canonical = urljoin(site_url, f'countries/{parent}/{slug}/')
    published = data.get('regionPublished') is True
    hero = data['hero']
    segments: list[str] = []
    segments.append('<div class="region-wrap"><nav class="region-crumb" aria-label="パンくずリスト">'
                    f'<a href="./">JOURNEY ATLAS</a> <span aria-hidden="true">/</span> '
                    f'<a href="countries/{esc(parent)}/">{esc(data["parentNameJa"])}</a> '
                    f'<span aria-hidden="true">/</span> <span aria-current="page">{esc(data["nameJa"])}</span></nav></div>')
    segments.append('<section aria-label="この地域の代表景観" class="region-cover">'
                    + render_image(hero['image'], f"{hero['name']} — {hero['location']}を描いた景観イメージ", version, eager=True)
                    + '<p class="region-cover__caption region-wrap">表紙の景観イメージ：'
                    + esc(hero['name']) + ' / ' + esc(hero['location'])
                    + '（実在する場所を題材に制作したイラストであり、現地写真ではありません）</p></section>')
    segments.append(f'<div class="region-wrap"><section class="region-intro" aria-labelledby="region-title">'
                    f'<span class="region-kicker">UNITED KINGDOM / CONSTITUENT COUNTRY</span>'
                    f'<h1 id="region-title">{esc(data["nameEn"])}</h1>'
                    f'<p class="region-intro__ja">{esc(data["nameJa"])}</p>'
                    f'<p class="region-intro__lead">{esc(hero["lead"])}</p></section>')
    segments.append('<dl class="region-facts">' + ''.join(
        f'<div><dt>{esc(item["label"])}</dt><dd>{esc(item["value"])}</dd></div>'
        for item in data['profile']) + '</dl>')
    segments.append('<section class="region-section" aria-labelledby="region-scenery-title">'
                    '<div class="region-section__head"><span class="region-kicker">TRAVEL MAP / SCENERY</span>'
                    '<h2 id="region-scenery-title">この地域で見たい8つの景色</h2>'
                    '<p class="region-section__intro">地図の番号と8景が対応しています。実在する場所を題材にした景観イメージです。</p></div>'
                    '<div class="region-scenery-grid"><div><div class="region-map">'
                    f'<img src="{esc(data["map"]["svg"])}" alt="スコットランド周辺の実際の海岸線と、8つの景色およびHeroの地点を示す地図" '
                    'loading="lazy" decoding="async"></div>'
                    '<p class="region-map-note">GSHHSの実海岸線に基づく地図。構成国境界は推測して描画していません。番号は景色、菱形はHeroの場所。</p></div>')
    card_fragments=[]
    for i,s in enumerate(data['scenes'],1):
        card_fragments.append('<article class="region-scene"><figure class="region-scene__figure">'
                     + render_image(s['image'], f'{s["name"]}を題材に制作した景観イメージ', version)
                     + f'<figcaption class="region-scene__index">{i:02d}</figcaption></figure>'
                     + f'<h3>{esc(s["name"])}</h3><p class="region-scene__local">{esc(s["nameLocal"])}</p>'
                     + f'<p>{esc(s["description"])}</p></article>')
    segments.append('<div class="region-scenes">'+''.join(card_fragments)+'</div></div></section>')
    segments.append('<section class="region-section" aria-labelledby="region-depth-title">'
                    '<div class="region-section__head"><span class="region-kicker">BEYOND THE SCENERY</span>'
                    '<h2 id="region-depth-title">景色の向こうへ</h2></div><div class="region-depth-grid">'
                    + ''.join(f'<article class="region-depth-card"><h3>{esc(s["title"])}</h3><p>{esc(s["text"])}</p></article>' for s in data['culture']) + '</div></section>')
    segments.append('<section class="region-section" aria-labelledby="region-taste-title">'
                    '<div class="region-section__head"><span class="region-kicker">TASTE OF SCOTLAND</span>'
                    f'<h2 id="region-taste-title">{esc(data["taste"]["title"])}</h2></div><div class="region-taste-grid">')
    for item in data['taste']['items']:
        segments.append('<article class="region-taste">'+render_image(item['image'], f'{item["name"]}の料理イメージ', version)
                +f'<h3>{esc(item["name"])}</h3><p class="region-taste__local">{esc(item["nameLocal"])}</p><p>{esc(item["text"])}</p></article>')
    segments.append('</div></section>')
    segments.append('<section class="region-section" aria-labelledby="region-planning-title">'
                    '<div class="region-section__head"><span class="region-kicker">TRAVEL NOTES</span>'
                    '<h2 id="region-planning-title">旅を考えるなら</h2></div><div class="region-info-grid">')
    for subtitle,items,title_key,text_key in (
        ('こんな人に',data['forWhom'],'title','text'),
        ('季節',data['seasons'],'label','text'),
        ('知っておきたいこと',data['notes'],'title','text'),
    ):
        segments.append('<section><h3>'+esc(subtitle)+'</h3>'
          +''.join(f'<p><strong>{esc(item[title_key])}</strong> — {esc(item[text_key])}</p>' for item in items)+'</section>')
    segments.append('</div></section>')
    segments.append('<div class="region-back"><div><p class="region-back__label">BACK TO COUNTRY</p>'
                    '<p>イギリス全体の8景や地図も見てみる</p></div>'
                    f'<a href="countries/{esc(parent)}/">UNITED KINGDOM に戻る</a></div>')
    segments.append('<details class="region-sources"><summary>DATA SOURCES / 参考資料</summary><ul>'
                    + ''.join(f'<li><a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(key)}</a></li>' for key,url in data['sources'].items())
                    + '</ul></details></div>')
    page = TEMPLATE.read_text(encoding='utf-8')
    repl = {'{{ROBOTS}}':'index,follow' if published else 'noindex,follow',
            '{{DESCRIPTION}}':esc(data['seo']['description']),
            '{{CANONICAL}}':esc(canonical),
            '{{TITLE}}':esc(title),
            '{{OG_IMAGE}}':esc(urljoin(site_url, f'{hero["image"]}?v={version}')),
            '{{BUILD_VERSION}}':esc(version),
            '{{CONTENT}}':'\n'.join(segments)}
    for field,value in repl.items():
        if field not in page:
            raise ValueError(f'Region HTML template field missing: {field}')
        page = page.replace(field, value)
    if '{{' in page or '}}' in page:
        raise ValueError('Unreplaced template tokens')
    return page, canonical, published


def generate_region_pages(*, site_url: str, version: str, parents: set[str] | None = None) -> list[str]:
    published_urls=[]
    for path in sorted(DATA_ROOT.glob('*/*.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        if parents is not None and data['parentSlug'] not in parents:
            continue
        page,canonical,published=render_region(data,site_url=site_url,version=version)
        output=ROOT/'countries'/data['parentSlug']/data['slug']/'index.html'
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(page,encoding='utf-8')
        if published: published_urls.append(canonical)
    return published_urls


if __name__=='__main__':
    for url in generate_region_pages(site_url='https://atlas.yagenji.com/',version='local'):
        print('Published:',url)
    print('Built reviewable region pages')
