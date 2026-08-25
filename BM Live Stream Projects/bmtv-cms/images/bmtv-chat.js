/*! =====================================================================
 *  BlackMarker.TV live chat — drop-in embed
 *
 *  ONE LINE TO ADD IT TO A PAGE:
 *
 *      <div data-bmtv-chat data-room="main"></div>
 *      <script src="https://<host>/chat/bmtv-chat.js" defer></script>
 *
 *  The script builds the whole panel inside that div — markup, styles and
 *  behaviour. The page supplies nothing but the div and its own layout.
 *
 *  ROOM
 *      data-room on the div wins over ?room= in the URL, so a visitor cannot
 *      retype their way from a public page into a paid room. If the div omits
 *      data-room the URL is consulted, which is the iframe-embed case. Falls
 *      back to 'main'.
 *
 *  MULTIPLE PANELS
 *      Every [data-bmtv-chat] on the page is mounted, each with its own room
 *      and its own realtime channel.
 *
 *  THE KEY IS MEANT TO BE PUBLIC
 *      It ships in every visitor's browser. Every rule that matters lives in
 *      the database — RLS plus triggers — so this file being readable gives
 *      nobody any power. A holder of this key cannot release, hide, delete,
 *      ban, promote themselves, or post as someone else. Never put the
 *      service_role key here; that one bypasses all of it.
 *
 *  STYLING
 *      The panel reads CSS variables from the page when they exist
 *      (--red, --surface, --border, --text, --muted...) and falls back to the
 *      BlackMarker.TV palette when they do not, so it looks right on a bare
 *      page and inherits the site's theme on a styled one.
 *
 *  DEPENDENCY
 *      supabase-js is loaded from jsDelivr if the page has not already loaded
 *      it. A CMS with a strict Content-Security-Policy must allow
 *      cdn.jsdelivr.net and *.supabase.co, or self-host the library and load
 *      it before this file.
 *  ===================================================================== */
(function () {
  'use strict';

  var SUPABASE_URL = 'https://eyqtvdwchwfomhkfjimv.supabase.co';
  var SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5cXR2ZHdjaHdmb21oa2ZqaW12Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY4MTgyNzEsImV4cCI6MjEwMjM5NDI3MX0.8J_Mi9sOt4-BP8NOF2NHkkPcHnN4fXL8p0bUzbn8qu0';
  var SDK = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js';

  var ROOM_RE = /^[a-z0-9][a-z0-9_-]{1,60}$/;
  var PALETTE = ['#E8181C', '#FFC21E', '#37E0C8', '#7C9CFF', '#FF8A3D', '#57D9A3'];

  /* ---------------------------------------------------------------
     Styles. Injected once. Scoped under .bmtv-chat so nothing here
     can touch the host page -- `.msg` and `.sys-msg` are generic
     enough to collide, and on the 3.0 Live page they already did:
     the top promo banner uses class="msg".
     --------------------------------------------------------------- */
  var CSS = [
    '.bmtv-chat{--bc-red:var(--red,#E8181C);--bc-surface:var(--surface,#141210);',
    '--bc-surface2:var(--surface2,#1c1917);--bc-border:var(--border,#2a2622);',
    '--bc-border2:var(--border2,#3a352f);--bc-text:var(--text,#F2EFEC);',
    '--bc-muted:var(--muted,#8a827a);--bc-muted2:var(--muted2,#6b645d);',
    'display:flex;flex-direction:column;border-radius:14px;overflow:hidden;',
    'border:1px solid var(--bc-border);background:var(--bc-surface);min-width:0;',
    'color:var(--bc-text);font-family:inherit;}',

    '.bmtv-chat .bc-head{display:flex;align-items:center;gap:9px;padding:13px 15px;',
    'border-bottom:1px solid var(--bc-border);flex:0 0 auto;}',
    '.bmtv-chat .bc-head .bc-t{font-weight:800;font-size:13px;}',
    '.bmtv-chat .bc-head .bc-cnt{margin-left:auto;color:var(--bc-muted);font-size:11.5px;font-weight:600;}',
    '.bmtv-chat .bc-cnt.on{color:#57D9A3;}.bmtv-chat .bc-cnt.down{color:#ff6b6b;}',

    // min-height:0 is load-bearing: a flex child defaults to min-height:auto and
    // refuses to shrink below its content, which pushes the composer off the
    // bottom instead of scrolling.
    '.bmtv-chat .bc-body{flex:1 1 auto;min-height:0;overflow-y:auto;padding:13px 15px;',
    'display:flex;flex-direction:column;gap:12px;overscroll-behavior:contain;',
    'scrollbar-width:thin;scrollbar-color:var(--bc-border2) transparent;}',
    '.bmtv-chat .bc-body::-webkit-scrollbar{width:10px;}',
    '.bmtv-chat .bc-body::-webkit-scrollbar-track{background:transparent;}',
    '.bmtv-chat .bc-body::-webkit-scrollbar-thumb{background:var(--bc-border2);border-radius:6px;',
    'border:2px solid transparent;background-clip:padding-box;}',
    '.bmtv-chat .bc-body::-webkit-scrollbar-thumb:hover{background:var(--bc-muted2);background-clip:padding-box;}',
    '.bmtv-chat .bc-body::-webkit-scrollbar-thumb:active{background:var(--bc-red);background-clip:padding-box;}',

    '.bmtv-chat .bc-msg{font-size:13px;line-height:1.45;}',
    '.bmtv-chat .bc-msg .bc-u{font-weight:800;margin-right:6px;}',
    '.bmtv-chat .bc-msg .bc-txt{opacity:.92;}',
    '.bmtv-chat .bc-sys{font-size:11.5px;color:var(--bc-muted2);text-align:center;font-style:italic;}',
    '.bmtv-chat .bc-onair{display:inline-block;font-size:9.5px;font-weight:800;letter-spacing:.09em;',
    'background:var(--bc-red);color:#fff;border-radius:3px;padding:1px 5px;margin-right:6px;vertical-align:1px;}',
    '.bmtv-chat .bc-tick{color:var(--bc-red);margin-left:3px;font-size:10px;vertical-align:1px;}',

    '.bmtv-chat .bc-name{display:flex;gap:8px;padding:10px 12px;align-items:center;',
    'border-top:1px solid var(--bc-border);flex:0 0 auto;}',
    '.bmtv-chat .bc-name.bc-hide{display:none;}',
    '.bmtv-chat .bc-name input{flex:1;min-width:0;background:#100d0b;border:1px solid var(--bc-border);',
    'border-radius:7px;padding:8px 11px;color:var(--bc-text);font:inherit;font-size:13px;}',
    '.bmtv-chat .bc-name button{background:var(--bc-red);border:0;border-radius:7px;padding:8px 13px;',
    'color:#fff;font:inherit;font-size:12.5px;font-weight:700;cursor:pointer;white-space:nowrap;}',
    '.bmtv-chat .bc-as{padding:6px 12px 0;font-size:11.5px;color:var(--bc-muted);flex:0 0 auto;}',
    '.bmtv-chat .bc-as.bc-hide{display:none;}',
    '.bmtv-chat .bc-as b{color:var(--bc-text);}',
    '.bmtv-chat .bc-as a{color:var(--bc-red);cursor:pointer;margin-left:6px;}',

    '.bmtv-chat .bc-foot{border-top:1px solid var(--bc-border);padding:11px;display:flex;gap:8px;flex:0 0 auto;}',
    '.bmtv-chat .bc-foot input{flex:1;min-width:0;background:var(--bc-surface2);',
    'border:1px solid var(--bc-border);border-radius:8px;padding:10px 12px;color:var(--bc-text);',
    'font:inherit;font-size:13px;outline:none;}',
    '.bmtv-chat .bc-foot input:focus{border-color:var(--bc-red);}',
    '.bmtv-chat .bc-send{background:var(--bc-red);border:none;color:#fff;border-radius:8px;',
    'padding:0 14px;font-weight:800;cursor:pointer;font:inherit;font-size:13px;}',
    '.bmtv-chat .bc-send:disabled{opacity:.5;cursor:default;}'
  ].join('');

  function injectCSS() {
    if (document.getElementById('bmtv-chat-css')) return;
    var s = document.createElement('style');
    s.id = 'bmtv-chat-css';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  /* ---------------------------------------------------------------
     One panel.
     --------------------------------------------------------------- */
  function mount(host, sb) {
    var room = host.getAttribute('data-room');
    if (!room) {
      try { room = new URLSearchParams(location.search).get('room'); } catch (e) { room = null; }
    }
    room = String(room || 'main').trim().toLowerCase();
    if (!ROOM_RE.test(room)) room = 'main';

    host.classList.add('bmtv-chat');
    host.innerHTML = '';

    var head = el('div', 'bc-head');
    head.appendChild(el('span', 'bc-t', host.getAttribute('data-title') || 'Live Chat'));
    var cnt = el('span', 'bc-cnt', 'connecting…');
    head.appendChild(cnt);

    var body = el('div', 'bc-body');
    var nameBar = el('div', 'bc-name');
    var nameInput = el('input');
    nameInput.maxLength = 40;
    nameInput.placeholder = 'Pick a name to chat as…';
    nameInput.setAttribute('aria-label', 'Display name');
    var nameBtn = el('button', null, 'Set');
    nameBtn.type = 'button';
    nameBar.appendChild(nameInput); nameBar.appendChild(nameBtn);
    var asBar = el('div', 'bc-as');

    var foot = el('div', 'bc-foot');
    var input = el('input');
    input.placeholder = 'Pick a name first…';
    input.setAttribute('aria-label', 'Chat message');
    input.disabled = true;
    var send = el('button', 'bc-send', 'Send');
    send.type = 'button'; send.disabled = true;
    foot.appendChild(input); foot.appendChild(send);

    host.appendChild(head); host.appendChild(body);
    host.appendChild(nameBar); host.appendChild(asBar); host.appendChild(foot);

    var me = null, seen = Object.create(null), sending = false;

    function status(text, cls) { cnt.textContent = text; cnt.className = 'bc-cnt ' + (cls || ''); }
    function sysMsg(t) {
      var d = el('div', 'bc-sys', t);
      body.appendChild(d);
      body.scrollTop = body.scrollHeight;
    }
    function colorFor(id) {
      var h = 0;
      for (var i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
      return PALETTE[h % PALETTE.length];
    }
    function atBottom() { return body.scrollHeight - body.scrollTop - body.clientHeight < 60; }

    function update(m) {
      var e = seen[m.id];
      if (!e) return;
      if (m.status === 'hidden') { e.remove(); delete seen[m.id]; return; }
      var tag = e.querySelector('.bc-onair');
      if (m.status === 'released' && !tag) {
        tag = el('span', 'bc-onair', 'ON AIR');
        e.insertBefore(tag, e.firstChild);
      } else if (m.status !== 'released' && tag) {
        tag.remove();
      }
    }

    function render(m) {
      if (seen[m.id]) { update(m); return; }
      var stick = atBottom();
      var e = el('div', 'bc-msg');
      var u = el('span', 'bc-u', m.display_name);
      u.style.color = colorFor(m.user_id);
      if (m.is_verified) {
        var v = el('span', 'bc-tick', '✓');
        v.title = 'Verified account';
        u.appendChild(v);
      }
      e.appendChild(u);
      e.appendChild(el('span', 'bc-txt', m.body));
      seen[m.id] = e;
      body.appendChild(e);
      if (m.status === 'released') update(m);
      if (stick) body.scrollTop = body.scrollHeight;
    }

    /* display name, remembered per browser */
    var nameKey = 'bmtv-chat-name', myName = null;
    try { myName = localStorage.getItem(nameKey); } catch (e) {}

    function paintName() {
      if (myName) {
        nameBar.classList.add('bc-hide');
        asBar.classList.remove('bc-hide');
        asBar.innerHTML = '';
        asBar.appendChild(document.createTextNode('Chatting as '));
        asBar.appendChild(el('b', null, myName));
        var a = el('a', null, 'change');
        a.addEventListener('click', function () { myName = null; paintName(); nameInput.focus(); });
        asBar.appendChild(a);
        input.placeholder = 'Say something…';
        input.disabled = false; send.disabled = false;
      } else {
        nameBar.classList.remove('bc-hide');
        asBar.classList.add('bc-hide');
        input.placeholder = 'Pick a name first…';
        input.disabled = true; send.disabled = true;
      }
    }
    function setName() {
      var v = nameInput.value.trim().slice(0, 40);
      if (!v) { nameInput.focus(); return; }
      myName = v;
      try { localStorage.setItem(nameKey, v); } catch (e) {}
      paintName(); input.focus();
    }
    nameBtn.addEventListener('click', setName);
    nameInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') setName(); });
    paintName();

    function post() {
      var v = input.value.trim();
      if (!v || !me || !myName || sending) return;
      sending = true;
      var keep = v;
      input.value = '';
      sb.from('messages').insert({ user_id: me, display_name: myName, body: keep, room: room })
        .then(function (res) {
          sending = false;
          if (!res.error) return;
          var msg = String(res.error.message || '');
          if (msg.indexOf('rate_limited') >= 0)   sysMsg('Slow down a second — too many messages at once.');
          else if (msg.indexOf('banned') >= 0)    sysMsg('You are not able to post in this chat.');
          else if (msg.indexOf('room_archived') >= 0) sysMsg('This chat is closed.');
          else                                    sysMsg('Message did not send. Try again.');
          input.value = keep;   // give them their text back rather than losing it
        });
    }
    send.addEventListener('click', post);
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') post(); });

    status('connecting…', '');

    sb.auth.getSession().then(function (r) {
      if (r.data && r.data.session) return r.data.session;
      return sb.auth.signInAnonymously().then(function (r2) {
        if (r2.error) throw r2.error;
        return r2.data.session;
      });
    }).then(function (session) {
      me = session.user.id;
      return sb.from('messages')
        .select('id,user_id,display_name,body,status,is_verified')
        .eq('room', room)
        .neq('status', 'hidden')
        .order('id', { ascending: false })
        .limit(50);
    }).then(function (res) {
      if (res.error) throw res.error;
      body.innerHTML = '';
      sysMsg('Welcome to BlackMarker.TV — keep it respectful.');
      (res.data || []).slice().reverse().forEach(render);
      body.scrollTop = body.scrollHeight;

      // Filter on room server-side. Without it every room's traffic reaches
      // every client and the browser decides what to show -- a leak between
      // rooms must not depend on client-side code.
      sb.channel('bmtv-chat-' + room)
        .on('postgres_changes',
            { event: 'INSERT', schema: 'public', table: 'messages', filter: 'room=eq.' + room },
            function (p) { render(p.new); })
        .on('postgres_changes',
            { event: 'UPDATE', schema: 'public', table: 'messages', filter: 'room=eq.' + room },
            function (p) { update(p.new); })
        .subscribe(function (s) {
          if (s === 'SUBSCRIBED')         status('live', 'on');
          else if (s === 'CHANNEL_ERROR') status('reconnecting…', 'down');
        });
    }).catch(function (e) {
      status('chat offline', 'down');
      sysMsg('Chat is unavailable right now.');
      if (window.console) console.warn('bmtv-chat init failed:', e);
    });
  }

  /* ---------------------------------------------------------------
     Boot
     --------------------------------------------------------------- */
  function hasPanels() {
    return !!document.querySelector('[data-bmtv-chat]');
  }

  function boot() {
    var hosts = document.querySelectorAll('[data-bmtv-chat]');
    if (!hosts.length) return;
    injectCSS();
    var sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON);
    Array.prototype.forEach.call(hosts, function (h) {
      try { mount(h, sb); }
      catch (e) { if (window.console) console.warn('bmtv-chat mount failed:', e); }
    });
  }

  function withSDK(cb) {
    if (window.supabase && window.supabase.createClient) return cb();
    var existing = document.querySelector('script[data-bmtv-sdk]');
    if (existing) { existing.addEventListener('load', cb); return; }
    var s = document.createElement('script');
    s.src = SDK;
    s.setAttribute('data-bmtv-sdk', '');
    s.onload = cb;
    s.onerror = function () {
      if (window.console) console.warn('bmtv-chat: could not load supabase-js from ' + SDK +
        ' — a Content-Security-Policy may be blocking cdn.jsdelivr.net.');
    };
    document.head.appendChild(s);
  }

  // Check for a panel BEFORE pulling supabase-js down. This file sits in the
  // site-wide footer, so most pages have no chat on them and should pay
  // nothing for it.
  function go() {
    if (!hasPanels()) return;
    withSDK(boot);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', go);
  } else {
    go();
  }
})();
