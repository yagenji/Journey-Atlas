(() => {
  const LENS_ORIGIN = 'https://journey.yagenji.com/';
  const LENS_FEED = `${LENS_ORIGIN}rss.xml`;

  const normalizeLensImageUrl = (value) => {
    const source = String(value || '').trim();
    if (!source) return '';
    try {
      const url = new URL(source, LENS_ORIGIN);
      return /^https?:$/.test(url.protocol) ? url.href : '';
    } catch {
      return '';
    }
  };

  const imageFromEmbeddedHtml = (html) => {
    const source = String(html || '').trim();
    if (!source || !/<img\b/i.test(source)) return '';
    const documentFragment = new DOMParser().parseFromString(source, 'text/html');
    const image = documentFragment.querySelector('img');
    if (!image) return '';
    return normalizeLensImageUrl(
      image.getAttribute('src') ||
      image.getAttribute('data-src') ||
      image.getAttribute('data-lazy-src') ||
      ''
    );
  };

  const extractLensImage = (item) => {
    const enclosureUrl = normalizeLensImageUrl(item.querySelector('enclosure')?.getAttribute('url'));
    if (enclosureUrl) return enclosureUrl;

    for (const node of item.querySelectorAll('*')) {
      const localName = (node.localName || '').toLowerCase();
      if (localName !== 'content' && localName !== 'thumbnail') continue;
      const mediaUrl = normalizeLensImageUrl(node.getAttribute?.('url'));
      if (mediaUrl) return mediaUrl;
    }

    for (const node of item.querySelectorAll('*')) {
      const localName = (node.localName || '').toLowerCase();
      if (!['encoded', 'description', 'content'].includes(localName)) continue;
      const embeddedImage = imageFromEmbeddedHtml(node.textContent || '');
      if (embeddedImage) return embeddedImage;
    }

    const imageNode = [...item.querySelectorAll('*')].find((node) => (node.localName || '').toLowerCase() === 'image');
    return normalizeLensImageUrl(imageNode?.getAttribute?.('url') || imageNode?.textContent || '');
  };

  const verifyLensImage = (source) => new Promise((resolve) => {
    const url = normalizeLensImageUrl(source);
    if (!url) {
      resolve('');
      return;
    }
    const image = new Image();
    image.onload = () => resolve(url);
    image.onerror = () => resolve('');
    image.src = url;
  });

  const imageFromStoryPage = (storyUrl) => fetch(storyUrl, { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error('JOURNEY LENS story not found');
      return response.text();
    })
    .then((html) => {
      const documentFragment = new DOMParser().parseFromString(html, 'text/html');
      const candidate =
        documentFragment.querySelector('meta[property="og:image"]')?.getAttribute('content') ||
        documentFragment.querySelector('meta[name="twitter:image"]')?.getAttribute('content') ||
        documentFragment.querySelector('main img')?.getAttribute('src') ||
        documentFragment.querySelector('img')?.getAttribute('src') ||
        '';
      return normalizeLensImageUrl(candidate);
    })
    .catch(() => '');

  // app.js starts the Country fetch first, but all deferred scripts normally execute
  // before its callbacks. The mount observer below also covers any timing race.
  window.parseCountryLensFeed = function parseCountryLensFeed(xmlText, countrySlug) {
    const xml = new DOMParser().parseFromString(xmlText, 'application/xml');
    if (xml.querySelector('parsererror')) throw new Error('Invalid JOURNEY LENS RSS XML');

    return [...xml.querySelectorAll('item')].flatMap((item) => {
      const link = (item.querySelector('link')?.textContent || '').trim();
      const match = link.match(/^https:\/\/journey\.yagenji\.com\/([a-z]+)(\d+)\/$/);
      if (!match || match[1] !== countrySlug) return [];
      const title = (item.querySelector('title')?.textContent || '').trim();
      const titleParts = title.split('｜');
      const subtitle = titleParts.length > 1 ? titleParts.slice(1).join('｜').trim() : title;
      return [{
        link,
        sequence: Number(match[2]),
        subtitle,
        image: extractLensImage(item),
      }];
    }).sort((a, b) => a.sequence - b.sequence);
  };

  window.initCountryLensBridge = function initCountryLensBridge(data) {
    const section = document.querySelector('#country-lens-bridge');
    if (!section || !data?.slug || section.dataset.lensImageEnhancement === 'active') return;
    section.dataset.lensImageEnhancement = 'active';

    fetch(LENS_FEED, { cache: 'no-store' })
      .then((response) => {
        if (!response.ok) throw new Error('JOURNEY LENS RSS not found');
        return response.text();
      })
      .then((xmlText) => {
        const stories = window.parseCountryLensFeed(xmlText, data.slug);
        if (!stories.length) return null;

        const first = stories[0];
        const link = section.querySelector('#country-lens-link');
        const thumb = section.querySelector('#country-lens-thumb');
        const title = section.querySelector('#country-lens-title');
        const description = section.querySelector('#country-lens-description');
        const meta = section.querySelector('#country-lens-meta');

        if (link) {
          link.href = first.link;
          link.setAttribute('aria-label', `JOURNEY LENSで${data.nameJa}の写真と物語を見る`);
        }
        if (title) title.textContent = `写真と物語で見る${data.nameJa}`;
        if (description) description.textContent = `実際に訪れた${data.nameJa}を、写真と物語で。`;
        if (meta) meta.textContent = stories.length > 1 ? `${stories.length} STORIES　写真と物語を見る →` : '1 STORY　写真と物語を見る →';
        section.hidden = false;

        if (!thumb) return null;
        return verifyLensImage(first.image)
          .then((rssImage) => rssImage || imageFromStoryPage(first.link).then(verifyLensImage))
          .then((resolvedImage) => {
            if (!resolvedImage) return;
            thumb.style.backgroundImage = `url("${resolvedImage.replaceAll('"', '%22')}")`;
            thumb.classList.add('has-image');
          });
      })
      .catch(() => {
        section.hidden = true;
      });
  };

  const enhanceMountedLensBridge = () => {
    const section = document.querySelector('#country-lens-bridge');
    if (!section || section.dataset.lensImageEnhancement === 'active') return false;
    const countrySlug = document.documentElement.dataset.country || new URLSearchParams(window.location.search).get('country') || '';
    const countryNameJa = document.querySelector('.country-ja')?.textContent?.trim() || '';
    if (!countrySlug || !countryNameJa) return false;
    window.initCountryLensBridge({ slug: countrySlug, nameJa: countryNameJa });
    return true;
  };

  const appHost = document.querySelector('#app');
  if (appHost) {
    const lensObserver = new MutationObserver(() => {
      if (enhanceMountedLensBridge()) lensObserver.disconnect();
    });
    lensObserver.observe(appHost, { childList: true, subtree: true });
    enhanceMountedLensBridge();
  }
})();

(() => {
  const params = new URLSearchParams(window.location.search);
  const slug = params.get('country') || document.documentElement.dataset.country || '';
  if (!slug) return;

  let themes = [];

  const render = () => {
    const section = document.querySelector('#country-theme-context');
    const list = document.querySelector('#country-theme-list');
    if (!section || !list) return false;

    // Generated Country HTML already contains taxonomy chips. Keep those visible
    // immediately so the theme row never depends on a second network request.
    if (!themes.length) {
      if (list.querySelector('.country-theme-chip')) {
        section.hidden = false;
        return true;
      }
      return false;
    }

    const matches = themes.filter((theme) => Array.isArray(theme.examples) && theme.examples.includes(slug));
    if (!matches.length) {
      // Preserve any server-rendered taxonomy chips rather than hiding a valid
      // row because a runtime taxonomy response is stale or temporarily empty.
      section.hidden = !list.querySelector('.country-theme-chip');
      return true;
    }

    list.replaceChildren(...matches.map((theme) => {
      const span = document.createElement('span');
      span.className = 'country-theme-chip';
      span.textContent = theme.label;
      if (theme.definition) span.title = theme.definition;
      return span;
    }));
    section.hidden = false;
    return true;
  };

  const host = document.querySelector('#app');
  const observer = host
    ? new MutationObserver(() => {
        if (render() && themes.length) observer.disconnect();
      })
    : null;

  if (observer && host) observer.observe(host, { childList: true, subtree: true });

  // First try the generated chips as soon as the Country template is mounted.
  render();

  const taxonomyUrl = new URL('data/theme-taxonomy.json', document.baseURI);
  taxonomyUrl.searchParams.set('v', '20260911-theme-context-v3');

  fetch(taxonomyUrl.href, { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error('Theme taxonomy not found');
      return response.json();
    })
    .then((payload) => {
      themes = Array.isArray(payload.themes) ? payload.themes : [];
      if (render() && observer) observer.disconnect();
    })
    .catch(() => {
      // The build-time injected chips remain the authoritative fallback.
      render();
    });
})();
