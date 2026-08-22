const rail = document.querySelector('#country-rail');
const grid = document.querySelector('#country-grid');
const count = document.querySelector('#country-count');
const prev = document.querySelector('[data-country-scroll="prev"]');
const next = document.querySelector('[data-country-scroll="next"]');
const toggleAll = document.querySelector('#all-countries-toggle');
const allPanel = document.querySelector('#all-countries-panel');
const searchInput = document.querySelector('#country-search');
const empty = document.querySelector('#country-empty');
const wishButton = document.querySelector('#wish-link');
const toast = document.querySelector('#top-toast');
const dots = [...document.querySelectorAll('.rail-dots i')];
const heroImage = document.querySelector('#hero-image');
const heroVisual = document.querySelector('#hero-visual');
const heroButtons = [...document.querySelectorAll('[data-hero]')];

let destinations = [];
let heroSources = [];
let heroIndex = 0;
let heroTimer;

const heroFiles = [1, 2, 3, 4, 5].map((n) => `assets/images/top/hero-set-${n}.webp.b64`);

Promise.all(heroFiles.map(async (file) => {
  const response = await fetch(file);
  if (!response.ok) throw new Error(`Hero source missing: ${file}`);
  return `data:image/webp;base64,${(await response.text()).trim()}`;
})).then((sources) => {
  heroSources = sources;
  setHero(0, false);
  startHeroRotation();
}).catch(() => {
  heroSources = [];
});

function setHero(index, animate = true) {
  if (!heroImage || heroSources.length === 0) return;
  heroIndex = (index + heroSources.length) % heroSources.length;
  if (animate) heroVisual?.classList.add('is-changing');
  window.setTimeout(() => {
    heroImage.src = heroSources[heroIndex];
    heroButtons.forEach((button, i) => button.classList.toggle('is-active', i === heroIndex));
    heroImage.onload = () => heroVisual?.classList.remove('is-changing');
  }, animate ? 160 : 0);
}

function startHeroRotation() {
  window.clearInterval(heroTimer);
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  heroTimer = window.setInterval(() => setHero(heroIndex + 1), 9000);
}

heroButtons.forEach((button) => button.addEventListener('click', () => {
  setHero(Number(button.dataset.hero));
  startHeroRotation();
}));
heroVisual?.addEventListener('mouseenter', () => window.clearInterval(heroTimer));
heroVisual?.addEventListener('mouseleave', startHeroRotation);
document.addEventListener('visibilitychange', () => document.hidden ? window.clearInterval(heroTimer) : startHeroRotation());

fetch('data/atlas-destinations.json')
  .then((response) => {
    if (!response.ok) throw new Error('Destination registry not found');
    return response.json();
  })
  .then(({ destinations: items = [], count: total }) => {
    destinations = sortForDisplay(items);
    if (count) count.textContent = `${total || destinations.length} DESTINATIONS`;
    renderRail(destinations);
    renderGrid(destinations);
  })
  .catch(() => {
    if (rail) rail.innerHTML = '<p class="country-load-error">国一覧を読み込めませんでした。</p>';
  });

function sortForDisplay(items) {
  return [...items].sort((a, b) => {
    if (a.slug === 'iceland') return -1;
    if (b.slug === 'iceland') return 1;
    return a.nameEn.localeCompare(b.nameEn, 'en');
  });
}

function hueFor(country, index) {
  const code = [...country.nameEn].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return (code * 7 + index * 19) % 360;
}

function createCard(country, index, compact = false) {
  const card = document.createElement(country.atlasPublished && country.href ? 'a' : 'article');
  card.className = `country-card${country.atlasPublished ? ' is-open' : ' is-closed'}${country.journeyLensPublished ? ' is-lens' : ''}`;
  card.dataset.slug = country.slug;
  card.dataset.name = `${country.nameEn} ${country.nameJa}`.toLowerCase();
  if (country.atlasPublished && country.href) {
    card.href = country.href;
    card.setAttribute('aria-label', `${country.nameJa}のJOURNEY ATLASを見る`);
  }

  const art = document.createElement('div');
  art.className = 'country-card__art';
  art.style.setProperty('--hue', String(hueFor(country, index)));
  if (country.image) {
    art.style.backgroundImage = `url("${country.image}")`;
    art.classList.add('has-image');
  }
  art.innerHTML = `<span class="country-card__flag" aria-hidden="true">${country.flag}</span>`;

  const body = document.createElement('div');
  body.className = 'country-card__body';
  body.innerHTML = `<h3>${country.nameEn}</h3><p>${country.nameJa}</p>${!compact && country.journeyLensPublished ? '<small class="country-card__lens">JOURNEY LENS</small>' : ''}${country.atlasPublished ? '<span class="country-card__open" aria-hidden="true">›</span>' : ''}`;
  card.append(art, body);
  return card;
}

function renderRail(items) {
  if (!rail) return;
  const fragment = document.createDocumentFragment();
  items.forEach((country, index) => fragment.append(createCard(country, index)));
  rail.replaceChildren(fragment);
  updateDots();
}

function renderGrid(items) {
  if (!grid) return;
  const fragment = document.createDocumentFragment();
  items.forEach((country, index) => fragment.append(createCard(country, index, true)));
  grid.replaceChildren(fragment);
  if (empty) empty.hidden = items.length !== 0;
}

function scrollRail(direction) {
  if (!rail) return;
  rail.scrollBy({ left: Math.max(460, rail.clientWidth * .82) * direction, behavior: 'smooth' });
}

function updateDots() {
  if (!rail || dots.length === 0) return;
  const max = rail.scrollWidth - rail.clientWidth;
  const ratio = max > 0 ? rail.scrollLeft / max : 0;
  const index = Math.min(dots.length - 1, Math.round(ratio * (dots.length - 1)));
  dots.forEach((dot, i) => dot.classList.toggle('is-active', i === index));
}

function setAllPanel(open, reset = true) {
  if (!allPanel || !toggleAll) return;
  allPanel.hidden = !open;
  toggleAll.setAttribute('aria-expanded', String(open));
  toggleAll.firstChild.textContent = open ? '一覧を閉じる ' : 'すべての国・地域を見る ';
  if (open && reset) {
    if (searchInput) searchInput.value = '';
    renderGrid(destinations);
  }
  if (open) allPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function focusCountry(slug) {
  const country = destinations.find((item) => item.slug === slug);
  if (!country) return;
  setAllPanel(true, false);
  if (searchInput) searchInput.value = country.nameJa;
  renderGrid([country]);
}

document.querySelectorAll('[data-country-focus]').forEach((button) => button.addEventListener('click', () => focusCountry(button.dataset.countryFocus)));

function getWishedSlugs() {
  try {
    return destinations.filter((country) => localStorage.getItem(`journey-atlas:wish:${country.slug}`) === 'true').map((country) => country.slug);
  } catch { return []; }
}

let toastTimer;
function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { toast.hidden = true; }, 2600);
}

prev?.addEventListener('click', () => scrollRail(-1));
next?.addEventListener('click', () => scrollRail(1));
rail?.addEventListener('scroll', () => window.requestAnimationFrame(updateDots), { passive: true });
toggleAll?.addEventListener('click', () => setAllPanel(Boolean(allPanel?.hidden)));
searchInput?.addEventListener('input', () => {
  const query = searchInput.value.trim().toLowerCase();
  renderGrid(query ? destinations.filter((country) => `${country.nameEn} ${country.nameJa}`.toLowerCase().includes(query)) : destinations);
});
wishButton?.addEventListener('click', () => {
  const wished = getWishedSlugs();
  if (wished.length === 0) {
    showToast('行ってみたい国はまだ保存されていません。国ページから追加できます。');
    return;
  }
  setAllPanel(true, false);
  if (searchInput) searchInput.value = '';
  renderGrid(destinations.filter((country) => wished.includes(country.slug)));
  showToast(`${wished.length}件の行ってみたい国を表示しています。`);
});
