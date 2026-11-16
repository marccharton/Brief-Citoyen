// Page « Comment c'est fait » : affiche une partie à la fois, choisie dans la navigation latérale.
// Sans JavaScript, toutes les parties restent affichées les unes sous les autres.
(function(){
  var parts = Array.prototype.slice.call(document.querySelectorAll('.part'));
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  if (!parts.length) return;
  document.documentElement.classList.add('parts-js');

  function show(id, scroll){
    var target = parts.filter(function(p){ return p.id === id; })[0] || parts[0];
    parts.forEach(function(p){ p.classList.toggle('active', p === target); });
    links.forEach(function(a){
      var on = a.getAttribute('href') === '#' + target.id;
      a.classList.toggle('active', on);
      if (on) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
      if (on && a.scrollIntoView && window.matchMedia('(max-width:860px)').matches){
        a.scrollIntoView({block: 'nearest', inline: 'center'});
      }
    });
    if (scroll){
      var top = document.querySelector('.about-layout').getBoundingClientRect().top + window.scrollY - 12;
      if (window.scrollY > top) window.scrollTo({top: top});
    }
  }

  window.addEventListener('hashchange', function(){ show(location.hash.slice(1), true); });
  show(location.hash.slice(1), false);
})();
