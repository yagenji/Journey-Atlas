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

  const NS = 'http://www.w3.org/2000/svg';
  const WORLD = [0, 0, 1000, 507.209];
  const RATIO = WORLD[3] / WORLD[2];
  const MINW = 4.5;
  const MAP = 'https://cdn.jsdelivr.net/gh/raphaellepuschitz/SVG-World-Map@master/src/world-states.svg';
  const ANT = 'https://cdn.jsdelivr.net/gh/amcharts/ammap3@master/ammap/maps/svg/worldWithAntarcticaLow.svg';
  const COLORS = {
    asia: '#a9bea4', europe: '#d2b98a', africa: '#d19a75',
    'north-america': '#abc5c9', 'south-america': '#aabb83',
    oceania: '#7fb4b0', antarctica: '#dcecef'
  };

  const REGION_OVERVIEW = {
    europe: { padding: 0.0, min: 72 },
    'north-america': {
      codes: ['CA', 'US', 'MX', 'BZ', 'GT', 'HN', 'SV', 'NI', 'CR', 'PA'],
      padding: 0.025,
      min: 185
    },
    oceania: {
      codes: ['AU', 'NZ', 'PG', 'FJ', 'SB', 'VU'],
      padding: 0.055,
      min: 205
    }
  };
  const SUB_OVERVIEW = {
    'western-europe': { padding: 0.035, min: 34 },
    'southern-europe': { padding: 0.035, min: 50 },
    'eastern-europe': { padding: 0.035, min: 60 },
    'northern-north-america': { padding: 0.025, min: 172 },
    micronesia: { view: [845, 198, 155, 78.617] }
  };

  let regions = [], dest = [];
  let byIso = new Map(), regIso = new Map(), subIso = new Map(), subs = new Map();
  let groups = new Map(), wrapGroups = new Map(), nav = new Map();
  let svg, tip, pin, subbar;
  let activeR = 'world', activeS = null, selected = null, anim = null, drag = null;

  function S(t, a = {}) {
    const n = document.createElementNS(NS, t);
    for (const [k, v] of Object.entries(a)) n.setAttribute(k, v);
    return n;
  }
  function region(id) { return regions.find(r => r.id === id); }
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
    list.innerHTML = `<div class="map-country-nav__wrap">${selectedCard}<div class="map-country-nav__guide"><strong>国・地域</strong><span>地図と連動します</span></div><div class="map-country-nav__list">${a.map(c => `<button type="button" data-n="${c.iso2}" class="map-country-nav__item ${picked?.iso2 === c.iso2 ? 'is-selected' : ''}"><span class="map-country-nav__flag">${c.flag}</span><span class="map-country-nav__names"><strong>${c.nameJa}</strong><small>${c.nameEn}</small></span></button>`).join('')}</div></div>`;
    list.querySelector('[data-clear-selection]')?.addEventListener('click', deselect);
    list.querySelectorAll('[data-n]').forEach(b => {
      nav.set(b.dataset.n, b);
      b.onmouseenter = () => hover(b.dataset.n, 1);
      b.onmouseleave = () => hover(b.dataset.n, 0);
      b.onfocus = () => hover(b.dataset.n, 1);
      b.onblur = () => hover(b.dataset.n, 0);
      b.onclick = () => select(b.dataset.n);
    });
  }
  function worldPanel() {
    kicker.textContent = 'WORLD';
    title.textContent = '世界';
    copy.textContent = '地域を選ぶか、− / ＋やホイールで地図を拡大できます。小さな島も、拡大すると実際の形が見えます。';
    count.textContent = `${dest.length || 199} DESTINATIONS`;
    status.textContent = '';
    list.className = 'map-country-preview';
    list.innerHTML = '<div class="map-country-preview__empty"><span class="map-country-preview__marker">⌖</span><div><strong>地域を選択</strong><p>地域を選ぶか、地図を直接拡大してください。</p></div></div>';
    renderSub(null);
  }
  function panel(r, s = null, p = null) {
    const codes = s ? s.iso2 : r.iso2;
    kicker.textContent = s ? `${r.labelEn} / ${s.labelEn}` : r.labelEn;
    title.textContent = s ? s.label : r.label;
    copy.textContent = '地図は − / ＋・ホイール・ドラッグで自由に操作できます。小さな国や島は、さらに拡大すると国土そのものが見えます。';
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
    x = Math.max(-20, Math.min(1020 - w, x));
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
  function regionOverview(id) {
    const r = region(id);
    if (!r) return WORLD;
    const cfg = REGION_OVERVIEW[id];
    const codes = cfg?.codes || r.iso2;
    return fit(codes, cfg?.padding ?? .07, cfg?.min ?? 95);
  }
  function subOverview(id) {
    const s = subs.get(id);
    if (!s) return regionOverview(activeR);
    const cfg = SUB_OVERVIEW[id];
    if (cfg?.view) return clamp(cfg.view);
    return fit(cfg?.codes || s.iso2, cfg?.padding ?? .08, cfg?.min ?? 26);
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
      worldPanel();
      animate(WORLD, 260);
      return;
    }
    const r = region(activeR), s = activeS ? subs.get(activeS) : null;
    panel(r, s, null);
    animate(currentOverview(), 280);
  }
  function setRegion(id, motion = true) {
    activeR = id; activeS = null;
    root.dataset.activeRegion = id;
    delete root.dataset.activeSubregion;
    clear(); setTabs(id);
    if (id === 'world') {
      focus(); motion ? animate(WORLD) : apply(WORLD); worldPanel(); return;
    }
    const r = region(id);
    if (!r) return;
    focus(r.iso2);
    const v = regionOverview(id);
    motion ? animate(v) : apply(v);
    panel(r);
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
  }
  function select(iso) {
    const c = byIso.get(iso), g = grp(iso);
    if (!c || !g) return;
    const rid = regIso.get(iso), sid = subIso.get(iso);
    activeR = rid; activeS = sid || null;
    root.dataset.activeRegion = rid;
    if (sid) root.dataset.activeSubregion = sid; else delete root.dataset.activeSubregion;
    setTabs(rid);
    focus(sid ? subs.get(sid).iso2 : region(rid).iso2);
    clear(); selected = iso;
    groups.get(iso)?.classList.add('is-selected');
    wrapGroups.get(iso)?.classList.add('is-selected');
    panel(region(rid), sid ? subs.get(sid) : null, c);
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
    g.tabIndex = 0;
    g.setAttribute('role', 'button');
    g.setAttribute('aria-label', `${c.nameJa}を選ぶ`);
    g.onpointerenter = e => {
      hover(c.iso2, 1);
      tip.innerHTML = `<strong>${c.nameJa}</strong><span>${c.nameEn}</span>`;
      tip.hidden = false; moveTip(e);
    };
    g.onpointermove = moveTip;
    g.onpointerleave = () => { hover(c.iso2, 0); tip.hidden = true; };
    g.onclick = e => { e.stopPropagation(); select(c.iso2); };
    g.onkeydown = e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(c.iso2); }
    };
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
  function wrapDateline() {
    const ids = new Set([...(subs.get('polynesia')?.iso2 || []), ...(subs.get('micronesia')?.iso2 || [])]);
    ids.forEach(iso => {
      const b = groups.get(iso);
      if (!b) return;
      const bb = b.getBBox();
      if (bb.x + bb.width / 2 > 100) return;
      const c = b.cloneNode(true);
      c.dataset.dx = '1000';
      c.setAttribute('transform', 'translate(1000 0)');
      c.classList.add('ja-wrap');
      bind(c, byIso.get(iso));
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
  }
  function placePin() {
    if (!pin || !selected || !svg) { if (pin) pin.hidden = true; return; }
    const g = grp(selected);
    if (!g) { pin.hidden = true; return; }
    const b = bbox(g), p = svg.createSVGPoint();
    p.x = b.x + b.width / 2; p.y = b.y + b.height / 2;
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
  function build(mapText, antText) {
    const doc = new DOMParser().parseFromString(mapText, 'image/svg+xml');
    const map = S('svg', {
      class: 'atlas-country-map', viewBox: WORLD.join(' '), role: 'img',
      'aria-label': '拡大すると小さな島まで見える世界地図', preserveAspectRatio: 'xMidYMid meet'
    });
    map.append(S('rect', { x: -20, y: -10, width: 1040, height: 530, fill: '#edf6f3', class: 'country-map-ocean' }));
    const land = S('g', { class: 'country-map-layer' }), wl = S('g', { class: 'ja-wrap-layer' });
    map.append(land, wl); wrap.replaceChildren(map); svg = map;

    [...doc.querySelectorAll('svg > g[id]')].filter(g => /^[A-Z]{2}$/.test(g.id)).forEach(src => {
      const iso = src.id, c = byIso.get(iso), g = clean(src, iso, c);
      if (!g) return;
      land.append(g);
      if (c) groups.set(iso, g);
    });

    if (!groups.has('AQ')) {
      const ad = new DOMParser().parseFromString(antText, 'image/svg+xml'), ap = ad.querySelector('#AQ');
      if (ap) {
        const g = S('g', { class: 'ja-country is-destination' }), p = document.importNode(ap, true);
        p.removeAttribute('id'); p.removeAttribute('class'); p.removeAttribute('fill'); p.removeAttribute('stroke');
        g.append(p); g.dataset.iso = 'AQ'; g.dataset.region = 'antarctica';
        g.style.setProperty('--fill', COLORS.antarctica); land.append(g);
        const bb = g.getBBox(), tw = 270, th = 75, scale = Math.min(tw / bb.width, th / bb.height);
        const ww = bb.width * scale, hh = bb.height * scale;
        const tx = 500 - (bb.x + bb.width / 2) * scale, ty = 463 - (bb.y + bb.height / 2) * scale;
        g.setAttribute('transform', `translate(${tx} ${ty}) scale(${scale})`);
        g.dataset.bbox = `${500 - ww / 2},${463 - hh / 2},${ww},${hh}`;
        groups.set('AQ', g); bind(g, byIso.get('AQ'));
      }
    }

    wrapDateline();
    tip = document.createElement('div'); tip.className = 'map-tooltip'; tip.hidden = true;
    pin = document.createElement('span'); pin.className = 'map-selection-pin'; pin.textContent = '📍'; pin.hidden = true;
    const h = document.createElement('p'); h.className = 'map-hint'; h.textContent = '− / ＋ で拡大縮小 ・ ホイールでズーム ・ ドラッグで移動';
    wrap.append(tip, pin, h);
    style(); controls(); gestures(); root.classList.add('has-country-map');
  }

  tabs.forEach(b => b.onclick = () => setRegion(b.dataset.mapTab));
  if (head) head.textContent = '世界から地域へ寄りながら、地図を自由に拡大・移動して次の旅先を見つけよう。';
  window.addEventListener('resize', () => requestAnimationFrame(placePin));

  Promise.all([
    fetch(MAP).then(r => r.text()),
    fetch(ANT).then(r => r.text()),
    fetch('data/region-taxonomy.json?v=20260823-0030').then(r => r.json()),
    fetch('data/atlas-destinations.json?v=20260822-2252').then(r => r.json())
  ]).then(([m, a, rd, dd]) => {
    regions = rd.regions || [];
    dest = dd.destinations || [];
    byIso = new Map(dest.map(c => [c.iso2, c]));
    lookup(); build(m, a); setRegion('world', false);
  }).catch(e => {
    console.error('[JOURNEY ATLAS map]', e);
    copy.textContent = '地図データを読み込めませんでした。';
  });
})();
