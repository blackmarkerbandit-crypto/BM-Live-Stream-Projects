$ErrorActionPreference = "Stop"
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$SCRATCH = "C:\Users\imagi\AppData\Local\Temp\claude\d--Dropbox-WORK-FILES-BMB-AI-SHIT-BM-Live-Stream-Projects\bba4b6cc-109c-4e11-ab1d-221c18f2d1f9\scratchpad"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$OUT  = Join-Path $PREVIEW "BlackMarkerTV-3-CONTACT.html"

$bak = Join-Path $PREVIEW ("_backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Get-ChildItem $PREVIEW -Filter "*.html" | Copy-Item -Destination $bak
"backed up : $bak"

# base = a show page (proven shell: header, nav, subscribe modal, footer)
$base = [System.IO.File]::ReadAllText((Join-Path $PREVIEW "BlackMarkerTV-3-CAN-YOU-DIG-IT.html"), [System.Text.Encoding]::UTF8)
$body = [System.IO.File]::ReadAllText((Join-Path $SCRATCH "contact-body.html"), [System.Text.Encoding]::UTF8)
$css  = [System.IO.File]::ReadAllText((Join-Path $SCRATCH "contact.css"),      [System.Text.Encoding]::UTF8)

# ---- 1. swap the middle: everything from "<!-- SHOW HERO -->" up to the FOOTER marker
$startTag = "<!-- SHOW HERO -->"
$endTag   = "<!-- ============ FOOTER (no chat support) ============ -->"
$s = $base.IndexOf($startTag)
$e = $base.IndexOf($endTag)
if ($s -lt 0 -or $e -lt 0 -or $e -le $s) { throw "content boundaries not found in base page" }
$c = $base.Substring(0, $s) + $body + "`n`n" + $base.Substring($e)
"content spliced : replaced $($e - $s) chars with $($body.Length)"

# ---- 2. inject contact CSS just before </style>
$styleEnd = $c.LastIndexOf("</style>")
if ($styleEnd -lt 0) { throw "</style> not found" }
$c = $c.Substring(0, $styleEnd) + "`n" + $css + "`n" + $c.Substring($styleEnd)

# ---- 3. title
$c = [regex]::Replace($c, '<title>.*?</title>', '<title>Contact &mdash; BlackMarker.TV</title>')

# ---- 4. nav: clear the On Demand highlight, light up Contact
$sub = [regex]::Match($c, '(?s)<span class="submenu">.*?</span>\s*(?=</span>)').Value.TrimEnd()
$c = $c.Replace($sub, ($sub -replace '\s*class="on"', ''))
$c = $c.Replace('<a href="#" class="on">On Demand</a>', '<a href="#">On Demand</a>')
$c = $c.Replace('<a href="#">Contact</a>', '<a href="BlackMarkerTV-3-CONTACT.html" class="on">Contact</a>')

[System.IO.File]::WriteAllText($OUT, $c, $utf8)
"built     : BlackMarkerTV-3-CONTACT.html ($([Math]::Round((Get-Item $OUT).Length/1KB)) KB)"

# ---- 5. point every other page's Contact nav link at the new page
foreach ($f in Get-ChildItem $PREVIEW -Filter "BlackMarkerTV-3-*.html") {
  if ($f.Name -eq "BlackMarkerTV-3-CONTACT.html") { continue }
  $p = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $before = $p
  $p = $p.Replace('<a href="#">Contact</a>', '<a href="BlackMarkerTV-3-CONTACT.html">Contact</a>')
  # route the gold "Submit Your Music" bar + CTAs to the submission form
  $p = $p.Replace('href="mailto:canyoudigit@blackmarker.tv?subject=Music%20Submission%20for%20Review"',
                  'href="BlackMarkerTV-3-CONTACT.html#contact-form"')
  if ($p -ne $before) {
    [System.IO.File]::WriteAllText($f.FullName, $p, $utf8)
    "relinked  : $($f.Name)"
  }
}
