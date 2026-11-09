// 景色を流す — a full-screen, lean-back slideshow of the 景色から探す gallery.
// It plays the gallery's current order, so the region / Wish / type / saved filters carry over.
(() => {
  'use strict';
  const button = document.querySelector('#gallery-view');
  if (!button) return;

  const INTERVALS = [5, 10, 15, 30, 60];
  const STORE = 'journey-atlas:view-interval';
  const FADE = 1200;
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)');
  let rows = [], at = 0, timer = 0, hideTimer = 0, playing = true, opener = null, front = 0, touchX = null;
  let seconds = 10;
  try { const saved = Number(localStorage.getItem(STORE)); if (INTERVALS.includes(saved)) seconds = saved; } catch { /* storage unavailable */ }

  const make = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  };
  const iconButton = (label, text, className = '') => {
    const element = make('button', `sv-btn ${className}`.trim(), text);
    element.type = 'button';
    element.setAttribute('aria-label', label);
    element.title = label;
    return element;
  };

  // Build once, on first open.
  let root, layers, place, country, prevBtn, playBtn, nextBtn, pageLink, fullBtn, closeBtn, speed, live;
  function build() {
    root = make('div', 'sv');
    root.setAttribute('role', 'dialog');
    root.setAttribute('aria-modal', 'true');
    root.setAttribute('aria-label', '景色を流す');
    root.hidden = true;
    const stage = make('div', 'sv-stage');
    layers = [make('img', 'sv-img'), make('img', 'sv-img')];
    layers.forEach((img) => { img.alt = ''; img.decoding = 'async'; stage.append(img); });
    const caption = make('div', 'sv-cap');
    place = make('p', 'sv-place');
    country = make('p', 'sv-country');
    caption.append(place, country);
    live = make('p', 'sv-live');
    live.setAttribute('aria-live', 'polite');

    const bar = make('div', 'sv-ui');
    prevBtn = iconButton('前の景色', '‹');
    playBtn = iconButton('一時停止', '❚❚', 'sv-play');
    nextBtn = iconButton('次の景色', '›');
    speed = make('div', 'sv-speed');
    speed.setAttribute('role', 'group');
    speed.setAttribute('aria-label', '切り替えの間隔');
    INTERVALS.forEach((value) => {
      const option = make('button', 'sv-speed__opt', `${value}秒`);
      option.type = 'button';
      option.dataset.seconds = String(value);
      speed.append(option);
    });
    pageLink = make('a', 'sv-link', 'このページを見る');
    const note = make('span', 'sv-note', '景観イメージ');
    fullBtn = iconButton('全画面', '⛶');
    fullBtn.hidden = !document.fullscreenEnabled;
    closeBtn = iconButton('閉じる', '✕', 'sv-close');
    bar.append(prevBtn, playBtn, nextBtn, make('span', 'sv-sep'), speed, make('span', 'sv-sep'), pageLink, note);
    const top = make('div', 'sv-top');
    top.append(fullBtn, closeBtn);
    root.append(stage, caption, bar, top, live);
    // Keep the caption just above the control bar, however many rows the bar wraps to.
    const placeCaption = () => caption.style.setProperty('--sv-bar', `${bar.offsetHeight}px`);
    if ('ResizeObserver' in window) new ResizeObserver(placeCaption).observe(bar);
    window.addEventListener('resize', placeCaption);
    document.body.append(root);

    prevBtn.addEventListener('click', () => step(-1));
    nextBtn.addEventListener('click', () => step(1));
    playBtn.addEventListener('click', () => setPlaying(!playing));
    closeBtn.addEventListener('click', close);
    fullBtn.addEventListener('click', toggleFullscreen);
    speed.addEventListener('click', (event) => {
      const option = event.target.closest('[data-seconds]');
      if (!option) return;
      seconds = Number(option.dataset.seconds);
      try { localStorage.setItem(STORE, String(seconds)); } catch { /* storage unavailable */ }
      renderSpeed();
      schedule();
    });
    // Tap the picture to show / hide the controls; swipe to move.
    stage.addEventListener('click', () => root.classList.toggle('is-idle'));
    root.addEventListener('pointermove', (event) => { if (event.pointerType === 'mouse') wake(); });
    root.addEventListener('touchstart', (event) => { touchX = event.touches[0].clientX; }, {passive: true});
    root.addEventListener('touchend', (event) => {
      if (touchX === null) return;
      const dx = event.changedTouches[0].clientX - touchX;
      touchX = null;
      if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
    });
    root.addEventListener('keydown', onKey);
    document.addEventListener('fullscreenchange', () => {
      const on = document.fullscreenElement === root;
      fullBtn.setAttribute('aria-label', on ? '全画面を終了' : '全画面');
      fullBtn.title = on ? '全画面を終了' : '全画面';
    });
    document.addEventListener('visibilitychange', () => {
      if (root.hidden) return;
      if (document.hidden) clearTimeout(timer); else schedule();
    });
  }

  function renderSpeed() {
    speed.querySelectorAll('[data-seconds]').forEach((option) => {
      option.setAttribute('aria-pressed', String(Number(option.dataset.seconds) === seconds));
    });
  }
  function src(row) { return row.full; }
  function show(index, first = false) {
    at = (index + rows.length) % rows.length;
    const row = rows[at];
    const next = layers[1 - front];
    const reveal = () => {
      next.classList.add('is-on');
      layers[front].classList.remove('is-on');
      front = 1 - front;
    };
    next.onload = reveal;
    next.onerror = () => { if (rows.length > 1) step(1); };
    next.src = src(row);
    if (next.complete && next.naturalWidth) { next.onload = null; reveal(); }
    place.textContent = row.name;
    country.replaceChildren();
    if (row.country.flagAsset) {
      const flag = make('img', 'sv-flag');
      flag.src = row.country.flagAsset; flag.alt = ''; flag.width = 16; flag.height = 16;
      country.append(flag, document.createTextNode(row.country.nameJa));
    } else {
      country.textContent = `${row.country.flag || ''} ${row.country.nameJa}`.trim();
    }
    pageLink.href = `${row.country.href}#${row.isHero ? 'hero-caption' : encodeURIComponent(row.id)}`;
    live.textContent = first ? '' : `${row.name}、${row.country.nameJa}`;
    // Fetch the following picture early so the next change is a clean fade.
    const after = rows[(at + 1) % rows.length];
    if (after) { const preload = new Image(); preload.decoding = 'async'; preload.src = src(after); }
    schedule();
  }
  function step(delta) { if (rows.length) show(at + delta); }
  function schedule() {
    clearTimeout(timer);
    if (playing && rows.length > 1 && !root.hidden) timer = setTimeout(() => step(1), seconds * 1000);
  }
  function setPlaying(on) {
    playing = on;
    playBtn.textContent = on ? '❚❚' : '▶';
    playBtn.setAttribute('aria-label', on ? '一時停止' : '再生');
    playBtn.title = on ? '一時停止' : '再生';
    schedule();
  }
  function wake() {
    root.classList.remove('is-idle');
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => { if (!root.contains(document.activeElement) || document.activeElement === root) root.classList.add('is-idle'); }, 3000);
  }
  function toggleFullscreen() {
    if (document.fullscreenElement) document.exitFullscreen?.();
    else root.requestFullscreen?.().catch(() => {});
  }
  function onKey(event) {
    if (event.key === 'Escape' && !document.fullscreenElement) { event.preventDefault(); close(); return; }
    if (event.key === 'ArrowRight') { step(1); wake(); }
    else if (event.key === 'ArrowLeft') { step(-1); wake(); }
    else if (event.key === ' ' && !event.target.closest('button, a')) { event.preventDefault(); setPlaying(!playing); wake(); }
    else if (event.key === 'f' || event.key === 'F') toggleFullscreen();
    else if (event.key === 'Tab') {
      // Keep focus inside the viewer while it is open.
      const focusable = [...root.querySelectorAll('button:not([hidden]), a[href]')].filter((el) => el.offsetParent !== null);
      if (!focusable.length) return;
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      wake();
    }
  }

  async function open() {
    const gallery = window.journeyAtlasSceneView;
    if (!gallery) return;
    await gallery.load();
    rows = gallery.rows();
    if (!rows.length) return;
    if (!root) build();
    opener = document.activeElement;
    root.classList.toggle('is-still', !!reduceMotion?.matches);
    root.style.setProperty('--sv-fade', `${reduceMotion?.matches ? 0 : FADE}ms`);
    layers.forEach((img) => { img.classList.remove('is-on'); img.removeAttribute('src'); });
    root.hidden = false;
    document.documentElement.classList.add('sv-open');
    renderSpeed();
    setPlaying(true);
    show(0, true);
    closeBtn.focus({preventScroll: true});
    wake();
  }
  function close() {
    if (!root || root.hidden) return;
    clearTimeout(timer); clearTimeout(hideTimer);
    if (document.fullscreenElement) document.exitFullscreen?.();
    root.hidden = true;
    document.documentElement.classList.remove('sv-open');
    (opener || button).focus?.({preventScroll: true});
  }

  button.addEventListener('click', open);
})();
