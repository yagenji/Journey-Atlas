(() => {
  const JAPAN_AREA_KM2 = 377973.68;
  const GSI_AREA_REFERENCE_DATE = '2026-07-01';

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

  const app = document.querySelector('#app');
  if (!app) return;
  if (enhanceAreaComparison()) return;

  const observer = new MutationObserver(() => {
    if (enhanceAreaComparison()) observer.disconnect();
  });
  observer.observe(app, { childList: true, subtree: true });
})();
