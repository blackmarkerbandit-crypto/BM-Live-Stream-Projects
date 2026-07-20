(function () {
  // Subscribe modal — opened by any .open-sub button (header + footer)
  var subModal = document.getElementById('subModal');
  if (subModal) {
    document.querySelectorAll('.open-sub').forEach(function (b) {
      b.addEventListener('click', function () { subModal.classList.add('open'); });
    });
    var closeSub = document.getElementById('closeSub');
    if (closeSub) closeSub.addEventListener('click', function () { subModal.classList.remove('open'); });
    subModal.addEventListener('click', function (e) { if (e.target === subModal) subModal.classList.remove('open'); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') subModal.classList.remove('open'); });
  }

  // Share — native share sheet, or copy link
  var shareBtn = document.getElementById('shareBtn');
  if (shareBtn) {
    shareBtn.addEventListener('click', function () {
      var url = location.origin || 'https://www.blackmarker.tv';
      if (navigator.share) {
        navigator.share({ title: 'Black Marker TV — The Free Loop', url: url }).catch(function () {});
      } else {
        var l = document.getElementById('shareLbl');
        var o = l ? l.textContent : '';
        if (navigator.clipboard) navigator.clipboard.writeText(url);
        if (l) { l.textContent = 'Link Copied!'; setTimeout(function () { l.textContent = o; }, 1600); }
      }
    });
  }

  // Live chat show/hide toggle (homepage only)
  var grid = document.getElementById('liveGrid');
  var ct = document.getElementById('chatToggle');
  var lbl = document.getElementById('chatToggleLbl');
  if (grid && ct) {
    ct.addEventListener('click', function () {
      var off = grid.classList.toggle('chat-off');
      ct.classList.toggle('active', !off);
      if (lbl) lbl.textContent = off ? 'Chat: Off' : 'Chat: On';
    });
  }

  // Placeholder chat input — LOCAL ECHO ONLY.
  // Replace with a realtime backend (planned: Supabase) so messages broadcast to all viewers.
  var cbody = document.getElementById('chatBody'),
      cinput = document.getElementById('chatInput'),
      csend = document.getElementById('chatSend');
  if (cbody && cinput && csend) {
    var post = function () {
      var v = cinput.value.trim(); if (!v) return;
      var m = document.createElement('div'); m.className = 'msg';
      m.innerHTML = '<span class="u" style="color:#37E0C8">you</span><span class="txt"></span>';
      m.querySelector('.txt').textContent = v;
      cbody.appendChild(m); cbody.scrollTop = cbody.scrollHeight; cinput.value = '';
    };
    csend.addEventListener('click', post);
    cinput.addEventListener('keydown', function (e) { if (e.key === 'Enter') post(); });
  }
})();
