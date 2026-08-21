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
    app.innerHTML = '<div class="error wrap"><p class="eyebrow">PAGE NOT FOUND</p><h1>旅のページを見つけられませんでした。</h1><a href="./">Icelandへ戻る</a></div>';
  });

function renderCountry(data) {
  const fragment = countryTemplate.content.cloneNode(true);
  fragment.querySelectorAll('[data-field]').forEach((element) => {
    const value = data[element.dataset.field] ?? (element.dataset.field === 'sceneCount' ? data.scenes.length : '');
    element.textContent = value;
  });

  setBackground(fragment.querySelector('[data-image-field="heroImage"]'), data.heroImage);
  renderScenes(fragment, data.scenes);
  renderEncounters(fragment, data.encounters);
  renderSeasons(fragment, data.seasons);
  renderPersonas(fragment, data.personas);
  renderFacts(fragment, data.facts);
  renderTips(fragment, data.tips);
  renderRelated(fragment, data.relatedCountries);

  app.replaceChildren(fragment);
  document.title = `${data.nameEn} — JOURNEY ATLAS`;
  initWishButton(data.slug);
}

function setBackground(element, image) {
  if (!image) return;
  element.style.backgroundImage = `linear-gradient(180deg, rgba(19,36,38,.05), rgba(19,36,38,.24)), url("${image}")`;
  element.classList.add('has-image');
}

function renderScenes(fragment, scenes) {
  const cards = fragment.querySelector('#scene-cards');
  const markers = fragment.querySelector('#map-markers');

  scenes.forEach((scene, index) => {
    const number = String(index + 1).padStart(2, '0');
    const card = document.createElement('article');
    card.className = 'scene-card';
    card.dataset.scene = scene.id;
    card.tabIndex = 0;
    card.innerHTML = `
      <div class="scene-image media-placeholder"><span>SCENE ${number}</span></div>
      <div class="scene-copy"><b>${number}</b><div><h3>${scene.name}</h3><p>${scene.description}</p></div></div>`;
    setBackground(card.querySelector('.scene-image'), scene.image);

    const marker = document.createElement('button');
    marker.type = 'button';
    marker.className = 'map-marker';
    marker.dataset.scene = scene.id;
    marker.setAttribute('aria-label', `${number} ${scene.name}を強調`);
    marker.textContent = number;

    const activate = () => setActiveScene(scene.id);
    ['mouseenter', 'focus', 'click'].forEach((eventName) => card.addEventListener(eventName, activate));
    ['mouseenter', 'focus', 'click'].forEach((eventName) => marker.addEventListener(eventName, activate));
    cards.append(card);
    markers.append(marker);
  });
}

function setActiveScene(id) {
  document.querySelectorAll('[data-scene]').forEach((element) => {
    const active = element.dataset.scene === id;
    element.classList.toggle('is-active', active);
    if (element.matches('button')) element.setAttribute('aria-pressed', String(active));
  });
}

function renderEncounters(fragment, items) {
  const container = fragment.querySelector('#encounters');
  items.forEach((item, index) => {
    const article = document.createElement('article');
    article.innerHTML = `<span>${String(index + 1).padStart(2, '0')}</span><div class="encounter-symbol" aria-hidden="true">${item.symbol}</div><h3>${item.title}</h3><p>${item.text}</p>`;
    container.append(article);
  });
}

function renderSeasons(fragment, items) {
  const container = fragment.querySelector('#seasons');
  items.forEach((item) => {
    const article = document.createElement('article');
    article.innerHTML = `<div><span>${item.months}</span><h3>${item.title}</h3></div><p>${item.text}</p>`;
    container.append(article);
  });
}

function renderPersonas(fragment, items) {
  const container = fragment.querySelector('#personas');
  items.forEach((item, index) => {
    const p = document.createElement('p');
    p.innerHTML = `<span>${String(index + 1).padStart(2, '0')}</span>${item}`;
    container.append(p);
  });
}

function renderFacts(fragment, facts) {
  const container = fragment.querySelector('#facts');
  facts.forEach((fact) => {
    const group = document.createElement('div');
    group.innerHTML = `<dt>${fact.label}</dt><dd>${fact.value}</dd>`;
    container.append(group);
  });
}

function renderTips(fragment, tips) {
  const container = fragment.querySelector('#tips');
  tips.forEach((tip, index) => {
    const article = document.createElement('article');
    article.innerHTML = `<span>${String(index + 1).padStart(2, '0')}</span><h3>${tip.title}</h3><p>${tip.text}</p>`;
    container.append(article);
  });
}

function renderRelated(fragment, countries) {
  const container = fragment.querySelector('#related');
  countries.forEach((country) => {
    const article = document.createElement('article');
    article.className = 'related-card';
    article.innerHTML = `<div class="related-image media-placeholder"><span>FUTURE JOURNEY</span></div><p>${country.reason}</p><h3>${country.nameEn}<small>${country.nameJa}</small></h3>`;
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
    button.querySelector('span').textContent = wished ? '行きたい国に保存しました' : 'この国に行きたい';
    button.querySelector('b').textContent = wished ? '✓' : '＋';
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

