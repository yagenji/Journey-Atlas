(() => {
  const root = document.querySelector('.map-explorer');
  if (!root) return;

  const RATIO = 507.209 / 1000;
  const FRAMES = {
    region: {
      europe: [405, 14, 305, 305 * RATIO],
      'north-america': [-20, 4, 405, 405 * RATIO]
    },
    subregion: {
      'western-europe': [455, 76, 145, 145 * RATIO],
      'northern-north-america': [-10, 2, 350, 350 * RATIO]
    }
  };

  let raf = null;
  let settleTimer = null;

  function map() {
    return root.querySelector('.atlas-country-map');
  }

  function readView(svg) {
    return svg.getAttribute('viewBox').trim().split(/\s+/).map(Number);
  }

  function animateTo(target, duration = 240) {
    const svg = map();
    if (!svg || !target) return;
    if (raf) cancelAnimationFrame(raf);

    const from = readView(svg);
    const start = performance.now();

    function tick(now) {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      const next = from.map((value, i) => value + (target[i] - value) * eased);
      svg.setAttribute('viewBox', next.join(' '));
      if (p < 1) raf = requestAnimationFrame(tick);
    }

    raf = requestAnimationFrame(tick);
  }

  function activeFrame() {
    const sub = root.dataset.activeSubregion;
    if (sub && FRAMES.subregion[sub]) return FRAMES.subregion[sub];
    const region = root.dataset.activeRegion;
    return FRAMES.region[region] || null;
  }

  function settle(frame, delay) {
    if (!frame) return;
    if (settleTimer) clearTimeout(settleTimer);
    settleTimer = setTimeout(() => animateTo(frame, 220), delay);
  }

  root.addEventListener('click', event => {
    const target = event.target.closest('button');
    if (!target) return;

    if (target.matches('[data-map-tab]')) {
      const frame = FRAMES.region[target.dataset.mapTab];
      if (frame) settle(frame, 390);
      return;
    }

    if (target.matches('[data-s]')) {
      const frame = FRAMES.subregion[target.dataset.s];
      if (frame) settle(frame, 455);
      return;
    }

    if (target.matches('[data-clear-selection], [data-z="reset"]')) {
      requestAnimationFrame(() => settle(activeFrame(), 40));
    }
  });
})();
