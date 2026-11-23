/* JOURNEY ATLAS — private travel record and scenery favorites.
   Uses existing Country JSON and browser-local preferences; no external account. */
(() => {
  'use strict';
  const SCENE_PREFIX = 'journey-atlas:scene:';
  const REGION_WISH_PREFIX = 'journey-atlas:region-wish:';
  const REGION_VISITED_PREFIX = 'journey-atlas:region-visited:';
  const VISITED_PREFIX = 'journey-atlas:visited:';
  const WISH_PREFIX = 'journey-atlas:wish:';
  // Optional year of the first visit: key = Country slug, or parent:slug for a detail Region.
  const VISIT_YEAR_PREFIX = 'journey-atlas:visited-year:';
  const validYear = value => /^\d{4}$/.test(String(value)) && +value >= 1900 && +value <= new Date().getFullYear();
  const REGISTRY_PATH = 'data/atlas-destinations.json';
  const ORIGINS_PATH = 'data/scene-origins.json';
  const validId = value => typeof value === 'string' && /^[a-z0-9-]+$/.test(value);
  const allStoredKeys = () => {
    try { return Array.from({length: localStorage.length}, (_, i) => localStorage.key(i)).filter(Boolean); }
    catch { return []; }
  };
  const getStored = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const putStored = (key, value) => {
    try { localStorage.setItem(key, value); return true; } catch { return false; }
  };
  const removeStored = key => { try { localStorage.removeItem(key); return true; } catch { return false; } };
  const make = (tag, className, content) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content !== undefined) element.textContent = content;
    return element;
  };
  const linkTo = (href, label, className) => {
    const a = make('a', className, label);
    a.href = href;
    return a;
  };
  const sceneKey = (slug, id) => SCENE_PREFIX + slug + ':' + id;
  const countryHref = slug => 'countries/' + encodeURIComponent(slug) + '/';
  const regionCountryHref = (parent, slug) => `countries/${parent}/${slug}/`;
  const regionSceneHref = (parent, slug, id) => regionCountryHref(parent, slug) + (id === 'hero' ? '#hero-caption' : '#scene-' + id);
  const isRegionFavorite = f => f?.kind === 'region' && validId(f.slug) && validId(f.parentSlug)
    && validId(f.id) && f.href === regionSceneHref(f.parentSlug, f.slug, f.id);
  const getRegionWishes = () => allStoredKeys().filter(key => key.startsWith(REGION_WISH_PREFIX)).map(key => {
    try {
      const item = JSON.parse(getStored(key));
      return item && validId(item.parentSlug) && validId(item.slug)
        && typeof item.nameJa === 'string'
        && key === REGION_WISH_PREFIX + item.parentSlug + ':' + item.slug
        && item.href === regionCountryHref(item.parentSlug, item.slug) ? item : null;
    } catch { return null; }
  }).filter(Boolean);
  // UK constituent Regions share the same personal-atlas detail-area contract.
  const getRegionVisits = () => allStoredKeys().filter(key => key.startsWith(REGION_VISITED_PREFIX)).map(key => {
    try {
      const item = JSON.parse(getStored(key));
      return item && validId(item.parentSlug) && validId(item.slug)
        && typeof item.nameJa === 'string'
        && key === REGION_VISITED_PREFIX + item.parentSlug + ':' + item.slug
        && item.href === regionCountryHref(item.parentSlug, item.slug) ? item : null;
    } catch { return null; }
  }).filter(Boolean);
  const fetchJSON = url => fetch(url).then(response => {
    if (!response.ok) throw Error('HTTP ' + response.status);
    return response.json();
  });
  const getFavorites = () => allStoredKeys().filter(key => key.startsWith(SCENE_PREFIX))
    .map(key => {
      try {
        const item = JSON.parse(getStored(key));
        if (!item || !validId(item.slug) || !validId(item.id) || key !== sceneKey(item.slug, item.id)) return null;
        return item;
      } catch { return null; }
    }).filter(Boolean);
  const updateSceneSaveButton = (button, stored, name) => {
    button.classList.toggle('is-saved', stored);
    button.setAttribute('aria-pressed', String(stored));
    button.textContent = stored ? '♥' : '♡';
    const label = stored ? name + 'をお気に入りから外す' : name + 'をお気に入りに保存する';
    button.setAttribute('aria-label', label);
    button.title = label;
  };
  // 景色のリンク共有: the phone's share sheet where available, otherwise copy the link.
  // Country pages accept #scene-{id} (same form as Region pages) and #hero-caption.
  const SHARE_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M10 14a4.5 4.5 0 0 0 6.4 0l3.2-3.2a4.5 4.5 0 0 0-6.4-6.4L11.6 6"/><path d="M14 10a4.5 4.5 0 0 0-6.4 0l-3.2 3.2a4.5 4.5 0 0 0 6.4 6.4l1.6-1.6"/></svg>';
  function makeShareButton(className, sceneName, country, fragmentId, status) {
    const button = make('button', 'ja-scene-share ' + className);
    button.type = 'button';
    const label = sceneName + 'へのリンクを共有';
    button.setAttribute('aria-label', label);
    button.title = 'リンクを共有';
    button.innerHTML = SHARE_ICON;
    let resetTimer = 0;
    button.addEventListener('click', async event => {
      event.stopPropagation();
      const url = location.origin + location.pathname + '#' + fragmentId;
      const title = sceneName + '｜' + country.nameJa + '｜JOURNEY ATLAS';
      if (navigator.share) {
        try { await navigator.share({ title, url }); } catch { /* closed by the visitor */ }
        return;
      }
      let ok = false;
      try { await navigator.clipboard.writeText(url); ok = true; } catch { ok = false; }
      status.textContent = ok ? 'リンクをコピーしました。' : 'リンクをコピーできませんでした。';
      button.classList.toggle('is-copied', ok);
      button.title = ok ? 'リンクをコピーしました' : 'リンクを共有';
      window.clearTimeout(resetTimer);
      resetTimer = window.setTimeout(() => { button.classList.remove('is-copied'); button.title = 'リンクを共有'; }, 2200);
    });
    button.addEventListener('keydown', event => event.stopPropagation());
    return button;
  }
  function mountCountry(country) {
    if (!country || !validId(country.slug) || document.querySelector('[data-ja-scene-save]')) return;
    const status = make('p', 'ja-scene-status');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    document.querySelector('#scene-cards')?.after(status);
    (country.scenes || []).forEach(scene => {
      if (!validId(scene.id)) return;
      const card = Array.from(document.querySelectorAll('.scene-card')).find(e => e.dataset.scene === scene.id);
      if (!card) return;
      const key = sceneKey(country.slug, scene.id);
      const button = make('button', 'ja-scene-save');
      button.type = 'button';
      button.dataset.jaSceneSave = scene.id;
      const saved = () => getStored(key) !== null;
      updateSceneSaveButton(button, saved(), scene.name);
      button.addEventListener('click', event => {
        event.stopPropagation();
        const existing = saved();
        const value = JSON.stringify({
          slug: country.slug, id: scene.id, name: scene.name,
          countryName: country.nameJa, image: scene.image,
          ...(validId(country.regionParent) ? {
            kind: 'region', parentSlug: country.regionParent,
            href: regionSceneHref(country.regionParent, country.slug, scene.id)
          } : {})
        });
        const ok = existing ? removeStored(key) : putStored(key, value);
        if (ok) updateSceneSaveButton(button, !existing, scene.name);
        status.textContent = ok ? (existing ? '景色の保存を解除しました。' : 'お気に入りの景色に保存しました。') : 'このブラウザには保存できませんでした。';
      });
      button.addEventListener('keydown', event => event.stopPropagation());
      card.append(button, makeShareButton('ja-scene-share--card', scene.name, country, 'scene-' + scene.id, status));
    });

    // The Hero belongs to the same saved-scenery collection, but its heart lives
    // next to the caption text rather than on top of the artwork.
    const heroName = country.hero?.name || country.hero?.location || country.nameJa + 'の代表風景';
    const heroTitle = document.querySelector('.hero-caption__name');
    if (heroTitle && typeof country.hero?.image === 'string') {
      const key = sceneKey(country.slug, 'hero');
      const button = make('button', 'ja-hero-save');
      button.type = 'button';
      button.dataset.jaHeroSave = 'hero';
      const saved = () => getStored(key) !== null;
      updateSceneSaveButton(button, saved(), heroName);
      const row = make('div', 'ja-hero-favorite-row');
      heroTitle.replaceWith(row);
      row.append(heroTitle, button, makeShareButton('ja-scene-share--hero', heroName, country, 'hero-caption', status));
      button.addEventListener('click', () => {
        const existing = saved();
        const value = JSON.stringify({
          slug: country.slug, id: 'hero', name: heroName,
          countryName: country.nameJa, image: country.hero.image,
          ...(validId(country.regionParent) ? {
            kind: 'region', parentSlug: country.regionParent,
            href: regionSceneHref(country.regionParent, country.slug, 'hero')
          } : {})
        });
        const ok = existing ? removeStored(key) : putStored(key, value);
        if (ok) updateSceneSaveButton(button, !existing, heroName);
        status.textContent = ok
          ? (existing ? '表紙の景色の保存を解除しました。' : '表紙の景色をお気に入りに保存しました。')
          : 'このブラウザには保存できませんでした。';
      });
    }

    fetchJSON(ORIGINS_PATH).then(data => {
      const entries = data.countries?.[country.slug];
      if (!entries) return;
      (country.scenes || []).forEach(scene => {
        const fact = entries[scene.id];
        if (!fact?.text || !/^https:\/\//.test(fact.source)) return;
        const card = Array.from(document.querySelectorAll('.scene-card')).find(e => e.dataset.scene === scene.id);
        if (!card) return;
        const details = make('details', 'ja-scene-origin');
        const summary = make('summary', '', 'この景色が生まれた理由');
        const paragraph = make('p', '', fact.text);
        const cite = linkTo(fact.source, '出典：' + fact.publisher + '（確認 ' + data.verifiedAt + '）', 'ja-origin-source');
        cite.target = '_blank';
        cite.rel = 'noopener noreferrer';
        // Links in a closed <details> are not keyboard focusable; keep the
        // citation out of the DOM until the explanation is actually expanded.
        details.append(summary, paragraph);
        details.addEventListener('toggle', () => {
          if (details.open) details.append(cite);
          else cite.remove();
        });
        details.addEventListener('click', event => event.stopPropagation());
        details.addEventListener('keydown', event => event.stopPropagation());
        card.querySelector('.scene-copy > div')?.append(details);
      });
    }).catch(() => { /* Only sourced landscape explanations are shown. */ });
  }
  window.addEventListener('journeyatlas:countryready', event => mountCountry(event.detail));
  if (window.journeyAtlasCurrentCountry) mountCountry(window.journeyAtlasCurrentCountry);

  const host = document.querySelector('#atlas-personal-home');
  if (!host) return;
  const disclosure = document.querySelector('#my-atlas');
  disclosure?.addEventListener('toggle', () => { if (disclosure.open) loadCenterMap(); });
  const openAtlas = () => { if (disclosure) disclosure.open = true; };
  if (window.location.hash === '#my-atlas') openAtlas();
  document.querySelectorAll('a[href="#my-atlas"]').forEach(link => link.addEventListener('click', openAtlas));
  window.addEventListener('hashchange', () => {
    if (window.location.hash === '#my-atlas') openAtlas();
  });
  const mine = make('section', 'ja-panel ja-mine');
  host.append(mine);
  let registry = [];
  let publishedRegionCount = null;
  // The published Region index is the source of truth for the detail denominator.
  // Keep the subtotals visible even if this optional request fails.
  const regionsReady = window.JourneyAtlasRegionsPromise ||
    fetchJSON('data/top-scene-index.json').then(data => data.regionHeroes || []);
  regionsReady.then(regions => {
    if (Array.isArray(regions) && regions.length) {
      publishedRegionCount = regions.length;
      renderMine();
    }
  }).catch(() => {});
  const summary = make('div', 'ja-mine-summary');
  const groups = make('div', 'ja-mine-groups');
  // 行った旅先・行きたい旅先 repeat the map's list, so they stay folded until asked for.
  const groupsBox = make('details', 'ja-timeline ja-mine-list');
  const groupsSummary = make('summary', 'ja-timeline__title', '行った旅先・行きたい旅先');
  const groupsCount = make('span', 'ja-timeline__count');
  groupsSummary.append(groupsCount);
  groupsBox.append(groupsSummary, groups);
  const tools = make('div', 'ja-backup-tools');
  let regionNames = [];
  const feedback = make('p', 'ja-subtitle');
  feedback.setAttribute('role', 'status');
  // 章ごとの記録: visited Countries counted per atlas chapter (region → subregion), the same
  // chapters the Country pages turn through. Only the 200 Country pages count.
  const chaptersBox = make('section', 'ja-chapters');
  chaptersBox.setAttribute('aria-labelledby', 'ja-chapters-title');
  let atlasChapters = [];
  let chaptersDetailOpen = false;
  window.JourneyAtlasOrder?.load().then(({chapters}) => { atlasChapters = chapters; renderMine(); }).catch(() => {});
  function renderChapters() {
    chaptersBox.replaceChildren();
    if (!atlasChapters.length) { chaptersBox.hidden = true; return; }
    chaptersBox.hidden = false;
    const title = make('h3', 'ja-chapters__title', '章ごとの記録');
    title.id = 'ja-chapters-title';
    chaptersBox.append(title, make('p', 'ja-chapters__note', '図鑑の章ごとに、行った国・地域の数です。'));
    const regions = [];
    atlasChapters.forEach(chapter => {
      let block = regions.find(item => item.label === chapter.region);
      if (!block) { block = {label: chapter.region, chapters: []}; regions.push(block); }
      block.chapters.push(chapter);
    });
    // The seven regions at a glance, then the chapters in detail below.
    const board = make('ul', 'ja-regions-board');
    board.setAttribute('aria-label', '地域ごとの割合');
    regions.forEach(region => {
      const total = region.chapters.reduce((sum, chapter) => sum + chapter.pages.length, 0);
      const done = region.chapters.reduce((sum, chapter) => sum + chapter.pages.filter(visited).length, 0);
      const rate = total ? Math.round(done / total * 100) : 0;
      const tile = make('li', 'ja-region-tile' + (done ? '' : ' is-empty') + (total && done === total ? ' is-complete' : ''));
      const bar = make('span', 'ja-region-tile__bar');
      bar.setAttribute('aria-hidden', 'true');
      const fill = make('span', '');
      fill.style.width = rate + '%';
      bar.append(fill);
      tile.append(
        make('span', 'ja-region-tile__label', region.label),
        make('strong', 'ja-region-tile__rate', rate + '%'),
        make('span', 'ja-region-tile__count', done + ' / ' + total + (total && done === total ? ' ✓' : '')),
        bar
      );
      board.append(tile);
    });
    // The chapter detail is long: folded by default, opened only when wanted.
    const detail = make('details', 'ja-chapters__detail');
    detail.open = chaptersDetailOpen;
    detail.addEventListener('toggle', () => { chaptersDetailOpen = detail.open; });
    detail.append(make('summary', 'ja-chapters__detail-title', '章ごとの内訳'));
    chaptersBox.append(board, detail);
    regions.forEach(region => {
      const group = make('div', 'ja-chapters__region');
      // Region totals are on the board above; the detail heading only names the region.
      const head = make('h4', 'ja-chapters__region-title');
      head.append(make('span', '', region.label));
      const list = make('ol', 'ja-chapters__list');
      if (region.chapters.length > 1 || region.chapters[0].label !== region.label) {
        region.chapters.forEach(chapter => {
          const seen = chapter.pages.filter(visited).length;
          const item = make('li', 'ja-chapter' + (seen === chapter.pages.length ? ' is-complete' : '') + (seen ? '' : ' is-empty'));
          const label = make('span', 'ja-chapter__label', chapter.label);
          const count = make('span', 'ja-chapter__count', seen + ' / ' + chapter.pages.length + (seen === chapter.pages.length ? ' ✓' : ''));
          const bar = make('span', 'ja-chapter__bar');
          bar.setAttribute('aria-hidden', 'true');
          const fill = make('span', '');
          fill.style.width = (chapter.pages.length ? Math.round(seen / chapter.pages.length * 100) : 0) + '%';
          bar.append(fill);
          item.append(label, count, bar);
          list.append(item);
        });
      }
      group.append(head);
      if (list.children.length) group.append(list);
      detail.append(group);
    });
  }
  // わたしの旅の果て: the farthest north / south and the farthest from Tokyo among visited
  // places (capital / seat positions from data/geo-facts.json; 南極 counts as the far south).
  // 旅の年表: visited places with an optional first-visit year, newest year first.
  const extremesBox = make('section', 'ja-extremes');
  extremesBox.setAttribute('aria-labelledby', 'ja-extremes-title');
  const timelineBox = make('details', 'ja-timeline');
  let geoEntries = null;
  let timelineOpen = false;
  let timelineYear = null;
  timelineBox.addEventListener('toggle', () => { timelineOpen = timelineBox.open; });
  fetchJSON('data/geo-facts.json').then(data => { geoEntries = data.entries || {}; renderMine(); }).catch(() => {});
  const TOKYO = [35.6812, 139.7671];
  const distanceKm = (a, b) => {
    const r = Math.PI / 180, dLat = (b[0] - a[0]) * r, dLon = (b[1] - a[1]) * r;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLon / 2) ** 2;
    return 6371 * 2 * Math.asin(Math.sqrt(h));
  };
  // Standard-time offset in minutes (daylight saving ignored, so the ranking does not change
  // with the season): the smaller of mid-January and mid-July. Morocco keeps UTC+1 as its
  // standard time and only steps back during Ramadan, so it is fixed here.
  const STD_OFFSET = {'Africa/Casablanca': 60};
  const offsetAt = (tz, date) => {
    const parts = new Intl.DateTimeFormat('en-US', {timeZone: tz, hourCycle: 'h23', year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric'})
      .formatToParts(date).reduce((acc, part) => ({...acc, [part.type]: Number(part.value)}), {});
    return Math.round((Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute) - date.getTime()) / 60000);
  };
  const standardOffset = tz => {
    if (tz in STD_OFFSET) return STD_OFFSET[tz];
    try {
      const year = new Date().getUTCFullYear();
      return Math.min(offsetAt(tz, new Date(Date.UTC(year, 0, 15, 12))), offsetAt(tz, new Date(Date.UTC(year, 6, 15, 12))));
    } catch { return null; }
  };
  const diffText = minutes => {
    const sign = minutes < 0 ? '−' : '+', abs = Math.abs(minutes), h = Math.floor(abs / 60), m = abs % 60;
    return sign + h + '時間' + (m ? m + '分' : '');
  };
  const latText = lat => (lat < 0 ? '南緯' : '北緯') + Math.abs(lat).toFixed(1) + '°';
  const lonText = lon => (lon < 0 ? '西経' : '東経') + Math.abs(lon).toFixed(1) + '°';

  // わたしの旅の中心: the average of the visited capitals as points on the globe (3D unit
  // vectors), projected back to the surface. The average lies inside the Earth, so its depth
  // below the surface is shown too. The world map's Robinson projection (lon_0 = 10°E,
  // 1000 × 507.209 units, scripts/build_world_map.py) places the point on the map and finds
  // the country it falls in; outside every country it is water (sea or a large lake).
  const ROBIN_X = [1, .9986, .9954, .99, .9822, .973, .96, .9427, .9216, .8962, .8679, .835, .7986, .7597, .7186, .6732, .6213, .5722, .5322];
  const ROBIN_Y = [0, .062, .124, .186, .248, .31, .372, .434, .4958, .5571, .6176, .6769, .7346, .7903, .8435, .8936, .9394, .9761, 1];
  const robinson = (lat, lon) => {
    const a = Math.min(Math.abs(lat), 90) / 5, i = Math.min(Math.floor(a), 17), t = a - i;
    const X = ROBIN_X[i] + (ROBIN_X[i + 1] - ROBIN_X[i]) * t, Y = ROBIN_Y[i] + (ROBIN_Y[i + 1] - ROBIN_Y[i]) * t;
    const dLon = ((lon - 10 + 540) % 360) - 180;
    const scale = 1000 / (2 * .8487 * Math.PI);
    return [500 + .8487 * X * dLon * Math.PI / 180 * scale, 507.209 / 2 - 1.3523 * Y * Math.sign(lat) * scale];
  };
  // Large lakes are cut out of the map's countries (scalerank ≤ 1 in scripts/build_world_map.py).
  // A point outside every country inside one of these boxes is in that lake; the boxes hold no
  // open sea, so anything else outside the countries is sea.
  const LAKES = [
    ['カスピ海', 36.5, 47.5, 46.5, 55.5], ['五大湖', 41.3, 49.1, -92.3, -76], ['ビクトリア湖', -3.1, .6, 31.5, 34.9],
    ['バイカル湖', 51.4, 55.9, 103.6, 110], ['タンガニーカ湖', -8.9, -3.3, 29, 31.3], ['マラウイ湖', -14.5, -9.4, 33.8, 35.4],
    ['グレートベア湖', 64.7, 67.2, -125.3, -117.5], ['グレートスレーブ湖', 60.8, 62.95, -117.4, -108.8], ['ウィニペグ湖', 50.3, 54, -99.3, -96.2],
    ['ラドガ湖', 59.9, 61.8, 30.5, 33], ['オネガ湖', 60.8, 62.95, 34.2, 36.5], ['バルハシ湖', 45, 47.2, 73.4, 79.3],
    ['チチカカ湖', -16.7, -15.2, -70.1, -68.6], ['ニカラグア湖', 10.9, 12.2, -85.8, -84.6]
  ];
  const lakeAt = (lat, lon) => (LAKES.find(([, s, n, w, e]) => lat >= s && lat <= n && lon >= w && lon <= e) || [])[0];
  let centerMap = null, centerMapLoading = false;
  const loadCenterMap = () => {
    if (centerMap || centerMapLoading || !window.JourneyAtlasWorldMap) return;
    centerMapLoading = true;
    window.JourneyAtlasWorldMap.load().then(map => { centerMap = map; renderMine(); }).catch(() => {}).finally(() => { centerMapLoading = false; });
  };
  const countryAt = point => {
    if (!centerMap?.land) return undefined;
    const dom = new DOMPoint(point[0], point[1]);
    for (const group of centerMap.land.querySelectorAll('[data-iso]')) {
      const shapes = group.querySelectorAll('path, polygon, circle');
      for (const shape of shapes) {
        try { if (shape.isPointInFill(dom)) return centerMap.byIso.get(group.dataset.iso) || {nameJa: ''}; } catch { /* not rendered */ }
      }
    }
    return null;
  };
  // Returns {place, coord, depth} for the 旅の中心 tile, or null with fewer than two places.
  function travelCenter(places) {
    const located = places.filter(item => item.place);
    if (located.length < 2) return null;
    const r = Math.PI / 180;
    let x = 0, y = 0, z = 0;
    located.forEach(({place}) => {
      x += Math.cos(place.lat * r) * Math.cos(place.lon * r);
      y += Math.cos(place.lat * r) * Math.sin(place.lon * r);
      z += Math.sin(place.lat * r);
    });
    x /= located.length; y /= located.length; z /= located.length;
    const length = Math.hypot(x, y, z);
    if (length < 1e-6) return {place: '地球の中心', coord: '', depth: '地表から約6,370km下'};
    const lat = Math.asin(z / length) / r, lon = Math.atan2(y, x) / r;
    const depth = Math.round(6371 * (1 - length) / 10) * 10;
    const country = countryAt(robinson(lat, lon));
    // Until the map geometry has loaded (country === undefined) only the coordinates show.
    const place = country === undefined ? null
      : country ? (country.nameJa ? `${country.nameJa}の上` : '陸の上') : `${lakeAt(lat, lon) || '海'}の上`;
    return {place, coord: `${latText(lat)}・${lonText(lon)}`, depth: `地表から約${depth.toLocaleString('ja-JP')}km下`};
  }
  function renderExtremes(places) {
    extremesBox.replaceChildren();
    const located = places.filter(item => item.place);
    const antarctica = places.find(item => item.slug === 'antarctica');
    if (!located.length && !antarctica) { extremesBox.hidden = true; return; }
    extremesBox.hidden = false;
    const title = make('h3', 'ja-extremes__title', 'わたしの旅の中心と果て');
    title.id = 'ja-extremes-title';
    const list = make('ul', 'ja-extremes__list');
    const tile = (label, item, value) => {
      const li = make('li', 'ja-extreme');
      li.append(make('span', 'ja-extreme__label', label), linkTo(item.href, item.nameJa, 'ja-extreme__name'), make('span', 'ja-extreme__value', value));
      list.append(li);
    };
    const center = travelCenter(places);
    if (center) {
      const li = make('li', 'ja-extreme ja-extreme--center');
      const value = make('span', 'ja-extreme__value');
      value.append(...(center.place && center.coord ? [center.coord, document.createElement('br')] : []), center.depth);
      li.append(make('span', 'ja-extreme__label', '旅の中心'), make('span', 'ja-extreme__name', center.place || center.coord), value);
      list.append(li);
    }
    if (located.length) {
      const north = located.reduce((a, b) => (b.place.lat > a.place.lat ? b : a));
      tile('いちばん北', north, latText(north.place.lat));
    }
    if (antarctica) tile('いちばん南', antarctica, '南極大陸');
    else if (located.length) {
      const south = located.reduce((a, b) => (b.place.lat < a.place.lat ? b : a));
      tile('いちばん南', south, latText(south.place.lat));
    }
    const away = located.filter(item => item.slug !== 'japan');
    if (away.length) {
      const far = away.map(item => ({item, km: distanceKm(TOKYO, [item.place.lat, item.place.lon])}))
        .reduce((a, b) => (b.km > a.km ? b : a));
      tile('東京からいちばん遠い', far.item, '約' + (Math.round(far.km / 100) * 100).toLocaleString('ja-JP') + 'km');
      const diffs = away.map(item => ({item, offset: item.tz ? standardOffset(item.tz) : null}))
        .filter(entry => entry.offset !== null)
        .map(entry => ({...entry, diff: entry.offset - 540}));
      if (diffs.length) {
        const widest = diffs.reduce((a, b) => (Math.abs(b.diff) > Math.abs(a.diff) ? b : a));
        if (widest.diff) tile('時差がいちばん大きい', widest.item, '日本と' + diffText(widest.diff));
      }
    }
    extremesBox.append(title, list, make('p', 'ja-extremes__note', '200の国・地域の首都の位置と、首都の標準時（夏時間を除く）で比べています。旅の中心は、行った国・地域の首都を地球儀の上で平均した地点で、平均した点は地球の内側にあるため、その深さも示しています。'));
  }
  // 旅の年表を画像に: one PNG drawn in this browser (nothing is uploaded), shared or saved
  // through the same dialog style as わたしの地図.
  function drawTimeline(dated) {
    const W = 1600, H = 900, PAD = 80, TOP = 250, BASE = 720;
    const canvas = document.createElement('canvas');
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext('2d');
    const INK = {paper: '#faf9f4', navy: '#173b5d', bar: '#36566b', track: '#e8ebe8', muted: '#5f6f7b', faint: '#9aa3a0', line: '#d9dcd6'};
    const font = (weight, size) => weight + ' ' + size + 'px "Zen Kaku Gothic New",sans-serif';
    ctx.fillStyle = INK.paper; ctx.fillRect(0, 0, W, H);
    const counts = new Map();
    dated.forEach(item => counts.set(item.year, (counts.get(item.year) || 0) + 1));
    const first = Math.min(...counts.keys()), last = Math.max(...counts.keys());
    const peak = Math.max(...counts.values());
    ctx.fillStyle = INK.navy; ctx.font = font(700, 46); ctx.textBaseline = 'alphabetic';
    ctx.fillText('わたしの旅の年表', PAD, 120);
    ctx.fillStyle = INK.muted; ctx.font = font(500, 22);
    ctx.fillText(first + '年〜' + last + '年に初めて行った国・地域', PAD, 168);
    const totalText = dated.length + ' / ' + parentsCount;
    ctx.textAlign = 'right';
    ctx.fillStyle = INK.navy; ctx.font = font(700, 54); ctx.fillText(totalText, W - PAD, 124);
    ctx.fillStyle = INK.muted; ctx.font = font(500, 20); ctx.fillText('記録した国・地域', W - PAD, 160);
    ctx.textAlign = 'left';
    const span = last - first + 1;
    const slot = (W - PAD * 2) / span;
    const barW = Math.max(6, Math.min(44, slot * 0.56));
    const every = span <= 16 ? 1 : span <= 32 ? 2 : 5;
    ctx.strokeStyle = INK.line; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(PAD, BASE + 1); ctx.lineTo(W - PAD, BASE + 1); ctx.stroke();
    for (let year = first; year <= last; year += 1) {
      const count = counts.get(year) || 0;
      const cx = PAD + (year - first + 0.5) * slot;
      const height = count ? Math.max(10, (BASE - TOP - 40) * count / peak) : 0;
      ctx.fillStyle = INK.track;
      ctx.beginPath(); ctx.roundRect(cx - barW / 2, TOP + 40, barW, BASE - TOP - 40, 5); ctx.fill();
      if (count) {
        ctx.fillStyle = INK.bar;
        ctx.beginPath(); ctx.roundRect(cx - barW / 2, BASE - height, barW, height, 5); ctx.fill();
        ctx.fillStyle = INK.navy; ctx.font = font(700, slot < 30 ? 16 : 22); ctx.textAlign = 'center';
        ctx.fillText(String(count), cx, BASE - height - 12);
      }
      if ((year - first) % every === 0 || year === last) {
        ctx.fillStyle = count ? INK.navy : INK.faint; ctx.font = font(500, slot < 30 ? 15 : 19); ctx.textAlign = 'center';
        ctx.fillText(String(year), cx, BASE + 36);
      }
    }
    ctx.textAlign = 'left';
    ctx.fillStyle = INK.muted; ctx.font = font(600, 20);
    ctx.fillText('JOURNEY ATLAS', PAD, H - 48);
    ctx.textAlign = 'right'; ctx.font = font(500, 18);
    ctx.fillText('atlas.yagenji.com', W - PAD, H - 48);
    return canvas;
  }
  let parentsCount = 200;
  let timelineDialog = null;
  async function openTimelineShare(dated) {
    if (!timelineDialog) {
      const dialog = make('dialog', 'ja-share');
      dialog.setAttribute('aria-labelledby', 'ja-timeline-share-title');
      const head = make('div', 'ja-share__head');
      const title = make('h2', '', '旅の年表を画像にする');
      title.id = 'ja-timeline-share-title';
      const close = make('button', 'ja-share__close', '閉じる');
      close.type = 'button';
      close.addEventListener('click', () => dialog.close());
      head.append(title, close);
      const preview = make('img', 'ja-share__preview');
      const actions = make('div', 'ja-share__actions');
      const save = make('button', 'ja-tool-button', '画像を保存');
      save.type = 'button';
      const shareButton = make('button', 'ja-tool-button', '共有する');
      shareButton.type = 'button';
      actions.append(save, shareButton);
      const note = make('p', 'ja-share__note');
      note.setAttribute('role', 'status');
      dialog.append(head, preview, actions, note);
      dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
      document.body.append(dialog);
      timelineDialog = {dialog, preview, save, shareButton, note, file: null, url: ''};
      save.addEventListener('click', () => {
        const link = make('a');
        link.href = timelineDialog.url; link.download = timelineDialog.file.name;
        document.body.append(link); link.click(); link.remove();
        note.textContent = '画像を保存しました。';
      });
      shareButton.addEventListener('click', async () => {
        try {
          await navigator.share({files: [timelineDialog.file], text: 'わたしの旅の年表（' + timelineDialog.count + '件）。JOURNEY ATLASより https://atlas.yagenji.com/'});
        } catch (error) { if (error?.name !== 'AbortError') note.textContent = '共有できませんでした。画像を保存してお使いください。'; }
      });
    }
    const box = timelineDialog;
    if (!box.dialog.open) box.dialog.showModal();
    box.note.textContent = '画像を作成しています…';
    box.preview.hidden = true; box.save.hidden = true; box.shareButton.hidden = true;
    try {
      if (document.fonts?.load) await Promise.race([document.fonts.load('700 46px "Zen Kaku Gothic New"', 'わたしの旅の年表'), new Promise(done => setTimeout(done, 2000))]);
      const canvas = drawTimeline(dated);
      const blob = await new Promise((resolve, reject) => canvas.toBlob(b => (b ? resolve(b) : reject(Error('PNG'))), 'image/png'));
      box.file = new File([blob], 'journey-atlas-timeline.png', {type: 'image/png'});
      box.count = dated.length;
      if (box.url) URL.revokeObjectURL(box.url);
      box.url = URL.createObjectURL(box.file);
      box.preview.src = box.url;
      box.preview.alt = '旅の年表の画像。記録した国・地域は' + dated.length + '件。';
      box.preview.hidden = false; box.save.hidden = false;
      let canShare = false;
      try { canShare = !!navigator.canShare?.({files: [box.file]}) && !!navigator.share; } catch { canShare = false; }
      box.shareButton.hidden = !canShare;
      box.note.textContent = '画像はこのブラウザの中で作られ、送信されません。';
    } catch { box.note.textContent = '画像を作成できませんでした。'; }
  }

  function renderTimeline(places) {
    timelineBox.replaceChildren();
    const yearOf = item => { const year = getStored(VISIT_YEAR_PREFIX + item.yearKey); return validYear(year) ? +year : null; };
    const items = places.map(item => ({...item, year: yearOf(item)}));
    const dated = items.filter(item => item.year);
    const summaryLine = make('summary', 'ja-timeline__title', '旅の年表');
    summaryLine.append(make('span', 'ja-timeline__count', dated.length ? '（' + dated.length + '件）' : ''));
    timelineBox.append(summaryLine);
    timelineBox.open = timelineOpen;
    if (!items.length) {
      timelineBox.append(make('p', 'ja-empty', '「行った旅先」を登録すると、年表をつくれます。'));
      return;
    }
    // Years run left to right (oldest → newest, empty years kept so the gaps show): the
    // number of first visits as a bar, the running total under it. Every year can be chosen;
    // the chosen year's places are recorded by tapping them below (tap again to clear).
    const thisYear = new Date().getFullYear();
    const counts = new Map();
    dated.forEach(item => counts.set(item.year, (counts.get(item.year) || 0) + 1));
    const recorded = [...counts.keys()];
    const first = Math.min(thisYear - 10, ...recorded);
    const peak = Math.max(1, ...counts.values());
    if (!validYear(timelineYear)) timelineYear = recorded.length ? Math.max(...recorded) : thisYear;
    const chart = make('div', 'ja-timeline__chart');
    chart.setAttribute('role', 'group');
    chart.setAttribute('aria-label', '年を選ぶ（年ごとの初めて行った旅先の数）');
    let total = 0;
    const startYear = Math.min(first, timelineYear);
    for (let year = startYear; year <= thisYear; year += 1) {
      const count = counts.get(year) || 0;
      total += count;
      const col = make('button', 'ja-timeline__col' + (count ? '' : ' is-empty') + (year === timelineYear ? ' is-selected' : ''));
      col.type = 'button';
      col.dataset.year = String(year);
      col.setAttribute('aria-pressed', String(year === timelineYear));
      col.setAttribute('aria-label', year + '年 ' + count + '件（累計' + total + '件）');
      const track = make('span', 'ja-timeline__track');
      const bar = make('span', 'ja-timeline__bar');
      bar.style.height = (count ? Math.max(8, Math.round(count / peak * 100)) : 0) + '%';
      track.append(bar);
      col.append(make('span', 'ja-timeline__n', count ? String(count) : ''), track,
        make('span', 'ja-timeline__yr', String(year)), make('span', 'ja-timeline__sum', '累計' + total));
      col.addEventListener('click', () => { timelineYear = year; renderMine(); });
      chart.append(col);
    }
    const scroller = make('div', 'ja-timeline__scroller');
    scroller.append(chart);
    // Earlier years than the chart shows.
    const earlier = make('label', 'ja-timeline__earlier', 'もっと前の年');
    const select = make('select', 'visit-year__select');
    select.append(new Option('選ぶ', ''));
    for (let year = startYear - 1; year >= 1950; year -= 1) select.append(new Option(year + '年', String(year)));
    select.addEventListener('change', () => { if (select.value) { timelineYear = +select.value; renderMine(); } });
    earlier.append(select);

    const detail = make('div', 'ja-timeline__detail');
    const year = timelineYear;
    detail.append(make('h4', 'ja-timeline__detail-title', year + '年に初めて行った旅先'));
    detail.append(make('p', 'ja-timeline__hint', '行った旅先を押すと、' + year + '年として記録します。もう一度押すと外れます。'));
    const byName = (a, b) => a.nameJa.localeCompare(b.nameJa, 'ja');
    const chip = item => {
      const on = item.year === year;
      const button = make('button', 'ja-year-chip' + (on ? ' is-on' : ''));
      button.type = 'button';
      button.setAttribute('aria-pressed', String(on));
      button.append(make('span', '', (on ? '✓ ' : '') + item.nameJa));
      if (item.year && !on) button.append(make('small', '', String(item.year)));
      button.addEventListener('click', () => {
        const ok = on ? removeStored(VISIT_YEAR_PREFIX + item.yearKey) : putStored(VISIT_YEAR_PREFIX + item.yearKey, String(year));
        // Same-tab writes fire no storage event; keep わたしの地図's year slider in step.
        window.dispatchEvent(new StorageEvent('storage', {key: VISIT_YEAR_PREFIX + item.yearKey}));
        feedback.textContent = !ok ? 'このブラウザには保存できませんでした。'
          : on ? item.nameJa + 'の年の記録を外しました。' : item.nameJa + 'を' + year + '年として記録しました。';
        renderMine();
      });
      return button;
    };
    const group = (label, list, open = true) => {
      if (!list.length) return null;
      const box = open ? make('div', 'ja-year-group') : make('details', 'ja-year-group');
      const head = make(open ? 'p' : 'summary', 'ja-year-group__label', label + '（' + list.length + '）');
      const chips = make('div', 'ja-year-chips');
      list.sort(byName).forEach(item => chips.append(chip(item)));
      box.append(head, chips);
      return box;
    };
    [
      group('この年', items.filter(item => item.year === year)),
      group('年が未記入', items.filter(item => !item.year)),
      group('ほかの年に記録済み', items.filter(item => item.year && item.year !== year), false)
    ].filter(Boolean).forEach(node => detail.append(node));

    const shareTimeline = make('button', 'ja-tool-button ja-timeline__share', '年表を画像にして共有');
    shareTimeline.type = 'button';
    shareTimeline.hidden = !dated.length;
    shareTimeline.addEventListener('click', () => openTimelineShare(dated));
    timelineBox.append(scroller, earlier, shareTimeline, detail);
    // Keep the chosen year in view.
    const toSelected = () => chart.querySelector('.is-selected')?.scrollIntoView({block: 'nearest', inline: 'center'});
    if (timelineBox.open) requestAnimationFrame(toSelected);
    timelineBox.addEventListener('toggle', () => { if (timelineBox.open) requestAnimationFrame(toSelected); }, {once: true});
  }

  mine.append(summary, chaptersBox, extremesBox, timelineBox, groupsBox, tools, feedback);
  // わたしの地図 (atlas-my-map.js) may already be in place: keep 行った数・行きたい数 first.
  mine.prepend(summary);
  // Flags for UK Regions follow each Region page; Northern Ireland has no official
  // regional flag, so the United Kingdom flag is used (see its sourceNotes.flag).
  const REGION_FLAGS = {
    'unitedkingdom:england': {flagAsset: 'assets/icons/region-flags/england-waved.svg'},
    'unitedkingdom:scotland': {flagAsset: 'assets/icons/region-flags/scotland-waved.svg'},
    'unitedkingdom:wales': {flagAsset: 'assets/icons/region-flags/wales-waved.svg'},
    'unitedkingdom:northern-ireland': {flag: '🇬🇧'}
  };
  const regionFlag = item => ({flag: '', ...REGION_FLAGS[item.parentSlug + ':' + item.slug]});
  const visited = country => getStored(VISITED_PREFIX + country.slug) === 'true';
  const wished = country => getStored(WISH_PREFIX + country.slug) === 'true';
  function sectionFor(title, items, empty, groupByRegion = false) {
    const section = make('section', 'ja-mine-group');
    section.append(make('h3', '', title));
    if (items.length) {
      const appendLinks = (container, countries) => {
        const list = make('div', 'ja-mine-links');
        countries.forEach(country => {
          const link = linkTo(country.href || countryHref(country.slug), [country.flag, country.nameJa].filter(Boolean).join(' '));
          if (country.flagAsset) {
            // Subdivision flag emoji do not render everywhere; use the same images as the Region pages.
            const flag = make('img', 'ja-flag-img');
            flag.src = country.flagAsset;
            flag.alt = '';
            flag.width = 18;
            flag.height = 18;
            flag.decoding = 'async';
            link.prepend(flag, ' ');
          }
          list.append(link);
        });
        container.append(list);
      };
      if (groupByRegion && regionNames.length) {
        const assigned = new Set();
        regionNames.forEach(region => {
          const matches = items.filter(country => region.iso2.includes(country.iso2));
          if (!matches.length) return;
          matches.forEach(country => assigned.add(country.slug));
          const block = make('div', 'ja-mine-region');
          block.append(make('h4', 'ja-mine-region-title', region.label + ' ' + matches.length + ' / ' + region.iso2.length));
          appendLinks(block, matches);
          section.append(block);
        });
        const unmatched = items.filter(country => !assigned.has(country.slug));
        if (unmatched.length) {
          const block = make('div', 'ja-mine-region');
          block.append(make('h4', 'ja-mine-region-title', 'その他 ' + unmatched.length));
          appendLinks(block, unmatched);
          section.append(block);
        }
      } else appendLinks(section, items);
    } else section.append(make('p', 'ja-empty', empty));
    return section;
  }
  function renderMine() {
    if (!registry.length) return;
    const all = registry.filter(c => validId(c.slug));
    const detailSlugs = new Set(['hong-kong','macau']);
    const parents = all.filter(c => !detailSlugs.has(c.slug));
    const seen = parents.filter(visited), want = parents.filter(wished);
    parentsCount = parents.length;
    const detailSeen = all.filter(c => detailSlugs.has(c.slug) && visited(c));
    const detailWant = all.filter(c => detailSlugs.has(c.slug) && wished(c));
    const regionWishes = getRegionWishes().filter(w => all.some(c => c.slug === w.parentSlug));
    const regionVisits = getRegionVisits().filter(w => all.some(c => c.slug === w.parentSlug));
    // Parent Countries define the 200 denominator. Detail regions keep
    // independent wishes and visits; no automatic parent selection.
    const detailWishCount = detailWant.length + regionWishes.length;
    const detailVisitCount = detailSeen.length + regionVisits.length;
    const detailTotal = publishedRegionCount === null ? null : publishedRegionCount + all.filter(c => detailSlugs.has(c.slug)).length;
    summary.replaceChildren();
    [
      ['VISITED', seen.length, '行った旅先', detailVisitCount, '行った詳細地域', 'visited'],
      ['WISHLIST', want.length, '行きたい旅先', detailWishCount, '行きたい詳細地域', 'wished']
    ].forEach(([tag, count, name, detailCount, detailName, kind]) => {
      const item = make('div', 'ja-summary-item');
      item.dataset.summaryKind = kind;
      const detail = make('p', 'ja-summary-detail');
      detail.append(
        make('span', 'ja-summary-detail__label', detailName),
        make('strong', 'ja-summary-detail__count', detailCount + (detailTotal === null ? '' : ' / ' + detailTotal))
      );
      item.append(make('span', '', tag), make('strong', '', count + ' / ' + parents.length), make('small', '', name), detail);
      summary.append(item);
    });
    const seenColumn = make('div', 'ja-mine-column');
    const wantColumn = make('div', 'ja-mine-column');
    seenColumn.append(sectionFor('行った旅先', seen, 'ページの「ここに行った」または地図から登録できます。', true));
    if (detailSeen.length || regionVisits.length) seenColumn.append(
      sectionFor('行った詳細地域', [...detailSeen,...regionVisits.map(w => ({...w,...regionFlag(w)}))], '')
    );
    wantColumn.append(sectionFor('行きたい旅先', want, 'ページの「ここに行きたい」で登録できます。', true));
    if (detailWant.length || regionWishes.length) wantColumn.append(
      sectionFor('行きたい詳細地域', [...detailWant,...regionWishes.map(w => ({...w,...regionFlag(w)}))], '')
    );
    groups.replaceChildren(seenColumn, wantColumn);
    groupsCount.textContent = '（行った' + seen.length + '・行きたい' + want.length + '）';
    renderChapters();
    // 旅の果て and 旅の年表 use the 200 Country pages only (no detail regions such as
    // England, Hong Kong or Macau), the same base as the VISITED count.
    const visitedPlaces = parents.filter(visited)
      .map(c => ({slug: c.slug, nameJa: c.nameJa, href: c.href || countryHref(c.slug), yearKey: c.slug}))
      .map(item => ({...item, place: geoEntries?.[item.slug]?.place && Number.isFinite(geoEntries[item.slug].place.lon) ? geoEntries[item.slug].place : null, tz: geoEntries?.[item.slug]?.tz || null}));
    if (geoEntries) { renderExtremes(visitedPlaces); if (!centerMap && disclosure?.open) loadCenterMap(); }
    else extremesBox.hidden = true;
    renderTimeline(visitedPlaces);

  }
  const exportButton = make('button', 'ja-tool-button', '保存データを書き出す');
  exportButton.type = 'button';
  exportButton.addEventListener('click', () => {
    const countries = registry.filter(c => validId(c.slug));
    const payload = {
      version: 1,
      visited: countries.filter(visited).map(c => c.slug),
      wished: countries.filter(wished).map(c => c.slug),
      favorites: getFavorites(),
      regionWishes: getRegionWishes(),
      regionVisits: getRegionVisits(),
      visitYears: Object.fromEntries(allStoredKeys().filter(key => key.startsWith(VISIT_YEAR_PREFIX))
        .map(key => [key.slice(VISIT_YEAR_PREFIX.length), getStored(key)]).filter(([, year]) => validYear(year)))
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], {type: 'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'journey-atlas-my-atlas.json';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    feedback.textContent = 'このブラウザの保存データを書き出しました。';
  });
  const importLabel = make('label', 'ja-tool-button ja-import-label', '保存データを読み込む');
  const fileInput = make('input');
  fileInput.type = 'file';
  fileInput.accept = '.json,application/json';
  fileInput.setAttribute('aria-label', '保存データのJSONファイル');
  importLabel.append(fileInput);
  fileInput.addEventListener('change', async () => {
    const file = fileInput.files?.[0];
    fileInput.value = '';
    if (!file) return;
    if (file.size > 1024 * 1024) { feedback.textContent = 'ファイルサイズが大きすぎます。'; return; }
    try {
      const payload = JSON.parse(await file.text());
      if (payload.version !== 1 || !Array.isArray(payload.visited) || !Array.isArray(payload.wished) || !Array.isArray(payload.favorites)) throw Error('Invalid backup');
      const allowed = new Set(registry.map(c => c.slug));
      payload.visited.filter(slug => allowed.has(slug)).forEach(slug => { if (!putStored(VISITED_PREFIX + slug, 'true')) throw Error('Storage unavailable'); });
      payload.wished.filter(slug => allowed.has(slug)).forEach(slug => { if (!putStored(WISH_PREFIX + slug, 'true')) throw Error('Storage unavailable'); });
      payload.favorites.filter(f => f && (allowed.has(f.slug) || (isRegionFavorite(f) && allowed.has(f.parentSlug))) && validId(f.id) && typeof f.name === 'string' && typeof f.countryName === 'string' && typeof f.image === 'string').slice(0, 3000).forEach(f => {
        const metadata = isRegionFavorite(f) ? {kind:'region',parentSlug:f.parentSlug,href:f.href} : {};
        if (!putStored(sceneKey(f.slug, f.id), JSON.stringify({slug: f.slug, id: f.id, name: f.name.slice(0, 150), countryName: f.countryName.slice(0, 100), image: f.image.slice(0, 240), ...metadata}))) throw Error('Storage unavailable');
      });
      if (Array.isArray(payload.regionWishes)) payload.regionWishes.filter(w => w && validId(w.parentSlug) && validId(w.slug)
        && allowed.has(w.parentSlug) && typeof w.nameJa === 'string'
        && w.href === regionCountryHref(w.parentSlug,w.slug)).slice(0,100).forEach(w => {
        if (!putStored(REGION_WISH_PREFIX + w.parentSlug + ':' + w.slug,
          JSON.stringify({parentSlug:w.parentSlug,slug:w.slug,nameJa:w.nameJa.slice(0,100),href:w.href}))) throw Error('Storage unavailable');
      });
      if (Array.isArray(payload.regionVisits)) payload.regionVisits.filter(w => w && validId(w.parentSlug) && validId(w.slug)
        && allowed.has(w.parentSlug) && typeof w.nameJa === 'string'
        && w.href === regionCountryHref(w.parentSlug,w.slug)).slice(0,100).forEach(w => {
        if (!putStored(REGION_VISITED_PREFIX + w.parentSlug + ':' + w.slug,
          JSON.stringify({parentSlug:w.parentSlug,slug:w.slug,nameJa:w.nameJa.slice(0,100),href:w.href}))) throw Error('Storage unavailable');
      });
      if (payload.visitYears && typeof payload.visitYears === 'object') Object.entries(payload.visitYears).slice(0, 400).forEach(([id, year]) => {
        const [first, second] = id.split(':');
        const known = second === undefined ? allowed.has(first) : allowed.has(first) && validId(second);
        if (known && validYear(year) && !putStored(VISIT_YEAR_PREFIX + id, String(year))) throw Error('Storage unavailable');
      });
      feedback.textContent = '保存データを読み込みました。既存の記録には追加されます。';
      renderMine();
    } catch { feedback.textContent = '保存データを読み込めませんでした。書き出したJSONファイルを選んでください。'; }
  });
  tools.append(exportButton, importLabel, make('p', 'ja-storage-note', 'アカウント不要。記録はこのブラウザに保存されます。端末を変える際はファイルで引き継げます。'));
  fetchJSON(REGISTRY_PATH).then(data => {
    registry = Array.isArray(data.destinations) ? data.destinations : [];
    renderMine();
    fetchJSON('data/region-taxonomy.json').then(data => {
      regionNames = (data.regions || []).filter(region => Array.isArray(region.iso2));
      renderMine();
    }).catch(() => {});
  }).catch(() => {
    feedback.textContent = 'アトラスの一覧を読み込めませんでした。';
  });
  window.addEventListener('storage', () => {
    renderMine();
  });
})();
