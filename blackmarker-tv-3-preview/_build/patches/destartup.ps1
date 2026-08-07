# Removes every "we're small / early / build phase" framing from the Work With Us pages.
# Rule applied: stop apologising, but do NOT replace it with claims we can't back.
# Nothing here asserts audience size or reach - it just stops volunteering weakness.
$ErrorActionPreference = "Stop"
$B = "D:\Dropbox\WORK FILES\BMB\AI SHIT\blackmarker-tv-3-preview\_build"
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Swap([string]$file, [string]$old, [string]$new, [string]$label) {
  $p = Join-Path $B $file
  $c = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
  if (-not $c.Contains($old)) { "  MISS  $label"; return }
  [System.IO.File]::WriteAllText($p, $c.Replace($old, $new), $utf8)
  "  ok    $label"
}

"--- partnerships ---"
Swap "src\wk-partnerships.html" `
'      <div class="wk-eye">Stage</div>
      <h3>Early enough to matter</h3>
      <p>The network is in its build phase. That&rsquo;s an honest trade: smaller audience today, but real input into programming, better terms, and a founding credit that isn&rsquo;t available later.</p>' `
'      <div class="wk-eye">Access</div>
      <h3>You deal with decision-makers</h3>
      <p>No account managers, no layers between you and the people who make the show. Programming, scheduling and creative happen in one room &mdash; and partners are in it. Faster answers, and terms shaped around what you&rsquo;re actually trying to do.</p>' `
"Stage card -> Access"

Swap "src\wk-partnerships.html" `
'  <div class="wk-note"><b>Straight talk on where we are.</b> Black Marker Media is a working production company with recurring contract revenue.
  BlackMarker.TV is newer &mdash; the programming, catalogue and infrastructure are built, and audience is what we&rsquo;re building now.
  We&rsquo;d rather tell you that up front than sell you a number we can&rsquo;t stand behind. Ask us for real figures and you&rsquo;ll get them.</div>' `
'  <div class="wk-note"><b>How we work.</b> Every partnership starts with a real conversation about what you&rsquo;re trying to accomplish &mdash;
  not a media kit and a rate sheet. We&rsquo;ll tell you plainly where we can move the needle for you and where we can&rsquo;t, and we&rsquo;ll bring
  numbers to back either answer. If it&rsquo;s a fit, we move fast.</div>' `
"straight-talk note -> How we work"

Swap "src\wk-partnerships.html" `
'      <p>We&rsquo;re a profitable production business building a network on top of it. If that shape interests you, the numbers conversation is open.</p>' `
'      <p>We run a profitable production business and an independent broadcast network. If that shape interests you, the numbers conversation is open.</p>' `
"investment intro"

Swap "src\wk-partnerships.html" `
'        <li>Existing production revenue funds the network build</li>' `
'        <li>Production revenue funds the network &mdash; it isn&rsquo;t waiting on outside money</li>' `
"investment bullet"

"--- advertising ---"
Swap "src\wk-advertising.html" `
'    <div><div class="eyebrow">Charter Rates</div><h2 class="sec-title">Founding Advertiser Pricing</h2></div>
    <span class="sec-link">Introductory &middot; locked for 12 months</span>' `
'    <div><div class="eyebrow">Rates</div><h2 class="sec-title">Advertising Rates</h2></div>
    <span class="sec-link">Held for 12 months from signing</span>' `
"rates heading"

$oldNote = @'
  <div class="wk-note">
    <b>Why these numbers are low, in plain terms.</b> BlackMarker.TV is in its build phase. We are not going to quote you a
    CPM or an impressions number, because the audience we can currently <i>prove</i> on our own player is small &mdash; the
    network&rsquo;s reach today sits mostly on our social and event side, and our own analytics only measure the ChannelCast
    player. These are <b>charter rates</b>: priced for what we can actually deliver now, locked for twelve months, in
    exchange for you being early. When the audience numbers justify more, your rate doesn&rsquo;t move. Ask us for the real
    play data before you commit &mdash; we&rsquo;ll send it.
  </div>
'@
$newNote = @'
  <div class="wk-note">
    <b>How we price.</b> We sell <b>placement and association</b> &mdash; not impressions. You&rsquo;re buying a named
    position: a slot in the Loop rotation, a show to call yours, or your name across an event broadcast. And it doesn&rsquo;t
    evaporate when the stream ends &mdash; your brand stays in the permanent on-demand archive alongside the episode.
    Rates are held for twelve months from signing. Want the play data behind a specific placement before you commit?
    Ask and we&rsquo;ll send it.
  </div>
'@
Swap "src\wk-advertising.html" $oldNote $newNote "pricing rationale note"

"--- hero copy (build script) ---"
Swap "build-workwithus.ps1" `
'Charter rates below &mdash; priced honestly for a network in its build phase."' `
'Rates below, held for twelve months from signing."' `
"advertising hero desc"

# the committed toolchain keeps page bodies + css in src\, so point the builder there
$p = Join-Path $B "build-workwithus.ps1"
$c = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
if ($c -notmatch '\$SRC\s*=') {
  $c = $c.Replace('$SCR = $PSScriptRoot', '$SCR = $PSScriptRoot' + "`n" + '$SRC = Join-Path $PSScriptRoot "src"   # page bodies + css live here in the repo layout')
  $c = $c.Replace('(Join-Path $SCR $p.body)', '(Join-Path $SRC $p.body)')
  $c = $c.Replace('(Join-Path $SCR "workwithus.css")', '(Join-Path $SRC "workwithus.css")')
  [System.IO.File]::WriteAllText($p, $c, $utf8)
  "  ok    builder paths -> src\"
}
