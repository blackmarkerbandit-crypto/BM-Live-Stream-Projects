Add-Type -AssemblyName System.Drawing
$out = "C:\Users\imagi\AppData\Local\Temp\claude\d--Dropbox-WORK-FILES-BMB-AI-SHIT-BM-Live-Stream-Projects\bba4b6cc-109c-4e11-ab1d-221c18f2d1f9\scratchpad\sched-art\SpecialInterrupts-placeholder.jpg"
$W = 1200; $H = 675

$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

# dark ground
$rect = New-Object System.Drawing.Rectangle(0, 0, $W, $H)
$grad = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect,
  [System.Drawing.Color]::FromArgb(38, 20, 14),
  [System.Drawing.Color]::FromArgb(10, 7, 5), 155.0)
$g.FillRectangle($grad, $rect)

# red glow, upper-left (matches the other branded placeholder)
$gp = New-Object System.Drawing.Drawing2D.GraphicsPath
$gp.AddEllipse(-320, -430, 1350, 1120)
$pg = New-Object System.Drawing.Drawing2D.PathGradientBrush($gp)
$pg.CenterColor = [System.Drawing.Color]::FromArgb(66, 232, 24, 28)
$pg.SurroundColors = @([System.Drawing.Color]::FromArgb(0, 232, 24, 28))
$g.FillPath($pg, $gp)

# faint scanlines -- broadcast texture
$scan = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(10, 255, 255, 255))
for ($y = 0; $y -lt $H; $y += 4) { $g.FillRectangle($scan, 0, $y, $W, 1) }

# offset "signal break" bars through the middle -- the interruption motif
$bars = @(
  @{ y=250; x=170; w=380; a=26 }, @{ y=250; x=610; w=250; a=16 }
  @{ y=286; x=250; w=520; a=34 }
  @{ y=402; x=330; w=300; a=22 }, @{ y=402; x=680; w=190; a=14 }
  @{ y=436; x=210; w=420; a=18 }
)
foreach ($b in $bars) {
  $br = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb($b.a, 255, 255, 255))
  $g.FillRectangle($br, [int]$b.x, [int]$b.y, [int]$b.w, 14)
}
# one red break bar for accent
$brRed = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(120, 232, 24, 28))
$g.FillRectangle($brRed, 700, 286, 210, 14)

$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = [System.Drawing.StringAlignment]::Center
$sf.LineAlignment = [System.Drawing.StringAlignment]::Center

# title
$fTitle = New-Object System.Drawing.Font("Arial", 54, [System.Drawing.FontStyle]::Bold)
$bTitle = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(242, 239, 236))
$g.DrawString("SPECIAL INTERRUPTS", $fTitle, $bTitle, (New-Object System.Drawing.RectangleF(0, 306, $W, 80)), $sf)

# red rule
$bRed = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(232, 24, 28))
$g.FillRectangle($bRed, [int](($W - 160) / 2), 388, 160, 5)

$fSub = New-Object System.Drawing.Font("Arial", 20, [System.Drawing.FontStyle]::Regular)
$bSub = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(140, 242, 239, 236))
$g.DrawString("BLACKMARKER.TV", $fSub, $bSub, (New-Object System.Drawing.RectangleF(0, 500, $W, 50)), $sf)

$g.Dispose()
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ps = New-Object System.Drawing.Imaging.EncoderParameters(1)
$ps.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [int64]88)
$bmp.Save($out, $codec, $ps)
$bmp.Dispose()
"built: $out ($([Math]::Round((Get-Item $out).Length/1KB)) KB)"
