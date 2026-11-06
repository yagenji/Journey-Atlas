/* JOURNEY ATLAS — わたしの地図 inside マイアトラス.
   Records stay in this browser. Geometry is copied from the world map built by
   map-regions.js and is loaded only when マイアトラス is opened. */
(() => {
  'use strict';
  const home = document.querySelector('.ja-mine');
  const disclosure = document.querySelector('#my-atlas');
  if (!home || !disclosure) return;
  const WORLD = [0, 0, 1000, 507.209];
  const RATIO = WORLD[3] / WORLD[2];
  const MIN_WIDTH = 4.5;
  const NS = 'http://www.w3.org/2000/svg';
  const TOUCH = window.matchMedia?.('(hover: none) and (pointer: coarse)').matches;
  const visitedKey = slug => 'journey-atlas:visited:' + slug;
  const wishKey = slug => 'journey-atlas:wish:' + slug;
  const flag = key => { try { return localStorage.getItem(key) === 'true'; } catch { return false; } };
  const isVisited = country => flag(visitedKey(country.slug));
  const isWished = country => flag(wishKey(country.slug));
  const searchText = value => String(value || '').normalize('NFKC').toLowerCase().replace(/macao/g, 'macau');
  const make = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };

  const section = make('section', 'ja-mymap');
  section.setAttribute('aria-labelledby', 'ja-mymap-title');
  const title = make('h3', 'ja-mymap__title', 'わたしの地図');
  title.id = 'ja-mymap-title';
  const modes = make('div', 'ja-mymap__modes');
  modes.setAttribute('role', 'radiogroup');
  modes.setAttribute('aria-label', '地図の表示');
  const stage = make('div', 'ja-mymap__stage');
  const hint = make('p', 'ja-mymap__hint', TOUCH
    ? '国をタップで「行った国」に印 ・ 2本指で移動・拡大'
    : '国をクリックで「行った国」に印 ・ ホイールで拡大縮小 ・ ドラッグで移動');
  const status = make('p', 'ja-mymap__status');
  status.setAttribute('role', 'status');
  const share = make('button', 'ja-tool-button ja-mymap__share', '地図を画像にして共有');
  share.type = 'button';
  share.addEventListener('click', () => window.JourneyAtlasMapShare?.open(mode));
  const mapColumn = make('div', 'ja-mymap__column');
  mapColumn.append(modes, stage, hint, status, share);
  const picker = make('div', 'map-mine ja-mymap__picker');
  section.append(title, mapColumn, picker);
  home.prepend(section);

  let map, svg, view = [...WORLD], query = '', visitedOnly = false, loading = false, mode = 'both';
  [['both', '行った国と行きたい国'], ['visited', '行った国だけ'], ['wished', '行きたい国だけ']].forEach(([id, label]) => {
    const choice = make('label', 'ja-mymap__mode');
    const radio = make('input');
    radio.type = 'radio';
    radio.name = 'ja-mymap-mode';
    radio.value = id;
    radio.checked = id === mode;
    radio.addEventListener('change', () => { mode = id; if (svg) paint(); });
    choice.append(radio, make('span', '', label));
    modes.append(choice);
  });
  const applyView = next => {
    const width = Math.max(MIN_WIDTH, Math.min(WORLD[2], next[2]));
    const height = width * RATIO;
    view = [
      Math.max(0, Math.min(WORLD[2] - width, next[0])),
      Math.max(0, Math.min(WORLD[3] - height, next[1])),
      width, height
    ];
    svg.setAttribute('viewBox', view.join(' '));
  };
  const point = (x, y) => {
    const box = svg.getBoundingClientRect();
    return {x: view[0] + (x - box.left) / box.width * view[2], y: view[1] + (y - box.top) / box.height * view[3]};
  };
  const zoom = (factor, cx = view[0] + view[2] / 2, cy = view[1] + view[3] / 2) => {
    const width = Math.max(MIN_WIDTH, Math.min(WORLD[2], view[2] * factor));
    const scale = width / view[2];
    applyView([cx - (cx - view[0]) * scale, cy - (cy - view[1]) * scale, width, width * RATIO]);
  };
  function paint() {
    svg.querySelectorAll('.ja-country.is-destination').forEach(group => {
      const country = map.byIso.get(group.dataset.iso);
      const visited = !!country && mode !== 'wished' && isVisited(country);
      const wished = !!country && mode !== 'visited' && !visited && isWished(country);
      group.classList.toggle('is-visited', visited);
      group.classList.toggle('is-wished', wished);
    });
  }
  function renderCountries() {
    const rows = picker.querySelector('.map-mine__countries');
    const activeSlug = rows.contains(document.activeElement) ? document.activeElement.dataset.visitedSlug : null;
    const scrollTop = rows.scrollTop;
    const needle = searchText(query).trim();
    const countries = map.countries
      .filter(c => (!visitedOnly || isVisited(c)) && searchText(`${c.nameJa} ${c.nameEn} ${c.slug} ${c.iso2}`).includes(needle))
      .sort((a, b) => a.nameEn.localeCompare(b.nameEn, 'en', {sensitivity: 'base'}));
    const assigned = new Set();
    const blocks = map.regions.map(region => {
      const items = countries.filter(c => region.iso2.includes(c.iso2));
      items.forEach(c => assigned.add(c.slug));
      return {label: region.label, items};
    });
    blocks.push({label: 'その他', items: countries.filter(c => !assigned.has(c.slug))});
    rows.replaceChildren(...blocks.filter(block => block.items.length).map(block => {
      const group = make('section', 'map-mine__region');
      group.setAttribute('aria-label', block.label);
      const heading = make('h4', 'map-mine__region-heading');
      heading.append(make('span', '', block.label),
        make('span', 'map-mine__region-count', block.items.filter(isVisited).length + ' / ' + block.items.length));
      group.append(heading);
      block.items.forEach(country => {
        const item = make('div', 'map-mine__item');
        const choice = make('label', 'map-mine__choice');
        const box = make('input');
        box.type = 'checkbox';
        box.dataset.visitedSlug = country.slug;
        box.checked = isVisited(country);
        box.setAttribute('aria-label', country.nameJa + 'を行った国・地域にする');
        const flagMark = make('span', 'map-country-nav__flag', country.flag);
        flagMark.setAttribute('aria-hidden', 'true');
        const names = make('span', 'map-country-nav__names');
        names.append(make('strong', '', country.nameJa), make('small', '', country.nameEn));
        choice.append(box, flagMark, names);
        item.append(choice);
        if (country.href) {
          const link = make('a', 'map-mine__country-link', '↗');
          link.href = country.href;
          link.setAttribute('aria-label', country.nameJa + 'のページを開く');
          item.append(link);
        }
        group.append(item);
      });
      return group;
    }));
    picker.querySelector('.map-mine__result-count').textContent = countries.length + '件（詳細地域を含む）';
    const empty = picker.querySelector('.map-mine__no-results');
    empty.hidden = countries.length > 0;
    empty.textContent = visitedOnly && !needle
      ? '行った国・地域はまだありません。「行った国・地域だけ表示」を外して追加できます。'
      : '該当する国・地域がありません。';
    rows.scrollTop = scrollTop;
    if (activeSlug) (rows.querySelector(`[data-visited-slug="${activeSlug}"]`) || picker.querySelector('[data-mine-filter]')).focus({preventScroll: true});
  }
  function toggleVisited(country) {
    const on = !isVisited(country);
    try {
      if (on) localStorage.setItem(visitedKey(country.slug), 'true');
      else localStorage.removeItem(visitedKey(country.slug));
    } catch {
      renderCountries();
      status.textContent = '記録を保存できませんでした。ブラウザの保存設定をご確認ください。';
      return;
    }
    paint();
    renderCountries();
    status.textContent = on ? country.nameJa + 'を「行った国」にしました' : country.nameJa + 'の印を外しました';
    // Same-tab writes fire no storage event; keep マイアトラス's lists in step.
    window.dispatchEvent(new StorageEvent('storage', {key: visitedKey(country.slug)}));
  }
  function buildPicker() {
    const search = make('label', 'map-mine__search');
    const input = make('input');
    input.type = 'search';
    input.placeholder = '国・地域名で検索（例：マカオ）';
    input.autocomplete = 'off';
    input.setAttribute('aria-label', '行った国・地域を検索');
    search.append(make('span', '', '行った国・地域を選ぶ'), input);
    const filter = make('label', 'map-mine__filter');
    const only = make('input');
    only.type = 'checkbox';
    only.dataset.mineFilter = '';
    filter.append(only, document.createTextNode('行った国・地域だけ表示'));
    const count = make('p', 'map-mine__result-count');
    count.setAttribute('aria-live', 'polite');
    const rows = make('div', 'map-mine__countries');
    rows.setAttribute('role', 'group');
    rows.setAttribute('aria-label', '行った国・地域の選択');
    const empty = make('p', 'map-mine__no-results map-mine__empty');
    empty.hidden = true;
    picker.append(search, filter, count, rows, empty);
    input.addEventListener('input', () => { query = input.value; rows.scrollTop = 0; renderCountries(); });
    only.addEventListener('change', () => { visitedOnly = only.checked; rows.scrollTop = 0; renderCountries(); });
    rows.addEventListener('change', event => {
      const country = map.countries.find(c => c.slug === event.target.dataset.visitedSlug);
      if (country) toggleVisited(country);
    });
  }
  function buildMap() {
    svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'ja-mymap__map');
    svg.setAttribute('viewBox', view.join(' '));
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', '行った国を塗る世界地図。国名の一覧からも選べます。');
    const ocean = document.createElementNS(NS, 'rect');
    ocean.setAttribute('width', WORLD[2]);
    ocean.setAttribute('height', WORLD[3]);
    ocean.setAttribute('class', 'ja-mymap__ocean');
    const land = map.land.cloneNode(true);
    land.querySelectorAll('.ja-country').forEach(group => {
      group.classList.remove('is-hovered', 'is-selected', 'is-muted');
      ['tabindex', 'role', 'aria-label', 'style'].forEach(name => group.removeAttribute(name));
      const country = map.byIso.get(group.dataset.iso);
      if (!country) return;
      const name = document.createElementNS(NS, 'title');
      name.textContent = country.nameJa;
      group.prepend(name);
    });
    svg.append(ocean, land);
    const controls = make('div', 'ja-mymap__zoom');
    [['＋', '拡大', () => zoom(.69)], ['−', '縮小', () => zoom(1.45)], ['↺', '表示を戻す', () => applyView(WORLD)]].forEach(([mark, label, action]) => {
      const button = make('button', '', mark);
      button.type = 'button';
      button.setAttribute('aria-label', label);
      button.addEventListener('click', action);
      controls.append(button);
    });
    stage.replaceChildren(svg, controls);

    let drag = null, moved = false, pinch = null;
    svg.addEventListener('click', event => {
      if (moved) { moved = false; return; }
      const group = event.target.closest?.('.is-destination');
      const country = group && map.byIso.get(group.dataset.iso);
      if (country) toggleVisited(country);
    });
    svg.addEventListener('wheel', event => {
      event.preventDefault();
      const at = point(event.clientX, event.clientY);
      zoom(event.deltaY < 0 ? .8 : 1.23, at.x, at.y);
    }, {passive: false});
    svg.addEventListener('pointerdown', event => {
      if (event.pointerType === 'touch') return;
      moved = false;
      drag = {id: event.pointerId, x: event.clientX, y: event.clientY, view: [...view]};
    });
    svg.addEventListener('pointermove', event => {
      if (!drag || drag.id !== event.pointerId) return;
      const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
      if (!moved && Math.hypot(dx, dy) < 4) return;
      if (!moved) svg.setPointerCapture?.(event.pointerId);
      moved = true;
      const box = svg.getBoundingClientRect();
      applyView([drag.view[0] - dx / box.width * drag.view[2], drag.view[1] - dy / box.height * drag.view[3], drag.view[2], drag.view[3]]);
    });
    const endDrag = event => { if (drag?.id === event.pointerId) drag = null; };
    svg.addEventListener('pointerup', endDrag);
    svg.addEventListener('pointercancel', endDrag);
    // Touch: one finger keeps scrolling the page; two fingers pan and pinch.
    svg.style.touchAction = 'pan-x pan-y';
    const middle = touches => ({x: (touches[0].clientX + touches[1].clientX) / 2, y: (touches[0].clientY + touches[1].clientY) / 2});
    const spread = touches => Math.hypot(touches[0].clientX - touches[1].clientX, touches[0].clientY - touches[1].clientY) || 1;
    svg.addEventListener('touchstart', event => {
      if (event.touches.length !== 2) { pinch = null; return; }
      event.preventDefault();
      const at = middle(event.touches);
      pinch = {view: [...view], spread: spread(event.touches), at: point(at.x, at.y)};
    }, {passive: false});
    svg.addEventListener('touchmove', event => {
      if (!pinch || event.touches.length !== 2) return;
      event.preventDefault();
      const width = pinch.view[2] * pinch.spread / spread(event.touches);
      applyView([pinch.view[0], pinch.view[1], width, width * RATIO]);
      const at = middle(event.touches), now = point(at.x, at.y);
      applyView([view[0] + pinch.at.x - now.x, view[1] + pinch.at.y - now.y, view[2], view[3]]);
    }, {passive: false});
    const endPinch = event => { if (event.touches.length < 2) pinch = null; };
    svg.addEventListener('touchend', endPinch);
    svg.addEventListener('touchcancel', endPinch);
  }
  async function load() {
    if (loading || svg) return;
    loading = true;
    status.textContent = '地図を読み込んでいます…';
    try {
      map = await window.JourneyAtlasWorldMap.load();
      buildMap();
      buildPicker();
      paint();
      renderCountries();
      status.textContent = '';
    } catch {
      status.textContent = '地図を読み込めませんでした。時間をおいてお試しください。';
    } finally { loading = false; }
  }
  // Older links and bookmarks pointed at the map section.
  const url = new URL(location.href);
  if (url.searchParams.get('map') === 'mine') {
    url.searchParams.delete('map');
    url.hash = 'my-atlas';
    history.replaceState(history.state, '', url);
    disclosure.open = true;
    disclosure.scrollIntoView();
  }
  disclosure.addEventListener('toggle', () => { if (disclosure.open) load(); });
  // Sections above finish laying out after the browser's own jump to #my-atlas.
  if (disclosure.open) {
    let userMoved = false;
    ['wheel', 'touchstart', 'keydown'].forEach(type => window.addEventListener(type, () => { userMoved = true; }, {once: true, passive: true}));
    const settle = () => { if (!userMoved) disclosure.scrollIntoView({behavior: 'instant'}); };
    load().then(settle);
    [600, 1500].forEach(delay => setTimeout(settle, delay));
  }
  window.addEventListener('storage', event => {
    if (svg && (event.key === null || event.key.startsWith('journey-atlas:visited:') || event.key.startsWith('journey-atlas:wish:'))) {
      paint();
      renderCountries();
    }
  });
})();
