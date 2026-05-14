/**
 * editor.js — BMB Inline Page Editor
 * Activates only on localhost. Click any text element to edit it in place.
 * Save writes the updated HTML back to disk via the local server.
 *
 * Usage: <script src="editor.js"></script> at the bottom of any page.
 */
(function () {
  'use strict';

  // ── Localhost guard ───────────────────────────────────────────────────────
  var host = window.location.hostname;
  if (host !== 'localhost' && host !== '127.0.0.1' && host !== '') return;

  // ── State ─────────────────────────────────────────────────────────────────
  var editMode     = false;
  var dirty        = false;
  var activeEl     = null;
  var linkTarget   = null;
  var idCounter    = 0;
  var snapshots    = {};   // data-bmb-id → original innerHTML

  // ── Editable selectors (covers all 5 pages) ───────────────────────────────
  var EDITABLE_SEL = [
    'h1','h2','h3','h4','h5','h6','p',
    '.section-eyebrow','.eyebrow','.hero-eyebrow',
    '.section-title','.section-sub','.hero-sub','.hero-tagline',
    '.pillar-title','.pillar-sub','.pillar-number','.pillar-tag','.pillar-link',
    '.feature-title','.feature-text',
    '.for-title','.for-text',
    '.service-title','.service-text','.service-num',
    '.serve-title','.serve-text',
    '.prog-title','.prog-text','.prog-type',
    '.aud-title','.aud-sub','.aud-tag',
    '.why-item-title','.why-item-text',
    '.hero-stat-value','.hero-stat-label',
    '.stat-value','.stat-label',
    '.why-visual-value','.why-visual-label',
    '.stream-title','.stream-meta-value','.stream-meta-label',
    '.price-name','.price-amount','.price-period','.price-feature',
    '.formula-result','.formula-label','.formula-pill',
    '.investor-text h2','.investor-text p',
    '.cta-inner h2','.cta-inner p',
    '.footer-brand-name','.footer-brand-text','.footer-copy','.footer-mark-text',
    '.live-text','.btn-primary','.btn-secondary','.nav-cta',
    '.preview-card-label','.preview-card-stat',
    '.aud-item','.service-bullet'
  ].join(',');

  // ── Styles ────────────────────────────────────────────────────────────────
  function injectStyles() {
    var s = document.createElement('style');
    s.setAttribute('data-bmb-editor', '');
    s.textContent = '\
[data-bmb-editable]{\
  cursor:text!important;\
  transition:outline 0.1s;\
}\
[data-bmb-editable]:hover{\
  outline:1px dashed rgba(232,24,28,0.55)!important;\
  outline-offset:3px;\
}\
[data-bmb-editable][contenteditable="true"]{\
  outline:2px solid #E8181C!important;\
  outline-offset:3px;\
  background:rgba(232,24,28,0.05)!important;\
  border-radius:3px;\
  min-width:20px;\
  display:inline-block;\
}\
[data-bmb-link]:hover{\
  cursor:pointer!important;\
  outline:1px dashed rgba(99,179,237,0.6)!important;\
  outline-offset:3px;\
}\
#bmb-bar{\
  position:fixed;bottom:20px;right:20px;z-index:2147483647;\
  display:flex;align-items:center;gap:8px;\
  background:#0d0d0d;border:1px solid #222;\
  border-radius:10px;padding:9px 13px;\
  font-family:Inter,system-ui,sans-serif;font-size:12px;\
  box-shadow:0 4px 28px rgba(0,0,0,0.8);\
  transition:border-color 0.2s;\
}\
#bmb-bar.active{border-color:rgba(232,24,28,0.35);}\
.bmb-label{\
  font-size:10px;font-weight:700;color:#333;\
  letter-spacing:0.12em;text-transform:uppercase;\
}\
.bmb-sep{width:1px;height:14px;background:#222;}\
#bmb-toggle{\
  display:flex;align-items:center;gap:7px;\
  background:#161616;border:1px solid #2a2a2a;\
  border-radius:6px;color:#666;font-size:12px;\
  font-weight:600;padding:5px 11px;cursor:pointer;\
  font-family:inherit;transition:all 0.15s;white-space:nowrap;\
}\
#bmb-toggle:hover{border-color:#444;color:#aaa;}\
#bmb-toggle.on{\
  background:rgba(232,24,28,0.1);\
  border-color:rgba(232,24,28,0.4);color:#E8181C;\
}\
#bmb-toggle .bmb-dot{\
  width:6px;height:6px;border-radius:50%;background:currentColor;\
}\
#bmb-save{\
  display:none;background:#161616;border:1px solid #2a2a2a;\
  border-radius:6px;color:#444;font-size:12px;font-weight:600;\
  padding:5px 12px;cursor:pointer;font-family:inherit;\
  transition:all 0.15s;white-space:nowrap;\
}\
#bmb-save.dirty{\
  background:#E8181C;border-color:#E8181C;color:#fff;\
}\
#bmb-save.dirty:hover{background:#B01212;}\
#bmb-status{\
  font-size:11px;color:#333;min-width:56px;text-align:right;\
}\
#bmb-status.ok{color:#4caf50;}\
#bmb-status.err{color:#E8181C;}\
#bmb-banner{\
  display:none;position:fixed;top:64px;left:0;right:0;z-index:2147483646;\
  background:rgba(232,24,28,0.07);border-bottom:1px solid rgba(232,24,28,0.18);\
  padding:7px 40px;text-align:center;pointer-events:none;\
  font-family:Inter,system-ui,sans-serif;font-size:11px;font-weight:600;\
  color:rgba(232,24,28,0.7);letter-spacing:0.05em;\
}\
#bmb-link-popup{\
  display:none;position:fixed;z-index:2147483647;\
  background:#111;border:1px solid #2a2a2a;border-radius:10px;\
  padding:16px;box-shadow:0 8px 40px rgba(0,0,0,0.85);\
  font-family:Inter,system-ui,sans-serif;min-width:300px;\
}\
.bmb-field-label{\
  display:block;font-size:10px;font-weight:700;color:#444;\
  letter-spacing:0.1em;text-transform:uppercase;margin-bottom:5px;\
}\
.bmb-field-input{\
  width:100%;background:#0a0a0a;border:1px solid #2a2a2a;\
  border-radius:5px;color:#ccc;font-size:12px;padding:7px 10px;\
  font-family:inherit;margin-bottom:11px;outline:none;box-sizing:border-box;\
}\
.bmb-field-input:focus{border-color:rgba(232,24,28,0.5);}\
.bmb-pop-row{display:flex;gap:8px;justify-content:flex-end;margin-top:4px;}\
.bmb-pop-btn{\
  background:#1a1a1a;border:1px solid #2a2a2a;border-radius:5px;\
  color:#666;font-size:11px;font-weight:600;padding:6px 13px;\
  cursor:pointer;font-family:inherit;transition:all 0.1s;\
}\
.bmb-pop-btn:hover{border-color:#444;color:#aaa;}\
.bmb-pop-btn.primary{background:#E8181C;border-color:#E8181C;color:#fff;}\
.bmb-pop-btn.primary:hover{background:#B01212;}\
';
    document.head.appendChild(s);
  }

  // ── Build UI ──────────────────────────────────────────────────────────────
  function buildUI() {
    // Floating bar
    var bar = el('div', { id:'bmb-bar', 'data-bmb-editor':'' });
    bar.innerHTML =
      '<span class="bmb-label">BMB</span>' +
      '<div class="bmb-sep"></div>' +
      '<button id="bmb-toggle"><span class="bmb-dot"></span>\u00a0Edit Mode</button>' +
      '<button id="bmb-save">Save Page</button>' +
      '<span id="bmb-status"></span>';
    document.body.appendChild(bar);

    // Banner
    var banner = el('div', { id:'bmb-banner', 'data-bmb-editor':'' });
    banner.textContent = 'EDIT MODE \u2014 Click any highlighted element to edit text \u2022 Click blue-outlined links to edit URL \u2022 ESC to cancel \u2022 Save when done';
    document.body.appendChild(banner);

    // Link popup
    var popup = el('div', { id:'bmb-link-popup', 'data-bmb-editor':'' });
    popup.innerHTML =
      '<label class="bmb-field-label">Link Text</label>' +
      '<input class="bmb-field-input" id="bmb-lp-text" type="text"/>' +
      '<label class="bmb-field-label">URL (href)</label>' +
      '<input class="bmb-field-input" id="bmb-lp-href" type="text" placeholder="https://"/>' +
      '<div class="bmb-pop-row">' +
        '<button class="bmb-pop-btn" id="bmb-lp-cancel">Cancel</button>' +
        '<button class="bmb-pop-btn primary" id="bmb-lp-apply">Apply</button>' +
      '</div>';
    document.body.appendChild(popup);

    // Events
    get('bmb-toggle').addEventListener('click', toggleEditMode);
    get('bmb-save').addEventListener('click', savePage);
    get('bmb-lp-cancel').addEventListener('click', closeLinkPopup);
    get('bmb-lp-apply').addEventListener('click', applyLink);

    // Global keydown for ESC
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (get('bmb-link-popup').style.display === 'block') {
          closeLinkPopup();
        } else if (activeEl) {
          revertEl(activeEl);
          deactivateEl(activeEl);
        }
      }
    });

    // Click outside link popup to close it
    document.addEventListener('mousedown', function (e) {
      var popup = get('bmb-link-popup');
      if (popup.style.display === 'block' && !popup.contains(e.target)) {
        closeLinkPopup();
      }
    });

    // Input event for dirty detection (captures typing in contenteditable)
    document.addEventListener('input', function (e) {
      if (editMode && e.target.hasAttribute('data-bmb-editable')) {
        markDirty();
      }
    });
  }

  // ── Toggle edit mode ──────────────────────────────────────────────────────
  function toggleEditMode() {
    editMode = !editMode;
    var toggle = get('bmb-toggle');
    var bar    = get('bmb-bar');
    var banner = get('bmb-banner');
    var save   = get('bmb-save');

    if (editMode) {
      toggle.classList.add('on');
      toggle.innerHTML = '<span class="bmb-dot"></span>\u00a0Editing';
      bar.classList.add('active');
      banner.style.display = 'block';
      save.style.display = 'block';
      markEditables();
    } else {
      toggle.classList.remove('on');
      toggle.innerHTML = '<span class="bmb-dot"></span>\u00a0Edit Mode';
      bar.classList.remove('active');
      banner.style.display = 'none';
      save.style.display = 'none';
      if (activeEl) deactivateEl(activeEl);
      unmarkEditables();
    }
  }

  // ── Mark / unmark editable elements ──────────────────────────────────────
  function markEditables() {
    var candidates = document.querySelectorAll(EDITABLE_SEL);
    candidates.forEach(function (node) {
      if (node.closest('[data-bmb-editor]')) return;
      if (node.closest('nav .nav-links')) return;   // keep nav links functional
      if (!node.textContent.trim()) return;

      // Assign stable ID for snapshotting
      if (!node.getAttribute('data-bmb-id')) {
        node.setAttribute('data-bmb-id', 'b' + (idCounter++));
      }

      if (node.tagName === 'A') {
        node.setAttribute('data-bmb-link', '');
        node.addEventListener('click', onLinkClick, true);  // capture → prevent nav
      } else {
        node.setAttribute('data-bmb-editable', '');
        node.addEventListener('click', onTextClick);
      }
    });
  }

  function unmarkEditables() {
    document.querySelectorAll('[data-bmb-editable]').forEach(function (node) {
      node.removeAttribute('data-bmb-editable');
      node.removeAttribute('contenteditable');
      node.removeEventListener('click', onTextClick);
    });
    document.querySelectorAll('[data-bmb-link]').forEach(function (node) {
      node.removeAttribute('data-bmb-link');
      node.removeEventListener('click', onLinkClick, true);
    });
  }

  // ── Text editing ──────────────────────────────────────────────────────────
  function onTextClick(e) {
    if (!editMode) return;
    e.stopPropagation();

    var node = e.currentTarget;
    if (activeEl === node) return;  // already active

    if (activeEl) deactivateEl(activeEl);
    activateEl(node);
  }

  function activateEl(node) {
    var id = node.getAttribute('data-bmb-id');
    if (!snapshots[id]) snapshots[id] = node.innerHTML;   // save original once

    node.contentEditable = 'true';
    node.focus();
    placeCursorAtEnd(node);
    activeEl = node;

    node.addEventListener('blur', onTextBlur);
  }

  function deactivateEl(node) {
    node.removeAttribute('contenteditable');
    node.removeEventListener('blur', onTextBlur);
    if (activeEl === node) activeEl = null;
  }

  function onTextBlur() {
    var node = this;
    // Small delay so ESC revert can fire before blur finalises
    setTimeout(function () {
      deactivateEl(node);
      markDirty();
    }, 80);
  }

  function revertEl(node) {
    var id = node.getAttribute('data-bmb-id');
    if (snapshots[id] !== undefined) node.innerHTML = snapshots[id];
  }

  // ── Link editing ──────────────────────────────────────────────────────────
  function onLinkClick(e) {
    if (!editMode) return;
    e.preventDefault();
    e.stopPropagation();

    linkTarget = e.currentTarget;
    var id = linkTarget.getAttribute('data-bmb-id');
    if (!snapshots[id]) {
      snapshots[id] = JSON.stringify({
        text: linkTarget.textContent.trim(),
        href: linkTarget.getAttribute('href') || ''
      });
    }

    get('bmb-lp-text').value = linkTarget.textContent.trim();
    get('bmb-lp-href').value = linkTarget.getAttribute('href') || '';

    positionPopup(e.clientX, e.clientY);
    get('bmb-link-popup').style.display = 'block';
    setTimeout(function () { get('bmb-lp-text').focus(); }, 40);
  }

  function closeLinkPopup() {
    get('bmb-link-popup').style.display = 'none';
    linkTarget = null;
  }

  function applyLink() {
    if (!linkTarget) return;
    var text = get('bmb-lp-text').value.trim();
    var href = get('bmb-lp-href').value.trim();
    if (text) linkTarget.textContent = text;
    if (href) linkTarget.setAttribute('href', href);
    closeLinkPopup();
    markDirty();
  }

  // ── Dirty state ───────────────────────────────────────────────────────────
  function markDirty() {
    dirty = true;
    var btn = get('bmb-save');
    btn.classList.add('dirty');
    btn.textContent = 'Save Page \u25cf';
  }

  function clearDirty() {
    dirty = false;
    // Refresh all snapshots to current DOM state
    document.querySelectorAll('[data-bmb-id]').forEach(function (node) {
      var id = node.getAttribute('data-bmb-id');
      if (node.tagName === 'A') {
        snapshots[id] = JSON.stringify({
          text: node.textContent.trim(),
          href: node.getAttribute('href') || ''
        });
      } else {
        snapshots[id] = node.innerHTML;
      }
    });
    var btn = get('bmb-save');
    btn.classList.remove('dirty');
    btn.textContent = 'Save Page';
  }

  // ── Save ──────────────────────────────────────────────────────────────────
  function savePage() {
    setStatus('Saving\u2026', '');

    // Deactivate any open edit first
    if (activeEl) deactivateEl(activeEl);

    // Clone full document
    var clone = document.documentElement.cloneNode(true);

    // Strip editor UI
    clone.querySelectorAll('[data-bmb-editor]').forEach(function (n) { n.remove(); });

    // Strip editor.js script tag
    clone.querySelectorAll('script').forEach(function (n) {
      if ((n.getAttribute('src') || '').indexOf('editor.js') !== -1) n.remove();
    });

    // Clean up editor attributes
    clone.querySelectorAll('[contenteditable]').forEach(function (n) {
      n.removeAttribute('contenteditable');
    });
    clone.querySelectorAll('[data-bmb-editable]').forEach(function (n) {
      n.removeAttribute('data-bmb-editable');
    });
    clone.querySelectorAll('[data-bmb-link]').forEach(function (n) {
      n.removeAttribute('data-bmb-link');
    });
    // Keep data-bmb-id stripped too (not needed in shipped HTML)
    clone.querySelectorAll('[data-bmb-id]').forEach(function (n) {
      n.removeAttribute('data-bmb-id');
    });

    var filename = window.location.pathname.split('/').pop() || 'index.html';
    if (!filename || !filename.endsWith('.html')) filename = 'index.html';

    var html = '<!DOCTYPE html>\n' + clone.outerHTML;

    fetch('/api/save-page', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: filename, html: html })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.success) {
        clearDirty();
        setStatus('Saved \u2713', 'ok');
        setTimeout(function () { setStatus('', ''); }, 3000);
      } else {
        setStatus('Error \u2715', 'err');
        setTimeout(function () { setStatus('', ''); }, 4000);
      }
    })
    .catch(function () {
      setStatus('Error \u2715', 'err');
      setTimeout(function () { setStatus('', ''); }, 4000);
    });
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function get(id) { return document.getElementById(id); }

  function el(tag, attrs) {
    var node = document.createElement(tag);
    Object.keys(attrs).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    return node;
  }

  function setStatus(msg, cls) {
    var s = get('bmb-status');
    if (!s) return;
    s.textContent = msg;
    s.className = cls;
  }

  function placeCursorAtEnd(node) {
    try {
      var range = document.createRange();
      range.selectNodeContents(node);
      range.collapse(false);
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    } catch (e) {}
  }

  function positionPopup(x, y) {
    var popup = get('bmb-link-popup');
    var pw = 320, ph = 160;
    var px = Math.min(x + 8, window.innerWidth - pw - 16);
    var py = (y + ph + 16 > window.innerHeight) ? y - ph - 8 : y + 12;
    popup.style.left = Math.max(8, px) + 'px';
    popup.style.top  = Math.max(8, py) + 'px';
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  function init() {
    injectStyles();
    buildUI();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
