// The atlas as a book: page order shared by the top page (索引・地図の章立て) and Country pages (ページ送り).
// Chapters = regions → subregions in data/region-taxonomy.json; A–Z by English name inside a chapter.
window.JourneyAtlasOrder={
  build(taxonomy,registry){
    const byIso=new Map((registry.destinations||[]).filter((item)=>item.atlasPublished&&item.href).map((item)=>[item.iso2,item]));
    const used=new Set();
    const pages=[];
    const chapters=[];
    (taxonomy.regions||[]).forEach((region)=>{
      const groups=region.subregions?.length?region.subregions:[{id:region.id,label:region.label,iso2:region.iso2}];
      groups.forEach((group)=>{
        const items=(group.iso2||[]).map((iso)=>byIso.get(iso)).filter((item)=>item&&!used.has(item.slug))
          .sort((a,b)=>a.nameEn.localeCompare(b.nameEn,'en',{sensitivity:'base'}));
        if(!items.length)return;
        const chapter={id:group.id||region.id,label:group.label,region:region.label,regionId:region.id,first:pages.length+1,pages:[]};
        items.forEach((item,index)=>{
          used.add(item.slug);
          const page={...item,chapter,chapterIndex:index+1,folio:pages.length+1};
          pages.push(page);chapter.pages.push(page);
        });
        chapter.last=pages.length;
        chapters.push(chapter);
      });
    });
    return {pages,chapters,bySlug:new Map(pages.map((page)=>[page.slug,page]))};
  },
  load(){
    const json=(url)=>fetch(url).then((response)=>{if(!response.ok)throw new Error(url);return response.json();});
    return Promise.all([json('data/region-taxonomy.json'),json('data/atlas-destinations.json')]).then(([taxonomy,registry])=>this.build(taxonomy,registry));
  }
};
