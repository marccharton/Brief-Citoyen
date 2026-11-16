// Page d'un brief (brief/?id=AAAA-MM-JJ) : charge le JSON, affiche le brief, gère le partage et le PDF.
(function(){
  var esc = BC.esc, lst = BC.lst;
  var $ = function(id){ return document.getElementById(id); };
  var toastEl = $('toast'), timer = null, data = null;

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

  function render(b, entry, labels, prev, next){
    var isInst = entry.type === 'institutions';
    var out = [];
    var paras = function(v){ return lst(v).map(function(p){ return '<p>' + esc(p) + '</p>'; }).join(''); };

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

    var pro = b.pro || {}, con = b.con || {};
    if (lst(pro.args).length || lst(con.args).length){
      out.push('<section class="sides">');
      [['pro', pro, 'Pour'], ['con', con, 'Contre']].forEach(function(x){
        var s = x[1];
        if (!lst(s.args).length) return;
        out.push('<div class="side ' + x[0] + '"><h2>' + esc(s.label || x[2]) + '</h2>'
          + (s.who ? '<p class="who">' + esc(s.who) + '</p>' : '')
          + '<ul>' + lst(s.args).map(function(a){ return '<li>' + esc(a) + '</li>'; }).join('') + '</ul></div>');
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

    var used = lst(b.consulted).filter(function(s){ return s && typeof s === 'object' && s.name; });
    var note = 'Toutes les pages consultées pour construire ce brief, y compris celles qui ne sont pas citées plus haut.';
    if (!used.length){
      used = sources;
      note = "La liste complète des sources consultées n'a pas été conservée pour ce brief, publié avant "
        + "l'ajout de cette rubrique : seules les sources citées plus haut sont indiquées.";
    }
    if (used.length){
      out.push('<section class="used"><h2 class="kicker">Sources utilisées pour ce brief</h2><p class="note">' + esc(note) + '</p><ol>'
        + used.map(function(s){
          return BC.isHttps(s.url)
            ? '<li><a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.name) + '</a> <span class="h">' + esc(BC.host(s.url)) + '</span></li>'
            : '<li>' + esc(s.name) + '</li>';
        }).join('') + '</ol></section>');
    }

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

  var pdf = $('pdf');
  if (pdf) pdf.addEventListener('click', function(){
    if (!data || !window.jspdf || typeof buildBriefPdf !== 'function'){
      toast("Le PDF n'a pas pu se préparer. Recharger la page puis réessayer.");
      return;
    }
    try {
      var slug = String(data.title || 'brief').normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/[^a-zA-Z0-9]+/g, '-').replace(/^-|-$/g, '').toLowerCase().slice(0, 60);
      buildBriefPdf(window.jspdf.jsPDF, data).save('brief-citoyen-' + data.date + '-' + slug + '.pdf');
    } catch (err) {
      toast("Le PDF de ce brief n'a pas pu être créé.");
    }
  });
})();
