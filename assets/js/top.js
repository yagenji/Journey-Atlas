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
const heroImage = document.querySelector('#hero-image');
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
let themeMeta = {};
let heroSources = [];
let heroIndex = 0;
let heroTimer;
let themeSets = {};

const heroFiles = [
  'assets/images/top/hero-world-collage.svg',
  'assets/images/top/hero-set-1.webp',
  'assets/images/top/hero-set-2.webp',
  'assets/images/top/hero-set-3.webp',
  'assets/images/top/hero-set-4.webp',
  'assets/images/top/hero-set-5.webp'
];
const featuredArt = {
  antarctica:{x:'0%',y:'0%'},
  turkiye:{x:'50%',y:'0%'},
  italy:{x:'100%',y:'0%'},
  maldives:{x:'0%',y:'100%'},
  peru:{x:'50%',y:'100%'},
  kenya:{x:'100%',y:'100%'}
};

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
      button.type='button';button.dataset.hero=String(i);button.setAttribute('aria-label',`ビジュアル${i+1}`);
      if(i===0)button.classList.add('is-active');
      return button;
    }));
    heroButtons.splice(0,heroButtons.length,...controls.querySelectorAll('[data-hero]'));
  }
}
setHero(0,false);
applyHeroDerivedArt();
if(destinations.length){renderRail(destinations);renderGrid(destinations);}
startHeroRotation();

function setHero(index,animate=true){
  if(!heroImage || heroSources.length===0) return;
  heroIndex=(index+heroSources.length)%heroSources.length;
  if(animate) heroVisual?.classList.add('is-changing');
  window.setTimeout(()=>{
    heroImage.src=heroSources[heroIndex];
    heroButtons.forEach((button,i)=>button.classList.toggle('is-active',i===heroIndex));
    heroImage.onload=()=>heroVisual?.classList.remove('is-changing');
  },animate?130:0);
}
function startHeroRotation(){
  window.clearInterval(heroTimer);
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  heroTimer=window.setInterval(()=>setHero(heroIndex+1),9000);
}
function applyHeroDerivedArt(){
  const cards=[
    document.querySelector('.explore-card--country .explore-card__art'),
    document.querySelector('.explore-card--map .explore-card__art'),
    document.querySelector('.explore-card--theme .explore-card__art')
  ];
  const positions=['0% 50%','50% 50%','100% 50%'];

  if(!document.querySelector('#explore-entry-style')){
    const style=document.createElement('style');
    style.id='explore-entry-style';
    style.textContent=`
      .explore-card__art{height:186px;background-image:none;background-color:#eef3f0;background-repeat:no-repeat;background-size:300% 100%;filter:contrast(1.02) saturate(.98)}
      .explore-card__copy{min-height:92px;padding:14px 16px 15px}
      .explore-card{border-radius:13px;overflow:hidden}
      @media(max-width:1050px){.explore-card__art{height:160px}}
      @media(max-width:760px){.explore-card__art{height:100%;min-height:126px;background-size:300% 100%}.explore-card__copy{min-height:126px}}
    `;
    document.head.append(style);
  }

  {
    const image='url("assets/images/top/explore-entry-sprite.webp")';
    cards.forEach((art,index)=>{
      if(!art)return;
      art.style.backgroundImage=image;
      art.style.backgroundSize='300% 100%';
      art.style.backgroundPosition=positions[index];
      art.style.backgroundRepeat='no-repeat';
    });
  }
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
coreRegistryPromise
  .then((core)=>{
    destinations=sortForDisplay(core.destinations||[]);
    if(count) count.textContent=`${destinations.length} DESTINATIONS`;
    renderRail(destinations);renderGrid(destinations);
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

// LENS mark: the live JOURNEY LENS feed is the source of truth (the registry flag is only the
// fallback while the feed loads or if it is unreachable), so new LENS countries appear automatically.
const LENS_MARK='<span class="country-card__lens" title="JOURNEY LENSに旅の記事があります">LENS</span>';
let lensSlugs=null;
function hasLens(country){return lensSlugs?lensSlugs.has(country.slug):Boolean(country.journeyLensPublished);}
function refreshLensMarks(){
  document.querySelectorAll('.country-card[data-slug]').forEach((card)=>{
    const country=destinations.find((item)=>item.slug===card.dataset.slug);
    const body=card.querySelector('.country-card__body');
    if(!country||!body)return;
    const mark=body.querySelector('.country-card__lens');
    if(hasLens(country)&&!mark)body.querySelector('p')?.insertAdjacentHTML('afterend',LENS_MARK);
    if(!hasLens(country)&&mark)mark.remove();
  });
}
function renderLensRail(registryItems,rssText){
  if(!lensRail)return;
  const registryBySlug=new Map(registryItems.map((item)=>[item.slug,item]));
  const parsedEntries=parseLensFeed(rssText);
  if(parsedEntries.length){lensSlugs=new Set(parsedEntries.map((entry)=>entry.slug));refreshLensMarks();}
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
function createCard(country,index,compact=false){
  const card=document.createElement(country.atlasPublished&&country.href?'a':'article');
  card.className=`country-card${country.atlasPublished?' is-open':' is-closed'}`;
  card.dataset.slug=country.slug;card.dataset.name=`${country.nameEn} ${country.nameJa}`.toLowerCase();
  if(country.atlasPublished&&country.href){card.href=country.href;card.setAttribute('aria-label',`${country.nameJa}のJOURNEY ATLASを見る`);}
  const art=document.createElement('div');art.className='country-card__art';art.style.setProperty('--hue',String(hueFor(country,index)));
  const featured=featuredArt[country.slug];
  if(featured&&heroSources[0]){
    art.style.backgroundImage=`url("${heroSources[0]}")`;
    art.style.backgroundPosition=`${featured.x} ${featured.y}`;
    art.style.backgroundSize='205% 205%';
    art.classList.add('has-image');
  }else if(country.image){art.style.backgroundImage=`url("${country.image}")`;art.classList.add('has-image');}
  art.innerHTML=`<span class="country-card__flag" aria-hidden="true">${country.flag}</span>`;
  const body=document.createElement('div');body.className='country-card__body';
  body.innerHTML=`<h3>${country.nameEn}</h3><p>${country.nameJa}</p>${hasLens(country)?LENS_MARK:''}${country.atlasPublished?'<span class="country-card__open" aria-hidden="true">›</span>':''}`;
  if(hasLens(country)&&card.hasAttribute('aria-label'))card.setAttribute('aria-label',`${country.nameJa}のJOURNEY ATLASを見る（JOURNEY LENSの記事あり）`);
  card.append(art,body);return card;
}
function renderRail(items){if(!rail)return;const fragment=document.createDocumentFragment();items.forEach((country,index)=>fragment.append(createCard(country,index)));rail.replaceChildren(fragment);updateDots();}
function renderGrid(items,captions=null){if(!grid)return;const fragment=document.createDocumentFragment();items.forEach((country,index)=>{const card=createCard(country,index,true);const note=captions?.get(country.slug);if(note){const small=document.createElement('small');small.className='country-card__match';small.textContent=note;card.querySelector('.country-card__body')?.append(small);}fragment.append(card);});grid.replaceChildren(fragment);if(empty)empty.hidden=items.length!==0;}
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

  const themeItems=getThemeItems(activeTheme);
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
    fragment.append(card);
  });
  themeResultsGrid.replaceChildren(fragment);
  renderThemeMore(items.length-shown.length);
  saveTopState();

  const label=themeLabel(activeTheme);
  if(themeResultsTitle)themeResultsTitle.textContent=label;
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
  activeThemeRegion='all';
  activeTheme=null;
  renderThemeResults();
  saveTopState();
}
function setAllPanel(open,reset=true){
  if(!allPanel||!toggleAll)return;
  allPanel.hidden=!open;toggleAll.setAttribute('aria-expanded',String(open));
  toggleAll.firstChild.textContent=open?'一覧を閉じる ':'すべての国・地域を見る ';
  if(open&&reset){
    if(searchInput)searchInput.value='';document.querySelector('#countries')?.classList.remove('is-searching');if(allTitle)allTitle.textContent='すべての国・地域';
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
  if(allTitle)allTitle.textContent=searchInput.value.trim()?`「${searchInput.value.trim()}」の検索結果 ${items.length}件`:'すべての国・地域';
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
wishButton?.addEventListener('click',()=>{const wished=getWishedSlugs();if(wished.length===0){showToast('行ってみたい国はまだ保存されていません。国ページから追加できます。');return;}setAllPanel(true,false);if(searchInput)searchInput.value='';document.querySelector('#countries')?.classList.remove('is-searching');if(allTitle)allTitle.textContent='すべての国・地域';renderGrid(destinations.filter((country)=>wished.includes(country.slug)));showToast(`${wished.length}件の行ってみたい国を表示しています。`);});
document.querySelectorAll('[data-country-focus]').forEach((button)=>button.addEventListener('click',()=>focusCountry(button.dataset.countryFocus)));
document.querySelectorAll('[data-theme]').forEach((button)=>button.addEventListener('click',()=>showTheme(button.dataset.theme)));
document.querySelector('[data-open-all]')?.addEventListener('click',()=>setAllPanel(true));
document.addEventListener('click',(event)=>{
  const button=event.target.closest('[data-letter]');if(!button)return;
  alphabetButtons().forEach((item)=>item.classList.toggle('is-active',item===button));
  const letter=button.dataset.letter;
  const filtered=letter==='all'?destinations:letter==='#'?destinations.filter((country)=>!/[A-Z]/.test(country.nameEn[0])):destinations.filter((country)=>country.nameEn.startsWith(letter));
  setAllPanel(true,false);
  if(searchInput)searchInput.value='';document.querySelector('#countries')?.classList.remove('is-searching');if(allTitle)allTitle.textContent='すべての国・地域';
  renderGrid(filtered);
});

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
      note.textContent=`おすすめ ${window_[1]}`;
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

// "ランダムに旅先を選ぶ": open one published Country at random, skipping ones already marked as visited.
document.querySelector('#random-country')?.addEventListener('click',()=>{
  const visited=(slug)=>{try{return localStorage.getItem(`journey-atlas:visited:${slug}`)==='true';}catch{return false;}};
  const open=destinations.filter((country)=>country.atlasPublished&&country.href);
  const pool=open.filter((country)=>!visited(country.slug));
  const list=pool.length?pool:open;
  if(!list.length)return;
  location.href=list[Math.floor(Math.random()*list.length)].href;
});
