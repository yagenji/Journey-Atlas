const app = document.querySelector('#app');
const countryTemplate = document.querySelector('#country-template');
const slug = new URLSearchParams(window.location.search).get('country') || 'iceland';
const safeSlug = /^[a-z0-9-]+$/.test(slug) ? slug : 'iceland';

fetch(`data/countries/${safeSlug}.json`)
  .then((response) => {
    if (!response.ok) throw new Error('Country data not found');
    return response.json();
  })
  .then(renderCountry)
  .catch(() => {
    app.innerHTML = '<div class="error"><p>PAGE NOT FOUND</p><h1>旅のページを見つけられませんでした。</h1><a href="./">Icelandへ戻る</a></div>';
  });

function getValue(source, path) {
  return path.split('.').reduce((value, key) => value?.[key], source);
}

function renderCountry(data) {
  const fragment = countryTemplate.content.cloneNode(true);
  fragment.querySelectorAll('[data-field]').forEach((element) => {
    const key = element.dataset.field;
    const value = key === 'sceneCount' ? data.scenes.length : getValue(data, key);
    element.textContent = value ?? '';
  });

  setBackground(fragment.querySelector('[data-image-field="hero.image"]'), data.hero.image);
  renderMapBase(fragment, data.map);
  renderScenes(fragment, data.scenes, data.map.bounds);
  renderEncounters(fragment, data.encounters);
  renderSeasons(fragment, data.seasons);
  renderTransport(fragment, data.transport);
  renderPersonas(fragment, data.personas);
  renderFacts(fragment, data.facts);
  renderTips(fragment, data.tips);
  renderRelated(fragment, data.relatedCountries);

  app.replaceChildren(fragment);
  document.title = `${data.nameEn} — JOURNEY ATLAS`;
  initWishButton(data.slug);
  setActiveScene(data.scenes[0]?.id);
}

function renderMapBase(fragment, mapData) {
  if (!mapData.svg) return;
  const mapArt = fragment.querySelector('#country-map-art');
  const image = document.createElement('img');
  image.className = 'map-base';
  image.src = mapData.svg;
  image.alt = '';
  mapArt.prepend(image);
  mapArt.querySelector('.map-placeholder').hidden = true;
  mapArt.querySelector('.map-grid').hidden = true;
}

function setBackground(element, image) {
  if (!element || !image) return;
  element.style.backgroundImage = `url("${image}")`;
  element.classList.add('has-image');
  element.querySelectorAll('.art-placeholder, .scene-placeholder').forEach((placeholder) => {
    placeholder.hidden = true;
  });
}

function projectPoint(coordinates, bounds) {
  if (!coordinates || !bounds) return null;
  const longitudeRange = bounds.east - bounds.west;
  const latitudeRange = bounds.north - bounds.south;
  return {
    x: ((coordinates.longitude - bounds.west) / longitudeRange) * 100,
    y: ((bounds.north - coordinates.latitude) / latitudeRange) * 100
  };
}

function renderSceneName(element, name, preferredBreaks = []) {
  const characters = Array.from(name);
  const breaks = Array.isArray(preferredBreaks) ? preferredBreaks : [];
  const breakPositions = new Set(
    breaks.filter((position) => Number.isInteger(position) && position > 0 && position < characters.length)
  );

  characters.forEach((character, index) => {
    if (breakPositions.has(index)) element.append(document.createElement('wbr'));
    element.append(document.createTextNode(character));
  });
}

function renderScenes(fragment, scenes, bounds) {
  const cards = fragment.querySelector('#scene-cards');
  const markers = fragment.querySelector('#map-markers');

  scenes.forEach((scene, index) => {
    const number = String(index + 1);
    const card = document.createElement('article');
    card.className = 'scene-card';
    card.dataset.scene = scene.id;
    card.tabIndex = 0;
    card.setAttribute('aria-label', `${number} ${scene.name}`);
    card.innerHTML = `
      <div class="scene-image media-slot"><span class="scene-placeholder">SCENE ${number}<small>実景イラスト差し替え領域</small></span><b>${number}</b></div>
      <div class="scene-copy">
        <strong>${number}</strong>
        <div><h3></h3><small>${scene.nameLocal}</small><p>${scene.description}</p></div>
      </div>`;
    renderSceneName(card.querySelector('h3'), scene.name, scene.nameBreaks);
    setBackground(card.querySelector('.scene-image'), scene.image);

    const point = projectPoint(scene.coordinates, bounds);
    if (point) {
      const marker = document.createElement('button');
      marker.type = 'button';
      marker.className = 'map-marker';
      marker.dataset.scene = scene.id;
      marker.style.left = `${point.x}%`;
      marker.style.top = `${point.y}%`;
      marker.setAttribute('aria-label', `${number} ${scene.name}を強調`);
      marker.setAttribute('aria-pressed', 'false');
      marker.innerHTML = `<b>${number}</b><span>${scene.mapLabel}</span>`;
      bindSceneActivation(marker, scene.id);
      markers.append(marker);
    }

    bindSceneActivation(card, scene.id);
    cards.append(card);
  });
}

function bindSceneActivation(element, id) {
  ['mouseenter', 'focus', 'click'].forEach((eventName) => {
    element.addEventListener(eventName, () => setActiveScene(id));
  });
}

function setActiveScene(id) {
  if (!id) return;
  document.querySelectorAll('[data-scene]').forEach((element) => {
    const active = element.dataset.scene === id;
    element.classList.toggle('is-active', active);
    if (element.matches('button')) element.setAttribute('aria-pressed', String(active));
  });
}

function renderEncounters(fragment, items) {
  const container = fragment.querySelector('#encounters');
  items.forEach((item) => {
    const article = document.createElement('article');
    article.innerHTML = `<span aria-hidden="true">${item.symbol}</span><b>${item.title}</b>`;
    container.append(article);
  });
}

function renderSeasons(fragment, items) {
  const container = fragment.querySelector('#seasons');
  items.forEach((item) => {
    const article = document.createElement('article');
    article.style.setProperty('--season-color', item.color);
    article.innerHTML = `<span class="season-symbol" aria-hidden="true">${item.symbol}</span><b>${item.months}</b><p>${item.text}</p>`;
    container.append(article);
  });
}

function renderTransport(fragment, item) {
  const container = fragment.querySelector('#transport');
  container.innerHTML = `<span aria-hidden="true">${item.symbol}</span><div><small>移動</small><h3>${item.title}</h3><p>${item.text}</p></div>${item.distance ? `<b>${item.distance}<small>km</small></b>` : ''}`;
}

function renderPersonas(fragment, items) {
  const container = fragment.querySelector('#personas');
  items.forEach((item) => {
    const article = document.createElement('article');
    article.innerHTML = `<span aria-hidden="true">${item.symbol}</span><div><h3>${item.title}</h3><p>${item.text}</p></div>`;
    container.append(article);
  });
}

function renderFacts(fragment, facts) {
  const container = fragment.querySelector('#facts');
  facts.forEach((fact) => {
    const group = document.createElement('div');
    group.innerHTML = `<span aria-hidden="true">${fact.symbol}</span><div><dt>${fact.label}</dt><dd>${fact.value}</dd></div>`;
    container.append(group);
  });
}

function renderTips(fragment, tips) {
  const container = fragment.querySelector('#tips');
  tips.forEach((tip) => {
    const article = document.createElement('article');
    article.innerHTML = `<span aria-hidden="true">${tip.symbol}</span><div><h3>${tip.title}</h3><p>${tip.text}</p></div>`;
    container.append(article);
  });
}

function renderRelated(fragment, countries) {
  const container = fragment.querySelector('#related');
  countries.forEach((country) => {
    const article = document.createElement('article');
    article.className = 'related-card';
    article.innerHTML = `<div class="related-image media-slot"><span>FUTURE ARTWORK</span><div><h3>${country.nameEn}</h3><b>${country.nameJa}</b><p>${country.reason}</p></div></div>`;
    setBackground(article.querySelector('.related-image'), country.image);
    container.append(article);
  });
}

function initWishButton(countrySlug) {
  const button = document.querySelector('#wish-button');
  const status = document.querySelector('#wish-status');
  const storageKey = `journey-atlas:wish:${countrySlug}`;
  let wished = localStorage.getItem(storageKey) === 'true';

  const update = () => {
    button.classList.toggle('is-saved', wished);
    button.querySelector('.wish-icon').textContent = wished ? '♥' : '♡';
    button.querySelector('strong').textContent = wished ? '行きたい国に保存しました' : 'この国に行きたい';
    button.setAttribute('aria-pressed', String(wished));
  };
  update();

  button.addEventListener('click', () => {
    wished = !wished;
    localStorage.setItem(storageKey, String(wished));
    status.textContent = wished ? 'この端末に保存しました。' : '保存を解除しました。';
    update();
  });
}
