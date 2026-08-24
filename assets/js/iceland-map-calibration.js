(() => {
  const params = new URLSearchParams(window.location.search);
  if ((params.get('country') || 'iceland') !== 'iceland') return;

  /*
    The production illustration contains generous ocean margins, so the
    geographic extent of Iceland occupies only part of the full image box.
    These positions are calibrated to the visible island rather than the
    outer image rectangle. Coordinates remain represented by the original
    country data; this layer only corrects the artwork-to-overlay alignment.
  */
  const positions = {
    skogafoss: { x: 46.1, y: 65.1 },
    jokulsarlon: { x: 71.6, y: 59.2 },
    studlagil: { x: 78.3, y: 46.6 },
    thingvellir: { x: 33.7, y: 56.9 },
    geysir: { x: 40.0, y: 56.3 },
    myvatn: { x: 65.3, y: 41.6 },
    kirkjufell: { x: 17.0, y: 49.1 },
    landmannalaugar: { x: 49.5, y: 60.0 }
  };

  function calibrate() {
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

  if (calibrate()) return;

  const app = document.querySelector('#app');
  if (!app) return;
  const observer = new MutationObserver(() => {
    if (calibrate()) observer.disconnect();
  });
  observer.observe(app, { childList: true, subtree: true });
})();
