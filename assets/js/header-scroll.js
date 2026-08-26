(() => {
  const HEADER_SELECTOR = '.top-header, .site-header';
  const HERO_SELECTOR = '.top-hero, .country-page .hero';

  function getThreshold(header) {
    const hero = document.querySelector(HERO_SELECTOR);
    if (!hero) return Math.max(1, header.offsetHeight);
    return Math.max(header.offsetHeight, hero.offsetTop + hero.offsetHeight - header.offsetHeight);
  }

  function syncHeader() {
    const header = document.querySelector(HEADER_SELECTOR);
    if (!header) return;
    header.classList.toggle('is-scroll-sticky', window.scrollY >= getThreshold(header));
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