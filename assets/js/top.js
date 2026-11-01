const rail = document.querySelector('#country-rail');
const grid = document.querySelector('#country-grid');
const count = document.querySelector('#country-count');
const prev = document.querySelector('[data-country-scroll="prev"]');
const next = document.querySelector('[data-country-scroll="next"]');
const toggleAll = document.querySelector('#all-countries-toggle');
const allPanel = document.querySelector('#all-countries-panel');
const searchInput = document.querySelector('#country-search');
const allTitle = document.querySelector('#all-countries-title');
const themeResults = document.querySelector('#theme-results');
const themeResultsGrid = document.querySelector('#theme-results-grid');
const themeResultsTitle = document.querySelector('#theme-results-title');
const themeResultsMeta = document.querySelector('#theme-results-meta');
const themeResultsSearch = document.querySelector('#theme-country-search');
const themeResultsClear = document.querySelector('#theme-results-clear');
const themeResultsEmpty = document.querySelector('#theme-results-empty');
const themeRegionTabs = document.querySelector('#theme-region-tabs');
// Region filter for theme results (same regions and order as the map).
let themeRegions = [];
let themeRegionByIso = new Map();
let activeThemeRegion = 'all';
const themeRegionPromise=fetch('data/region-taxonomy.json')
  .then((response)=>{if(!response.ok)throw new Error('Region taxonomy not found');return response.json();})
  .then(({regions=[]})=>{
    themeRegions=regions.map(({id,label})=>({id,label}));
    regions.forEach((region)=>(region.iso2||[]).forEach((iso)=>themeRegionByIso.set(iso,region.id)));
    if(activeTheme)renderThemeResults();
  })
  .catch((error)=>console.warn('[JOURNEY ATLAS] Theme region filter unavailable.',error));
const empty = document.querySelector('#country-empty');
const wishButton = document.querySelector('#wish-link');
const toast = document.querySelector('#top-toast');
const dots = [...document.querySelectorAll('.rail-dots i')];
const heroCollage = document.querySelector('#hero-collage');
const heroVisual = document.querySelector('#hero-visual');
const heroButtons = [...document.querySelectorAll('[data-hero]')];
const heroStepButtons = [...document.querySelectorAll('[data-hero-step]')];
const alphabetHost = document.querySelector('#alphabet-buttons');
const alphabetButtons = () => [...document.querySelectorAll('[data-letter]')];
const themeArtElements = [...document.querySelectorAll('[data-theme-art]')];
const lensRail = document.querySelector('.lens-rail');
const lensPrevButton = document.querySelector('[data-lens-prev]');
const lensNextButton = document.querySelector('[data-lens-next]');
const lensCount = document.querySelector('[data-lens-count]');
const LENS_RSS_URL = 'https://journey.yagenji.com/rss.xml';
const LENS_LINK_PATTERN = /^https:\/\/journey\.yagenji\.com\/([a-z]+)(\d+)\/$/;
const ATLAS_TOTAL = 202;
const INDEX_TITLE = '索引　すべての国・地域（A–Z）';

function syncScrollHeader() {
  const header = document.querySelector('.top-header');
  if (!header) return;
  const threshold = header.offsetHeight;
  header.classList.toggle('is-scroll-sticky', window.scrollY > threshold);
}
window.addEventListener('scroll', syncScrollHeader, { passive: true });
window.addEventListener('resize', syncScrollHeader);
syncScrollHeader();

let destinations = [];
let activeTheme = null;
let activeThemeMonth = null;   // テーマ×季節: 1–12, or null for every month
let themeMeta = {};
let heroSources = [];
let heroIndex = 0;
let heroTimer;
let heroTransitionId=0;
let themeSets = {};

// Homepage-only regional montages built from existing approved Country images.
// First entry is the dominant center; the following four appear around it.
const heroFiles = [
  { id: 'asia', labelJa: 'アジア', labelEn: 'ASIA', description: '日本・富士山、インド・タージ・マハル、ベトナム・ハロン湾、ヨルダン・ペトラ', image: 'assets/images/top/regions/top-asia.webp?v=20261101-four-scenes-1' },
  { id: 'europe', labelJa: 'ヨーロッパ', labelEn: 'EUROPE', description: 'ギリシャ・サントリーニ、イタリア・ヴェネツィア、スイス・アルプス、フランス・パリ', image: 'assets/images/top/regions/top-europe.webp?v=20261101-four-scenes-1' },
  { id: 'africa', labelJa: 'アフリカ', labelEn: 'AFRICA', description: 'アフリカのサバンナ、ビクトリアの滝、ナミビアの砂丘、マダガスカルのバオバブ', image: 'assets/images/top/regions/top-africa.webp?v=20261101-four-scenes-1' },
  { id: 'north-america', labelJa: '北米', labelEn: 'NORTH AMERICA', description: 'アメリカ・グランドキャニオン、ニューヨーク、カナダ・ロッキー山脈、ナイアガラの滝', image: 'assets/images/top/regions/top-north-america.webp?v=20261101-four-scenes-1' },
  { id: 'south-america', labelJa: '南米', labelEn: 'SOUTH AMERICA', description: 'ペルー・マチュピチュ、イグアスの滝、ボリビア・ウユニ塩湖、ブラジル・リオデジャネイロ', image: 'assets/images/top/regions/top-south-america.webp?v=20261101-four-scenes-1' },
  { id: 'oceania', labelJa: 'オセアニア', labelEn: 'OCEANIA', description: 'オーストラリア・シドニー湾、ニュージーランド・フィヨルド、南太平洋の島々、ウルル', image: 'assets/images/top/regions/top-oceania.webp?v=20261101-four-scenes-1' },
  { id: 'antarctica', labelJa: '南極', labelEn: 'ANTARCTICA', description: '南極のペンギン、氷河、氷山、雪山', image: 'assets/images/top/regions/top-antarctica.webp?v=20261101-four-scenes-1' }
];

{
  const image='url("assets/images/top/theme-approved-sprite.webp")';
  themeArtElements.forEach((art,index)=>{
    art.style.backgroundImage=image;
    art.style.backgroundPosition=`${index*(100/7)}% 50%`;
  });
}

const themeTaxonomyPromise=fetch('data/theme-taxonomy.json')
  .then((response)=>{if(!response.ok) throw new Error('Theme taxonomy not found');return response.json();})
  .then(({themes=[]})=>{
    if(themes.length){
      themeSets=Object.fromEntries(themes.map((theme)=>[theme.id,theme.examples||[]]));
      themeMeta=Object.fromEntries(themes.map((theme)=>[theme.id,theme]));
      const buttons=[...document.querySelectorAll('.theme-icons button')];
      themes.forEach((theme,index)=>{
        const button=buttons[index];
        if(!button)return;
        button.dataset.theme=theme.id;
        const label=button.querySelector('b');
        if(label)label.textContent=theme.label;
        button.title=theme.definition;
        button.setAttribute('aria-pressed',String(activeTheme===theme.id));
      });
      syncThemeSelectionUI();
    }
    const entryCopy=document.querySelector('.explore-card--theme p');
    if(entryCopy)entryCopy.textContent='行きたい理由から、世界を選ぶ';
    const detailCopy=document.querySelector('.theme-panel .detail-heading p');
    if(detailCopy)detailCopy.textContent=`あなたが惹かれるのは、どんな旅？ ${ATLAS_TOTAL}の国・地域を、8つのテーマから見つけてみよう。`;
  })
  .catch(()=>{});

heroSources=heroFiles;
{
  const controls=document.querySelector('.hero-controls');
  if(controls){
    controls.replaceChildren(...heroSources.map((_,i)=>{
      const button=document.createElement('button');
      button.type='button';button.dataset.hero=String(i);button.setAttribute('aria-label',`${heroSources[i].labelJa}のビジュアル`);button.setAttribute('aria-pressed',String(i===0));
      if(i===0)button.classList.add('is-active');
      return button;
    }));
    heroButtons.splice(0,heroButtons.length,...controls.querySelectorAll('[data-hero]'));
  }
}
setHero(0,false);
if(destinations.length)renderRail(destinations);
startHeroRotation();

function setHero(index,animate=true){
  if(!heroCollage || heroSources.length===0) return;
  const nextIndex=(index+heroSources.length)%heroSources.length;
  const region=heroSources[nextIndex];
  const token=++heroTransitionId;
  const render=()=>{
    if(token!==heroTransitionId) return;
    const picture=heroCollage.querySelector('.hero-collage__image');
    const label=heroCollage.querySelector('.hero-collage__region');
    if(picture && picture.getAttribute('src')!==region.image) picture.src=region.image;
    if(label) label.textContent=region.labelEn;
    heroIndex=nextIndex;
    heroCollage.dataset.region=region.id;
    heroCollage.setAttribute('aria-label',region.labelJa+'の旅の風景をめぐる水彩コラージュ：'+region.description);
    heroButtons.forEach((button,i)=>{
      const selected=i===heroIndex;
      button.classList.toggle('is-active',selected);
      button.setAttribute('aria-pressed',String(selected));
    });
    heroVisual?.classList.remove('is-changing');
  };
  if(!animate || region.id===heroCollage.dataset.region){render();return;}
  const preload=new Image();
  preload.decoding='async';
  preload.src=region.image;
  const ready=preload.decode?preload.decode():new Promise((resolve,reject)=>{
    if(preload.complete){preload.naturalWidth?resolve():reject(new Error('Image unavailable'));return;}
    preload.onload=resolve;preload.onerror=reject;
  });
  ready.then(()=>{
    if(token!==heroTransitionId)return;
    heroVisual?.classList.add('is-changing');
    window.setTimeout(render,140);
  }).catch((error)=>{
    if(token!==heroTransitionId)return;
    heroVisual?.classList.remove('is-changing');
    console.warn('[JOURNEY ATLAS] Regional Hero image unavailable:',region.image,error);
  });
}
function startHeroRotation(){
  window.clearInterval(heroTimer);
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  heroTimer=window.setInterval(()=>setHero(heroIndex+1),9000);
}
heroButtons.forEach((button)=>button.addEventListener('click',()=>{setHero(Number(button.dataset.hero));startHeroRotation();}));
heroStepButtons.forEach((button)=>button.addEventListener('click',()=>{setHero(heroIndex+Number(button.dataset.heroStep));startHeroRotation();}));
heroVisual?.addEventListener('mouseenter',()=>window.clearInterval(heroTimer));
heroVisual?.addEventListener('mouseleave',startHeroRotation);
document.addEventListener('visibilitychange',()=>document.hidden?window.clearInterval(heroTimer):startHeroRotation());

if(alphabetHost){
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').forEach((letter)=>{
    const button=document.createElement('button');
    button.type='button';button.dataset.letter=letter;button.textContent=letter;
    alphabetHost.append(button);
  });
}

const coreRegistryPromise=fetch('data/atlas-destinations.json')
  .then((response)=>{if(!response.ok) throw new Error('Core destination registry not found');return response.json();});
window.JourneyAtlasRegistryPromise=coreRegistryPromise;
coreRegistryPromise
  .then((core)=>{
    destinations=sortForDisplay(core.destinations||[]);
    if(count) count.textContent=`${destinations.length} DESTINATIONS`;
    renderRail(destinations);
    // The A–Z panel starts hidden; build its cards only after the visitor opens it.
    if(allPanel&&!allPanel.hidden)renderGrid(destinations);
    if(activeTheme)renderThemeResults();
  })
  .catch(()=>{if(rail) rail.innerHTML='<p class="country-load-error">国一覧を読み込めませんでした。</p>';});

Promise.all([
  coreRegistryPromise,
  fetch(LENS_RSS_URL).then((response)=>{if(!response.ok) throw new Error('JOURNEY LENS RSS not found');return response.text();})
])
  .then(([core,rssText])=>renderLensRail(core.destinations||[],rssText))
  .catch((error)=>{
    console.warn('[JOURNEY ATLAS] JOURNEY LENS rail could not be loaded.',error);
    document.querySelector('#lens-world')?.classList.add('is-unavailable');
    if(lensRail) lensRail.hidden=true;
  });


function parseLensFeed(xmlText){
  const xml=new DOMParser().parseFromString(xmlText,'application/xml');
  if(xml.querySelector('parsererror')) throw new Error('Invalid JOURNEY LENS RSS XML');
  return [...xml.querySelectorAll('item')].flatMap((item)=>{
    const link=(item.querySelector('link')?.textContent||'').trim();
    const match=link.match(LENS_LINK_PATTERN);
    if(!match){
      console.warn('[JOURNEY ATLAS] LENS article URL does not match slug+sequence convention:',link);
      return [];
    }
    const slug=match[1];
    const sequence=Number(match[2]);
    const title=(item.querySelector('title')?.textContent||'').trim();
    const titleParts=title.split('｜');
    const subtitle=titleParts.length>1?titleParts.slice(1).join('｜').trim():'';
    const image=(item.querySelector('enclosure')?.getAttribute('url')||'').trim();
    return [{slug,sequence,link,subtitle,image}];
  });
}

// Same order as the rest of the top page: A–Z by the Country's English name (国から探す).
// One story per Country first, then the remaining stories, again A–Z.
function orderLensStories(entries,registryItems){
  const countryOrder=new Map(sortForDisplay(registryItems).map((item,index)=>[item.slug,index]));
  const groups=new Map();

  entries.forEach((entry)=>{
    if(!groups.has(entry.slug))groups.set(entry.slug,[]);
    groups.get(entry.slug).push(entry);
  });
  groups.forEach((items)=>items.sort((a,b)=>a.sequence-b.sequence));

  const orderedSlugs=[...groups.keys()].sort((a,b)=>{
    const aOrder=countryOrder.get(a)??Number.MAX_SAFE_INTEGER;
    const bOrder=countryOrder.get(b)??Number.MAX_SAFE_INTEGER;
    if(aOrder!==bOrder)return aOrder-bOrder;
    return a.localeCompare(b,'en');
  });

  // Round by round, A–Z: the first story of every Country, then each Country's second, and so on.
  const output=[];
  while(orderedSlugs.some((slug)=>(groups.get(slug)?.length||0)>0)){
    orderedSlugs.forEach((slug)=>{
      const next=groups.get(slug)?.shift();
      if(next)output.push(next);
    });
  }

  return output;
}

function createLensCard(entry,country){
  const card=document.createElement('a');
  card.className='lens-card';
  card.href=entry.link;
  card.target='_blank';
  card.rel='noopener noreferrer';
  card.setAttribute('role','listitem');

  const art=document.createElement('div');
  art.className='lens-card__art';
  if(entry.image){
    const img=document.createElement('img');
    img.src=entry.image;
    img.loading='lazy';
    img.decoding='async';
    img.alt=country?`${country.nameJa} — ${entry.subtitle}`:entry.subtitle;
    art.append(img);
  }else{
    art.classList.add('is-image-missing');
    art.setAttribute('aria-hidden','true');
  }

  const body=document.createElement('div');
  body.className='lens-card__body';
  if(country){
    const name=document.createElement('h3');
    name.textContent=country.nameEn;
    const nameJa=document.createElement('small');
    nameJa.textContent=country.nameJa;
    const subtitle=document.createElement('p');
    subtitle.textContent=entry.subtitle;
    body.append(name,nameJa,subtitle);
    card.setAttribute('aria-label',`${country.nameJa}のJOURNEY LENS「${entry.subtitle}」を読む`);
  }else{
    const subtitle=document.createElement('p');
    subtitle.className='lens-card__fallback-title';
    subtitle.textContent=entry.subtitle;
    body.append(subtitle);
    card.setAttribute('aria-label',`JOURNEY LENS「${entry.subtitle}」を読む`);
  }
  card.append(art,body);
  return card;
}

function updateLensControls(){
  if(!lensRail)return;
  const maxScroll=Math.max(0,lensRail.scrollWidth-lensRail.clientWidth);
  if(lensPrevButton)lensPrevButton.disabled=lensRail.scrollLeft<=2;
  if(lensNextButton)lensNextButton.disabled=lensRail.scrollLeft>=maxScroll-2;
}

function scrollLensRail(direction){
  if(!lensRail)return;
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const distance=Math.max(220,lensRail.clientWidth*0.82);
  lensRail.scrollBy({
    left:direction*distance,
    behavior:reduced?'auto':'smooth'
  });
}

lensPrevButton?.addEventListener('click',()=>scrollLensRail(-1));
lensNextButton?.addEventListener('click',()=>scrollLensRail(1));
lensRail?.addEventListener('scroll',()=>window.requestAnimationFrame(updateLensControls),{passive:true});
window.addEventListener('resize',()=>window.requestAnimationFrame(updateLensControls),{passive:true});

function renderLensRail(registryItems,rssText){
  if(!lensRail)return;
  const registryBySlug=new Map(registryItems.map((item)=>[item.slug,item]));
  const parsedEntries=parseLensFeed(rssText);
  const entries=orderLensStories(parsedEntries,registryItems).map((entry)=>({
    ...entry,
    country:registryBySlug.get(entry.slug)||null
  }));

  entries.forEach((entry)=>{
    if(!entry.country)console.warn('[JOURNEY ATLAS] LENS slug not found in atlas-destinations.json:',entry.slug);
  });

  if(lensCount){
    const countryCount=new Set(parsedEntries.map((entry)=>entry.slug)).size;
    lensCount.textContent=`${parsedEntries.length} STORIES / ${countryCount} COUNTRIES`;
  }

  const track=document.createElement('div');
  track.className='lens-rail__track';
  track.setAttribute('role','list');
  entries.forEach((entry)=>track.append(createLensCard(entry,entry.country)));

  lensRail.replaceChildren(track);
  lensRail.scrollLeft=0;
  window.requestAnimationFrame(updateLensControls);
}

// 国から探す: plain A–Z by English name (accents folded, e.g. TÜRKIYE sorts as TURKIYE).
function sortForDisplay(items){
  return [...items].sort((a,b)=>a.nameEn.localeCompare(b.nameEn,'en',{sensitivity:'base'}));
}
function hueFor(country,index){
  const code=[...country.nameEn].reduce((sum,char)=>sum+char.charCodeAt(0),0);
  return (code*7+index*19)%360;
}
// Country heroes are hundreds of individual images. Defer off-screen cards,
// including cards clipped by the horizontal rail and cards in hidden result panels.
const countryArtObserver='IntersectionObserver' in window
  ? new IntersectionObserver((entries,observer)=>{
      entries.forEach((entry)=>{
        if(!entry.isIntersecting)return;
        observer.unobserve(entry.target);
        const image=entry.target.dataset.countryImage;
        delete entry.target.dataset.countryImage;
        if(image)entry.target.style.backgroundImage=`url("${image}")`;
      });
    },{rootMargin:'250px 350px'})
  : null;
function setCountryArtImage(art,image){
  if(!image)return;
  art.classList.add('has-image');
  if(countryArtObserver){
    art.dataset.countryImage=image;
    countryArtObserver.observe(art);
  }else art.style.backgroundImage=`url("${image}")`;
}
function createCard(country,index,compact=false){
  const card=document.createElement(country.atlasPublished&&country.href?'a':'article');
  card.className=`country-card${country.atlasPublished?' is-open':' is-closed'}`;
  card.dataset.slug=country.slug;card.dataset.name=`${country.nameEn} ${country.nameJa}`.toLowerCase();
  if(country.atlasPublished&&country.href){card.href=country.href;card.setAttribute('aria-label',`${country.nameJa}のJOURNEY ATLASを見る`);}
  const art=document.createElement('div');art.className='country-card__art';art.style.setProperty('--hue',String(hueFor(country,index)));
  // Every card uses the Country's own approved hero image. (Six cards used to crop a shared
  // six-panel collage; the hero art has since changed, which left them blank or mis-cropped.)
  setCountryArtImage(art,country.image);
  art.innerHTML=`<span class="country-card__flag" aria-hidden="true">${country.flag}</span>`;
  const body=document.createElement('div');body.className='country-card__body';
  body.innerHTML=`<h3>${country.nameEn}</h3><p>${country.nameJa}</p>${country.atlasPublished?'<span class="country-card__open" aria-hidden="true">›</span>':''}`;
  card.append(art,body);return card;
}
function renderRail(items){if(!rail)return;const fragment=document.createDocumentFragment();items.forEach((country,index)=>fragment.append(createCard(country,index)));rail.replaceChildren(fragment);updateDots();}
function renderGrid(items,captions=null){if(!grid)return;const fragment=document.createDocumentFragment();items.forEach((country,index)=>{const card=createCard(country,index,true);const note=captions?.get(country.slug);if(note){const small=document.createElement('small');small.className='country-card__match';small.textContent=note;card.querySelector('.country-card__body')?.append(small);}fragment.append(card);});grid.replaceChildren(fragment);addFolios();if(empty)empty.hidden=items.length!==0;}
function scrollRail(direction){if(!rail)return;rail.scrollBy({left:Math.max(460,rail.clientWidth*.82)*direction,behavior:'smooth'});}
function updateDots(){if(!rail||dots.length===0)return;const max=rail.scrollWidth-rail.clientWidth;const ratio=max>0?rail.scrollLeft/max:0;const index=Math.min(dots.length-1,Math.round(ratio*(dots.length-1)));dots.forEach((dot,i)=>dot.classList.toggle('is-active',i===index));}
function themeLabel(theme){
  if(themeMeta[theme]?.label)return themeMeta[theme].label;
  return document.querySelector(`[data-theme="${theme}"] b`)?.textContent?.trim()||theme;
}
function getThemeItems(theme=activeTheme){
  if(!theme)return [];
  const slugs=themeSets[theme]||[];
  return sortForDisplay(slugs
    .map((slug)=>destinations.find((country)=>country.slug===slug))
    .filter((country)=>country?.atlasPublished===true));
}
function syncThemeSelectionUI(){
  document.querySelectorAll('.theme-icons button[data-theme]').forEach((button)=>{
    const selected=Boolean(activeTheme)&&button.dataset.theme===activeTheme;
    button.classList.toggle('is-active',selected);
    button.setAttribute('aria-pressed',String(selected));
  });
}
function renderThemeResults(){
  if(!themeResults||!themeResultsGrid)return;
  if(!activeTheme){
    themeResults.hidden=true;
    themeResultsGrid.replaceChildren();
    if(themeResultsSearch)themeResultsSearch.value='';
    syncThemeSelectionUI();
    return;
  }

  const allThemeItems=getThemeItems(activeTheme);
  // テーマ×季節: narrow to Countries whose おすすめの時期 includes the chosen month.
  // The season index is shared with 季節から探す and loaded on demand.
  const monthReady=Boolean(seasonIndex);
  if(!monthReady)loadSeasonIndex()?.then(()=>{if(activeTheme&&seasonIndex)renderThemeResults();});
  renderThemeMonthTabs(allThemeItems,monthReady);
  const themeItems=activeThemeMonth&&monthReady
    ?allThemeItems.filter((country)=>seasonWindowFor(country.slug,activeThemeMonth))
    :allThemeItems;
  const regionCounts=new Map();
  themeItems.forEach((country)=>{
    const region=themeRegionByIso.get(country.iso2);
    if(region)regionCounts.set(region,(regionCounts.get(region)||0)+1);
  });
  if(activeThemeRegion!=='all'&&!regionCounts.has(activeThemeRegion))activeThemeRegion='all';
  renderThemeRegionTabs(themeItems.length,regionCounts);
  const baseItems=activeThemeRegion==='all'
    ?themeItems
    :themeItems.filter((country)=>themeRegionByIso.get(country.iso2)===activeThemeRegion);
  const query=themeResultsSearch?.value.trim().toLowerCase()||'';
  const items=query
    ?baseItems.filter((country)=>`${country.nameEn} ${country.nameJa}`.toLowerCase().includes(query))
    :baseItems;

  const fragment=document.createDocumentFragment();
  const shown=items.slice(0,themeLimit);
  shown.forEach((country,index)=>{
    const card=createCard(country,index,true);
    card.setAttribute('role','listitem');
    const window_=activeThemeMonth&&monthReady?seasonWindowFor(country.slug,activeThemeMonth):null;
    if(window_){
      const note=document.createElement('small');
      note.className='country-card__match country-card__season';
      seasonNote(note,window_[1]);
      note.title=window_[2];
      card.querySelector('.country-card__body')?.append(note);
    }
    fragment.append(card);
  });
  themeResultsGrid.replaceChildren(fragment);
  renderThemeMore(items.length-shown.length);
  saveTopState();

  const label=themeLabel(activeTheme);
  if(themeResultsTitle)themeResultsTitle.textContent=activeThemeMonth?`${label}　${activeThemeMonth}月におすすめ`:label;
  const regionLabel=themeRegions.find((region)=>region.id===activeThemeRegion)?.label;
  if(themeResultsMeta)themeResultsMeta.textContent=query
    ?`${baseItems.length}件の候補から、${items.length}件を表示しています。`
    :regionLabel
      ?`${regionLabel}　${baseItems.length} / ${themeItems.length} DESTINATIONS`
      :`${baseItems.length} DESTINATIONS`;
  if(themeResultsEmpty)themeResultsEmpty.hidden=items.length!==0;
  themeResults.hidden=false;
  syncThemeSelectionUI();
}
const themeMonthTabs=document.querySelector('#theme-month-tabs');
function renderThemeMonthTabs(items,ready){
  if(!themeMonthTabs)return;
  themeMonthTabs.hidden=false;
  const count=(month)=>ready?items.filter((country)=>seasonWindowFor(country.slug,month)).length:null;
  const options=[{month:null,label:'すべての月'},...Array.from({length:12},(_,i)=>({month:i+1,label:`${i+1}月`}))];
  const head=document.createElement('span');
  head.className='theme-month-tabs__label';
  head.textContent='旅に出る月';
  themeMonthTabs.replaceChildren(head,...options.map(({month,label})=>{
    const button=document.createElement('button');
    button.type='button';
    button.dataset.themeMonth=month===null?'':String(month);
    const on=month===activeThemeMonth;
    button.classList.toggle('is-active',on);
    button.setAttribute('aria-pressed',String(on));
    const n=month===null?null:count(month);
    button.innerHTML=n===null?label:`${label}<span>${n}</span>`;
    return button;
  }));
}
themeMonthTabs?.addEventListener('click',(event)=>{
  const button=event.target.closest('[data-theme-month]');
  if(!button)return;
  activeThemeMonth=button.dataset.themeMonth?Number(button.dataset.themeMonth):null;
  themeLimit=THEME_PAGE;
  if(activeThemeMonth&&!seasonIndex){loadSeasonIndex()?.then(()=>renderThemeResults());}
  renderThemeResults();
});
function renderThemeRegionTabs(total,regionCounts){
  if(!themeRegionTabs)return;
  if(!themeRegions.length||regionCounts.size<2){themeRegionTabs.hidden=true;themeRegionTabs.replaceChildren();return;}
  themeRegionTabs.hidden=false;
  const options=[{id:'all',label:'すべて',count:total},...themeRegions.filter((region)=>regionCounts.has(region.id)).map((region)=>({...region,count:regionCounts.get(region.id)}))];
  themeRegionTabs.replaceChildren(...options.map(({id,label,count})=>{
    const button=document.createElement('button');
    button.type='button';
    button.dataset.themeRegion=id;
    const on=id===activeThemeRegion;
    button.classList.toggle('is-active',on);
    button.setAttribute('aria-pressed',String(on));
    button.innerHTML=`${label}<span>${count}</span>`;
    return button;
  }));
}
themeRegionTabs?.addEventListener('click',(event)=>{
  const button=event.target.closest('[data-theme-region]');
  if(!button)return;
  activeThemeRegion=button.dataset.themeRegion;
  themeLimit=THEME_PAGE;
  renderThemeResults();
});
// Long theme lists (up to ~140) start with one screenful; the rest is one tap away.
const THEME_PAGE=24;
let themeLimit=THEME_PAGE;
let themeMore=null;
function renderThemeMore(remaining){
  if(!themeResultsGrid)return;
  if(!themeMore){
    themeMore=document.createElement('button');
    themeMore.type='button';
    themeMore.className='theme-results__more';
    themeMore.addEventListener('click',()=>{
      const before=themeResultsGrid.children.length;
      themeLimit+=THEME_PAGE*2;
      renderThemeResults();
      themeResultsGrid.children[before]?.focus({preventScroll:true});
    });
    themeResultsGrid.after(themeMore);
  }
  themeMore.hidden=remaining<=0;
  themeMore.textContent=`もっと見る（残り${remaining}件）`;
}
function clearThemeResults(){
  themeLimit=THEME_PAGE;
  activeThemeMonth=null;
  activeThemeRegion='all';
  activeTheme=null;
  renderThemeResults();
  saveTopState();
}
function setAllPanel(open,reset=true){
  if(!allPanel||!toggleAll)return;
  allPanel.hidden=!open;toggleAll.setAttribute('aria-expanded',String(open));
  toggleAll.firstChild.textContent=open?'一覧を閉じる ':'索引（A–Z）を見る ';
  if(open&&reset){
    if(searchInput)searchInput.value='';document.querySelector('#countries')?.classList.remove('is-searching');if(allTitle)allTitle.textContent=INDEX_TITLE;
    renderGrid(destinations);
  }
  if(open) allPanel.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function focusCountry(slug){
  const country=destinations.find((item)=>item.slug===slug);
  if(!country)return;
  setAllPanel(true,false);
  if(searchInput)searchInput.value=country.nameJa;
  renderGrid([country]);
}
function showTheme(theme,{scroll=true}={}){
  activeTheme=theme;
  themeLimit=THEME_PAGE;
  if(themeResultsSearch)themeResultsSearch.value='';
  renderThemeResults();
  // On narrow screens the results render far below the eight theme buttons, so a tap looked
  // like nothing happened. Bring the selected theme's results into view.
  if(scroll&&themeResults&&!themeResults.hidden){
    const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    themeResults.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'});
  }
}

function getWishedSlugs(){try{return destinations.filter((country)=>localStorage.getItem(`journey-atlas:wish:${country.slug}`)==='true').map((country)=>country.slug);}catch{return[];}}
let toastTimer;
function showToast(message){if(!toast)return;toast.textContent=message;toast.hidden=false;window.clearTimeout(toastTimer);toastTimer=window.setTimeout(()=>{toast.hidden=true;},2600);}

prev?.addEventListener('click',()=>scrollRail(-1));next?.addEventListener('click',()=>scrollRail(1));rail?.addEventListener('scroll',()=>window.requestAnimationFrame(updateDots),{passive:true});
toggleAll?.addEventListener('click',()=>setAllPanel(Boolean(allPanel?.hidden)));
// Search box in the 国から探す header: English or Japanese (hiragana/katakana/full-width all match).
function normalizeSearch(value){
  return String(value||'').normalize('NFKC').toLowerCase()
    .replace(/[\u3041-\u3096]/g,(ch)=>String.fromCharCode(ch.charCodeAt(0)+0x60))
    .replace(/[\s・&'’.\-]/g,'');
}
// Keyword search: country names first, then the names of the eight scenes, then scene
// descriptions and season notes (e.g. 「オーロラ」「フィヨルド」「紅葉」). The scene index is
// generated from the Country data at build time and loaded on first use.
let sceneIndex=null,sceneIndexPromise=null;
function loadSceneIndex(){
  if(!sceneIndexPromise){
    sceneIndexPromise=fetch('data/top-search-index.json')
      .then((response)=>{if(!response.ok)throw new Error('Search index not found');return response.json();})
      .then(({countries={}})=>{
        sceneIndex=new Map(Object.entries(countries).map(([slug,row])=>[slug,{
          scenes:(row.s||[]).map(([name,local,text])=>({name,key:normalizeSearch(`${name} ${local}`),text:normalizeSearch(text)})),
          seasons:(row.m||[]).map(([months,text])=>({months,text,key:normalizeSearch(text)}))
        }]));
        if(searchInput?.value.trim())searchInput.dispatchEvent(new Event('input'));
      })
      .catch((error)=>{console.warn('[JOURNEY ATLAS] Scene search unavailable.',error);});
  }
  return sceneIndexPromise;
}
searchInput?.addEventListener('focus',loadSceneIndex,{once:true});
let searchCaptions=new Map();
function searchCountries(){
  const query=normalizeSearch(searchInput?.value);
  searchCaptions=new Map();
  if(!query)return destinations;
  const scored=[];
  destinations.forEach((country)=>{
    const names=[country.nameJa,country.nameEn].map(normalizeSearch);
    if(names.some((name)=>name.startsWith(query))){scored.push([0,country]);return;}
    if(normalizeSearch(`${country.nameEn} ${country.nameJa} ${country.slug}`).includes(query)){scored.push([1,country]);return;}
    const row=query.length>=2&&sceneIndex?.get(country.slug);
    if(!row)return;
    const byName=row.scenes.find((scene)=>scene.key.includes(query));
    if(byName){scored.push([2,country]);searchCaptions.set(country.slug,`景色：${byName.name}`);return;}
    const byText=row.scenes.find((scene)=>scene.text.includes(query));
    if(byText){scored.push([3,country]);searchCaptions.set(country.slug,`景色：${byText.name}`);return;}
    const bySeason=row.seasons.find((season)=>season.key.includes(query));
    if(bySeason){scored.push([4,country]);searchCaptions.set(country.slug,`季節：${bySeason.months}`);}
  });
  // A country-name hit (タイ → Thailand) wins outright; scene/season matches are for words
  // that are not country names (オーロラ, フィヨルド, 紅葉), so they would only add noise here.
  const named=scored.filter(([rank])=>rank<=1);
  if(named.length){searchCaptions=new Map();return named.sort((a,b)=>a[0]-b[0]).map(([,country])=>country);}
  return scored.sort((a,b)=>a[0]-b[0]).map(([,country])=>country);
}
searchInput?.addEventListener('input',()=>{
  const wasHidden=Boolean(allPanel?.hidden);
  if(allPanel&&wasHidden&&searchInput.value.trim()){
    allPanel.hidden=false;toggleAll?.setAttribute('aria-expanded','true');
    if(toggleAll)toggleAll.firstChild.textContent='一覧を閉じる ';
  }
  alphabetButtons().forEach((item)=>item.classList.toggle('is-active',item.dataset.letter==='all'));
  document.querySelector('#countries')?.classList.toggle('is-searching',Boolean(searchInput.value.trim()));
  if(searchInput.value.trim())loadSceneIndex();
  const items=searchCountries();
  renderGrid(items,searchCaptions);
  if(allTitle)allTitle.textContent=searchInput.value.trim()?`「${searchInput.value.trim()}」の検索結果 ${items.length}件`:INDEX_TITLE;
});
searchInput?.addEventListener('keydown',(event)=>{
  if(event.key!=='Enter'||event.isComposing)return;
  event.preventDefault();
  const items=searchCountries();
  if(items.length===1&&items[0].href){location.href=items[0].href;return;}
  allPanel?.scrollIntoView({behavior:'smooth',block:'nearest'});
});
themeResultsSearch?.addEventListener('input',()=>{themeLimit=THEME_PAGE;renderThemeResults();});
themeResultsClear?.addEventListener('click',clearThemeResults);
wishButton?.addEventListener('click',()=>{const wished=getWishedSlugs();if(wished.length===0){showToast('行ってみたい国はまだ保存されていません。国ページから追加できます。');return;}setAllPanel(true,false);if(searchInput)searchInput.value='';document.querySelector('#countries')?.classList.remove('is-searching');if(allTitle)allTitle.textContent=INDEX_TITLE;renderGrid(destinations.filter((country)=>wished.includes(country.slug)));showToast(`${wished.length}件の行ってみたい国を表示しています。`);});
document.querySelectorAll('[data-country-focus]').forEach((button)=>button.addEventListener('click',()=>focusCountry(button.dataset.countryFocus)));
document.querySelectorAll('[data-theme]').forEach((button)=>button.addEventListener('click',()=>showTheme(button.dataset.theme)));
document.querySelector('[data-open-all]')?.addEventListener('click',()=>setAllPanel(true));
document.addEventListener('click',(event)=>{
  const button=event.target.closest('[data-letter]');if(!button)return;
  alphabetButtons().forEach((item)=>item.classList.toggle('is-active',item===button));
  const letter=button.dataset.letter;
  const filtered=letter==='all'?destinations:letter==='#'?destinations.filter((country)=>!/[A-Z]/.test(country.nameEn[0])):destinations.filter((country)=>country.nameEn.startsWith(letter));
  setAllPanel(true,false);
  if(searchInput)searchInput.value='';document.querySelector('#countries')?.classList.remove('is-searching');if(allTitle)allTitle.textContent=INDEX_TITLE;
  renderGrid(filtered);
});

// Header 「旅先を探す」: the five ways to search open as a small menu on wider screens.
// (In the mobile menu they are always listed, so the toggle does nothing there.)
(()=>{
  const wrap=document.querySelector('.nav-explore');
  const toggle=document.querySelector('#nav-explore-toggle');
  if(!wrap||!toggle)return;
  const setOpen=(open)=>{wrap.classList.toggle('is-open',open);toggle.setAttribute('aria-expanded',String(open));};
  toggle.addEventListener('click',(event)=>{event.stopPropagation();setOpen(!wrap.classList.contains('is-open'));});
  wrap.addEventListener('click',(event)=>{if(event.target.closest('a'))setOpen(false);});
  document.addEventListener('click',(event)=>{if(!wrap.contains(event.target))setOpen(false);});
  document.addEventListener('keydown',(event)=>{if(event.key==='Escape'&&wrap.classList.contains('is-open')){setOpen(false);toggle.focus();}});
  wrap.addEventListener('focusout',(event)=>{if(!wrap.contains(event.relatedTarget))setOpen(false);});
})();

// Mobile header menu (the nav links are collapsed behind a button on narrow screens).
(()=>{
  const toggle=document.querySelector('.top-menu-toggle');
  const nav=document.querySelector('#top-nav');
  const header=document.querySelector('.top-header');
  if(!toggle||!nav||!header)return;
  const setOpen=(open)=>{
    header.classList.toggle('is-menu-open',open);
    toggle.setAttribute('aria-expanded',String(open));
  };
  toggle.addEventListener('click',()=>setOpen(toggle.getAttribute('aria-expanded')!=='true'));
  nav.addEventListener('click',(event)=>{if(event.target.closest('a'))setOpen(false);});
  document.addEventListener('keydown',(event)=>{if(event.key==='Escape'&&header.classList.contains('is-menu-open')){setOpen(false);toggle.focus();}});
  document.addEventListener('click',(event)=>{if(!header.contains(event.target))setOpen(false);});
  window.matchMedia('(min-width:761px)').addEventListener?.('change',(e)=>{if(e.matches)setOpen(false);});
})();


// ---------------------------------------------------------------------------
// Remember the selection in the URL (?theme=sea&tregion=asia&q=タイ) so that
// coming back from a Country page — or opening a shared link — shows the same list.
// The fragment (#map, #themes …) is left untouched.
// ---------------------------------------------------------------------------
let restoringTopState=true;
const SCROLL_KEY='journey-atlas:top-scroll';
function saveTopState(){
  if(restoringTopState)return;
  const url=new URL(location.href);
  const set=(key,value)=>value?url.searchParams.set(key,value):url.searchParams.delete(key);
  set('theme',activeTheme||'');
  set('tregion',activeTheme&&activeThemeRegion!=='all'?activeThemeRegion:'');
  set('tmonth',activeTheme&&activeThemeMonth?String(activeThemeMonth):'');
  set('q',searchInput?.value.trim()||'');
  set('month',seasonChosen?String(seasonMonth):'');
  set('sregion',seasonChosen&&seasonRegion!=='all'?seasonRegion:'');
  if(url.href!==location.href)history.replaceState(history.state,'',url);
}
searchInput?.addEventListener('input',saveTopState);
try{history.scrollRestoration='manual';}catch{}
window.addEventListener('pagehide',()=>{
  try{sessionStorage.setItem(SCROLL_KEY,JSON.stringify({url:location.pathname+location.search,y:window.scrollY,limit:themeLimit,seasonLimit}));}catch{}
});
Promise.all([coreRegistryPromise.catch(()=>{}),themeTaxonomyPromise,themeRegionPromise]).then(()=>{
  const params=new URLSearchParams(location.search);
  const nav=performance.getEntriesByType?.('navigation')?.[0]?.type;
  let saved=null;
  try{saved=JSON.parse(sessionStorage.getItem(SCROLL_KEY)||'null');}catch{}
  const returning=(nav==='back_forward'||nav==='reload')&&saved&&saved.url===location.pathname+location.search;
  const theme=params.get('theme');
  if(theme&&themeSets[theme]){
    activeTheme=theme;
    activeThemeRegion=params.get('tregion')||'all';
    {const m=Number(params.get('tmonth'));activeThemeMonth=m>=1&&m<=12?m:null;}
    themeLimit=returning&&saved.limit?saved.limit:THEME_PAGE;
    renderThemeResults();
  }
  const q=params.get('q');
  if(q&&searchInput){searchInput.value=q;searchInput.dispatchEvent(new Event('input'));}
  restoringTopState=false;
  // Season results load their own index; wait for them so the saved scroll position exists.
  if(returning)Promise.resolve(seasonChosen?seasonReady:null).then(()=>requestAnimationFrame(()=>window.scrollTo(0,saved.y)));
  else if(!location.hash&&(theme||q))(theme?themeResults:document.querySelector('#countries'))?.scrollIntoView({block:'start'});
});


// ---------------------------------------------------------------------------
// 季節から探す: pick a month, list the Countries whose おすすめの時期 (bestSeason) includes it.
// data/top-season-index.json is generated from the Country data at build time and loaded
// when the panel comes near the viewport (or at once when the URL carries ?month=).
// ---------------------------------------------------------------------------
const seasonMonthsHost=document.querySelector('#season-months');
const seasonResults=document.querySelector('#season-results');
const seasonGrid=document.querySelector('#season-results-grid');
const seasonTitle=document.querySelector('#season-results-title');
const seasonMeta=document.querySelector('#season-results-meta');
const seasonTabs=document.querySelector('#season-region-tabs');
const seasonMore=document.querySelector('#season-results-more');
const seasonEmpty=document.querySelector('#season-results-empty');
const SEASON_PAGE=24;
let seasonIndex=null,seasonIndexPromise=null;
let seasonMonth=null;     // nothing selected until the visitor picks a month (or ?month=)
let seasonChosen=false;   // true once the visitor picks a month (or arrives with ?month=)
let seasonRegion='all';
let seasonLimit=SEASON_PAGE;
let seasonReady=null;
{
  const params=new URLSearchParams(location.search);
  const month=Number(params.get('month'));
  if(month>=1&&month<=12){seasonMonth=month;seasonChosen=true;seasonRegion=params.get('sregion')||'all';}
}
let seasonStage='idle';   // where loading is, shown if it stalls (helps diagnose one browser)
function loadSeasonIndex(){
  if(!seasonIndexPromise){
    seasonStage='fetch';
    seasonIndexPromise=fetch('data/top-season-index.json')
      .then((response)=>{
        seasonStage=`response ${response.status} ${response.headers.get('content-type')||''}`.trim();
        if(!response.ok)throw new Error(`HTTP ${response.status}`);
        return response.text();
      })
      .then((text)=>{
        seasonStage=`parse ${text.length}`;
        const {countries={}}=JSON.parse(text);
        seasonIndex=new Map(Object.entries(countries));
        seasonStage='ready';
      })
      .catch((error)=>{
        console.warn('[JOURNEY ATLAS] Season search unavailable.',error);
        seasonIndexPromise=null;   // allow a retry on the next tap
        showSeasonStatus(`おすすめの時期を読み込めませんでした。少し待ってから、もう一度月を選んでください。（${error?.name||'Error'}: ${error?.message||''} / ${seasonStage}）`);
      });
  }
  return seasonIndexPromise;
}
// Shown in the results area while the index loads, or if it cannot be loaded, so a tap
// on a month always gives visible feedback.
function showSeasonStatus(message){
  if(!seasonResults||!seasonGrid||!seasonMonth)return;
  seasonResults.hidden=false;
  if(seasonTitle)seasonTitle.textContent=`${seasonMonth}月におすすめの旅先`;
  if(seasonMeta)seasonMeta.textContent='';
  if(seasonTabs){seasonTabs.hidden=true;seasonTabs.replaceChildren();}
  if(seasonMore)seasonMore.hidden=true;
  seasonGrid.replaceChildren();
  if(seasonEmpty){seasonEmpty.textContent=message;seasonEmpty.hidden=false;}
}
// 「おすすめ 12〜4月」: keep the period on one line so it never splits as 「12〜 / 4月」.
function seasonNote(note,label){
  const period=document.createElement('span');
  period.className='country-card__season-period';
  period.textContent=label;
  note.replaceChildren('おすすめ ',period);
}
function seasonWindowFor(slug,month){
  return (seasonIndex?.get(slug)||[]).find(([months])=>months.includes(month))||null;
}
function seasonItems(month){
  return destinations.filter((country)=>country.atlasPublished&&seasonWindowFor(country.slug,month));
}
function renderSeasonMonths(){
  if(!seasonMonthsHost)return;
  const ready=Boolean(seasonIndex&&destinations.length);
  seasonMonthsHost.replaceChildren(...Array.from({length:12},(_,i)=>{
    const month=i+1;
    const button=document.createElement('button');
    button.type='button';
    button.dataset.seasonMonth=String(month);
    const on=month===seasonMonth;
    button.classList.toggle('is-active',on);
    button.setAttribute('aria-pressed',String(on));
    const total=ready?seasonItems(month).length:null;
    button.innerHTML=`<b>${month}<small>月</small></b>${total===null?'':`<span>${total}</span>`}`;
    button.setAttribute('aria-label',total===null?`${month}月`:`${month}月（${total}件）`);
    return button;
  }));
}
function renderSeasonResults(){
  renderSeasonMonths();
  if(!seasonMonth){if(seasonResults)seasonResults.hidden=true;return;}
  if(!seasonResults||!seasonGrid||!seasonIndex||!destinations.length)return;
  const all=seasonItems(seasonMonth);
  const counts=new Map();
  all.forEach((country)=>{const region=themeRegionByIso.get(country.iso2);if(region)counts.set(region,(counts.get(region)||0)+1);});
  if(seasonRegion!=='all'&&!counts.has(seasonRegion))seasonRegion='all';
  if(seasonTabs){
    if(!themeRegions.length||counts.size<2){seasonTabs.hidden=true;seasonTabs.replaceChildren();}
    else{
      seasonTabs.hidden=false;
      const options=[{id:'all',label:'すべて',count:all.length},...themeRegions.filter((region)=>counts.has(region.id)).map((region)=>({...region,count:counts.get(region.id)}))];
      seasonTabs.replaceChildren(...options.map(({id,label,count})=>{
        const button=document.createElement('button');
        button.type='button';
        button.dataset.seasonRegion=id;
        const on=id===seasonRegion;
        button.classList.toggle('is-active',on);
        button.setAttribute('aria-pressed',String(on));
        button.innerHTML=`${label}<span>${count}</span>`;
        return button;
      }));
    }
  }
  const items=seasonRegion==='all'?all:all.filter((country)=>themeRegionByIso.get(country.iso2)===seasonRegion);
  const shown=items.slice(0,seasonLimit);
  const fragment=document.createDocumentFragment();
  shown.forEach((country,index)=>{
    const card=createCard(country,index,true);
    card.setAttribute('role','listitem');
    const window_=seasonWindowFor(country.slug,seasonMonth);
    if(window_){
      const note=document.createElement('small');
      note.className='country-card__match country-card__season';
      seasonNote(note,window_[1]);
      note.title=window_[2];
      card.querySelector('.country-card__body')?.append(note);
      if(card.hasAttribute('aria-label'))card.setAttribute('aria-label',`${card.getAttribute('aria-label')}（おすすめの時期 ${window_[1]}）`);
    }
    fragment.append(card);
  });
  seasonGrid.replaceChildren(fragment);
  if(seasonMore){
    const remaining=items.length-shown.length;
    seasonMore.hidden=remaining<=0;
    seasonMore.textContent=`もっと見る（残り${remaining}件）`;
  }
  const regionLabel=themeRegions.find((region)=>region.id===seasonRegion)?.label;
  if(seasonTitle)seasonTitle.textContent=`${seasonMonth}月におすすめの旅先`;
  if(seasonMeta)seasonMeta.textContent=regionLabel?`${regionLabel}　${items.length} / ${all.length} DESTINATIONS`:`${items.length} DESTINATIONS`;
  if(seasonEmpty){seasonEmpty.textContent='該当する国・地域がありません。';seasonEmpty.hidden=items.length!==0;}
  seasonResults.hidden=false;
  saveTopState();
}
seasonMonthsHost?.addEventListener('click',(event)=>{
  const button=event.target.closest('[data-season-month]');
  if(!button)return;
  seasonMonth=Number(button.dataset.seasonMonth);
  seasonChosen=true;
  seasonLimit=SEASON_PAGE;
  if(seasonIndex&&destinations.length){
    try{renderSeasonResults();}
    catch(error){
      console.error('[JOURNEY ATLAS] Season results failed.',error);
      showSeasonStatus(`一覧を表示できませんでした。（${error?.name||'Error'}: ${error?.message||''}）`);
    }
    return;
  }
  // Data not ready yet (slow network, or the panel was reached without scrolling past it):
  // say so, then load and show the list.
  renderSeasonMonths();
  showSeasonStatus('読み込んでいます…');
  startSeason();
});
seasonTabs?.addEventListener('click',(event)=>{
  const button=event.target.closest('[data-season-region]');
  if(!button)return;
  seasonRegion=button.dataset.seasonRegion;
  seasonLimit=SEASON_PAGE;
  renderSeasonResults();
});
seasonMore?.addEventListener('click',()=>{
  const before=seasonGrid?.children.length||0;
  seasonLimit+=SEASON_PAGE*2;
  renderSeasonResults();
  seasonGrid?.children[before]?.focus({preventScroll:true});
});
renderSeasonMonths();
function startSeason(){
  // If loading stalls, say where it stopped instead of leaving 「読み込んでいます…」 forever.
  const timer=window.setTimeout(()=>{
    if(!seasonIndex)showSeasonStatus(`読み込みに時間がかかっています。もう一度月を選んでください。（${seasonStage}）`);
  },10000);
  return Promise.all([loadSeasonIndex(),coreRegistryPromise.catch(()=>{}),themeRegionPromise.catch(()=>{})]).then(()=>{
    window.clearTimeout(timer);
    if(!seasonIndex)return;
    if(!destinations.length){showSeasonStatus('国の一覧を読み込めませんでした。ページを再読み込みしてください。');return;}
    try{renderSeasonResults();}
    catch(error){
      console.error('[JOURNEY ATLAS] Season results failed.',error);
      showSeasonStatus(`一覧を表示できませんでした。（${error?.name||'Error'}: ${error?.message||''}）`);
    }
  });
}
{
  const start=()=>Promise.all([loadSeasonIndex(),coreRegistryPromise.catch(()=>{}),themeRegionPromise.catch(()=>{})]).then(()=>{
    if(!seasonIndex)return;
    try{const saved=JSON.parse(sessionStorage.getItem(SCROLL_KEY)||'null');if(seasonChosen&&saved?.url===location.pathname+location.search&&saved.seasonLimit)seasonLimit=saved.seasonLimit;}catch{}
    try{seasonChosen?renderSeasonResults():renderSeasonMonths();}
    catch(error){
      console.error('[JOURNEY ATLAS] Season results failed.',error);
      showSeasonStatus(`一覧を表示できませんでした。（${error?.name||'Error'}: ${error?.message||''}）`);
      return;
    }
    // A shared ?month= link (not a back/reload, which restores its own scroll) opens at the panel.
    const nav=performance.getEntriesByType?.('navigation')?.[0]?.type;
    const params=new URLSearchParams(location.search);
    if(seasonChosen&&!location.hash&&nav!=='back_forward'&&nav!=='reload'&&!params.get('theme')&&!params.get('q'))
    {
      // Images above the panel can still change its position, so settle again once the page has loaded.
      const go=()=>requestAnimationFrame(()=>document.querySelector('#seasons')?.scrollIntoView({block:'start'}));
      go();
      if(document.readyState!=='complete')window.addEventListener('load',go,{once:true});
    }
  });
  const panel=document.querySelector('#seasons');
  if(seasonChosen||location.hash==='#seasons'||!panel||!('IntersectionObserver' in window))seasonReady=start();
  else{
    const observer=new IntersectionObserver((entries)=>{
      if(entries.some((entry)=>entry.isIntersecting)){observer.disconnect();start();}
    },{rootMargin:'600px 0px'});
    observer.observe(panel);
    // Also start on any interaction with the panel (e.g. jumping here from the header menu).
    ['pointerdown','focusin'].forEach((type)=>panel.addEventListener(type,()=>{loadSeasonIndex();},{once:true,passive:true}));
  }
}

// ---------------------------------------------------------------------------
// Closing lists: 「月の選択を解除 ×」, 「一覧を閉じる ×」 in the country list head, and an
// 「一覧を閉じる」 at the end of every long list (country / theme / season). Closing from the
// bottom brings the section heading back into view, so the visitor is not left mid-page.
// ---------------------------------------------------------------------------
function clearSeasonResults(){
  seasonMonth=null;
  seasonChosen=false;
  seasonRegion='all';
  seasonLimit=SEASON_PAGE;
  renderSeasonResults();
  saveTopState();
}
document.querySelector('#season-results-clear')?.addEventListener('click',()=>{
  clearSeasonResults();
  seasonMonthsHost?.querySelector('button')?.focus({preventScroll:true});
});
document.querySelector('#all-countries-close')?.addEventListener('click',()=>{
  setAllPanel(false);
  toggleAll?.focus({preventScroll:true});
});
document.addEventListener('click',(event)=>{
  const button=event.target.closest('[data-results-close]');
  if(!button)return;
  const target=button.dataset.resultsClose;
  if(target==='countries'){setAllPanel(false);}
  else if(target==='themes'){clearThemeResults();}
  else if(target==='seasons'){clearSeasonResults();}
  const section=document.querySelector(`#${target}`);
  if(section){
    const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    section.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'});
  }
});

// ---------------------------------------------------------------------------
// 景色から探す: a gallery of Scene illustrations (small thumbnails generated by
// scripts/build_scene_thumbs.py). Order is shuffled on every visit: one Scene per Country
// first (so no Country repeats early), then more. A tile opens the Country page at that Scene.
// ---------------------------------------------------------------------------
const sceneGrid=document.querySelector('#gallery-grid');
const sceneTabs=document.querySelector('#gallery-region-tabs');
const sceneMore=document.querySelector('#gallery-more');
const sceneShuffle=document.querySelector('#gallery-shuffle');
const sceneLead=document.querySelector('#gallery-lead');
const SCENE_PAGE=12;
let sceneRows=null,scenePromise=null,sceneOrder=[],sceneRegion='all',sceneLimit=SCENE_PAGE;
function shuffled(items){
  const list=[...items];
  for(let i=list.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[list[i],list[j]]=[list[j],list[i]];}
  return list;
}
function loadScenes(){
  if(!scenePromise){
    scenePromise=Promise.all([
      fetch('data/top-scene-index.json').then((response)=>{if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json();}),
      coreRegistryPromise.catch(()=>null),
      themeRegionPromise.catch(()=>null)
    ]).then(([{countries={}}])=>{
      const bySlug=new Map(destinations.map((country)=>[country.slug,country]));
      sceneRows=Object.entries(countries).flatMap(([slug,rows])=>{
        const country=bySlug.get(slug);
        if(!country?.atlasPublished||!country.href)return [];
        return rows.map(([id,name])=>({slug,id,name,country}));
      });
      if(sceneLead){
        const countryCount=new Set(sceneRows.map((row)=>row.slug)).size;
        sceneLead.textContent=`気になる景色から、旅先を見つけよう。${countryCount}の国・地域の${sceneRows.length.toLocaleString('ja-JP')}の景色から、開くたびにちがう組み合わせで並びます。`;
      }
      shuffleScenes();
    }).catch((error)=>{
      console.warn('[JOURNEY ATLAS] Scene gallery unavailable.',error);
      scenePromise=null;
      if(sceneGrid)sceneGrid.innerHTML='<p class="country-empty">景色を読み込めませんでした。ページを再読み込みしてください。</p>';
    });
  }
  return scenePromise;
}
function shuffleScenes(){
  if(!sceneRows)return;
  const rows=sceneRegion==='all'?sceneRows:sceneRows.filter((row)=>themeRegionByIso.get(row.country.iso2)===sceneRegion);
  const groups=new Map();
  shuffled(rows).forEach((row)=>{if(!groups.has(row.slug))groups.set(row.slug,[]);groups.get(row.slug).push(row);});
  const slugs=shuffled([...groups.keys()]);
  sceneOrder=[];
  while(sceneOrder.length<rows.length){
    slugs.forEach((slug)=>{const next=groups.get(slug).shift();if(next)sceneOrder.push(next);});
  }
  sceneLimit=SCENE_PAGE;
  renderScenes();
}
function renderScenes(){
  if(!sceneGrid||!sceneRows)return;
  if(sceneTabs){
    const counts=new Map();
    sceneRows.forEach((row)=>{const region=themeRegionByIso.get(row.country.iso2);if(region)counts.set(region,(counts.get(region)||0)+1);});
    if(themeRegions.length&&counts.size>1){
      sceneTabs.hidden=false;
      const options=[{id:'all',label:'すべて'},...themeRegions.filter((region)=>counts.has(region.id))];
      sceneTabs.replaceChildren(...options.map(({id,label})=>{
        const button=document.createElement('button');
        button.type='button';
        button.dataset.sceneRegion=id;
        const on=id===sceneRegion;
        button.classList.toggle('is-active',on);
        button.setAttribute('aria-pressed',String(on));
        button.textContent=label;
        return button;
      }));
    }
  }
  const fragment=document.createDocumentFragment();
  sceneOrder.slice(0,sceneLimit).forEach((row)=>{
    const tile=document.createElement('a');
    tile.className='gallery-tile';
    tile.href=`${row.country.href}#${encodeURIComponent(row.id)}`;
    tile.setAttribute('role','listitem');
    tile.setAttribute('aria-label',`${row.name}（${row.country.nameJa}）のページを見る`);
    const img=document.createElement('img');
    img.src=`assets/images/top/scenes/${row.slug}/${row.id}.webp`;
    img.alt='';
    img.width=480;img.height=320;
    img.loading='lazy';img.decoding='async';
    const caption=document.createElement('span');
    caption.className='gallery-tile__caption';
    const name=document.createElement('b');
    name.textContent=row.name;
    const country=document.createElement('small');
    country.textContent=`${row.country.flag||''} ${row.country.nameJa}`.trim();
    caption.append(name,country);
    tile.append(img,caption);
    fragment.append(tile);
  });
  sceneGrid.replaceChildren(fragment);
  if(sceneMore){
    const remaining=sceneOrder.length-Math.min(sceneLimit,sceneOrder.length);
    sceneMore.hidden=remaining<=0;
    sceneMore.textContent='もっと見る';
  }
  // Like the other lists: a 解除 button while a region is chosen, and 「一覧を閉じる」 at the end
  // once the gallery has been opened out (もっと見る) or narrowed to a region.
  const clear=document.querySelector('#gallery-clear');
  if(clear)clear.hidden=sceneRegion==='all';
  const close=document.querySelector('#gallery-close');
  if(close)close.hidden=sceneRegion==='all'&&sceneLimit<=SCENE_PAGE;
}
function resetScenes({scroll=false}={}){
  sceneRegion='all';
  shuffleScenes();
  if(scroll){
    const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    document.querySelector('#scenery')?.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'});
  }
}
document.querySelector('#gallery-clear')?.addEventListener('click',()=>{
  resetScenes();
  document.querySelector('#gallery-shuffle')?.focus({preventScroll:true});
});
document.querySelector('#gallery-close')?.addEventListener('click',()=>resetScenes({scroll:true}));
sceneTabs?.addEventListener('click',(event)=>{
  const button=event.target.closest('[data-scene-region]');
  if(!button)return;
  sceneRegion=button.dataset.sceneRegion;
  shuffleScenes();
});
sceneShuffle?.addEventListener('click',()=>{loadScenes().then(shuffleScenes);});
sceneMore?.addEventListener('click',()=>{
  const before=sceneGrid?.children.length||0;
  sceneLimit+=SCENE_PAGE;
  renderScenes();
  sceneGrid?.children[before]?.focus({preventScroll:true});
});
{
  const panel=document.querySelector('#scenery');
  if(location.hash==='#scenery'||!panel||!('IntersectionObserver' in window))loadScenes();
  else{
    const observer=new IntersectionObserver((entries)=>{
      if(entries.some((entry)=>entry.isIntersecting)){observer.disconnect();loadScenes();}
    },{rootMargin:'800px 0px'});
    observer.observe(panel);
    ['pointerdown','focusin'].forEach((type)=>panel.addEventListener(type,()=>{loadScenes();},{once:true,passive:true}));
  }
}

// ---------------------------------------------------------------------------
// 索引: page numbers beside the names in the A–Z list. Page order comes from atlas-order.js and is
// the order Country pages turn in (the map's country list is grouped by the same chapters).
// ---------------------------------------------------------------------------
var atlasBook=null;   // var: renderGrid → addFolios may run before this line on a fast load
function bookEl(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;}
function addFolios(){
  if(!atlasBook||!grid)return;
  grid.querySelectorAll('.country-card[data-slug]').forEach((card)=>{
    const page=atlasBook.bySlug.get(card.dataset.slug);
    const body=card.querySelector('.country-card__body');
    if(!page||!body||body.querySelector('.country-card__folio'))return;
    const folio=bookEl('span','country-card__folio',`p.${page.folio}`);
    folio.setAttribute('aria-label',`${page.folio}ページ`);
    body.querySelector('h3')?.after(folio);
  });
}
(window.JourneyAtlasOrder?window.JourneyAtlasOrder.load():Promise.reject(new Error('atlas-order.js missing')))
  .then((book)=>{atlasBook=book;addFolios();})
  .catch((error)=>{
    console.warn('[JOURNEY ATLAS] Book order unavailable.',error);
  });

// "ランダムに旅先を選ぶ": open one published Country at random, skipping ones already marked as visited.
document.querySelector('#random-country')?.addEventListener('click',()=>{
  const visited=(slug)=>{try{return localStorage.getItem(`journey-atlas:visited:${slug}`)==='true';}catch{return false;}};
  const open=destinations.filter((country)=>country.atlasPublished&&country.href);
  const pool=open.filter((country)=>!visited(country.slug));
  const list=pool.length?pool:open;
  if(!list.length)return;
  location.href=list[Math.floor(Math.random()*list.length)].href;
});
