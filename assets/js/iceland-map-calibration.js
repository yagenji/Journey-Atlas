(() => {
  const params = new URLSearchParams(window.location.search);
  if ((params.get('country') || 'iceland') !== 'iceland') return;

  /*
    The production illustration contains generous ocean margins, so the
    geographic extent of Iceland occupies only part of the full image box.
    These positions are calibrated to the visible island rather than the
    outer image rectangle. Label directions are also set per point so the
    place names do not collide with neighbouring numbered pins.
  */
  const positions = {
    skogafoss: { x: 46.1, y: 65.1, label: 'below' },
    jokulsarlon: { x: 71.6, y: 59.2, label: 'below' },
    studlagil: { x: 78.3, y: 46.6, label: 'right' },
    thingvellir: { x: 33.7, y: 56.9, label: 'left' },
    geysir: { x: 40.0, y: 56.3, label: 'above' },
    myvatn: { x: 65.3, y: 41.6, label: 'above' },
    kirkjufell: { x: 17.0, y: 49.1, label: 'right' },
    landmannalaugar: { x: 49.5, y: 60.0, label: 'right' }
  };

  function calibrate() {
    const markers = document.querySelectorAll('#map-markers .map-marker[data-scene]');
    if (!markers.length) return false;

    markers.forEach((marker) => {
      const point = positions[marker.dataset.scene];
      if (!point) return;
      marker.style.left = `${point.x}%`;
      marker.style.top = `${point.y}%`;
      marker.dataset.labelPosition = point.label;
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
