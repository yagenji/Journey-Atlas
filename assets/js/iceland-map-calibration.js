(() => {
  const params = new URLSearchParams(window.location.search);
  if ((params.get('country') || 'iceland') !== 'iceland') return;

  const positions = {
    skogafoss: { x: 46.1, y: 65.1 },
    jokulsarlon: { x: 71.6, y: 59.2 },
    studlagil: { x: 78.3, y: 46.6 },
    myvatn: { x: 65.3, y: 41.6 },
    kirkjufell: { x: 17.0, y: 49.1 },
    thingvellir: { x: 33.7, y: 56.9 },
    geysir: { x: 40.0, y: 56.3 },
    landmannalaugar: { x: 49.5, y: 60.0 }
  };
  const heroPosition = { x: 42.7, y: 64.2 };

  function calibrateScenes() {
    const markers = document.querySelectorAll('#map-markers .map-marker[data-scene]');
    if (!markers.length) return false;
    markers.forEach((marker) => {
      const point = positions[marker.dataset.scene];
      if (!point) return;
      marker.style.left = `${point.x}%`;
      marker.style.top = `${point.y}%`;
    });
    return true;
  }

  function calibrateHero() {
    const marker = document.querySelector('#map-markers .map-hero-marker');
    if (!marker) return false;
    marker.style.left = `${heroPosition.x}%`;
    marker.style.top = `${heroPosition.y}%`;
    return true;
  }

  function calibrateAll() {
    return calibrateScenes() && calibrateHero();
  }

  if (calibrateAll()) return;

  const app = document.querySelector('#app');
  if (!app) return;
  const observer = new MutationObserver(() => {
    if (calibrateAll()) observer.disconnect();
  });
  observer.observe(app, { childList: true, subtree: true });
})();