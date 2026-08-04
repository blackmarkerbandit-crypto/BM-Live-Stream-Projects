# Builds The Bodega page (rotating ad banner + [STORE] placeholder), then rebuilds nav.
$ErrorActionPreference = "Stop"
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$SCR = "C:\Users\imagi\AppData\Local\Temp\claude\d--Dropbox-WORK-FILES-BMB-AI-SHIT-BM-Live-Stream-Projects\bba4b6cc-109c-4e11-ab1d-221c18f2d1f9\scratchpad"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$OUT = Join-Path $PREVIEW "BlackMarkerTV-3-BODEGA.html"

$bak = Join-Path $PREVIEW ("_backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Get-ChildItem $PREVIEW -Filter "*.html" | Copy-Item -Destination $bak
"backed up : $bak"

$base = [System.IO.File]::ReadAllText((Join-Path $PREVIEW "BlackMarkerTV-3-CAN-YOU-DIG-IT.html"), [System.Text.Encoding]::UTF8)
$body = [System.IO.File]::ReadAllText((Join-Path $SCR "bodega-body.html"), [System.Text.Encoding]::UTF8)
$css  = [System.IO.File]::ReadAllText((Join-Path $SCR "bodega.css"),      [System.Text.Encoding]::UTF8)

# swap the middle: everything from the show hero up to the footer marker
$startTag = "<!-- SHOW HERO -->"
$endTag   = "<!-- ============ FOOTER (no chat support) ============ -->"
$s = $base.IndexOf($startTag); $e = $base.IndexOf($endTag)
if ($s -lt 0 -or $e -le $s) { throw "content boundaries not found in base page" }
$c = $base.Substring(0, $s) + $body + "`n`n" + $base.Substring($e)
"spliced   : replaced $($e - $s) chars with $($body.Length)"

$i = $c.LastIndexOf("</style>")
if ($i -lt 0) { throw "</style> not found" }
$c = $c.Substring(0, $i) + "`n" + $css + "`n" + $c.Substring($i)

$c = [regex]::Replace($c, '<title>.*?</title>', '<title>The Bodega &mdash; BlackMarker.TV</title>')

[System.IO.File]::WriteAllText($OUT, $c, $utf8)
"built     : BlackMarkerTV-3-BODEGA.html ($([Math]::Round((Get-Item $OUT).Length/1KB)) KB)"

& (Join-Path $SCR 'build-nav.ps1')
