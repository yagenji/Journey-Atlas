/* Region page interactions: reuse the established Country scene and favorite semantics.
 * Region pages do not increase the canonical 200 Country Page count. */
(() => {
  'use strict';
  const match = window.location.pathname.match(/\/countries\/([a-z0-9-]+)\/([a-z0-9-]+)\/?/);
  if (!match) return;
  const [, parentSlug, slug] = match;
  const cards = Array.from(document.querySelectorAll('.region-scene[data-scene]'));
  const mapHits = Array.from(document.querySelectorAll('.region-map-hit[data-scene]'));
  if (cards.length !== 8 || new Set(mapHits.map(hit => hit.dataset.scene)).size !== cards.length) return;
  const cardById = new Map(cards.map(card => [card.dataset.scene, card]));
  const mapById = new Map(mapHits.map(hit => [hit.dataset.scene, hit]));
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let selectedId = '';

  // Show only one geographic map at a time; keep the overview at its real scale.
  const switchButtons = Array.from(document.querySelectorAll('.region-map-switcher__button'));
  if (switchButtons.length) {
    const mapArt = document.querySelector('#country-map-art');
    const mapImage = mapArt?.querySelector('.map-base');
    const mapColumn = mapArt?.closest('.map-column');
    const captions = Array.from(document.querySelectorAll('[data-region-map-caption]'));
    const overviewSrc = mapImage?.getAttribute('src') || '';
    const overviewAlt = mapImage?.getAttribute('alt') || '';
    const setMapView = button => {
      if (!mapImage || !mapArt || !mapColumn) return;
      const isOverview = button.dataset.regionMapView === 'overview';
      const nextSrc = isOverview ? overviewSrc : button.dataset.regionMapSrc;
      if (!nextSrc) return;
      mapImage.setAttribute('src', nextSrc);
      mapImage.setAttribute('alt', isOverview ? overviewAlt : button.dataset.regionMapLabel + 'の拡大地図（別縮尺）');
      mapArt.classList.toggle('is-region-detail', !isOverview);
      mapColumn.classList.toggle('is-region-detail', !isOverview);
      switchButtons.forEach(control => {
        const active = control === button;
        control.classList.toggle('is-active', active);
        control.setAttribute('aria-pressed', String(active));
      });
      captions.forEach(caption => {
        caption.hidden = caption.dataset.regionMapCaption !== button.dataset.regionMapView;
      });
    };
    switchButtons.forEach(button => button.addEventListener('click', () => setMapView(button)));
  }


  const select = (id, scrollToCard = false) => {
    if (!cardById.has(id) || !mapById.has(id)) return;
    selectedId = id;
    for (const [sceneId, card] of cardById) {
      const selected = sceneId === id;
      card.classList.toggle('is-active', selected);
      card.setAttribute('aria-pressed', String(selected));
    }
    for (const hit of mapHits) {
      const selected = hit.dataset.scene === id;
      hit.classList.toggle('is-active', selected);
      hit.setAttribute('aria-pressed', String(selected));
    }
    if (scrollToCard) {
      cardById.get(id).scrollIntoView({block: 'center', behavior: reducedMotion.matches ? 'instant' : 'smooth'});
    }
  };

  const preview = (id, active) => {
    cardById.get(id)?.classList.toggle('is-preview', active);
    mapById.get(id)?.classList.toggle('is-preview', active);
  };
  cards.forEach(card => {
    const id = card.dataset.scene;
    card.addEventListener('click', event => {
      if (event.target.closest('button,a,summary,details')) return;
      select(id);
    });
    card.addEventListener('keydown', event => {
      if (event.target !== card || !['Enter', ' '].includes(event.key)) return;
      event.preventDefault();
      select(id);
    });
    card.addEventListener('mouseenter', () => preview(id, true));
    card.addEventListener('mouseleave', () => preview(id, false));
    card.addEventListener('focus', () => preview(id, true));
    card.addEventListener('blur', () => preview(id, false));
  });
  mapHits.forEach(hit => {
    const id = hit.dataset.scene;
    hit.addEventListener('click', () => select(id, true));
    hit.addEventListener('mouseenter', () => preview(id, true));
    hit.addEventListener('mouseleave', () => preview(id, false));
    hit.addEventListener('focus', () => preview(id, true));
    hit.addEventListener('blur', () => preview(id, false));
  });
  const hash = decodeURIComponent(window.location.hash.slice(1));
  const requested = hash.startsWith('scene-') ? hash.slice(6) : '';
  select(cardById.has(requested) ? requested : cards[0].dataset.scene);
  window.addEventListener('hashchange', () => {
    const current = decodeURIComponent(window.location.hash.slice(1));
    if (current.startsWith('scene-') && cardById.has(current.slice(6))) select(current.slice(6), true);
  });

  const assetPath = img => img?.getAttribute('src')?.split('?', 1)[0] || '';
  const hero = document.querySelector('.hero-caption');
  const country = {
    slug,
    regionParent: parentSlug,
    nameJa: document.querySelector('.country-ja')?.textContent?.trim() || slug,
    hero: {
      name: hero?.querySelector('.hero-caption__name')?.textContent?.trim() || '',
      image: assetPath(document.querySelector('.hero-art img')),
      location: hero?.querySelector('.hero-caption__local')?.textContent?.trim() || ''
    },
    scenes: cards.map(card => ({
      id: card.dataset.scene,
      name: card.querySelector('.scene-copy h3')?.textContent?.trim() || '',
      image: assetPath(card.querySelector('.scene-image img')),
      sceneTypes: (card.dataset.sceneTypes || '').split(',').filter(Boolean)
    }))
  };
  // atlas-personal.js provides the same Hero/Scene hearts as the Country pages.
  window.journeyAtlasCurrentCountry = country;
  window.dispatchEvent(new CustomEvent('journeyatlas:countryready', {detail: country}));

  // Visits are independent of wishes and never increment the 200-Country total.
  const visitedButton = document.querySelector('#region-visited-button');
  const visitedKey = `journey-atlas:region-visited:${parentSlug}:${slug}`;
  const readVisited = () => {
    try { return localStorage.getItem(visitedKey) !== null; }
    catch { return false; }
  };
  const paintVisited = () => {
    if (!visitedButton) return;
    const done = readVisited();
    visitedButton.classList.toggle('is-saved', done);
    visitedButton.setAttribute('aria-pressed', String(done));
    visitedButton.querySelector('.wish-icon').textContent = done ? '✓' : '○';
    visitedButton.querySelector('strong').textContent = done ? 'この地域に行きました' : 'この地域に行った';
  };
  paintVisited();
  visitedButton?.addEventListener('click', () => {
    try {
      if (readVisited()) localStorage.removeItem(visitedKey);
      else localStorage.setItem(visitedKey, JSON.stringify({
        parentSlug, slug, nameJa: country.nameJa,
        href: `countries/${parentSlug}/${slug}/`
      }));
      paintVisited();
      const message = document.querySelector('#region-wish-status');
      if (message) message.textContent = readVisited()
        ? '訪問の記録を保存しました。' : '訪問の記録を解除しました。';
    } catch {
      const message = document.querySelector('#region-wish-status');
      if (message) message.textContent = 'このブラウザには保存できませんでした。';
    }
  });
  window.addEventListener('pageshow', paintVisited);
  window.addEventListener('focus', paintVisited);
  window.addEventListener('storage', event => {
    if (event.key === visitedKey || event.key === null) paintVisited();
  });

  const button = document.querySelector('#region-wish-button');
  const status = document.querySelector('#region-wish-status');
  if (!button) return;
  const key = `journey-atlas:region-wish:${parentSlug}:${slug}`;
  const read = () => {try {return localStorage.getItem(key) !== null;} catch {return false;}};
  let wished = read();
  const draw = () => {
    button.classList.toggle('is-saved', wished);
    button.setAttribute('aria-pressed', String(wished));
    button.querySelector('.wish-icon').textContent = wished ? '♥' : '♡';
    button.querySelector('strong').textContent = wished ? '行きたい地域に保存しました' : 'この地域に行きたい';
  };
  draw();
  button.addEventListener('click', () => {
    try {
      if (wished) localStorage.removeItem(key);
      else localStorage.setItem(key, JSON.stringify({parentSlug, slug, nameJa: country.nameJa, href: `countries/${parentSlug}/${slug}/`}));
      wished = !wished;
      status.textContent = wished ? '行きたい地域に保存しました。' : '行きたい地域から外しました。';
      draw();
    } catch {status.textContent = 'このブラウザには保存できませんでした。';}
  });
})();