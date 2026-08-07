# Advertising page: per-placement icons/colours (matching the Partnerships treatment)
# + Eric's revised rate card.
$ErrorActionPreference = "Stop"
$B = "D:\Dropbox\WORK FILES\BMB\AI SHIT\blackmarker-tv-3-preview\_build"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$f = Join-Path $B "src\wk-advertising.html"
$h = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)

# ------------------------------------------------ 1. icons on the placement cards
$icons = @{
  1 = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10a7 7 0 0111.9-4.9L20 8"/><path d="M20 4v4h-4"/><path d="M20 14a7 7 0 01-11.9 4.9L4 16"/><path d="M4 20v-4h4"/></svg>'   # loop
  2 = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="5" width="19" height="13" rx="2.5"/><path d="M8 21h8"/><path d="M12 18v3"/></svg>'                       # broadcast screen
  3 = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2.2"/><path d="M8.4 8.4a5 5 0 000 7.2"/><path d="M15.6 15.6a5 5 0 000-7.2"/><path d="M5.8 5.8a8.6 8.6 0 000 12.4"/><path d="M18.2 18.2a8.6 8.6 0 000-12.4"/></svg>' # live signal
  4 = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11v2a1 1 0 001 1h2l5 4V6L6 10H4a1 1 0 00-1 1z"/><path d="M16 8.5a5 5 0 010 7"/></svg>'                  # megaphone
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
"icons : $n placement cards"

# --------------------------------------------------------- 2. revised rate card
function Swap([string]$old, [string]$new, [string]$label) {
  if (-not $script:h.Contains($old)) { "  MISS  $label"; return }
  $script:h = $script:h.Replace($old, $new)
  "  ok    $label"
}

# Show Sponsor: $300/ep -> $75/ep, and $1,200/mo all shows -> $300/mo all five
Swap '<div class="wk-price">$300<span> / episode</span></div>
      <div class="wk-rate-sub">Or $1,200/mo across all shows</div>' `
     '<div class="wk-price">$75<span> / episode</span></div>
      <div class="wk-rate-sub">Or <b>$300/mo</b> &mdash; all five shows</div>' `
     "show sponsor -> 75/ep, 300/mo"

# Live Broadcast Sponsor: flat $750 -> a range that scales with the event
Swap '<div class="wk-price">$750<span> / event</span></div>
      <div class="wk-rate-sub">Battles, festivals, parades, conferences</div>' `
     '<div class="wk-price">$250&ndash;$500<span> / event</span></div>
      <div class="wk-rate-sub">Scales with the event &mdash; battles, festivals, parades, conferences</div>' `
     "live broadcast -> 250-500"

# Network Partner: $2,000 -> $1,500
Swap '<div class="wk-price">$2,000<span> / month</span></div>' `
     '<div class="wk-price">$1,500<span> / month</span></div>' `
     "network partner -> 1500"

# promo package is unchanged at $400 / 2-week campaign - just make the window explicit
Swap '<div class="wk-rate-sub">Two-week push &mdash; selective, we vet every one</div>' `
     '<div class="wk-rate-sub">Two-week campaign &mdash; selective, we vet every one</div>' `
     "promo wording"

[System.IO.File]::WriteAllText($f, $h, $utf8)
"written"
