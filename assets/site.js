(function () {
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
  document.querySelectorAll('.has-sub > button').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var open = btn.parentElement.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('.has-sub.open').forEach(function (li) {
      li.classList.remove('open');
      li.querySelector('button').setAttribute('aria-expanded', 'false');
    });
  });

  // Category filters + text search. Without JavaScript everything stays visible.
  function setup(scope, items) {
    var chips = scope.querySelectorAll('.chip');
    var status = scope.querySelector('.filter-status');
    var input = scope.querySelector('.search input');
    var current = 'all';
    function apply() {
      var q = input ? input.value.trim().toLowerCase() : '';
      var shown = 0;
      items.forEach(function (el) {
        var cats = (el.getAttribute('data-cats') || '').split(' ');
        var text = el.getAttribute('data-text') || el.textContent.toLowerCase();
        var ok = (current === 'all' || cats.indexOf(current) >= 0) && (!q || text.indexOf(q) >= 0);
        el.hidden = !ok;
        if (ok) shown++;
      });
      scope.querySelectorAll('section.tier').forEach(function (sec) {
        sec.hidden = !sec.querySelector('.member-card:not([hidden])');
      });
      if (status) {
        var empty = status.getAttribute('data-empty');
        status.textContent = (shown === 0 && empty) ? empty : status.getAttribute('data-template').replace('{n}', shown);
      }
    }
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        current = chip.getAttribute('data-filter');
        chips.forEach(function (c) { c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); });
        apply();
      });
    });
    if (input) input.addEventListener('input', apply);
  }
  var archive = document.querySelector('.archive');
  if (archive) setup(archive, Array.prototype.slice.call(archive.querySelectorAll('.arch-list li')));
  var content = document.querySelector('.content');
  var cards = document.querySelectorAll('.events .event, .member-grid .member-card');
  if (content && cards.length && content.querySelector(':scope > .filters')) {
    setup(content, Array.prototype.slice.call(cards));
  }
})();
