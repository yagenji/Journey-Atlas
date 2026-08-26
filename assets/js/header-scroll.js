(() => {
  const HEADER_SELECTOR = '.top-header, .site-header';
  const HERO_SELECTOR = '.top-hero, .country-page .hero';

  function getThreshold(header) {
    const hero = document.querySelector(HERO_SELECTOR);
    if (!hero) return Math.max(1, header.offsetHeight);
    return Math.max(header.offsetHeight, hero.offsetTop + hero.offsetHeight - header.offsetHeight);
  }

  function syncBrandCollision(header) {
    const hero = document.querySelector('.country-page .hero');
    const title = document.querySelector('.country-page .hero h1');
    const brand = header.querySelector('.country-brand');
    if (!hero || !title || !brand) return;

    const heroRect = hero.getBoundingClientRect();
    const titleRect = title.getBoundingClientRect();
    const sticky = window.scrollY >= getThreshold(header);
    const inHero = heroRect.bottom > header.offsetHeight;
    const colliding = !sticky && inHero && titleRect.top < header.offsetHeight + 14 && titleRect.bottom > 0;

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
