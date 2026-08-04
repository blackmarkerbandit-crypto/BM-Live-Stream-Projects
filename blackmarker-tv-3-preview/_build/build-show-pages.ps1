# Builds every generated show page listed in site-data.ps1 ($GENERATED), then
# rebuilds the nav on all pages. Supersedes build-archive-shows.ps1.
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$SCR = "C:\Users\imagi\AppData\Local\Temp\claude\d--Dropbox-WORK-FILES-BMB-AI-SHIT-BM-Live-Stream-Projects\bba4b6cc-109c-4e11-ab1d-221c18f2d1f9\scratchpad"
$utf8 = New-Object System.Text.UTF8Encoding($false)
. (Join-Path $SCR "site-data.ps1")

$bak = Join-Path $PREVIEW ("_backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Get-ChildItem $PREVIEW -Filter "*.html" | Copy-Item -Destination $bak
"backed up : $bak"

function Get-ArtB64([string]$file) {
  $img = [System.Drawing.Image]::FromFile("$SCR\sched-art\$file")
  $W = 1200; $H = 675
  $bmp = New-Object System.Drawing.Bitmap($W, $H)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
  $g.Clear([System.Drawing.Color]::White)   # logo art sits on white; avoids a black letterbox
  $scale = [Math]::Max($W / $img.Width, $H / $img.Height)
  $dw = [int]($img.Width * $scale); $dh = [int]($img.Height * $scale)
  $g.DrawImage($img, [int](($W - $dw) / 2), [int](($H - $dh) / 2), $dw, $dh)
  $g.Dispose()
  $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
  $ps = New-Object System.Drawing.Imaging.EncoderParameters(1)
  $ps.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [int64]86)
  $tmp = Join-Path $env:TEMP "gen-$file.jpg"
  $bmp.Save($tmp, $codec, $ps); $bmp.Dispose(); $img.Dispose()
  return [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($tmp))
}

# base shell = Can You Dig It (a real, hand-tuned show page)
$base = [System.IO.File]::ReadAllText((Join-Path $PREVIEW "BlackMarkerTV-3-CAN-YOU-DIG-IT.html"), [System.Text.Encoding]::UTF8)
$A_TITLE  = [regex]::Match($base, '<title>.*?</title>').Value
$A_CRUMB  = [regex]::Match($base, '<div class="show-crumb">.*?</div>').Value
$A_KICKER = [regex]::Match($base, '<div class="show-kicker">.*?</div>').Value
$A_H1     = [regex]::Match($base, '<h1 class="show-title">.*?</h1>').Value
$A_DESC   = [regex]::Match($base, '<p class="show-desc">.*?</p>').Value
$A_STATS  = [regex]::Match($base, '(?s)<div class="show-stats">.*?</div>\s*</div>').Value
$A_IMG    = [regex]::Match($base, '<img class="show-art-img" src="data:image/[^"]+"[^>]*>').Value
$A_CAT    = [regex]::Match($base, 'category:\s*"[^"]*"').Value
foreach ($n in @("A_TITLE","A_CRUMB","A_KICKER","A_H1","A_DESC","A_STATS","A_IMG","A_CAT")) {
  if (-not (Get-Variable $n -ValueOnly)) { throw "anchor $n missing from base page" }
}

$emptyCss = @'
.ott-empty{border:1px dashed var(--border2);border-radius:14px;background:var(--surface);
  padding:44px 28px;text-align:center;margin-top:8px;}
.ott-empty-icon{width:46px;height:46px;border-radius:50%;background:var(--surface2);border:1px solid var(--border2);
  color:var(--red);font-size:17px;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;}
.ott-empty-h{font-size:18px;font-weight:900;letter-spacing:-.015em;margin-bottom:9px;}
.ott-empty-p{font-size:14px;color:var(--muted);line-height:1.6;max-width:520px;margin:0 auto 20px;}
.ott-empty-p b{color:var(--text);}
'@

foreach ($a in $GENERATED) {
  $c = $base
  $eid = "empty-$($a.slug)"

  $stats = @"
<div class="show-stats">
          <div class="show-stat"><span class="n">$($a.s1n)</span><span class="l">$($a.s1l)</span></div>
          <div class="show-stat"><span class="n">$($a.s2n)</span><span class="l">$($a.s2l)</span></div>
          <div class="show-stat"><span class="n">$($a.s3n)</span><span class="l">$($a.s3l)</span></div>
        </div>
"@

  $crumb = '<div class="show-crumb"><a href="#">' + $a.crumb +
           '</a> <span class="sep">/</span> <span>' + $a.title + '</span></div>'

  $c = $c.Replace($A_TITLE,  "<title>$($a.title) &mdash; BlackMarker.TV</title>")
  $c = $c.Replace($A_CRUMB,  $crumb)
  $c = $c.Replace($A_KICKER, "<div class=""show-kicker"">$($a.kicker)</div>")
  $c = $c.Replace($A_H1,     "<h1 class=""show-title"">$($a.title)</h1>")
  $c = $c.Replace($A_DESC,   "<p class=""show-desc"">$($a.desc)</p>")
  $c = $c.Replace($A_STATS,  $stats.TrimEnd())
  $c = $c.Replace($A_IMG,    ('<img class="show-art-img" src="data:image/jpeg;base64,{0}" alt="{1} show art">' -f (Get-ArtB64 $a.art), $a.title))
  $c = $c.Replace($A_CAT,    "category: ""$($a.cat)""")

  # safety net: only surfaces if the OTT grid renders nothing (feed hiccup / empty category)
  $empty = @"
  <div class="ott-empty" id="$eid" hidden>
    <div class="ott-empty-icon">&#9654;</div>
    <h3 class="ott-empty-h">Episodes aren&rsquo;t loading right now</h3>
    <p class="ott-empty-p">The <b>$($a.title)</b> archive lives on ChannelCast and should appear here.
    Give it a refresh &mdash; if it still doesn&rsquo;t show, the feed is having a moment.</p>
    <a class="btn btn-ghost" href="BlackMarkerTV-3-SCHEDULE.html">See the full schedule</a>
  </div>
  <script>
    (function () {
      var host = document.getElementById('cc-ott-019eba4dbb24746eafa619f8fea1e9aa');
      var empty = document.getElementById('$eid');
      if (!host || !empty) return;
      function check() { empty.hidden = host.querySelectorAll('.ott-card').length > 0; }
      new MutationObserver(check).observe(host, { childList: true, subtree: true });
      [600, 1500, 3000, 5000].forEach(function (ms) { setTimeout(check, ms); });
    })();
  </script>
"@
  $idx = $c.IndexOf('<!-- CTA -->')
  if ($idx -lt 0) { throw "CTA marker not found for $($a.file)" }
  $c = $c.Substring(0, $idx) + $empty + "`n`n" + $c.Substring($idx)

  $i = $c.LastIndexOf("</style>")
  $c = $c.Substring(0, $i) + $emptyCss + "`n" + $c.Substring($i)

  $out = Join-Path $PREVIEW $a.file
  [System.IO.File]::WriteAllText($out, $c, $utf8)
  "built     : $($a.file) ($([Math]::Round((Get-Item $out).Length/1KB)) KB)"
}

# nav is owned by build-nav.ps1
& (Join-Path $SCR 'build-nav.ps1')
