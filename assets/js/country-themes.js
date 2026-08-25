(() => {
  const params = new URLSearchParams(window.location.search);
  const slug = params.get('country') || document.documentElement.dataset.country || '';
  if (!slug) return;

  const render = (themes) => {
    const section = document.querySelector('#country-theme-context');
    const list = document.querySelector('#country-theme-list');
    if (!section || !list) return false;

    const matches = themes.filter((theme) => Array.isArray(theme.examples) && theme.examples.includes(slug));
    if (!matches.length) {
      section.hidden = true;
      return true;
    }

    list.replaceChildren(...matches.map((theme) => {
      const span = document.createElement('span');
      span.className = 'country-theme-chip';
      span.textContent = theme.label;
      if (theme.definition) span.title = theme.definition;
      return span;
    }));
    section.hidden = false;
    return true;
  };

  fetch('data/theme-taxonomy.json?v=20260825-1148', { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error('Theme taxonomy not found');
      return response.json();
    })
    .then(({ themes = [] }) => {
      if (render(themes)) return;
      const host = document.querySelector('#app');
      if (!host) return;
      const observer = new MutationObserver(() => {
        if (render(themes)) observer.disconnect();
      });
      observer.observe(host, { childList: true, subtree: true });
    })
    .catch(() => {});
})();
