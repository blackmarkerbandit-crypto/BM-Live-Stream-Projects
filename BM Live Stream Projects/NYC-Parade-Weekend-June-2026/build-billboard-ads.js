'use strict';
const fs = require('fs');

const dir = 'D:/Dropbox/WORK FILES/BMB/AI SHIT/BM Live Stream Projects/NYC-Parade-Weekend-June-2026/';

const titleB64 = fs.readFileSync(dir + 'bmb-title-b64.txt', 'utf8').trim();
const iconB64  = fs.readFileSync(dir + 'bmb-icon-b64.txt',  'utf8').trim();
const qrB64    = fs.readFileSync(dir + 'qrcode-jpg-b64.txt','utf8').trim();

const title = `data:image/png;base64,${titleB64}`;
const icon  = `data:image/png;base64,${iconB64}`;
const qr    = `data:image/jpeg;base64,${qrB64}`;

/* ============================================================
   AD 1 — Jun 12 · Times Square · 960×640
   Message: Artists, find us this weekend at 116th + Parade
   ============================================================ */
const ad1 = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AD1 - BlackMarkerTV - Times Square - Jun 12</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:960px; height:640px; overflow:hidden; background:#080808; }
.ad {
  width:960px; height:640px; background:#080808;
  position:relative; display:flex; align-items:stretch;
  font-family:'Inter',Arial,sans-serif; overflow:hidden;
}
.red-bar { position:absolute; top:0; left:0; right:0; height:5px; background:#E8181C; z-index:10; }
.glow {
  position:absolute; bottom:-80px; left:-80px;
  width:500px; height:500px;
  background:radial-gradient(circle,rgba(232,24,28,0.18) 0%,transparent 70%);
}
.glow2 {
  position:absolute; top:-80px; right:220px;
  width:360px; height:360px;
  background:radial-gradient(circle,rgba(232,24,28,0.07) 0%,transparent 70%);
}
.icon-bg {
  position:absolute; right:290px; top:50%; transform:translateY(-50%);
  width:280px; height:280px; opacity:0.04;
}
.divider { position:absolute; right:260px; top:0; width:1px; height:100%; background:#1c1c1c; }
.left {
  flex:1; padding:52px 48px; display:flex; flex-direction:column;
  justify-content:center; position:relative; z-index:2;
}
.eyebrow {
  font-size:11px; font-weight:700; letter-spacing:4px;
  text-transform:uppercase; color:#E8181C; margin-bottom:18px;
  display:flex; align-items:center; gap:12px;
}
.eyebrow::before { content:''; width:28px; height:2px; background:#E8181C; display:block; }
.headline {
  font-size:86px; font-weight:900; line-height:0.88;
  color:#FFFFFF; letter-spacing:-3px; margin-bottom:28px;
}
.headline .red { color:#E8181C; }
.subline {
  font-size:15px; font-weight:600; color:#777; line-height:1.65;
  margin-bottom:36px; max-width:480px;
}
.subline strong { color:#D8D8D8; }
.logo { height:130px; width:auto; align-self:flex-start; object-fit:contain; display:block; }
.right {
  width:260px; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:40px 36px 40px 0; position:relative; z-index:2; gap:14px;
}
.icon-logo { width:44px; height:44px; }
.qr-wrap {
  background:#fff; border-radius:14px; padding:12px;
  box-shadow:0 0 40px rgba(232,24,28,0.15);
}
.qr-wrap img { width:150px; height:150px; display:block; }
.scan {
  font-size:9px; font-weight:700; letter-spacing:2.5px;
  text-transform:uppercase; color:#505050; text-align:center;
}
</style>
</head>
<body>
<div class="ad">
  <div class="red-bar"></div>
  <div class="glow"></div><div class="glow2"></div>
  <img class="icon-bg" src="${icon}" alt="">
  <div class="divider"></div>
  <div class="left">
    <div class="eyebrow">This Weekend — New York City</div>
    <div class="headline">ARTISTS.<br><span class="red">FIND</span><br>US.</div>
    <div class="subline">
      <strong>116th St Festival · PR Day Parade</strong><br>
      We're going LIVE — come get on air at BlackMarker.TV
    </div>
    <img class="logo" src="${title}" alt="BlackMarker.TV">
  </div>
  <div class="right">
    <img class="icon-logo" src="${icon}" alt="BMB">
    <div class="qr-wrap"><img src="${qr}" alt="QR Code"></div>
    <div class="scan">Watch Live</div>
  </div>
</div>
</body>
</html>`;

/* ============================================================
   AD 2 — Jun 13 · 116th St Festival · 1920×1080
   Message: Drop your 16 / come to vendor tent CTA
   ============================================================ */
const ad2 = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AD2 - BlackMarkerTV - 116th Festival - Jun 13</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1920px; height:1080px; overflow:hidden; background:#060606; }
.ad {
  width:1920px; height:1080px; background:#060606;
  position:relative; display:flex; align-items:stretch;
  font-family:'Inter',Arial,sans-serif; overflow:hidden;
}
.red-bar { position:absolute; top:0; left:0; right:0; height:6px; background:#E8181C; z-index:10; }
.glow {
  position:absolute; bottom:-200px; left:-100px;
  width:900px; height:900px;
  background:radial-gradient(circle,rgba(232,24,28,0.15) 0%,transparent 65%);
}
.icon-bg {
  position:absolute; right:530px; top:50%; transform:translateY(-50%);
  width:620px; height:620px; opacity:0.03;
}
.divider { position:absolute; right:480px; top:0; width:1px; height:100%; background:#181818; }
.left {
  flex:1; padding:90px 100px; display:flex; flex-direction:column;
  justify-content:center; position:relative; z-index:2;
}
.eyebrow {
  font-size:14px; font-weight:700; letter-spacing:5px;
  text-transform:uppercase; color:#E8181C; margin-bottom:22px;
  display:flex; align-items:center; gap:14px;
}
.eyebrow::before { content:''; width:36px; height:2px; background:#E8181C; display:block; }
.headline {
  font-size:178px; font-weight:900; line-height:0.86;
  color:#FFFFFF; letter-spacing:-6px; margin-bottom:30px;
}
.headline .red { color:#E8181C; }
.sub {
  font-size:32px; font-weight:700; color:#C8C8C8;
  margin-bottom:20px; line-height:1.3;
}
.location-tag {
  display:inline-flex; align-items:center; gap:10px;
  background:rgba(232,24,28,0.1); border:1px solid rgba(232,24,28,0.28);
  border-radius:6px; padding:10px 20px; margin-bottom:26px;
  font-size:20px; font-weight:700; color:#E8181C;
  letter-spacing:1px; text-transform:uppercase;
}
.detail {
  font-size:20px; font-weight:500; color:#585858;
  line-height:1.65; margin-bottom:48px; max-width:840px;
}
.detail strong { color:#A0A0A0; }
.logo { height:130px; width:auto; align-self:flex-start; object-fit:contain; display:block; }
.right {
  width:480px; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:60px 60px 60px 0; position:relative; z-index:2; gap:22px;
}
.icon-logo { width:70px; height:70px; }
.qr-wrap {
  background:#fff; border-radius:18px; padding:18px;
  box-shadow:0 0 80px rgba(232,24,28,0.15);
}
.qr-wrap img { width:260px; height:260px; display:block; }
.scan {
  font-size:12px; font-weight:700; letter-spacing:3px;
  text-transform:uppercase; color:#404040; text-align:center;
}
</style>
</head>
<body>
<div class="ad">
  <div class="red-bar"></div>
  <div class="glow"></div>
  <img class="icon-bg" src="${icon}" alt="">
  <div class="divider"></div>
  <div class="left">
    <div class="eyebrow">Live at 116th Street Festival — Today</div>
    <div class="headline">DROP<br>YOUR <span class="red">16.</span></div>
    <div class="sub">BlackMarker.TV is LIVE at this festival.</div>
    <div class="location-tag">📍 Our Tent — 116th &amp; 3rd Ave · Slot 75</div>
    <div class="detail">
      Step up and drop a hot 16 — or get a drop/interview on air.<br>
      <strong>Get on BlackMarker.TV. TODAY.</strong>
    </div>
    <img class="logo" src="${title}" alt="BlackMarker.TV">
  </div>
  <div class="right">
    <img class="icon-logo" src="${icon}" alt="BMB">
    <div class="qr-wrap"><img src="${qr}" alt="QR Code"></div>
    <div class="scan">Scan · Watch Live</div>
  </div>
</div>
</body>
</html>`;

/* ============================================================
   AD 3 — Jun 14A · Parade Broadway · 1920×1080
   Message: We're on the float — watch live on BlackMarker.TV
   ============================================================ */
const ad3 = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AD3 - BlackMarkerTV - Parade Broadway - Jun 14</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1920px; height:1080px; overflow:hidden; background:#060606; }
.ad {
  width:1920px; height:1080px; background:#060606;
  position:relative; display:flex; align-items:stretch;
  font-family:'Inter',Arial,sans-serif; overflow:hidden;
}
.flag-stripe {
  position:absolute; bottom:0; left:0; right:0;
  height:6px; display:flex; z-index:10;
}
.flag-stripe div { flex:1; }
.f-r  { background:#EF3340; }
.f-w  { background:#FFFFFF; }
.f-b  { background:#002868; }
.glow {
  position:absolute; top:-200px; left:-150px;
  width:1000px; height:1000px;
  background:radial-gradient(circle,rgba(239,51,64,0.1) 0%,transparent 65%);
}
.glow2 {
  position:absolute; bottom:-80px; right:320px;
  width:600px; height:600px;
  background:radial-gradient(circle,rgba(0,40,104,0.1) 0%,transparent 65%);
}
.icon-bg {
  position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
  width:700px; height:700px; opacity:0.025;
}
.divider { position:absolute; right:480px; top:0; width:1px; height:100%; background:#181818; }
.left {
  flex:1; padding:90px 100px; display:flex; flex-direction:column;
  justify-content:center; position:relative; z-index:2;
}
.eyebrow {
  font-size:14px; font-weight:700; letter-spacing:5px;
  text-transform:uppercase; color:#EF3340; margin-bottom:22px;
  display:flex; align-items:center; gap:14px;
}
.eyebrow::before { content:''; width:36px; height:2px; background:#EF3340; display:block; }
.headline {
  font-size:146px; font-weight:900; line-height:0.87;
  color:#FFFFFF; letter-spacing:-5px; margin-bottom:34px;
}
.headline .red { color:#EF3340; }
.sub {
  font-size:34px; font-weight:700; color:#C8C8C8;
  margin-bottom:22px; line-height:1.3;
}
.hashtag {
  font-size:20px; font-weight:600; color:#525252;
  margin-bottom:48px; line-height:1.6;
}
.hashtag strong { color:#888; }
.logo { height:130px; width:auto; align-self:flex-start; object-fit:contain; display:block; }
.right {
  width:480px; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:60px 60px 60px 0; position:relative; z-index:2; gap:22px;
}
.icon-logo { width:70px; height:70px; }
.qr-wrap {
  background:#fff; border-radius:18px; padding:18px;
  box-shadow:0 0 80px rgba(239,51,64,0.15);
}
.qr-wrap img { width:260px; height:260px; display:block; }
.scan {
  font-size:12px; font-weight:700; letter-spacing:3px;
  text-transform:uppercase; color:#404040; text-align:center;
}
</style>
</head>
<body>
<div class="ad">
  <div class="glow"></div><div class="glow2"></div>
  <img class="icon-bg" src="${icon}" alt="">
  <div class="flag-stripe">
    <div class="f-r"></div><div class="f-w"></div><div class="f-b"></div>
    <div class="f-w"></div><div class="f-r"></div>
  </div>
  <div class="divider"></div>
  <div class="left">
    <div class="eyebrow">Puerto Rican Day Parade — Watch Live Now</div>
    <div class="headline">WE'RE ON<br>THE <span class="red">FLOAT.</span></div>
    <div class="sub">Watch the Puerto Rican Day Parade LIVE on BlackMarker.TV</div>
    <div class="hashtag">
      <strong>#SomosMasQue100x35</strong> · Celebrating Puerto Rican Pioneers
    </div>
    <img class="logo" src="${title}" alt="BlackMarker.TV">
  </div>
  <div class="right">
    <img class="icon-logo" src="${icon}" alt="BMB">
    <div class="qr-wrap"><img src="${qr}" alt="QR Code"></div>
    <div class="scan">Watch Live Now</div>
  </div>
</div>
</body>
</html>`;

/* ============================================================
   AD 4 — Jun 14B · Parade 40th & 7th · 960×640
   Message: Same parade CTA — compressed format
   ============================================================ */
const ad4 = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AD4 - BlackMarkerTV - Parade 40th - Jun 14</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:960px; height:640px; overflow:hidden; background:#060606; }
.ad {
  width:960px; height:640px; background:#060606;
  position:relative; display:flex; align-items:stretch;
  font-family:'Inter',Arial,sans-serif; overflow:hidden;
}
.flag-stripe {
  position:absolute; bottom:0; left:0; right:0;
  height:5px; display:flex; z-index:10;
}
.flag-stripe div { flex:1; }
.f-r { background:#EF3340; }
.f-w { background:#FFFFFF; }
.f-b { background:#002868; }
.glow {
  position:absolute; top:-100px; left:-100px;
  width:600px; height:600px;
  background:radial-gradient(circle,rgba(239,51,64,0.13) 0%,transparent 65%);
}
.icon-bg {
  position:absolute; right:282px; top:50%; transform:translateY(-50%);
  width:300px; height:300px; opacity:0.04;
}
.divider { position:absolute; right:252px; top:0; width:1px; height:100%; background:#1a1a1a; }
.left {
  flex:1; padding:52px 48px; display:flex; flex-direction:column;
  justify-content:center; position:relative; z-index:2;
}
.eyebrow {
  font-size:10px; font-weight:700; letter-spacing:4px;
  text-transform:uppercase; color:#EF3340; margin-bottom:16px;
  display:flex; align-items:center; gap:10px;
}
.eyebrow::before { content:''; width:24px; height:2px; background:#EF3340; display:block; }
.headline {
  font-size:86px; font-weight:900; line-height:0.87;
  color:#FFFFFF; letter-spacing:-3px; margin-bottom:22px;
}
.headline .red { color:#EF3340; }
.sub {
  font-size:17px; font-weight:700; color:#C0C0C0; margin-bottom:12px;
}
.hashtag {
  font-size:12px; font-weight:600; color:#505050; margin-bottom:32px;
}
.hashtag strong { color:#777; }
.logo { height:130px; width:auto; align-self:flex-start; object-fit:contain; display:block; }
.right {
  width:252px; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:36px 32px 36px 0; position:relative; z-index:2; gap:14px;
}
.icon-logo { width:46px; height:46px; }
.qr-wrap {
  background:#fff; border-radius:12px; padding:12px;
  box-shadow:0 0 40px rgba(239,51,64,0.13);
}
.qr-wrap img { width:152px; height:152px; display:block; }
.scan {
  font-size:9px; font-weight:700; letter-spacing:2.5px;
  text-transform:uppercase; color:#484848; text-align:center;
}
</style>
</head>
<body>
<div class="ad">
  <div class="glow"></div>
  <img class="icon-bg" src="${icon}" alt="">
  <div class="flag-stripe">
    <div class="f-r"></div><div class="f-w"></div><div class="f-b"></div>
    <div class="f-w"></div><div class="f-r"></div>
  </div>
  <div class="divider"></div>
  <div class="left">
    <div class="eyebrow">PR Day Parade — Live Now</div>
    <div class="headline">WATCH<br><span class="red">LIVE.</span></div>
    <div class="sub">Puerto Rican Day Parade on BlackMarker.TV</div>
    <div class="hashtag"><strong>#SomosMasQue100x35</strong> · Puerto Rican Pioneers</div>
    <img class="logo" src="${title}" alt="BlackMarker.TV">
  </div>
  <div class="right">
    <img class="icon-logo" src="${icon}" alt="BMB">
    <div class="qr-wrap"><img src="${qr}" alt="QR Code"></div>
    <div class="scan">Watch Live</div>
  </div>
</div>
</body>
</html>`;

// Write all 4 files
const files = [
  ['AD1-Jun12-TimesSquare-960x640.html',         ad1],
  ['AD2-Jun13-116thFestival-1920x1080.html',     ad2],
  ['AD3-Jun14A-Parade-Broadway-1920x1080.html',  ad3],
  ['AD4-Jun14B-Parade-40th-960x640.html',        ad4],
];

files.forEach(([name, content]) => {
  fs.writeFileSync(dir + name, content, 'utf8');
  const kb = (fs.statSync(dir + name).size / 1024).toFixed(0);
  console.log(`✓ ${name} — ${kb}KB`);
});

console.log('\nAll 4 billboard ads built successfully.');
