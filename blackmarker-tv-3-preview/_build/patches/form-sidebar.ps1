# Moves the lead form on the four Work With Us pages from a full-width block at the
# bottom into a STICKY RIGHT RAIL beside the content.
# Two wins: kills ~900px of page height, and the form is visible from the first screen
# instead of only after someone scrolls the whole page.
$ErrorActionPreference = "Stop"
$B = "D:\Dropbox\WORK FILES\BMB\AI SHIT\blackmarker-tv-3-preview\_build"
$utf8 = New-Object System.Text.UTF8Encoding($false)

# ---------------------------------------------------------------- 1. layout CSS
$css = Join-Path $B "src\workwithus.css"
$c = [System.IO.File]::ReadAllText($css, [System.Text.Encoding]::UTF8)
if ($c -notmatch '\.wk-layout\{') {
  $add = @'

/* two-column body: content left, sticky form right */
.wk-layout{display:grid;grid-template-columns:minmax(0,1fr) 390px;gap:32px;align-items:start;
  padding-top:8px;padding-bottom:40px;}
.wk-main{min-width:0;}
.wk-main .section{padding:30px 0 0;}
.wk-side{position:sticky;top:66px;}          /* clears the sticky nav */
.wk-side .wk-form{max-width:none;padding:22px;}
.wk-side .wk-form-head{margin-bottom:18px;padding-bottom:14px;}
.wk-side .wk-field{margin-bottom:13px;}
.wk-side .wk-row{grid-template-columns:1fr;gap:0;}   /* single column in a narrow rail */
.wk-side .wk-form textarea{min-height:88px;}
/* if a form ever outgrows the viewport, let the rail scroll on its own
   rather than trapping the page */
.wk-side{max-height:calc(100vh - 84px);overflow-y:auto;scrollbar-width:thin;}
.wk-side::-webkit-scrollbar{width:8px;}
.wk-side::-webkit-scrollbar-thumb{background:var(--border2);border-radius:4px;}

@media (max-width:1150px){
  .wk-layout{grid-template-columns:1fr;gap:0;}
  .wk-side{position:static;max-height:none;overflow:visible;margin-top:28px;}
  .wk-side .wk-row{grid-template-columns:1fr 1fr;gap:14px;}
  .wk-side .wk-form{padding:26px;}
}
'@
  [System.IO.File]::WriteAllText($css, $c + $add, $utf8)
  "css   : layout rules added"
} else { "css   : already present" }

# ------------------------------------------------------------- 2. page assembly
$p = Join-Path $B "build-workwithus.ps1"
$s = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
if ($s -match 'wk-layout') { "build : already restructured"; exit }

$old = @'
  $content = [System.IO.File]::ReadAllText((Join-Path $SRC $p.body), [System.Text.Encoding]::UTF8)
  $body = $hero + "`n" + $content + "`n" + $form
'@

$new = @'
  $content = [System.IO.File]::ReadAllText((Join-Path $SRC $p.body), [System.Text.Encoding]::UTF8)

  # content sections sit inside the left column, so they lose their own .wrap
  $contentCols = $content -replace 'class="section wrap"', 'class="section"'
  # the form loses its outer <section> and becomes the right rail
  $formInner = $form -replace '(?s)^\s*<section class="section wrap" id="lead-form">\s*', ''
  $formInner = $formInner -replace '(?s)</section>\s*$', ''

  $body = $hero + "`n" +
          '<div class="wrap wk-layout">' + "`n" +
          '  <div class="wk-main">' + "`n" + $contentCols + "`n" + '  </div>' + "`n" +
          '  <aside class="wk-side" id="lead-form">' + "`n" + $formInner + "`n" + '  </aside>' + "`n" +
          '</div>'
'@

if (-not $s.Contains($old)) { throw "assembly block not found - it may have changed shape" }
$s = $s.Replace($old, $new)
[System.IO.File]::WriteAllText($p, $s, $utf8)
"build : page assembly restructured"
