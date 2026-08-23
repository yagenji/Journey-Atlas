(() => {
  const ATLAS_TOTAL = 201;
  const ADDITIONS = [
    {
      order: 200,
      iso2: 'HK',
      flag: '🇭🇰',
      slug: 'hong-kong',
      nameEn: 'HONG KONG',
      nameJa: '香港',
      journeyLensPublished: false,
      atlasPublished: false,
      href: '',
      image: ''
    },
    {
      order: 201,
      iso2: 'MO',
      flag: '🇲🇴',
      slug: 'macao',
      nameEn: 'MACAO',
      nameJa: 'マカオ',
      journeyLensPublished: false,
      atlasPublished: false,
      href: '',
      image: ''
    }
  ];

  const nativeFetch = window.fetch.bind(window);

  function jsonResponse(response, data) {
    const headers = new Headers(response.headers);
    headers.set('content-type', 'application/json; charset=utf-8');
    return new Response(JSON.stringify(data), {
      status: response.status,
      statusText: response.statusText,
      headers
    });
  }

  window.fetch = async (...args) => {
    const request = args[0];
    const target = typeof request === 'string' ? request : (request?.url || '');

    if (target.includes('data/atlas-destinations.json')) {
      const response = await nativeFetch(...args);
      if (!response.ok) return response;
      try {
        const data = await response.clone().json();
        data.destinations = Array.isArray(data.destinations) ? data.destinations : [];
        const existing = new Set(data.destinations.map(item => item.iso2));
        ADDITIONS.forEach(item => {
          if (!existing.has(item.iso2)) data.destinations.push({ ...item });
        });
        data.count = data.destinations.length;
        data.updatedAt = '2026-08-23';
        data.definition = 'UN Member States 193 + Japan-recognized non-UN states (Vatican City, Kosovo, Cook Islands, Niue) + Taiwan + Hong Kong + Macao + Antarctica = 201 JOURNEY ATLAS destinations.';
        data.behavior = 'Render all 201 destinations on the top page from the beginning. Only atlasPublished=true entries are links.';
        return jsonResponse(response, data);
      } catch {
        return response;
      }
    }

    if (target.includes('data/region-taxonomy.json')) {
      const response = await nativeFetch(...args);
      if (!response.ok) return response;
      try {
        const data = await response.clone().json();
        data.updatedAt = '2026-08-23';
        data.rule = 'Each of the 201 JOURNEY ATLAS destinations belongs to exactly one top-level region. Subregions are spatial navigation aids. Hong Kong and Macao are treated as independent travel destinations in East Asia.';
        const asia = (data.regions || []).find(region => region.id === 'asia');
        if (asia) {
          asia.iso2 = Array.isArray(asia.iso2) ? asia.iso2 : [];
          ['HK', 'MO'].forEach(code => {
            if (!asia.iso2.includes(code)) asia.iso2.push(code);
          });
          const eastAsia = (asia.subregions || []).find(region => region.id === 'east-asia');
          if (eastAsia) {
            eastAsia.iso2 = Array.isArray(eastAsia.iso2) ? eastAsia.iso2 : [];
            ['HK', 'MO'].forEach(code => {
              if (!eastAsia.iso2.includes(code)) eastAsia.iso2.push(code);
            });
          }
        }
        return jsonResponse(response, data);
      } catch {
        return response;
      }
    }

    return nativeFetch(...args);
  };

  const aboutHtml = '<span>JOURNEY ATLASは、国連加盟193か国と、日本が国家承認している国のうち国連未加盟のバチカン、コソボ、クック諸島、ニウエを基本対象にしています。さらに、旅行先として独立して探せるよう、台湾・香港・マカオ・南極を加え、計201の国・地域を掲載します。</span><span>香港とマカオは中国の特別行政区です。台湾・香港・マカオ・南極を独立ページとして扱うのは、旅行先としての探しやすさを目的としたJOURNEY ATLAS独自の編集上の区分であり、国家承認に関する立場を示すものではありません。国連加盟国を基準にするため、日本が国家承認していない北朝鮮も含まれます。</span>';

  function applyScopeCopy() {
    const heroLead = document.querySelector('.hero-copy .lead');
    if (heroLead && heroLead.textContent.includes('199')) {
      heroLead.innerHTML = 'まだ知らない景色、心に残る出会い。<br>文化や人々の暮らし。<br>201の国・地域を、イラストとともに<br>めぐる世界図鑑です。';
    }

    const countryEntry = document.querySelector('.explore-card--country p');
    if (countryEntry?.textContent.includes('199')) countryEntry.textContent = '201の国・地域から、旅のインスピレーションを得る';

    const countriesCopy = document.querySelector('.countries .section-head p');
    if (countriesCopy?.textContent.includes('199')) countriesCopy.textContent = '世界201の国・地域を、イラストで紹介しています。';

    const themeCopy = document.querySelector('.theme-panel .detail-heading p');
    if (themeCopy?.textContent.includes('199')) themeCopy.textContent = 'あなたが惹かれるのは、どんな旅？ 201の国・地域を、8つのテーマから見つけてみよう。';

    const rail = document.querySelector('#country-rail');
    if (rail?.getAttribute('aria-label')?.includes('199')) rail.setAttribute('aria-label', '201の国・地域');

    const count = document.querySelector('#country-count');
    if (count?.textContent.includes('199')) count.textContent = `${ATLAS_TOTAL} DESTINATIONS`;

    const mapCount = document.querySelector('#map-region-count');
    if (mapCount?.textContent.includes('199')) mapCount.textContent = `${ATLAS_TOTAL} DESTINATIONS`;

    document.querySelectorAll('.explore-icon').forEach(icon => icon.remove());

    const about = document.querySelector('#about.about-note p');
    if (about && about.innerHTML !== aboutHtml) about.innerHTML = aboutHtml;

    const footer = document.querySelector('.atlas-colophon .meta');
    if (footer?.innerHTML.includes('199の国・地域')) footer.innerHTML = footer.innerHTML.replace('199の国・地域', '201の国・地域');
  }

  document.addEventListener('DOMContentLoaded', () => {
    applyScopeCopy();
    const observer = new MutationObserver(applyScopeCopy);
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    window.setTimeout(applyScopeCopy, 250);
    window.setTimeout(applyScopeCopy, 1000);
  });
})();
