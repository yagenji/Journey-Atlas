const app = document.querySelector('#app');
const countryTemplate = document.querySelector('#country-template');
const embeddedSlug = document.documentElement.dataset.country;
const querySlug = new URLSearchParams(window.location.search).get('country');
const slug = embeddedSlug || querySlug || 'iceland';
const safeSlug = /^[a-z0-9-]+$/.test(slug) ? slug : 'iceland';
const DATA_VERSION = '20260828-estonia-review';
const ICON_SPRITE = 'assets/icons/atlas-icons.svg';
const SITE_ORIGIN = 'https://atlas.yagenji.com/';

const countryRequest = fetch(`data/countries/${safeSlug}.json?v=${DATA_VERSION}`, { cache: 'no-store' })
  .then((response) => {
    if (!response.ok) throw new Error('Country data not found');
    return response.json();
  });

const registryRequest = fetch(`data/atlas-destinations.json?v=${DATA_VERSION}`, { cache: 'no-store' })
  .then((response) => response.ok ? response.json() : { destinations: [] })
  .catch(() => ({ destinations: [] }));

Promise.all([countryRequest, registryRequest])
  .then(([data, registry]) => renderCountry(data, registry.destinations || []))
  .catch(() => {
    app.innerHTML = '<div class="error"><p>PAGE NOT FOUND</p><h1>旅のページを見つけられませんでした。</h1><a href="./">トップへ戻る</a></div>';
  });

function getValue(source, path) {
  return path.split('.').reduce((value, key) => value?.[key], source);
}

function escapeHtml(value = '') {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

const ICON_ALIASES = new Map([
  ['地域', 'globe'], ['首都', 'landmark'], ['人口', 'users'], ['面積', 'map'], ['言語', 'language'], ['主な宗教', 'culture'], ['通貨', 'coin'],
  ['人口密度', 'users'], ['氷河', 'ice'], ['再生可能電力', 'energy'],
  ['火山', 'volcano'], ['滝', 'waterfall'], ['黒砂海岸', 'shore'], ['地熱', 'geothermal'], ['温泉', 'hot-spring'], ['オーロラ', 'aurora'], ['ロードトリップ', 'road'],
  ['景色のために旅する人', 'landscape'], ['ロードトリップが好きな人', 'road'], ['写真を撮る人', 'camera'], ['歩くことが好きな人', 'hike'], ['静かな場所が好きな人', 'quiet'],
  ['昼と夜が大きく変わる', 'sun'], ['道路は旅の一部', 'road'], ['火山と氷河が隣り合う', 'volcano']
]);

const backgroundObserver = 'IntersectionObserver' in window
  ? new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        const source = entry.target.dataset.lazyBackground;
        delete entry.target.dataset.lazyBackground;
        if (source) applyBackground(entry.target, source);
      });
    }, { rootMargin: '700px 0px' })
  : null;

function iconName(item, fallback = 'compass') {
  if (item?.icon) return item.icon;
  return ICON_ALIASES.get(item?.label) || ICON_ALIASES.get(item?.title) || fallback;
}

function iconSvg(name, className = 'ui-icon') {
  const safeName = /^[a-z0-9-]+$/.test(name || '') ? name : 'compass';
  return `<svg class="${className}" aria-hidden="true" viewBox="0 0 24 24"><use href="${ICON_SPRITE}#${safeName}"></use></svg>`;
}

function renderCountry(data, registry) {
  const fragment = countryTemplate.content.cloneNode(true);
  fragment.querySelectorAll('[data-field]').forEach((element) => {
    const key = element.dataset.field;
    const value = key === 'sceneCount' ? (data.scenes || []).length : getValue(data, key);
    element.textContent = value ?? '';
  });

  const heroTitle = fragment.querySelector('.hero h1');
  if (heroTitle) {
    const normalizedTitle = (data.nameEn || '').trim();
    const titleLength = Array.from(normalizedTitle.replace(/\s+/g, '')).length;
    if (titleLength >= 12) heroTitle.classList.add('hero-title--long');
    if (titleLength >= 18) heroTitle.classList.add('hero-title--very-long');
    if (!/\s/.test(normalizedTitle) && titleLength >= 10) {
      heroTitle.classList.add('hero-title--unbroken-long');
    }
  }

  const heroArt = fragment.querySelector('[data-image-field="hero.image"]');
  if (heroArt) {
    const heroLabel = data.hero?.location || data.nameJa || data.nameEn || '代表風景';
    heroArt.setAttribute('aria-label', `代表風景: ${heroLabel}`);
  }
  setBackground(heroArt, data.hero?.image);
  renderMapBase(fragment, data.map);
  renderCapitalMarker(fragment, data.capital, data.map?.bounds);
  renderScenes(fragment, data.scenes, data.map?.bounds);
  renderHeroMarker(fragment, data.hero, data.map?.bounds);
  renderEncounters(fragment, data.encounters);
  renderSignatureFacts(fragment, data.signatureFacts);
  renderAtlasExtras(fragment, data.atlasExtras);
  renderTravelTrivia(fragment, data.travelTrivia);
  renderSeasons(fragment, data.seasons);
  renderTransport(fragment, data.transport);
  renderPersonas(fragment, data.personas);
  renderFacts(fragment, data.facts);
  renderTips(fragment, data.tips);
  renderRelated(fragment, data.relatedCountries, registry);
  renderPhotoCredits(fragment, data.photoCredits);

  app.replaceChildren(fragment);
  updatePageMetadata(data);
  initWishButton(data.slug);

  const scenes = data.scenes || [];
  const requestedScene = getSceneFromHash(scenes) || scenes[0]?.id;
  setActiveScene(requestedScene, false);

  window.addEventListener('hashchange', () => {
    const sceneId = getSceneFromHash(scenes);
    if (sceneId) setActiveScene(sceneId, true);
  });
}

function setMeta(selector, value, attribute = 'content') {
  const element = document.querySelector(selector);
  if (element && value) element.setAttribute(attribute, value);
}

function updatePageMetadata(data) {
  const title = `${data.nameJa} | ${data.nameEn} — JOURNEY ATLAS`;
  const description = data.seo?.description || data.hero?.lead || `${data.nameJa}を景色と地図からめぐるJOURNEY ATLAS。`;
  const canonical = `${SITE_ORIGIN}countries/${data.slug}/`;
  const heroImage = data.seo?.ogImage || data.hero?.image;
  const absoluteImage = heroImage && !heroImage.endsWith('.parts.json') && !heroImage.endsWith('.b64')
    ? new URL(heroImage, SITE_ORIGIN).href
    : `${SITE_ORIGIN}assets/icons/favicon.svg`;

  document.title = title;
  setMeta('#meta-description', description);
  setMeta('#canonical-link', canonical, 'href');
  setMeta('#og-title', title);
  setMeta('#og-description', description);
  setMeta('#og-url', canonical);
  setMeta('#og-image', absoluteImage);
}

function resolveImageSource(source) {
  if (!source || typeof source !== 'string') return Promise.reject(new Error('Image source missing'));
  if (source.endsWith('.parts.json')) {
    return fetch(`${source}?v=${DATA_VERSION}`, { cache: 'no-store' })
      .then((response) => {
        if (!response.ok) throw new Error('Image manifest missing');
        return response.json();
      })
      .then((manifest) => {
        const parts = Array.isArray(manifest.parts) ? manifest.parts : [];
        if (!parts.length) throw new Error('Image manifest has no parts');
        return Promise.all(parts.map((part) =>
          fetch(`${part}${part.includes('?') ? '&' : '?'}v=${manifest.version || DATA_VERSION}`, { cache: 'no-store' })
            .then((response) => {
              if (!response.ok) throw new Error(`Image part missing: ${part}`);
              return response.text();
            })
        )).then((chunks) => {
          const encoded = chunks.join('').replace(/\s+/g, '');
          if (manifest.signature && !encoded.startsWith(manifest.signature)) throw new Error('Encoded image signature mismatch');
          return `data:${manifest.mime || 'image/webp'};base64,${encoded}`;
        });
      });
  }
  if (!source.endsWith('.b64')) return Promise.resolve(source);
  return fetch(`${source}?v=${DATA_VERSION}`, { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error('Encoded image missing');
      return response.text();
    })
    .then((encoded) => {
      const clean = encoded.trim();
      if (!clean.startsWith('UklGR')) throw new Error('Encoded image is not WebP');
      return `data:image/webp;base64,${clean}`;
    });
}

function renderMapBase(fragment, mapData) {
  if (!mapData?.svg) return;
  const mapArt = fragment.querySelector('#country-map-art');
  const placeholder = mapArt.querySelector('.map-placeholder');
  const grid = mapArt.querySelector('.map-grid');
  const image = document.createElement('img');
  image.className = 'map-base';
  image.alt = '';
  image.decoding = 'async';
  image.loading = 'lazy';
  image.fetchPriority = 'low';
  image.addEventListener('load', () => {
    placeholder.hidden = true;
    grid.hidden = true;
    mapArt.classList.add('has-map');
  });
  image.addEventListener('error', () => {
    image.remove();
    placeholder.hidden = false;
    grid.hidden = false;
  });
  resolveImageSource(mapData.svg).then((resolvedSource) => { image.src = resolvedSource; }).catch(() => image.dispatchEvent(new Event('error')));
  mapArt.prepend(image);
}

function applyBackground(element, image) {
  resolveImageSource(image)
    .then((resolvedSource) => {
      element.style.backgroundImage = `url("${resolvedSource}")`;
      element.classList.add('has-image');
      element.querySelectorAll('.art-placeholder, .scene-placeholder').forEach((placeholder) => { placeholder.hidden = true; });
    })
    .catch(() => {});
}

function setBackground(element, image, options = {}) {
  if (!element || !image) return;
  if (options.lazy && backgroundObserver) {
    element.dataset.lazyBackground = image;
    backgroundObserver.observe(element);
    return;
  }
  applyBackground(element, image);
}

function projectPoint(coordinates, bounds, offset = {}) {
  if (!coordinates || !bounds) return null;
  const longitudeRange = bounds.east - bounds.west;
  const latitudeRange = bounds.north - bounds.south;
  if (longitudeRange <= 0 || latitudeRange <= 0) return null;

  const mapWidth = 1200;
  const mapHeight = 760;
  const midpointLatitude = (bounds.south + bounds.north) / 2;
  const longitudeScale = Math.cos((midpointLatitude * Math.PI) / 180);
  const projectedWidth = longitudeRange * longitudeScale;
  const projectedHeight = latitudeRange;
  const canvasScale = Math.min(mapWidth / projectedWidth, mapHeight / projectedHeight);
  const drawWidth = projectedWidth * canvasScale;
  const drawHeight = projectedHeight * canvasScale;
  const offsetX = (mapWidth - drawWidth) / 2;
  const offsetY = (mapHeight - drawHeight) / 2;

  const xPx = offsetX + (coordinates.longitude - bounds.west) * longitudeScale * canvasScale;
  const yPx = offsetY + (bounds.north - coordinates.latitude) * canvasScale;
  const x = (xPx / mapWidth) * 100 + (Number(offset.x) || 0);
  const y = (yPx / mapHeight) * 100 + (Number(offset.y) || 0);
  return { x: Math.max(0, Math.min(100, x)), y: Math.max(0, Math.min(100, y)) };
}

function renderCapitalMarker(fragment, capital, bounds) {
  const markers = fragment.querySelector('#map-markers');
  const point = projectPoint(capital?.coordinates, bounds, capital?.mapOffset);
  if (!markers || !point) return;
  const marker = document.createElement('div');
  marker.className = 'map-capital-marker';
  marker.style.left = `${point.x}%`;
  marker.style.top = `${point.y}%`;
  marker.dataset.labelPosition = capital.labelPosition || 'right';
  marker.setAttribute('role', 'img');
  marker.setAttribute('aria-label', `首都: ${capital.nameJa || capital.nameEn || ''}`);
  marker.innerHTML = `<i aria-hidden="true"></i><span>${escapeHtml(capital.nameJa || capital.nameEn || '')}</span>`;
  markers.append(marker);
}

function renderSceneName(element, name, preferredBreaks = []) {
  const characters = Array.from(name || '');
  const breakPositions = new Set((Array.isArray(preferredBreaks) ? preferredBreaks : []).filter((position) => Number.isInteger(position) && position > 0 && position < characters.length));
  characters.forEach((character, index) => {
    if (breakPositions.has(index)) element.append(document.createElement('wbr'));
    element.append(document.createTextNode(character));
  });
}

function renderScenes(fragment, scenes = [], bounds) {
  const cards = fragment.querySelector('#scene-cards');
  const markers = fragment.querySelector('#map-markers');
  scenes.forEach((scene, index) => {
    const number = String(index + 1);
    const card = document.createElement('article');
    card.className = 'scene-card';
    card.dataset.scene = scene.id;
    card.id = `scene-${scene.id}`;
    card.tabIndex = 0;
    card.setAttribute('role', 'button');
    card.setAttribute('aria-pressed', 'false');
    card.setAttribute('aria-label', `${number} ${scene.name}を選択`);
    card.innerHTML = `<div class="scene-image media-slot"><span class="scene-placeholder">SCENE ${number}<small>実景イラスト差し替え領域</small></span><b>${number}</b></div><div class="scene-copy"><strong>${number}</strong><div><h3></h3><small>${escapeHtml(scene.nameLocal)}</small><p>${escapeHtml(scene.description)}</p></div></div>`;
    renderSceneName(card.querySelector('h3'), scene.name, scene.nameBreaks);
    const sceneImage = card.querySelector('.scene-image');
    sceneImage.setAttribute('role', 'img');
    sceneImage.setAttribute('aria-label', `景色 ${number}: ${scene.name}`);
    setBackground(sceneImage, scene.image, { lazy: true });
    const point = projectPoint(scene.coordinates, bounds, scene.mapOffset);
    if (point) {
      const marker = document.createElement('button');
      marker.type = 'button';
      marker.className = 'map-marker';
      marker.dataset.scene = scene.id;
      marker.style.left = `${point.x}%`;
      marker.style.top = `${point.y}%`;
      marker.setAttribute('aria-label', `${number} ${scene.name}を見る`);
      marker.setAttribute('aria-pressed', 'false');
      if (scene.labelPosition) marker.dataset.labelPosition = scene.labelPosition;
      marker.innerHTML = `<b>${number}</b><span>${escapeHtml(scene.mapLabel)}</span>`;
      bindSceneActivation(marker, scene.id, true);
      markers.append(marker);
    }
    bindSceneActivation(card, scene.id, false);
    cards.append(card);
  });
}

function renderHeroMarker(fragment, hero, bounds) {
  const markers = fragment.querySelector('#map-markers');
  const point = projectPoint(hero?.coordinates, bounds, hero?.mapOffset);
  if (!markers || !point) return;
  const marker = document.createElement('div');
  marker.className = 'map-hero-marker';
  marker.style.left = `${point.x}%`;
  marker.style.top = `${point.y}%`;
  marker.setAttribute('role', 'img');
  marker.setAttribute('aria-label', `代表画像の場所: ${hero.location || ''}`);
  marker.innerHTML = '<span aria-hidden="true"></span>';
  markers.append(marker);
}

function bindSceneActivation(element, id, scrollOnClick) {
  element.addEventListener('mouseenter', () => setActiveScene(id, false));
  element.addEventListener('focus', () => setActiveScene(id, false));
  element.addEventListener('click', () => {
    setActiveScene(id, scrollOnClick);
    history.replaceState(null, '', `#${id}`);
  });
  element.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      setActiveScene(id, scrollOnClick);
      history.replaceState(null, '', `#${id}`);
    }
  });
}

function setActiveScene(id, shouldScroll = false) {
  if (!id) return;
  document.querySelectorAll('[data-scene]').forEach((element) => {
    const active = element.dataset.scene === id;
    element.classList.toggle('is-active', active);
    if (element.hasAttribute('aria-pressed')) element.setAttribute('aria-pressed', String(active));
  });
  if (shouldScroll) document.querySelector(`.scene-card[data-scene="${id}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function getSceneFromHash(scenes = []) {
  const hash = decodeURIComponent(window.location.hash.replace(/^#/, ''));
  return scenes.some((scene) => scene.id === hash) ? hash : null;
}

function renderEncounters(fragment, items = []) {
  const container = fragment.querySelector('#encounters');
  items.forEach((item) => {
    const article = document.createElement('article');
    article.innerHTML = `${iconSvg(iconName(item, 'compass'))}<b>${escapeHtml(item.title)}</b>`;
    container.append(article);
  });
}

function renderSignatureFacts(fragment, items = []) {
  const section = fragment.querySelector('#signature-facts-section');
  const container = fragment.querySelector('#signature-facts');
  if (!section || !container || !items.length) {
    if (section) section.hidden = true;
    return;
  }
  items.forEach((item) => {
    const article = document.createElement('article');
    article.innerHTML = `<div class="signature-fact__label">${iconSvg(iconName(item, 'spark'))}<span>${escapeHtml(item.label)}</span></div><strong>${escapeHtml(item.value)}</strong><p>${escapeHtml(item.note || '')}</p>`;
    container.append(article);
  });
  section.hidden = false;
}

function renderAtlasExtras(fragment, items = []) {
  const section = fragment.querySelector('#atlas-extras-section');
  const grid = fragment.querySelector('#atlas-extras-grid');
  if (!section || !grid || !items.length) {
    if (section) section.hidden = true;
    return;
  }
  const themeIcons = { CITY: 'city', HISTORY: 'history', LIFE: 'home', WILDLIFE: 'wildlife', FOOD: 'food', ROAD: 'road', SEA: 'sea', EARTH: 'landscape' };
  items.forEach((item) => {
    const points = Array.isArray(item.points) ? item.points.filter(Boolean) : [];
    const article = document.createElement('article');
    article.className = 'atlas-extra';
    article.innerHTML = `<span class="atlas-extra__theme">${iconSvg(item.icon || themeIcons[item.themeEn] || 'compass', 'ui-icon ui-icon--small')}${escapeHtml(item.themeEn)} / ${escapeHtml(item.themeJa)}</span><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.text)}</p>${points.length ? `<ul>${points.map((point) => `<li>${escapeHtml(point)}</li>`).join('')}</ul>` : ''}`;
    grid.append(article);
  });
  section.hidden = false;
}

function renderTravelTrivia(fragment, items = []) {
  const section = fragment.querySelector('#travel-trivia-section');
  const grid = fragment.querySelector('#travel-trivia-grid');
  if (!section || !grid || !items.length) {
    if (section) section.hidden = true;
    return;
  }
  items.slice(0, 6).forEach((item) => {
    const article = document.createElement('article');
    article.className = 'travel-trivia__item';
    article.innerHTML = `<div class="travel-trivia__meta">${iconSvg(item.icon || 'spark')}<span>${escapeHtml(item.categoryEn || 'TRIVIA')} / ${escapeHtml(item.categoryJa || '')}</span></div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.text)}</p>`;
    grid.append(article);
  });
  section.hidden = false;
}

function renderSeasons(fragment, items = []) {
  const container = fragment.querySelector('#seasons');
  const defaults = ['sun', 'aurora', 'snow', 'leaf'];
  items.forEach((item, index) => {
    const article = document.createElement('article');
    article.style.setProperty('--season-color', item.color || '#75824e');
    article.innerHTML = `${iconSvg(item.icon || defaults[index] || 'calendar')}<div><b>${escapeHtml(item.months)}</b><p>${escapeHtml(item.text)}</p></div>`;
    container.append(article);
  });
}

function renderTransport(fragment, item = {}) {
  const container = fragment.querySelector('#transport');
  container.innerHTML = `${iconSvg(item.icon || 'road')}<div><small>移動</small><h3>${escapeHtml(item.title || '')}</h3><p>${escapeHtml(item.text || '')}</p></div>${item.distance ? `<b>${escapeHtml(item.distance)}<small>km</small></b>` : ''}`;
}

function renderPersonas(fragment, items = []) {
  const container = fragment.querySelector('#personas');
  items.forEach((item) => {
    const article = document.createElement('article');
    article.innerHTML = `${iconSvg(iconName(item, 'traveler'))}<div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.text)}</p></div>`;
    container.append(article);
  });
}

function renderFacts(fragment, facts = []) {
  const container = fragment.querySelector('#facts');
  facts.forEach((fact) => {
    const group = document.createElement('div');
    group.innerHTML = `${iconSvg(iconName(fact, 'info'))}<div><dt>${escapeHtml(fact.label)}</dt><dd>${escapeHtml(fact.value)}</dd></div>`;
    container.append(group);
  });
}

function renderTips(fragment, tips = []) {
  const container = fragment.querySelector('#tips');
  tips.forEach((tip) => {
    const article = document.createElement('article');
    article.innerHTML = `${iconSvg(iconName(tip, 'note'))}<div><h3>${escapeHtml(tip.title)}</h3><p>${escapeHtml(tip.text)}</p></div>`;
    container.append(article);
  });
}

function renderRelated(fragment, countries = [], registry = []) {
  const container = fragment.querySelector('#related');
  const published = new Map(registry.filter((item) => item?.slug && item?.atlasPublished && item?.href).map((item) => [item.slug, item]));
  countries.forEach((country) => {
    const destination = published.get(country.slug);
    const article = document.createElement(destination ? 'a' : 'article');
    article.className = `related-card${destination ? ' is-open' : ' is-coming'}`;
    if (destination) {
      article.href = destination.href;
      article.setAttribute('aria-label', `${country.nameJa}のJOURNEY ATLASを見る`);
    }
    article.innerHTML = `<div class="related-country"><span class="related-flag" aria-hidden="true">${country.flag || '◌'}</span><div class="related-copy"><h3>${escapeHtml(country.nameEn)}</h3><b>${escapeHtml(country.nameJa)}</b><p>${escapeHtml(country.reason)}</p><small class="related-status">${destination ? 'EXPLORE →' : 'COMING SOON'}</small></div></div>`;
    container.append(article);
  });
}

function renderPhotoCredits(fragment, items = []) {
  const section = fragment.querySelector('#photo-credits');
  const list = fragment.querySelector('#photo-credit-list');
  if (!section || !list || !Array.isArray(items) || !items.length) return;
  items.forEach((item) => {
    const li = document.createElement('li');
    const label = escapeHtml(item.label || 'Photo');
    const author = escapeHtml(item.author || '');
    const license = escapeHtml(item.license || '');
    if (item.url) {
      li.innerHTML = `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${label}</a><span>${author}${author && license ? ' / ' : ''}${license}</span>`;
    } else {
      li.innerHTML = `<span>${label}${author ? ` — ${author}` : ''}${license ? ` / ${license}` : ''}</span>`;
    }
    list.append(li);
  });
  section.hidden = false;
}

function initWishButton(countrySlug) {
  const button = document.querySelector('#wish-button');
  const status = document.querySelector('#wish-status');
  if (!button) return;
  const storageKey = `journey-atlas:wish:${countrySlug}`;
  let wished = false;
  try { wished = localStorage.getItem(storageKey) === 'true'; } catch { if (status) status.textContent = 'このブラウザでは保存機能を利用できません。'; }
  const update = () => {
    button.classList.toggle('is-saved', wished);
    button.querySelector('.wish-icon').textContent = wished ? '♥' : '♡';
    button.querySelector('strong').textContent = wished ? '行きたい国に保存しました' : 'この国に行きたい';
    button.setAttribute('aria-pressed', String(wished));
  };
  update();
  button.addEventListener('click', () => {
    wished = !wished;
    try {
      localStorage.setItem(storageKey, String(wished));
      if (status) status.textContent = wished ? 'このブラウザに保存しました。' : '保存を解除しました。';
    } catch {
      wished = !wished;
      if (status) status.textContent = 'このブラウザでは保存機能を利用できません。';
    }
    update();
  });
}
