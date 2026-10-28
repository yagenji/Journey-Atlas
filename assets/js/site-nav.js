// Shared header menu (Country pages, About, FAQ, Privacy): 「旅先を探す」 opens the five ways to
// search on the top page. Uses event delegation because Country pages render their header from a
// <template> after the data loads. Closes on outside click, Escape or choosing a link.
(()=>{
  const setOpen=(wrap,open)=>{
    wrap.classList.toggle('is-open',open);
    wrap.querySelector('.site-explore__toggle')?.setAttribute('aria-expanded',String(open));
  };
  const closeAll=(except)=>document.querySelectorAll('.site-explore.is-open').forEach((wrap)=>{if(wrap!==except)setOpen(wrap,false);});
  document.addEventListener('click',(event)=>{
    const toggle=event.target.closest('.site-explore__toggle');
    if(toggle){
      const wrap=toggle.closest('.site-explore');
      closeAll(wrap);
      setOpen(wrap,!wrap.classList.contains('is-open'));
      return;
    }
    const wrap=event.target.closest('.site-explore');
    if(wrap&&event.target.closest('a')){setOpen(wrap,false);return;}
    if(!wrap)closeAll();
  });
  document.addEventListener('keydown',(event)=>{
    if(event.key!=='Escape')return;
    const open=document.querySelector('.site-explore.is-open');
    if(open){setOpen(open,false);open.querySelector('.site-explore__toggle')?.focus();}
  });
  document.addEventListener('focusin',(event)=>{if(!event.target.closest('.site-explore'))closeAll();});
})();
