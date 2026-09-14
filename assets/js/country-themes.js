(() => {
  const params = new URLSearchParams(window.location.search);
  const slug = params.get('country') || document.documentElement.dataset.country || '';
  if (!slug) return;

  let themes = [];

  const themeVisuals = {
    earth: { icon: 'landscape', accent: 'earth' },
    city: { icon: 'city', accent: 'city' },
    history: { icon: 'history', accent: 'history' },
    life: { icon: 'home', accent: 'life' },
    wildlife: { icon: 'wildlife', accent: 'wildlife' },
    sea: { icon: 'sea', accent: 'sea' },
    food: { icon: 'food', accent: 'food' },
    road: { icon: 'road', accent: 'road' },
  };

  const labelToTheme = {
    '地球の風景': 'earth',
    '街を歩く': 'city',
    '時をたどる': 'history',
    '暮らしに出会う': 'life',
    '野生に会う': 'wildlife',
    '海の世界へ': 'sea',
    '食をめぐる': 'food',
    '道の先へ': 'road',
  };

  const decorateChip = (span, themeId, label) => {
    const visual = themeVisuals[themeId] || { icon: 'compass', accent: 'default' };
    span.className = 'country-theme-chip';
    span.dataset.theme = visual.accent;
    span.innerHTML = `<svg class="country-theme-chip__icon" aria-hidden="true" viewBox="0 0 24 24"><use href="assets/icons/atlas-icons.svg#${visual.icon}"></use></svg><span>${label}</span>`;
  };

  const decorateExisting = (list) => {
    list.querySelectorAll('.country-theme-chip').forEach((span) => {
      if (span.dataset.theme) return;
      const label = span.textContent.trim();
      decorateChip(span, labelToTheme[label] || 'default', label);
    });
  };

  const render = () => {
    const section = document.querySelector('#country-theme-context');
    const list = document.querySelector('#country-theme-list');
    if (!section || !list) return false;

    // Generated Country HTML already contains taxonomy chips. Decorate and keep
    // them visible immediately so the theme row never depends on a second request.
    if (!themes.length) {
      if (list.querySelector('.country-theme-chip')) {
        decorateExisting(list);
        section.hidden = false;
        return true;
      }
      return false;
    }

    const matches = themes.filter((theme) => Array.isArray(theme.examples) && theme.examples.includes(slug));
    if (!matches.length) {
      decorateExisting(list);
      section.hidden = !list.querySelector('.country-theme-chip');
      return true;
    }

    list.replaceChildren(...matches.map((theme) => {
      const span = document.createElement('span');
      decorateChip(span, theme.id || labelToTheme[theme.label] || 'default', theme.label || '');
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

  render();

  const taxonomyUrl = new URL('data/theme-taxonomy.json', document.baseURI);
  taxonomyUrl.searchParams.set('v', '20260914-theme-visual-v4');

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
      render();
    });
})();