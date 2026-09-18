/* Shared Country Profile enhancement. Japan area: Geospatial Information Authority
 * of Japan, 2026-04-01, 377,974.87 km²:
 * https://www.gsi.go.jp/KOKUJYOHO/MENCHO-title.htm
 * The Country's own area must already appear in its sourced Profile facts.
 * Do not guess a missing area or overwrite an explicit authored comparison.
 */
(() => {
  const JAPAN_AREA_KM2 = 377974.87;

  const formatComparison = (areaKm2) => {
    const percent = (areaKm2 / JAPAN_AREA_KM2) * 100;
    return `日本の約${percent < 1 ? percent.toFixed(2) : percent.toFixed(1)}%`;
  };

  const parseAreaKm2 = (value) => {
    const match = String(value || '').match(/([0-9][0-9,]*(?:\.[0-9]+)?)\s*(万)?\s*(?:km\s*[²2]|㎢|平方キロ(?:メートル)?)/i);
    if (!match) return null;
    const area = Number(match[1].replaceAll(',', '')) * (match[2] ? 10000 : 1);
    return Number.isFinite(area) && area > 0 ? area : null;
  };

  const enhance = () => {
    const facts = document.querySelector('#facts');
    if (!facts || !facts.children.length) return false;
    for (const entry of facts.children) {
      const label = entry.querySelector('dt')?.textContent?.trim();
      const value = entry.querySelector('dd');
      if (!value || label !== '面積') continue;
      const original = value.textContent.trim();
      if (/日本の|日本比/.test(original)) return true;
      const areaKm2 = parseAreaKm2(original);
      if (areaKm2 === null) {
        console.warn('Country area comparison not shown: source area and unit are missing or ambiguous.');
        return true;
      }
      value.append(document.createTextNode(`（${formatComparison(areaKm2)}）`));
      return true;
    }
    return true;
  };

  const app = document.querySelector('#app');
  if (!app || enhance()) return;
  const observer = new MutationObserver(() => {
    if (enhance()) observer.disconnect();
  });
  observer.observe(app, { childList: true, subtree: false });
})();
