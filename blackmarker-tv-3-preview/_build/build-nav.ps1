# CANONICAL NAV BUILDER for the BlackMarker.TV 3.0 preview.
# Owns the entire <div class="nav-in"> block on every page, including which top-level
# item gets class="on". Run this after any script that adds/rebuilds a page.
$ErrorActionPreference = "Stop"
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$utf8 = New-Object System.Text.UTF8Encoding($false)

$bak = Join-Path $PREVIEW ("_backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Get-ChildItem $PREVIEW -Filter "*.html" | Copy-Item -Destination $bak
"backed up : $bak"

$HOME_PAGE = "BlackMarkerTV-3-LIVE-PREVIEW.html"

. (Join-Path $PSScriptRoot 'site-data.ps1')
$odGroups = @($NAV.exclusiveRecurring, $NAV.exclusiveArchive)
$evGroups = @(,$NAV.events)

function Get-Submenu($groups, [string]$current) {
  $out = @('      <span class="submenu">')
  for ($gi = 0; $gi -lt $groups.Count; $gi++) {
    if ($gi -gt 0) { $out += '        <span class="sep"></span>' }
    foreach ($r in $groups[$gi]) {
      $on = if ($r.f -eq $current) { ' class="on"' } else { '' }
      $out += ('        <a href="{0}"{1}>{2}</a>' -f $r.f, $on, $r.n)
    }
  }
  $out += '      </span>'
  return ($out -join "`n")
}

function Test-InGroups($groups, [string]$current) {
  foreach ($g in $groups) { foreach ($r in $g) { if ($r.f -eq $current) { return $true } } }
  return $false
}

# the Account button (with its inline svg) is lifted verbatim from an existing page
$sample = [System.IO.File]::ReadAllText((Join-Path $PREVIEW $HOME_PAGE), [System.Text.Encoding]::UTF8)
$acctSvg = [regex]::Match($sample, '<a href="[^"]*" class="acct">(.*?)Account</a>').Groups[1].Value
if (-not $acctSvg) { throw "account button svg not found" }

function Get-Nav([string]$current) {
  $onHome     = if ($current -eq $HOME_PAGE) { ' class="on"' } else { '' }
  $onDemand   = if (Test-InGroups $odGroups $current) { ' class="on"' } else { '' }
  $onEvents   = if (Test-InGroups $evGroups $current) { ' class="on"' } else { '' }
  $onBodega   = if ($current -eq "BlackMarkerTV-3-BODEGA.html")   { ' class="on"' } else { '' }
  $onSched    = if ($current -eq "BlackMarkerTV-3-SCHEDULE.html") { ' class="on"' } else { '' }
  $onContact  = if ($current -eq "BlackMarkerTV-3-CONTACT.html")  { ' class="on"' } else { '' }

  $lines = @()
  $lines += '  <div class="nav-in">'
  $lines += ('    <a href="{0}"{1}>Home</a>' -f $HOME_PAGE, $onHome)
  $lines += '    <span class="has-sub">'
  $lines += ('      <a href="#"{0}>Exclusive Shows</a>' -f $onDemand)
  $lines += (Get-Submenu $odGroups $current)
  $lines += '    </span>'
  $lines += '    <span class="has-sub">'
  $lines += ('      <a href="#"{0}>Event Streams</a>' -f $onEvents)
  $lines += (Get-Submenu $evGroups $current)
  $lines += '    </span>'
  $lines += ('    <a href="BlackMarkerTV-3-BODEGA.html"{0}>The Bodega</a>' -f $onBodega)
  $lines += ('    <a href="BlackMarkerTV-3-SCHEDULE.html"{0}>Schedule</a>' -f $onSched)
  $lines += ('    <a href="BlackMarkerTV-3-CONTACT.html"{0}>Contact</a>' -f $onContact)
  $onAcct = if ($current -eq 'BlackMarkerTV-3-ACCOUNT.html') { ' on' } else { '' }
  $lines += ('    <a href="BlackMarkerTV-3-ACCOUNT.html" class="acct{0}">{1}Account</a>' -f $onAcct, $acctSvg)
  $lines += '  </div>'
  return ($lines -join "`n")
}

foreach ($f in Get-ChildItem $PREVIEW -Filter "BlackMarkerTV-3-*.html") {
  $p = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $old = [regex]::Match($p, '(?s)<div class="nav-in">.*?</div>\s*</nav>').Value
  if (-not $old) { "NO NAV  : $($f.Name)"; continue }
  $new = (Get-Nav $f.Name) + "`n</nav>"
  if ($old -ne $new) {
    [System.IO.File]::WriteAllText($f.FullName, $p.Replace($old, $new), $utf8)
    "nav     : $($f.Name)"
  }
}
