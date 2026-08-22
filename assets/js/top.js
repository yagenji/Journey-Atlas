const rail = document.querySelector('#country-rail');
const count = document.querySelector('#country-count');
const prev = document.querySelector('[data-country-scroll="prev"]');
const next = document.querySelector('[data-country-scroll="next"]');

fetch('data/atlas-destinations.json')
  .then((response) => {
    if (!response.ok) throw new Error('Destination registry not found');
    return response.json();
  })
  .then(({ destinations = [], count: total }) => {
    if (count) count.textContent = `${total || destinations.length} DESTINATIONS`;
    renderCountries(destinations);
  })
  .catch(() => {
    if (rail) rail.innerHTML = '<p class="country-load-error">国一覧を読み込めませんでした。</p>';
  });

function renderCountries(destinations) {
  if (!rail) return;
  const fragment = document.createDocumentFragment();

  destinations.forEach((country) => {
    const card = document.createElement(country.atlasPublished && country.href ? 'a' : 'article');
    card.className = `country-card${country.atlasPublished ? ' is-open' : ' is-closed'}${country.journeyLensPublished ? ' is-lens' : ''}`;
    if (country.atlasPublished && country.href) card.href = country.href;
    else card.setAttribute('aria-disabled', 'true');

    const art = document.createElement('div');
    art.className = 'country-card__art';
    if (country.image) {
      art.style.backgroundImage = `url("${country.image}")`;
      art.classList.add('has-image');
    }
    art.innerHTML = `<span class="country-card__flag" aria-hidden="true">${country.flag}</span>`;

    const body = document.createElement('div');
    body.className = 'country-card__body';
    body.innerHTML = `
      <div class="country-card__meta">
        <span>${String(country.order).padStart(3, '0')}</span>
        ${country.journeyLensPublished ? '<small>JOURNEY LENS</small>' : ''}
      </div>
      <h3>${country.nameEn}</h3>
      <p>${country.nameJa}</p>
      <span class="country-card__state">${country.atlasPublished ? 'ATLASを見る →' : 'COMING LATER'}</span>`;

    card.append(art, body);
    fragment.append(card);
  });

  rail.replaceChildren(fragment);
}

function scrollRail(direction) {
  if (!rail) return;
  const distance = Math.max(320, rail.clientWidth * 0.82) * direction;
  rail.scrollBy({ left: distance, behavior: 'smooth' });
}

prev?.addEventListener('click', () => scrollRail(-1));
next?.addEventListener('click', () => scrollRail(1));
