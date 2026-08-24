(() => {
  const slug = new URLSearchParams(window.location.search).get('country') || 'iceland';
  const safeSlug = /^[a-z0-9-]+$/.test(slug) ? slug : 'iceland';
  const version = '20260824-2058';

  const projectPoint = (coordinates, bounds, offset = { x: 0, y: 0 }) => {
    if (!coordinates || !bounds) return null;
    const longitudeRange = bounds.east - bounds.west;
    const latitudeRange = bounds.north - bounds.south;
    if (longitudeRange <= 0 || latitudeRange <= 0) return null;
    return {
      x: ((coordinates.longitude - bounds.west) / longitudeRange) * 100 + (offset.x || 0),
      y: ((bounds.north - coordinates.latitude) / latitudeRange) * 100 + (offset.y || 0)
    };
  };

  Promise.all([
    fetch(`data/maps/${safeSlug}.json?v=${version}`, { cache: 'no-store' }).then((response) => {
      if (!response.ok) throw new Error('Map config not found');
      return response.json();
    }),
    fetch(`data/countries/${safeSlug}.json?v=${version}`, { cache: 'no-store' }).then((response) => {
      if (!response.ok) throw new Error('Country data not found');
      return response.json();
    })
  ])
    .then(([mapConfig, country]) => {
      const apply = () => {
        const mapImage = document.querySelector('#country-map-art .map-base');
        const sceneMarkers = document.querySelectorAll('#map-markers .map-marker[data-scene]');
        const heroMarker = document.querySelector('#map-markers .map-hero-marker');
        if (!mapImage || !sceneMarkers.length || !heroMarker) return false;

        const source = `${mapConfig.source}?v=${version}`;
        if (mapImage.dataset.atlasMapSource !== source) {
          mapImage.dataset.atlasMapSource = source;
          mapImage.src = source;
        }

        sceneMarkers.forEach((marker) => {
          const scene = country.scenes.find((item) => item.id === marker.dataset.scene);
          if (!scene) return;
          const offset = mapConfig.markerOffsets?.[scene.id] || { x: 0, y: 0 };
          const point = projectPoint(scene.coordinates, mapConfig.bounds, offset);
          if (!point) return;
          marker.style.left = `${point.x}%`;
          marker.style.top = `${point.y}%`;
        });

        const heroOffset = mapConfig.markerOffsets?.hero || { x: 0, y: 0 };
        const heroPoint = projectPoint(country.hero?.coordinates, mapConfig.bounds, heroOffset);
        if (heroPoint) {
          heroMarker.style.left = `${heroPoint.x}%`;
          heroMarker.style.top = `${heroPoint.y}%`;
        }

        return true;
      };

      if (apply()) return;
      const app = document.querySelector('#app');
      if (!app) return;
      const observer = new MutationObserver(() => {
        if (apply()) observer.disconnect();
      });
      observer.observe(app, { childList: true, subtree: true });
    })
    .catch(() => {
      /* Country pages without an atlas map config keep their existing map. */
    });
})();
