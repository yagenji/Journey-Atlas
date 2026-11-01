(() => {
  const root = document.querySelector('.map-explorer');
  if (!root) return;

  const q = s => root.querySelector(s);
  const tabs = [...root.querySelectorAll('[data-map-tab]')];
  const bar = q('.map-region-tabs');
  const wrap = q('.atlas-map-wrap');
  const kicker = q('#map-region-kicker');
  const title = q('#map-region-title');
  const copy = q('#map-region-copy');
  const count = q('#map-region-count');
  const list = q('#map-region-list');
  const status = q('#map-country-status');
  const head = q('.map-heading p');

  // Touch screens: no hover/wheel, and one-finger drag scrolls the page, so describe the controls that actually work.
  const TOUCH = window.matchMedia?.('(hover: none) and (pointer: coarse)').matches;
  const HOW = TOUCH ? '地図は2本指で移動・拡大できます（＋ / − でも拡大縮小）。' : '地図は − / ＋・ホイール・ドラッグで自由に操作できます。';
  const NS = 'http://www.w3.org/2000/svg';
  const WORLD = [0, 0, 1000, 507.209];
  const RATIO = WORLD[3] / WORLD[2];
  const MINW = 4.5;
  const MAP_MIN_X = -80;
  const MAP_MAX_X = 1120;
  const MAP = 'assets/maps/world-states.svg?v=20261003-1';
  const COLORS = {
    asia: '#a9bea4', europe: '#d2b98a', africa: '#d19a75',
    'north-america': '#abc5c9', 'south-america': '#aabb83',
    oceania: '#7fb4b0', antarctica: '#dcecef'
  };

  const REGION_OVERVIEW = {
    europe: { view: [405, 14, 305, 154.698745] },
    // Alaska to Panama and the Lesser Antilles (Central America and the Caribbean are in this region)
    'north-america': { view: [-50, 6, 465, 235.852185] },
    oceania: {
      codes: ['AU', 'NZ', 'PG', 'FJ', 'SB', 'VU'],
      padding: 0.045, min: 195
    }
  };
  const SUB_OVERVIEW = {
    'western-europe': { view: [432, 78, 120, 60.86508] },
    'southern-europe': { padding: 0.035, min: 50 },
    'eastern-europe': { codes: ['BY','BG','CZ','HU','MD','PL','RO','SK','UA'], padding: 0.03, min: 58 },
    'northern-north-america': { view: [-30, 0, 425, 215.563825] },
    micronesia: { view: [835, 185, 215, 109.05] }
  };

  let regions = [], dest = [];
  let byIso = new Map(), regIso = new Map(), subIso = new Map(), subs = new Map();
  let groups = new Map(), wrapGroups = new Map(), nav = new Map();
  let svg, tip, pin, subbar;
  let activeR = 'world', activeS = null, selected = null, anim = null, drag = null;
  let restoring = true;

  function S(t, a = {}) {
    const n = document.createElementNS(NS, t);
    for (const [k, v] of Object.entries(a)) n.setAttribute(k, v);
    return n;
  }
  function region(id) { return regions.find(r => r.id === id); }
  // Atlas page order (atlas-order.js): chapters = subregions, A–Z inside, as on Country pages.
  let book = null;
  function atlasBook() {
    if (!book && window.JourneyAtlasOrder && regions.length && dest.length) book = window.JourneyAtlasOrder.build({ regions }, { destinations: dest });
    return book;
  }
  function bookPage(c) { return atlasBook()?.bySlug.get(c.slug) || null; }
  function chapterGroups(items) {
    const b = atlasBook();
    if (!b) return null;
    const groups = new Map();
    items.forEach(c => {
      const page = b.bySlug.get(c.slug);
      if (!page) return;
      if (!groups.has(page.chapter)) groups.set(page.chapter, []);
      groups.get(page.chapter).push(page);
    });
    if (!groups.size) return null;
    const pagesOnly = [...groups.entries()].sort((x, y) => x[0].first - y[0].first)
      .map(([chapter, pages]) => ({ chapter, items: pages.sort((x, y) => x.folio - y.folio).map(p => items.find(c => c.slug === p.slug)) }));
    const missing = items.filter(c => !b.bySlug.get(c.slug));
    if (missing.length) pagesOnly.push({ chapter: { label: 'その他', first: '', last: '' }, items: missing });
    return pagesOnly;
  }
  function countries(codes = []) {
    const s = new Set(codes);
    return dest.filter(c => s.has(c.iso2)).sort((a, b) => a.nameJa.localeCompare(b.nameJa, 'ja'));
  }
  function lookup() {
    regions.forEach(r => {
      (r.iso2 || []).forEach(i => regIso.set(i, r.id));
      (r.subregions || []).forEach(s => {
        subs.set(s.id, { ...s, regionId: r.id });
        (s.iso2 || []).forEach(i => subIso.set(i, s.id));
      });
    });
  }

  function ensureSub() {
    if (subbar) return;
    subbar = document.createElement('div');
    subbar.className = 'map-subregion-tabs';
    bar.after(subbar);
  }
  function renderSub(r) {
    ensureSub();
    const a = r?.subregions || [];
    subbar.hidden = !a.length;
    subbar.innerHTML = a.length
      ? '<span class="map-subregion-tabs__guide">さらに拡大</span>' + a.map(s => `<button type="button" data-s="${s.id}" class="${activeS === s.id ? 'is-active' : ''}">${s.label}</button>`).join('')
      : '';
    subbar.querySelectorAll('[data-s]').forEach(b => b.onclick = () => setSub(b.dataset.s));
  }

  function right(codes, picked) {
    nav = new Map();
    const a = countries(codes);
    const selectedCard = picked ? `
      <div class="map-country-nav__selected">
        <span class="map-country-nav__selected-flag">${picked.flag}</span>
        <div class="map-country-nav__selected-names"><strong>${picked.nameJa}</strong><span>${picked.nameEn}</span></div>
        ${picked.atlasPublished && picked.href ? `<a class="map-country-nav__selected-link" href="${picked.href}">見る ›</a>` : '<span class="map-country-nav__selected-waiting">COMING SOON</span>'}
        <button type="button" class="map-country-nav__clear" data-clear-selection>× 選択解除</button>
      </div>` : '';

    list.className = 'map-country-nav';
    const item = c => {
      const cls = `map-country-nav__item ${picked?.iso2 === c.iso2 ? 'is-selected' : ''}`;
      const page = bookPage(c);
      const folio = page ? `<span class="map-country-nav__folio" aria-label="${page.folio}ページ">p.${page.folio}</span>` : '';
      const inner = `<span class="map-country-nav__flag">${c.flag}</span><span class="map-country-nav__names"><strong>${c.nameJa}</strong><small>${c.nameEn}</small></span>${folio}`;
      // Published countries are plain links: one click opens the page (new tab via Ctrl/Cmd/middle-click works natively).
      return c.atlasPublished && c.href
        ? `<a href="${c.href}" data-n="${c.iso2}" class="${cls}">${inner}</a>`
        : `<button type="button" data-n="${c.iso2}" class="${cls}">${inner}</button>`;
    };
    // The list doubles as the atlas's table of contents: countries in page order, under the same
    // chapter headings (東アジア, 東南アジア …) that Country pages turn through.
    const groups = chapterGroups(a);
    const rows = groups
      ? groups.map(g => `<div class="map-country-nav__chapter"><span>${g.chapter.label}</span><small>${g.chapter.first === g.chapter.last ? g.chapter.first : `${g.chapter.first}–${g.chapter.last}`}</small></div>${g.items.map(item).join('')}`).join('')
      : a.map(item).join('');
    list.innerHTML = `<div class="map-country-nav__wrap">${selectedCard}<div class="map-country-nav__guide"><strong>国・地域</strong><span>地図と連動します</span></div><div class="map-country-nav__list">${rows}</div></div>`;
    list.querySelector('[data-clear-selection]')?.addEventListener('click', deselect);
    list.querySelectorAll('[data-n]').forEach(b => {
      nav.set(b.dataset.n, b);
      b.onmouseenter = () => hover(b.dataset.n, 1);
      b.onmouseleave = () => hover(b.dataset.n, 0);
      b.onfocus = () => hover(b.dataset.n, 1);
      b.onblur = () => hover(b.dataset.n, 0);
      if (b.tagName === 'BUTTON') b.onclick = () => select(b.dataset.n);
    });
  }
  function worldPanel() {
    kicker.textContent = 'WORLD';
    title.textContent = '世界';
    copy.textContent = `地域を選ぶと、その地域の国・地域が一覧で表示されます。${HOW}`;
    count.textContent = `${dest.length || 202} DESTINATIONS`;
    status.textContent = '';
    // World view: the panel lists the regions themselves so it is never an empty dead end.
    list.className = 'map-country-nav map-world-regions';
    list.innerHTML = `<div class="map-country-nav__wrap"><div class="map-country-nav__guide"><strong>地域</strong><span>選ぶと地図が寄ります</span></div><div class="map-country-nav__list map-world-regions__list">${regions.map(r => `<button type="button" data-world-region="${r.id}" class="map-country-nav__item map-world-regions__item"><span class="map-country-nav__names"><strong>${r.label}</strong><small>${r.labelEn}</small></span><span class="map-world-regions__count">${countries(r.iso2).length}</span></button>`).join('')}</div></div>`;
    list.querySelectorAll('[data-world-region]').forEach(b => {
      const r = region(b.dataset.worldRegion);
      const on = () => { if (activeR === 'world') focus(r?.iso2); };
      const off = () => { if (activeR === 'world') focus(); };
      b.onmouseenter = on; b.onfocus = on;
      b.onmouseleave = off; b.onblur = off;
      b.onclick = () => setRegion(b.dataset.worldRegion);
    });
    renderSub(null);
  }
  function panel(r, s = null, p = null) {
    const codes = s ? s.iso2 : r.iso2;
    kicker.textContent = s ? `${r.labelEn} / ${s.labelEn}` : r.labelEn;
    title.textContent = s ? s.label : r.label;
    copy.textContent = `${HOW}小さな国や島は、さらに拡大すると国土そのものが見えます。`;
    count.textContent = `${countries(codes).length} DESTINATIONS`;
    status.textContent = p ? `${p.nameJa}を選択中` : '';
    right(codes, p);
    renderSub(r);
  }
  function setTabs(id) {
    tabs.forEach(b => {
      const on = b.dataset.mapTab === id;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-pressed', on);
    });
  }

  function view() { return svg ? svg.getAttribute('viewBox').split(/\s+/).map(Number) : WORLD.slice(); }
  function clamp(v) {
    let [x, y, w] = v;
    w = Math.max(MINW, Math.min(1000, w));
    const h = w * RATIO;
    x = Math.max(MAP_MIN_X, Math.min(MAP_MAX_X - w, x));
    y = Math.max(-10, Math.min(517.209 - h, y));
    return [x, y, w, h];
  }
  function apply(v) {
    if (!svg) return;
    svg.setAttribute('viewBox', clamp(v).join(' '));
    requestAnimationFrame(placePin);
  }
  function animate(to, d = 350) {
    if (!svg) return;
    if (anim) cancelAnimationFrame(anim);
    const from = view(), T = clamp(to), st = performance.now();
    function tick(n) {
      const p = Math.min(1, (n - st) / d), e = 1 - (1 - p) ** 3;
      svg.setAttribute('viewBox', from.map((x, i) => x + (T[i] - x) * e).join(' '));
      placePin();
      if (p < 1) anim = requestAnimationFrame(tick);
    }
    anim = requestAnimationFrame(tick);
  }
  function zoom(f, cx, cy) {
    const v = view();
    const x = cx ?? v[0] + v[2] / 2, y = cy ?? v[1] + v[3] / 2;
    const w = Math.max(MINW, Math.min(1000, v[2] * f)), h = w * RATIO;
    const rx = (x - v[0]) / v[2], ry = (y - v[1]) / v[3];
    apply([x - rx * w, y - ry * h, w, h]);
  }
  function point(x, y) {
    const p = svg.createSVGPoint();
    p.x = x; p.y = y;
    const m = svg.getScreenCTM()?.inverse();
    return m ? p.matrixTransform(m) : null;
  }
  function grp(iso) {
    return (activeS === 'polynesia' || activeS === 'micronesia') && wrapGroups.has(iso)
      ? wrapGroups.get(iso)
      : groups.get(iso);
  }
  function bbox(g) {
    if (g.dataset.bbox) {
      const a = g.dataset.bbox.split(',').map(Number);
      return { x: a[0], y: a[1], width: a[2], height: a[3] };
    }
    const b = g.getBBox(), dx = +(g.dataset.dx || 0);
    return { x: b.x + dx, y: b.y, width: b.width, height: b.height };
  }
  function fit(codes, p = .15, min = 45) {
    const bs = codes.map(grp).filter(Boolean).map(bbox);
    if (!bs.length) return WORLD;
    const l = Math.min(...bs.map(b => b.x)), t = Math.min(...bs.map(b => b.y));
    const r = Math.max(...bs.map(b => b.x + b.width)), bt = Math.max(...bs.map(b => b.y + b.height));
    let w = Math.max((r - l) * (1 + 2 * p), min);
    const h = Math.max((bt - t) * (1 + 2 * p), w * RATIO);
    w = Math.max(w, h / RATIO);
    return clamp([(l + r - w) / 2, (t + bt - w * RATIO) / 2, w, w * RATIO]);
  }
  function tune(v, cfg) {
    if (!cfg || (!cfg.scale && !cfg.shiftX && !cfg.shiftY)) return v;
    const scale = cfg.scale ?? 1;
    const shiftX = cfg.shiftX ?? 0;
    const shiftY = cfg.shiftY ?? 0;
    const cx = v[0] + v[2] / 2 + v[2] * shiftX;
    const cy = v[1] + v[3] / 2 + v[3] * shiftY;
    const w = v[2] * scale, h = w * RATIO;
    return clamp([cx - w / 2, cy - h / 2, w, h]);
  }
  function regionOverview(id) {
    const r = region(id);
    if (!r) return WORLD;
    const cfg = REGION_OVERVIEW[id];
    if (cfg?.view) return clamp(cfg.view);
    const codes = cfg?.codes || r.iso2;
    return tune(fit(codes, cfg?.padding ?? .07, cfg?.min ?? 95), cfg);
  }
  function subOverview(id) {
    const s = subs.get(id);
    if (!s) return regionOverview(activeR);
    const cfg = SUB_OVERVIEW[id];
    if (cfg?.view) return clamp(cfg.view);
    return tune(fit(cfg?.codes || s.iso2, cfg?.padding ?? .08, cfg?.min ?? 26), cfg);
  }
  function currentOverview() {
    if (activeR === 'world') return WORLD;
    return activeS ? subOverview(activeS) : regionOverview(activeR);
  }
  function focus(codes) {
    const s = codes ? new Set(codes) : null;
    groups.forEach((g, iso) => {
      g.classList.toggle('is-muted', !!(s && !s.has(iso)));
      g.classList.toggle('is-in-focus', !!(s && s.has(iso)));
    });
    wrapGroups.forEach((g, iso) => {
      g.classList.toggle('is-muted', !!(s && !s.has(iso)));
      g.classList.toggle('is-in-focus', !!(s && s.has(iso)));
    });
  }
  function clear() {
    if (selected) {
      groups.get(selected)?.classList.remove('is-selected');
      wrapGroups.get(selected)?.classList.remove('is-selected');
    }
    selected = null;
    if (pin) pin.hidden = true;
  }
  function deselect() {
    clear();
    if (activeR === 'world') {
      worldPanel(); animate(WORLD, 260); return;
    }
    const r = region(activeR), s = activeS ? subs.get(activeS) : null;
    panel(r, s, null);
    animate(currentOverview(), 280);
  }
  // Keep the map selection in the URL (?map=asia&sub=…) so Back from a Country page returns here.
  function remember() {
    if (restoring) return;
    const url = new URL(location.href);
    const set = (k, v) => v ? url.searchParams.set(k, v) : url.searchParams.delete(k);
    set('map', mine ? 'mine' : (activeR === 'world' ? '' : activeR));
    set('sub', mine ? '' : (activeS || ''));
    if (url.href !== location.href) history.replaceState(history.state, '', url);
  }
  function setRegion(id, motion = true) {
    if (mine) leaveMine();
    activeR = id; activeS = null;
    root.dataset.activeRegion = id;
    delete root.dataset.activeSubregion;
    clear(); setTabs(id);
    if (id === 'world') {
      focus(); motion ? animate(WORLD) : apply(WORLD); worldPanel(); remember(); return;
    }
    const r = region(id);
    if (!r) return;
    focus(r.iso2);
    const v = regionOverview(id);
    motion ? animate(v) : apply(v);
    panel(r);
    remember();
  }
  function setSub(id) {
    const s = subs.get(id);
    if (!s) return;
    activeR = s.regionId; activeS = id;
    root.dataset.activeRegion = activeR;
    root.dataset.activeSubregion = id;
    clear(); setTabs(activeR); focus(s.iso2);
    panel(region(activeR), s);
    animate(subOverview(id), 420);
    remember();
  }

  // ---------- わたしの地図: visited / wished countries, stored in this browser only ----------
  let mine = false, mineBtn = null, mineQuery = '', mineVisitedOnly = false;
  const VKEY = slug => `journey-atlas:visited:${slug}`;
  const WKEY = slug => `journey-atlas:wish:${slug}`;
  const flag = key => { try { return localStorage.getItem(key) === 'true'; } catch { return false; } };
  const isVisited = c => flag(VKEY(c.slug));
  const isWished = c => flag(WKEY(c.slug));
  function paintMine() {
    groups.forEach((g, iso) => {
      const c = byIso.get(iso);
      const v = mine && c && isVisited(c), w = mine && c && !v && isWished(c);
      g.classList.toggle('is-visited', !!v); g.classList.toggle('is-wished', !!w);
      if (c) g.setAttribute('aria-label', mine ? `${c.nameJa}：${v ? '行った国（選ぶと外す）' : '行った国にする'}` : (c.href ? `${c.nameJa}のページを開く` : `${c.nameJa}を選ぶ`));
      wrapGroups.get(iso)?.classList.toggle('is-visited', !!v);
      wrapGroups.get(iso)?.classList.toggle('is-wished', !!w);
    });
  }
  function toggleVisited(c) {
    const on = !isVisited(c);
    try { on ? localStorage.setItem(VKEY(c.slug), 'true') : localStorage.removeItem(VKEY(c.slug)); }
    catch {
      minePanel();
      status.textContent = '記録を保存できませんでした。ブラウザの保存設定をご確認ください。';
      return;
    }
    paintMine(); minePanel();
    status.textContent = on ? `${c.nameJa}を「行った国」にしました` : `${c.nameJa}の印を外しました`;
  }
  const mineSearchText = value => String(value || '').normalize('NFKC').toLowerCase().replace(/macao/g, 'macau');
  function renderMineCountries() {
    const rows = list.querySelector('.map-mine__countries');
    if (!rows) return;
    const activeSlug = rows.contains(document.activeElement) ? document.activeElement.dataset.visitedSlug : null;
    const scrollTop = rows.scrollTop;
    const query = mineSearchText(mineQuery).trim();
    const countries = dest.filter(c => (!mineVisitedOnly || isVisited(c)) && mineSearchText(`${c.nameJa} ${c.nameEn} ${c.slug} ${c.iso2}`).includes(query))
      .sort((a, b) => a.nameEn.localeCompare(b.nameEn, 'en', { sensitivity: 'base' }));
    rows.innerHTML = countries.map(c => `<div class="map-mine__item"><label class="map-mine__choice"><input type="checkbox" data-visited-slug="${c.slug}" aria-label="${c.nameJa}を行った国・地域にする"${isVisited(c) ? ' checked' : ''}><span class="map-country-nav__flag" aria-hidden="true">${c.flag}</span><span class="map-country-nav__names"><strong>${c.nameJa}</strong><small>${c.nameEn}</small></span></label>${c.href ? `<a class="map-mine__country-link" href="${c.href}" aria-label="${c.nameJa}のページを開く">↗</a>` : ''}</div>`).join('');
    list.querySelector('.map-mine__result-count').textContent = `${countries.length}件の国・地域`;
    const empty = list.querySelector('.map-mine__no-results');
    empty.hidden = countries.length > 0;
    empty.textContent = mineVisitedOnly && !query ? '行った国・地域はまだありません。「行った国・地域だけ表示」を外して追加できます。' : '該当する国・地域がありません。';
    rows.scrollTop = scrollTop;
    if (activeSlug) (rows.querySelector(`[data-visited-slug="${activeSlug}"]`) || list.querySelector('[data-mine-filter]')).focus({ preventScroll: true });
  }
  function minePanel() {
    const visited = dest.filter(isVisited).sort((a, b) => a.nameEn.localeCompare(b.nameEn, 'en', { sensitivity: 'base' }));
    const wished = dest.filter(c => !isVisited(c) && isWished(c)).sort((a, b) => a.nameEn.localeCompare(b.nameEn, 'en', { sensitivity: 'base' }));
    kicker.textContent = 'MY ATLAS';
    title.textContent = 'わたしの地図';
    copy.textContent = '国名で検索し、一覧にチェックして「行った国・地域」を記録できます。地図からも選べます。記録はこのブラウザにだけ保存されます。';
    count.textContent = `${visited.length} / ${dest.length} VISITED`;
    const item = c => `<a class="map-country-nav__item" href="${c.href || '#'}"><span class="map-country-nav__flag">${c.flag}</span><span class="map-country-nav__names"><strong>${c.nameJa}</strong><small>${c.nameEn}</small></span></a>`;
    const block = (label, note, rows, empty) => `<div class="map-country-nav__guide"><strong>${label}</strong><span>${note}</span></div>${rows.length ? `<div class="map-country-nav__list">${rows.map(item).join('')}</div>` : `<p class="map-mine__empty">${empty}</p>`}`;
    if (!list.querySelector('.map-mine__countries')) {
      list.className = 'map-country-nav map-mine';
      list.innerHTML = `<div class="map-country-nav__wrap"><label class="map-mine__search"><span>行った国・地域を選ぶ</span><input type="search" aria-label="行った国・地域を検索" placeholder="国・地域名で検索（例：マカオ）" autocomplete="off"></label><label class="map-mine__filter"><input type="checkbox" data-mine-filter>行った国・地域だけ表示</label><p class="map-mine__result-count" aria-live="polite"></p><div class="map-mine__countries" role="group" aria-label="行った国・地域の選択"></div><p class="map-mine__no-results map-mine__empty" hidden></p><div class="map-mine__wishes"></div><button type="button" class="map-mine__exit">地図に戻る</button></div>`;
      const search = list.querySelector('input[type="search"]');
      search.value = mineQuery;
      search.oninput = () => { mineQuery = search.value; list.querySelector('.map-mine__countries').scrollTop = 0; renderMineCountries(); };
      const filter = list.querySelector('[data-mine-filter]');
      filter.checked = mineVisitedOnly;
      filter.onchange = () => { mineVisitedOnly = filter.checked; list.querySelector('.map-mine__countries').scrollTop = 0; renderMineCountries(); };
      list.querySelector('.map-mine__countries').onchange = event => {
        const c = dest.find(c => c.slug === event.target.dataset.visitedSlug);
        if (c) toggleVisited(c);
      };
      list.querySelector('.map-mine__exit').onclick = () => setRegion('world');
    }
    renderMineCountries();
    list.querySelector('.map-mine__wishes').innerHTML = block('行ってみたい国', `${wished.length}か国`, wished, '国ページの「行ってみたい」で追加できます。');
    renderSub(null);
  }
  const HINT_MINE = TOUCH ? '国をタップで「行った国」に印 ・ 2本指で移動・拡大' : '国をクリックで「行った国」に印 ・ ホイールで拡大縮小 ・ ドラッグで移動';
  let hintDefault = '';
  function setHint(on) {
    const h = wrap.querySelector('.map-hint');
    if (!h) return;
    if (!hintDefault) hintDefault = h.textContent;
    h.textContent = on ? HINT_MINE : hintDefault;
  }
  function enterMine() {
    mine = true; root.classList.add('is-mine'); setHint(true);
    mineBtn?.setAttribute('aria-pressed', 'true');
    activeR = 'world'; activeS = null; root.dataset.activeRegion = 'world'; delete root.dataset.activeSubregion;
    clear(); setTabs(''); focus(); animate(WORLD, 300);
    paintMine(); minePanel(); remember();
  }
  function leaveMine() {
    mine = false; root.classList.remove('is-mine'); setHint(false);
    mineBtn?.setAttribute('aria-pressed', 'false');
    paintMine();
  }
  function mineControl() {
    mineBtn = document.createElement('button');
    mineBtn.type = 'button';
    mineBtn.className = 'map-mine-toggle';
    mineBtn.setAttribute('aria-pressed', 'false');
    mineBtn.textContent = 'わたしの地図';
    mineBtn.onclick = () => mine ? setRegion('world') : enterMine();
    bar.append(mineBtn);
    status.setAttribute('role', 'status');
  }
  window.addEventListener('storage', event => {
    if (mine && (event.key === null || event.key.startsWith('journey-atlas:visited:') || event.key.startsWith('journey-atlas:wish:'))) {
      paintMine(); minePanel();
    }
  });
  function select(iso) {
    const c = byIso.get(iso);
    if (!c) return;
    const rid = regIso.get(iso), sid = subIso.get(iso);
    const r = region(rid), s = sid ? subs.get(sid) : null;
    if (!r) return;
    const g = ((sid === 'polynesia' || sid === 'micronesia') && wrapGroups.has(iso))
      ? wrapGroups.get(iso)
      : groups.get(iso);

    activeR = rid; activeS = sid || null;
    root.dataset.activeRegion = rid;
    if (sid) root.dataset.activeSubregion = sid; else delete root.dataset.activeSubregion;
    setTabs(rid);
    focus(s ? s.iso2 : r.iso2);
    clear(); selected = iso;
    panel(r, s, c);

    if (!g) {
      animate(s ? subOverview(sid) : regionOverview(rid), 280);
      return;
    }

    groups.get(iso)?.classList.add('is-selected');
    wrapGroups.get(iso)?.classList.add('is-selected');
    const b = bbox(g), w = Math.max(Math.max(b.width, b.height / RATIO) * 3.2, 9), h = w * RATIO;
    animate([b.x + b.width / 2 - w / 2, b.y + b.height / 2 - h / 2, w, h], 340);
    requestAnimationFrame(placePin);
  }
  function hover(iso, on) {
    groups.get(iso)?.classList.toggle('is-hovered', !!on);
    wrapGroups.get(iso)?.classList.toggle('is-hovered', !!on);
    nav.get(iso)?.classList.toggle('is-hovered', !!on);
  }
  function bind(g, c) {
    if (!c) return;
    g.tabIndex = 0;
    g.setAttribute('role', 'button');
    g.setAttribute('aria-label', c.href ? `${c.nameJa}のページを開く` : `${c.nameJa}を選ぶ`);
    g.onpointerenter = e => {
      hover(c.iso2, 1);
      tip.innerHTML = `<strong>${c.nameJa}</strong><span>${c.nameEn}</span>`;
      tip.hidden = false; moveTip(e);
    };
    g.onpointermove = moveTip;
    g.onpointerleave = () => { hover(c.iso2, 0); tip.hidden = true; };
    // Clicking a country on the map opens its page directly (no second step via the side panel).
    g.onclick = e => { e.stopPropagation(); open(c, e); };
    g.onauxclick = e => { if (e.button === 1) { e.preventDefault(); open(c, e); } };
    g.onkeydown = e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(c, e); }
    };
  }
  function open(c, e) {
    if (mine) { toggleVisited(c); return; }
    if (!(c.atlasPublished && c.href)) { select(c.iso2); return; }
    if (e && (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1)) {
      window.open(c.href, '_blank', 'noopener');
      return;
    }
    location.href = c.href;
  }
  function moveTip(e) {
    const r = wrap.getBoundingClientRect();
    tip.style.transform = `translate(${Math.min(r.width - 145, Math.max(12, e.clientX - r.left + 12))}px,${Math.min(r.height - 55, Math.max(12, e.clientY - r.top + 12))}px)`;
  }
  function clean(src, iso, c) {
    const g = document.importNode(src, true);
    g.removeAttribute('id');
    g.querySelectorAll('text,title,desc,defs,style,[fill-opacity="0"],[opacity="0"]').forEach(n => n.remove());
    g.querySelectorAll('[id]').forEach(n => {
      if ((n.id || '').endsWith('_')) n.remove(); else n.removeAttribute('id');
    });
    const parts = [...g.querySelectorAll('path,polygon,polyline,circle,ellipse,rect')];
    if (!parts.length) return null;
    g.querySelectorAll('*').forEach(n => {
      ['fill', 'stroke', 'stroke-width', 'stroke-miterlimit', 'style', 'class'].forEach(a => n.removeAttribute(a));
    });
    g.classList.add('ja-country');
    g.dataset.iso = iso;
    if (!c) { g.classList.add('is-outside'); return g; }
    g.classList.add('is-destination');
    g.dataset.region = regIso.get(iso) || 'world';
    g.style.setProperty('--fill', COLORS[g.dataset.region] || '#cbd4cf');
    bind(g, c);
    return g;
  }

  function geometryBoxes(g) {
    const out = [];
    g.querySelectorAll('path,polygon,polyline,circle,ellipse,rect').forEach(el => {
      try {
        const b = el.getBBox();
        if (Number.isFinite(b.x) && Number.isFinite(b.y) && b.width >= 0 && b.height >= 0) out.push({ el, b });
      } catch (_) {}
    });
    return out;
  }
  function unionBoxes(boxes) {
    if (!boxes.length) return null;
    const l = Math.min(...boxes.map(b => b.x)), t = Math.min(...boxes.map(b => b.y));
    const r = Math.max(...boxes.map(b => b.x + b.width)), bt = Math.max(...boxes.map(b => b.y + b.height));
    return { x: l, y: t, width: r - l, height: bt - t };
  }
  function normalizedDatelineBBox(g) {
    const boxes = geometryBoxes(g).map(({ b }) => {
      const cx = b.x + b.width / 2;
      return { x: cx < 250 ? b.x + 1000 : b.x, y: b.y, width: b.width, height: b.height };
    });
    return unionBoxes(boxes);
  }
  function makeDatelineClone(iso, source) {
    const boxes = geometryBoxes(source);
    const left = boxes.filter(({ b }) => b.x + b.width / 2 < 250);
    if (!left.length) return null;
    const c = S('g', { class: 'ja-country is-destination ja-wrap' });
    c.dataset.iso = iso;
    c.dataset.region = regIso.get(iso) || 'oceania';
    c.style.setProperty('--fill', COLORS[c.dataset.region] || '#cbd4cf');
    left.forEach(({ el }) => {
      const shell = S('g', { transform: 'translate(1000 0)' });
      shell.append(el.cloneNode(true));
      c.append(shell);
    });
    const nb = normalizedDatelineBBox(source);
    if (nb) c.dataset.bbox = `${nb.x},${nb.y},${nb.width},${nb.height}`;
    bind(c, byIso.get(iso));
    return c;
  }
  function wrapDateline() {
    const ids = new Set([...(subs.get('polynesia')?.iso2 || []), ...(subs.get('micronesia')?.iso2 || [])]);
    ids.forEach(iso => {
      const b = groups.get(iso);
      if (!b) return;
      const bb = b.getBBox();
      const spansDateline = bb.width > 400;
      const sitsAtLeftEdge = bb.x + bb.width / 2 < 100;
      if (!spansDateline && !sitsAtLeftEdge) return;
      const c = makeDatelineClone(iso, b);
      if (!c) return;
      wrapGroups.set(iso, c);
      svg.querySelector('.ja-wrap-layer').append(c);
    });
  }

  function controls() {
    const z = document.createElement('div');
    z.className = 'map-zoom-controls ja-controls';
    z.innerHTML = '<button type="button" data-z="in" aria-label="拡大">＋</button><button type="button" data-z="out" aria-label="縮小">−</button><button type="button" data-z="reset" aria-label="表示を戻す">↺</button>';
    z.querySelector('[data-z="out"]').onclick = () => zoom(1.45);
    z.querySelector('[data-z="in"]').onclick = () => zoom(.69);
    z.querySelector('[data-z="reset"]').onclick = () => animate(currentOverview(), 250);
    wrap.append(z);
  }
  function gestures() {
    svg.onwheel = e => {
      e.preventDefault();
      const p = point(e.clientX, e.clientY);
      zoom(e.deltaY < 0 ? .8 : 1.23, p?.x, p?.y);
    };
    svg.onpointerdown = e => {
      if (e.pointerType === 'touch' || e.target.closest?.('.is-destination')) return;
      drag = { id: e.pointerId, x: e.clientX, y: e.clientY, v: view() };
      svg.setPointerCapture?.(e.pointerId);
      svg.classList.add('is-dragging');
    };
    svg.onpointermove = e => {
      if (!drag || drag.id !== e.pointerId) return;
      const r = svg.getBoundingClientRect(), dx = e.clientX - drag.x, dy = e.clientY - drag.y, v = drag.v;
      apply([v[0] - dx / r.width * v[2], v[1] - dy / r.height * v[3], v[2], v[3]]);
    };
    const end = e => {
      if (drag && drag.id === e.pointerId) { drag = null; svg.classList.remove('is-dragging'); }
    };
    svg.onpointerup = end; svg.onpointercancel = end;

    // Touch: one finger keeps scrolling the page; two fingers pan and pinch the map.
    svg.style.touchAction = 'pan-x pan-y';
    let pinch = null;
    const mid = t => ({ x: (t[0].clientX + t[1].clientX) / 2, y: (t[0].clientY + t[1].clientY) / 2 });
    const dist = t => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY) || 1;
    svg.addEventListener('touchstart', e => {
      if (e.touches.length !== 2) { pinch = null; return; }
      e.preventDefault();
      if (anim) cancelAnimationFrame(anim);
      const m = mid(e.touches);
      pinch = { v: view(), d: dist(e.touches), p: point(m.x, m.y) };
    }, { passive: false });
    svg.addEventListener('touchmove', e => {
      if (!pinch || e.touches.length !== 2) return;
      e.preventDefault();
      const m = mid(e.touches);
      const w = Math.max(MINW, Math.min(1000, pinch.v[2] * pinch.d / dist(e.touches))), h = w * RATIO;
      apply([pinch.v[0], pinch.v[1], w, h]);
      const q = point(m.x, m.y);
      if (q && pinch.p) {
        const v = view();
        apply([v[0] + pinch.p.x - q.x, v[1] + pinch.p.y - q.y, v[2], v[3]]);
      }
    }, { passive: false });
    const stop = e => { if (e.touches.length < 2) pinch = null; };
    svg.addEventListener('touchend', stop);
    svg.addEventListener('touchcancel', stop);
  }
  // A point on the country's main landmass: the bbox centre can fall in the sea
  // when outlying islands widen the bbox (e.g. Taiwan with Kinmen and Matsu).
  const anchors = new Map();
  function anchor(g) {
    const key = g.dataset.iso + ':' + (g.dataset.dx || 0);
    if (anchors.has(key)) return anchors.get(key);
    let result = null;
    try {
      const shapes = [...g.querySelectorAll('path,polygon,rect,circle,ellipse')].filter(e => e.isPointInFill);
      const bb = g.getBBox(), dx = +(g.dataset.dx || 0), n = 24, pts = [];
      const q = svg.createSVGPoint();
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
        q.x = bb.x + bb.width * (i + .5) / n; q.y = bb.y + bb.height * (j + .5) / n;
        if (shapes.some(e => e.isPointInFill(q))) pts.push([i, j, q.x, q.y]);
      }
      if (pts.length) {
        const cx = bb.x + bb.width / 2, cy = bb.y + bb.height / 2;
        const centre = pts.find(t => Math.abs(t[2] - cx) <= bb.width / n && Math.abs(t[3] - cy) <= bb.height / n);
        let best = centre, score = -1;
        if (!best) for (const t of pts) {
          const c = pts.filter(u => Math.abs(u[0] - t[0]) <= 3 && Math.abs(u[1] - t[1]) <= 3).length;
          if (c > score) { score = c; best = t; }
        }
        result = { x: best[2] + dx, y: best[3] };
      }
    } catch (e) { result = null; }
    anchors.set(key, result);
    return result;
  }
  function placePin() {
    if (!pin || !selected || !svg) { if (pin) pin.hidden = true; return; }
    const g = grp(selected);
    if (!g) { pin.hidden = true; return; }
    const b = bbox(g), p = svg.createSVGPoint(), a = anchor(g);
    p.x = a ? a.x : b.x + b.width / 2; p.y = a ? a.y : b.y + b.height / 2;
    const m = svg.getScreenCTM();
    if (!m) return;
    const s = p.matrixTransform(m), r = wrap.getBoundingClientRect();
    pin.style.left = `${s.x - r.left}px`;
    pin.style.top = `${s.y - r.top}px`;
    pin.hidden = false;
  }
  function style() {
    const s = document.createElement('style');
    const geom = '.ja-country path,.ja-country polygon,.ja-country polyline,.ja-country circle,.ja-country ellipse,.ja-country rect';
    s.textContent = `
      #map ${geom}{fill:var(--fill,#d7dfda)!important;stroke:#fffaf1!important;stroke-width:.5!important;vector-effect:non-scaling-stroke}
      #map .ja-country.is-outside path,#map .ja-country.is-outside polygon,#map .ja-country.is-outside polyline,#map .ja-country.is-outside circle,#map .ja-country.is-outside ellipse,#map .ja-country.is-outside rect{fill:#dfe7e3!important;opacity:.25}
      #map .ja-country.is-muted{opacity:.12}
      #map .ja-country.is-destination{cursor:pointer;outline:none}
      #map .ja-country.is-destination:hover path,#map .ja-country.is-destination:hover polygon,#map .ja-country.is-destination:hover polyline,#map .ja-country.is-destination:hover circle,#map .ja-country.is-destination:hover ellipse,#map .ja-country.is-destination:hover rect,
      #map .ja-country.is-hovered path,#map .ja-country.is-hovered polygon,#map .ja-country.is-hovered polyline,#map .ja-country.is-hovered circle,#map .ja-country.is-hovered ellipse,#map .ja-country.is-hovered rect,
      #map .ja-country:focus path,#map .ja-country:focus polygon,#map .ja-country:focus polyline,#map .ja-country:focus circle,#map .ja-country:focus ellipse,#map .ja-country:focus rect{fill:#e7c585!important;opacity:1}
      #map .ja-country.is-selected path,#map .ja-country.is-selected polygon,#map .ja-country.is-selected polyline,#map .ja-country.is-selected circle,#map .ja-country.is-selected ellipse,#map .ja-country.is-selected rect{fill:#e0aa59!important;stroke:#fff7e8!important;stroke-width:1!important;vector-effect:non-scaling-stroke}
      #map .ja-wrap{display:none}
      #map[data-active-subregion="polynesia"] .ja-wrap,#map[data-active-subregion="micronesia"] .ja-wrap{display:block}
      .ja-controls{position:absolute!important;left:22px!important;top:20px!important;z-index:20!important;display:grid!important;grid-template-columns:36px 36px 36px!important;width:108px!important;height:34px!important;overflow:hidden!important;border:1px solid rgba(34,66,82,.18)!important;border-radius:10px!important;background:#fffdf8!important;box-shadow:0 4px 14px #29465e22!important}
      .ja-controls button{display:grid!important;place-items:center!important;width:36px!important;height:34px!important;min-width:36px!important;margin:0!important;padding:0!important;border:0!important;border-right:1px solid #29465e1c!important;border-radius:0!important;background:transparent!important;color:#29465e!important;font:600 17px/1 sans-serif!important;visibility:visible!important;opacity:1!important}
      .ja-controls button:last-child{border-right:0!important;font-size:14px!important}
      .map-selection-pin{position:absolute;z-index:21;width:22px;height:27px;font-size:21px;line-height:1;transform:translate(-50%,-92%);pointer-events:none;user-select:none}
      .map-selection-pin[hidden]{display:none!important}
      .map-country-nav__selected{grid-template-columns:34px minmax(0,1fr) auto!important}
      .map-country-nav__clear{grid-column:1/-1;justify-self:end;margin-top:2px;padding:4px 7px;border:0;border-radius:6px;background:transparent;color:#7b746b;font:600 8.5px/1.2 var(--jp);cursor:pointer}
      .map-country-nav__clear:hover,.map-country-nav__clear:focus{background:rgba(35,72,102,.07);color:#29465e;outline:none}
      .country-fallback-pin,.country-focus-pin{display:none!important}`;
    document.head.append(s);
  }
  function build(mapText) {
    const doc = new DOMParser().parseFromString(mapText, 'image/svg+xml');
    const map = S('svg', {
      class: 'atlas-country-map', viewBox: WORLD.join(' '), role: 'img',
      'aria-label': '拡大すると小さな島まで見える世界地図', preserveAspectRatio: 'xMidYMid meet'
    });
    map.append(S('rect', { x: MAP_MIN_X, y: -10, width: MAP_MAX_X - MAP_MIN_X, height: 530, fill: '#edf6f3', class: 'country-map-ocean' }));
    const land = S('g', { class: 'country-map-layer' }), wl = S('g', { class: 'ja-wrap-layer' });
    map.append(land, wl); wrap.replaceChildren(map); svg = map;

    [...doc.querySelectorAll('svg > g[id]')].filter(g => /^[A-Z]{2}$/.test(g.id)).forEach(src => {
      const iso = src.id, c = byIso.get(iso), g = clean(src, iso, c);
      if (!g) return;
      land.append(g);
      if (c) groups.set(iso, g);
    });

    wrapDateline();
    tip = document.createElement('div'); tip.className = 'map-tooltip'; tip.hidden = true;
    pin = document.createElement('span'); pin.className = 'map-selection-pin'; pin.textContent = '📍'; pin.hidden = true;
    const h = document.createElement('p'); h.className = 'map-hint'; h.textContent = TOUCH ? '国をタップでページへ ・ 2本指で移動・拡大' : '国をクリックでページへ ・ − / ＋・ホイールで拡大縮小 ・ ドラッグで移動';
    wrap.append(tip, pin, h);
    style(); controls(); gestures(); root.classList.add('has-country-map');
  }

  tabs.forEach(b => b.onclick = () => setRegion(b.dataset.mapTab));
  if (head) head.textContent = '世界から地域へ寄りながら、地図を自由に拡大・移動して次の旅先を見つけよう。';
  window.addEventListener('resize', () => requestAnimationFrame(placePin));

  Promise.all([
    fetch(MAP).then(r => r.text()),
    fetch('data/region-taxonomy.json?v=20260823-0030').then(r => r.json()),
    fetch('data/atlas-destinations.json?v=20260825-0128').then(r => r.json())
  ]).then(([m, rd, core]) => {
    regions = rd.regions || [];
    dest = core.destinations || [];
    byIso = new Map(dest.map(c => [c.iso2, c]));
    lookup(); build(m); mineControl();
    const params = new URLSearchParams(location.search);
    const want = params.get('map'), sub = params.get('sub');
    if (want === 'mine') enterMine();
    else if (sub && subs.has(sub)) { setRegion(subs.get(sub).regionId, false); setSub(sub); }
    else if (want && region(want)) setRegion(want, false);
    else setRegion('world', false);
    restoring = false;
  }).catch(e => {
    console.error('[JOURNEY ATLAS map]', e);
    copy.textContent = '地図データを読み込めませんでした。';
  });
})();
