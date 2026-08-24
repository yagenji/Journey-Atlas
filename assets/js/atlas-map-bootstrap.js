(() => {
  const configs = window.JOURNEY_ATLAS_MAP_CONFIGS || {};
  const version = '20260824-2115';
  const nativeFetch = window.fetch.bind(window);

  window.fetch = async (input, init = {}) => {
    const url = typeof input === 'string' ? input : input?.url || '';
    const response = await nativeFetch(input, init);

    const match = url.match(/data\/countries\/([a-z0-9-]+)\.json/i);
    if (!match || !response.ok) return response;

    const slug = match[1].toLowerCase();
    const config = configs[slug];
    if (!config) return response;

    try {
      const data = await response.clone().json();
      data.map = {
        ...(data.map || {}),
        svg: `${config.source}?v=${version}`,
        bounds: { ...config.bounds },
        markerOffsets: config.markerOffsets ? { ...config.markerOffsets } : {}
      };

      const headers = new Headers(response.headers);
      headers.set('content-type', 'application/json; charset=utf-8');
      return new Response(JSON.stringify(data), {
        status: response.status,
        statusText: response.statusText,
        headers
      });
    } catch (error) {
      console.error('Atlas map bootstrap failed', error);
      return response;
    }
  };
})();
