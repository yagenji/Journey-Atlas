// 図鑑のページ送り: Country pages turn like the pages of an atlas.
// Order comes from atlas-order.js (chapters by region → subregion, A–Z inside a chapter). Adds (1) a 「前のページ / 次のページ」 spread with a folio (e.g. 12 / 200) above the
// site footer, (2) slim edge tabs on wide screens and (3) ← / → keys. The next page is prefetched.
// Detail regions (e.g. ザンジバル) are appendix pages of their parent Country and keep the
// 200-page folio of the parent; see the region branch below.
(()=>{
  const regionPath=location.pathname.match(/\/countries\/([a-z0-9-]+)\/([a-z0-9-]+)\/?$/);
  const slug=regionPath?regionPath[2]:(document.documentElement.dataset.country||new URLSearchParams(location.search).get('country'));
  if(!slug||!/^[a-z0-9-]+$/.test(slug))return;
  if(!window.JourneyAtlasOrder)return;
  const json=(url)=>fetch(url).then((response)=>{if(!response.ok)throw new Error(url);return response.json();});
  // Every detail region with its parent: regionHeroes (data/regions) plus the registry's
  // own detail pages (Hong Kong, Macau under China).
  const loadDetails=()=>Promise.all([json('data/top-scene-index.json'),json('data/atlas-destinations.json')]).then(([index,registry])=>{
    const own=new Set(registry.detailRegionSlugs||['hong-kong','macau']);
    return [
      ...(index.regionHeroes||[]).filter((item)=>item.parentSlug&&item.href),
      ...(registry.destinations||[]).filter((item)=>own.has(item.slug)&&item.atlasPublished&&item.href).map((item)=>({...item,parentSlug:'china'}))
    ];
  });
  window.JourneyAtlasOrder.load().then(({pages})=>{
    const at=pages.findIndex((page)=>page.slug===slug);
    if(at>=0){
      if(pages.length<2)return;
      turn(pages[at],pages[(at-1+pages.length)%pages.length],pages[(at+1)%pages.length],`${at+1} / ${pages.length}`);
      return;
    }
    return loadDetails().then((details)=>{
      const here=details.find((item)=>item.slug===slug);
      const parentAt=here?pages.findIndex((page)=>page.slug===here.parentSlug):-1;
      if(parentAt<0)return;
      const parent=pages[parentAt];
      const afterParent=pages[(parentAt+1)%pages.length];
      // Region pages already carry their own 「〇〇に戻る / 次の地域」 cards, following the
      // editorially ordered nextRegion loop. Turn the same way from the edge tabs and ← / →
      // keys, without a second spread; a Region with no next Region turns to the next Country.
      const ownNav=document.querySelector('.region-return');
      if(ownNav){
        const nextHref=ownNav.querySelector('a.region-return__link--next')?.getAttribute('href')||'';
        const nextRegion=details.find((item)=>nextHref&&item.href.replace(/\/?$/,'/')===nextHref.replace(/\/?$/,'/'));
        const prev={...parent,kicker:'国のページへ'};
        const next=nextRegion?{...nextRegion,kicker:'次の地域'}:afterParent;
        renderTabs(prev,next);
        bindKeys(prev,next);
        return;
      }
      // Hong Kong and Macau use the Country template: parent → its regions (A–Z) → next Country.
      const siblings=details.filter((item)=>item.parentSlug===parent.slug)
        .sort((a,b)=>a.nameEn.localeCompare(b.nameEn,'en',{sensitivity:'base'}))
        .map((item)=>({...item,chapter:{...parent.chapter,label:`${parent.nameJa}の地域`,region:`${parent.nameJa}の地域`},folio:parent.folio}));
      const i=siblings.findIndex((item)=>item.slug===slug);
      const prev=i===0?{...parent,kicker:'国のページへ'}:{...siblings[i-1],kicker:'前の地域'};
      const next=i<siblings.length-1?{...siblings[i+1],kicker:'次の地域'}:afterParent;
      turn(siblings[i],prev,next,`${parent.folio} / ${pages.length}`);
    });
  }).catch((error)=>console.warn('[JOURNEY ATLAS] Atlas pager unavailable.',error));

  function turn(here,prev,next,folio){
    renderSpread(here,prev,next,folio);
    renderTabs(prev,next);
    bindKeys(prev,next);
    const link=document.createElement('link');
    link.rel='prefetch';link.href=next.href;
    document.head.append(link);
  }
  function el(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;}
  function card(page,dir,here){
    const a=el('a',`atlas-pager__card atlas-pager__card--${dir}`);
    a.href=page.href;
    a.rel=dir==='next'?'next':'prev';
    const newChapter=page.chapter!==here.chapter;
    // The atlas wraps around: from the last page back to the first, and the reverse.
    const wraps=dir==='next'?page.folio<here.folio:page.folio>here.folio;
    const kicker=page.kicker||(wraps
      ?(dir==='next'?'はじめのページへ':'最後のページへ')
      :dir==='next'
        ?(newChapter?`次の章　${page.chapter.label}`:'次のページ')
        :(newChapter?`前の章　${page.chapter.label}`:'前のページ'));
    a.setAttribute('aria-label',`${kicker}：${page.nameJa}`);
    const art=el('span','atlas-pager__art');
    if(page.image){
      const img=el('img');
      img.src=page.image;img.alt='';img.loading='lazy';img.decoding='async';
      art.append(img);
    }
    const body=el('span','atlas-pager__body');
    body.append(
      el('span','atlas-pager__kicker',`${dir==='prev'?'‹ ':''}${kicker}${dir==='next'?' ›':''}`),
      el('strong','atlas-pager__name',page.nameEn),
      el('span','atlas-pager__ja',`${page.flag||''} ${page.nameJa}`.trim())
    );
    a.append(art,body);
    return a;
  }
  function renderSpread(here,prev,next,folio){
    const section=el('nav','atlas-pager page-shell');
    section.setAttribute('aria-label','図鑑のページ送り');
    const head=el('div','atlas-pager__head');
    head.append(
      el('span','atlas-pager__chapter',here.chapter.label===here.chapter.region?here.chapter.region:`${here.chapter.region}　/　${here.chapter.label}`),
      el('span','atlas-pager__folio',folio)
    );
    const row=el('div','atlas-pager__row');
    row.append(card(prev,'prev',here),card(next,'next',here));
    section.append(head,row);
    const footer=document.querySelector('.atlas-footer');
    if(footer)footer.before(section);else document.body.append(section);
  }
  function renderTabs(prev,next){
    [['prev',prev,'‹'],['next',next,'›']].forEach(([dir,page,arrow])=>{
      const a=el('a',`atlas-pager-tab atlas-pager-tab--${dir}`);
      a.href=page.href;
      a.setAttribute('aria-label',`${page.kicker||(dir==='next'?'次のページ':'前のページ')}：${page.nameJa}`);
      a.append(el('span','atlas-pager-tab__arrow',arrow),el('span','atlas-pager-tab__name',page.nameEn));
      document.body.append(a);
    });
  }
  function bindKeys(prev,next){
    document.addEventListener('keydown',(event)=>{
      if(event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
      if(event.key!=='ArrowLeft'&&event.key!=='ArrowRight')return;
      const target=event.target;
      if(target.closest?.('input,textarea,select,[contenteditable="true"],.map-art,[role="application"]'))return;
      location.href=(event.key==='ArrowRight'?next:prev).href;
    });
  }
})();
