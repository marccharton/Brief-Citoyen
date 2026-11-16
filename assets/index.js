// Page d'accueil : charge data/index.json, affiche la liste des briefs et gère les filtres.
(function(){
  var esc = BC.esc;
  var list = document.getElementById('list'), box = document.getElementById('filters');

  function render(index){
    var briefs = index.briefs, types = index.types;
    var n = briefs.length;
    document.getElementById('count').textContent = n + ' brief' + (n > 1 ? 's' : '');

    var used = {};
    briefs.forEach(function(b){ b.categories.forEach(function(c){ used[c] = true; }); });
    box.querySelector('[data-group="type"]').insertAdjacentHTML('beforeend', Object.keys(types).map(function(k){
      return '<button class="chip" type="button" data-type="' + esc(k) + '" aria-pressed="false">' + esc(types[k]) + '</button>';
    }).join(''));
    box.querySelector('[data-group="cat"]').insertAdjacentHTML('beforeend', index.categories.filter(function(c){ return used[c.name]; }).map(function(c){
      return '<button class="chip" type="button" data-cat="' + esc(c.name) + '" aria-pressed="false">' + esc(c.name) + '</button>';
    }).join(''));

    var out = [], month = null;
    briefs.forEach(function(b){
      var d = BC.parseDate(b.date);
      var m = BC.MOIS[d.getUTCMonth()];
      m = m.charAt(0).toUpperCase() + m.slice(1) + ' ' + d.getUTCFullYear();
      if (m !== month){ out.push('<li class="month">' + esc(m) + '</li>'); month = m; }
      out.push('<li class="item" data-type="' + esc(b.type) + '" data-cats="' + esc(b.categories.join('|')) + '">'
        + '<a href="brief/?id=' + esc(b.id) + '">'
        + '<span class="when"><span class="d">' + BC.JOURS[d.getUTCDay()].slice(0, 3) + '.</span><span class="n">' + d.getUTCDate() + '</span></span>'
        + '<span class="body"><span class="meta"><span class="type ' + esc(b.type) + '">' + esc(types[b.type] || '') + '</span>'
        + b.categories.map(function(c){ return '<span class="cat">' + esc(c) + '</span>'; }).join('')
        + '</span><span class="t">' + esc(b.title) + '</span><span class="s">' + esc(b.subject || '') + '</span></span></a></li>');
    });
    list.innerHTML = out.join('\n');
    box.hidden = false;
  }

  var sel = {type: '', cat: ''};
  box.addEventListener('click', function(ev){
    var c = ev.target.closest('.chip'); if (!c) return;
    var row = c.closest('.frow'), g = row.getAttribute('data-group');
    sel[g] = c.getAttribute(g === 'type' ? 'data-type' : 'data-cat');
    row.querySelectorAll('.chip').forEach(function(x){ x.setAttribute('aria-pressed', String(x === c)); });
    list.querySelectorAll('.item').forEach(function(it){
      var okT = !sel.type || it.getAttribute('data-type') === sel.type;
      var okC = !sel.cat || it.getAttribute('data-cats').split('|').indexOf(sel.cat) >= 0;
      it.hidden = !(okT && okC);
    });
    list.querySelectorAll('.month').forEach(function(mo){
      var nx = mo.nextElementSibling, any = false;
      while (nx && !nx.classList.contains('month')){ if (!nx.hidden) any = true; nx = nx.nextElementSibling; }
      mo.hidden = !any;
    });
  });

  BC.loadJson('data/index.json').then(render).catch(function(){
    list.innerHTML = '<li class="month">La liste des briefs n\'a pas pu être chargée. Réessayer dans un instant.</li>';
  });
})();
