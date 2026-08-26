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

  function initHeader() {
    syncHeader();
    window.addEventListener('scroll', syncHeader, { passive: true });
    window.addEventListener('resize', syncHeader);

    const app = document.querySelector('#app');
    if (app && 'MutationObserver' in window) {
      const observer = new MutationObserver(syncHeader);
      observer.observe(app, { childList: true, subtree: false });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeader, { once: true });
  } else {
    initHeader();
  }
})();
