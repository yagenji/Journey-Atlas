(() => {
  const HEADER_SELECTOR = '.top-header, .site-header';
  const HERO_SELECTOR = '.top-hero, .country-page .hero';

  function getThreshold(header) {
    const hero = document.querySelector(HERO_SELECTOR);
    if (!hero) return Math.max(1, header.offsetHeight);
    return Math.max(header.offsetHeight, hero.offsetTop + hero.offsetHeight - header.offsetHeight);
  }

  function syncCountryHeroSafeArea(header) {
    const heroCopy = document.querySelector('.country-page .hero-copy');
    if (!heroCopy) return;
    heroCopy.style.setProperty('padding-top', '42px', 'important');
    heroCopy.style.setProperty('top', `${header.offsetHeight}px`, 'important');
  }

  function syncHeader() {
    const header = document.querySelector(HEADER_SELECTOR);
    if (!header) return;
    syncCountryHeroSafeArea(header);
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