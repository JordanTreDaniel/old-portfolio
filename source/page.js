
(function () {
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.tab-panel'));
  function activate(id, push) {
    tabs.forEach(function (t) {
      t.setAttribute('aria-selected', String(t.dataset.tab === id));
    });
    panels.forEach(function (p) {
      p.classList.toggle('active', p.dataset.panel === id);
    });
    if (push && history.replaceState) history.replaceState(null, '', '#' + id);
    window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function () { activate(t.dataset.tab, true); });
  });
  var initial = (location.hash || '').replace('#', '');
  if (initial === 'combine' || initial === 'rankings') activate(initial, false);
})();
