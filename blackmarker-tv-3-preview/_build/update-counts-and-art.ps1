$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$utf8 = New-Object System.Text.UTF8Encoding($false)

$bak = Join-Path $PREVIEW ("_backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Get-ChildItem $PREVIEW -Filter "*.html" | Copy-Item -Destination $bak
"backed up : $bak"

# ---------------------------------------------------------------------------
# 1. Talking Tipsy -- swap in the real show art (4K 16:9 -> 1200x675 jpeg)
# ---------------------------------------------------------------------------
$src = "D:\Dropbox\WORK FILES\BMB\SHOW FOLDERS\Talking Tipsy\TalkingTipsyScreen_v2-4K.jpg"
$W = 1200; $H = 675
$img = [System.Drawing.Image]::FromFile($src)
$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$scale = [Math]::Max($W / $img.Width, $H / $img.Height)
$dw = [int]($img.Width * $scale); $dh = [int]($img.Height * $scale)
$g.DrawImage($img, [int](($W - $dw) / 2), [int](($H - $dh) / 2), $dw, $dh)
$g.Dispose()
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ps = New-Object System.Drawing.Imaging.EncoderParameters(1)
$ps.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [int64]86)
$tmp = Join-Path $env:TEMP "tt-art.jpg"
$bmp.Save($tmp, $codec, $ps)
$bmp.Dispose(); $img.Dispose()

$b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($tmp))
$ttFile = Join-Path $PREVIEW "BlackMarkerTV-3-TALKING-TIPSY.html"
$c = [System.IO.File]::ReadAllText($ttFile, [System.Text.Encoding]::UTF8)
$oldImg = [regex]::Match($c, '<img class="show-art-img" src="data:image/[^"]+"[^>]*>').Value
$newImg = '<img class="show-art-img" src="data:image/jpeg;base64,{0}" alt="Talking Tipsy show art">' -f $b64
$c = $c.Replace($oldImg, $newImg)
[System.IO.File]::WriteAllText($ttFile, $c, $utf8)
"art swapped : Talking Tipsy ($([Math]::Round((Get-Item $tmp).Length/1KB)) KB embedded)"

# ---------------------------------------------------------------------------
# 2. Episode counts -> exactly what the MRSS feed / OTT grid renders
# ---------------------------------------------------------------------------
$counts = @{
  "BlackMarkerTV-3-WEEKLY-INTERRUPT.html"    = 12
  "BlackMarkerTV-3-CAN-YOU-DIG-IT.html"      = 21
  "BlackMarkerTV-3-TALKING-TIPSY.html"       = 11
  "BlackMarkerTV-3-ALIEN-PODCAST.html"       = 8
  "BlackMarkerTV-3-FOR-THE-RECORD.html"      = 10
  "BlackMarkerTV-3-PERFORMANCE-BATTLES.html" = 19
}

foreach ($k in $counts.Keys) {
  $f = Join-Path $PREVIEW $k
  $c = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)

  # first .show-stat is always the episode/battle count tile
  $m = [regex]::Match($c, '(?s)(<div class="show-stats">\s*<div class="show-stat"><span class="n">)([^<]*)(</span>)')
  if (-not $m.Success) { throw "count tile not found in $k" }
  $was = $m.Groups[2].Value
  if ($was -eq [string]$counts[$k]) { "count ok    : $k ($was)"; continue }

  $c = $c.Remove($m.Groups[2].Index, $m.Groups[2].Length).Insert($m.Groups[2].Index, [string]$counts[$k])
  [System.IO.File]::WriteAllText($f, $c, $utf8)
  "count fixed : $k  $was -> $($counts[$k])"
}
