/* JOURNEY ATLAS — turns わたしの地図 into one PNG, entirely in this browser.
   Geometry comes from the map already built by map-regions.js; nothing is uploaded. */
(() => {
  'use strict';
  const WIDTH = 1600, HEIGHT = 924, MAP_X = 40, MAP_Y = 40, MAP_SCALE = 1.52;
  const MAP_HEIGHT = 507.209 * MAP_SCALE;
  const SMALL = 4.5, DOT = 3.1; // World units: markers keep tiny Countries visible.
  const INK = {
    paper: '#faf9f4', ocean: '#edf6f3', navy: '#173b5d', muted: '#5f6f7b', line: '#d9dcd6',
    land: '#dde3e3', outside: '#e6ebe7', visited: '#234866', wished: '#c9824f', border: '#fffaf1'
  };
  const FONT = {
    label: '500 19px "Zen Kaku Gothic New",sans-serif',
    labelStrong: '700 21px "Zen Kaku Gothic New",sans-serif'
  };
  const make = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const flag = key => { try { return localStorage.getItem(key) === 'true'; } catch { return false; } };

  function shapePath(element) {
    const path = new Path2D();
    const tag = element.tagName.toLowerCase();
    if (tag === 'path') path.addPath(new Path2D(element.getAttribute('d') || ''));
    else if (tag === 'circle') {
      const r = +element.getAttribute('r') || 0;
      path.arc(+element.getAttribute('cx') || 0, +element.getAttribute('cy') || 0, r, 0, Math.PI * 2);
    } else return null;
    return path;
  }
  function drawCountry(ctx, group, fill, opacity = 1) {
    ctx.globalAlpha = opacity;
    ctx.fillStyle = fill;
    group.querySelectorAll('path,circle').forEach(element => {
      const path = shapePath(element);
      if (!path) return;
      ctx.fill(path, 'evenodd');
      ctx.stroke(path);
    });
    ctx.globalAlpha = 1;
  }
  function drawMarker(ctx, group, fill) {
    let box;
    try { box = group.getBBox(); } catch { return; }
    if (Math.max(box.width, box.height) >= SMALL) return;
    ctx.beginPath();
    ctx.arc(box.x + box.width / 2, box.y + box.height / 2, DOT, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.lineWidth = .9;
    ctx.strokeStyle = INK.paper;
    ctx.stroke();
  }
  // 'both' matches the map: a visited Country is navy even if it is also wished.
  function paintFor(data, country, mode) {
    if (mode === 'wished') return data.isWished(country) ? INK.wished : INK.land;
    if (data.isVisited(country)) return INK.visited;
    return mode === 'both' && data.isWished(country) ? INK.wished : INK.land;
  }
  function legendItem(ctx, x, y, fill, text) {
    ctx.fillStyle = fill;
    ctx.beginPath();
    ctx.roundRect(x, y - 15, 24, 18, 3);
    ctx.fill();
    ctx.fillStyle = INK.muted;
    ctx.font = FONT.label;
    ctx.fillText(text, x + 33, y);
    return x + 33 + ctx.measureText(text).width + 30;
  }
  function render(data, mode) {
    const canvas = document.createElement('canvas');
    canvas.width = WIDTH;
    canvas.height = HEIGHT;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = INK.paper;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    ctx.textBaseline = 'alphabetic';

    const parents = data.countries.filter(country => !data.isDetail(country));

    ctx.save();
    ctx.beginPath();
    ctx.roundRect(MAP_X, MAP_Y, WIDTH - MAP_X * 2, MAP_HEIGHT, 10);
    ctx.clip();
    ctx.fillStyle = INK.ocean;
    ctx.fillRect(MAP_X, MAP_Y, WIDTH - MAP_X * 2, MAP_HEIGHT);
    ctx.translate(MAP_X, MAP_Y);
    ctx.scale(MAP_SCALE, MAP_SCALE);
    ctx.lineWidth = .4;
    ctx.lineJoin = 'round';
    ctx.strokeStyle = INK.border;
    const markers = [];
    data.land.querySelectorAll('.ja-country').forEach(group => {
      const country = data.byIso.get(group.dataset.iso);
      if (!country) { drawCountry(ctx, group, INK.outside); return; }
      const fill = paintFor(data, country, mode);
      drawCountry(ctx, group, fill);
      if (fill !== INK.land) markers.push([group, fill]);
    });
    markers.forEach(([group, fill]) => drawMarker(ctx, group, fill));
    ctx.restore();

    const footerY = MAP_Y + MAP_HEIGHT;
    let x = 48;
    if (mode !== 'wished') x = legendItem(ctx, x, footerY + 42, INK.visited, '行った');
    if (mode !== 'visited') legendItem(ctx, x, footerY + 42, INK.wished, '行きたい');

    // The world total and each region share one evenly spaced row.
    const counted = mode === 'wished' ? data.isWished : data.isVisited;
    const stats = [{label: '世界', items: parents}, ...data.regions.map(region => ({
      label: region.label,
      items: parents.filter(country => region.iso2.includes(country.iso2))
    }))].map(({label, items}) => {
      const value = items.filter(counted).length + ' / ' + items.length;
      ctx.font = FONT.label;
      const labelWidth = ctx.measureText(label).width;
      ctx.font = FONT.labelStrong;
      return {label, value, labelWidth, width: labelWidth + 10 + ctx.measureText(value).width};
    });
    const gap = (WIDTH - 96 - stats.reduce((sum, stat) => sum + stat.width, 0)) / (stats.length - 1);
    let left = 48;
    stats.forEach(stat => {
      ctx.fillStyle = INK.muted;
      ctx.font = FONT.label;
      ctx.fillText(stat.label, left, footerY + 82);
      ctx.fillStyle = INK.navy;
      ctx.font = FONT.labelStrong;
      ctx.fillText(stat.value, left + stat.labelWidth + 10, footerY + 82);
      left += stat.width + gap;
    });
    return canvas;
  }
  const loadFonts = () => {
    if (!document.fonts?.load) return Promise.resolve();
    const fonts = [
      document.fonts.load(FONT.label, '行った行きたい世界アジアヨーロッパフリカ北米南オセニ極'),
      document.fonts.load(FONT.labelStrong, '0123456789 /')
    ];
    return Promise.race([Promise.allSettled(fonts), new Promise(done => setTimeout(done, 2500))]);
  };

  let dialog, preview, note, saveButton, shareButton, data, file, objectUrl, mode = 'both';
  const toFile = canvas => new Promise((resolve, reject) => canvas.toBlob(blob => {
    if (blob) resolve(new File([blob], 'journey-atlas-my-map.png', {type: 'image/png'}));
    else reject(Error('PNG unavailable'));
  }, 'image/png'));
  const canShareFile = candidate => {
    try { return !!navigator.canShare?.({files: [candidate]}) && !!navigator.share; }
    catch { return false; }
  };
  function setBusy(busy) { saveButton.disabled = busy; shareButton.disabled = busy; }
  async function refresh() {
    setBusy(true);
    const painted = data.countries.filter(country => paintFor(data, country, mode) !== INK.land).length;
    if (!painted) {
      preview.hidden = true;
      saveButton.hidden = shareButton.hidden = true;
      note.textContent = mode === 'wished'
        ? '行きたい国を登録すると、塗られた世界地図を画像にできます。'
        : '行った国・地域を登録すると、塗られた世界地図を画像にできます。';
      return;
    }
    saveButton.hidden = false;
    note.textContent = '画像はこのブラウザの中で作られ、送信されません。';
    try {
      file = await toFile(render(data, mode));
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = URL.createObjectURL(file);
      preview.src = objectUrl;
      preview.alt = '塗った世界地図の画像。国・地域数は' + painted + '件。';
      preview.hidden = false;
      shareButton.hidden = !canShareFile(file);
      setBusy(false);
    } catch { note.textContent = '画像を作成できませんでした。'; }
  }
  function save() {
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = file.name;
    document.body.append(link);
    link.click();
    link.remove();
    note.textContent = '画像を保存しました。';
  }
  async function share() {
    const count = data.countries.filter(country => !data.isDetail(country) && (mode === 'wished' ? data.isWished : data.isVisited)(country)).length;
    const total = data.countries.filter(country => !data.isDetail(country)).length;
    const label = mode === 'wished' ? '行きたい国・地域' : '行った国・地域';
    try {
      await navigator.share({
        files: [file],
        text: `${label}は ${count} / ${total}。JOURNEY ATLASのわたしの地図より https://atlas.yagenji.com/`
      });
    } catch (error) {
      if (error?.name !== 'AbortError') note.textContent = '共有できませんでした。画像を保存してお使いください。';
    }
  }
  function ensureDialog() {
    if (dialog) return;
    dialog = make('dialog', 'ja-share');
    dialog.setAttribute('aria-labelledby', 'ja-share-title');
    const head = make('div', 'ja-share__head');
    const title = make('h2', '', 'わたしの地図を画像にする');
    title.id = 'ja-share-title';
    const close = make('button', 'ja-share__close', '閉じる');
    close.type = 'button';
    close.addEventListener('click', () => dialog.close());
    head.append(title, close);
    preview = make('img', 'ja-share__preview');
    preview.hidden = true;
    const actions = make('div', 'ja-share__actions');
    saveButton = make('button', 'ja-tool-button', '画像を保存');
    saveButton.type = 'button';
    saveButton.addEventListener('click', save);
    shareButton = make('button', 'ja-tool-button', '共有する');
    shareButton.type = 'button';
    shareButton.addEventListener('click', share);
    actions.append(saveButton, shareButton);
    note = make('p', 'ja-share__note');
    note.setAttribute('role', 'status');
    dialog.append(head, preview, actions, note);
    dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
    document.body.append(dialog);
  }
  async function open(nextMode = 'both') {
    mode = nextMode;
    ensureDialog();
    if (!dialog.open) dialog.showModal();
    preview.hidden = true;
    saveButton.hidden = shareButton.hidden = true;
    note.textContent = '画像を作成しています…';
    try {
      const [map] = await Promise.all([window.JourneyAtlasWorldMap.load(), loadFonts()]);
      data = {
        ...map,
        isVisited: country => flag('journey-atlas:visited:' + country.slug),
        isWished: country => flag('journey-atlas:wish:' + country.slug)
      };
      await refresh();
    } catch { note.textContent = '地図を読み込めませんでした。時間をおいてお試しください。'; }
  }
  window.JourneyAtlasMapShare = {open};
})();
