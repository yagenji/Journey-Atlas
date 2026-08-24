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
    if (!markers) return false;
    if (markers.querySelector('.map-hero-marker')) return true;

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

  function matchFooterToTop() {
    const footer = document.querySelector('.atlas-colophon');
    if (!footer) return false;
    if (footer.classList.contains('atlas-colophon--legal')) return true;

    footer.classList.add('atlas-colophon--legal');
    footer.innerHTML = `
      <div class="atlas-legal-footer__inner">
        <p class="atlas-legal-footer__copyright">© 2026 Makoto Yagenji · 無断使用・転載を禁じます</p>
        <div class="atlas-legal-footer__bottom">
          <p class="atlas-legal-footer__note">イラストとことばは、実在する場所・景色・文化をもとに編集したJOURNEY ATLASのコンテンツです。</p>
          <a class="atlas-legal-footer__contact" href="mailto:journeylensmy@gmail.com?subject=JOURNEY%20ATLAS%20%E3%81%B8%E3%81%AE%E3%81%94%E9%80%A3%E7%B5%A1">連絡</a>
        </div>
      </div>`;
    return true;
  }

  function enhance(data) {
    const markerDone = insertMarker(data);
    const footerDone = matchFooterToTop();
    return markerDone && footerDone;
  }

  fetch(`data/countries/${safeSlug}.json?v=20260824-1247`)
    .then((response) => {
      if (!response.ok) throw new Error('Country data not found');
      return response.json();
    })
    .then((data) => {
      if (enhance(data)) return;
      const app = document.querySelector('#app');
      if (!app) return;
      const observer = new MutationObserver(() => {
        if (enhance(data)) observer.disconnect();
      });
      observer.observe(app, { childList: true, subtree: true });
    })
    .catch(() => {});
})();