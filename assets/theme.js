/*
 * Perth BitDevs — theme toggle handler.
 *
 * Builds the toggle button and wires click/persistence. The FOUC-prevention
 * script that sets the initial data-theme attribute lives inline in each
 * page's <head> — it has to, because external scripts can't run before the
 * stylesheet applies.
 *
 * On slide pages the toggle is placed inside the existing .header flex bar
 * (with .in-header to opt out of fixed positioning). On all other pages it
 * is appended to <body> and floats top-right.
 */

(function () {
  'use strict';

  var STORAGE_KEY = 'pbd-theme';
  var SUN_SVG =
    '<svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<circle cx="12" cy="12" r="4"/>' +
    '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41' +
    'M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>';
  var MOON_SVG =
    '<svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

  function build() {
    if (document.getElementById('themeToggle')) return;

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'themeToggle';
    btn.className = 'theme-toggle';
    btn.setAttribute('aria-label', 'Toggle theme');
    btn.innerHTML = SUN_SVG + MOON_SVG + '<span class="lbl"></span>';

    var header = document.querySelector('.header');
    var branding = header && header.querySelector(':scope > .branding');
    if (header && branding) {
      btn.classList.add('in-header');
      header.appendChild(btn);
    } else {
      document.body.appendChild(btn);
    }

    paint(btn);
    btn.addEventListener('click', function () {
      var current = document.documentElement.dataset.theme || 'dark';
      var next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem(STORAGE_KEY, next); } catch (e) {}
      paint(btn);
    });
  }

  function paint(btn) {
    var t = document.documentElement.dataset.theme || 'dark';
    var lbl = btn.querySelector('.lbl');
    if (lbl) lbl.textContent = t === 'dark' ? 'Light' : 'Dark';
    btn.setAttribute('aria-label', 'Switch to ' + (t === 'dark' ? 'light' : 'dark') + ' mode');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
