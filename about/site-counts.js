/* JOURNEY ATLAS — counts for informational pages.
 * Basic Country Pages are the fixed editorial 200; published detail Regions
 * plus the existing Hong Kong/Macau pages expand the overall destination set.
 * Use generated publication indexes rather than hand-maintained Region totals. */
(() => {
  'use strict';
  const targets = document.querySelectorAll('[data-atlas-count]');
  const list = document.querySelector('[data-atlas-detail-regions]');
  if (!targets.length && !list) return;

  const children = new Set(['hong-kong', 'macau']);
  const getJson = url => fetch(url).then(response => {
    if (!response.ok) throw Error('Publication index unavailable');
    return response.json();
  });
  Promise.all([
    getJson('data/atlas-destinations.json'),
    getJson('data/top-scene-index.json')
  ]).then(([catalog, sceneIndex]) => {
    if (!Array.isArray(catalog.destinations) || !Array.isArray(sceneIndex.regionHeroes)) return;
    const base = catalog.destinations.filter(item => !children.has(item.slug) && item.atlasPublished);
    const legacy = catalog.destinations.filter(item => children.has(item.slug) && item.atlasPublished);
    const published = sceneIndex.regionHeroes.filter(item => item.slug && item.parentSlug && item.href);
    const counts = {
      base: base.length, legacy: legacy.length, published: published.length,
      regions: legacy.length + published.length,
      total: base.length + legacy.length + published.length
    };
    targets.forEach(node => {
      const value = counts[node.dataset.atlasCount];
      if (Number.isInteger(value)) node.textContent = String(value);
    });
    if (!list) return;

    // Existing HTML stays as a readable fallback until the published indexes load.
    // Its parent order is preserved; new parent groups are appended automatically.
    const originalOrder = [...list.querySelectorAll('li a[href^="countries/"]')]
      .map(a => a.getAttribute('href').split('/')[1]);
    const parents = new Map(base.map(item => [item.slug, item]));
    const grouped = new Map();
    const add = (parent, child) => {
      if (!parent || !parents.has(parent) || !child.nameJa) return;
      if (!grouped.has(parent)) grouped.set(parent, []);
      grouped.get(parent).push(child.nameJa);
    };
    legacy.forEach(item => add('china', item));
    published.forEach(item => add(item.parentSlug, item));
    const order = [...grouped.keys()].sort((a,b) => {
      const aOrder = originalOrder.indexOf(a), bOrder = originalOrder.indexOf(b);
      if (aOrder !== -1 || bOrder !== -1)
        return (aOrder === -1 ? 999 : aOrder) - (bOrder === -1 ? 999 : bOrder);
      return parents.get(a).nameJa.localeCompare(parents.get(b).nameJa, 'ja');
    });
    list.replaceChildren(...order.map(slug => {
      const parent = parents.get(slug), names = grouped.get(slug);
      const li = document.createElement('li'), link = document.createElement('a');
      link.href = parent.href || 'countries/' + slug + '/';
      link.textContent = parent.nameJa + '（' + names.length + '）';
      li.append(link, '：' + names.join('、') + '。');
      return li;
    }));
  }).catch(() => { /* Keep the server-rendered fallback rather than a false zero. */ });
})();
