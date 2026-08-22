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

let destinations = [];
let allPanelMode = 'all';

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
  body.innerHTML = `
    <h3>${country.nameEn}</h3>
    <p>${country.nameJa}</p>
    ${!compact && country.journeyLensPublished ? '<small class="country-card__lens">JOURNEY LENS</small>' : ''}
    ${country.atlasPublished ? '<span class="country-card__open" aria-hidden="true">›</span>' : ''}`;

  card.append(art, body);
  return card;
}

function renderRail(items) {
  if (!rail) return;
  const fragment = document.createDocumentFragment();
  items.forEach((country, index) => fragment.append(createCard(country, index, false)));
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
  const distance = Math.max(460, rail.clientWidth * 0.82) * direction;
  rail.scrollBy({ left: distance, behavior: 'smooth' });
}

function updateDots() {
  if (!rail || dots.length === 0) return;
  const max = rail.scrollWidth - rail.clientWidth;
  const ratio = max > 0 ? rail.scrollLeft / max : 0;
  const index = Math.min(dots.length - 1, Math.round(ratio * (dots.length - 1)));
  dots.forEach((dot, dotIndex) => dot.classList.toggle('is-active', dotIndex === index));
}

function setAllPanel(open, mode = 'all') {
  if (!allPanel || !toggleAll) return;
  allPanel.hidden = !open;
  toggleAll.setAttribute('aria-expanded', String(open));
  toggleAll.firstChild.textContent = open ? '一覧を閉じる ' : 'すべての国・地域を見る ';
  allPanelMode = mode;
  if (open) {
    if (mode === 'all') {
      if (searchInput) searchInput.value = '';
      renderGrid(destinations);
    }
    allPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function getWishedSlugs() {
  try {
    return destinations
      .filter((country) => localStorage.getItem(`journey-atlas:wish:${country.slug}`) === 'true')
      .map((country) => country.slug);
  } catch {
    return [];
  }
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

toggleAll?.addEventListener('click', () => {
  const isOpen = allPanel && !allPanel.hidden;
  setAllPanel(!isOpen, 'all');
});

searchInput?.addEventListener('input', () => {
  allPanelMode = 'all';
  const query = searchInput.value.trim().toLowerCase();
  if (!query) {
    renderGrid(destinations);
    return;
  }
  renderGrid(destinations.filter((country) => `${country.nameEn} ${country.nameJa}`.toLowerCase().includes(query)));
});

wishButton?.addEventListener('click', () => {
  const wished = getWishedSlugs();
  if (wished.length === 0) {
    showToast('行ってみたい国はまだ保存されていません。国ページの「この国に行きたい」から追加できます。');
    return;
  }
  if (searchInput) searchInput.value = '';
  renderGrid(destinations.filter((country) => wished.includes(country.slug)));
  setAllPanel(true, 'wish');
  showToast(`${wished.length}件の行ってみたい国を表示しています。`);
});
