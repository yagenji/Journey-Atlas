/* JOURNEY ATLAS — private travel record and scenery favorites.
   Uses existing Country JSON and browser-local preferences; no external account. */
(() => {
  'use strict';
  const SCENE_PREFIX = 'journey-atlas:scene:';
  const VISITED_PREFIX = 'journey-atlas:visited:';
  const WISH_PREFIX = 'journey-atlas:wish:';
  const REGISTRY_PATH = 'data/atlas-destinations.json';
  const ORIGINS_PATH = 'data/scene-origins.json';
  const validId = value => typeof value === 'string' && /^[a-z0-9-]+$/.test(value);
  const allStoredKeys = () => {
    try { return Array.from({length: localStorage.length}, (_, i) => localStorage.key(i)).filter(Boolean); }
    catch { return []; }
  };
  const getStored = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const putStored = (key, value) => {
    try { localStorage.setItem(key, value); return true; } catch { return false; }
  };
  const removeStored = key => { try { localStorage.removeItem(key); return true; } catch { return false; } };
  const make = (tag, className, content) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content !== undefined) element.textContent = content;
    return element;
  };
  const linkTo = (href, label, className) => {
    const a = make('a', className, label);
    a.href = href;
    return a;
  };
  const sceneKey = (slug, id) => SCENE_PREFIX + slug + ':' + id;
  const countryHref = slug => 'countries/' + encodeURIComponent(slug) + '/';
  const sceneHref = (slug, id) => countryHref(slug) + '#'+encodeURIComponent(id);
  const fetchJSON = url => fetch(url).then(response => {
    if (!response.ok) throw Error('HTTP ' + response.status);
    return response.json();
  });
  const getFavorites = () => allStoredKeys().filter(key => key.startsWith(SCENE_PREFIX))
    .map(key => {
      try {
        const item = JSON.parse(getStored(key));
        if (!item || !validId(item.slug) || !validId(item.id) || key !== sceneKey(item.slug, item.id)) return null;
        return item;
      } catch { return null; }
    }).filter(Boolean);
  const updateSceneSaveButton = (button, stored, name) => {
    button.classList.toggle('is-saved', stored);
    button.setAttribute('aria-pressed', String(stored));
    button.textContent = stored ? '♥' : '♡';
    const label = stored ? name + 'をお気に入りから外す' : name + 'をお気に入りに保存する';
    button.setAttribute('aria-label', label);
    button.title = label;
  };
  function mountCountry(country) {
    if (!country || !validId(country.slug) || document.querySelector('[data-ja-scene-save]')) return;
    const status = make('p', 'ja-scene-status');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    document.querySelector('#scene-cards')?.after(status);
    (country.scenes || []).forEach(scene => {
      if (!validId(scene.id)) return;
      const card = Array.from(document.querySelectorAll('.scene-card')).find(e => e.dataset.scene === scene.id);
      if (!card) return;
      const key = sceneKey(country.slug, scene.id);
      const button = make('button', 'ja-scene-save');
      button.type = 'button';
      button.dataset.jaSceneSave = scene.id;
      const saved = () => getStored(key) !== null;
      updateSceneSaveButton(button, saved(), scene.name);
      button.addEventListener('click', event => {
        event.stopPropagation();
        const existing = saved();
        const value = JSON.stringify({
          slug: country.slug, id: scene.id, name: scene.name,
          countryName: country.nameJa, image: scene.image
        });
        const ok = existing ? removeStored(key) : putStored(key, value);
        if (ok) updateSceneSaveButton(button, !existing, scene.name);
        status.textContent = ok ? (existing ? '景色の保存を解除しました。' : 'お気に入りの景色に保存しました。') : 'このブラウザには保存できませんでした。';
      });
      button.addEventListener('keydown', event => event.stopPropagation());
      card.append(button);
    });
    fetchJSON(ORIGINS_PATH).then(data => {
      const entries = data.countries?.[country.slug];
      if (!entries) return;
      (country.scenes || []).forEach(scene => {
        const fact = entries[scene.id];
        if (!fact?.text || !/^https:\/\//.test(fact.source)) return;
        const card = Array.from(document.querySelectorAll('.scene-card')).find(e => e.dataset.scene === scene.id);
        if (!card) return;
        const details = make('details', 'ja-scene-origin');
        const summary = make('summary', '', 'この景色が生まれた理由');
        const paragraph = make('p', '', fact.text);
        const cite = linkTo(fact.source, '出典：' + fact.publisher + '（確認 ' + data.verifiedAt + '）', 'ja-origin-source');
        cite.target = '_blank';
        cite.rel = 'noopener noreferrer';
        // Links in a closed <details> are not keyboard focusable; keep the
        // citation out of the DOM until the explanation is actually expanded.
        details.append(summary, paragraph);
        details.addEventListener('toggle', () => {
          if (details.open) details.append(cite);
          else cite.remove();
        });
        details.addEventListener('click', event => event.stopPropagation());
        details.addEventListener('keydown', event => event.stopPropagation());
        card.querySelector('.scene-copy > div')?.append(details);
      });
    }).catch(() => { /* Only sourced landscape explanations are shown. */ });
  }
  window.addEventListener('journeyatlas:countryready', event => mountCountry(event.detail));
  if (window.journeyAtlasCurrentCountry) mountCountry(window.journeyAtlasCurrentCountry);

  const host = document.querySelector('#atlas-personal-home');
  if (!host) return;
  const disclosure = document.querySelector('#my-atlas');
  const openAtlas = () => { if (disclosure) disclosure.open = true; };
  if (window.location.hash === '#my-atlas') openAtlas();
  document.querySelectorAll('a[href="#my-atlas"]').forEach(link => link.addEventListener('click', openAtlas));
  window.addEventListener('hashchange', () => {
    if (window.location.hash === '#my-atlas') openAtlas();
  });
  const mine = make('section', 'ja-panel ja-mine');
  host.append(mine);
  let registry = [];
  const header = (parent, kicker, title, intro) => {
    const head = make('div', 'ja-panel-head');
    head.append(make('span', 'ja-kicker', kicker), make('h2', '', title), make('p', '', intro));
    parent.append(head);
  };
  header(mine, 'MY ATLAS', 'わたしのアトラス', '行った国・行きたい国・お気に入りの景色を、一つの場所で振り返る。');
  const summary = make('div', 'ja-mine-summary');
  const groups = make('div', 'ja-mine-groups');
  const savedScenes = make('div', 'ja-favorite-scenes');
  const tools = make('div', 'ja-backup-tools');
  const regionCounts = make('div', 'ja-region-counts');
  let regionNames = [];
  const feedback = make('p', 'ja-subtitle');
  feedback.setAttribute('role', 'status');
  mine.append(summary, regionCounts, groups, savedScenes, tools, feedback);
  const visited = country => getStored(VISITED_PREFIX + country.slug) === 'true';
  const wished = country => getStored(WISH_PREFIX + country.slug) === 'true';
  function sectionFor(title, items, empty) {
    const section = make('div', 'ja-mine-group');
    section.append(make('h3', '', title));
    if (items.length) {
      const list = make('div', 'ja-mine-links');
      items.forEach(country => list.append(linkTo(country.href || countryHref(country.slug), country.flag + ' ' + country.nameJa)));
      section.append(list);
    } else section.append(make('p', 'ja-empty', empty));
    return section;
  }
  function renderMine() {
    if (!registry.length) return;
    const all = registry.filter(c => validId(c.slug));
    const seen = all.filter(visited), want = all.filter(wished);
    const favorites = getFavorites().filter(f => all.some(c => c.slug === f.slug));
    summary.replaceChildren();
    [['VISITED', seen.length, '行った国・地域'], ['WISHLIST', want.length, '行きたい国・地域'], ['SCENERY', favorites.length, '保存した景色']].forEach(([tag, count, name]) => {
      const item = make('div', 'ja-summary-item');
      item.append(make('span', '', tag), make('strong', '', count + (tag === 'SCENERY' ? ' 景色' : ' / ' + all.length)), make('small', '', name));
      summary.append(item);
    });
    regionCounts.replaceChildren();
    regionNames.forEach(region => {
      const count = seen.filter(country => region.iso2.includes(country.iso2)).length;
      if (count) regionCounts.append(make('span', '', region.label + ' ' + count + ' / ' + region.iso2.length));
    });
    groups.replaceChildren(sectionFor('行った国・地域', seen, '地図の「わたしの地図」から登録できます。'), sectionFor('行きたい国・地域', want, '国ページの「この国に行きたい」で登録できます。'));
    savedScenes.replaceChildren(make('h3', '', 'お気に入りの景色'));
    const gallery = make('div', 'ja-scene-gallery');
    favorites.forEach(favorite => {
      const item = make('div', 'ja-favorite-card');
      const link = linkTo(sceneHref(favorite.slug, favorite.id), '', 'ja-favorite-link');
      const img = make('img');
      if (typeof favorite.image === 'string' && /^assets\/images\/[a-z0-9/-]+\.(webp|jpg|png)(\?v=[a-zA-Z0-9._-]+)?$/.test(favorite.image)) {
        img.loading = 'lazy';
        img.decoding = 'async';
        img.src = favorite.image;
        img.alt = '';
        link.append(img);
      }
      const names = make('span');
      names.append(make('strong', '', favorite.name), make('small', '', favorite.countryName));
      link.append(names);
      const remove = make('button', 'ja-remove', '保存を解除');
      remove.type = 'button';
      remove.setAttribute('aria-label', favorite.name + 'の保存を解除');
      remove.addEventListener('click', () => { removeStored(sceneKey(favorite.slug, favorite.id)); renderMine(); });
      item.append(link, remove);
      gallery.append(item);
    });
    if (!favorites.length) gallery.append(make('p', 'ja-empty', '国ページの景色のハートを押すと、ここに並びます。'));
    savedScenes.append(gallery);
  }
  const exportButton = make('button', 'ja-tool-button', '保存データを書き出す');
  exportButton.type = 'button';
  exportButton.addEventListener('click', () => {
    const countries = registry.filter(c => validId(c.slug));
    const payload = {
      version: 1,
      visited: countries.filter(visited).map(c => c.slug),
      wished: countries.filter(wished).map(c => c.slug),
      favorites: getFavorites()
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], {type: 'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'journey-atlas-my-atlas.json';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    feedback.textContent = 'このブラウザの保存データを書き出しました。';
  });
  const importLabel = make('label', 'ja-tool-button ja-import-label', '保存データを読み込む');
  const fileInput = make('input');
  fileInput.type = 'file';
  fileInput.accept = '.json,application/json';
  fileInput.setAttribute('aria-label', '保存データのJSONファイル');
  importLabel.append(fileInput);
  fileInput.addEventListener('change', async () => {
    const file = fileInput.files?.[0];
    fileInput.value = '';
    if (!file) return;
    if (file.size > 1024 * 1024) { feedback.textContent = 'ファイルサイズが大きすぎます。'; return; }
    try {
      const payload = JSON.parse(await file.text());
      if (payload.version !== 1 || !Array.isArray(payload.visited) || !Array.isArray(payload.wished) || !Array.isArray(payload.favorites)) throw Error('Invalid backup');
      const allowed = new Set(registry.map(c => c.slug));
      payload.visited.filter(slug => allowed.has(slug)).forEach(slug => { if (!putStored(VISITED_PREFIX + slug, 'true')) throw Error('Storage unavailable'); });
      payload.wished.filter(slug => allowed.has(slug)).forEach(slug => { if (!putStored(WISH_PREFIX + slug, 'true')) throw Error('Storage unavailable'); });
      payload.favorites.filter(f => f && allowed.has(f.slug) && validId(f.id) && typeof f.name === 'string' && typeof f.countryName === 'string' && typeof f.image === 'string').slice(0, 3000).forEach(f => {
        if (!putStored(sceneKey(f.slug, f.id), JSON.stringify({slug: f.slug, id: f.id, name: f.name.slice(0, 150), countryName: f.countryName.slice(0, 100), image: f.image.slice(0, 240)}))) throw Error('Storage unavailable');
      });
      feedback.textContent = '保存データを読み込みました。既存の記録には追加されます。';
      renderMine();
    } catch { feedback.textContent = '保存データを読み込めませんでした。書き出したJSONファイルを選んでください。'; }
  });
  tools.append(exportButton, importLabel, make('p', 'ja-storage-note', 'アカウント不要。記録はこのブラウザに保存されます。端末を変える際はファイルで引き継げます。'));
  fetchJSON(REGISTRY_PATH).then(data => {
    registry = Array.isArray(data.destinations) ? data.destinations : [];
    renderMine();
    fetchJSON('data/region-taxonomy.json').then(data => {
      regionNames = (data.regions || []).filter(region => Array.isArray(region.iso2));
      renderMine();
    }).catch(() => {});
  }).catch(() => {
    feedback.textContent = 'アトラスの一覧を読み込めませんでした。';
  });
  window.addEventListener('storage', () => {
    renderMine();
  });
})();
