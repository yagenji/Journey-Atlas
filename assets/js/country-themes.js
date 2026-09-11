(() => {
  const params = new URLSearchParams(window.location.search);
  const slug = params.get('country') || document.documentElement.dataset.country || '';
  if (!slug) return;

  let themes = [];

  const render = () => {
    const section = document.querySelector('#country-theme-context');
    const list = document.querySelector('#country-theme-list');
    if (!section || !list) return false;

    // Generated Country HTML already contains taxonomy chips. Keep those visible
    // immediately so the theme row never depends on a second network request.
    if (!themes.length) {
      if (list.querySelector('.country-theme-chip')) {
        section.hidden = false;
        return true;
      }
      return false;
    }

    const matches = themes.filter((theme) => Array.isArray(theme.examples) && theme.examples.includes(slug));
    if (!matches.length) {
      // Preserve any server-rendered taxonomy chips rather than hiding a valid
      // row because a runtime taxonomy response is stale or temporarily empty.
      section.hidden = !list.querySelector('.country-theme-chip');
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
        if (render() && themes.length) observer.disconnect();
      })
    : null;

  if (observer && host) observer.observe(host, { childList: true, subtree: true });

  // First try the generated chips as soon as the Country template is mounted.
  render();

  const taxonomyUrl = new URL('data/theme-taxonomy.json', document.baseURI);
  taxonomyUrl.searchParams.set('v', '20260911-theme-context-v3');

  fetch(taxonomyUrl.href, { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error('Theme taxonomy not found');
      return response.json();
    })
    .then((payload) => {
      themes = Array.isArray(payload.themes) ? payload.themes : [];
      if (render() && observer) observer.disconnect();
    })
    .catch(() => {
      // The build-time injected chips remain the authoritative fallback.
      render();
    });
})();
