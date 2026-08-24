(() => {
  const params = new URLSearchParams(window.location.search);
  if ((params.get('country') || 'iceland') !== 'iceland') return;

  const version = '20260824-1948';
  const parts = Array.from(
    { length: 10 },
    (_, index) =>
      `assets/images/iceland/v3/hero-parts/part-${String(index + 1).padStart(2, '0')}.b64?v=${version}`
  );

  const heroSource = Promise.all(
    parts.map((url) =>
      fetch(url, { cache: 'no-store' }).then((response) => {
        if (!response.ok) throw new Error(`Hero part missing: ${url}`);
        return response.text();
      })
    )
  ).then((chunks) => {
    const encoded = chunks.join('').replace(/\s+/g, '');
    if (!encoded.startsWith('UklGR')) throw new Error('Hero WebP is invalid');
    return `data:image/webp;base64,${encoded}`;
  });

  const applyHero = (source) => {
    const hero = document.querySelector('.hero-art');
    if (!hero) return false;
    hero.style.setProperty('background-image', `url("${source}")`, 'important');
    hero.classList.add('has-image');
    hero.querySelectorAll('.art-placeholder, .scene-placeholder').forEach((placeholder) => {
      placeholder.hidden = true;
    });
    return true;
  };

  heroSource
    .then((source) => {
      if (applyHero(source)) return;
      const root = document.querySelector('#app') || document.body;
      const observer = new MutationObserver(() => {
        if (applyHero(source)) observer.disconnect();
      });
      observer.observe(root, { childList: true, subtree: true });
    })
    .catch((error) => console.error('Iceland hero failed to load', error));
})();
