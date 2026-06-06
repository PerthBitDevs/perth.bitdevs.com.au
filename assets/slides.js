/*
 * Perth BitDevs — shared slide-deck runtime.
 *
 * Drives:
 *   - Keyboard navigation (ArrowLeft/Right between .slide elements)
 *   - Dot rendering and click-to-jump
 *   - Prev/Next button state
 *   - Disclosure trigger toggling (aria-expanded + hidden body)
 *   - Escape → back to the month hub (derived from location.pathname)
 *
 * The Escape handler always attaches. The slide runtime only initialises if
 * the page contains .slide elements, so this script is safe to load on
 * auxiliary visual pages too.
 *
 * Replaces the inline copies that used to live at the bottom of every
 * slide-deck page. See agent_docs/slide-page-conventions.md.
 */

(function () {
  'use strict';

  if (window.__pbdSlidesLoaded) return;
  window.__pbdSlidesLoaded = true;

  function backUrl() {
    var m = location.pathname.match(/^\/(\d{4}-\d{2})\//);
    return m ? '/' + m[1] + '/' : '/';
  }

  function bindDisclosures() {
    document.querySelectorAll('[data-disclosure-target]').forEach(function (btn) {
      var panel = document.getElementById(btn.dataset.disclosureTarget);
      if (!panel) return;
      btn.addEventListener('click', function () {
        var expanded = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', String(!expanded));
        panel.hidden = expanded;
      });
    });
  }

  function bindSlides() {
    var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
    if (slides.length === 0) return;

    var names = slides.map(function (s) { return s.dataset.name || 'Slide'; });
    var dots = document.getElementById('dots');
    var navInfo = document.getElementById('navInfo');
    var prevBtn = document.getElementById('prevBtn');
    var nextBtn = document.getElementById('nextBtn');
    var cur = 0;

    function goTo(index) {
      cur = Math.max(0, Math.min(slides.length - 1, index));
      render();
    }
    function go(delta) { goTo(cur + delta); }

    function render() {
      slides.forEach(function (slide, i) {
        slide.classList.toggle('active', i === cur);
      });
      if (dots) {
        dots.replaceChildren();
        names.forEach(function (name, i) {
          var b = document.createElement('button');
          b.type = 'button';
          b.className = 'dot' + (i === cur ? ' on' : '');
          b.textContent = String(i + 1);
          b.setAttribute('aria-label', 'Go to slide ' + (i + 1) + ': ' + name);
          if (i === cur) b.setAttribute('aria-current', 'step');
          b.addEventListener('click', function () { goTo(i); });
          dots.append(b);
        });
      }
      if (navInfo) {
        navInfo.textContent = names[cur] + ' - ' + (cur + 1) + ' / ' + slides.length;
      }
      if (prevBtn) prevBtn.disabled = cur === 0;
      if (nextBtn) {
        nextBtn.disabled = cur === slides.length - 1;
        nextBtn.className = cur === slides.length - 1 ? 'nav-btn' : 'nav-btn next';
      }
    }

    if (prevBtn) prevBtn.addEventListener('click', function () { go(-1); });
    if (nextBtn) nextBtn.addEventListener('click', function () { go(1); });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') go(1);
      else if (e.key === 'ArrowLeft') go(-1);
    });

    render();
  }

  function bindEscape() {
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') window.location.href = backUrl();
    });
  }

  function init() {
    bindEscape();
    bindDisclosures();
    bindSlides();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
