// 初めて行った年: once a Country page is marked 「ここに行った」, an optional year can be recorded
// under the buttons. Stored only in this browser (journey-atlas:visited-year:{slug}) and shown
// as 旅の年表 in マイアトラス.
(() => {
  'use strict';
  // 旅の年表 covers the 200 Country pages only: no year on detail regions.
  const regionPath = location.pathname.match(/\/countries\/([a-z0-9-]+)\/([a-z0-9-]+)\/?$/);
  if (regionPath || ['hong-kong', 'macau'].includes(document.documentElement.dataset.country)) return;
  const selector = regionPath ? '#region-visited-button' : '#visited-button';
  // Country pages render their body after the data loads; Region pages are static.
  if (document.querySelector(selector)) init();
  else window.addEventListener('journeyatlas:countryready', () => requestAnimationFrame(init), { once: true });

  function init() {
  const button = document.querySelector(selector);
  const slug = regionPath ? regionPath[2] : document.documentElement.dataset.country;
  if (!button || !slug || !/^[a-z0-9-]+$/.test(slug) || document.querySelector('.visit-year')) return;
  const key = 'journey-atlas:visited-year:' + (regionPath ? regionPath[1] + ':' + slug : slug);
  const get = () => { try { return localStorage.getItem(key) || ''; } catch { return ''; } };
  const set = (value) => {
    try { if (value) localStorage.setItem(key, value); else localStorage.removeItem(key); return true; } catch { return false; }
  };

  const label = document.createElement('label');
  label.className = 'visit-year';
  label.append(document.createTextNode('初めて行った年'));
  const select = document.createElement('select');
  select.className = 'visit-year__select';
  const thisYear = new Date().getFullYear();
  const blank = new Option('記録しない', '');
  select.append(blank);
  for (let year = thisYear; year >= 1950; year -= 1) select.append(new Option(year + '年', String(year)));
  label.append(select);
  const status = document.querySelector(regionPath ? '#region-wish-status' : '#wish-status');
  (button.closest('.wish-wrap') || button).after(label);

  select.addEventListener('change', () => {
    const ok = set(select.value);
    if (status) status.textContent = !ok ? 'このブラウザには保存できませんでした。'
      : select.value ? `初めて行った年（${select.value}年）を記録しました。` : '初めて行った年の記録を外しました。';
  });
  const paint = () => {
    const visited = button.getAttribute('aria-pressed') === 'true';
    if (!visited && get()) set('');
    label.hidden = !visited;
    select.value = visited ? get() : '';
  };
  new MutationObserver(paint).observe(button, { attributes: true, attributeFilter: ['aria-pressed'] });
  window.addEventListener('storage', (event) => { if (event.key === key || event.key === null) paint(); });
  paint();
  }
})();
