#!/usr/bin/env python3
"""Temporary, single-country repair script; removed before merge."""
import json
from pathlib import Path

p = Path('data/countries/belize.json')
d = json.loads(p.read_text(encoding='utf-8'))
assert d['slug'] == 'belize' and d['map']['svg'] == 'assets/images/belize/map-atlas-v1.svg'
assert len(d['scenes']) == 8 and len(d['taste']['items']) == 4
assert d['facts'][3]['label'] == '面積'
assert d['signatureFacts'][0]['topicKey'] == 'great-blue-hole-diameter'
assert d['atlasExtras'][0]['topicKey'] == 'protected-reef-network'
d['map']['japanAreaComparison'] = '国土面積は日本の約6.1%（ベリーズ約22,970 km²）'
d['facts'][3]['value'] = '約22,970 km²（日本の約6.1%）'
d['signatureFacts'][0] = {
    'topicKey': 'belize-reef-world-scale',
    'label': 'サンゴ礁システム',
    'value': '世界で2番目の規模',
    'note': '沿岸と沖合に広がるサンゴ礁システム。北半球最大のバリアリーフを含む。',
    'icon': 'sea',
    'interestReason': 'ブルー・ホールを一つの景色ではなく、広大なサンゴ礁と海岸生態系の一部として捉えるための尺度。',
}
d['atlasExtras'][0]['title'] = '世界で2番目の規模をもつサンゴ礁システム'
d['atlasExtras'][0]['text'] = ('ベリーズ沿岸のサンゴ礁システムは世界で2番目の規模で、北半球最大のバリアリーフを含む。'
    '一方、世界遺産「ベリーズ・バリア・リーフ保護区」は珊瑚礁全体ではなく、沿岸と沖合の7つの保護区域から成る。')
d['atlasExtras'][0]['points'] = [
    '保護区の7区域は、サンゴ礁システム全体の約12%に当たる',
    'ライトハウス・リーフのブルー・ホールも世界遺産の構成資産の一つである',
]
d['sourceDates']['japanArea'] = '2026-04-01'
d['sources']['japanArea'] = ('国土地理院「令和8年全国都道府県市区町村別面積調」2026年4月1日時点、'
    '日本の国土面積377,974.87 km²。ベリーズ22,970 km² ÷ 377,974.87 km² = 約6.1%。'
    ' https://web1.gsi.go.jp/KOKUJYOHO/MENCHO-title.htm')
d['sources']['reef'] = ('UNESCO World Heritage Centre, Belize Barrier Reef Reserve System: '
    'world second-largest reef system, largest barrier reef in the Northern Hemisphere; '
    'seven protected areas cover 12% of the reef complex. https://whc.unesco.org/en/list/764')
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

js_path = Path('assets/js/app.js')
js = js_path.read_text(encoding='utf-8')
map_anchor = '  mapArt.prepend(image);\n  if (typeof mapData.insetNote === "string"'
assert js.count(map_anchor) == 1
js = js.replace(map_anchor, '''  mapArt.prepend(image);
  if (typeof mapData.japanAreaComparison === 'string' && mapData.japanAreaComparison.trim()) {
    const legend = fragment.querySelector('.map-legend--below');
    if (legend) {
      const comparison = document.createElement('span');
      comparison.className = 'map-legend__area-comparison';
      comparison.textContent = mapData.japanAreaComparison;
      legend.prepend(comparison);
    }
  }
  if (typeof mapData.insetNote === "string"''')
taste_anchor = "    const image = article.querySelector('.taste-card__img');\n    image.addEventListener('error',"
assert js.count(taste_anchor) == 1
js = js.replace(taste_anchor, '''    const image = article.querySelector('.taste-card__img');
    image.addEventListener('load', () => {
      // Match approved 4:3 artwork with integral paper ground to its own frame.
      if (image.naturalWidth > 0 && image.naturalHeight > 0 &&
          Math.abs(image.naturalWidth / image.naturalHeight - 4 / 3) < 0.005) {
        const frame = article.querySelector('.taste-card__image');
        frame.classList.add('taste-card__image--source-4x3');
        image.classList.add('taste-card__img--source-4x3');
      }
    }, { once: true });
    image.addEventListener('error',''')
assert "image.addEventListener('error', () =>" in js
js_path.write_text(js, encoding='utf-8')

css_path = Path('assets/css/taste-image-framing.css')
css = css_path.read_text(encoding='utf-8')
assert '.taste-card__image--source-4x3' not in css
css += '''\n/* Shared 4:3 Taste framing: use the artwork's own complete paper ground. */
.taste-card__image--source-4x3 {
  aspect-ratio: 4 / 3;
  background: transparent;
}
.taste-card__img--source-4x3 {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}
'''
css_path.write_text(css, encoding='utf-8')

map_css_path = Path('assets/css/site-unify.css')
map_css = map_css_path.read_text(encoding='utf-8')
assert '.map-legend__area-comparison' not in map_css
map_css += '''\n/* Shared factual area comparison under the standard country map. */
.map-legend--below .map-legend__area-comparison {
  flex: 0 0 100%;
  white-space: normal;
  color: #31576a;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.5;
}
'''
map_css_path.write_text(map_css, encoding='utf-8')

print('Belize content, map comparison and shared image frame patched; publication unchanged.')
