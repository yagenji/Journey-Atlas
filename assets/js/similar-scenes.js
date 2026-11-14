/* JOURNEY ATLAS — 「この景色が好きなら」.
   Rank real, published scenery by subject and geographic context. Never fill a
   fixed number of cards with unrelated types merely for variety. */
(() => {
  'use strict';
  const INDEX = 'data/top-scene-index.json?v=20261114-scenery-affinity-2';
  const PICKS = 6;
  const MIN_SCORE = 4.25;
  // Detail areas count as part of their parent for "another country".
  const FAMILY = {'hong-kong': 'china', macau: 'china'};
  // Geography is a useful guardrail for climate-dependent natural scenery.
  // It is NOT a substitute for the taxonomy: ice on tropical mountains is real.
  const LAT_SENSITIVE = new Set([
    'fjord', 'island', 'bay', 'harbor', 'beach', 'lagoon', 'reef', 'cliff',
    'forest', 'rainforest', 'grassland', 'wetland', 'dune', 'oasis',
    'rock', 'cave', 'lake', 'river', 'birds', 'wildlife', 'marine'
  ]);
  // Broad labels alone are weaker evidence of visual resemblance.
  const BROAD = new Set([
    'island', 'bay', 'harbor', 'rock', 'cliff', 'birds', 'beach',
    'lake', 'river', 'village', 'road', 'peak'
  ]);
  const json = url => fetch(url).then(response => {
    if (!response.ok) throw Error('HTTP ' + response.status);
    return response.json();
  });
  const make = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const latitude = value => typeof value === 'number' && Number.isFinite(value) && Math.abs(value) <= 90
    ? value : null;

  function ownScenes(data, index) {
    let entries = [data.hero, ...(data.scenes || [])].filter(Boolean).map(entry => ({
      types: Array.isArray(entry.sceneTypes) ? entry.sceneTypes : [],
      latitude: latitude(entry.coordinates?.latitude)
    }));
    if (!entries.some(entry => entry.types.length) && data.regionParent) {
      // Compatibility with older published Region markup.
      const region = (index.regionHeroes || []).find(item => item.slug === data.slug);
      entries = (region?.pageTypes || []).map((types, i) => ({
        types, latitude: latitude(region?.pageLatitudes?.[i])
      }));
    }
    return entries;
  }

  function buildPool(index, registry, regionByIso) {
    const destinations = new Map(registry.filter(item => item.atlasPublished && item.href).map(item => [item.slug, item]));
    const pool = [];
    Object.entries(index.countries || {}).forEach(([slug, rows]) => {
      const place = destinations.get(slug);
      if (!place) return;
      rows.forEach(([id, name, types = [], , sceneLatitude]) => types.length && pool.push({
        slug, family: FAMILY[slug] || slug, name, types, place,
        latitude: latitude(sceneLatitude),
        region: regionByIso.get(place.iso2),
        image: `assets/images/top/scenes/${slug}/${id}.webp`,
        href: `${place.href}#${encodeURIComponent(id)}`
      }));
    });
    Object.entries(index.heroTypes || {}).forEach(([slug, types]) => {
      const place = destinations.get(slug);
      if (!place?.image || !index.heroes?.[slug]) return;
      pool.push({
        slug, family: FAMILY[slug] || slug, name: index.heroes[slug], types, place,
        latitude: latitude(index.heroLatitudes?.[slug]),
        region: regionByIso.get(place.iso2), image: place.image, href: `${place.href}#hero-caption`
      });
    });
    (index.regionHeroes || []).forEach(region => region.sceneTypes?.length && pool.push({
      slug: region.slug, family: region.parentSlug, name: region.heroName, types: region.sceneTypes,
      place: region, region: region.regionId, latitude: latitude(region.latitude),
      image: region.image, href: `${region.href}#hero-caption`
    }));
    return pool;
  }

  function affinity(anchor, candidate) {
    let best = 0;
    let matching = 0;
    for (let i = 0; i < anchor.types.length; i++) {
      const type = anchor.types[i];
      for (let j = 0; j < candidate.types.length; j++) {
        if (type !== candidate.types[j]) continue;
        let geographicBonus = 0;
        if (LAT_SENSITIVE.has(type)) {
          if (anchor.latitude !== null && candidate.latitude !== null) {
            // Compare distance from the equator, not hemisphere. Similar polar
            // landscapes exist at opposite ends of the planet.
            const delta = Math.abs(Math.abs(anchor.latitude) - Math.abs(candidate.latitude));
            if (delta > 30) continue;
            geographicBonus = 1.2 * (1 - delta / 30);
          } else {
            geographicBonus = -0.6; // Unknown context must not look like a strong match.
          }
        }
        let match = i === 0 ? (j === 0 ? 6 : 4.5) : (j === 0 ? 3.5 : 2.5);
        if (BROAD.has(type) && anchor.types.length === 1 && candidate.types.length === 1) {
          match -= 1.1;
        }
        best = Math.max(best, match + geographicBonus);
        matching++;
      }
    }
    return best + (matching > 1 ? 1.4 : 0);
  }

  function choose(anchors, pool, family) {
    const scored = [];
    for (const candidate of pool) {
      if (candidate.family === family) continue;
      let best = 0;
      for (let i = 0; i < anchors.length; i++) {
        if (!anchors[i].types.length) continue;
        // The Hero is the primary visual promise. The eight Scenes are
        // supporting evidence, not eight unrelated quotas to satisfy.
        const weight = i === 0 ? 1 : 0.72;
        best = Math.max(best, affinity(anchors[i], candidate) * weight);
      }
      if (best >= MIN_SCORE) scored.push({...candidate, score: best});
    }
    // Stable ordering, strongest resemblance first. Country and continent
    // diversity never override the match, and weak matches are left out.
    scored.sort((a, b) => b.score - a.score ||
      a.family.localeCompare(b.family) || a.name.localeCompare(b.name));
    const seen = new Set([family]);
    return scored.filter(item => {
      if (seen.has(item.family)) return false;
      seen.add(item.family);
      return true;
    }).slice(0, PICKS);
  }

  function render(picks) {
    const closing = document.querySelector('.journey-footer');
    const grid = document.querySelector('#scene-cards, .scene-grid');
    const anchor = closing || grid?.closest('section');
    if (!anchor || document.querySelector('.similar-scenes')) return;
    const section = make('section', 'similar-scenes');
    section.setAttribute('aria-labelledby', 'similar-scenes-title');
    const head = make('div', 'similar-scenes__head');
    const titleWrap = make('div');
    const title = make('h2', '', 'この景色が好きなら');
    title.id = 'similar-scenes-title';
    titleWrap.append(make('span', 'section-kicker-en', 'IF YOU LIKE THIS SCENERY'), title,
      make('p', 'similar-scenes__intro', `${document.querySelector('.region-country-page') ? 'この地域' : 'この国'}の景色と、主題や自然環境が近い景色を、ほかの国から。`));
    const list = make('div', 'similar-scenes__grid');
    list.setAttribute('role', 'list');
    picks.forEach(pick => {
      const card = make('a', 'similar-scene');
      card.href = pick.href;
      card.setAttribute('role', 'listitem');
      card.setAttribute('aria-label', `${pick.name}（${pick.place.nameJa}）のページを見る`);
      const image = make('img');
      image.src = pick.image;
      image.alt = '';
      image.width = 240;
      image.height = 160;
      image.loading = 'lazy';
      image.decoding = 'async';
      const copy = make('span', 'similar-scene__copy');
      const country = make('small', 'similar-scene__country');
      if (pick.place.flagAsset) {
        const flag = make('img', 'similar-scene__flag');
        flag.src = pick.place.flagAsset;
        flag.alt = '';
        flag.width = 16;
        flag.height = 16;
        country.append(flag, ' ' + pick.place.nameJa);
      } else {
        country.textContent = `${pick.place.flag || ''} ${pick.place.nameJa}`.trim();
      }
      copy.append(make('b', '', pick.name), country);
      card.append(image, copy);
      list.append(card);
    });
    const more = make('a', 'similar-scenes__more', '景色の種類から探す →');
    more.href = './#scenery';
    head.append(titleWrap, more);
    section.append(head, list);
    anchor.after(section);
    if ('IntersectionObserver' in window) {
      const watch = new IntersectionObserver(entries => {
        if (!entries.some(entry => entry.isIntersecting)) return;
        list.querySelectorAll('img[loading="lazy"]').forEach(img => { img.loading = 'eager'; });
        watch.disconnect();
      }, {rootMargin: '400px 0px'});
      watch.observe(list);
    }
  }

  async function mount(data) {
    if (!data?.slug) return;
    try {
      const [index, registry, taxonomy] = await Promise.all([
        json(INDEX), json('data/atlas-destinations.json'), json('data/region-taxonomy.json')
      ]);
      const anchors = ownScenes(data, index);
      if (!anchors.some(entry => entry.types.length)) return;
      const regionByIso = new Map();
      (taxonomy.regions || []).forEach(region => (region.iso2 || []).forEach(iso => regionByIso.set(iso, region.id)));
      const places = registry.destinations || [];
      const family = data.regionParent || FAMILY[data.slug] || data.slug;
      const picks = choose(anchors, buildPool(index, places, regionByIso), family);
      if (!picks.length) return;
      render(picks);
    } catch (error) {
      console.warn('[JOURNEY ATLAS] Similar scenes unavailable.', error);
    }
  }
  if (window.journeyAtlasCurrentCountry) mount(window.journeyAtlasCurrentCountry);
  else window.addEventListener('journeyatlas:countryready', event => mount(event.detail), {once: true});
})();
