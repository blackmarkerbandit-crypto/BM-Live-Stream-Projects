$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$SCR  = "C:\Users\imagi\AppData\Local\Temp\claude\d--Dropbox-WORK-FILES-BMB-AI-SHIT-BM-Live-Stream-Projects\bba4b6cc-109c-4e11-ab1d-221c18f2d1f9\scratchpad"
$ART  = "$SCR\sched-art"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$OUT  = Join-Path $PREVIEW "BlackMarkerTV-3-SCHEDULE.html"

$bak = Join-Path $PREVIEW ("_backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Get-ChildItem $PREVIEW -Filter "*.html" | Copy-Item -Destination $bak
"backed up : $bak"

# ---------- re-encode card art to 800x450 jpeg (cards render ~400px; 2x for retina)
function Get-B64([string]$file) {
  $img = [System.Drawing.Image]::FromFile((Join-Path $ART $file))
  $W = 800; $H = 450
  $bmp = New-Object System.Drawing.Bitmap($W, $H)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
  $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
  # white-background logo art gets a white fill so PNG transparency doesn't go black
  $g.Clear([System.Drawing.Color]::White)
  $scale = [Math]::Max($W / $img.Width, $H / $img.Height)
  $dw = [int]($img.Width * $scale); $dh = [int]($img.Height * $scale)
  $g.DrawImage($img, [int](($W - $dw) / 2), [int](($H - $dh) / 2), $dw, $dh)
  $g.Dispose()
  $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
  $ps = New-Object System.Drawing.Imaging.EncoderParameters(1)
  $ps.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [int64]82)
  $tmp = Join-Path $env:TEMP ("sch-" + [IO.Path]::GetFileNameWithoutExtension($file) + ".jpg")
  $bmp.Save($tmp, $codec, $ps); $bmp.Dispose(); $img.Dispose()
  return [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($tmp))
}

# ---------- schedule data (verbatim from www.blackmarker.tv/Schedule, EST -> ET)
# Order = Eric's editorial priority (2026-08-04): CUDI 1, Weekly Interrupt 2,
# For The Record 3, Alien Podcast 4. (Talking Tipsy 5 is in the On Demand block.)
$live = @(
  @{ name="Can You Dig It!? Live Music Review"; art="MainImage1080.png";          page="BlackMarkerTV-3-CAN-YOU-DIG-IT.html"
     when="Last Fridays &middot; 8:00 PM ET";            replay="Sat &amp; Sun &middot; 12:00 PM ET" }
  @{ name="The Weekly Interrupt";            art="VODCategoryLandscape47.jpg";   page="BlackMarkerTV-3-WEEKLY-INTERRUPT.html"
     when="1st &amp; 3rd Tuesdays &middot; 8:00 PM ET";  replay="Fri&ndash;Wed &middot; 6:00 PM ET" }
  @{ name="For The Record Album Reviews";    art="VODCategoryLandscape92.jpg";   page="BlackMarkerTV-3-FOR-THE-RECORD.html"
     when="Last Mondays &middot; 9:00 PM ET";            replay="Wednesdays &middot; 6:00 PM ET" }
  @{ name="The Alien Podcast";               art="ShowCoverImage.jpg";           page="BlackMarkerTV-3-ALIEN-PODCAST.html"
     when="3rd Sundays &middot; 6:00 PM ET";             replay="Thursdays &middot; 6:00 PM ET" }
)
# Talking Tipsy is off the live schedule while the show is being revamped (Eric, 2026-08-03).
# Its 11 episodes are still live, so it keeps its show-page link unlike the other two.
$vod = @(
  @{ name="Talking Tipsy Podcast"; art="TalkingTipsyScreen_v2-4K.jpg"; page="BlackMarkerTV-3-TALKING-TIPSY.html" }
  @{ name="Duh Diggity Show";      art="VODCategoryLandscape48.jpg";   page="" }
  @{ name="2 Bafoonz, 1 Lagoon";   art="VODCategoryLandscape49.jpg";   page="" }
)

# ---------- build cards
$liveCards = foreach ($s in $live) {
  $b64 = Get-B64 $s.art
  $cta = if ($s.page) { "<a class=""sch-link"" href=""$($s.page)"">Watch episodes <span>&rarr;</span></a>" } else { "" }
@"
      <article class="sch-card">
        <a class="sch-art" href="$($s.page)">
          <img src="data:image/jpeg;base64,$b64" alt="$($s.name)" loading="lazy">
          <span class="sch-badge">Live</span>
        </a>
        <div class="sch-body">
          <h3 class="sch-name">$($s.name)</h3>
          <div class="sch-slot is-live">
            <span class="sch-lbl">New</span>
            <span class="sch-when">$($s.when)</span>
          </div>
          <div class="sch-slot">
            <span class="sch-lbl">Replays</span>
            <span class="sch-when">$($s.replay)</span>
          </div>
          $cta
        </div>
      </article>
"@
}

$vodCards = foreach ($s in $vod) {
  $b64 = Get-B64 $s.art
  # shows that still have an archive keep a route to it; the others are art-only
  $artOpen  = if ($s.page) { "<a class=""sch-art"" href=""$($s.page)"">" } else { "<div class=""sch-art"">" }
  $artClose = if ($s.page) { "</a>" } else { "</div>" }
  $cta      = if ($s.page) { "<a class=""sch-link"" href=""$($s.page)"">Watch episodes <span>&rarr;</span></a>" } else { "" }
@"
      <article class="sch-card is-vod">
        $artOpen
          <img src="data:image/jpeg;base64,$b64" alt="$($s.name)" loading="lazy">
          <span class="sch-badge is-vod">On Demand</span>
        $artClose
        <div class="sch-body">
          <h3 class="sch-name">$($s.name)</h3>
          <div class="sch-slot">
            <span class="sch-lbl">Live</span>
            <span class="sch-when is-off">No live broadcasts</span>
          </div>
          <div class="sch-slot">
            <span class="sch-lbl">Watch</span>
            <span class="sch-when">On demand, anytime on The Loop</span>
          </div>
          $cta
        </div>
      </article>
"@
}

$body = (Get-Content "$SCR\schedule-body.html" -Raw -Encoding UTF8)
$body = $body.Replace("{{LIVE_CARDS}}", ($liveCards -join "`n")).Replace("{{VOD_CARDS}}", ($vodCards -join "`n"))

# ---------- splice into the shared shell
$base = [System.IO.File]::ReadAllText((Join-Path $PREVIEW "BlackMarkerTV-3-CAN-YOU-DIG-IT.html"), [System.Text.Encoding]::UTF8)
$css  = [System.IO.File]::ReadAllText("$SCR\schedule.css", [System.Text.Encoding]::UTF8)

$startTag = "<!-- SHOW HERO -->"
$endTag   = "<!-- ============ FOOTER (no chat support) ============ -->"
$s1 = $base.IndexOf($startTag); $e1 = $base.IndexOf($endTag)
if ($s1 -lt 0 -or $e1 -le $s1) { throw "content boundaries not found" }
$c = $base.Substring(0, $s1) + $body + "`n`n" + $base.Substring($e1)

$i = $c.LastIndexOf("</style>")
$c = $c.Substring(0, $i) + "`n" + $css + "`n" + $c.Substring($i)

$c = [regex]::Replace($c, '<title>.*?</title>', '<title>Schedule &mdash; BlackMarker.TV</title>')

# nav: clear On Demand highlight, light up Schedule
$sub = [regex]::Match($c, '(?s)<span class="submenu">.*?</span>\s*(?=</span>)').Value.TrimEnd()
$c = $c.Replace($sub, ($sub -replace '\s*class="on"', ''))
$c = $c.Replace('<a href="#" class="on">On Demand</a>', '<a href="#">On Demand</a>')
$c = $c.Replace('<a href="#">Schedule</a>', '<a href="BlackMarkerTV-3-SCHEDULE.html" class="on">Schedule</a>')

[System.IO.File]::WriteAllText($OUT, $c, $utf8)
"built     : BlackMarkerTV-3-SCHEDULE.html ($([Math]::Round((Get-Item $OUT).Length/1KB)) KB)"

# ---------- point every other page's Schedule nav link here
foreach ($f in Get-ChildItem $PREVIEW -Filter "BlackMarkerTV-3-*.html") {
  if ($f.Name -eq "BlackMarkerTV-3-SCHEDULE.html") { continue }
  $p = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $b = $p
  $p = $p.Replace('<a href="#">Schedule</a>', '<a href="BlackMarkerTV-3-SCHEDULE.html">Schedule</a>')
  if ($p -ne $b) { [System.IO.File]::WriteAllText($f.FullName, $p, $utf8); "relinked  : $($f.Name)" }
}
