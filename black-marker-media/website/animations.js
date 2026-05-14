/**
 * animations.js — Black Marker Media
 * Particle network, scroll-reveal, and animated counters.
 * Drop one <script src="animations.js"></script> on any page.
 */
(function () {
  'use strict';

  // ── CONFIG ──────────────────────────────────────────────────────────────────
  var RED        = 'rgba(232,24,28,';
  var WHITE      = 'rgba(255,255,255,';
  var N_PARTICLES = 90;
  var RED_SHARE   = 0.1;      // 10% of particles are red
  var LINK_DIST   = 150;      // max px distance to draw a connecting line
  var SPEED       = 0.28;     // max particle speed


  // ══════════════════════════════════════════════════════════════════════════
  // 1. PARTICLE NETWORK — canvas behind every .hero section
  // ══════════════════════════════════════════════════════════════════════════
  function initParticles(hero) {
    var canvas = document.createElement('canvas');
    canvas.setAttribute('aria-hidden', 'true');
    canvas.style.cssText = [
      'position:absolute',
      'top:0', 'left:0',
      'width:100%', 'height:100%',
      'pointer-events:none',
      'z-index:0'
    ].join(';');

    // Make sure hero content sits above the canvas
    var inner = hero.querySelector('.hero-inner, .hero > *:not(canvas):not(.hero-grid)');
    if (inner && !inner.style.position) {
      inner.style.position = 'relative';
      inner.style.zIndex   = '2';
    }
    var grid = hero.querySelector('.hero-grid');
    if (grid) { grid.style.zIndex = '1'; }

    hero.insertBefore(canvas, hero.firstChild);

    var ctx   = canvas.getContext('2d');
    var W     = 0;
    var H     = 0;
    var parts = [];

    function resize() {
      W = canvas.width  = hero.offsetWidth;
      H = canvas.height = hero.offsetHeight;
    }

    function makeParticle() {
      var red = Math.random() < RED_SHARE;
      return {
        x:   Math.random() * W,
        y:   Math.random() * H,
        vx:  (Math.random() - 0.5) * SPEED,
        vy:  (Math.random() - 0.5) * SPEED,
        r:   Math.random() * 1.6 + 0.5,
        red: red,
        a:   red ? 0.55 : (Math.random() * 0.25 + 0.08),
        phase: Math.random() * Math.PI * 2   // for pulsing
      };
    }

    function setup() {
      resize();
      parts = [];
      for (var i = 0; i < N_PARTICLES; i++) parts.push(makeParticle());
    }

    var tick = 0;

    function draw() {
      ctx.clearRect(0, 0, W, H);
      tick += 0.012;

      // ── Draw connection lines first ───────────────────────────────────────
      for (var i = 0; i < parts.length; i++) {
        var a = parts[i];
        for (var j = i + 1; j < parts.length; j++) {
          var b  = parts[j];
          var dx = a.x - b.x;
          var dy = a.y - b.y;
          var d  = Math.sqrt(dx * dx + dy * dy);
          if (d >= LINK_DIST) continue;

          var fade    = 1 - d / LINK_DIST;
          var anyRed  = a.red || b.red;
          var opacity = anyRed ? fade * 0.18 : fade * 0.07;

          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = anyRed ? RED + opacity + ')' : WHITE + opacity + ')';
          ctx.lineWidth   = 0.6;
          ctx.stroke();
        }
      }

      // ── Draw particles ────────────────────────────────────────────────────
      for (var k = 0; k < parts.length; k++) {
        var p = parts[k];

        if (p.red) {
          // Pulsing glow
          var pulse  = 0.5 + 0.5 * Math.sin(tick * 2.2 + p.phase);
          var alpha  = 0.35 + pulse * 0.45;
          var radius = p.r * (1 + pulse * 0.7);
          var glowR  = radius * 5;

          var grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, glowR);
          grad.addColorStop(0, RED + (alpha * 0.6) + ')');
          grad.addColorStop(0.4, RED + (alpha * 0.15) + ')');
          grad.addColorStop(1, RED + '0)');
          ctx.beginPath();
          ctx.arc(p.x, p.y, glowR, 0, Math.PI * 2);
          ctx.fillStyle = grad;
          ctx.fill();

          ctx.beginPath();
          ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
          ctx.fillStyle = RED + alpha + ')';
          ctx.fill();
        } else {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
          ctx.fillStyle = WHITE + p.a + ')';
          ctx.fill();
        }

        // Move
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -5)     p.x = W + 5;
        if (p.x > W + 5)  p.x = -5;
        if (p.y < -5)     p.y = H + 5;
        if (p.y > H + 5)  p.y = -5;
      }

      requestAnimationFrame(draw);
    }

    setup();
    draw();
    window.addEventListener('resize', setup);
  }


  // ══════════════════════════════════════════════════════════════════════════
  // 2. SCANLINE BROADCAST OVERLAY — subtle TV scan effect on hero
  // ══════════════════════════════════════════════════════════════════════════
  function initScanlines(hero) {
    var overlay = document.createElement('div');
    overlay.setAttribute('aria-hidden', 'true');
    overlay.style.cssText = [
      'position:absolute', 'top:0', 'left:0',
      'width:100%', 'height:100%',
      'pointer-events:none',
      'z-index:1',
      'background:repeating-linear-gradient(',
        'to bottom,',
        'transparent 0px,',
        'transparent 3px,',
        'rgba(0,0,0,0.06) 3px,',
        'rgba(0,0,0,0.06) 4px',
      ')',
      'animation:scanMove 8s linear infinite'
    ].join('');
    hero.appendChild(overlay);
  }


  // ══════════════════════════════════════════════════════════════════════════
  // 3. SCROLL REVEAL — fade + rise on cards and sections
  // ══════════════════════════════════════════════════════════════════════════
  function initScrollReveal() {
    if (!window.IntersectionObserver) return;

    var selectors = [
      '.pillar-card',
      '.feature-card',
      '.price-card',
      '.for-card',
      '.why-item',
      '.why-visual',
      '.preview-card',
      '.stat-card'
    ].join(', ');

    var elements = document.querySelectorAll(selectors);
    if (!elements.length) return;

    // Sort into row groups by approximate top offset for staggered delays
    elements.forEach(function (el) {
      el.style.opacity   = '0';
      el.style.transform = 'translateY(28px)';
      el.style.willChange = 'opacity, transform';
    });

    // Group siblings for stagger
    function getDelay(el) {
      var siblings = el.parentElement ? el.parentElement.children : [];
      var idx = 0;
      for (var i = 0; i < siblings.length; i++) {
        if (siblings[i] === el) { idx = i; break; }
      }
      return Math.min(idx * 90, 360); // max 360ms stagger
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el    = entry.target;
        var delay = getDelay(el);
        el.style.transition = [
          'opacity 0.55s ease ' + delay + 'ms',
          'transform 0.55s cubic-bezier(0.22,1,0.36,1) ' + delay + 'ms'
        ].join(', ');
        el.style.opacity   = '1';
        el.style.transform = 'translateY(0)';
        observer.unobserve(el);
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    elements.forEach(function (el) { observer.observe(el); });
  }


  // ══════════════════════════════════════════════════════════════════════════
  // 4. ANIMATED COUNTERS — rolls up numeric hero stats on scroll entry
  // ══════════════════════════════════════════════════════════════════════════
  function animateNum(el) {
    var raw = el.textContent.trim();
    // Only animate if it looks like a plain number (with optional leading $)
    var match = raw.match(/^(\$?)(\d+)(\+?)$/);
    if (!match) return;

    var prefix = match[1];
    var target = parseInt(match[2], 10);
    var suffix = match[3];
    var duration = 1100;
    var startTime = null;

    function step(ts) {
      if (!startTime) startTime = ts;
      var progress = Math.min((ts - startTime) / duration, 1);
      var eased    = 1 - Math.pow(1 - progress, 3);
      var value    = Math.round(eased * target);
      el.textContent = prefix + value.toLocaleString() + suffix;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function initCounters() {
    if (!window.IntersectionObserver) return;

    var els = document.querySelectorAll('.hero-stat-value');
    if (!els.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        animateNum(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.5 });

    els.forEach(function (el) { observer.observe(el); });
  }


  // ══════════════════════════════════════════════════════════════════════════
  // 5. NAV SCROLL SHADOW — deepen nav border on scroll
  // ══════════════════════════════════════════════════════════════════════════
  function initNavScroll() {
    var nav = document.querySelector('nav');
    if (!nav) return;
    window.addEventListener('scroll', function () {
      if (window.scrollY > 10) {
        nav.style.borderBottomColor = 'rgba(232,24,28,0.2)';
        nav.style.boxShadow = '0 1px 32px rgba(0,0,0,0.6)';
      } else {
        nav.style.borderBottomColor = '';
        nav.style.boxShadow = '';
      }
    }, { passive: true });
  }


  // ══════════════════════════════════════════════════════════════════════════
  // INJECT KEYFRAMES (scanline movement, shared pulse)
  // ══════════════════════════════════════════════════════════════════════════
  function injectStyles() {
    var style = document.createElement('style');
    style.textContent = [
      '@keyframes scanMove{',
        'from{background-position:0 0}',
        'to{background-position:0 40px}',
      '}',
      // Smooth transition default for revealed elements
      '.bmb-revealed{transition:opacity 0.55s ease,transform 0.55s cubic-bezier(0.22,1,0.36,1);}'
    ].join('');
    document.head.appendChild(style);
  }


  // ══════════════════════════════════════════════════════════════════════════
  // INIT
  // ══════════════════════════════════════════════════════════════════════════
  function init() {
    injectStyles();

    var hero = document.querySelector('.hero');
    if (hero) {
      initParticles(hero);
      initScanlines(hero);
    }

    initScrollReveal();
    initCounters();
    initNavScroll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
