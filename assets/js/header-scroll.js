(() => {
  const HEADER_SELECTOR = '.top-header, .site-header';
  const HERO_SELECTOR = '.top-hero, .country-page .hero';
  const HERO_COPY_SELECTOR = '.top-hero .hero-copy, .country-page .hero-copy';
  const BRAND_SELECTOR = '.brand-block, .country-brand';

  function getThreshold(header) {
    const hero = document.querySelector(HERO_SELECTOR);
    if (!hero) return Math.max(1, header.offsetHeight);
    return Math.max(header.offsetHeight, hero.offsetTop + hero.offsetHeight - header.offsetHeight);
  }

  function getHeroTextBounds() {
    const copy = document.querySelector(HERO_COPY_SELECTOR);
    if (!copy) return null;

    const nodes = Array.from(copy.children).filter((node) => {
      const style = window.getComputedStyle(node);
      return !node.hidden && style.display !== 'none' && style.visibility !== 'hidden';
    });
    if (!nodes.length) return null;

    const rects = nodes.map((node) => node.getBoundingClientRect());
    return {
      top: Math.min(...rects.map((rect) => rect.top)),
      bottom: Math.max(...rects.map((rect) => rect.bottom))
    };
  }

  function syncBrandCollision(header) {
    const hero = document.querySelector(HERO_SELECTOR);
    const brand = header.querySelector(BRAND_SELECTOR);
    const textBounds = getHeroTextBounds();
    if (!hero || !brand || !textBounds) return;

    const heroRect = hero.getBoundingClientRect();
    const sticky = window.scrollY >= getThreshold(header);
    const inHero = heroRect.bottom > header.offsetHeight;
    const collisionZoneBottom = header.offsetHeight + 14;
    const colliding = !sticky && inHero && textBounds.top < collisionZoneBottom && textBounds.bottom > 0;

    brand.style.transition = 'opacity .16s ease, visibility .16s ease';
    brand.style.opacity = colliding ? '0' : '1';
    brand.style.visibility = colliding ? 'hidden' : 'visible';
    brand.style.pointerEvents = colliding ? 'none' : 'auto';
  }

  function syncHeader() {
    const header = document.querySelector(HEADER_SELECTOR);
    if (!header) return;
    header.classList.toggle('is-scroll-sticky', window.scrollY >= getThreshold(header));
    syncBrandCollision(header);
  }

  // Historic Country JSON may describe only its approved national outline while
  // the newly staged SVG adds OSM-derived surrounding land. Read the actual SVG
  // provenance instead of changing approved Country data or showing false credit.
  function syncMapSourceCredit() {
    const image = document.querySelector('#country-map-art .map-base');
    if (!image || image.dataset.sourceCreditBound === '1') return;
    image.dataset.sourceCreditBound = '1';
    let requested = false;
    async function inspectSource() {
      const legend = document.querySelector('.map-legend--below');
      if (requested || !legend || legend.querySelector('.map-legend__source-credit')) return;
      const url = image.currentSrc || image.src;
      if (!url || !new URL(url, location.href).pathname.endsWith('.svg')) return;
      requested = true;
      try {
        const response = await fetch(url, { cache: 'force-cache' });
        if (!response.ok) return;
        const xml = new DOMParser().parseFromString(await response.text(), 'image/svg+xml');
        if (xml.querySelector('parsererror')) return;
        const provenance = [xml.querySelector('#geographic-context desc'), ...xml.querySelectorAll('metadata')];
        if (!provenance.some((node) => /OpenStreetMap|\bODbL\b/i.test(node?.textContent || ''))) return;
        if (legend.querySelector('.map-legend__source-credit')) return;
        const credit = document.createElement('a');
        credit.className = 'map-legend__source-credit';
        credit.href = 'https://www.openstreetmap.org/copyright';
        credit.target = '_blank';
        credit.rel = 'noopener noreferrer';
        credit.textContent = '地図データ © OpenStreetMap contributors · ODbL 1.0';
        credit.style.flexBasis = '100%';
        credit.style.textAlign = 'left';
        credit.style.color = 'inherit';
        credit.style.fontSize = '11px';
        credit.style.lineHeight = '1.5';
        credit.style.textDecoration = 'underline';
        credit.style.textUnderlineOffset = '2px';
        legend.append(credit);
      } catch (error) {
        console.warn('Map source attribution could not be inspected', error);
      }
    }
    image.addEventListener('load', inspectSource, { once: true });
    if (image.complete && image.naturalWidth > 0) void inspectSource();
  }

  function initHeader() {
    syncHeader();
    syncMapSourceCredit();
    window.addEventListener('scroll', syncHeader, { passive: true });
    window.addEventListener('resize', syncHeader);

    const app = document.querySelector('#app');
    if (app && 'MutationObserver' in window) {
      const observer = new MutationObserver(() => {
        syncHeader();
        syncMapSourceCredit();
      });
      observer.observe(app, { childList: true, subtree: false });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeader, { once: true });
  } else {
    initHeader();
  }
})();
