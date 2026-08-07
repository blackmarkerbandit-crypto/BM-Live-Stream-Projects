# Production page:
#  1. icon + colour treatment on the six "Events We Broadcast" cards
#  2. replace the two-box "us vs them" with a real row-by-row comparison
$ErrorActionPreference = "Stop"
$B = "D:\Dropbox\WORK FILES\BMB\AI SHIT\blackmarker-tv-3-preview\_build"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$f = Join-Path $B "src\wk-production.html"
$h = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)

# ------------------------------------------------- 1. icons on the six event cards
$ico = @(
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2.5" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0013 0"/><path d="M12 17.5V21"/><path d="M8.5 21h7"/></svg>'                                  # battles - mic
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4h10v5a5 5 0 01-10 0z"/><path d="M7 5.5H4.5a2.5 2.5 0 005 0"/><path d="M17 5.5h2.5a2.5 2.5 0 01-5 0"/><path d="M12 14v4"/><path d="M8.5 20.5h7"/></svg>'   # sports - trophy
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="17.5" r="2.6"/><circle cx="18" cy="15.5" r="2.6"/><path d="M9.6 17.5V6.4l10.8-2.2v11.3"/></svg>'                                                   # festivals - notes
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5.5 21V3"/><path d="M5.5 4.5h13l-2.6 4 2.6 4h-13"/></svg>'                                                                                                 # parades - flag
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="4" width="19" height="12" rx="2"/><path d="M12 16v3"/><path d="M8 19.5h8"/><path d="M7 11.5l2.5-2.5 2 2L15 7.5"/></svg>'                            # conferences - screen
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 8.5h19v11a1.5 1.5 0 01-1.5 1.5H4a1.5 1.5 0 01-1.5-1.5z"/><path d="M3.2 8.5l2-4.2 4.4 3.6"/><path d="M9.9 4.1l4.4 3.6"/><path d="M15.1 3.6l4.4 3.6"/></svg>' # studio - clapper
)
$i = 0
$h = [regex]::Replace($h, '<div class="wk-card"><div class="wk-eye">([^<]*)</div>', {
  param($m)
  $script:i++
  '<div class="wk-card wk-type t' + $script:i + '">' +
  '<div class="wk-type-head"><span class="wk-type-ico">' + $ico[$script:i - 1] + '</span>' +
  '<div class="wk-eye">' + $m.Groups[1].Value + '</div></div>'
})
"icons : $i event cards"

# --------------------------------------------- 2. real comparison, not two boxes
$oldSection = [regex]::Match($h, '(?s)<section class="section wrap">\s*<div class="sec-head"><div><div class="eyebrow">The Difference</div>.*?</section>').Value
if (-not $oldSection) { throw "comparison section not found" }

$rows = @(
  @{ c = "The broadcast itself";      them = "Multi-camera, professional, properly run";        us = "Multi-camera, professional, properly run"; themOk = $true }
  @{ c = "When the stream ends";      them = "You get a file and a link";                       us = "It gets a permanent home on BlackMarker.TV" }
  @{ c = "Promotion beforehand";      them = "Yours to organise";                               us = "Run-up spots on the Free Loop, the site and our socials" }
  @{ c = "The audience you gathered"; them = "Disperses the moment it&rsquo;s over";            us = "Stays with the archive, still finding the show" }
  @{ c = "Finding it six months on";  them = "A link you have to dig up and send";              us = "Sitting on a show page anyone can browse to" }
  @{ c = "Your next event";           them = "Start from zero again";                           us = "Builds on the audience the last one brought in" }
)
$rowHtml = foreach ($r in $rows) {
  $themIco = if ($r.themOk) { '<span class="cmp-i ok">&#10003;</span>' } else { '<span class="cmp-i no">&#10005;</span>' }
  @"
    <div class="cmp-row">
      <div class="cmp-crit">$($r.c)</div>
      <div class="cmp-them" data-lbl="Typical production company">$themIco<span>$($r.them)</span></div>
      <div class="cmp-us" data-lbl="Black Marker Media"><span class="cmp-i ok">&#10003;</span><span>$($r.us)</span></div>
    </div>
"@
}

$newSection = @"
<section class="section wrap">
  <div class="sec-head"><div><div class="eyebrow">The Difference</div><h2 class="sec-title">Production Bundled With Promotion</h2></div></div>
  <p class="cmp-lede">Most production companies shoot your event, hand over a file and move on. The stream was the product.
  We treat the stream as the <b>start</b> of the product &mdash; because we own a network to put it on.</p>

  <div class="cmp">
    <div class="cmp-row cmp-head">
      <div class="cmp-crit"></div>
      <div class="cmp-them">Typical production company</div>
      <div class="cmp-us">Black Marker Media</div>
    </div>
$($rowHtml -join "`n")
  </div>
</section>
"@
$h = $h.Replace($oldSection, $newSection)
"cmp   : two boxes -> $($rows.Count)-row comparison"

[System.IO.File]::WriteAllText($f, $h, $utf8)

# ------------------------------------------------------------------------- CSS
$css = Join-Path $B "src\workwithus.css"
$c = [System.IO.File]::ReadAllText($css, [System.Text.Encoding]::UTF8)
if ($c -notmatch '\.cmp\{') {
  $c += @'

/* two more accents so six-card sections can be colour-coded too */
.wk-type.t5{--tc:#FF8A3D;}
.wk-type.t6{--tc:#57D9A3;}

/* side-by-side comparison */
.cmp-lede{color:var(--muted);font-size:15px;line-height:1.6;max-width:760px;margin:-4px 0 20px;}
.cmp-lede b{color:var(--text);}
.cmp{border:1px solid var(--border);border-radius:14px;overflow:hidden;background:var(--surface);}
.cmp-row{display:grid;grid-template-columns:minmax(150px,1fr) 1.25fr 1.25fr;align-items:stretch;
  border-top:1px solid var(--border);}
.cmp-row:first-child{border-top:none;}
.cmp-crit{padding:14px 18px;font-size:13px;font-weight:800;color:var(--text);
  background:rgba(255,255,255,.018);display:flex;align-items:center;}
.cmp-them,.cmp-us{padding:14px 18px;font-size:13.5px;color:var(--muted);line-height:1.5;
  display:flex;gap:10px;align-items:flex-start;}
/* our column is tinted the whole way down so the eye tracks it */
.cmp-us{background:rgba(232,24,28,.055);border-left:1px solid rgba(232,24,28,.22);color:var(--text);}
.cmp-head{background:var(--surface2);}
.cmp-head .cmp-them,.cmp-head .cmp-us{font-size:12px;font-weight:900;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted2);padding-top:13px;padding-bottom:13px;}
.cmp-head .cmp-us{color:var(--red);}
.cmp-i{flex-shrink:0;width:17px;height:17px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:10px;font-weight:900;margin-top:1px;}
.cmp-i.ok{background:rgba(87,217,163,.16);color:#57D9A3;}
.cmp-i.no{background:rgba(232,24,28,.14);color:#ff6b6b;}

@media (max-width:820px){
  .cmp-row{grid-template-columns:1fr;}
  .cmp-head{display:none;}
  .cmp-crit{background:var(--surface2);font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);}
  .cmp-them,.cmp-us{flex-wrap:wrap;}
  .cmp-them::before,.cmp-us::before{content:attr(data-lbl);flex-basis:100%;font-size:10.5px;
    font-weight:900;letter-spacing:.1em;text-transform:uppercase;color:var(--muted2);margin-bottom:2px;}
  .cmp-us{border-left:none;border-top:1px solid rgba(232,24,28,.22);}
  .cmp-us::before{color:var(--red);}
}
'@
  [System.IO.File]::WriteAllText($css, $c, $utf8)
  "css   : comparison + t5/t6 accents"
}
