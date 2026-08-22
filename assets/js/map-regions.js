(() => {
  const root = document.querySelector('.map-explorer');
  if (!root) return;

  const tabs = [...root.querySelectorAll('[data-map-tab]')];
  const tabBar = root.querySelector('.map-region-tabs');
  const mapWrap = root.querySelector('.atlas-map-wrap');
  const kicker = root.querySelector('#map-region-kicker');
  const title = root.querySelector('#map-region-title');
  const copy = root.querySelector('#map-region-copy');
  const count = root.querySelector('#map-region-count');
  const preview = root.querySelector('#map-region-list');
  const status = root.querySelector('#map-country-status');
  const headingCopy = root.querySelector('.map-heading p');

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const WORLD_VIEW = [0, -18, 2000, 1055];
  const REGION_VIEWS = {
    world: WORLD_VIEW,
    asia: [1010, 70, 930, 650],
    europe: [790, 95, 570, 405],
    africa: [790, 300, 610, 650],
    'north-america': [0, 55, 925, 665],
    'south-america': [365, 430, 540, 590],
    oceania: [1335, 475, 660, 510],
    antarctica: [90, 790, 1820, 230]
  };

  const REGION_COLORS = {
    asia: ['#9eb79c', '#c6cfaa'],
    europe: ['#ccb078', '#dfcda6'],
    africa: ['#c78f69', '#dfb48d'],
    'north-america': ['#9fbec5', '#c4d4d1'],
    'south-america': ['#9eb47c', '#c8d1a3'],
    oceania: ['#78aaa8', '#aad0c7'],
    antarctica: ['#d7e7e9', '#f3f6f1']
  };

  let regions = [];
  let destinations = [];
  let themes = [];
  let destinationByIso = new Map();
  let regionByIso = new Map();
  let subregionByIso = new Map();
  let subregionById = new Map();
  let pathByIso = new Map();
  let mapSvg = null;
  let tooltip = null;
  let selectedPath = null;
  let activeRegion = 'world';
  let activeSubregion = null;
  let animationFrame = null;
  let subregionBar = null;

  const makeSvg = (tag, attrs = {}) => {
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    return node;
  };

  const regionById = (id) => regions.find((region) => region.id === id);
  const countriesForCodes = (codes = []) => {
    const set = new Set(codes);
    return destinations.filter((country) => set.has(country.iso2));
  };

  function buildRegionLookup() {
    regionByIso = new Map();
    subregionByIso = new Map();
    subregionById = new Map();
    regions.forEach((region) => {
      (region.iso2 || []).forEach((iso) => regionByIso.set(iso, region.id));
      (region.subregions || []).forEach((subregion) => {
        subregionById.set(subregion.id, { ...subregion, regionId: region.id });
        (subregion.iso2 || []).forEach((iso) => subregionByIso.set(iso, subregion.id));
      });
    });
  }

  function themeLabelsFor(country) {
    const explicit = Array.isArray(country.themes) ? country.themes : [];
    const ids = explicit.length ? explicit : themes.filter((theme) => (theme.examples || []).includes(country.slug)).map((theme) => theme.id);
    return ids.map((id) => themes.find((theme) => theme.id === id)).filter(Boolean).slice(0, 3).map((theme) => theme.label);
  }

  function ensureSubregionBar() {
    if (subregionBar || !tabBar) return;
    subregionBar = document.createElement('div');
    subregionBar.className = 'map-subregion-tabs';
    subregionBar.setAttribute('aria-label', '小地域まで拡大');
    subregionBar.hidden = true;
    tabBar.insertAdjacentElement('afterend', subregionBar);
  }

  function renderSubregionTabs(region) {
    ensureSubregionBar();
    if (!subregionBar) return;
    const items = region?.subregions || [];
    if (!items.length) {
      subregionBar.hidden = true;
      subregionBar.replaceChildren();
      return;
    }
    const fragment = document.createDocumentFragment();
    const guide = document.createElement('span');
    guide.className = 'map-subregion-tabs__guide';
    guide.textContent = 'さらに拡大';
    fragment.append(guide);
    items.forEach((subregion) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.mapSubregion = subregion.id;
      button.textContent = subregion.label;
      button.classList.toggle('is-active', activeSubregion === subregion.id);
      button.setAttribute('aria-pressed', String(activeSubregion === subregion.id));
      button.addEventListener('click', () => setSubregion(subregion.id));
      fragment.append(button);
    });
    subregionBar.replaceChildren(fragment);
    subregionBar.hidden = false;
  }

  function renderPrompt(message) {
    if (!preview) return;
    preview.className = 'map-country-preview';
    const wrapper = document.createElement('div');
    wrapper.className = 'map-country-preview__empty';
    const eye = document.createElement('span');
    eye.className = 'map-country-preview__marker';
    eye.textContent = '＋';
    const body = document.createElement('div');
    const main = document.createElement('strong');
    main.textContent = '地図上の国を選択';
    const sub = document.createElement('p');
    sub.textContent = message;
    body.append(main, sub);
    wrapper.append(eye, body);
    preview.replaceChildren(wrapper);
  }

  function renderWorld() {
    if (kicker) kicker.textContent = 'WORLD';
    if (title) title.textContent = '世界';
    if (copy) copy.textContent = 'まず大地域へ。そこから必要なら小地域まで拡大し、最後は地図上の国そのものを選びます。';
    if (count) count.textContent = `${destinations.length || 199} DESTINATIONS`;
    if (status) status.textContent = '';
    renderPrompt('上の大地域を選ぶと、国を選びやすい大きさまで地図が近づきます。');
    renderSubregionTabs(null);
  }

  function renderRegion(region) {
    if (!region) return;
    if (kicker) kicker.textContent = region.labelEn;
    if (title) title.textContent = region.label;
    if (copy) copy.textContent = region.description;
    if (count) count.textContent = `${countriesForCodes(region.iso2).length} DESTINATIONS`;
    if (status) status.textContent = '';
    renderPrompt((region.subregions || []).length ? '小地域からさらに拡大するか、見えている国の形を直接クリックしてください。' : '地図上の国の形を直接クリックしてください。');
    renderSubregionTabs(region);
  }

  function renderSubregion(subregion) {
    if (!subregion) return;
    const region = regionById(subregion.regionId);
    if (kicker) kicker.textContent = `${region?.labelEn || ''} / ${subregion.labelEn}`;
    if (title) title.textContent = subregion.label;
    if (copy) copy.textContent = `${region?.label || ''}の中をさらに拡大しています。国名一覧ではなく、地図上の形から旅先を選びます。`;
    if (count) count.textContent = `${countriesForCodes(subregion.iso2).length} DESTINATIONS`;
    if (status) status.textContent = '';
    renderPrompt('この範囲の国の形を直接クリックしてください。');
    renderSubregionTabs(region);
  }

  function renderCountry(country, regionId, subregionId) {
    const region = regionById(regionId);
    const subregion = subregionById.get(subregionId);
    const themeLabels = themeLabelsFor(country);
    if (kicker) kicker.textContent = subregion ? `${region?.labelEn || ''} / ${subregion.labelEn}` : (region?.labelEn || country.iso2);
    if (title) title.textContent = country.nameJa;
    if (copy) copy.textContent = country.nameEn;
    if (count) count.textContent = `${country.flag} ${country.iso2}`;
    if (status) status.textContent = '地図上で別の国を選ぶと、この表示が切り替わります。';
    if (!preview) return;

    preview.className = 'map-country-preview';
    const card = document.createElement('div');
    card.className = 'map-country-card';
    const visual = document.createElement('div');
    visual.className = 'map-country-card__visual';
    if (country.image) {
      visual.style.backgroundImage = `url("${country.image}")`;
      visual.classList.add('has-image');
    }
    const flag = document.createElement('span');
    flag.className = 'map-country-card__flag';
    flag.textContent = country.flag;
    visual.append(flag);

    const meta = document.createElement('div');
    meta.className = 'map-country-card__meta';
    const place = document.createElement('span');
    place.className = 'map-country-card__region';
    place.textContent = subregion ? `${region?.label || ''} / ${subregion.label}` : (region?.label || 'JOURNEY ATLAS');
    const english = document.createElement('strong');
    english.textContent = country.nameEn;
    const japanese = document.createElement('span');
    japanese.className = 'map-country-card__ja';
    japanese.textContent = country.nameJa;
    meta.append(place, english, japanese);

    if (themeLabels.length) {
      const themeWrap = document.createElement('div');
      themeWrap.className = 'map-country-card__themes';
      themeLabels.forEach((label) => {
        const chip = document.createElement('span');
        chip.textContent = label;
        themeWrap.append(chip);
      });
      meta.append(themeWrap);
    }

    const state = document.createElement('p');
    state.textContent = country.atlasPublished ? 'JOURNEY ATLAS 公開中' : 'この国のページは準備中です。';
    meta.append(state);
    if (country.atlasPublished && country.href) {
      const link = document.createElement('a');
      link.href = country.href;
      link.className = 'map-country-card__link';
      link.innerHTML = 'この国を見る <span>›</span>';
      meta.append(link);
    } else {
      const waiting = document.createElement('span');
      waiting.className = 'map-country-card__waiting';
      waiting.textContent = 'COMING SOON';
      meta.append(waiting);
    }
    card.append(visual, meta);
    preview.replaceChildren(card);
  }

  function setTabs(id) {
    tabs.forEach((button) => {
      const selected = button.dataset.mapTab === id;
      button.classList.toggle('is-active', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
  }

  function currentViewBox() {
    if (!mapSvg) return WORLD_VIEW;
    return mapSvg.getAttribute('viewBox').trim().split(/\s+/).map(Number);
  }

  function animateViewBox(target, duration = 420) {
    if (!mapSvg) return;
    if (animationFrame) cancelAnimationFrame(animationFrame);
    const from = currentViewBox();
    const start = performance.now();
    const ease = (t) => 1 - Math.pow(1 - t, 3);
    const tick = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const e = ease(progress);
      const value = from.map((item, index) => item + (target[index] - item) * e);
      mapSvg.setAttribute('viewBox', value.join(' '));
      if (progress < 1) animationFrame = requestAnimationFrame(tick);
      else animationFrame = null;
    };
    animationFrame = requestAnimationFrame(tick);
  }

  function clearSelection() {
    if (selectedPath) selectedPath.classList.remove('is-selected');
    selectedPath = null;
  }

  function applyMapFocus(codes = null) {
    const activeCodes = codes ? new Set(codes) : null;
    pathByIso.forEach((path, iso) => {
      path.classList.toggle('is-muted', Boolean(activeCodes && !activeCodes.has(iso)));
      path.classList.toggle('is-in-focus', Boolean(activeCodes && activeCodes.has(iso)));
    });
  }

  function boundsForCodes(codes) {
    const boxes = (codes || []).map((iso) => pathByIso.get(iso)).filter(Boolean).map((path) => path.getBBox()).filter((box) => Number.isFinite(box.x) && Number.isFinite(box.y));
    if (!boxes.length) return null;
    const left = Math.min(...boxes.map((box) => box.x));
    const top = Math.min(...boxes.map((box) => box.y));
    const right = Math.max(...boxes.map((box) => box.x + box.width));
    const bottom = Math.max(...boxes.map((box) => box.y + box.height));
    let width = right - left;
    let height = bottom - top;
    const padX = Math.max(width * 0.13, 22);
    const padY = Math.max(height * 0.16, 18);
    width += padX * 2;
    height += padY * 2;
    if (width < 150) width = 150;
    if (height < 120) height = 120;
    const centerX = (left + right) / 2;
    const centerY = (top + bottom) / 2;
    return [centerX - width / 2, centerY - height / 2, width, height];
  }

  function setRegion(id, { animate = true } = {}) {
    activeRegion = id;
    activeSubregion = null;
    root.dataset.activeRegion = id;
    delete root.dataset.activeSubregion;
    clearSelection();
    setTabs(id);
    const target = REGION_VIEWS[id] || WORLD_VIEW;
    if (animate) animateViewBox(target);
    else if (mapSvg) mapSvg.setAttribute('viewBox', target.join(' '));
    if (id === 'world') {
      applyMapFocus(null);
      renderWorld();
      return;
    }
    const region = regionById(id);
    if (!region) return;
    applyMapFocus(region.iso2);
    renderRegion(region);
  }

  function setSubregion(id) {
    const subregion = subregionById.get(id);
    if (!subregion) return;
    activeRegion = subregion.regionId;
    activeSubregion = id;
    root.dataset.activeRegion = activeRegion;
    root.dataset.activeSubregion = id;
    clearSelection();
    setTabs(activeRegion);
    applyMapFocus(subregion.iso2);
    renderSubregion(subregion);
    const target = boundsForCodes(subregion.iso2);
    if (target) animateViewBox(target, 430);
  }

  function zoomToCountry(path) {
    if (!mapSvg || !path) return;
    const box = path.getBBox();
    const width = Math.max(box.width * 2.25, 105);
    const height = Math.max(box.height * 2.25, 82);
    const x = box.x + box.width / 2 - width / 2;
    const y = box.y + box.height / 2 - height / 2;
    animateViewBox([x, y, width, height], 360);
  }

  function selectCountry(path, country) {
    if (!path || !country) return;
    clearSelection();
    selectedPath = path;
    path.classList.add('is-selected');
    const regionId = regionByIso.get(country.iso2) || 'world';
    const subregionId = subregionByIso.get(country.iso2) || null;
    activeRegion = regionId;
    activeSubregion = subregionId;
    root.dataset.activeRegion = regionId;
    if (subregionId) root.dataset.activeSubregion = subregionId;
    else delete root.dataset.activeSubregion;
    setTabs(regionId);
    const region = regionById(regionId);
    renderSubregionTabs(region);
    if (subregionBar) {
      [...subregionBar.querySelectorAll('[data-map-subregion]')].forEach((button) => {
        const selected = button.dataset.mapSubregion === subregionId;
        button.classList.toggle('is-active', selected);
        button.setAttribute('aria-pressed', String(selected));
      });
    }
    applyMapFocus(subregionId ? subregionById.get(subregionId)?.iso2 : region?.iso2);
    renderCountry(country, regionId, subregionId);
    zoomToCountry(path);
  }

  function positionTooltip(event) {
    if (!tooltip || !mapWrap) return;
    const rect = mapWrap.getBoundingClientRect();
    const x = Math.min(rect.width - 142, Math.max(12, event.clientX - rect.left + 12));
    const y = Math.min(rect.height - 54, Math.max(12, event.clientY - rect.top + 12));
    tooltip.style.transform = `translate(${x}px, ${y}px)`;
  }

  function appendGradient(defs, id, colors) {
    const gradient = makeSvg('linearGradient', { id, x1: '0%', y1: '0%', x2: '100%', y2: '100%' });
    gradient.append(makeSvg('stop', { offset: '0%', 'stop-color': colors[0] }), makeSvg('stop', { offset: '100%', 'stop-color': colors[1] }));
    defs.append(gradient);
  }

  function buildMap(countryShapes) {
    if (!mapWrap) return;
    mapWrap.classList.add('country-map-wrap');
    const svg = makeSvg('svg', {
      class: 'atlas-country-map',
      viewBox: WORLD_VIEW.join(' '),
      role: 'img',
      'aria-label': '世界から地域へ拡大し、国を直接選べるイラスト地図',
      preserveAspectRatio: 'xMidYMid meet'
    });

    const defs = makeSvg('defs');
    const ocean = makeSvg('linearGradient', { id: 'atlas-ocean', x1: '0%', y1: '0%', x2: '0%', y2: '100%' });
    ocean.append(makeSvg('stop', { offset: '0%', 'stop-color': '#e8f4f2' }), makeSvg('stop', { offset: '58%', 'stop-color': '#eef6f1' }), makeSvg('stop', { offset: '100%', 'stop-color': '#f4f0e4' }));
    defs.append(ocean);
    Object.entries(REGION_COLORS).forEach(([id, colors]) => appendGradient(defs, `land-${id}`, colors));
    const grid = makeSvg('pattern', { id: 'atlas-grid', width: '125', height: '125', patternUnits: 'userSpaceOnUse' });
    grid.append(makeSvg('path', { d: 'M 125 0 L 0 0 0 125', fill: 'none', stroke: '#6f9295', 'stroke-opacity': '.11', 'stroke-width': '1' }));
    defs.append(grid);
    const paper = makeSvg('filter', { id: 'atlas-paper', x: '-5%', y: '-5%', width: '110%', height: '110%' });
    paper.append(makeSvg('feTurbulence', { type: 'fractalNoise', baseFrequency: '.018', numOctaves: '3', seed: '9', result: 'noise' }), makeSvg('feColorMatrix', { in: 'noise', type: 'matrix', values: '1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 .10 0', result: 'texture' }), makeSvg('feBlend', { in: 'SourceGraphic', in2: 'texture', mode: 'multiply' }));
    defs.append(paper);
    svg.append(defs);

    svg.append(
      makeSvg('rect', { class: 'country-map-ocean', x: '0', y: '-30', width: '2000', height: '1090', rx: '28', fill: 'url(#atlas-ocean)' }),
      makeSvg('ellipse', { class: 'country-map-wash country-map-wash--one', cx: '360', cy: '310', rx: '360', ry: '205' }),
      makeSvg('ellipse', { class: 'country-map-wash country-map-wash--two', cx: '1510', cy: '310', rx: '420', ry: '225' }),
      makeSvg('ellipse', { class: 'country-map-wash country-map-wash--three', cx: '1130', cy: '770', rx: '360', ry: '180' }),
      makeSvg('rect', { class: 'country-map-grid', x: '0', y: '-30', width: '2000', height: '1090', fill: 'url(#atlas-grid)' }),
      makeSvg('rect', { class: 'country-map-paper', x: '0', y: '-30', width: '2000', height: '1090', filter: 'url(#atlas-paper)' })
    );

    const iceLayer = makeSvg('g', { class: 'country-map-ice-layer', 'aria-hidden': 'true' });
    const countryLayer = makeSvg('g', { class: 'country-map-layer' });
    countryShapes.forEach(({ id, shape }) => {
      const iso = String(id || '').toUpperCase();
      const country = destinationByIso.get(iso);
      if (iso === 'AQ') iceLayer.append(makeSvg('path', { d: shape, class: 'antarctica-glow' }));
      const path = makeSvg('path', { d: shape });
      path.dataset.iso = iso;
      if (!country) {
        path.classList.add('country-shape', 'is-outside-atlas');
        countryLayer.append(path);
        return;
      }
      const regionId = regionByIso.get(iso) || 'world';
      const tone = Math.abs(iso.charCodeAt(0) + iso.charCodeAt(1)) % 4;
      path.classList.add('country-shape', 'is-destination', `tone-${tone}`);
      path.dataset.region = regionId;
      path.style.fill = `url(#land-${regionId})`;
      path.setAttribute('tabindex', '0');
      path.setAttribute('role', 'button');
      path.setAttribute('aria-label', `${country.nameJa}を選ぶ`);
      const nativeTitle = makeSvg('title');
      nativeTitle.textContent = `${country.nameJa} / ${country.nameEn}`;
      path.append(nativeTitle);
      path.addEventListener('pointerenter', (event) => {
        if (tooltip) {
          tooltip.innerHTML = `<strong>${country.nameJa}</strong><span>${country.nameEn}</span>`;
          tooltip.hidden = false;
          positionTooltip(event);
        }
      });
      path.addEventListener('pointermove', positionTooltip);
      path.addEventListener('pointerleave', () => { if (tooltip) tooltip.hidden = true; });
      path.addEventListener('click', () => selectCountry(path, country));
      path.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          selectCountry(path, country);
        }
      });
      pathByIso.set(iso, path);
      countryLayer.append(path);
    });
    svg.append(iceLayer, countryLayer);

    tooltip = document.createElement('div');
    tooltip.className = 'map-tooltip';
    tooltip.hidden = true;
    const hint = document.createElement('p');
    hint.className = 'map-hint';
    hint.textContent = '世界 → 大地域 → 小地域 → 地図上の国';
    mapWrap.replaceChildren(svg, tooltip, hint);
    mapSvg = svg;
    root.classList.add('has-country-map');
  }

  tabs.forEach((button) => button.addEventListener('click', () => setRegion(button.dataset.mapTab)));
  if (headingCopy) headingCopy.textContent = '世界から地域へ寄りながら、最後は地図上の国そのものを選択。場所から次の旅先を見つけよう。';

  Promise.all([
    import('https://cdn.jsdelivr.net/npm/world-map-country-shapes@1.0.0/index.js').then((module) => module.default || []),
    fetch('data/region-taxonomy.json?v=20260822-2252').then((response) => { if (!response.ok) throw new Error('Region taxonomy not found'); return response.json(); }),
    fetch('data/atlas-destinations.json?v=20260822-2252').then((response) => { if (!response.ok) throw new Error('Destination registry not found'); return response.json(); }),
    fetch('data/theme-taxonomy.json?v=20260822-2252').then((response) => { if (!response.ok) throw new Error('Theme taxonomy not found'); return response.json(); })
  ]).then(([countryShapes, regionData, destinationData, themeData]) => {
    regions = regionData.regions || [];
    destinations = destinationData.destinations || [];
    themes = themeData.themes || [];
    destinationByIso = new Map(destinations.map((country) => [country.iso2, country]));
    buildRegionLookup();
    buildMap(countryShapes);
    setRegion('world', { animate: false });
  }).catch((error) => {
    console.error('[JOURNEY ATLAS map]', error);
    if (copy) copy.textContent = '地図データを読み込めませんでした。';
    if (count) count.textContent = '';
    if (status) status.textContent = '再読み込みしてください。';
  });
})();
