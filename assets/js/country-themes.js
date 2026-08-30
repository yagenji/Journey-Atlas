(() => {
  const params = new URLSearchParams(window.location.search);
  const slug = params.get('country') || document.documentElement.dataset.country || '';
  if (!slug) return;

  let themes = [];

  const render = () => {
    if (!themes.length) return false;
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

  const host = document.querySelector('#app');
  const observer = host
    ? new MutationObserver(() => {
        if (render()) observer.disconnect();
      })
    : null;

  if (observer && host) observer.observe(host, { childList: true, subtree: true });

  fetch('data/theme-taxonomy.json?v=20260830-theme-context', { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error('Theme taxonomy not found');
      return response.json();
    })
    .then((payload) => {
      themes = Array.isArray(payload.themes) ? payload.themes : [];
      if (render() && observer) observer.disconnect();
    })
    .catch(() => {});
})();
