(() => {
  const root=document.querySelector('.map-explorer');
  if(!root) return;

  const tabs=[...root.querySelectorAll('[data-map-tab]')];
  const shapes=[...root.querySelectorAll('[data-map-shape]')];
  const kicker=root.querySelector('#map-region-kicker');
  const title=root.querySelector('#map-region-title');
  const copy=root.querySelector('#map-region-copy');
  const count=root.querySelector('#map-region-count');
  const list=root.querySelector('#map-region-list');
  const status=root.querySelector('#map-country-status');

  let regions=[];
  let destinations=[];
  let active='world';

  const byId=(id)=>regions.find((region)=>region.id===id);
  const countriesFor=(region)=>{
    if(!region) return [];
    const codes=new Set(region.iso2||[]);
    return destinations
      .filter((country)=>codes.has(country.iso2))
      .sort((a,b)=>a.nameEn.localeCompare(b.nameEn,'en'));
  };

  function makeRegionChoice(region){
    const button=document.createElement('button');
    button.type='button';
    button.className='map-region-choice';
    button.dataset.regionChoice=region.id;
    const total=countriesFor(region).length;
    button.innerHTML=`<b>${region.label}</b><small>${total}</small>`;
    button.addEventListener('click',()=>setRegion(region.id));
    return button;
  }

  function makeCountryChoice(country){
    if(country.atlasPublished&&country.href){
      const link=document.createElement('a');
      link.className='is-published';
      link.href=country.href;
      link.textContent=country.nameJa;
      link.title=country.nameEn;
      return link;
    }
    const button=document.createElement('button');
    button.type='button';
    button.textContent=country.nameJa;
    button.title=country.nameEn;
    button.addEventListener('click',()=>{
      if(status) status.textContent=`${country.nameJa}のJOURNEY ATLASは準備中です。`;
    });
    return button;
  }

  function renderWorld(){
    if(kicker) kicker.textContent='WORLD';
    if(title) title.textContent='世界';
    if(copy) copy.textContent='地図または地域名から、気になるエリアを選んでください。地域を選ぶと、その地域の国・地域が表示されます。';
    if(count) count.textContent=`${destinations.length||199} DESTINATIONS`;
    if(status) status.textContent='';
    if(list){
      list.replaceChildren(...regions.map(makeRegionChoice));
    }
  }

  function renderRegion(region){
    const countries=countriesFor(region);
    if(kicker) kicker.textContent=region.labelEn;
    if(title) title.textContent=region.label;
    if(copy) copy.textContent=region.description;
    if(count) count.textContent=`${countries.length} DESTINATIONS`;
    if(status) status.textContent='国名を選ぶと、公開済みページへ進むか準備状況を確認できます。';
    if(list){
      list.replaceChildren(...countries.map(makeCountryChoice));
    }
  }

  function setRegion(id){
    active=id;
    root.dataset.activeRegion=id;
    tabs.forEach((button)=>{
      const selected=button.dataset.mapTab===id;
      button.classList.toggle('is-active',selected);
      button.setAttribute('aria-pressed',String(selected));
    });
    shapes.forEach((shape)=>{
      const selected=shape.dataset.mapShape===id;
      shape.classList.toggle('is-active',selected);
      shape.setAttribute('aria-pressed',String(selected));
    });
    if(id==='world') renderWorld();
    else{
      const region=byId(id);
      if(region) renderRegion(region);
    }
  }

  tabs.forEach((button)=>button.addEventListener('click',()=>setRegion(button.dataset.mapTab)));
  shapes.forEach((shape)=>{
    shape.addEventListener('click',()=>setRegion(shape.dataset.mapShape));
    shape.addEventListener('keydown',(event)=>{
      if(event.key==='Enter'||event.key===' '){
        event.preventDefault();
        setRegion(shape.dataset.mapShape);
      }
    });
  });

  Promise.all([
    fetch('data/region-taxonomy.json?v=20260822-2150').then((response)=>{if(!response.ok)throw new Error('Region taxonomy not found');return response.json();}),
    fetch('data/atlas-destinations.json').then((response)=>{if(!response.ok)throw new Error('Destination registry not found');return response.json();})
  ]).then(([regionData,destinationData])=>{
    regions=regionData.regions||[];
    destinations=destinationData.destinations||[];
    setRegion(active);
  }).catch(()=>{
    if(copy) copy.textContent='地域データを読み込めませんでした。';
    if(count) count.textContent='';
  });
})();
