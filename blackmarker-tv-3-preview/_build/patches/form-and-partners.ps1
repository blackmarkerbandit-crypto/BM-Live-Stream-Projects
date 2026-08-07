# 1. Make the lead form read as a separate block from the page.
# 2. Give each partner type on the Partnerships page its own icon + accent colour.
$ErrorActionPreference = "Stop"
$B = "D:\Dropbox\WORK FILES\BMB\AI SHIT\blackmarker-tv-3-preview\_build"
$utf8 = New-Object System.Text.UTF8Encoding($false)

# =================================================================== 1. FORM
$css = Join-Path $B "src\workwithus.css"
$c = [System.IO.File]::ReadAllText($css, [System.Text.Encoding]::UTF8)

# lighter panel than the page + a red cap so it clearly separates from the cards above
$c = $c.Replace(
  '.wk-form{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:26px;}',
  '.wk-form{position:relative;border:1px solid var(--border2);border-radius:16px;padding:30px 26px 26px;
  background:linear-gradient(180deg,#221d1a 0%,#191512 60%,#151210 100%);
  box-shadow:0 22px 60px -30px rgba(0,0,0,.95), inset 0 1px 0 rgba(255,255,255,.04);}
.wk-form::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 16px 0 0;
  background:linear-gradient(90deg,var(--red),#ff5a3c 55%,rgba(232,24,28,0));}
/* inputs sit darker than the panel so fields stay legible on the lighter card */
.wk-form input[type=text],.wk-form input[type=email],.wk-form input[type=tel],
.wk-form input[type=url],.wk-form input[type=date],.wk-form select,.wk-form textarea{
  background:#100d0b;border-color:#3a332d;}')

if ($c -notmatch '\.wk-form-lead\{') {
  $c += @'

/* a little air + a rule above the form so it reads as its own block */
.wk-form-lead{margin:6px 0 18px;padding-top:26px;border-top:1px solid var(--border);
  font-size:13.5px;color:var(--muted2);letter-spacing:.02em;}
'@
}
[System.IO.File]::WriteAllText($css, $c, $utf8)
"css   : form panel restyled"

# ============================================================== 2. PARTNERS
$pf = Join-Path $B "src\wk-partnerships.html"
$h = [System.IO.File]::ReadAllText($pf, [System.Text.Encoding]::UTF8)

$icons = @{
  1 = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="3"/><path d="M10 9.2l5 2.8-5 2.8z"/></svg>'
  2 = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11v2a1 1 0 001 1h2l5 4V6L6 10H4a1 1 0 00-1 1z"/><path d="M16 8.5a5 5 0 010 7"/><path d="M19 6a9 9 0 010 12"/></svg>'
  3 = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="13" height="12" rx="2"/><path d="M15 10.5l6-3.5v10l-6-3.5z"/></svg>'
  4 = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l5.5-5.5 3.5 3.5L21 6"/><path d="M15 6h6v6"/></svg>'
}
$n = 0
$h = [regex]::Replace($h, '<div class="wk-card">\s*\r?\n(\s*)<div class="wk-eye">(0\d) &middot; ([^<]*)</div>', {
  param($m)
  $script:n++
  $i = [int]$m.Groups[2].Value
  $pad = $m.Groups[1].Value
  '<div class="wk-card wk-type t' + $i + '">' + "`n" +
  $pad + '<div class="wk-type-head">' + "`n" +
  $pad + '  <span class="wk-type-ico">' + $icons[$i] + '</span>' + "`n" +
  $pad + '  <div class="wk-eye">' + $m.Groups[2].Value + ' &middot; ' + $m.Groups[3].Value + '</div>' + "`n" +
  $pad + '</div>'
})
[System.IO.File]::WriteAllText($pf, $h, $utf8)
"html  : $n partner cards given icons"

$c = [System.IO.File]::ReadAllText($css, [System.Text.Encoding]::UTF8)
if ($c -notmatch '\.wk-type\{') {
  $c += @'

/* partner types: each gets its own icon + accent so the four read as distinct
   offers rather than four identical boxes */
.wk-type{position:relative;padding-left:22px;overflow:hidden;}
.wk-type::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--tc);}
.wk-type::after{content:"";position:absolute;left:0;top:0;right:0;bottom:0;pointer-events:none;
  background:radial-gradient(120% 90% at 0% 0%,color-mix(in srgb,var(--tc) 12%,transparent),transparent 60%);}
.wk-type > *{position:relative;z-index:1;}
.wk-type-head{display:flex;align-items:center;gap:11px;margin-bottom:10px;}
.wk-type-ico{flex-shrink:0;width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;
  color:var(--tc);background:color-mix(in srgb,var(--tc) 14%,transparent);
  border:1px solid color-mix(in srgb,var(--tc) 34%,transparent);}
.wk-type-ico svg{width:20px;height:20px;}
.wk-type .wk-eye{margin-bottom:0;color:var(--tc);}
.wk-type li::before{background:var(--tc);}
.wk-type.t1{--tc:#E8181C;}   /* content partners  */
.wk-type.t2{--tc:#FFC21E;}   /* event sponsors    */
.wk-type.t3{--tc:#37E0C8;}   /* production        */
.wk-type.t4{--tc:#7C9CFF;}   /* investment        */
'@
  [System.IO.File]::WriteAllText($css, $c, $utf8)
  "css   : partner type accents added"
}
