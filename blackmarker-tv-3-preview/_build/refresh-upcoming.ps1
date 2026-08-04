# Regenerates the homepage "Upcoming Videos" list as a REAL snapshot of the loop
# that is live at the moment this runs.
#
# Loop resolution (same logic the live endpoint will need -- see CC-23):
#   blocks recur weekly at 04:00 / 10:00 / 16:00 / 22:00 UTC
#   -> pick the block covering "now"
#   -> map weekday+hour back to the base week (Mon 2026-07-06 .. Sun 2026-07-12)
#   -> that schedule's playlist is the live loop
#   -> cursor = now - blockStart, matched against each item's playsAtSeconds
$ErrorActionPreference = "Stop"
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$HOMEPG = Join-Path $PREVIEW "BlackMarkerTV-3-LIVE-PREVIEW.html"

# --- items of the live loop, captured from list_playlist_items for the active block.
# Passed in as a here-string so this script stays runnable without MCP access.
$itemsCsv = Get-Content (Join-Path $PSScriptRoot "loop-items.csv") -Raw -Encoding UTF8
$items = $itemsCsv | ConvertFrom-Csv | ForEach-Object {
  [pscustomobject]@{ order=[int]$_.order; title=$_.title; dur=[int]$_.dur; at=[int]$_.at }
}

$blockStartUtc = [DateTime]::Parse($env:BM_BLOCK_START).ToUniversalTime()
$now = [DateTime]::UtcNow
$cursor = [int]($now - $blockStartUtc).TotalSeconds

function Fmt([int]$s) {
  if ($s -ge 3600) { return "{0}:{1:00}:{2:00}" -f [Math]::Floor($s/3600), [Math]::Floor(($s%3600)/60), ($s%60) }
  return "{0}:{1:00}" -f [Math]::Floor($s/60), ($s%60)
}
function Esc([string]$t) { return ($t -replace '&','&amp;' -replace '<','&lt;' -replace '>','&gt;') }

# "MV Dyce HowManyTimes" -> artist "Dyce", song "How Many Times"
function Split-Camel([string]$s) {
  $s = [regex]::Replace($s, '(?<=[a-z0-9])(?=[A-Z])', ' ')
  $s = [regex]::Replace($s, '(?<=[A-Z])(?=[A-Z][a-z])', ' ')
  return $s.Trim()
}
$KIND = @{ MV='music'; IA='id'; NBP='promo'; LP='live'; LI='interview' }
function Clean([string]$raw) {
  $t = $raw.Trim()
  $tok = $t -split '\s+', 2
  $pfx = $tok[0]
  $kind = if ($KIND.ContainsKey($pfx)) { $KIND[$pfx] } else { '' }

  if ($kind -eq 'music' -and $tok.Count -eq 2) {
    $rest = $tok[1] -split '\s+', 2
    $artist = Split-Camel $rest[0]
    $song = if ($rest.Count -eq 2) { Split-Camel $rest[1] } else { '' }
    return @{ a=$artist; s=$song; k='' }
  }
  if ($kind -eq 'id')        { return @{ a='Black Marker TV'; s='Station ID'; k='id' } }
  if ($kind -eq 'promo')     { return @{ a='Black Marker TV'; s='Promo'; k='id' } }
  if ($kind -eq 'live')      { $r = if($tok.Count -eq 2){Split-Camel $tok[1]}else{''}; return @{ a=$r; s='Live Performance'; k='' } }
  if ($kind -eq 'interview') { $r = if($tok.Count -eq 2){Split-Camel $tok[1]}else{''}; return @{ a=$r; s='Interview'; k='' } }
  if ($t -match 'Promo')     { return @{ a='Black Marker TV'; s='Promo'; k='id' } }
  if ($pfx -eq 'Performance'){ $r = if($tok.Count -eq 2){Split-Camel $tok[1]}else{''}; return @{ a=$r; s='Performance'; k='' } }
  return @{ a=(Split-Camel $t); s=''; k='' }
}

# --- find NOW, then the next 6
$nowIdx = -1
for ($i = 0; $i -lt $items.Count; $i++) {
  if ($cursor -ge $items[$i].at -and $cursor -lt ($items[$i].at + $items[$i].dur)) { $nowIdx = $i; break }
}
if ($nowIdx -lt 0) { throw "cursor $cursor fell outside every item -- block may have rolled" }

$rows = @()
$nowItem = $items[$nowIdx]
$c = Clean $nowItem.title
$songHtml = if ($c.s) { " <span class=""up-song"">&mdash; $(Esc $c.s)</span>" } else { "" }
$rows += '        <div class="up-row now"><span class="up-when"><span class="d"></span>Now</span><span class="up-mid"><span class="up-artist">{0}</span>{1}</span><span class="up-dur">{2}</span></div>' -f (Esc $c.a), $songHtml, (Fmt $nowItem.dur)

for ($n = 1; $n -le 6; $n++) {
  $idx = $nowIdx + $n
  if ($idx -ge $items.Count) { break }
  $it = $items[$idx]
  $c = Clean $it.title
  $songHtml = if ($c.s) { " <span class=""up-song"">&mdash; $(Esc $c.s)</span>" } else { "" }
  $when = if ($n -eq 1) { "Next" } else { "+" + (Fmt ($it.at - ($nowItem.at + $nowItem.dur))) }
  $rows += '        <div class="up-row"><span class="up-when">{0}</span><span class="up-mid"><span class="up-artist">{1}</span>{2}</span><span class="up-dur">{3}</span></div>' -f $when, (Esc $c.a), $songHtml, (Fmt $it.dur)
}

# --- splice into the homepage
$html = [System.IO.File]::ReadAllText($HOMEPG, [System.Text.Encoding]::UTF8)
$old = [regex]::Match($html, '(?s)<div class="up-list">.*?</div>\s*\r?\n\s*<span class="ann-note">').Value
if (-not $old) { throw "up-list block not found" }
$new = "<div class=`"up-list`">`n" + ($rows -join "`n") + "`n      </div>`n      <span class=`"ann-note`">"
$html = $html.Replace($old, $new)

# refresh the snapshot sentence inside the annotation
$et = $blockStartUtc.AddHours(-4)
$stamp = "<b>This is a real snapshot:</b> $($blockStartUtc.DayOfWeek) $('{0:HH:mm}' -f $et) ET block, captured at $('{0:HH:mm}' -f $now.AddHours(-4)) ET ($([Math]::Floor($cursor/60))m into the loop). It's static, so it drifts as time passes until the live endpoint drives it."
$html = [regex]::Replace($html, '<b>This is a real snapshot:</b>.*?until the live endpoint drives it\.', $stamp)

[System.IO.File]::WriteAllText($HOMEPG, $html, $utf8)
"block start : $($blockStartUtc.ToString('yyyy-MM-dd HH:mm')) UTC"
"cursor      : $cursor s ($([Math]::Floor($cursor/60))m)"
"now playing : $($nowItem.title)"
"rows        : $($rows.Count)"
