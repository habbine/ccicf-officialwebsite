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

  // Lower-case and drop accents so "seminaire" matches "Séminaire" (same rule as the build's fold()).
  function fold(s) {
    return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').normalize('NFC');
  }

  // Category filters + text search. Without JavaScript everything stays visible.
  // opts.syncUrl: keep ?type= and ?q= in the address bar so a filtered view can be shared.
  function setup(scope, items, opts) {
    opts = opts || {};
    var chips = scope.querySelectorAll('.filters .chip');
    var status = scope.querySelector('.filter-status');
    var input = scope.querySelector('.search input');
    var moreBtn = scope.querySelector('.more-years');
    var current = 'all';
    var expanded = false;

    function apply() {
      var q = input ? fold(input.value.trim()) : '';
      var words = q.split(/\s+/).filter(Boolean);   // every word must appear, in any order
      var narrowing = q !== '' || current !== 'all';
      var shown = 0;
      items.forEach(function (el) {
        var cats = (el.getAttribute('data-cats') || '').split(' ');
        var text = el.getAttribute('data-text') || fold(el.textContent);
        var ok = (current === 'all' || cats.indexOf(current) >= 0) && words.every(function (w) { return text.indexOf(w) >= 0; });
        el.hidden = !ok;
        if (ok) shown++;
      });
      // Member tiers and archive years disappear when a filter leaves them empty.
      scope.querySelectorAll('section.tier').forEach(function (sec) {
        sec.hidden = !sec.querySelector('.member-card:not([hidden])');
      });
      scope.querySelectorAll('section.arch-year').forEach(function (sec) {
        var empty = !sec.querySelector('li:not([hidden])');
        var folded = sec.classList.contains('is-older') && !expanded && !narrowing;
        sec.hidden = empty || folded;
      });
      if (moreBtn) moreBtn.hidden = expanded || narrowing || !scope.querySelector('section.arch-year.is-older');
      if (status) {
        var emptyMsg = status.getAttribute('data-empty');
        status.textContent = narrowing || !moreBtn
          ? ((shown === 0 && emptyMsg) ? emptyMsg : status.getAttribute('data-template').replace('{n}', shown))
          : '';
      }
      if (opts.syncUrl && window.history && history.replaceState) {
        var params = new URLSearchParams(location.search);
        if (current !== 'all') params.set('type', current); else params.delete('type');
        if (input && input.value.trim()) params.set('q', input.value.trim()); else params.delete('q');
        var qs = params.toString();
        history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash);
      }
    }
    function select(value) {
      current = value;
      chips.forEach(function (c) { c.setAttribute('aria-pressed', c.getAttribute('data-filter') === value ? 'true' : 'false'); });
    }
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () { select(chip.getAttribute('data-filter')); apply(); });
    });
    if (input) input.addEventListener('input', apply);
    if (moreBtn) moreBtn.addEventListener('click', function () {
      expanded = true;
      apply();
      var first = scope.querySelector('section.arch-year.is-older h3 a');
      if (first) first.focus();
    });

    if (opts.syncUrl) {
      var params = new URLSearchParams(location.search);
      var type = params.get('type');
      if (type && scope.querySelector('.chip[data-filter="' + type + '"]')) select(type);
      if (input && params.get('q')) input.value = params.get('q');
    }
    apply();
  }

  var archive = document.querySelector('.archive');
  if (archive) {
    setup(archive, Array.prototype.slice.call(archive.querySelectorAll('.arch-list li')), { syncUrl: true });
    // Activity cards link to "?type=…#archive": apply without reloading when already on the page.
    document.querySelectorAll('a.type-link').forEach(function (a) {
      a.addEventListener('click', function (e) {
        var type = new URL(a.href).searchParams.get('type');
        var chip = archive.querySelector('.chip[data-filter="' + type + '"]');
        if (!chip) return;
        e.preventDefault();
        chip.click();
        archive.scrollIntoView({ behavior: 'smooth', block: 'start' });
        chip.focus({ preventScroll: true });
      });
    });
  }
  var content = document.querySelector('.content');
  var cards = document.querySelectorAll('.events .event, .member-grid .member-card');
  if (content && cards.length && content.querySelector(':scope > .filters')) {
    setup(content, Array.prototype.slice.call(cards));
  }
})();
