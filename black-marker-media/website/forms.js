/**
 * forms.js — BMB Form System
 * Renders lead, contact, signup, and booking forms.
 * Inline or modal. Submits to local server at /api/submit-form.
 *
 * Auto-init via data attributes:
 *   <div data-bmb-form="lead"></div>              → inline form
 *   <a data-bmb-modal="booking">Book Now</a>      → opens modal on click
 *   <a data-bmb-modal="lead"
 *      data-bmb-preset-interest="ChannelCast Pro">Get Started</a>
 */
(function () {
  'use strict';

  var ENDPOINT = '/api/submit-form';

  // ── Form definitions ───────────────────────────────────────────────────────
  var CONFIGS = {

    lead: {
      eyebrow:  'Get Started',
      title:    'Tell Us About Your Project',
      subtitle: "We'll follow up within 24 hours to learn more and figure out the right fit.",
      submit:   'Send My Request',
      success_title:   "Request received.",
      success_body:    "We'll be in touch within 24 hours. Check your inbox.",
      fields: [
        { name:'name',     label:'Full Name',              type:'text',     required:true  },
        { name:'email',    label:'Email Address',          type:'email',    required:true  },
        { name:'phone',    label:'Phone Number',           type:'tel',      required:false },
        { name:'company',  label:'Organization / Company', type:'text',     required:false },
        {
          name:'interest', label:"I'm interested in", type:'select', required:true,
          options:['ChannelCast Platform','Live Production Services','BlackMarker.TV Network','General / All Three']
        },
        { name:'message', label:'Anything else we should know?', type:'textarea', required:false, placeholder:"Project details, timeline, budget range, questions..." }
      ]
    },

    contact: {
      eyebrow:  'Send a Message',
      title:    "Let's Talk",
      subtitle: 'Questions, press, partnerships, or just curious — we read everything.',
      submit:   'Send Message',
      success_title: "Message sent.",
      success_body:  "We read every message and will get back to you soon.",
      fields: [
        { name:'name',    label:'Your Name',     type:'text',     required:true  },
        { name:'email',   label:'Email Address', type:'email',    required:true  },
        { name:'message', label:'Message',       type:'textarea', required:true, placeholder:"What's on your mind?" }
      ]
    },

    signup: {
      eyebrow:  'Stay Updated',
      title:    'Get BMB Updates',
      subtitle: 'New features, events, industry insights — no spam, unsubscribe any time.',
      submit:   'Subscribe',
      success_title: "You're on the list.",
      success_body:  "We'll send updates when there's something worth sharing.",
      fields: [
        { name:'name',  label:'First Name',     type:'text',  required:false },
        { name:'email', label:'Email Address',  type:'email', required:true  }
      ]
    },

    booking: {
      eyebrow:  'Book Production',
      title:    'Request an Event Quote',
      subtitle: "Fill in your event details and we'll get back to you within 48 hours with a quote.",
      submit:   'Request a Quote',
      success_title: "Quote request received.",
      success_body:  "We'll follow up within 48 hours with pricing and availability.",
      fields: [
        { name:'name',    label:'Full Name',           type:'text',     required:true  },
        { name:'email',   label:'Email Address',       type:'email',    required:true  },
        { name:'phone',   label:'Phone Number',        type:'tel',      required:true  },
        { name:'company', label:'Organization / Venue',type:'text',     required:false },
        {
          name:'event_type', label:'Event Type', type:'select', required:true,
          options:['Corporate Event','Church / Religious Service','Sports Event','Concert / Performance','Conference / Summit','Wedding / Private Event','Other']
        },
        { name:'event_date', label:'Event Date (if known)', type:'date', required:false },
        { name:'message', label:'Event Details', type:'textarea', required:false,
          placeholder:"Location, expected attendance, streaming destinations, camera setup needs, special requirements..." }
      ]
    },

    sponsor: {
      eyebrow:  'Sponsorship',
      title:    'Sponsorship Inquiry',
      subtitle: 'Tell us about your brand and what you are looking to achieve on BlackMarker.TV.',
      submit:   'Send Inquiry',
      success_title: "Inquiry received.",
      success_body:  "Our partnerships team will reach out within 2 business days.",
      fields: [
        { name:'name',    label:'Your Name',            type:'text',  required:true  },
        { name:'email',   label:'Email Address',        type:'email', required:true  },
        { name:'company', label:'Brand / Company Name', type:'text',  required:true  },
        { name:'phone',   label:'Phone Number',         type:'tel',   required:false },
        { name:'message', label:'Tell us about your sponsorship goals', type:'textarea', required:false,
          placeholder:"Budget range, target audience, campaign goals, preferred placement..." }
      ]
    },

    creator: {
      eyebrow:  'Creator Pitch',
      title:    'Pitch Your Show',
      subtitle: "Got a concept for BlackMarker.TV? We're always looking for the next great show.",
      submit:   'Submit My Pitch',
      success_title: "Pitch received.",
      success_body:  "Our programming team reviews all pitches. We'll be in touch if it's a fit.",
      fields: [
        { name:'name',    label:'Your Name',     type:'text',  required:true  },
        { name:'email',   label:'Email Address', type:'email', required:true  },
        { name:'phone',   label:'Phone Number',  type:'tel',   required:false },
        { name:'message', label:'Pitch Details', type:'textarea', required:true,
          placeholder:"Show title, concept summary, format, your background, existing audience (if any)..." }
      ]
    }

  };

  // ── Styles ────────────────────────────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById('bmb-forms-style')) return;
    var s = document.createElement('style');
    s.id = 'bmb-forms-style';
    s.textContent = [

      /* ── overlay ── */
      '#bmb-overlay{',
        'display:none;position:fixed;inset:0;z-index:99990;',
        'background:rgba(0,0,0,0.88);backdrop-filter:blur(4px);',
        'overflow-y:auto;padding:40px 16px;',
        'align-items:flex-start;justify-content:center;',
      '}',
      '#bmb-overlay.open{display:flex;}',

      /* ── dialog ── */
      '#bmb-dialog{',
        'position:relative;background:#0d0d0d;',
        'border:1px solid #1e1e1e;border-radius:14px;',
        'width:100%;max-width:540px;',
        'box-shadow:0 24px 80px rgba(0,0,0,0.9);',
        'animation:bmbSlideIn 0.28s cubic-bezier(0.22,1,0.36,1);',
        'margin:auto;',
      '}',
      '@keyframes bmbSlideIn{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}',

      /* ── close button ── */
      '#bmb-close{',
        'position:absolute;top:16px;right:16px;',
        'width:32px;height:32px;border-radius:50%;',
        'background:#1a1a1a;border:1px solid #2a2a2a;',
        'color:#666;font-size:18px;line-height:1;',
        'cursor:pointer;display:flex;align-items:center;justify-content:center;',
        'transition:all 0.15s;font-family:inherit;',
      '}',
      '#bmb-close:hover{background:#222;color:#ccc;border-color:#444;}',

      /* ── form wrapper (shared by modal + inline) ── */
      '.bmb-form{',
        'font-family:Inter,system-ui,sans-serif;',
        'color:#e0e0e0;',
      '}',
      '.bmb-form-inner{padding:40px 40px 36px;}',

      /* ── header ── */
      '.bmb-form-eyebrow{',
        'font-size:10px;font-weight:700;letter-spacing:0.14em;',
        'text-transform:uppercase;color:#E8181C;margin-bottom:10px;',
      '}',
      '.bmb-form-title{',
        'font-size:26px;font-weight:900;letter-spacing:-0.5px;',
        'color:#fff;line-height:1.1;margin-bottom:8px;',
      '}',
      '.bmb-form-sub{',
        'font-size:13px;color:#666;line-height:1.6;margin-bottom:28px;',
      '}',

      /* ── fields ── */
      '.bmb-field{margin-bottom:16px;}',
      '.bmb-field-lbl{',
        'display:block;font-size:11px;font-weight:700;',
        'color:#555;letter-spacing:0.06em;text-transform:uppercase;',
        'margin-bottom:6px;',
      '}',
      '.bmb-field-lbl .bmb-req{color:#E8181C;margin-left:2px;}',
      '.bmb-ctrl{',
        'width:100%;background:#080808;border:1px solid #1e1e1e;',
        'border-radius:6px;color:#e0e0e0;font-size:14px;',
        'padding:10px 12px;font-family:inherit;',
        'outline:none;transition:border-color 0.15s;box-sizing:border-box;',
        'appearance:none;',
      '}',
      '.bmb-ctrl:focus{border-color:rgba(232,24,28,0.55);}',
      '.bmb-ctrl::placeholder{color:#333;}',
      'textarea.bmb-ctrl{resize:vertical;min-height:100px;line-height:1.5;}',
      'select.bmb-ctrl{',
        'background-image:url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'12\' height=\'8\' viewBox=\'0 0 12 8\'%3E%3Cpath d=\'M1 1l5 5 5-5\' stroke=\'%23555\' stroke-width=\'1.5\' fill=\'none\'/%3E%3C/svg%3E");',
        'background-repeat:no-repeat;background-position:right 12px center;',
        'padding-right:36px;cursor:pointer;',
      '}',
      'input[type="date"].bmb-ctrl::-webkit-calendar-picker-indicator{filter:invert(0.4);}',

      /* ── field error ── */
      '.bmb-field-err{',
        'display:none;font-size:11px;color:#E8181C;margin-top:5px;',
      '}',
      '.bmb-field.has-error .bmb-ctrl{border-color:rgba(232,24,28,0.6);}',
      '.bmb-field.has-error .bmb-field-err{display:block;}',

      /* ── two-col row ── */
      '.bmb-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;}',
      '@media(max-width:480px){.bmb-row{grid-template-columns:1fr;}}',

      /* ── submit button ── */
      '.bmb-submit{',
        'width:100%;background:#E8181C;color:#fff;',
        'border:none;border-radius:7px;',
        'font-size:15px;font-weight:700;',
        'padding:13px 24px;cursor:pointer;',
        'font-family:inherit;margin-top:8px;',
        'transition:background 0.15s,opacity 0.15s;',
        'position:relative;',
      '}',
      '.bmb-submit:hover{background:#B01212;}',
      '.bmb-submit:disabled{opacity:0.55;cursor:not-allowed;}',
      '.bmb-submit .bmb-spinner{',
        'display:none;width:16px;height:16px;',
        'border:2px solid rgba(255,255,255,0.3);',
        'border-top-color:#fff;border-radius:50%;',
        'animation:bmbSpin 0.7s linear infinite;',
        'position:absolute;right:16px;top:50%;transform:translateY(-50%);',
      '}',
      '.bmb-submit.loading .bmb-spinner{display:block;}',
      '@keyframes bmbSpin{to{transform:translateY(-50%) rotate(360deg)}}',

      /* ── form error banner ── */
      '.bmb-form-banner{',
        'display:none;background:rgba(232,24,28,0.08);',
        'border:1px solid rgba(232,24,28,0.2);border-radius:6px;',
        'color:#E8181C;font-size:12px;padding:10px 14px;',
        'margin-bottom:14px;',
      '}',
      '.bmb-form-banner.show{display:block;}',

      /* ── success state ── */
      '.bmb-success{',
        'display:none;padding:56px 40px;text-align:center;',
      '}',
      '.bmb-success.show{display:block;}',
      '.bmb-success-check{',
        'width:56px;height:56px;border-radius:50%;',
        'background:rgba(76,175,80,0.12);border:1px solid rgba(76,175,80,0.3);',
        'display:flex;align-items:center;justify-content:center;',
        'margin:0 auto 20px;',
        'font-size:22px;color:#4caf50;',
      '}',
      '.bmb-success-title{',
        'font-size:22px;font-weight:800;color:#fff;',
        'letter-spacing:-0.3px;margin-bottom:10px;',
      '}',
      '.bmb-success-body{font-size:14px;color:#666;line-height:1.6;}',
      '.bmb-success-close{',
        'display:inline-block;margin-top:28px;',
        'background:#1a1a1a;border:1px solid #2a2a2a;',
        'border-radius:6px;color:#888;font-size:13px;',
        'font-weight:600;padding:9px 22px;cursor:pointer;',
        'font-family:inherit;transition:all 0.15s;',
      '}',
      '.bmb-success-close:hover{border-color:#444;color:#ccc;}',

      /* ── inline form wrapper ── */
      '.bmb-inline-wrap{',
        'background:#0d0d0d;border:1px solid #1e1e1e;border-radius:12px;',
        'overflow:hidden;',
      '}',

      /* ── privacy note ── */
      '.bmb-privacy{',
        'font-size:11px;color:#333;text-align:center;',
        'margin-top:14px;line-height:1.5;',
      '}',

    ].join('');
    document.head.appendChild(s);
  }

  // ── Build modal shell (created once) ─────────────────────────────────────
  var overlay, dialog, dialogContent;

  function buildModal() {
    if (document.getElementById('bmb-overlay')) return;

    overlay = document.createElement('div');
    overlay.id = 'bmb-overlay';

    dialog = document.createElement('div');
    dialog.id = 'bmb-dialog';

    var closeBtn = document.createElement('button');
    closeBtn.id = 'bmb-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.addEventListener('click', closeModal);

    dialogContent = document.createElement('div');
    dialogContent.id = 'bmb-dialog-content';

    dialog.appendChild(closeBtn);
    dialog.appendChild(dialogContent);
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    // Close on overlay click (outside dialog)
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    // Close on ESC
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && overlay.classList.contains('open')) closeModal();
    });
  }

  function openModal(type, presets) {
    if (!overlay) buildModal();
    dialogContent.innerHTML = '';
    dialogContent.appendChild(renderForm(type, presets));
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    // Focus first input
    setTimeout(function () {
      var first = dialog.querySelector('input,select,textarea');
      if (first) first.focus();
    }, 80);
  }

  function closeModal() {
    if (overlay) overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  // ── Render form ───────────────────────────────────────────────────────────
  function renderForm(type, presets) {
    var cfg = CONFIGS[type];
    if (!cfg) {
      var err = document.createElement('div');
      err.style.cssText = 'padding:40px;color:#E8181C;font-family:Inter,sans-serif;';
      err.textContent = 'Unknown form type: ' + type;
      return err;
    }

    var wrap = document.createElement('div');
    wrap.className = 'bmb-form';

    // Success state
    var success = document.createElement('div');
    success.className = 'bmb-success';
    success.innerHTML =
      '<div class="bmb-success-check">&#10003;</div>' +
      '<div class="bmb-success-title">' + esc(cfg.success_title) + '</div>' +
      '<p class="bmb-success-body">' + esc(cfg.success_body) + '</p>' +
      '<button class="bmb-success-close">Close</button>';
    success.querySelector('.bmb-success-close').addEventListener('click', function () {
      var modal = document.getElementById('bmb-overlay');
      if (modal && modal.classList.contains('open')) {
        closeModal();
      } else {
        // Inline: reset form
        wrap.querySelector('.bmb-form-inner').style.display = '';
        success.classList.remove('show');
      }
    });

    // Form inner
    var inner = document.createElement('div');
    inner.className = 'bmb-form-inner';

    // Header
    inner.innerHTML =
      '<div class="bmb-form-eyebrow">' + esc(cfg.eyebrow) + '</div>' +
      '<h3 class="bmb-form-title">' + esc(cfg.title) + '</h3>' +
      '<p class="bmb-form-sub">' + esc(cfg.subtitle) + '</p>';

    // Error banner
    var banner = document.createElement('div');
    banner.className = 'bmb-form-banner';
    banner.textContent = 'Please fix the errors below and try again.';
    inner.appendChild(banner);

    // Form element
    var form = document.createElement('form');
    form.noValidate = true;

    // Hidden field for form_type
    var typeInput = document.createElement('input');
    typeInput.type = 'hidden';
    typeInput.name = 'form_type';
    typeInput.value = type;
    form.appendChild(typeInput);

    // Render fields
    cfg.fields.forEach(function (field, i) {
      var fieldEl = buildField(field, presets);
      form.appendChild(fieldEl);
    });

    // Submit button
    var submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.className = 'bmb-submit';
    submitBtn.innerHTML = esc(cfg.submit) + '<span class="bmb-spinner"></span>';
    form.appendChild(submitBtn);

    // Privacy note
    var privacy = document.createElement('p');
    privacy.className = 'bmb-privacy';
    privacy.textContent = 'We respect your privacy. No spam, ever.';
    form.appendChild(privacy);

    // Form submit handler
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      handleSubmit(form, submitBtn, banner, inner, success);
    });

    inner.appendChild(form);
    wrap.appendChild(inner);
    wrap.appendChild(success);
    return wrap;
  }

  // ── Build individual field ────────────────────────────────────────────────
  function buildField(field, presets) {
    // Check if two short fields should share a row (name+email, name+phone)
    var fieldWrap = document.createElement('div');
    fieldWrap.className = 'bmb-field';
    fieldWrap.setAttribute('data-field', field.name);

    var label = document.createElement('label');
    label.className = 'bmb-field-lbl';
    label.textContent = field.label;
    if (field.required) {
      var req = document.createElement('span');
      req.className = 'bmb-req';
      req.textContent = '*';
      label.appendChild(req);
    }

    var ctrl;
    if (field.type === 'textarea') {
      ctrl = document.createElement('textarea');
      ctrl.rows = 4;
      if (field.placeholder) ctrl.placeholder = field.placeholder;
    } else if (field.type === 'select') {
      ctrl = document.createElement('select');
      // Blank default option
      var blank = document.createElement('option');
      blank.value = '';
      blank.textContent = 'Select one\u2026';
      blank.disabled = true;
      blank.selected = true;
      ctrl.appendChild(blank);
      field.options.forEach(function (opt) {
        var o = document.createElement('option');
        o.value = opt;
        o.textContent = opt;
        ctrl.appendChild(o);
      });
    } else {
      ctrl = document.createElement('input');
      ctrl.type = field.type;
      if (field.placeholder) ctrl.placeholder = field.placeholder;
    }

    ctrl.name = field.name;
    ctrl.className = 'bmb-ctrl';
    if (field.required) ctrl.required = true;

    // Apply preset value if provided
    if (presets && presets[field.name]) {
      ctrl.value = presets[field.name];
    }

    // Error span
    var errSpan = document.createElement('span');
    errSpan.className = 'bmb-field-err';

    fieldWrap.appendChild(label);
    fieldWrap.appendChild(ctrl);
    fieldWrap.appendChild(errSpan);

    // Clear error on change
    ctrl.addEventListener('input', function () {
      fieldWrap.classList.remove('has-error');
    });

    return fieldWrap;
  }

  // ── Validation ────────────────────────────────────────────────────────────
  var EMAIL_RX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function validate(form) {
    var fields = form.querySelectorAll('[data-field]');
    var valid = true;

    fields.forEach(function (fieldWrap) {
      var ctrl = fieldWrap.querySelector('.bmb-ctrl');
      var errSpan = fieldWrap.querySelector('.bmb-field-err');
      var val = ctrl.value.trim();
      var msg = '';

      if (ctrl.required && !val) {
        msg = 'This field is required.';
      } else if (ctrl.type === 'email' && val && !EMAIL_RX.test(val)) {
        msg = 'Please enter a valid email address.';
      } else if (ctrl.type === 'tel' && val && !/^[\d\s\+\-\(\)\.]{7,}$/.test(val)) {
        msg = 'Please enter a valid phone number.';
      }

      if (msg) {
        fieldWrap.classList.add('has-error');
        errSpan.textContent = msg;
        valid = false;
      } else {
        fieldWrap.classList.remove('has-error');
        errSpan.textContent = '';
      }
    });

    return valid;
  }

  // ── Submission ────────────────────────────────────────────────────────────
  function handleSubmit(form, btn, banner, inner, success) {
    banner.classList.remove('show');

    if (!validate(form)) {
      banner.classList.add('show');
      // Scroll to first error
      var firstErr = form.querySelector('.has-error .bmb-ctrl');
      if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    // Collect form data
    var data = {};
    var formData = new FormData(form);
    formData.forEach(function (val, key) { data[key] = val; });

    // UI: loading state
    btn.disabled = true;
    btn.classList.add('loading');
    var originalText = btn.firstChild.nodeValue || btn.textContent.replace('', '').trim();

    fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
      btn.disabled = false;
      btn.classList.remove('loading');
      if (res.success) {
        inner.style.display = 'none';
        success.classList.add('show');
      } else {
        banner.textContent = res.error || 'Something went wrong. Please try again.';
        banner.classList.add('show');
      }
    })
    .catch(function () {
      btn.disabled = false;
      btn.classList.remove('loading');
      banner.textContent = 'Network error — please check your connection and try again.';
      banner.classList.add('show');
    });
  }

  // ── Auto-init ─────────────────────────────────────────────────────────────
  function init() {
    injectStyles();

    // Inline forms: <div data-bmb-form="lead"></div>
    document.querySelectorAll('[data-bmb-form]').forEach(function (container) {
      var type = container.getAttribute('data-bmb-form');
      var presets = readPresets(container);
      var wrap = document.createElement('div');
      wrap.className = 'bmb-inline-wrap';
      wrap.appendChild(renderForm(type, presets));
      container.appendChild(wrap);
    });

    // Modal triggers: <a data-bmb-modal="lead">...</a>
    document.querySelectorAll('[data-bmb-modal]').forEach(function (trigger) {
      var type = trigger.getAttribute('data-bmb-modal');
      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        var presets = readPresets(trigger);
        openModal(type, presets);
      });
    });
  }

  // Read data-bmb-preset-* attributes as preset object
  function readPresets(el) {
    var presets = {};
    Array.prototype.forEach.call(el.attributes, function (attr) {
      var m = attr.name.match(/^data-bmb-preset-(.+)$/);
      if (m) presets[m[1].replace(/-/g, '_')] = attr.value;
    });
    return Object.keys(presets).length ? presets : null;
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function esc(str) {
    return (str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── Public API ────────────────────────────────────────────────────────────
  window.BMBForms = {
    open: openModal,
    close: closeModal,
    render: renderForm
  };

  // ── Run ───────────────────────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
