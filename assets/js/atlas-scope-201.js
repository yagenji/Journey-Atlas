(() => {
  const ATLAS_TOTAL = 199;

  const aboutMarkup = `
    <div class="about-note__label">
      <span class="section-kicker">ABOUT</span>
      <strong>JOURNEY ATLAS</strong>
    </div>
    <div class="about-note__content">
      <p class="about-note__lead">JOURNEY ATLASは、次に行きたい世界と出会うための旅のビジュアル図鑑です。</p>
      <p>旅の計画を完成させるための情報サイトではなく、まだ知らない国や地域への入口をつくることを目的にしています。国・地図・テーマから世界をたどり、景色、街、歴史、暮らし、野生、海、食、道をきっかけに、「ここへ行ってみたい」と思える場所を見つける。実際に訪れた場所は、JOURNEY LENSの写真と物語へつながります。</p>
      <p class="about-note__definition"><b>掲載範囲について</b> 国連加盟193か国と、日本が国家承認している国のうち国連未加盟のバチカン、コソボ、クック諸島、ニウエを基本対象とし、旅行先として独立して探せるよう台湾・南極を加えた計199の国・地域を掲載します。台湾・南極を独立して扱うのは、旅行先としての探しやすさを目的とするJOURNEY ATLAS独自の編集上の区分であり、国家承認に関する立場を示すものではありません。国連加盟国を基準にするため、日本が国家承認していない北朝鮮も含まれます。</p>
    </div>`;

  function installWishLink() {
    if (document.querySelector('#wish-link')) return;
    const toggle = document.querySelector('#all-countries-toggle');
    if (!toggle?.parentElement) return;

    const actions = document.createElement('div');
    actions.className = 'country-head-actions';
    const wish = document.createElement('button');
    wish.type = 'button';
    wish.id = 'wish-link';
    wish.className = 'all-countries-toggle wish-list-toggle';
    wish.innerHTML = '♡ 行ってみたい国 <span>›</span>';

    toggle.replaceWith(actions);
    actions.append(wish, toggle);

    if (!document.querySelector('#country-head-actions-style')) {
      const style = document.createElement('style');
      style.id = 'country-head-actions-style';
      style.textContent = `
        .country-head-actions{display:flex;align-items:center;justify-content:flex-end;gap:10px;flex-wrap:wrap}
        .wish-list-toggle{color:#8a5c48}
        @media(max-width:760px){.country-head-actions{width:100%;justify-content:flex-start}}
      `;
      document.head.append(style);
    }
  }

  function applyScopeCopy() {
    const heroLead = document.querySelector('.hero-copy .lead');
    if (heroLead) {
      heroLead.innerHTML = `まだ知らない景色、心に残る出会い。<br>文化や人々の暮らし。<br>${ATLAS_TOTAL}の国・地域を、イラストとともに<br>めぐる世界図鑑です。`;
    }

    const countryEntry = document.querySelector('.explore-card--country p');
    if (countryEntry) countryEntry.textContent = `${ATLAS_TOTAL}の国・地域から、旅のインスピレーションを得る`;

    const countriesCopy = document.querySelector('.countries .section-head p');
    if (countriesCopy) countriesCopy.textContent = `世界${ATLAS_TOTAL}の国・地域を、イラストで紹介しています。`;

    const themeCopy = document.querySelector('.theme-panel .detail-heading p');
    if (themeCopy) themeCopy.textContent = `あなたが惹かれるのは、どんな旅？ ${ATLAS_TOTAL}の国・地域を、8つのテーマから見つけてみよう。`;

    const rail = document.querySelector('#country-rail');
    if (rail) rail.setAttribute('aria-label', `${ATLAS_TOTAL}の国・地域`);

    const count = document.querySelector('#country-count');
    if (count) count.textContent = `${ATLAS_TOTAL} DESTINATIONS`;

    const mapCount = document.querySelector('#map-region-count');
    if (mapCount) mapCount.textContent = `${ATLAS_TOTAL} DESTINATIONS`;

    document.querySelectorAll('.explore-icon').forEach((icon) => icon.remove());

    const lensHead = document.querySelector('.lens-head > div');
    if (lensHead && !lensHead.querySelector('.section-kicker')) {
      lensHead.insertAdjacentHTML('afterbegin', '<span class="section-kicker lens-kicker">EXPLORE BY PHOTO</span>');
    }

    const about = document.querySelector('#about.about-note');
    if (about && !about.querySelector('.about-note__content')) about.innerHTML = aboutMarkup;

    installWishLink();
  }

  applyScopeCopy();
  document.addEventListener('DOMContentLoaded', applyScopeCopy, { once: true });
})();
