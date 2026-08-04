Add-Type -AssemblyName System.Drawing
$out = "C:\Users\imagi\AppData\Local\Temp\claude\d--Dropbox-WORK-FILES-BMB-AI-SHIT-BM-Live-Stream-Projects\bba4b6cc-109c-4e11-ab1d-221c18f2d1f9\scratchpad\art"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$W = 1200; $H = 675

function Save-Jpeg([System.Drawing.Bitmap]$bmp, [string]$path, [int]$q) {
  $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
  $ps = New-Object System.Drawing.Imaging.EncoderParameters(1)
  $ps.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [int64]$q)
  $bmp.Save($path, $codec, $ps)
}

# --- cover-crop + resize real source images to 1200x675 ---
$jobs = @(
  @{ src = "D:\Dropbox\WORK FILES\BMB\SHOW FOLDERS\Alien Podcast\ShowCoverImage.jpg";      name = "alien-podcast" },
  @{ src = "D:\Dropbox\WORK FILES\BMB\SHOW FOLDERS\For The Record\FTR-CoverHorizontal.jpg"; name = "for-the-record" },
  @{ src = "D:\Dropbox\WORK FILES\BMB\SHOW FOLDERS\THUMBNAIL GENERATED\TT-MothersDay.png";  name = "talking-tipsy" }
)

foreach ($j in $jobs) {
  $img = [System.Drawing.Image]::FromFile($j.src)
  $bmp = New-Object System.Drawing.Bitmap($W, $H)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
  $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
  # cover fit
  $scale = [Math]::Max($W / $img.Width, $H / $img.Height)
  $dw = [int]($img.Width * $scale); $dh = [int]($img.Height * $scale)
  $dx = [int](($W - $dw) / 2); $dy = [int](($H - $dh) / 2)
  $g.DrawImage($img, $dx, $dy, $dw, $dh)
  $g.Dispose()
  Save-Jpeg $bmp "$out\$($j.name).jpg" 86
  $bmp.Dispose(); $img.Dispose()
  "built $($j.name).jpg"
}

# --- branded placeholder for Performance Battles (no source art exists) ---
$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

$rect = New-Object System.Drawing.Rectangle(0, 0, $W, $H)
$grad = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect,
  [System.Drawing.Color]::FromArgb(48, 26, 16),
  [System.Drawing.Color]::FromArgb(10, 7, 5), 150.0)
$g.FillRectangle($grad, $rect)

# red glow top-left
$gp = New-Object System.Drawing.Drawing2D.GraphicsPath
$gp.AddEllipse(-300, -420, 1300, 1100)
$pg = New-Object System.Drawing.Drawing2D.PathGradientBrush($gp)
$pg.CenterColor = [System.Drawing.Color]::FromArgb(70, 232, 24, 28)
$pg.SurroundColors = @([System.Drawing.Color]::FromArgb(0, 232, 24, 28))
$g.FillPath($pg, $gp)

$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = [System.Drawing.StringAlignment]::Center
$sf.LineAlignment = [System.Drawing.StringAlignment]::Center

# oversized VS watermark, sitting high and faint behind the lockup
$fBig = New-Object System.Drawing.Font("Arial Black", 190, [System.Drawing.FontStyle]::Bold)
$bVs = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(20, 255, 255, 255))
$g.DrawString("VS", $fBig, $bVs, (New-Object System.Drawing.RectangleF(0, 60, $W, 240)), $sf)

# title
$fTitle = New-Object System.Drawing.Font("Arial", 50, [System.Drawing.FontStyle]::Bold)
$bTitle = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(242, 239, 236))
$g.DrawString("PERFORMANCE BATTLES", $fTitle, $bTitle, (New-Object System.Drawing.RectangleF(0, 360, $W, 70)), $sf)

# red rule
$bRed = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(232, 24, 28))
$g.FillRectangle($bRed, [int](($W - 160) / 2), 440, 160, 5)

$fSub = New-Object System.Drawing.Font("Arial", 20, [System.Drawing.FontStyle]::Regular)
$bSub = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(140, 242, 239, 236))
$g.DrawString("BLACKMARKER.TV", $fSub, $bSub, (New-Object System.Drawing.RectangleF(0, 465, $W, 50)), $sf)

$g.Dispose()
Save-Jpeg $bmp "$out\performance-battles.jpg" 88
$bmp.Dispose()
"built performance-battles.jpg (placeholder)"

Get-ChildItem $out | Select-Object Name, Length | Format-Table -AutoSize
