(() => {
  const cards = [
    document.querySelector('.explore-card--country .explore-card__art'),
    document.querySelector('.explore-card--map .explore-card__art'),
    document.querySelector('.explore-card--theme .explore-card__art')
  ];
  const positions = ['0% 50%','50% 50%','100% 50%'];

  // Prevent top.js from replacing the approved entry artwork with Hero crops.
  if (typeof window.applyHeroDerivedArt === 'function') {
    window.applyHeroDerivedArt = () => {};
  }

  fetch('assets/images/top/explore-entry-sprite.webp.b64?v=20260823-1202')
    .then((response) => {
      if (!response.ok) throw new Error('Explore entry artwork missing');
      return response.text();
    })
    .then((encoded) => {
      const source = encoded.trim();
      if (source.length < 10000) throw new Error('Explore entry artwork incomplete');
      const image = `url("data:image/webp;base64,${source}")`;
      cards.forEach((art, index) => {
        if (!art) return;
        art.style.backgroundImage = image;
        art.style.backgroundSize = '300% 100%';
        art.style.backgroundPosition = positions[index];
        art.style.backgroundRepeat = 'no-repeat';
      });
    })
    .catch(() => {});
})();
