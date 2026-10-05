/* Keep OpenStreetMap attribution aligned with the actual map provenance. */
(() => {
  const app = document.querySelector('#app');
  if (!app) return;

  const CREDIT_SELECTOR = '.map-legend__source-credit';
  const OSM_PATTERN = /OpenStreetMap/i;

  function removeCredits(legend) {
    legend.querySelectorAll(CREDIT_SELECTOR).forEach((credit) => credit.remove());
    document.querySelectorAll(`.atlas-footer__copyright ${CREDIT_SELECTOR}`).forEach((credit) => {
      const previous = credit.previousSibling;
      credit.remove();
      if (previous?.nodeName === 'BR') previous.remove();
    });
  }

  function appendCredit(container, inFooter) {
    const credit = document.createElement('a');
    credit.className = 'map-legend__source-credit';
    credit.href = 'https://www.openstreetmap.org/copyright';
    credit.target = '_blank';
    credit.rel = 'noopener noreferrer';
    credit.textContent = inFooter
      ? '© OpenStreetMap contributors · ODbL 1.0'
      : '地図データ © OpenStreetMap contributors · ODbL 1.0';
    credit.style.flexBasis = '100%';
    credit.style.textAlign = 'left';
    credit.style.color = 'inherit';
    credit.style.fontSize = '11px';
    credit.style.lineHeight = '1.5';
    credit.style.textDecoration = 'underline';
    credit.style.textUnderlineOffset = '2px';
    if (inFooter) container.append(document.createElement('br'));
    container.append(credit);
  }

  const observer = new MutationObserver(() => {
    const image = app.querySelector('#country-map-art .map-base[src]');
    const legend = app.querySelector('.map-legend--below');
    if (!image || !legend) return;
    observer.disconnect();

    const slug = document.documentElement.dataset.country || '';
    const countryPromise = slug
      ? fetch(`data/countries/${slug}.json`, { cache: 'no-store' })
          .then((response) => response.ok ? response.json() : null)
          .catch(() => null)
      : Promise.resolve(null);

    const rawUrl = image.getAttribute('src') || '';
    let svgPromise = Promise.resolve('');
    try {
      const url = new URL(rawUrl, document.baseURI);
      if (url.origin === location.origin && /\.svg$/i.test(url.pathname)) {
        svgPromise = fetch(url.href)
          .then((response) => {
            if (!response.ok) throw new Error('Map SVG provenance unavailable');
            return response.text();
          })
          .catch(() => '');
      }
    } catch (_) {
      svgPromise = Promise.resolve('');
    }

    Promise.all([countryPromise, svgPromise])
      .then(([country, svgText]) => {
        const source = typeof country?.map?.source === 'string' ? country.map.source : '';
        let svgProvenance = '';
        if (svgText) {
          const xml = new DOMParser().parseFromString(svgText, 'image/svg+xml');
          if (!xml.querySelector('parsererror')) {
            const context = xml.querySelector('[id="geographic-context"]');
            const contextDesc = context?.querySelector('desc')?.textContent || '';
            const metadata = Array.from(xml.querySelectorAll('metadata'))
              .map((node) => node.textContent || '')
              .join(' ');
            svgProvenance = `${contextDesc} ${metadata}`;
          }
        }

        // ODbL is used by datasets other than OpenStreetMap (for example
        // geoBoundaries). Only explicit OpenStreetMap provenance warrants this
        // OpenStreetMap-specific attribution link.
        const hasOpenStreetMap = OSM_PATTERN.test(`${source} ${svgProvenance}`);
        const inFooter = country?.map?.sourceCreditPlacement === 'footer'
          || image.parentElement?.dataset.sourceCreditPlacement === 'footer';
        const footer = document.querySelector('.atlas-footer__copyright');
        const existing = [
          ...legend.querySelectorAll(CREDIT_SELECTOR),
          ...(footer ? footer.querySelectorAll(CREDIT_SELECTOR) : []),
        ];

        if (!hasOpenStreetMap) {
          removeCredits(legend);
          return;
        }
        if (existing.length) return;

        const container = inFooter ? footer : legend;
        if (container) appendCredit(container, inFooter);
      })
      .catch((error) => {
        console.warn('Map source attribution could not be verified:', error);
      });
  });

  observer.observe(app, { childList: true, subtree: true, attributes: true, attributeFilter: ['src'] });
})();
