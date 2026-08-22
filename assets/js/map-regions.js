(() => {
  const root = document.querySelector('.map-explorer');
  if (!root) return;

  const $ = (s) => root.querySelector(s);
  const tabs = [...root.querySelectorAll('[data-map-tab]')];
  const tabBar = $('.map-region-tabs');
  const mapWrap = $('.atlas-map-wrap');
  const kicker = $('#map-region-kicker');
  const title = $('#map-region-title');
  const copy = $('#map-region-copy');
  const count = $('#map-region-count');
  const preview = $('#map-region-list');
  const status = $('#map-country-status');
  const headingCopy = $('.map-heading p');
  const NS = 'http://www.w3.org/2000/svg';

  const WORLD = [0, -18, 2000, 1055];
  const MAP_LIMITS = [-120, -40, 2360, 1110];
  const REGION_VIEW = {
    world: WORLD,
    asia: [1010, 70, 930, 650],
    europe: [790, 95, 570, 405],
    africa: [790, 300, 610, 650],
    'north-america': [0, 55, 925, 665],
    'south-america': [365, 430, 540, 590],
    oceania: [1335, 440, 665, 555],
    antarctica: [310, 900, 1380, 145]
  };
  const SUB_VIEW = {
    'northern-europe': [835, 105, 390, 285],
    'western-europe': [915, 185, 255, 205],
    'southern-europe': [895, 245, 350, 205],
    'eastern-europe': [1010, 175, 400, 285],
    'central-america': [250, 360, 300, 250],
    caribbean: [430, 370, 275, 215],
    'australia-new-zealand': [1535, 555, 440, 345],
    melanesia: [1570, 455, 390, 305],
    micronesia: [1665, 400, 350, 185],
    polynesia: [1885, 525, 355, 175]
  };
  const COLORS = {
    asia: ['#9eb79c', '#c6cfaa'], europe: ['#ccb078', '#dfcda6'], africa: ['#c78f69', '#dfb48d'],
    'north-america': ['#9fbec5', '#c4d4d1'], 'south-america': ['#9eb47c', '#c8d1a3'],
    oceania: ['#78aaa8', '#aad0c7'], antarctica: ['#d7e7e9', '#f3f6f1']
  };

  const FALLBACK = {
    FM: [1878, 463], KI: [1962, 494], MH: [1950, 461], NR: [1928, 503], PW: [1748, 459],
    CK: [2112, 618], NU: [2057, 606], WS: [2044, 578], TO: [2028, 619], TV: [1991, 548]
  };
  const POLY_WRAP = { WS: 2000, TO: 2000, CK: 2000, NU: 2000 };

  const ANTARCTICA_PATH = 'M356.2 1011.1 L423.1 1014.6 L432.7 1011.3 L426.8 1007.6 L452.7 1009.1 L451.2 1001.4 L458.6 999.5 L477.3 1000.3 L490.3 995.6 L515.8 994.4 L512.9 989.3 L582.0 994.0 L596.1 999.0 L599.9 996.4 L619.8 998.2 L614.1 995.4 L616.5 993.8 L607.2 990.9 L613.6 991.1 L603.5 988.6 L598.4 984.2 L614.0 981.5 L687.5 992.1 L690.1 987.7 L703.6 989.4 L694.8 987.7 L693.6 984.4 L722.8 988.6 L718.0 984.3 L705.5 982.1 L711.8 979.3 L710.3 977.0 L698.5 978.2 L706.7 975.4 L697.1 972.3 L707.7 974.2 L707.2 969.7 L712.4 970.8 L709.0 967.2 L714.7 966.3 L727.1 973.1 L723.2 969.6 L729.7 968.8 L728.6 963.5 L721.3 957.1 L726.5 958.7 L724.0 954.9 L727.8 955.2 L726.0 952.3 L732.5 949.3 L730.7 946.2 L734.2 947.0 L740.0 940.8 L753.7 936.2 L756.9 938.4 L750.8 939.1 L750.6 943.6 L743.0 944.7 L749.7 947.4 L738.4 947.8 L751.5 955.9 L752.7 969.6 L769.0 985.3 L768.9 997.0 L825.5 1010.9 L871.9 1013.0 L878.3 1008.7 L902.0 1003.0 L897.5 1000.7 L905.8 998.4 L902.8 993.3 L916.5 994.2 L926.0 986.3 L949.7 983.0 L951.9 979.4 L965.3 975.4 L986.4 975.0 L1000.0 970.5 L1001.1 973.3 L1016.1 974.1 L1051.0 973.1 L1059.5 969.9 L1097.9 974.5 L1136.3 965.6 L1148.5 971.0 L1153.2 968.9 L1149.3 971.2 L1154.9 973.0 L1161.3 966.6 L1191.2 958.4 L1198.9 960.0 L1203.6 955.9 L1209.7 958.0 L1209.8 953.3 L1225.0 950.6 L1232.2 951.6 L1237.6 954.4 L1235.1 957.1 L1243.0 959.2 L1285.1 960.8 L1285.2 965.9 L1295.0 965.6 L1298.8 969.2 L1295.0 971.4 L1298.4 971.4 L1358.2 953.1 L1370.6 956.1 L1391.2 955.0 L1406.9 945.9 L1410.3 950.0 L1424.2 948.1 L1428.7 950.9 L1433.8 946.7 L1436.4 949.0 L1433.9 951.3 L1449.6 956.6 L1474.0 950.2 L1475.7 954.0 L1485.8 956.9 L1526.0 952.8 L1531.8 957.1 L1543.8 952.1 L1562.4 951.4 L1596.3 958.1 L1606.2 955.1 L1596.7 959.6 L1601.2 964.0 L1626.7 963.7 L1628.1 967.2 L1641.6 970.1 L1640.7 974.3 L1660.7 975.8 L1665.7 981.3 L1669.2 979.3 L1667.4 982.1 L1646.7 990.2 L1606.0 998.9 L1615.9 1000.0 L1603.3 1000.1 L1589.0 1007.1 L1586.0 1012.3 L1603.0 1008.0 L1643.9 1011.1 L1644 1035 L356 1035 Z';

  let regions = [], destinations = [], destByIso = new Map(), regionByIso = new Map(), subByIso = new Map(), subById = new Map();
  let primary = new Map(), interactive = new Map(), nav = new Map(), fallbackPins = new Map(), wrapped = new Map();
  let svgMap = null, tooltip = null, focusPin = null, subBar = null, zoomControls = null;
  let activeRegion = 'world', activeSub = null, selected = null, hovered = null, frame = null, dragging = null;

  const S = (tag, attrs = {}) => {
    const n = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, String(v)));
    return n;
  };
  const region = (id) => regions.find(r => r.id === id);
  const countries = (codes = []) => {
    const set = new Set(codes);
    return destinations.filter(c => set.has(c.iso2)).sort((a, b) => a.nameJa.localeCompare(b.nameJa, 'ja'));
  };

  function buildLookup() {
    regions.forEach(r => {
      (r.iso2 || []).forEach(i => regionByIso.set(i, r.id));
      (r.subregions || []).forEach(s => {
        subById.set(s.id, { ...s, regionId: r.id });
        (s.iso2 || []).forEach(i => subByIso.set(i, s.id));
      });
    });
  }

  function ensureSubBar() {
    if (subBar || !tabBar) return;
    subBar = document.createElement('div');
    subBar.className = 'map-subregion-tabs';
    subBar.setAttribute('aria-label', '小地域まで拡大');
    tabBar.insertAdjacentElement('afterend', subBar);
  }
  function renderSubTabs(r) {
    ensureSubBar();
    const items = r?.subregions || [];
    if (!items.length) { subBar.hidden = true; subBar.replaceChildren(); return; }
    subBar.hidden = false;
    subBar.innerHTML = '<span class="map-subregion-tabs__guide">さらに拡大</span>' + items.map(s => `<button type="button" data-map-subregion="${s.id}" class="${activeSub === s.id ? 'is-active' : ''}" aria-pressed="${activeSub === s.id}">${s.label}</button>`).join('');
    subBar.querySelectorAll('[data-map-subregion]').forEach(b => b.addEventListener('click', () => setSub(b.dataset.mapSubregion)));
  }

  function prompt(text) {
    nav = new Map();
    preview.className = 'map-country-preview';
    preview.innerHTML = `<div class="map-country-preview__empty"><span class="map-country-preview__marker">＋</span><div><strong>地域を選択</strong><p>${text}</p></div></div>`;
  }
  function countryNav(codes, picked = null) {
    nav = new Map();
    const items = countries(codes);
    const summary = picked ? `<div class="map-country-nav__selected"><span class="map-country-nav__selected-flag">${picked.flag}</span><div class="map-country-nav__selected-names"><strong>${picked.nameJa}</strong><span>${picked.nameEn}</span></div>${picked.atlasPublished && picked.href ? `<a class="map-country-nav__selected-link" href="${picked.href}">見る ›</a>` : '<span class="map-country-nav__selected-waiting">COMING SOON</span>'}</div>` : '';
    preview.className = 'map-country-nav';
    preview.innerHTML = `<div class="map-country-nav__wrap">${summary}<div class="map-country-nav__guide"><strong>国・地域</strong><span>国名と地図が連動します</span></div><div class="map-country-nav__list">${items.map(c => `<button type="button" class="map-country-nav__item ${picked?.iso2 === c.iso2 ? 'is-selected' : ''}" data-country-nav="${c.iso2}" aria-pressed="${picked?.iso2 === c.iso2}"><span class="map-country-nav__flag">${c.flag}</span><span class="map-country-nav__names"><strong>${c.nameJa}</strong><small>${c.nameEn}</small></span></button>`).join('')}</div></div>`;
    preview.querySelectorAll('[data-country-nav]').forEach(b => {
      nav.set(b.dataset.countryNav, b);
      b.addEventListener('pointerenter', () => hover(b.dataset.countryNav, true));
      b.addEventListener('pointerleave', () => hover(b.dataset.countryNav, false));
      b.addEventListener('focus', () => hover(b.dataset.countryNav, true));
      b.addEventListener('blur', () => hover(b.dataset.countryNav, false));
      b.addEventListener('click', () => selectIso(b.dataset.countryNav));
    });
  }

  function renderWorld() {
    kicker.textContent = 'WORLD'; title.textContent = '世界';
    copy.textContent = '地域を選ぶか、＋/−で地図を拡大できます。拡大すると小さな国の形も見つけやすくなります。';
    count.textContent = `${destinations.length || 199} DESTINATIONS`; status.textContent = '';
    prompt('上の大地域から見たい場所を選ぶか、地図を直接拡大してください。'); renderSubTabs(null);
  }
  function renderRegion(r, picked = null) {
    kicker.textContent = r.labelEn; title.textContent = r.label;
    copy.textContent = (r.subregions || []).length ? '小地域へさらに寄れます。＋/−でも自由に拡大でき、国名と地図は連動します。' : '＋/−で自由に拡大できます。国名と地図は連動しています。';
    count.textContent = `${countries(r.iso2).length} DESTINATIONS`; status.textContent = picked ? `${picked.nameJa}を選択中` : '';
    countryNav(r.iso2, picked); renderSubTabs(r);
  }
  function renderSub(s, picked = null) {
    const r = region(s.regionId); kicker.textContent = `${r?.labelEn || ''} / ${s.labelEn}`; title.textContent = s.label;
    copy.textContent = '国を選びやすい倍率まで拡大しています。さらに＋/−で寄れます。国名に触れると地図上の位置が📍で反応します。';
    count.textContent = `${countries(s.iso2).length} DESTINATIONS`; status.textContent = picked ? `${picked.nameJa}を選択中` : '';
    countryNav(s.iso2, picked); renderSubTabs(r);
  }

  function setTabs(id) {
    tabs.forEach(b => { const on = b.dataset.mapTab === id; b.classList.toggle('is-active', on); b.setAttribute('aria-pressed', String(on)); });
  }
  function view() { return svgMap ? svgMap.getAttribute('viewBox').trim().split(/\s+/).map(Number) : WORLD.slice(); }
  function clampView(v) {
    let [x, y, w, h] = v;
    const ratio = h / w;
    if (w < 46) { w = 46; h = w * ratio; }
    if (w > 2200) { w = 2200; h = w * ratio; }
    const [minX, minY, maxX, maxY] = MAP_LIMITS;
    x = Math.min(maxX - Math.min(w, maxX - minX), Math.max(minX, x));
    y = Math.min(maxY - Math.min(h, maxY - minY), Math.max(minY, y));
    return [x, y, w, h];
  }
  function applyView(v) {
    if (!svgMap) return;
    svgMap.setAttribute('viewBox', clampView(v).join(' '));
    updateFocusPin();
    updateFallbackPins();
  }
  function animate(target, d = 420) {
    if (!svgMap) return;
    if (frame) cancelAnimationFrame(frame);
    target = clampView(target);
    const from = view(), start = performance.now(), ease = t => 1 - Math.pow(1 - t, 3);
    const tick = now => {
      const p = Math.min(1, (now - start) / d), e = ease(p);
      applyView(from.map((v, i) => v + (target[i] - v) * e));
      if (p < 1) frame = requestAnimationFrame(tick); else frame = null;
    };
    frame = requestAnimationFrame(tick);
  }
  function contextView() {
    if (activeSub && SUB_VIEW[activeSub]) return SUB_VIEW[activeSub];
    return REGION_VIEW[activeRegion] || WORLD;
  }
  function zoomAt(factor, cx = null, cy = null, motion = false) {
    const v = view();
    const nx = cx == null ? v[0] + v[2] / 2 : cx;
    const ny = cy == null ? v[1] + v[3] / 2 : cy;
    const nw = v[2] * factor, nh = v[3] * factor;
    const target = [nx - (nx - v[0]) * factor, ny - (ny - v[1]) * factor, nw, nh];
    motion ? animate(target, 180) : applyView(target);
  }
  function svgPoint(clientX, clientY) {
    if (!svgMap?.getScreenCTM) return null;
    const matrix = svgMap.getScreenCTM(); if (!matrix) return null;
    const p = svgMap.createSVGPoint(); p.x = clientX; p.y = clientY;
    return p.matrixTransform(matrix.inverse());
  }

  const elems = iso => interactive.get(iso) || [];
  function clearSelected() { if (selected) elems(selected).forEach(e => e.classList.remove('is-selected')); selected = null; }
  function markSelected(iso) { clearSelected(); selected = iso; elems(iso).forEach(e => e.classList.add('is-selected')); updateFocusPin(); }
  function focus(codes = null) {
    const set = codes ? new Set(codes) : null;
    primary.forEach((e, iso) => { e.classList.toggle('is-muted', !!(set && !set.has(iso))); e.classList.toggle('is-in-focus', !!(set && set.has(iso))); });
    interactive.forEach((arr, iso) => arr.filter(e => e.classList.contains('country-shape--wrapped')).forEach(e => { e.classList.toggle('is-muted', !!(set && !set.has(iso))); e.classList.toggle('is-in-focus', !!(set && set.has(iso))); }));
    updateFallbackPins();
  }
  function positionFor(iso) {
    if (activeSub === 'polynesia' && FALLBACK[iso]) return FALLBACK[iso];
    const e = activeSub === 'polynesia' && wrapped.get(iso) ? wrapped.get(iso) : primary.get(iso);
    if (e) {
      const b = e.getBBox();
      const dx = e.classList.contains('country-shape--wrapped') ? (POLY_WRAP[iso] || 0) : 0;
      return [b.x + b.width / 2 + dx, b.y + b.height / 2];
    }
    return FALLBACK[iso] || null;
  }
  function bounds(codes) {
    const points = (codes || []).map(positionFor).filter(Boolean);
    const shapes = (codes || []).map(iso => primary.get(iso)).filter(Boolean).map(e => e.getBBox());
    const xs = points.map(p => p[0]), ys = points.map(p => p[1]);
    shapes.forEach(b => { xs.push(b.x, b.x + b.width); ys.push(b.y, b.y + b.height); });
    if (!xs.length) return null;
    const l = Math.min(...xs), t = Math.min(...ys), r = Math.max(...xs), bt = Math.max(...ys);
    let w = r - l, h = bt - t; const px = Math.max(w * .1, 14), py = Math.max(h * .13, 12);
    w = Math.max(w + px * 2, 100); h = Math.max(h + py * 2, 76);
    return [(l + r) / 2 - w / 2, (t + bt) / 2 - h / 2, w, h];
  }

  function setRegion(id, { motion = true } = {}) {
    activeRegion = id; activeSub = null; root.dataset.activeRegion = id; delete root.dataset.activeSubregion;
    clearSelected(); hovered = null; hideFocusPin(); setTabs(id);
    const v = REGION_VIEW[id] || WORLD; motion ? animate(v) : applyView(v);
    if (id === 'world') { focus(); renderWorld(); return; }
    const r = region(id); if (!r) return; focus(r.iso2); renderRegion(r);
  }
  function setSub(id) {
    const s = subById.get(id); if (!s) return;
    activeRegion = s.regionId; activeSub = id; root.dataset.activeRegion = activeRegion; root.dataset.activeSubregion = id;
    clearSelected(); hovered = null; hideFocusPin(); setTabs(activeRegion); focus(s.iso2); renderSub(s);
    const v = SUB_VIEW[id] || bounds(s.iso2); if (v) animate(v, 430);
  }
  function zoomCountry(c) {
    const pos = positionFor(c.iso2); if (!pos) return;
    if (c.iso2 === 'AQ') { animate(REGION_VIEW.antarctica, 390); return; }
    const p = primary.get(c.iso2);
    if (p) {
      const b = p.getBBox(), dx = activeSub === 'polynesia' && POLY_WRAP[c.iso2] ? POLY_WRAP[c.iso2] : 0;
      const w = Math.max(b.width * 3.3, 58), h = Math.max(b.height * 3.3, 44);
      animate([b.x + dx + b.width / 2 - w / 2, b.y + b.height / 2 - h / 2, w, h], 360);
    } else {
      animate([pos[0] - 40, pos[1] - 30, 80, 60], 360);
    }
  }
  function selectIso(iso) { const c = destByIso.get(iso); if (c && positionFor(iso)) selectCountry(c); }
  function selectCountry(c) {
    const rid = regionByIso.get(c.iso2) || 'world', sid = subByIso.get(c.iso2) || null;
    activeRegion = rid; activeSub = sid; root.dataset.activeRegion = rid;
    if (sid) root.dataset.activeSubregion = sid; else delete root.dataset.activeSubregion;
    setTabs(rid); const r = region(rid); renderSubTabs(r); focus(sid ? subById.get(sid)?.iso2 : r?.iso2);
    markSelected(c.iso2); hovered = null;
    if (sid) renderSub(subById.get(sid), c); else renderRegion(r, c);
    zoomCountry(c);
  }

  function posTip(ev) {
    if (!tooltip || !mapWrap) return;
    const r = mapWrap.getBoundingClientRect();
    tooltip.style.transform = `translate(${Math.min(r.width - 142, Math.max(12, ev.clientX - r.left + 12))}px, ${Math.min(r.height - 54, Math.max(12, ev.clientY - r.top + 12))}px)`;
  }
  function updateFocusPin() {
    if (!focusPin) return;
    const iso = hovered || selected; if (!iso) return hideFocusPin();
    const p = positionFor(iso); if (!p) return hideFocusPin();
    const v = view(), size = Math.max(16, Math.min(38, v[2] * .028));
    focusPin.setAttribute('x', p[0]); focusPin.setAttribute('y', p[1] - size * .18); focusPin.setAttribute('font-size', size); focusPin.hidden = false;
  }
  function hideFocusPin() { if (focusPin) focusPin.hidden = true; }
  function hover(iso, on) {
    elems(iso).forEach(e => e.classList.toggle('is-hovered', on)); nav.get(iso)?.classList.toggle('is-hovered', on);
    if (on) hovered = iso; else if (hovered === iso) hovered = null;
    updateFocusPin();
  }

  function gradient(defs, id, colors) {
    const g = S('linearGradient', { id, x1: '0%', y1: '0%', x2: '100%', y2: '100%' });
    g.append(S('stop', { offset: '0%', 'stop-color': colors[0] }), S('stop', { offset: '100%', 'stop-color': colors[1] })); defs.append(g);
  }
  function addInteractive(iso, e) { if (!interactive.has(iso)) interactive.set(iso, []); interactive.get(iso).push(e); }
  function bind(e, c, tip = true) {
    addInteractive(c.iso2, e); e.dataset.iso = c.iso2; e.setAttribute('tabindex', '0'); e.setAttribute('role', 'button'); e.setAttribute('aria-label', `${c.nameJa}を選ぶ`);
    e.addEventListener('pointerenter', ev => { hover(c.iso2, true); if (tip && tooltip) { tooltip.innerHTML = `<strong>${c.nameJa}</strong><span>${c.nameEn}</span>`; tooltip.hidden = false; posTip(ev); } });
    e.addEventListener('pointermove', ev => { if (tip) posTip(ev); });
    e.addEventListener('pointerleave', () => { hover(c.iso2, false); if (tip && tooltip) tooltip.hidden = true; });
    e.addEventListener('focus', () => hover(c.iso2, true)); e.addEventListener('blur', () => hover(c.iso2, false));
    e.addEventListener('click', () => selectCountry(c));
    e.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); selectCountry(c); } });
  }
  function createFallbackPin(c, xy, layer) {
    const pin = S('text', { x: xy[0], y: xy[1], class: 'country-fallback-pin', 'text-anchor': 'middle', 'dominant-baseline': 'central' });
    pin.textContent = '📍'; pin.hidden = true; bind(pin, c, false); layer.append(pin); fallbackPins.set(c.iso2, pin);
  }
  function updateFallbackPins() {
    if (!svgMap) return;
    const width = view()[2];
    fallbackPins.forEach((pin, iso) => {
      const sid = subByIso.get(iso), inContext = activeSub && sid === activeSub;
      const show = inContext && width <= 430;
      pin.hidden = !show;
      if (show) {
        const size = Math.max(10, Math.min(22, width * .036));
        pin.setAttribute('font-size', size);
      }
    });
  }

  function installZoomControls() {
    zoomControls = document.createElement('div'); zoomControls.className = 'map-zoom-controls'; zoomControls.setAttribute('aria-label', '地図の拡大縮小');
    zoomControls.innerHTML = '<button type="button" data-map-zoom="in" aria-label="地図を拡大">＋</button><button type="button" data-map-zoom="out" aria-label="地図を縮小">−</button><button type="button" data-map-zoom="reset" aria-label="地図表示を戻す">↺</button>';
    zoomControls.querySelector('[data-map-zoom="in"]').addEventListener('click', () => zoomAt(.72, null, null, true));
    zoomControls.querySelector('[data-map-zoom="out"]').addEventListener('click', () => zoomAt(1.38, null, null, true));
    zoomControls.querySelector('[data-map-zoom="reset"]').addEventListener('click', () => animate(contextView(), 260));
    mapWrap.append(zoomControls);
  }
  function installMapGestures() {
    svgMap.addEventListener('wheel', ev => {
      ev.preventDefault();
      const p = svgPoint(ev.clientX, ev.clientY), factor = ev.deltaY < 0 ? .82 : 1.2;
      zoomAt(factor, p?.x, p?.y, false);
    }, { passive: false });
    svgMap.addEventListener('pointerdown', ev => {
      if (ev.pointerType === 'touch' || ev.target.closest?.('.is-destination')) return;
      dragging = { id: ev.pointerId, x: ev.clientX, y: ev.clientY, view: view() };
      svgMap.setPointerCapture?.(ev.pointerId); svgMap.classList.add('is-dragging');
    });
    svgMap.addEventListener('pointermove', ev => {
      if (!dragging || dragging.id !== ev.pointerId) return;
      const rect = svgMap.getBoundingClientRect(), dx = ev.clientX - dragging.x, dy = ev.clientY - dragging.y, v = dragging.view;
      applyView([v[0] - dx / rect.width * v[2], v[1] - dy / rect.height * v[3], v[2], v[3]]);
    });
    const end = ev => { if (dragging && dragging.id === ev.pointerId) { dragging = null; svgMap.classList.remove('is-dragging'); } };
    svgMap.addEventListener('pointerup', end); svgMap.addEventListener('pointercancel', end);
  }

  function buildMap(shapes) {
    primary = new Map(); interactive = new Map(); wrapped = new Map(); fallbackPins = new Map(); mapWrap.classList.add('country-map-wrap');
    const map = S('svg', { class: 'atlas-country-map', viewBox: WORLD.join(' '), role: 'img', 'aria-label': '拡大・移動しながら国を選べるイラスト世界地図', preserveAspectRatio: 'xMidYMid meet' }), defs = S('defs');
    const ocean = S('linearGradient', { id: 'atlas-ocean', x1: '0%', y1: '0%', x2: '0%', y2: '100%' });
    ocean.append(S('stop', { offset: '0%', 'stop-color': '#e8f4f2' }), S('stop', { offset: '58%', 'stop-color': '#eef6f1' }), S('stop', { offset: '100%', 'stop-color': '#f4f0e4' })); defs.append(ocean);
    Object.entries(COLORS).forEach(([id, c]) => gradient(defs, `land-${id}`, c));
    const grid = S('pattern', { id: 'atlas-grid', width: 125, height: 125, patternUnits: 'userSpaceOnUse' });
    grid.append(S('path', { d: 'M 125 0 L 0 0 0 125', fill: 'none', stroke: '#6f9295', 'stroke-opacity': '.11', 'stroke-width': 1 })); defs.append(grid);
    const paper = S('filter', { id: 'atlas-paper', x: '-5%', y: '-5%', width: '110%', height: '110%' });
    paper.append(S('feTurbulence', { type: 'fractalNoise', baseFrequency: '.018', numOctaves: 3, seed: 9, result: 'noise' }), S('feColorMatrix', { in: 'noise', type: 'matrix', values: '1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 .10 0', result: 'texture' }), S('feBlend', { in: 'SourceGraphic', in2: 'texture', mode: 'multiply' })); defs.append(paper); map.append(defs);

    map.append(
      S('rect', { class: 'country-map-ocean', x: -120, y: -40, width: 2480, height: 1150, rx: 28, fill: 'url(#atlas-ocean)' }),
      S('ellipse', { class: 'country-map-wash country-map-wash--one', cx: 360, cy: 310, rx: 360, ry: 205 }),
      S('ellipse', { class: 'country-map-wash country-map-wash--two', cx: 1510, cy: 310, rx: 420, ry: 225 }),
      S('ellipse', { class: 'country-map-wash country-map-wash--three', cx: 1130, cy: 770, rx: 360, ry: 180 }),
      S('rect', { class: 'country-map-grid', x: -120, y: -40, width: 2480, height: 1150, fill: 'url(#atlas-grid)' }),
      S('rect', { class: 'country-map-paper', x: -120, y: -40, width: 2480, height: 1150, filter: 'url(#atlas-paper)' })
    );

    const ice = S('g', { class: 'country-map-ice-layer', 'aria-hidden': 'true' }), land = S('g', { class: 'country-map-layer' }), wrappedLayer = S('g', { class: 'country-map-wrapped-layer' }), fallbackLayer = S('g', { class: 'country-map-fallback-layer' }), overlay = S('g', { class: 'country-map-overlay-layer' });
    shapes.forEach(({ id, shape }) => {
      const iso = String(id || '').toUpperCase(); if (iso === 'AQ') return;
      const c = destByIso.get(iso), p = S('path', { d: shape }); p.dataset.iso = iso;
      if (!c) { p.classList.add('country-shape', 'is-outside-atlas'); land.append(p); return; }
      const rid = regionByIso.get(iso) || 'world', tone = Math.abs(iso.charCodeAt(0) + iso.charCodeAt(1)) % 4;
      p.classList.add('country-shape', 'is-destination', `tone-${tone}`); p.dataset.region = rid; p.style.fill = `url(#land-${rid})`;
      const t = S('title'); t.textContent = `${c.nameJa} / ${c.nameEn}`; p.append(t); bind(p, c); primary.set(iso, p); land.append(p);
      if (POLY_WRAP[iso]) {
        const clone = S('path', { d: shape, transform: `translate(${POLY_WRAP[iso]} 0)` });
        clone.classList.add('country-shape', 'country-shape--wrapped', 'is-destination', `tone-${tone}`); clone.dataset.region = rid; clone.style.fill = `url(#land-${rid})`; bind(clone, c); wrapped.set(iso, clone); wrappedLayer.append(clone);
      }
    });

    const aq = destByIso.get('AQ');
    if (aq) {
      const glow = S('path', { d: ANTARCTICA_PATH, class: 'antarctica-glow' }); ice.append(glow);
      const p = S('path', { d: ANTARCTICA_PATH }); p.classList.add('country-shape', 'country-shape--antarctica', 'is-destination', 'tone-2'); p.dataset.region = 'antarctica'; p.style.fill = 'url(#land-antarctica)'; bind(p, aq); primary.set('AQ', p); land.append(p);
    }

    destinations.forEach(c => { if (!primary.has(c.iso2) && FALLBACK[c.iso2]) createFallbackPin(c, FALLBACK[c.iso2], fallbackLayer); });
    map.append(ice, land, wrappedLayer, fallbackLayer, overlay); mapWrap.replaceChildren(map); svgMap = map;
    focusPin = S('text', { class: 'country-focus-pin', x: 0, y: 0, 'text-anchor': 'middle', 'dominant-baseline': 'central', 'aria-hidden': 'true' }); focusPin.textContent = '📍'; focusPin.hidden = true; overlay.append(focusPin);
    tooltip = document.createElement('div'); tooltip.className = 'map-tooltip'; tooltip.hidden = true;
    const hint = document.createElement('p'); hint.className = 'map-hint'; hint.textContent = '＋/−・ホイールで拡大 ／ ドラッグで移動';
    mapWrap.append(tooltip, hint); installZoomControls(); installMapGestures(); root.classList.add('has-country-map'); updateFallbackPins();
    const unresolved = destinations.filter(c => !primary.has(c.iso2) && !FALLBACK[c.iso2]);
    if (unresolved.length) console.warn('[JOURNEY ATLAS map] unresolved map locations:', unresolved.map(c => c.iso2));
  }

  tabs.forEach(b => b.addEventListener('click', () => setRegion(b.dataset.mapTab)));
  if (headingCopy) headingCopy.textContent = '世界から地域へ寄りながら、地図を自由に拡大・移動して次の旅先を見つけよう。';
  Promise.all([
    import('https://cdn.jsdelivr.net/npm/world-map-country-shapes@1.0.0/index.js').then(m => m.default || []),
    fetch('data/region-taxonomy.json?v=20260822-2318').then(r => { if (!r.ok) throw new Error('Region taxonomy not found'); return r.json(); }),
    fetch('data/atlas-destinations.json?v=20260822-2252').then(r => { if (!r.ok) throw new Error('Destination registry not found'); return r.json(); })
  ]).then(([shapes, regionData, destinationData]) => {
    regions = regionData.regions || []; destinations = destinationData.destinations || []; destByIso = new Map(destinations.map(c => [c.iso2, c]));
    buildLookup(); buildMap(shapes); setRegion('world', { motion: false });
  }).catch(err => {
    console.error('[JOURNEY ATLAS map]', err); copy.textContent = '地図データを読み込めませんでした。'; count.textContent = ''; status.textContent = '再読み込みしてください。';
  });
})();
