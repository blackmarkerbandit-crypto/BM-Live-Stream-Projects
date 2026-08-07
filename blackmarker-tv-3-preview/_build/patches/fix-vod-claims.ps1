# The Free Loop is live rotation. It is NOT an on-demand library - only show episodes
# and event broadcasts have on-demand homes. Removes every claim that says otherwise.
$ErrorActionPreference = "Stop"
$B = "D:\Dropbox\WORK FILES\BMB\AI SHIT\blackmarker-tv-3-preview\_build\src"
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Swap([string]$file, [string]$old, [string]$new, [string]$label) {
  $p = Join-Path $B $file
  $c = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
  if (-not $c.Contains($old)) { "  MISS  $label"; return }
  [System.IO.File]::WriteAllText($p, $c.Replace($old, $new), $utf8)
  "  ok    $label"
}

"--- submit your music ---"
Swap "wk-submit.html" `
  'The Loop runs music videos around the clock. Accepted videos go into regular rotation alongside everything else on the network &mdash; and stay in the on-demand library.' `
  'The Loop runs music videos around the clock. Accepted videos go into regular rotation alongside everything else on the network.' `
  "removed 'stay in the on-demand library'"

Swap "wk-submit.html" `
  '<li>Video required &mdash; this is a visual rotation</li>' `
  '<li>Video required &mdash; this is a visual rotation</li><li>Airplay on the Loop &mdash; it&rsquo;s a live rotation, not a VOD library</li>' `
  "added explicit 'not a VOD library' line"

"--- advertising ---"
Swap "wk-advertising.html" `
  'You&rsquo;re buying a named
    position: a slot in the Loop rotation, a show to call yours, or your name across an event broadcast. And it doesn&rsquo;t
    evaporate when the stream ends &mdash; your brand stays in the permanent on-demand archive alongside the episode.' `
  'You&rsquo;re buying a named
    position: a slot in the Loop rotation, a show to call yours, or your name across an event broadcast. Sponsor a
    <b>show</b> or an <b>event</b> and it doesn&rsquo;t evaporate when the stream ends &mdash; your brand carries into the
    permanent on-demand episode, not just the live window. (Loop rotation is live airplay; the Loop itself isn&rsquo;t
    an on-demand library.)' `
  "scoped archive claim to shows/events"

"--- partnerships ---"
Swap "wk-partnerships.html" `
  '<p>Bring a show to the network or license your catalogue into the rotation. You keep making it; we handle broadcast, distribution and the on-demand archive.</p>' `
  '<p>Bring a show to the network or license your catalogue into the Loop. You keep making it; we handle the broadcast and the distribution &mdash; and a show gets its own on-demand home.</p>' `
  "content partner intro"

Swap "wk-partnerships.html" `
  '<li>A slot on the <b>24/7 Free Loop</b> plus a permanent on-demand home</li>' `
  '<li>A show gets its own page and a permanent on-demand archive</li>
        <li>Catalogue and music videos go into <b>24/7 Free Loop</b> rotation &mdash; live airplay</li>' `
  "split loop rotation from on-demand home"
