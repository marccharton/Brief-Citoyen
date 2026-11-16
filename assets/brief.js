// Page d'un brief (brief/?id=AAAA-MM-JJ) : charge le JSON, affiche le brief, le mode inspection
// (chaque phrase reliée à sa source), la fiche technique et le bouton de partage.
(function(){
  var esc = BC.esc, lst = BC.lst;
  var $ = function(id){ return document.getElementById(id); };
  var toastEl = $('toast'), timer = null, data = null;
  var CONSIGNES_URL = 'https://github.com/marccharton/Brief-Citoyen/blob/main/methode/consignes.md';
  var CONSIGNES_HIST = 'https://github.com/marccharton/Brief-Citoyen/commits/main/methode/consignes.md';
  var NB_COULEURS = 8;
  // Repère de source en fin de phrase : [3], [2,5] ou [IA].
  var MARK_RE = /\s*\[(IA|\d+(?:\s*,\s*\d+)*)\]/g;

  function toast(msg){
    if (!toastEl) return;
    toastEl.textContent = msg;
    clearTimeout(timer);
    timer = setTimeout(function(){ toastEl.textContent = ''; }, 3500);
  }

  function fail(title, msg){
    document.title = title + ' · Brief citoyen';
    $('title').textContent = title;
    $('content').innerHTML = '<section class="question"><p>' + esc(msg) + '</p>'
      + '<a class="cta" href="../">Voir tous les briefs</a></section>';
  }

  function setMeta(sel, attr, val){
    var m = document.querySelector(sel);
    if (m) m.setAttribute(attr, val);
  }

  function colorOf(n){ return 'var(--src-' + (((n - 1) % NB_COULEURS) + 1) + ')'; }

  // Lien qui ouvre la page et surligne le passage cité (fragment de texte).
  function fragUrl(url, extrait){
    if (!BC.isHttps(url)) return '';
    var base = url.split('#')[0];
    var t = String(extrait || '').trim();
    if (!t) return base;
    return base + '#:~:text=' + encodeURIComponent(t).replace(/-/g, '%2D');
  }

  // Découpe un texte en segments {t, refs} : refs = null (pas de repère), 'IA' ou [numéros].
  function segments(text){
    var s = String(text == null ? '' : text), out = [], last = 0, m;
    MARK_RE.lastIndex = 0;
    while ((m = MARK_RE.exec(s))){
      var t = s.slice(last, m.index);
      var refs = m[1] === 'IA' ? 'IA' : m[1].split(',').map(function(x){ return parseInt(x, 10); });
      if (t.trim()) out.push({t: t, refs: refs});
      last = MARK_RE.lastIndex;
    }
    var rest = s.slice(last);
    if (rest.trim()) out.push({t: rest, refs: null});
    return out;
  }

  function hasMarks(text){ MARK_RE.lastIndex = 0; return MARK_RE.test(String(text || '')); }

  // Statistiques de sourçage, remplies pendant le rendu.
  var stats = {src: 0, ia: 0, none: 0};

  function txt(text){
    return segments(text).map(function(sg){
      if (sg.refs === null){ stats.none++; return esc(sg.t); }
      if (sg.refs === 'IA'){
        stats.ia++;
        return '<span class="seg ia" data-refs="IA">' + esc(sg.t) + '<sup class="mk">IA</sup></span>';
      }
      stats.src++;
      return '<span class="seg" data-refs="' + sg.refs.join(' ') + '" style="--c:' + colorOf(sg.refs[0]) + '">'
        + esc(sg.t) + '<sup class="mk">' + sg.refs.join(',') + '</sup></span>';
    }).join(' ');
  }

  function sourceItem(s){
    var lean = String(s.lean || ''), l = lean.toLowerCase();
    var cls = l.indexOf('gauche') >= 0 ? 'l' : l.indexOf('droite') >= 0 ? 'r' : 'n';
    var name = BC.isHttps(s.url)
      ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.name) + '</a>' : esc(s.name);
    var h = BC.host(s.url);
    return '<li class="' + cls + '"><span class="lean">' + esc(lean) + '</span><span class="name">' + name + '</span>'
      + (s.note ? '<span class="note">' + esc(s.note) + '</span>' : '')
      + (h ? '<span class="host">' + esc(h) + '</span>' : '') + '</li>';
  }

  // Sources utilisées, numérotées : le numéro est celui des repères [n] du texte.
  function numbered(used){
    return used.map(function(s, i){
      var n = parseInt(s.n, 10) || (i + 1);
      return {n: n, name: s.name, url: s.url, type: s.type || '', extrait: s.extrait || ''};
    });
  }

  function usedItem(s, withChip){
    var name = BC.isHttps(s.url)
      ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.name) + '</a>' : esc(s.name);
    var out = '<li' + (withChip ? ' value="' + s.n + '" style="--c:' + colorOf(s.n) + '"' : '') + '>'
      + (withChip ? '<span class="chip-n">' + s.n + '</span>' : '')
      + '<span class="u-main">' + name + ' <span class="h">' + esc(BC.host(s.url)) + '</span>'
      + (s.type ? ' <span class="u-type">' + esc(s.type) + '</span>' : '') + '</span>';
    if (s.extrait){
      var fu = fragUrl(s.url, s.extrait);
      out += '<span class="u-ext">« ' + esc(s.extrait) + ' »'
        + (fu ? ' <a href="' + esc(fu) + '" target="_blank" rel="noopener">voir le passage</a>' : '') + '</span>';
    }
    return out + '</li>';
  }

  function pct(a, total){ return total ? Math.round(100 * a / total) : 0; }

  var SCORE_COLS = [['couverture', 'Couverture', 3], ['variete', 'Variété', 2], ['deux_cotes', 'Deux côtés', 1],
    ['fraicheur', 'Fraîcheur', 2], ['impact', 'Impact', 2], ['local', 'Local', 1], ['repetition', 'Répétition', 0]];

  function num(v){ var x = Number(v); return isFinite(x) ? x : 0; }

  function fiche(b, isInst, marked){
    var f = b.fiche && typeof b.fiche === 'object' ? b.fiche : null;
    var out = ['<details class="fiche" id="fiche"><summary><span class="kicker">Fiche technique</span>'
      + '<span class="f-sum">Comment ce brief a été fait : choix du sujet, sources, part rédigée par l’IA</span></summary><div class="f-body">'];
    if (!f){
      out.push('<p class="note">Ce brief a été publié avant la mise en place des fiches techniques, le 17 novembre 2026 : '
        + 'le détail du choix de son sujet n’a pas été conservé. La méthode générale est décrite dans '
        + '<a href="../comment-c-est-fait/">Comment c’est fait</a>.</p></div></details>');
      return out.join('');
    }
    var total = stats.src + stats.ia;
    var rows = [];
    rows.push(['Rédigé le', esc(BC.dateLong(b.date)) + (f.genere_a ? ' à ' + esc(f.genere_a) : '')]);
    if (f.modele) rows.push(['Modèle', esc(f.modele)]);
    if (f.consignes) rows.push(['Consignes', '<a href="' + CONSIGNES_URL + '" target="_blank" rel="noopener">version '
      + esc(String(f.consignes).replace(/^v/i, '')) + '</a> (<a href="' + CONSIGNES_HIST + '" target="_blank" rel="noopener">historique</a>)']);
    if (marked && total){
      rows.push(['Sourçage', stats.src + ' phrases sur ' + total + ' reliées à une source (' + pct(stats.src, total) + ' %), '
        + stats.ia + ' rédigées par l’IA sans source précise (' + pct(stats.ia, total) + ' %)']);
    }
    out.push('<dl class="f-meta">' + rows.map(function(r){ return '<div><dt>' + r[0] + '</dt><dd>' + r[1] + '</dd></div>'; }).join('') + '</dl>');

    if (isInst){
      if (f.progression) out.push('<h3>Notion traitée</h3><p>' + esc(f.progression) + '</p>');
      if (f.choix) out.push('<p>' + esc(f.choix) + '</p>');
    } else {
      var cands = lst(f.candidats).filter(function(c){ return c && typeof c === 'object' && c.sujet; });
      if (f.choix) out.push('<h3>Pourquoi ce sujet</h3><p>' + esc(f.choix) + '</p>');
      if (cands.length){
        out.push('<h3>Les sujets candidats</h3><p class="note">Chaque sujet repéré reçoit un score selon une '
          + '<a href="../comment-c-est-fait/#choix-du-sujet">règle fixe</a>. Le maximum de chaque critère est indiqué entre parenthèses.</p>'
          + '<div class="f-scroll"><table class="f-table"><thead><tr><th>Sujet</th>'
          + SCORE_COLS.map(function(c){ return '<th>' + c[1] + (c[2] ? ' <span>(' + c[2] + ')</span>' : ' <span>(−1)</span>') + '</th>'; }).join('')
          + '<th>Total</th></tr></thead><tbody>'
          + cands.map(function(c){
            var sc = c.score && typeof c.score === 'object' ? c.score : {};
            var tot = c.total != null ? num(c.total) : SCORE_COLS.reduce(function(a, k){ return a + num(sc[k[0]]); }, 0);
            var ok = String(c.decision || '').toLowerCase().indexOf('retenu') === 0;
            return '<tr class="' + (ok ? 'kept' : '') + '"><th scope="row"><span class="f-dec">' + (ok ? 'Retenu' : 'Écarté') + '</span>'
              + esc(c.sujet) + (c.categorie ? '<span class="f-cat">' + esc(c.categorie)
              + (c.nb_sources != null ? ' · ' + esc(c.nb_sources) + ' sources' : '') + '</span>' : '')
              + (c.raison ? '<span class="f-why">' + esc(c.raison) + '</span>' : '') + '</th>'
              + SCORE_COLS.map(function(k){ return '<td>' + num(sc[k[0]]) + '</td>'; }).join('')
              + '<td class="tot">' + tot + '</td></tr>';
          }).join('') + '</tbody></table></div>');
      }
      var rech = lst(f.recherches).filter(function(r){ return typeof r === 'string'; });
      if (rech.length){
        out.push('<h3>Recherches lancées pour le repérage</h3><ul class="f-list">'
          + rech.map(function(r){ return '<li>« ' + esc(r) + ' »</li>'; }).join('') + '</ul>');
      }
      var rep = lst(f.reperage).filter(function(s){ return s && typeof s === 'object' && s.name; });
      if (rep.length){
        out.push('<h3>Pages ouvertes pour le repérage (' + rep.length + ')</h3><ul class="f-list">'
          + rep.map(function(s){
            return '<li>' + (BC.isHttps(s.url) ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.name) + '</a>'
              : esc(s.name)) + ' <span class="h">' + esc(BC.host(s.url)) + '</span></li>';
          }).join('') + '</ul>');
      }
    }
    out.push('</div></details>');
    return out.join('');
  }

  function panel(srcs){
    var total = stats.src + stats.ia;
    return '<div class="p-head"><button type="button" class="p-toggle" id="p-toggle" aria-expanded="true">'
      + '<strong>Sources de chaque phrase</strong><span class="p-stat">' + pct(stats.src, total) + ' % sourcé</span></button>'
      + '<button type="button" class="p-close" id="p-close" aria-label="Quitter le mode inspection">×</button></div>'
      + '<div class="p-body"><p class="p-help">Chaque phrase est colorée selon sa source. Toucher une source pour ne voir que ses phrases.</p><ul>'
      + srcs.map(function(s){
        var cnt = document.querySelectorAll('.seg[data-refs~="' + s.n + '"]').length;
        var fu = fragUrl(s.url, s.extrait);
        return '<li style="--c:' + colorOf(s.n) + '"><button type="button" class="p-src" data-n="' + s.n + '"' + (cnt ? '' : ' disabled') + '>'
          + '<span class="chip-n">' + s.n + '</span><span class="p-name">' + esc(s.name) + '<span class="h">'
          + esc(BC.host(s.url)) + (s.type ? ' · ' + esc(s.type) : '') + ' · ' + cnt + ' phrase' + (cnt > 1 ? 's' : '') + '</span></span></button>'
          + (fu ? '<a class="p-open" href="' + esc(fu) + '" target="_blank" rel="noopener" aria-label="Ouvrir la source ' + s.n + '">↗</a>' : '')
          + '</li>';
      }).join('')
      + '<li class="p-ia"><button type="button" class="p-src" data-n="IA"' + (stats.ia ? '' : ' disabled') + '><span class="chip-n">IA</span>'
      + '<span class="p-name">Rédigé par l’IA sans source précise<span class="h">contexte, définitions, transitions · '
      + stats.ia + ' phrase' + (stats.ia > 1 ? 's' : '') + '</span></span></button></li></ul></div>';
  }

  function render(b, entry, labels, prev, next){
    var isInst = entry.type === 'institutions';
    var out = [];
    stats = {src: 0, ia: 0, none: 0};
    var paras = function(v){ return lst(v).map(function(p){ return '<p>' + txt(p) + '</p>'; }).join(''); };
    var pro = b.pro || {}, con = b.con || {};
    var marked = [].concat(lst(b.basics), lst(b.stakes), lst(b.local), lst(pro.args), lst(con.args)).some(hasMarks);

    var basics = lst(b.basics);
    var terms = lst(b.terms).filter(function(t){ return t && typeof t === 'object' && t.term; });
    if (basics.length || terms.length){
      out.push('<section class="basics' + (terms.length ? ' with-terms' : '') + '"><div class="prose">'
        + '<h2 class="kicker">' + (isInst ? 'L’éclairage' : 'Les bases') + '</h2>' + paras(basics) + '</div>'
        + (terms.length ? '<aside class="terms"><h2 class="kicker">Les mots à connaître</h2><dl>'
          + terms.map(function(t){ return '<div><dt>' + esc(t.term) + '</dt><dd>' + esc(t.def || '') + '</dd></div>'; }).join('')
          + '</dl></aside>' : '')
        + '</section>');
    }

    if (lst(b.stakes).length){
      out.push('<section class="box stakes"><h2 class="kicker">' + (isInst ? 'Pourquoi ça compte' : 'Ce qui se joue')
        + '</h2>' + paras(b.stakes) + '</section>');
    }

    if (lst(pro.args).length || lst(con.args).length){
      out.push('<section class="sides">');
      [['pro', pro, 'Pour'], ['con', con, 'Contre']].forEach(function(x){
        var s = x[1];
        if (!lst(s.args).length) return;
        out.push('<div class="side ' + x[0] + '"><h2>' + esc(s.label || x[2]) + '</h2>'
          + (s.who ? '<p class="who">' + esc(s.who) + '</p>' : '')
          + '<ul>' + lst(s.args).map(function(a){ return '<li>' + txt(a) + '</li>'; }).join('') + '</ul></div>');
      });
      out.push('</section>');
    }

    if (lst(b.local).length){
      out.push('<section class="box local"><h2 class="kicker">À Toulouse et en Occitanie</h2>' + paras(b.local) + '</section>');
    }

    var sources = lst(b.sources).filter(function(s){ return s && typeof s === 'object' && s.name; });
    if (sources.length){
      out.push('<section class="sources"><h2 class="kicker">Sources à creuser</h2><ul>'
        + sources.map(sourceItem).join('') + '</ul></section>');
    }

    if (b.question){
      out.push('<section class="question"><h2 class="kicker">Pour se faire un avis</h2><p>' + esc(b.question) + '</p></section>');
    }

    var used = numbered(lst(b.consulted).filter(function(s){ return s && typeof s === 'object' && s.name; }));
    var note = marked
      ? 'Toutes les pages utilisées pour construire ce brief. Le numéro de chaque source est celui qui s’affiche dans le texte en mode inspection.'
      : 'Toutes les pages consultées pour construire ce brief, y compris celles qui ne sont pas citées plus haut.';
    if (!used.length){
      used = numbered(sources);
      note = "La liste complète des sources consultées n'a pas été conservée pour ce brief, publié avant "
        + "l'ajout de cette rubrique : seules les sources citées plus haut sont indiquées.";
    }
    if (used.length){
      out.push('<section class="used' + (marked ? ' marked' : '') + '"><h2 class="kicker">Sources utilisées pour ce brief</h2><p class="note">'
        + esc(note) + '</p><ol>' + used.map(function(s){ return usedItem(s, marked); }).join('') + '</ol></section>');
    }

    out.push(fiche(b, isInst, marked));

    var nav = [];
    if (next) nav.push('<a class="nav-prev" href="?id=' + esc(next.id) + '"><span>Brief suivant</span>' + esc(next.title) + '</a>');
    if (prev) nav.push('<a class="nav-next" href="?id=' + esc(prev.id) + '"><span>Brief précédent</span>' + esc(prev.title) + '</a>');
    if (nav.length) out.push('<nav class="pager">' + nav.join('') + '</nav>');

    // En-tête
    document.title = b.title + ' · Brief citoyen';
    setMeta('meta[name="description"]', 'content', b.subject || '');
    setMeta('meta[property="og:title"]', 'content', document.title);
    setMeta('meta[property="og:description"]', 'content', b.subject || '');
    $('eyebrow').innerHTML = '<span>Brief citoyen</span><span class="dot">·</span><time datetime="' + esc(b.date) + '">'
      + esc(BC.dateLong(b.date)) + '</time><span class="dot">·</span><span>' + esc(labels.types[entry.type] || '') + '</span>'
      + entry.categories.map(function(c){ return '<span class="dot">·</span><span>' + esc(c) + '</span>'; }).join('');
    $('title').textContent = b.title;
    if (b.subject){ $('subject').textContent = b.subject; $('subject').hidden = false; }
    $('tools').hidden = false;
    $('content').innerHTML = out.join('\n');
    if (marked) setupInspect(used);
  }

  // Mode inspection
  function setupInspect(srcs){
    var btn = $('inspect'), pnl = $('srcpanel');
    if (!btn || !pnl) return;
    pnl.innerHTML = panel(srcs);
    btn.hidden = false;
    var focus = null;

    function setFocus(n){
      focus = (n === focus) ? null : n;
      document.body.classList.toggle('focusing', focus !== null);
      Array.prototype.forEach.call(document.querySelectorAll('.seg'), function(el){
        var refs = (el.getAttribute('data-refs') || '').split(' ');
        el.classList.toggle('on', focus !== null && refs.indexOf(String(focus)) >= 0);
      });
      Array.prototype.forEach.call(pnl.querySelectorAll('.p-src'), function(el){
        el.setAttribute('aria-pressed', String(el.getAttribute('data-n') === String(focus)));
      });
    }

    function setMode(on){
      document.body.classList.toggle('inspect', on);
      btn.setAttribute('aria-pressed', String(on));
      btn.textContent = on ? 'Masquer les sources' : 'Voir la source de chaque phrase';
      pnl.hidden = !on;
      if (!on && focus !== null) setFocus(focus);
      try { localStorage.setItem('bc-inspect', on ? '1' : '0'); } catch (e) {}
    }

    btn.addEventListener('click', function(){ setMode(!document.body.classList.contains('inspect')); });
    $('p-close').addEventListener('click', function(){ setMode(false); });
    $('p-toggle').addEventListener('click', function(){
      var open = pnl.classList.toggle('folded');
      this.setAttribute('aria-expanded', String(!open));
    });
    pnl.addEventListener('click', function(ev){
      var el = ev.target.closest('.p-src');
      if (el && !el.disabled){
        var n = el.getAttribute('data-n');
        setFocus(n);
        var first = focus !== null && document.querySelector('.seg.on');
        if (first) window.scrollTo({top: first.getBoundingClientRect().top + window.scrollY - window.innerHeight * 0.2, behavior: 'smooth'});
      }
    });
    $('content').addEventListener('click', function(ev){
      if (!document.body.classList.contains('inspect')) return;
      var seg = ev.target.closest('.seg');
      if (!seg) return;
      setFocus((seg.getAttribute('data-refs') || '').split(' ')[0]);
    });
    var saved = null;
    try { saved = localStorage.getItem('bc-inspect'); } catch (e) {}
    if (saved === '1') setMode(true);
  }

  var id = new URLSearchParams(location.search).get('id') || '';
  if (!BC.ID_RE.test(id)){
    fail('Brief introuvable', "L'adresse ne précise pas quel brief afficher.");
  } else {
    Promise.all([BC.loadJson('../data/index.json'), BC.loadJson('../data/briefs/' + id + '.json')])
      .then(function(res){
        var index = res[0], b = res[1];
        var list = index.briefs, i = -1;
        for (var k = 0; k < list.length; k++) if (list[k].id === id){ i = k; break; }
        var entry = i >= 0 ? list[i] : {id: id, type: b.type || 'actualite', categories: lst(b.categories).slice(0, 3)};
        data = b;
        // Liste du plus récent au plus ancien : le suivant est avant, le précédent après.
        render(b, entry, index, i + 1 < list.length && i >= 0 ? list[i + 1] : null, i > 0 ? list[i - 1] : null);
        if (location.hash === '#fiche'){ var f = $('fiche'); if (f){ f.open = true; f.scrollIntoView(); } }
      })
      .catch(function(){
        fail('Brief introuvable', "Ce brief n'existe pas ou n'a pas pu être chargé. Vérifier l'adresse, ou réessayer dans un instant.");
      });
  }

  var share = $('share');
  if (share) share.addEventListener('click', function(){
    var url = location.href.split('#')[0];
    var title = data && data.title ? data.title : document.title;
    if (navigator.share){
      navigator.share({title: title, url: url}).catch(function(){});
      return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(url).then(function(){ toast('Lien copié.'); }, function(){ toast(url); });
    } else {
      toast(url);
    }
  });
})();
