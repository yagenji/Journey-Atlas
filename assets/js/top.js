const rail = document.querySelector('#country-rail');
const grid = document.querySelector('#country-grid');
const count = document.querySelector('#country-count');
const prev = document.querySelector('[data-country-scroll="prev"]');
const next = document.querySelector('[data-country-scroll="next"]');
const toggleAll = document.querySelector('#all-countries-toggle');
const allPanel = document.querySelector('#all-countries-panel');
const searchInput = document.querySelector('#country-search');
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
const LENS_RSS_URL = 'https://journey.yagenji.com/rss.xml';
const LENS_LINK_PATTERN = /^https:\/\/journey\.yagenji\.com\/([a-z]+)(\d+)\/$/;
const ATLAS_TOTAL = 201;

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
let heroSources = [];
let heroIndex = 0;
let heroTimer;
let themeSets = {
  earth:['iceland','antarctica','bolivia','namibia','newzealand','nepal'],
  city:['japan','italy','morocco','cuba','uzbekistan','mexico'],
  history:['egypt','peru','italy','cambodia','india','jordan'],
  life:['india','morocco','vietnam','mexico','ethiopia','mongolia'],
  wildlife:['kenya','tanzania','botswana','southafrica','australia','costarica'],
  sea:['maldives','belize','philippines','seychelles','fiji','palau'],
  food:['japan','italy','mexico','thailand','vietnam','turkiye'],
  road:['tajikistan','kyrgyz','argentina','chile','lesotho','iceland']
};

const heroFiles = [
  'assets/images/top/hero-world-collage.svg',
  'assets/images/top/hero-set-1.webp',
  'assets/images/top/hero-set-2.webp',
  'assets/images/top/hero-set-3.webp',
  'assets/images/top/hero-set-4.webp',
  'assets/images/top/hero-set-5.webp'
];
const featuredOrder = ['iceland','antarctica','turkiye','italy','maldives','peru','kenya'];
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

fetch('data/theme-taxonomy.json')
  .then((response)=>{if(!response.ok) throw new Error('Theme taxonomy not found');return response.json();})
  .then(({themes=[]})=>{
    if(themes.length){
      themeSets=Object.fromEntries(themes.map((theme)=>[theme.id,theme.examples||[]]));
      const buttons=[...document.querySelectorAll('.theme-icons button')];
      themes.forEach((theme,index)=>{
        const button=buttons[index];
        if(!button)return;
        button.dataset.theme=theme.id;
        const label=button.querySelector('b');
        if(label)label.textContent=theme.label;
        button.title=theme.definition;
      });
    }
    const entryCopy=document.querySelector('.explore-card--theme p');
    if(entryCopy)entryCopy.textContent='行きたい理由から、世界を選ぶ';
    const detailCopy=document.querySelector('.theme-panel .detail-heading p');
    if(detailCopy)detailCopy.textContent=`あなたが惹かれるのは、どんな旅？ ${ATLAS_TOTAL}の国・地域を、8つのテーマから見つけてみよう。`;
  })
  .catch(()=>{});

heroSources=heroFiles;
heroButtons.forEach((button,index)=>{button.hidden=index>=heroSources.length;});
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
const editorialRegistryPromise=fetch('data/atlas-destinations-editorial.json')
  .then((response)=>{if(!response.ok) throw new Error('Editorial destination registry not found');return response.json();});

Promise.all([coreRegistryPromise,editorialRegistryPromise])
  .then(([core, editorial])=>{
    const items=[...(core.destinations||[]),...(editorial.destinations||[])];
    destinations=sortForDisplay(items);
    if(count) count.textContent=`${destinations.length} DESTINATIONS`;
    renderRail(destinations);renderGrid(destinations);
  })
  .catch(()=>{if(rail) rail.innerHTML='<p class="country-load-error">国一覧を読み込めませんでした。</p>';});

Promise.all([
  coreRegistryPromise,
  fetch(LENS_RSS_URL).then((response)=>{if(!response.ok) throw new Error('JOURNEY LENS RSS not found');return response.text();})
])
  .then(([core,rssText])=>renderLensRail(core.destinations||[],rssText))
  .catch((error)=>{
    console.warn('[JOURNEY ATLAS] JOURNEY LENS rail could not be loaded.',error);
    if(lensRail) lensRail.innerHTML='<p class="lens-rail__error">JOURNEY LENSを読み込めませんでした。</p>';
  });


function parseLensFeed(xmlText){
  const xml=new DOMParser().parseFromString(xmlText,'application/xml');
  if(xml.querySelector('parsererror')) throw new Error('Invalid JOURNEY LENS RSS XML');
  const grouped=new Map();
  [...xml.querySelectorAll('item')].forEach((item)=>{
    const link=(item.querySelector('link')?.textContent||'').trim();
    const match=link.match(LENS_LINK_PATTERN);
    if(!match){
      console.warn('[JOURNEY ATLAS] LENS article URL does not match slug+sequence convention:',link);
      return;
    }
    const slug=match[1];
    const sequence=Number(match[2]);
    const existing=grouped.get(slug);
    if(existing&&existing.sequence<=sequence)return;
    const title=(item.querySelector('title')?.textContent||'').trim();
    const titleParts=title.split('｜');
    const subtitle=titleParts.length>1?titleParts.slice(1).join('｜').trim():'';
    const image=(item.querySelector('enclosure')?.getAttribute('url')||'').trim();
    grouped.set(slug,{slug,sequence,link,subtitle,image});
  });
  return [...grouped.values()];
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
  const entries=parseLensFeed(rssText).map((entry)=>({
    ...entry,
    country:registryBySlug.get(entry.slug)||null
  }));
  entries.forEach((entry)=>{
    if(!entry.country)console.warn('[JOURNEY ATLAS] LENS slug not found in atlas-destinations.json:',entry.slug);
  });
  entries.sort((a,b)=>{
    const aOrder=a.country?.order??Number.MAX_SAFE_INTEGER;
    const bOrder=b.country?.order??Number.MAX_SAFE_INTEGER;
    if(aOrder!==bOrder)return aOrder-bOrder;
    return a.slug.localeCompare(b.slug,'en');
  });

  const track=document.createElement('div');
  track.className='lens-rail__track';
  track.setAttribute('role','list');
  entries.forEach((entry)=>track.append(createLensCard(entry,entry.country)));

  lensRail.replaceChildren(track);
  lensRail.scrollLeft=0;
  window.requestAnimationFrame(updateLensControls);
}

function sortForDisplay(items){
  const rank=new Map(featuredOrder.map((slug,index)=>[slug,index]));
  return [...items].sort((a,b)=>{
    const ar=rank.has(a.slug)?rank.get(a.slug):999;
    const br=rank.has(b.slug)?rank.get(b.slug):999;
    if(ar!==br) return ar-br;
    return a.nameEn.localeCompare(b.nameEn,'en');
  });
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
  body.innerHTML=`<h3>${country.nameEn}</h3><p>${country.nameJa}</p>${country.atlasPublished?'<span class="country-card__open" aria-hidden="true">›</span>':''}`;
  card.append(art,body);return card;
}
function renderRail(items){if(!rail)return;const fragment=document.createDocumentFragment();items.forEach((country,index)=>fragment.append(createCard(country,index)));rail.replaceChildren(fragment);updateDots();}
function renderGrid(items){if(!grid)return;const fragment=document.createDocumentFragment();items.forEach((country,index)=>fragment.append(createCard(country,index,true)));grid.replaceChildren(fragment);if(empty)empty.hidden=items.length!==0;}
function scrollRail(direction){if(!rail)return;rail.scrollBy({left:Math.max(460,rail.clientWidth*.82)*direction,behavior:'smooth'});}
function updateDots(){if(!rail||dots.length===0)return;const max=rail.scrollWidth-rail.clientWidth;const ratio=max>0?rail.scrollLeft/max:0;const index=Math.min(dots.length-1,Math.round(ratio*(dots.length-1)));dots.forEach((dot,i)=>dot.classList.toggle('is-active',i===index));}
function setAllPanel(open,reset=true){
  if(!allPanel||!toggleAll)return;
  allPanel.hidden=!open;toggleAll.setAttribute('aria-expanded',String(open));
  toggleAll.firstChild.textContent=open?'一覧を閉じる ':'すべての国・地域を見る ';
  if(open&&reset){if(searchInput)searchInput.value='';renderGrid(destinations);}
  if(open) allPanel.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function focusCountry(slug){const country=destinations.find((item)=>item.slug===slug);if(!country)return;setAllPanel(true,false);if(searchInput)searchInput.value=country.nameJa;renderGrid([country]);}
function showTheme(theme){
  const slugs=themeSets[theme]||[];
  const items=slugs.map((slug)=>destinations.find((country)=>country.slug===slug)).filter(Boolean);
  setAllPanel(true,false);if(searchInput)searchInput.value='';renderGrid(items);
  showToast(`${items.length}件の候補を表示しています。`);
}
function getWishedSlugs(){try{return destinations.filter((country)=>localStorage.getItem(`journey-atlas:wish:${country.slug}`)==='true').map((country)=>country.slug);}catch{return[];}}
let toastTimer;
function showToast(message){if(!toast)return;toast.textContent=message;toast.hidden=false;window.clearTimeout(toastTimer);toastTimer=window.setTimeout(()=>{toast.hidden=true;},2600);}

prev?.addEventListener('click',()=>scrollRail(-1));next?.addEventListener('click',()=>scrollRail(1));rail?.addEventListener('scroll',()=>window.requestAnimationFrame(updateDots),{passive:true});
toggleAll?.addEventListener('click',()=>setAllPanel(Boolean(allPanel?.hidden)));
searchInput?.addEventListener('input',()=>{const query=searchInput.value.trim().toLowerCase();renderGrid(query?destinations.filter((country)=>`${country.nameEn} ${country.nameJa}`.toLowerCase().includes(query)):destinations);});
wishButton?.addEventListener('click',()=>{const wished=getWishedSlugs();if(wished.length===0){showToast('行ってみたい国はまだ保存されていません。国ページから追加できます。');return;}setAllPanel(true,false);if(searchInput)searchInput.value='';renderGrid(destinations.filter((country)=>wished.includes(country.slug)));showToast(`${wished.length}件の行ってみたい国を表示しています。`);});
document.querySelectorAll('[data-country-focus]').forEach((button)=>button.addEventListener('click',()=>focusCountry(button.dataset.countryFocus)));
document.querySelectorAll('[data-theme]').forEach((button)=>button.addEventListener('click',()=>showTheme(button.dataset.theme)));
document.querySelector('[data-theme-open]')?.addEventListener('click',()=>{document.querySelector('#themes')?.scrollIntoView({behavior:'smooth'});});
document.querySelector('[data-open-all]')?.addEventListener('click',()=>setAllPanel(true));
document.addEventListener('click',(event)=>{
  const button=event.target.closest('[data-letter]');if(!button)return;
  alphabetButtons().forEach((item)=>item.classList.toggle('is-active',item===button));
  const letter=button.dataset.letter;
  const filtered=letter==='all'?destinations:letter==='#'?destinations.filter((country)=>!/[A-Z]/.test(country.nameEn[0])):destinations.filter((country)=>country.nameEn.startsWith(letter));
  setAllPanel(true,false);if(searchInput)searchInput.value='';renderGrid(filtered);
});