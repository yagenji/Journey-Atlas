/* JOURNEY ATLAS — discover-first top-page review. Existing module IDs are preserved. */
(() => {
  'use strict';
  const host = document.querySelector('#ja-discover');
  const image = document.querySelector('#ja-discover-image');
  const countryLabel = document.querySelector('#ja-discover-country');
  const sceneName = document.querySelector('#ja-discover-scene');
  const sceneLink = document.querySelector('#ja-discover-link');
  const counter = document.querySelector('#ja-discover-count');
  const next = document.querySelector('#ja-discover-next');
  if (!host || !image || !countryLabel || !sceneName || !sceneLink || !next) return;

  // Keep the existing map, filters, scenery gallery and search handlers intact.
  const main = host.closest('main');
  const countries = document.querySelector('#countries');
  if (main && countries) {
    for (const [id, className] of [
      ['scenery', 'ja-discover-gallery'],
      ['map', 'ja-discover-map'],
      ['lens-world', ''],
      ['ja-find', '']
    ]) {
      const panel = document.getElementById(id);
      if (!panel) continue;
      if (className) panel.classList.add('shell', className);
      main.insertBefore(panel, countries);
    }
  }
  document.querySelector('#ja-discover-search')?.addEventListener('click', () => {
    window.setTimeout(() => document.querySelector('#country-search')?.focus({preventScroll: true}), 350);
  });

  // Verified approved Hero fallback for first paint/network interruption.
  const fallback = [
    ['iceland','ICELAND','アイスランド','セリャラントスフォス','assets/images/iceland/approved/hero-seljalandsfoss.webp'],
    ['namibia','NAMIBIA','ナミビア','デッドフレイ','assets/images/namibia/approved/hero-deadvlei.webp'],
    ['peru','PERU','ペルー','マチュ・ピチュ','assets/images/peru/approved/hero-machu-picchu.webp'],
    ['japan','JAPAN','日本','河口湖と富士山','assets/images/japan/approved/hero-fuji-lake-kawaguchi-oishi.webp'],
    ['morocco','MOROCCO','モロッコ','アイト・ベン・ハドゥ','assets/images/morocco/approved/hero.webp'],
    ['newzealand','NEW ZEALAND','ニュージーランド','ミルフォード・サウンド','assets/images/newzealand/approved/hero-milford-sound.webp'],
    ['italy','ITALY','イタリア','ヴェネツィア / カナル・グランデ','assets/images/italy/approved/hero-venice-grand-canal-salute.webp']
  ].map(([slug,nameEn,nameJa,name,src]) => ({
    slug, nameEn, nameJa, name, src, href:'countries/'+slug+'/#hero-caption'
  }));

  const shuffled = items => {
    const rows = [...items];
    for (let i=rows.length-1;i>0;i--) {
      const j=Math.floor(Math.random()*(i+1));
      [rows[i],rows[j]]=[rows[j],rows[i]];
    }
    return rows;
  };
  let collection=fallback;
  let queue=[];
  let current=null;
  let shown=0;
  let token=0;

  function buildQueue() {
    const groups=new Map();
    for (const row of collection) {
      if (!row.src || !row.name || !row.href) continue;
      if (!groups.has(row.slug)) groups.set(row.slug,[]);
      groups.get(row.slug).push(row);
    }
    // One scene per destination in each round: diversity without repetition.
    queue=shuffled([...groups.values()].map(rows=>rows[Math.floor(Math.random()*rows.length)]));
    if (queue.length>1 && queue[0].slug===current?.slug) {
      const index=queue.findIndex(row=>row.slug!==current.slug);
      if (index>0) [queue[0],queue[index]]=[queue[index],queue[0]];
    }
  }
  function show(row) {
    current=row;
    shown++;
    image.src=row.src;
    image.alt=row.name+'（'+row.nameJa+'）を描いた景観イメージ';
    countryLabel.textContent=row.nameEn+' / '+row.nameJa;
    sceneName.textContent=row.name;
    sceneLink.href=row.href;
    counter.textContent=String(shown).padStart(2,'0')+' / DISCOVER';
    host.classList.add('is-ready');
  }
  async function advance() {
    if (!queue.length) buildQueue();
    const row=queue.shift();
    if (!row) return;
    const request=++token;
    next.disabled=true;
    const preload=new Image();
    preload.decoding='async';
    preload.src=row.src;
    try {
      if (preload.decode) await preload.decode();
      else if (!preload.complete) await new Promise((resolve,reject)=>{
        preload.onload=resolve;preload.onerror=reject;
      });
      if (request!==token) return;
      show(row);
    } catch {
      if (request===token && queue.length) {
        next.disabled=false;
        return advance();
      }
      if (!current) {
        host.classList.add('has-error');
        host.querySelector('.ja-discover-placeholder').textContent='景色を表示できませんでした。';
      }
    } finally {
      if (request===token) next.disabled=false;
    }
  }
  next.addEventListener('click',advance);
  advance();

  // Only published destinations are included; use the canonical Scene index.
  Promise.all([
    fetch('data/top-scene-index.json?v=20261109-scene-view-1').then(response=>{
      if(!response.ok) throw Error('Scene index HTTP '+response.status);
      return response.json();
    }),
    window.JourneyAtlasRegistryPromise || fetch('data/atlas-destinations.json').then(response=>response.json()),
    window.JourneyAtlasRegionsPromise || Promise.resolve([])
  ]).then(([index,registry,regions])=>{
    const places=[...(registry.destinations||[]),...regions].filter(row=>row.atlasPublished&&row.href);
    const bySlug=new Map(places.map(row=>[row.slug,row]));
    const rows=[];
    for (const place of places) {
      const name=place.heroName||index.heroes?.[place.slug];
      if(!name||!place.image) continue;
      rows.push({slug:place.slug,nameEn:place.nameEn,nameJa:place.nameJa,name,
        src:place.image,href:place.href+'#hero-caption'});
    }
    for (const [slug,scenes] of Object.entries(index.countries||{})) {
      const place=bySlug.get(slug);
      if (!place) continue;
      for (const [id,name,,file] of scenes) {
        if(!name||!file) continue;
        const src=file.includes('/')?file:'assets/images/'+slug+'/approved/'+file;
        rows.push({slug,nameEn:place.nameEn,nameJa:place.nameJa,name,
          src,href:place.href+'#'+encodeURIComponent(id)});
      }
    }
    if (rows.length) {
      collection=rows;
      queue=[];
    }
  }).catch(error=>console.warn('[JOURNEY ATLAS] Discover index unavailable:',error));
})();