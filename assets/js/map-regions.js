(() => {
  const root=document.querySelector('.map-explorer');
  if(!root) return;

  const tabs=[...root.querySelectorAll('[data-map-tab]')];
  const mapWrap=root.querySelector('.atlas-map-wrap');
  const kicker=root.querySelector('#map-region-kicker');
  const title=root.querySelector('#map-region-title');
  const copy=root.querySelector('#map-region-copy');
  const count=root.querySelector('#map-region-count');
  const preview=root.querySelector('#map-region-list');
  const status=root.querySelector('#map-country-status');
  const headingCopy=root.querySelector('.map-heading p');

  const SVG_NS='http://www.w3.org/2000/svg';
  const WORLD_VIEW=[0,0,2000,1001];
  const REGION_VIEWS={
    world:WORLD_VIEW,
    asia:[1030,105,910,625],
    europe:[815,130,540,390],
    africa:[835,340,555,590],
    'north-america':[0,80,830,550],
    'latin-america':[320,400,590,590],
    oceania:[1430,505,565,475],
    antarctica:[120,820,1760,181]
  };

  let regions=[];
  let destinations=[];
  let destinationByIso=new Map();
  let regionByIso=new Map();
  let mapSvg=null;
  let tooltip=null;
  let selectedPath=null;
  let active='world';
  let animationFrame=null;

  const regionById=(id)=>regions.find((region)=>region.id===id);
  const countriesFor=(region)=>{
    if(!region) return [];
    const codes=new Set(region.iso2||[]);
    return destinations.filter((country)=>codes.has(country.iso2));
  };
  const makeSvg=(tag,attrs={})=>{
    const node=document.createElementNS(SVG_NS,tag);
    Object.entries(attrs).forEach(([key,value])=>node.setAttribute(key,String(value)));
    return node;
  };

  function buildRegionLookup(){
    regionByIso=new Map();
    regions.forEach((region)=>{
      (region.iso2||[]).forEach((iso)=>regionByIso.set(iso,region.id));
    });
  }

  function renderPrompt(region=null){
    if(!preview) return;
    preview.className='map-country-preview';
    const wrapper=document.createElement('div');
    wrapper.className='map-country-preview__empty';
    const eye=document.createElement('span');
    eye.className='map-country-preview__marker';
    eye.textContent='＋';
    const body=document.createElement('div');
    const main=document.createElement('strong');
    main.textContent='地図上の国を選択';
    const sub=document.createElement('p');
    sub.textContent=region
      ? `${region.label}を拡大しています。国の形を直接クリックしてください。`
      : '地域ボタンは地図を拡大するためのものです。国は地図上から直接選びます。';
    body.append(main,sub);
    wrapper.append(eye,body);
    preview.replaceChildren(wrapper);
  }

  function renderRegion(region){
    if(kicker) kicker.textContent=region.labelEn;
    if(title) title.textContent=region.label;
    if(copy) copy.textContent=region.description;
    if(count) count.textContent=`${countriesFor(region).length} DESTINATIONS`;
    if(status) status.textContent='';
    renderPrompt(region);
  }

  function renderWorld(){
    if(kicker) kicker.textContent='WORLD';
    if(title) title.textContent='世界';
    if(copy) copy.textContent='地域で拡大しながら、地図そのものから国を選べます。';
    if(count) count.textContent=`${destinations.length||199} DESTINATIONS`;
    if(status) status.textContent='';
    renderPrompt();
  }

  function renderCountry(country,regionId){
    const region=regionById(regionId);
    if(kicker) kicker.textContent=region?.labelEn||country.iso2;
    if(title) title.textContent=country.nameJa;
    if(copy) copy.textContent=country.nameEn;
    if(count) count.textContent=`${country.flag} ${country.iso2}`;
    if(status) status.textContent='地図上で別の国を選ぶと、この表示が切り替わります。';
    if(!preview) return;

    preview.className='map-country-preview';
    const card=document.createElement('div');
    card.className='map-country-card';

    const visual=document.createElement('div');
    visual.className='map-country-card__visual';
    if(country.image){
      visual.style.backgroundImage=`url("${country.image}")`;
      visual.classList.add('has-image');
    }
    const flag=document.createElement('span');
    flag.className='map-country-card__flag';
    flag.textContent=country.flag;
    visual.append(flag);

    const meta=document.createElement('div');
    meta.className='map-country-card__meta';
    const regionLabel=document.createElement('span');
    regionLabel.textContent=region?.label||'JOURNEY ATLAS';
    const name=document.createElement('strong');
    name.textContent=country.nameEn;
    const state=document.createElement('p');
    state.textContent=country.atlasPublished?'JOURNEY ATLAS 公開中':'この国のページは準備中です。';
    meta.append(regionLabel,name,state);

    if(country.atlasPublished&&country.href){
      const link=document.createElement('a');
      link.href=country.href;
      link.className='map-country-card__link';
      link.innerHTML='この国を見る <span>›</span>';
      meta.append(link);
    }else{
      const waiting=document.createElement('span');
      waiting.className='map-country-card__waiting';
      waiting.textContent='COMING SOON';
      meta.append(waiting);
    }

    card.append(visual,meta);
    preview.replaceChildren(card);
  }

  function setTabs(id){
    tabs.forEach((button)=>{
      const selected=button.dataset.mapTab===id;
      button.classList.toggle('is-active',selected);
      button.setAttribute('aria-pressed',String(selected));
    });
  }

  function currentViewBox(){
    if(!mapSvg) return WORLD_VIEW;
    return mapSvg.getAttribute('viewBox').trim().split(/\s+/).map(Number);
  }

  function animateViewBox(target,duration=420){
    if(!mapSvg) return;
    if(animationFrame) cancelAnimationFrame(animationFrame);
    const from=currentViewBox();
    const start=performance.now();
    const ease=(t)=>1-Math.pow(1-t,3);
    const tick=(now)=>{
      const progress=Math.min(1,(now-start)/duration);
      const e=ease(progress);
      const value=from.map((item,index)=>item+(target[index]-item)*e);
      mapSvg.setAttribute('viewBox',value.join(' '));
      if(progress<1) animationFrame=requestAnimationFrame(tick);
      else animationFrame=null;
    };
    animationFrame=requestAnimationFrame(tick);
  }

  function clearSelection(){
    if(selectedPath) selectedPath.classList.remove('is-selected');
    selectedPath=null;
  }

  function setRegion(id,{animate=true}={}){
    active=id;
    root.dataset.activeRegion=id;
    clearSelection();
    setTabs(id);
    const target=REGION_VIEWS[id]||WORLD_VIEW;
    if(animate) animateViewBox(target);
    else if(mapSvg) mapSvg.setAttribute('viewBox',target.join(' '));
    if(id==='world') renderWorld();
    else{
      const region=regionById(id);
      if(region) renderRegion(region);
    }
  }

  function zoomToCountry(path){
    if(!mapSvg||!path) return;
    const box=path.getBBox();
    const minWidth=120;
    const minHeight=90;
    const width=Math.max(box.width*2.1,minWidth);
    const height=Math.max(box.height*2.1,minHeight);
    const x=box.x+box.width/2-width/2;
    const y=box.y+box.height/2-height/2;
    animateViewBox([x,y,width,height],360);
  }

  function selectCountry(path,country){
    if(!path||!country) return;
    clearSelection();
    selectedPath=path;
    path.classList.add('is-selected');
    const regionId=regionByIso.get(country.iso2)||'world';
    active=regionId;
    root.dataset.activeRegion=regionId;
    setTabs(regionId);
    renderCountry(country,regionId);
    zoomToCountry(path);
  }

  function positionTooltip(event){
    if(!tooltip||!mapWrap) return;
    const rect=mapWrap.getBoundingClientRect();
    const x=Math.min(rect.width-130,Math.max(12,event.clientX-rect.left+12));
    const y=Math.min(rect.height-48,Math.max(12,event.clientY-rect.top+12));
    tooltip.style.transform=`translate(${x}px,${y}px)`;
  }

  function buildMap(countryShapes){
    if(!mapWrap) return;
    mapWrap.classList.add('country-map-wrap');
    const svg=makeSvg('svg',{
      class:'atlas-country-map',
      viewBox:WORLD_VIEW.join(' '),
      role:'img',
      'aria-label':'国を直接選べる世界地図',
      preserveAspectRatio:'xMidYMid meet'
    });

    const defs=makeSvg('defs');
    const pattern=makeSvg('pattern',{id:'atlas-grid',width:'125',height:'125',patternUnits:'userSpaceOnUse'});
    pattern.append(
      makeSvg('path',{d:'M 125 0 L 0 0 0 125',fill:'none',stroke:'#7c9aa3','stroke-opacity':'.14','stroke-width':'1'})
    );
    defs.append(pattern);
    svg.append(defs);

    svg.append(
      makeSvg('rect',{class:'country-map-ocean',x:'0',y:'0',width:'2000',height:'1001',rx:'28'}),
      makeSvg('rect',{class:'country-map-grid',x:'0',y:'0',width:'2000',height:'1001',fill:'url(#atlas-grid)'})
    );

    const countryLayer=makeSvg('g',{class:'country-map-layer'});
    countryShapes.forEach(({id,shape})=>{
      const iso=String(id||'').toUpperCase();
      const country=destinationByIso.get(iso);
      const path=makeSvg('path',{d:shape});
      path.dataset.iso=iso;
      if(!country){
        path.classList.add('country-shape','is-outside-atlas');
        countryLayer.append(path);
        return;
      }
      const regionId=regionByIso.get(iso)||'world';
      path.classList.add('country-shape','is-destination');
      path.dataset.region=regionId;
      path.setAttribute('tabindex','0');
      path.setAttribute('role','button');
      path.setAttribute('aria-label',`${country.nameJa}を選ぶ`);
      const nativeTitle=makeSvg('title');
      nativeTitle.textContent=`${country.nameJa} / ${country.nameEn}`;
      path.append(nativeTitle);
      path.addEventListener('pointerenter',(event)=>{
        if(tooltip){
          tooltip.innerHTML=`<strong>${country.nameJa}</strong><span>${country.nameEn}</span>`;
          tooltip.hidden=false;
          positionTooltip(event);
        }
      });
      path.addEventListener('pointermove',positionTooltip);
      path.addEventListener('pointerleave',()=>{if(tooltip)tooltip.hidden=true;});
      path.addEventListener('click',()=>selectCountry(path,country));
      path.addEventListener('keydown',(event)=>{
        if(event.key==='Enter'||event.key===' '){
          event.preventDefault();
          selectCountry(path,country);
        }
      });
      countryLayer.append(path);
    });
    svg.append(countryLayer);

    tooltip=document.createElement('div');
    tooltip.className='map-tooltip';
    tooltip.hidden=true;
    const hint=document.createElement('p');
    hint.className='map-hint';
    hint.textContent='地域で拡大 → 地図上の国を選択';
    mapWrap.replaceChildren(svg,tooltip,hint);
    mapSvg=svg;
    root.classList.add('has-country-map');
  }

  tabs.forEach((button)=>button.addEventListener('click',()=>setRegion(button.dataset.mapTab)));
  if(headingCopy) headingCopy.textContent='地域で拡大しながら、地図上の国を直接選択。国名一覧ではなく、場所から次の旅先を見つけよう。';

  Promise.all([
    import('https://cdn.jsdelivr.net/npm/world-map-country-shapes@1.0.0/index.js').then((module)=>module.default||[]),
    fetch('data/region-taxonomy.json?v=20260822-2218').then((response)=>{if(!response.ok)throw new Error('Region taxonomy not found');return response.json();}),
    fetch('data/atlas-destinations.json').then((response)=>{if(!response.ok)throw new Error('Destination registry not found');return response.json();})
  ]).then(([countryShapes,regionData,destinationData])=>{
    regions=regionData.regions||[];
    destinations=destinationData.destinations||[];
    destinationByIso=new Map(destinations.map((country)=>[country.iso2,country]));
    buildRegionLookup();
    buildMap(countryShapes);
    setRegion('world',{animate:false});
  }).catch(()=>{
    if(copy) copy.textContent='地図データを読み込めませんでした。';
    if(count) count.textContent='';
    if(status) status.textContent='再読み込みしてください。';
  });
})();
