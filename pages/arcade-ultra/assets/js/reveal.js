/* Shared scrollytelling toolkit: reveal-on-scroll + lightweight parallax + sticky-scene progress.
   Vanilla JS, no dependencies, offline-safe. */
(function () {
  'use strict';

  var reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---- Reveal on scroll -------------------------------------------------
  function initReveal() {
    var els = document.querySelectorAll('[data-reveal]');
    if (!els.length) return;
    if (reduceMotion || !('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var el = entry.target;
          var delay = el.getAttribute('data-reveal-delay');
          if (delay) el.style.transitionDelay = delay + 'ms';
          el.classList.add('is-visible');
          io.unobserve(el);
        }
      });
    }, { threshold: 0.18, rootMargin: '0px 0px -8% 0px' });
    els.forEach(function (el) { io.observe(el); });
  }

  // ---- Parallax (rAF, dirty-flag driven, never reads scroll in listener) --
  function initParallax() {
    var els = document.querySelectorAll('[data-parallax]');
    if (!els.length || reduceMotion) return;
    var dirty = true;
    addEventListener('scroll', function () { dirty = true; }, { passive: true });
    addEventListener('resize', function () { dirty = true; }, { passive: true });
    function loop() {
      if (dirty) {
        dirty = false;
        var vh = innerHeight;
        els.forEach(function (el) {
          var speed = parseFloat(el.getAttribute('data-parallax')) || 0.15;
          var rect = el.getBoundingClientRect();
          var center = rect.top + rect.height / 2 - vh / 2;
          el.style.transform = 'translate3d(0,' + (-center * speed).toFixed(1) + 'px,0)';
        });
      }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
  }

  // ---- Sticky-scene progress: drives a CSS var --scene-progress on a track
  function initSceneProgress() {
    var tracks = document.querySelectorAll('[data-scene-track]');
    if (!tracks.length) return;
    var dirty = true;
    addEventListener('scroll', function () { dirty = true; }, { passive: true });
    addEventListener('resize', function () { dirty = true; }, { passive: true });
    function loop() {
      if (dirty) {
        dirty = false;
        tracks.forEach(function (track) {
          var rect = track.getBoundingClientRect();
          var vh = innerHeight;
          var total = rect.height - vh;
          var p = total > 0 ? Math.min(1, Math.max(0, -rect.top / total)) : 0;
          track.style.setProperty('--scene-progress', p.toFixed(4));
        });
      }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
  }

  // ---- Nav shrink + progress bar -----------------------------------------
  function initChrome() {
    var bar = document.querySelector('[data-scroll-bar]');
    var nav = document.querySelector('[data-nav]');
    if (!bar && !nav) return;
    var dirty = true;
    addEventListener('scroll', function () { dirty = true; }, { passive: true });
    function loop() {
      if (dirty) {
        dirty = false;
        var doc = document.documentElement;
        var max = doc.scrollHeight - innerHeight;
        var p = max > 0 ? doc.scrollTop / max : 0;
        if (bar) bar.style.transform = 'scaleX(' + p.toFixed(4) + ')';
        if (nav) nav.classList.toggle('is-scrolled', doc.scrollTop > 40);
      }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
  }

  document.addEventListener('DOMContentLoaded', function () {
    initReveal();
    initParallax();
    initSceneProgress();
    initChrome();
  });
})();
