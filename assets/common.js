// Outils partagés par la liste (index.html) et la page d'un brief (brief/index.html).
var BC = (function(){
  var MOIS = ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'];
  var JOURS = ['dimanche','lundi','mardi','mercredi','jeudi','vendredi','samedi'];
  var ID_RE = /^\d{4}-\d{2}-\d{2}(-[a-z0-9]+)?$/;

  function esc(s){
    return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){
      return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;'}[c];
    });
  }
  function lst(v){
    if (Array.isArray(v)) return v.filter(function(x){
      return x != null && x !== '' && !(typeof x === 'object' && !Array.isArray(x) && !Object.keys(x).length);
    });
    return v ? [v] : [];
  }
  function parseDate(s){
    var p = String(s).slice(0, 10).split('-').map(Number);
    return new Date(Date.UTC(p[0], p[1] - 1, p[2]));
  }
  function dateLong(s){
    var d = parseDate(s);
    return JOURS[d.getUTCDay()] + ' ' + d.getUTCDate() + ' ' + MOIS[d.getUTCMonth()] + ' ' + d.getUTCFullYear();
  }
  function isHttps(u){ return typeof u === 'string' && u.indexOf('https://') === 0; }
  function host(u){ return isHttps(u) ? u.replace(/^https:\/\/(www\.)?/, '').split('/')[0] : ''; }

  // Index généré par build.py : {types, categories, briefs:[{id, date, title, subject, type, categories}]}, du plus récent au plus ancien.
  function loadJson(url){
    return fetch(url, {cache: 'no-cache'}).then(function(r){
      if (!r.ok) throw new Error(r.status + ' ' + url);
      return r.json();
    });
  }

  return {MOIS: MOIS, JOURS: JOURS, ID_RE: ID_RE, esc: esc, lst: lst, parseDate: parseDate,
          dateLong: dateLong, isHttps: isHttps, host: host, loadJson: loadJson};
})();
