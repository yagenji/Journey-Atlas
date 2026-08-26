(() => {
  const SELECTOR = '.top-header, .site-header';

  function syncHeader() {
    const header = document.querySelector(SELECTOR);
    if (!header) return;
    const threshold = Math.max(1, header.offsetHeight);
    header.classList.toggle('is-scroll-sticky', window.scrollY > threshold);
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