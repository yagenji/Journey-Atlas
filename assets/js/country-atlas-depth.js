(() => {
  const slug = new URLSearchParams(window.location.search).get('country') || 'iceland';
  const safeSlug = /^[a-z0-9-]+$/.test(slug) ? slug : 'iceland';

  function escapeHtml(value = '') {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function insertSection(data) {
    const items = Array.isArray(data.atlasExtras) ? data.atlasExtras : [];
    if (!items.length) return;
    const atlasPanel = document.querySelector('.atlas-panel');
    if (!atlasPanel || document.querySelector('.atlas-extras')) return;

    const section = document.createElement('section');
    section.className = 'atlas-extras';
    section.setAttribute('aria-labelledby', 'atlas-extras-title');
    section.innerHTML = `
      <div class="atlas-extras__head">
        <div>
          <p class="atlas-extras__kicker">BEYOND THE SCENERY</p>
          <h2 id="atlas-extras-title">景色の先で出会うもの</h2>
        </div>
        <p class="atlas-extras__intro">8つのテーマのうち、景色8選で強く扱う「地球の風景」「海の世界へ」を除く6テーマから、街・歴史・暮らし・野生・食・道をたどる。</p>
      </div>
      <div class="atlas-extras__grid"></div>`;

    const grid = section.querySelector('.atlas-extras__grid');
    items.forEach((item) => {
      const points = Array.isArray(item.points) ? item.points.filter(Boolean) : [];
      const article = document.createElement('article');
      article.className = 'atlas-extra';
      article.innerHTML = `
        <span class="atlas-extra__theme">${escapeHtml(item.themeEn)} / ${escapeHtml(item.themeJa)}</span>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.text)}</p>
        ${points.length ? `<ul>${points.map((point) => `<li>${escapeHtml(point)}</li>`).join('')}</ul>` : ''}`;
      grid.append(article);
    });

    atlasPanel.insertAdjacentElement('afterend', section);
  }

  function waitForAtlas(data) {
    if (document.querySelector('.atlas-panel')) {
      insertSection(data);
      return;
    }
    const app = document.querySelector('#app');
    if (!app) return;
    const observer = new MutationObserver(() => {
      if (!document.querySelector('.atlas-panel')) return;
      observer.disconnect();
      insertSection(data);
    });
    observer.observe(app, { childList: true, subtree: true });
  }

  fetch(`data/countries/${safeSlug}.json?v=20260824-1220`)
    .then((response) => {
      if (!response.ok) throw new Error('Country data not found');
      return response.json();
    })
    .then(waitForAtlas)
    .catch(() => {});
})();
