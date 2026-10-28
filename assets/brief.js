// Page d'un brief : partager le lien, télécharger le PDF.
(function(){
  var toastEl = document.getElementById('toast'), timer = null;
  function toast(msg){
    if (!toastEl) return;
    toastEl.textContent = msg;
    clearTimeout(timer);
    timer = setTimeout(function(){ toastEl.textContent = ''; }, 3500);
  }
  var data = null;
  try { data = JSON.parse(document.getElementById('brief-data').textContent); } catch (err) {}

  var share = document.getElementById('share');
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

  var pdf = document.getElementById('pdf');
  if (pdf) pdf.addEventListener('click', function(){
    if (!data || !window.jspdf || typeof buildBriefPdf !== 'function'){
      toast("Le PDF n'a pas pu se préparer. Recharge la page puis réessaie.");
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
