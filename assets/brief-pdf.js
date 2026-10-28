// Génère le PDF d'un brief (mise en page magazine). Partagé entre le test Node et la page.
function buildBriefPdf(jsPDF, b){
  const MOIS = ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'];
  const JOURS = ['dimanche','lundi','mardi','mercredi','jeudi','vendredi','samedi'];
  const clean = s => String(s == null ? '' : s)
    .replace(/[‘’ʼ]/g, "'").replace(/[“”]/g, '"')
    .replace(/[–—−]/g, '-').replace(/…/g, '...')
    .replace(/[   ]/g, ' ').replace(/œ/g, 'oe').replace(/Œ/g, 'OE')
    .replace(/[^\x00-\xFF€]/g, '');
  const arr = v => Array.isArray(v) ? v.filter(x => x != null && x !== '') : (v ? [v] : []);
  const [y0, m0, d0] = String(b.date || '').split('-').map(Number);
  const dt = new Date(Date.UTC(y0, (m0 || 1) - 1, d0 || 1));
  const dateTxt = JOURS[dt.getUTCDay()] + ' ' + dt.getUTCDate() + ' ' + MOIS[dt.getUTCMonth()] + ' ' + dt.getUTCFullYear();
  const isInst = b.theme === 'Institutions' && !arr((b.pro || {}).args).length;

  const doc = new jsPDF({unit: 'mm', format: 'a4'});
  const W = 210, H = 297, ML = 16, MR = 16, TOP = 16, BOT = 18, CW = W - ML - MR;
  const C = {
    ink: [27, 36, 48], soft: [80, 92, 106], mute: [128, 139, 154], white: [255, 255, 255],
    navy: [26, 43, 66], navySoft: [176, 196, 222], acc: [46, 92, 138],
    wash: [238, 241, 245], blueBg: [231, 238, 247],
    pro: [38, 112, 82], proBg: [226, 242, 234], con: [168, 78, 52], conBg: [250, 233, 226],
    sand: [246, 241, 230], sandInk: [140, 104, 40]
  };
  const PT = 0.3528;
  const lh = size => size * PT * 1.42;
  let yy = TOP;
  const font = (f, s, size, c) => { doc.setFont(f, s); doc.setFontSize(size); doc.setTextColor(c[0], c[1], c[2]); };
  const fill = c => doc.setFillColor(c[0], c[1], c[2]);

  // Rows : unités insécables de hauteur connue, dessinées à (x, y) dans une colonne de largeur w
  function textRows(text, o){
    o = o || {};
    const size = o.size || 10, f = o.font || 'helvetica', st = o.style || 'normal', ind = o.indent || 0;
    return function(w){
      font(f, st, size, o.color || C.ink);
      const lines = doc.splitTextToSize(o.upper ? clean(text).toUpperCase() : clean(text), w - ind - (o.cs ? 6 : 0));
      const rows = lines.map((l, i) => ({h: lh(size), draw(x, y){
        font(f, st, size, o.color || C.ink);
        doc.text(l, x + ind, y + size * PT * 0.95, o.cs ? {charSpace: o.cs} : undefined);
        if (i === 0 && o.bullet){ fill(o.bullet); doc.rect(x + 0.4, y + size * PT * 0.32, 1.9, 1.9, 'F'); }
        if (o.link) doc.link(x + ind, y, w - ind, lh(size), {url: o.link});
      }}));
      if (o.after) rows.push({h: o.after, draw(){}});
      return rows;
    };
  }
  const gap = h => () => [{h, draw(){}}];
  const block = (fn, w) => fn(w);

  // Colonnes côte à côte, fonds de même hauteur, coupure propre entre les pages
  function flow(cols, o){
    o = o || {};
    const pad = o.pad == null ? 4.5 : o.pad;
    cols.forEach(c => { c.rows = [].concat.apply([], c.items.map(it => block(it, c.w - 2 * (c.bg ? pad : 0)))); c.i = 0; });
    const minNeed = Math.min(40, Math.max.apply(null, cols.map(c => c.rows.slice(0, 4).reduce((s, r) => s + r.h, 0))) + 2 * pad);
    if (yy + minNeed > H - BOT){ doc.addPage(); yy = TOP; }
    let first = true;
    while (cols.some(c => c.i < c.rows.length)){
      const avail = H - BOT - yy - 2 * pad;
      const seg = cols.map(c => { let u = 0, j = c.i; while (j < c.rows.length && u + c.rows[j].h <= avail){ u += c.rows[j].h; j++; } if (j === c.i && c.i < c.rows.length){ u = c.rows[j].h; j++; } return {u, j}; });
      const segH = Math.max.apply(null, seg.map(s => s.u)) + 2 * pad;
      cols.forEach(c => {
        if (!first && c.i >= c.rows.length) return;
        if (c.bg){ fill(c.bg); doc.rect(c.x, yy, c.w, segH, 'F'); }
        if (c.bar && first){ fill(c.bar); doc.rect(c.x, yy, c.w, 1.6, 'F'); }
        if (c.side){ fill(c.side); doc.rect(c.x, yy, 1.4, segH, 'F'); }
      });
      cols.forEach((c, k) => {
        let y = yy + pad; const x = c.x + (c.bg || c.side ? pad + (c.side ? 1.5 : 0) : 0);
        for (let j = c.i; j < seg[k].j; j++){ c.rows[j].draw(x, y); y += c.rows[j].h; }
        c.i = seg[k].j;
      });
      yy += segH;
      first = false;
      if (cols.some(c => c.i < c.rows.length)){ doc.addPage(); yy = TOP; }
    }
    yy += o.after == null ? 6 : o.after;
  }
  const heading = (t, color) => textRows(t, {size: 8, style: 'bold', color: color || C.mute, upper: true, cs: 0.5, after: 2.2});

  // En-tête : bandeau pleine largeur
  (function(){
    const label = 'BRIEF CITOYEN  ·  ' + dateTxt.toUpperCase() + (b.theme ? '  ·  ' + clean(b.theme).toUpperCase() : '');
    font('times', 'bold', 25, C.white);
    const tl = doc.splitTextToSize(clean(b.title || 'Brief du jour'), CW);
    font('times', 'italic', 12.5, C.navySoft);
    const sl = b.subject ? doc.splitTextToSize(clean(b.subject), CW - 10) : [];
    const h = 14 + 6 + tl.length * lh(25) + (sl.length ? 3 + sl.length * lh(12.5) : 0) + 9;
    fill(C.navy); doc.rect(0, 0, W, h, 'F');
    fill(C.acc); doc.rect(0, h, W, 1.6, 'F');
    let y = 14;
    font('helvetica', 'bold', 8, C.navySoft); doc.text(label, ML, y, {charSpace: 0.45});
    y += 6;
    font('times', 'bold', 25, C.white);
    tl.forEach(l => { doc.text(l, ML, y + 25 * PT * 0.95); y += lh(25); });
    if (sl.length){ y += 3; font('times', 'italic', 12.5, C.navySoft); sl.forEach(l => { doc.text(l, ML, y + 12.5 * PT * 0.95); y += lh(12.5); }); }
    yy = h + 9;
  })();

  // Les bases + termes clés en encadré latéral
  const basics = arr(b.basics), terms = arr(b.terms).filter(t => t && t.term);
  if (basics.length || terms.length){
    const leftW = terms.length ? 108 : CW, rightW = CW - leftW - 6;
    const left = {x: ML, w: leftW, items: [heading(isInst ? "L'éclairage" : 'Les bases', C.acc)].concat(basics.map(p => textRows(p, {size: 10.2, after: 2.6})))};
    const cols = [left];
    if (terms.length){
      const items = [heading('Les mots à connaître', C.acc)];
      terms.forEach((t, i) => { items.push(textRows(t.term, {size: 9.6, style: 'bold', color: C.navy, after: 0.6})); items.push(textRows(t.def, {size: 8.8, color: C.soft, after: i < terms.length - 1 ? 3.2 : 0})); });
      cols.push({x: ML + leftW + 6, w: rightW, bg: C.wash, items});
    }
    flow(cols, {pad: 4.5});
  }

  // Ce qui se joue : encadré bleu pleine largeur
  const stakes = arr(b.stakes);
  if (stakes.length){
    flow([{x: ML, w: CW, bg: C.blueBg, side: C.acc, items: [heading(isInst ? 'Pourquoi ça compte' : 'Ce qui se joue', C.acc)].concat(stakes.map((p, i) => textRows(p, {size: 10.2, after: i < stakes.length - 1 ? 2.6 : 0})))}], {pad: 5});
  }

  // Pour / Contre côte à côte
  const pro = b.pro || {}, con = b.con || {};
  if (arr(pro.args).length || arr(con.args).length){
    const half = (CW - 6) / 2;
    const side = (s, def, col, bg, x) => {
      const items = [textRows(s.label || def, {font: 'times', style: 'bold', size: 17, color: col, after: 0.5})];
      if (s.who) items.push(textRows(s.who, {size: 8.6, style: 'italic', color: C.soft, after: 3.5}));
      arr(s.args).forEach((a, i, all) => items.push(textRows(a, {size: 9.8, indent: 5, bullet: col, after: i < all.length - 1 ? 2.8 : 0})));
      return {x, w: half, bg, bar: col, items};
    };
    flow([side(pro, 'Pour', C.pro, C.proBg, ML), side(con, 'Contre', C.con, C.conBg, ML + half + 6)], {pad: 5.5});
  }

  // Angle local
  const local = arr(b.local);
  if (local.length){
    flow([{x: ML, w: CW, bg: C.sand, side: C.sandInk, items: [heading('À Toulouse et en Occitanie', C.sandInk)].concat(local.map((p, i) => textRows(p, {size: 10.2, after: i < local.length - 1 ? 2.6 : 0})))}], {pad: 5});
  }

  // Sources en cartes
  const src = arr(b.sources).filter(s => s && s.name);
  if (src.length){
    flow([{x: ML, w: CW, items: [heading('Sources à creuser')]}], {pad: 0, after: 0});
    for (let i = 0; i < src.length; i += 3){
      const group = src.slice(i, i + 3), n = group.length, cw = (CW - 5 * (n - 1)) / n;
      flow(group.map((s, k) => {
        const ok = /^https:\/\//.test(s.url || '');
        const lean = String(s.lean || '').toLowerCase();
        const col = lean.includes('gauche') ? C.con : lean.includes('droite') ? C.acc : C.pro;
        const items = [textRows(s.lean || 'Source', {size: 7.4, style: 'bold', color: col, upper: true, cs: 0.35, after: 1.8}),
                       textRows(s.name, {size: 9.6, style: 'bold', color: ok ? C.navy : C.ink, link: ok ? s.url : null, after: 1.5})];
        if (s.note) items.push(textRows(s.note, {size: 8.6, color: C.soft, after: ok ? 1.8 : 0}));
        if (ok) items.push(textRows(s.url.replace(/^https:\/\/(www\.)?/, '').replace(/\/.*$/, '') + '  ›', {size: 7.8, color: C.acc, link: s.url}));
        return {x: ML + k * (cw + 5), w: cw, bg: C.wash, bar: col, items};
      }), {pad: 4, after: 5});
    }
    yy += 1;
  }

  // Question finale : bandeau sombre
  if (b.question){
    flow([{x: ML, w: CW, bg: C.navy, items: [
      textRows('Pour se faire un avis', {size: 8, style: 'bold', color: C.navySoft, upper: true, cs: 0.5, after: 2.5}),
      textRows(b.question, {font: 'times', style: 'italic', size: 14, color: C.white})
    ]}], {pad: 7, after: 0});
  }

  // Sources utilisées pour construire le brief
  const consulted = arr(b.consulted).filter(s => s && s.name);
  const used = consulted.length ? consulted : src;
  if (used.length){
    yy += 6;
    const items = [textRows('Sources utilisées pour ce brief', {size: 8, style: 'bold', color: C.mute, upper: true, cs: 0.5, after: 2.2})];
    if (!consulted.length) items.push(textRows("La liste complète des sources consultées n'a pas été conservée pour ce brief : seules les sources citées sont indiquées.", {size: 8.4, style: 'italic', color: C.soft, after: 2}));
    used.forEach((s, i) => {
      const ok = /^https:\/\//.test(s.url || '');
      items.push(textRows((i + 1) + '. ' + s.name, {size: 8.8, color: ok ? C.navy : C.ink, link: ok ? s.url : null, after: ok ? 0 : 1.6}));
      if (ok) items.push(textRows(s.url, {size: 7.4, color: C.mute, link: s.url, after: 1.6}));
    });
    flow([{x: ML, w: CW, items}], {pad: 0, after: 0});
  }

  const n = doc.getNumberOfPages();
  for (let i = 1; i <= n; i++){
    doc.setPage(i);
    doc.setDrawColor(220, 225, 232); doc.setLineWidth(0.25); doc.line(ML, H - 12, W - MR, H - 12);
    font('helvetica', 'normal', 7.5, C.mute);
    doc.text('Brief citoyen  ·  ' + dateTxt, ML, H - 8);
    doc.text(i + ' / ' + n, W - MR, H - 8, {align: 'right'});
  }
  return doc;
}
if (typeof module !== 'undefined') module.exports = buildBriefPdf;
