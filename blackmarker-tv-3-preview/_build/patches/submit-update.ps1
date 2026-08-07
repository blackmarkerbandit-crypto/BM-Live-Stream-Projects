# Submit Your Music page:
#  1. icon + colour treatment on the three "where it can land" cards
#  2. rebuild Do/Don't as a paired row layout so each rule sits opposite its mistake
$ErrorActionPreference = "Stop"
$B = "D:\Dropbox\WORK FILES\BMB\AI SHIT\blackmarker-tv-3-preview\_build"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$f = Join-Path $B "src\wk-submit.html"
$h = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)

# ------------------------------------------------------------- 1. landing cards
$ico = @(
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10a7 7 0 0111.9-4.9L20 8"/><path d="M20 4v4h-4"/><path d="M20 14a7 7 0 01-11.9 4.9L4 16"/><path d="M4 20v-4h4"/></svg>'
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2.2"/><path d="M8.4 8.4a5 5 0 000 7.2"/><path d="M15.6 15.6a5 5 0 000-7.2"/><path d="M5.8 5.8a8.6 8.6 0 000 12.4"/><path d="M18.2 18.2a8.6 8.6 0 000-12.4"/></svg>'
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 13v-1a8 8 0 0116 0v1"/><path d="M4 13h2.6a1 1 0 011 1v4a1 1 0 01-1 1H5.4A1.4 1.4 0 014 17.6z"/><path d="M20 13h-2.6a1 1 0 00-1 1v4a1 1 0 001 1h1.2a1.4 1.4 0 001.4-1.4z"/></svg>'
)
$i = 0
$h = [regex]::Replace($h, '<div class="wk-card">\s*\r?\n(\s*)<div class="wk-eye">(0\d) &middot; ([^<]*)</div>', {
  param($m)
  $script:i++
  $pad = $m.Groups[1].Value
  '<div class="wk-card wk-type t' + $script:i + '">' + "`n" +
  $pad + '<div class="wk-type-head">' + "`n" +
  $pad + '  <span class="wk-type-ico">' + $ico[$script:i - 1] + '</span>' + "`n" +
  $pad + '  <div class="wk-eye">' + $m.Groups[2].Value + ' &middot; ' + $m.Groups[3].Value + '</div>' + "`n" +
  $pad + '</div>'
})
"icons : $i landing cards"

# ------------------------------------------------------- 2. Do / Don't as pairs
$old = [regex]::Match($h, '(?s)<section class="section wrap">\s*<div class="sec-head"><div><div class="eyebrow">Before You Send</div>.*?</section>').Value
if (-not $old) { throw "do/don't section not found" }

$rows = @(
  @{ c = "What you send";     do = "Video &mdash; a performance, music video, live set or visualizer"; dont = "Audio only, when a video of it exists" }
  @{ c = "The link";          do = "One public link that plays on click. YouTube is perfect";          dont = "Anything behind a login, or a file we have to download" }
  @{ c = "Not out yet?";      do = "Unlisted YouTube is completely fine";                              dont = "Expiring transfers &mdash; WeTransfer dies before we reach it" }
  @{ c = "How much";          do = "Your single best piece";                                           dont = "Ten links at once and a &ldquo;pick whichever&rdquo;" }
  @{ c = "What you tell us";  do = "Who you are, what we&rsquo;re hearing, and what you want from it";  dont = "A bare link with no message attached" }
  @{ c = "Rights";            do = "Samples and beats cleared before you send it";                     dont = "Anything uncleared &mdash; we legally can&rsquo;t air it" }
)
$rowHtml = foreach ($r in $rows) {
  @"
    <div class="cmp-row">
      <div class="cmp-crit">$($r.c)</div>
      <div class="cmp-them" data-lbl="Do this"><span class="cmp-i ok">&#10003;</span><span>$($r.do)</span></div>
      <div class="cmp-us" data-lbl="Not this"><span class="cmp-i no">&#10005;</span><span>$($r.dont)</span></div>
    </div>
"@
}

$new = @"
<section class="section wrap">
  <div class="sec-head"><div><div class="eyebrow">Before You Send</div><h2 class="sec-title">How to Not Get Skipped</h2></div></div>
  <p class="cmp-lede">None of this is us being precious. Every one of these is a real reason something didn&rsquo;t get
  watched &mdash; and we&rsquo;d rather you knew before you sent it than wonder afterwards.</p>

  <div class="cmp cmp-dd">
    <div class="cmp-row cmp-head">
      <div class="cmp-crit"></div>
      <div class="cmp-them">Do this</div>
      <div class="cmp-us">Not this</div>
    </div>
$($rowHtml -join "`n")
  </div>

  <div class="wk-note"><b>Submitting is free, and it always will be.</b> We don&rsquo;t charge for consideration and we
  don&rsquo;t run pay-to-play. What that also means: there&rsquo;s no set turnaround and no guarantee a piece airs. We work
  through the queue as shows tape. If it&rsquo;s a fit, we&rsquo;ll reach out about when it&rsquo;s going up.</div>
</section>
"@
$h = $h.Replace($old, $new)
"dd    : $($rows.Count) do/don't pairs"
[System.IO.File]::WriteAllText($f, $h, $utf8)

# --------------------------------------------------------------------- CSS
$css = Join-Path $B "src\workwithus.css"
$c = [System.IO.File]::ReadAllText($css, [System.Text.Encoding]::UTF8)
if ($c -notmatch '\.cmp-dd\b') {
  $c += @'

/* Do / Don't variant of the comparison grid. Same three-column structure, but the
   GOOD column is the middle one and gets the positive tint - so the eye lands on
   what to do, not on the list of mistakes. */
.cmp-dd .cmp-them{background:rgba(87,217,163,.06);border-right:1px solid rgba(87,217,163,.2);color:var(--text);}
.cmp-dd .cmp-us{background:transparent;border-left:none;color:var(--muted);}
.cmp-dd .cmp-head .cmp-them{color:#57D9A3;}
.cmp-dd .cmp-head .cmp-us{color:#ff6b6b;}
@media (max-width:820px){
  .cmp-dd .cmp-them{border-right:none;}
  .cmp-dd .cmp-us{border-top:1px solid var(--border);}
  .cmp-dd .cmp-them::before{color:#57D9A3;}
  .cmp-dd .cmp-us::before{color:#ff6b6b;}
}
'@
  [System.IO.File]::WriteAllText($css, $c, $utf8)
  "css   : cmp-dd variant added"
}
