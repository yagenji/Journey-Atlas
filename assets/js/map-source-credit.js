/* Read the displayed SVG's own provenance: Country JSON may predate new neighboring land. */
(() => {
  const app = document.querySelector('#app');
  if (!app) return;

  const observer = new MutationObserver(() => {
    const image = app.querySelector('#country-map-art .map-base[src]');
    const legend = app.querySelector('.map-legend--below');
    if (!image || !legend) return;
    observer.disconnect();

    const footer = document.querySelector('.atlas-footer__copyright');
    const legendCredit = legend.querySelector('.map-legend__source-credit');
    const footerCredit = footer?.querySelector('.map-legend__source-credit');

    // Keep attribution, but do not insert a technical "地図データ" line beneath the map.
    // Country JSON may still use the older default placement, so normalize it here.
    if (legendCredit) {
      if (footer) {
        if (footerCredit) {
          legendCredit.remove();
        } else {
          legendCredit.textContent = '© OpenStreetMap contributors · ODbL 1.0';
          footer.append(legendCredit);
        }
      }
      return;
    }
    if (image.parentElement?.dataset.sourceCreditPlacement === 'footer' && footerCredit) return;

    const rawUrl = image.getAttribute('src') || '';
    const url = new URL(rawUrl, document.baseURI);
    if (url.origin !== location.origin || !/\.svg$/i.test(url.pathname)) return;

    // Reuse the image's HTTP cache where possible: never bypass it just for credit.
    fetch(url.href)
      .then((response) => {
        if (!response.ok) throw new Error('Map SVG provenance unavailable');
        return response.text();
      })
      .then((text) => {
        const xml = new DOMParser().parseFromString(text, 'image/svg+xml');
        if (xml.querySelector('parsererror')) throw new Error('Map SVG provenance is invalid XML');
        const context = xml.querySelector('[id="geographic-context"]');
        const provenance = context?.querySelector('desc')?.textContent || '';
        if (!/OpenStreetMap|\bODbL\b/i.test(provenance)) return;
        if (legend.querySelector('.map-legend__source-credit')) return;
        if (footer?.querySelector('.map-legend__source-credit')) return;

        const credit = document.createElement('a');
        credit.className = 'map-legend__source-credit';
        credit.href = 'https://www.openstreetmap.org/copyright';
        credit.target = '_blank';
        credit.rel = 'noopener noreferrer';
        credit.textContent = footer
          ? '© OpenStreetMap contributors · ODbL 1.0'
          : '地図データ © OpenStreetMap contributors · ODbL 1.0';
        credit.style.flexBasis = '100%';
        credit.style.textAlign = 'left';
        credit.style.color = 'inherit';
        credit.style.fontSize = '11px';
        credit.style.lineHeight = '1.5';
        credit.style.textDecoration = 'underline';
        credit.style.textUnderlineOffset = '2px';
        (footer || legend).append(credit);
      })
      .catch((error) => {
        console.warn('Map source attribution could not be verified:', error);
      });
  });

  observer.observe(app, { childList: true, subtree: true, attributes: true, attributeFilter: ['src'] });
})();
