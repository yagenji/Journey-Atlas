(() => {
  const JAPAN_AREA_KM2 = 377973.68;
  const GSI_AREA_REFERENCE_DATE = '2026-07-01';
  const POPULATION_ROUNDING_THRESHOLD = 100000;

  function currentSlug() {
    return document.documentElement.dataset.country
      || new URLSearchParams(window.location.search).get('country')
      || '';
  }

  function formatPercent(value) {
    if (value >= 10) return String(Math.round(value));
    if (value >= 1) return value.toFixed(1).replace(/\.0$/, '');
    if (value >= 0.1) return value.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
    if (value >= 0.001) return value.toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
    if (value >= 0.0001) return value.toFixed(5).replace(/0+$/, '').replace(/\.$/, '');
    return value.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
  }

  function formatRoundedPopulation(value) {
    const tenThousands = Math.round(value / 10000);
    if (tenThousands >= 10000) {
      const hundredMillions = Math.floor(tenThousands / 10000);
      const remainder = tenThousands % 10000;
      if (!remainder) return `${hundredMillions}億人`;
      return `${hundredMillions}億${remainder.toLocaleString('ja-JP')}万人`;
    }
    return `${tenThousands.toLocaleString('ja-JP')}万人`;
  }

  function enhancePopulationDisplay() {
    const groups = [...document.querySelectorAll('#facts > div')];
    if (!groups.length) return false;
    const populationGroup = groups.find((group) => group.querySelector('dt')?.textContent?.trim() === '人口');
    if (!populationGroup) return true;
    const value = populationGroup.querySelector('dd');
    if (!value) return true;
    const text = value.textContent?.trim() || '';
    if (!text || text.startsWith('約')) return true;
    const match = text.match(/^([0-9][0-9,]*)\s*人?(.*)$/);
    if (!match) return true;
    const population = Number(match[1].replaceAll(',', ''));
    if (!Number.isFinite(population) || population < POPULATION_ROUNDING_THRESHOLD) return true;
    value.textContent = `約${formatRoundedPopulation(population)}${match[2]}`;
    return true;
  }

  function enhanceAreaComparison() {
    if (currentSlug() === 'japan') return true;
    const groups = [...document.querySelectorAll('#facts > div')];
    if (!groups.length) return false;
    const areaGroup = groups.find((group) => group.querySelector('dt')?.textContent?.trim() === '面積');
    if (!areaGroup) return true;
    const value = areaGroup.querySelector('dd');
    if (!value) return true;
    const text = value.textContent?.trim() || '';
    if (text.includes('日本')) return true;
    const match = text.replaceAll(',', '').match(/([0-9]+(?:\.[0-9]+)?)\s*km²/i);
    if (!match) return true;
    const areaKm2 = Number(match[1]);
    if (!Number.isFinite(areaKm2) || areaKm2 <= 0) return true;
    const percent = (areaKm2 / JAPAN_AREA_KM2) * 100;
    value.textContent = `${text}（日本の約${formatPercent(percent)}%）`;
    value.dataset.japanAreaReference = GSI_AREA_REFERENCE_DATE;
    return true;
  }

  function enhanceCountryProfile() {
    const populationReady = enhancePopulationDisplay();
    const areaReady = enhanceAreaComparison();
    return populationReady && areaReady;
  }

  const app = document.querySelector('#app');
  if (!app) return;
  if (enhanceCountryProfile()) return;

  const observer = new MutationObserver(() => {
    if (enhanceCountryProfile()) observer.disconnect();
  });
  observer.observe(app, { childList: true, subtree: true });
})();