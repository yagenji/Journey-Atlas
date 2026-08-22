(() => {
  const root = document.querySelector('.map-explorer');
  if (!root) return;

  const $ = (s) => root.querySelector(s);
  const tabs = [...root.querySelectorAll('[data-map-tab]')];
  const tabBar = $('.map-region-tabs');
  const mapWrap = $('.atlas-map-wrap');
  const kicker = $('#map-region-kicker');
  const title = $('#map-region-title');
  const copy = $('#map-region-copy');
  const count = $('#map-region-count');
  const preview = $('#map-region-list');
  const status = $('#map-country-status');
  const headingCopy = $('.map-heading p');
  const NS = 'http://www.w3.org/2000/svg';

  const WORLD = [0, -18, 2000, 1055];
  const REGION_VIEW = {
    world: WORLD, asia: [1010,70,930,650], europe: [790,95,570,405], africa: [790,300,610,650],
    'north-america': [0,55,925,665], 'south-america': [365,430,540,590], oceania: [1335,440,665,555], antarctica: [250,805,1500,205]
  };
  const SUB_VIEW = {
    'northern-europe':[835,105,390,285], 'western-europe':[915,185,255,205], 'southern-europe':[845,235,410,245], 'eastern-europe':[1010,175,400,285],
    'central-america':[250,360,300,250], caribbean:[430,370,275,215], 'australia-new-zealand':[1535,555,440,345], melanesia:[1570,455,390,305],
    micronesia:[1660,385,360,245], polynesia:[1900,455,330,255]
  };
  const COLORS = {
    asia:['#9eb79c','#c6cfaa'], europe:['#ccb078','#dfcda6'], africa:['#c78f69','#dfb48d'], 'north-america':['#9fbec5','#c4d4d1'],
    'south-america':['#9eb47c','#c8d1a3'], oceania:['#78aaa8','#aad0c7'], antarctica:['#d7e7e9','#f3f6f1']
  };
  const FALLBACK = {
    FM:[1878,463], KI:[1962,494], MH:[1950,461], NR:[1928,503], PW:[1748,459], CK:[112,618], NU:[57,606], WS:[44,578], TO:[28,619], TV:[1991,548],
    MT:[1078,344], VA:[1047,313], SM:[1055,309], MC:[1019,291], LI:[1036,275]
  };
  const POLY_WRAP = {TV:[1991,548],TO:[2028,619],WS:[2044,578],NU:[2057,606],CK:[2112,618]};
  const AQ_D = 'M367 901c187-45 364-58 544-40 169 18 316 5 471-21 147-24 280-16 369 21l-56 66c-247 34-460 37-705 21-224-16-402 0-571 18z';

  let regions=[], destinations=[], destByIso=new Map(), regionByIso=new Map(), subByIso=new Map(), subById=new Map();
  let primary=new Map(), interactive=new Map(), nav=new Map(), wrapped=new Map();
  let svgMap=null, tooltip=null, ring=null, subBar=null, activeRegion='world', activeSub=null, selected=null, frame=null;

  const S = (tag, attrs={}) => {
    const n=document.createElementNS(NS,tag);
    Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v)));
    return n;
  };
  const region = (id) => regions.find(r=>r.id===id);
  const countries = (codes=[]) => {
    const set=new Set(codes);
    return destinations.filter(c=>set.has(c.iso2)).sort((a,b)=>a.nameJa.localeCompare(b.nameJa,'ja'));
  };

  function buildLookup(){
    regions.forEach(r=>{
      (r.iso2||[]).forEach(i=>regionByIso.set(i,r.id));
      (r.subregions||[]).forEach(s=>{
        subById.set(s.id,{...s,regionId:r.id});
        (s.iso2||[]).forEach(i=>subByIso.set(i,s.id));
      });
    });
  }

  function ensureSubBar(){
    if(subBar||!tabBar)return;
    subBar=document.createElement('div');
    subBar.className='map-subregion-tabs';
    subBar.setAttribute('aria-label','小地域まで拡大');
    tabBar.insertAdjacentElement('afterend',subBar);
  }
  function renderSubTabs(r){
    ensureSubBar();
    const items=r?.subregions||[];
    if(!items.length){subBar.hidden=true;subBar.replaceChildren();return;}
    subBar.hidden=false;
    subBar.innerHTML='<span class="map-subregion-tabs__guide">さらに拡大</span>'+items.map(s=>`<button type="button" data-map-subregion="${s.id}" class="${activeSub===s.id?'is-active':''}" aria-pressed="${activeSub===s.id}">${s.label}</button>`).join('');
    subBar.querySelectorAll('[data-map-subregion]').forEach(b=>b.addEventListener('click',()=>setSub(b.dataset.mapSubregion)));
  }

  function prompt(text){
    nav=new Map();
    preview.className='map-country-preview';
    preview.innerHTML=`<div class="map-country-preview__empty"><span class="map-country-preview__marker">＋</span><div><strong>地域を選択</strong><p>${text}</p></div></div>`;
  }
  function countryNav(codes, picked=null){
    nav=new Map();
    const items=countries(codes);
    const summary=picked ? `<div class="map-country-nav__selected"><span class="map-country-nav__selected-flag">${picked.flag}</span><div class="map-country-nav__selected-names"><strong>${picked.nameJa}</strong><span>${picked.nameEn}</span></div>${picked.atlasPublished&&picked.href?`<a class="map-country-nav__selected-link" href="${picked.href}">見る ›</a>`:'<span class="map-country-nav__selected-waiting">COMING SOON</span>'}</div>` : '';
    preview.className='map-country-nav';
    preview.innerHTML=`<div class="map-country-nav__wrap">${summary}<div class="map-country-nav__guide"><strong>国・地域</strong><span>国名と地図が連動します</span></div><div class="map-country-nav__list">${items.map(c=>`<button type="button" class="map-country-nav__item ${picked?.iso2===c.iso2?'is-selected':''}" data-country-nav="${c.iso2}" aria-pressed="${picked?.iso2===c.iso2}"><span class="map-country-nav__flag">${c.flag}</span><span class="map-country-nav__names"><strong>${c.nameJa}</strong><small>${c.nameEn}</small></span></button>`).join('')}</div></div>`;
    preview.querySelectorAll('[data-country-nav]').forEach(b=>{
      nav.set(b.dataset.countryNav,b);
      b.addEventListener('pointerenter',()=>hover(b.dataset.countryNav,true));
      b.addEventListener('pointerleave',()=>hover(b.dataset.countryNav,false));
      b.addEventListener('focus',()=>hover(b.dataset.countryNav,true));
      b.addEventListener('blur',()=>hover(b.dataset.countryNav,false));
      b.addEventListener('click',()=>selectIso(b.dataset.countryNav));
    });
  }

  function renderWorld(){
    kicker.textContent='WORLD'; title.textContent='世界'; copy.textContent='大地域を選ぶと地図が近づきます。小地域では、実際に国を選べる倍率まで拡大します。';
    count.textContent=`${destinations.length||199} DESTINATIONS`; status.textContent=''; prompt('上の大地域から、見たい場所を選んでください。'); renderSubTabs(null);
  }
  function renderRegion(r,picked=null){
    kicker.textContent=r.labelEn; title.textContent=r.label;
    copy.textContent=(r.subregions||[]).length?'小地域へさらに寄れます。右の国名に触れると、地図上の位置も反応します。':'右の国名と地図は連動しています。地図・国名のどちらからでも選べます。';
    count.textContent=`${countries(r.iso2).length} DESTINATIONS`; status.textContent=picked?`${picked.nameJa}を選択中`:''; countryNav(r.iso2,picked); renderSubTabs(r);
  }
  function renderSub(s,picked=null){
    const r=region(s.regionId); kicker.textContent=`${r?.labelEn||''} / ${s.labelEn}`; title.textContent=s.label;
    copy.textContent='国を選べる倍率まで拡大しています。右の国名に触れると、地図上の位置も反応します。';
    count.textContent=`${countries(s.iso2).length} DESTINATIONS`; status.textContent=picked?`${picked.nameJa}を選択中`:''; countryNav(s.iso2,picked); renderSubTabs(r);
  }

  function setTabs(id){tabs.forEach(b=>{const on=b.dataset.mapTab===id;b.classList.toggle('is-active',on);b.setAttribute('aria-pressed',String(on));});}
  function view(){return svgMap?svgMap.getAttribute('viewBox').trim().split(/\s+/).map(Number):WORLD;}
  function animate(target,d=420){
    if(!svgMap)return; if(frame)cancelAnimationFrame(frame); const from=view(), start=performance.now(), ease=t=>1-Math.pow(1-t,3);
    const tick=now=>{const p=Math.min(1,(now-start)/d),e=ease(p);svgMap.setAttribute('viewBox',from.map((v,i)=>v+(target[i]-v)*e).join(' '));if(p<1)frame=requestAnimationFrame(tick);else frame=null;};
    frame=requestAnimationFrame(tick);
  }
  const elems = iso => interactive.get(iso)||[];
  function clearSelected(){if(selected)elems(selected).forEach(e=>e.classList.remove('is-selected'));selected=null;}
  function markSelected(iso){clearSelected();selected=iso;elems(iso).forEach(e=>e.classList.add('is-selected'));}
  function focus(codes=null){
    const set=codes?new Set(codes):null;
    primary.forEach((e,iso)=>{e.classList.toggle('is-muted',!!(set&&!set.has(iso)));e.classList.toggle('is-in-focus',!!(set&&set.has(iso)));});
    interactive.forEach((arr,iso)=>arr.filter(e=>e.classList.contains('country-marker')).forEach(e=>{e.classList.toggle('is-muted',!!(set&&!set.has(iso)));e.classList.toggle('is-in-focus',!!(set&&set.has(iso)));}));
  }
  function target(iso){return activeSub==='polynesia'&&wrapped.has(iso)?wrapped.get(iso):primary.get(iso)||elems(iso).find(e=>e.classList.contains('country-marker'))||null;}
  function bounds(codes){
    const boxes=(codes||[]).map(target).filter(Boolean).map(e=>e.getBBox()).filter(b=>Number.isFinite(b.x)&&Number.isFinite(b.y)); if(!boxes.length)return null;
    const l=Math.min(...boxes.map(b=>b.x)),t=Math.min(...boxes.map(b=>b.y)),r=Math.max(...boxes.map(b=>b.x+b.width)),bt=Math.max(...boxes.map(b=>b.y+b.height));
    let w=r-l,h=bt-t; const px=Math.max(w*.11,16),py=Math.max(h*.14,14);w=Math.max(w+px*2,110);h=Math.max(h+py*2,88);return[(l+r)/2-w/2,(t+bt)/2-h/2,w,h];
  }
  function setRegion(id,{motion=true}={}){
    activeRegion=id;activeSub=null;root.dataset.activeRegion=id;delete root.dataset.activeSubregion;clearSelected();hideRing();setTabs(id);
    const v=REGION_VIEW[id]||WORLD;if(motion)animate(v);else if(svgMap)svgMap.setAttribute('viewBox',v.join(' '));
    if(id==='world'){focus();renderWorld();return;} const r=region(id);if(!r)return;focus(r.iso2);renderRegion(r);
  }
  function setSub(id){
    const s=subById.get(id);if(!s)return;activeRegion=s.regionId;activeSub=id;root.dataset.activeRegion=activeRegion;root.dataset.activeSubregion=id;clearSelected();hideRing();setTabs(activeRegion);focus(s.iso2);renderSub(s);
    const v=SUB_VIEW[id]||bounds(s.iso2);if(v)animate(v,430);
  }
  function zoomCountry(e,c){
    if(!svgMap||!e)return;if(c.iso2==='AQ'){animate(REGION_VIEW.antarctica,390);return;}const b=e.getBBox(),w=Math.max(b.width*2.5,68),h=Math.max(b.height*2.5,54);animate([b.x+b.width/2-w/2,b.y+b.height/2-h/2,w,h],360);
  }
  function selectIso(iso){const c=destByIso.get(iso),e=target(iso);if(c&&e)selectCountry(e,c);}
  function selectCountry(e,c){
    const rid=regionByIso.get(c.iso2)||'world',sid=subByIso.get(c.iso2)||null;activeRegion=rid;activeSub=sid;root.dataset.activeRegion=rid;if(sid)root.dataset.activeSubregion=sid;else delete root.dataset.activeSubregion;
    setTabs(rid);const r=region(rid);renderSubTabs(r);focus(sid?subById.get(sid)?.iso2:r?.iso2);markSelected(c.iso2);hideRing();if(sid)renderSub(subById.get(sid),c);else renderRegion(r,c);zoomCountry(e,c);
  }

  function posTip(ev){if(!tooltip||!mapWrap)return;const r=mapWrap.getBoundingClientRect();tooltip.style.transform=`translate(${Math.min(r.width-142,Math.max(12,ev.clientX-r.left+12))}px, ${Math.min(r.height-54,Math.max(12,ev.clientY-r.top+12))}px)`;}
  function showRing(iso){if(!ring)return;const e=target(iso);if(!e)return hideRing();const b=e.getBBox(),v=view(),rr=Math.max(5,Math.min(18,v[2]*.018));ring.setAttribute('cx',b.x+b.width/2);ring.setAttribute('cy',b.y+b.height/2);ring.setAttribute('r',rr);ring.hidden=false;}
  function hideRing(){if(ring)ring.hidden=true;}
  function hover(iso,on){elems(iso).forEach(e=>e.classList.toggle('is-hovered',on));nav.get(iso)?.classList.toggle('is-hovered',on);if(on)showRing(iso);else hideRing();}

  function gradient(defs,id,colors){const g=S('linearGradient',{id,x1:'0%',y1:'0%',x2:'100%',y2:'100%'});g.append(S('stop',{offset:'0%','stop-color':colors[0]}),S('stop',{offset:'100%','stop-color':colors[1]}));defs.append(g);}
  function addInteractive(iso,e){if(!interactive.has(iso))interactive.set(iso,[]);interactive.get(iso).push(e);}
  function bind(e,c,tip=true){
    addInteractive(c.iso2,e);e.dataset.iso=c.iso2;e.setAttribute('tabindex','0');e.setAttribute('role','button');e.setAttribute('aria-label',`${c.nameJa}を選ぶ`);
    e.addEventListener('pointerenter',ev=>{hover(c.iso2,true);if(tip&&tooltip){tooltip.innerHTML=`<strong>${c.nameJa}</strong><span>${c.nameEn}</span>`;tooltip.hidden=false;posTip(ev);}});
    e.addEventListener('pointermove',ev=>{if(tip)posTip(ev);});e.addEventListener('pointerleave',()=>{hover(c.iso2,false);if(tip&&tooltip)tooltip.hidden=true;});
    e.addEventListener('focus',()=>hover(c.iso2,true));e.addEventListener('blur',()=>hover(c.iso2,false));e.addEventListener('click',()=>selectCountry(e,c));
    e.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();selectCountry(e,c);}});
  }
  function marker(c,xy,layer,cls=''){
    const rid=regionByIso.get(c.iso2)||'world',m=S('circle',{cx:xy[0],cy:xy[1],r:5.2});m.classList.add('country-marker','is-destination');if(cls)m.classList.add(cls);m.dataset.region=rid;m.style.fill=`url(#land-${rid})`;bind(m,c);layer.append(m);return m;
  }
  function tinyHits(layer){
    primary.forEach((p,iso)=>{if(!p.classList.contains('country-shape'))return;const c=destByIso.get(iso),b=p.getBBox();if(!c||(b.width>=8&&b.height>=8))return;const h=S('circle',{cx:b.x+b.width/2,cy:b.y+b.height/2,r:Math.max(8,Math.min(12,9+(5-Math.min(b.width,b.height))*.4))});h.classList.add('country-hit-target');bind(h,c);layer.append(h);});
  }

  function buildMap(shapes){
    primary=new Map();interactive=new Map();wrapped=new Map();mapWrap.classList.add('country-map-wrap');
    const map=S('svg',{class:'atlas-country-map',viewBox:WORLD.join(' '),role:'img','aria-label':'世界から地域へ拡大し、地図と国名を連動して選べるイラスト地図',preserveAspectRatio:'xMidYMid meet'}),defs=S('defs');
    const ocean=S('linearGradient',{id:'atlas-ocean',x1:'0%',y1:'0%',x2:'0%',y2:'100%'});ocean.append(S('stop',{offset:'0%','stop-color':'#e8f4f2'}),S('stop',{offset:'58%','stop-color':'#eef6f1'}),S('stop',{offset:'100%','stop-color':'#f4f0e4'}));defs.append(ocean);Object.entries(COLORS).forEach(([id,c])=>gradient(defs,`land-${id}`,c));
    const grid=S('pattern',{id:'atlas-grid',width:125,height:125,patternUnits:'userSpaceOnUse'});grid.append(S('path',{d:'M 125 0 L 0 0 0 125',fill:'none',stroke:'#6f9295','stroke-opacity':'.11','stroke-width':1}));defs.append(grid);
    const paper=S('filter',{id:'atlas-paper',x:'-5%',y:'-5%',width:'110%',height:'110%'});paper.append(S('feTurbulence',{type:'fractalNoise',baseFrequency:'.018',numOctaves:3,seed:9,result:'noise'}),S('feColorMatrix',{in:'noise',type:'matrix',values:'1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 .10 0',result:'texture'}),S('feBlend',{in:'SourceGraphic',in2:'texture',mode:'multiply'}));defs.append(paper);map.append(defs);
    map.append(S('rect',{class:'country-map-ocean',x:-80,y:-30,width:2400,height:1090,rx:28,fill:'url(#atlas-ocean)'}),S('ellipse',{class:'country-map-wash country-map-wash--one',cx:360,cy:310,rx:360,ry:205}),S('ellipse',{class:'country-map-wash country-map-wash--two',cx:1510,cy:310,rx:420,ry:225}),S('ellipse',{class:'country-map-wash country-map-wash--three',cx:1130,cy:770,rx:360,ry:180}),S('rect',{class:'country-map-grid',x:-80,y:-30,width:2400,height:1090,fill:'url(#atlas-grid)'}),S('rect',{class:'country-map-paper',x:-80,y:-30,width:2400,height:1090,filter:'url(#atlas-paper)'}));
    const ice=S('g',{class:'country-map-ice-layer','aria-hidden':'true'}),land=S('g',{class:'country-map-layer'}),marks=S('g',{class:'country-map-marker-layer'}),hits=S('g',{class:'country-map-hit-layer'}),over=S('g',{class:'country-map-overlay-layer'});
    shapes.forEach(({id,shape})=>{const iso=String(id||'').toUpperCase(),c=destByIso.get(iso);if(iso==='AQ')ice.append(S('path',{d:shape,class:'antarctica-glow'}));const p=S('path',{d:shape});p.dataset.iso=iso;if(!c){p.classList.add('country-shape','is-outside-atlas');land.append(p);return;}const rid=regionByIso.get(iso)||'world',tone=Math.abs(iso.charCodeAt(0)+iso.charCodeAt(1))%4;p.classList.add('country-shape','is-destination',`tone-${tone}`);p.dataset.region=rid;p.style.fill=`url(#land-${rid})`;const t=S('title');t.textContent=`${c.nameJa} / ${c.nameEn}`;p.append(t);bind(p,c);primary.set(iso,p);land.append(p);});
    const aq=destByIso.get('AQ');if(aq&&!primary.has('AQ')){ice.append(S('path',{d:AQ_D,class:'antarctica-glow'}));const p=S('path',{d:AQ_D});p.classList.add('country-shape','is-destination','tone-2','country-shape--fallback-antarctica');p.dataset.region='antarctica';p.style.fill='url(#land-antarctica)';bind(p,aq);land.append(p);primary.set('AQ',p);}
    destinations.forEach(c=>{if(primary.has(c.iso2)||!FALLBACK[c.iso2])return;const m=marker(c,FALLBACK[c.iso2],marks,'country-marker--fallback');primary.set(c.iso2,m);});
    Object.entries(POLY_WRAP).forEach(([iso,xy])=>{const c=destByIso.get(iso);if(!c)return;const m=marker(c,xy,marks,'country-marker--wrapped');wrapped.set(iso,m);});
    map.append(ice,land,marks,hits,over);mapWrap.replaceChildren(map);svgMap=map;tinyHits(hits);ring=S('circle',{class:'country-focus-ring',cx:0,cy:0,r:8});ring.hidden=true;over.append(ring);
    tooltip=document.createElement('div');tooltip.className='map-tooltip';tooltip.hidden=true;const hint=document.createElement('p');hint.className='map-hint';hint.textContent='地図と国名は連動しています';mapWrap.append(tooltip,hint);root.classList.add('has-country-map');
    const unresolved=destinations.filter(c=>!primary.has(c.iso2));if(unresolved.length)console.warn('[JOURNEY ATLAS map] unresolved map locations:',unresolved.map(c=>c.iso2));
  }

  tabs.forEach(b=>b.addEventListener('click',()=>setRegion(b.dataset.mapTab)));
  if(headingCopy)headingCopy.textContent='世界から地域へ寄りながら、地図と国名を連動して次の旅先を見つけよう。';
  Promise.all([
    import('https://cdn.jsdelivr.net/npm/world-map-country-shapes@1.0.0/index.js').then(m=>m.default||[]),
    fetch('data/region-taxonomy.json?v=20260822-2318').then(r=>{if(!r.ok)throw new Error('Region taxonomy not found');return r.json();}),
    fetch('data/atlas-destinations.json?v=20260822-2252').then(r=>{if(!r.ok)throw new Error('Destination registry not found');return r.json();})
  ]).then(([shapes,regionData,destinationData])=>{
    regions=regionData.regions||[];destinations=destinationData.destinations||[];destByIso=new Map(destinations.map(c=>[c.iso2,c]));buildLookup();buildMap(shapes);setRegion('world',{motion:false});
  }).catch(err=>{console.error('[JOURNEY ATLAS map]',err);copy.textContent='地図データを読み込めませんでした。';count.textContent='';status.textContent='再読み込みしてください。';});
})();
