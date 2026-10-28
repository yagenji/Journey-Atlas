// 図鑑のページ送り: Country pages turn like the pages of an atlas.
// Order = chapters (regions → subregions, as in data/region-taxonomy.json), A–Z by English name
// inside each chapter. Adds (1) a 「前の国 / 次の国」 spread with a folio (e.g. 12 / 202) above the
// site footer, (2) slim edge tabs on wide screens and (3) ← / → keys. The next page is prefetched.
(()=>{
  const slug=document.documentElement.dataset.country||new URLSearchParams(location.search).get('country');
  if(!slug||!/^[a-z0-9-]+$/.test(slug))return;
  const json=(url)=>fetch(url).then((response)=>{if(!response.ok)throw new Error(url);return response.json();});
  Promise.all([json('data/region-taxonomy.json'),json('data/atlas-destinations.json')]).then(([taxonomy,registry])=>{
    const byIso=new Map((registry.destinations||[]).filter((item)=>item.atlasPublished&&item.href).map((item)=>[item.iso2,item]));
    const used=new Set();
    const pages=[];
    const chapters=[];
    (taxonomy.regions||[]).forEach((region)=>{
      const groups=region.subregions?.length?region.subregions:[{label:region.label,iso2:region.iso2}];
      groups.forEach((group)=>{
        const items=(group.iso2||[]).map((iso)=>byIso.get(iso)).filter((item)=>item&&!used.has(item.slug))
          .sort((a,b)=>a.nameEn.localeCompare(b.nameEn,'en',{sensitivity:'base'}));
        if(!items.length)return;
        const chapter={label:group.label===region.label?region.label:group.label,region:region.label,size:items.length};
        chapters.push(chapter);
        items.forEach((item,index)=>{used.add(item.slug);pages.push({...item,chapter,chapterIndex:index+1,folio:pages.length+1});});
      });
    });
    const at=pages.findIndex((page)=>page.slug===slug);
    if(at<0||pages.length<2)return;
    const here=pages[at];
    const prev=pages[(at-1+pages.length)%pages.length];
    const next=pages[(at+1)%pages.length];
    renderSpread(here,prev,next,at,pages.length);
    renderTabs(prev,next);
    bindKeys(prev,next);
    const link=document.createElement('link');
    link.rel='prefetch';link.href=next.href;
    document.head.append(link);
  }).catch((error)=>console.warn('[JOURNEY ATLAS] Atlas pager unavailable.',error));

  function el(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;}
  function card(page,dir,here){
    const a=el('a',`atlas-pager__card atlas-pager__card--${dir}`);
    a.href=page.href;
    a.rel=dir==='next'?'next':'prev';
    const newChapter=page.chapter!==here.chapter;
    // The atlas wraps around: from the last page back to the first, and the reverse.
    const wraps=dir==='next'?page.folio<here.folio:page.folio>here.folio;
    const kicker=wraps
      ?(dir==='next'?'はじめのページへ':'最後のページへ')
      :dir==='next'
        ?(newChapter?`次の章　${page.chapter.label}`:'次の国')
        :(newChapter?`前の章　${page.chapter.label}`:'前の国');
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
  function renderSpread(here,prev,next,index,total){
    const section=el('nav','atlas-pager page-shell');
    section.setAttribute('aria-label','図鑑のページ送り');
    const head=el('div','atlas-pager__head');
    head.append(
      el('span','atlas-pager__chapter',here.chapter.label===here.chapter.region?here.chapter.region:`${here.chapter.region}　/　${here.chapter.label}`),
      el('span','atlas-pager__folio',`${index+1} / ${total}`)
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
      a.setAttribute('aria-label',`${dir==='next'?'次の国':'前の国'}：${page.nameJa}`);
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
