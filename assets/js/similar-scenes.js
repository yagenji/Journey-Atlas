/* JOURNEY ATLAS — この景色が好きなら: three scenes from other countries that share
   this page's scene types (data/scene-taxonomy.json). Built entirely from the shared
   scene index, so any newly typed Scene joins the pool without per-page setup. */
(() => {
  'use strict';
  const INDEX = 'data/top-scene-index.json?v=20261109-scene-view-1';
  const PICKS = 6;
  // Detail areas count as part of their parent for "another country".
  const FAMILY = {'hong-kong': 'china', macau: 'china'};
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
  const shuffle = list => {
    const copy = [...list];
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  };

  function ownTypes(data, index) {
    let lists = [data.hero, ...(data.scenes || [])].filter(Boolean).map(entry => entry.sceneTypes || []);
    if (!lists.some(list => list.length) && data.regionParent) {
      // Region pages are static; their types travel in the shared index.
      lists = (index.regionHeroes || []).find(region => region.slug === data.slug)?.pageTypes || [];
    }
    lists = lists.filter(list => list.length);
    const order = [];
    // Main subjects first, in page order; second types only fill gaps.
    [0, 1].forEach(position => lists.forEach(list => {
      const type = list[position];
      if (type && !order.includes(type)) order.push(type);
    }));
    return order;
  }

  function buildPool(index, registry, regionByIso) {
    const destinations = new Map(registry.filter(item => item.atlasPublished && item.href).map(item => [item.slug, item]));
    const pool = [];
    Object.entries(index.countries || {}).forEach(([slug, rows]) => {
      const place = destinations.get(slug);
      if (!place) return;
      rows.forEach(([id, name, types = []]) => types.length && pool.push({
        slug, family: FAMILY[slug] || slug, name, types, place,
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
        region: regionByIso.get(place.iso2), image: place.image, href: `${place.href}#hero-caption`
      });
    });
    (index.regionHeroes || []).forEach(region => region.sceneTypes?.length && pool.push({
      slug: region.slug, family: region.parentSlug, name: region.heroName, types: region.sceneTypes,
      place: region, region: region.regionId, image: region.image, href: `${region.href}#hero-caption`
    }));
    return pool;
  }

  function choose(order, pool, family, homeRegion) {
    const picks = [];
    const families = new Set([family]);
    const regions = [homeRegion];
    // Go round the page's types until six are found, so a page with few types still fills the row.
    let added = true;
    while (picks.length < PICKS && added) {
      added = false;
      for (const type of order) {
        if (picks.length === PICKS) break;
        const open = pool.filter(item => item.types.includes(type) && !families.has(item.family));
        if (!open.length) continue;
        // Prefer the same main subject, then a part of the world not yet shown.
        const score = item => (item.types[0] === type ? 2 : 0) + (regions.includes(item.region) ? 0 : 1);
        const best = Math.max(...open.map(score));
        const pick = shuffle(open.filter(item => score(item) === best))[0];
        picks.push({...pick, reason: type});
        families.add(pick.family);
        regions.push(pick.region);
        added = true;
      }
    }
    return picks;
  }

  function render(picks) {
    // A small extra after the page has closed: below the closing links, not before them.
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
      make('p', 'similar-scenes__intro', `${document.querySelector('.region-country-page') ? 'この地域' : 'この国'}の景色と同じ種類の景色を、ほかの国から。`));
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
    // On phones the row scrolls sideways, so lazy loading would leave the hidden photos blank; load all six once the row is near.
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
      const order = ownTypes(data, index);
      if (!order.length) return;
      const regionByIso = new Map();
      (taxonomy.regions || []).forEach(region => (region.iso2 || []).forEach(iso => regionByIso.set(iso, region.id)));
      const places = registry.destinations || [];
      const self = places.find(item => item.slug === data.slug) || places.find(item => item.slug === data.regionParent);
      const family = data.regionParent || FAMILY[data.slug] || data.slug;
      const picks = choose(order, buildPool(index, places, regionByIso), family, regionByIso.get(self?.iso2));
      if (!picks.length) return;
      render(picks);
    } catch (error) {
      console.warn('[JOURNEY ATLAS] Similar scenes unavailable.', error);
    }
  }
  if (window.journeyAtlasCurrentCountry) mount(window.journeyAtlasCurrentCountry);
  else window.addEventListener('journeyatlas:countryready', event => mount(event.detail), {once: true});
})();
