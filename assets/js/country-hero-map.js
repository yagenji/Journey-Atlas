(() => {
  const slug = new URLSearchParams(window.location.search).get('country') || 'iceland';
  const safeSlug = /^[a-z0-9-]+$/.test(slug) ? slug : 'iceland';

  function projectPoint(coordinates, bounds) {
    if (!coordinates || !bounds) return null;
    const longitudeRange = bounds.east - bounds.west;
    const latitudeRange = bounds.north - bounds.south;
    if (longitudeRange <= 0 || latitudeRange <= 0) return null;
    return {
      x: ((coordinates.longitude - bounds.west) / longitudeRange) * 100,
      y: ((bounds.north - coordinates.latitude) / latitudeRange) * 100
    };
  }

  function insertMarker(data) {
    const markers = document.querySelector('#map-markers');
    if (!markers || markers.querySelector('.map-hero-marker')) return false;
    const point = projectPoint(data.hero?.coordinates, data.map?.bounds);
    if (!point) return true;

    const marker = document.createElement('div');
    marker.className = 'map-hero-marker';
    marker.dataset.heroLocation = 'true';
    marker.style.left = `${point.x}%`;
    marker.style.top = `${point.y}%`;
    marker.setAttribute('role', 'img');
    marker.setAttribute('aria-label', `代表画像の場所: ${data.hero.location || ''}`);
    marker.dataset.label = data.hero.location || '';
    marker.innerHTML = '<span aria-hidden="true">◆</span>';
    markers.append(marker);
    return true;
  }

  fetch(`data/countries/${safeSlug}.json?v=20260824-1228`)
    .then((response) => {
      if (!response.ok) throw new Error('Country data not found');
      return response.json();
    })
    .then((data) => {
      if (insertMarker(data)) return;
      const app = document.querySelector('#app');
      if (!app) return;
      const observer = new MutationObserver(() => {
        if (insertMarker(data)) observer.disconnect();
      });
      observer.observe(app, { childList: true, subtree: true });
    })
    .catch(() => {});
})();