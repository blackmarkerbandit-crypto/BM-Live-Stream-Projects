$ErrorActionPreference = "Stop"
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$SCR = $PSScriptRoot
$utf8 = New-Object System.Text.UTF8Encoding($false)
$OUT = Join-Path $PREVIEW "BlackMarkerTV-3-ACCOUNT.html"

$bak = Join-Path $PREVIEW ("_backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Get-ChildItem $PREVIEW -Filter "*.html" | Copy-Item -Destination $bak
"backed up : $bak"

$base = [System.IO.File]::ReadAllText((Join-Path $PREVIEW "BlackMarkerTV-3-CAN-YOU-DIG-IT.html"), [System.Text.Encoding]::UTF8)
$body = [System.IO.File]::ReadAllText((Join-Path $SCR "account-body.html"), [System.Text.Encoding]::UTF8)
$css  = [System.IO.File]::ReadAllText((Join-Path $SCR "account.css"),      [System.Text.Encoding]::UTF8)

$s = $base.IndexOf("<!-- SHOW HERO -->")
$e = $base.IndexOf("<!-- ============ FOOTER (no chat support) ============ -->")
if ($s -lt 0 -or $e -le $s) { throw "content boundaries not found" }
$c = $base.Substring(0, $s) + $body + "`n`n" + $base.Substring($e)

$i = $c.LastIndexOf("</style>")
$c = $c.Substring(0, $i) + "`n" + $css + "`n" + $c.Substring($i)
$c = [regex]::Replace($c, '<title>.*?</title>', '<title>Account &mdash; BlackMarker.TV</title>')

[System.IO.File]::WriteAllText($OUT, $c, $utf8)
"built     : BlackMarkerTV-3-ACCOUNT.html ($([Math]::Round((Get-Item $OUT).Length/1KB)) KB)"

& (Join-Path $SCR 'build-nav.ps1')