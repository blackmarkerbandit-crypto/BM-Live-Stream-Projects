# Reverts the sticky right rail. Form goes back BELOW the content, spanning the full
# content width. Fields are laid out 3-across so "full width" reads as deliberate
# rather than as one stretched input per row.
$ErrorActionPreference = "Stop"
$B = "D:\Dropbox\WORK FILES\BMB\AI SHIT\blackmarker-tv-3-preview\_build"
$utf8 = New-Object System.Text.UTF8Encoding($false)

# ---------------------------------------------------------------- 1. CSS
$css = Join-Path $B "src\workwithus.css"
$c = [System.IO.File]::ReadAllText($css, [System.Text.Encoding]::UTF8)

# strip every trace of the two-column experiment
$c = [regex]::Replace($c, '(?s)\r?\n/\* two-column body.*?(?=\r?\n/\* between the stack point)', '')
$c = [regex]::Replace($c, '(?s)\r?\n/\* between the stack point.*?\r?\n\}\r?\n', "`n")
$c = $c.Replace('.wk-form{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:26px;max-width:820px;}',
                '.wk-form{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:26px;}')

if ($c -notmatch '\.wk-row3\{') {
  $c += @'

/* full-width form: three across on desktop so the card fills the page without
   leaving single inputs stretched across 1200px */
.wk-row3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.wk-form .wk-field:last-of-type{margin-bottom:16px;}
@media (max-width:900px){
  .wk-row3{grid-template-columns:repeat(2,1fr);}
}
@media (max-width:640px){
  .wk-row3{grid-template-columns:1fr;}
}
'@
  "css   : row3 added, layout rules stripped"
}
[System.IO.File]::WriteAllText($css, $c, $utf8)

# ------------------------------------------------------------- 2. page assembly
$p = Join-Path $B "build-workwithus.ps1"
$s = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)

$twoCol = @'
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
$oneCol = @'
  $body = $hero + "`n" + $content + "`n" + $form
'@
if ($s.Contains($twoCol)) { $s = $s.Replace($twoCol, $oneCol); "build : reverted to single column" }

# -------------------------------------------------- 3. 3-across field layout
$oldTop = @'
      <div class="wk-field">
        <label for="f-topic">$($p.topicLabel) <span class="req">*</span></label>
        <select id="f-topic" name="topic" required>
$opts
        </select>
      </div>

      <div class="wk-row">
        <div class="wk-field">
          <label for="f-name">Name <span class="req">*</span></label>
          <input type="text" id="f-name" name="name" placeholder="First and last" required>
        </div>
        <div class="wk-field">
          <label for="f-email">Email <span class="req">*</span></label>
          <input type="email" id="f-email" name="email" placeholder="you@domain.com" required>
        </div>
      </div>

      <div class="wk-row">
        <div class="wk-field">
          <label for="f-entity">Company / Artist / Organization</label>
          <input type="text" id="f-entity" name="entity" placeholder="How you want to be credited">
        </div>
        <div class="wk-field">
          <label for="f-phone">Phone</label>
          <input type="tel" id="f-phone" name="phone" placeholder="Optional">
        </div>
      </div>
'@
$newTop = @'
      <div class="wk-row3">
        <div class="wk-field">
          <label for="f-topic">$($p.topicLabel) <span class="req">*</span></label>
          <select id="f-topic" name="topic" required>
$opts
          </select>
        </div>
        <div class="wk-field">
          <label for="f-name">Name <span class="req">*</span></label>
          <input type="text" id="f-name" name="name" placeholder="First and last" required>
        </div>
        <div class="wk-field">
          <label for="f-email">Email <span class="req">*</span></label>
          <input type="email" id="f-email" name="email" placeholder="you@domain.com" required>
        </div>
      </div>

      <div class="wk-row3">
        <div class="wk-field">
          <label for="f-entity">Company / Artist / Organization</label>
          <input type="text" id="f-entity" name="entity" placeholder="How you want to be credited">
        </div>
        <div class="wk-field">
          <label for="f-phone">Phone</label>
          <input type="tel" id="f-phone" name="phone" placeholder="Optional">
        </div>
$budgetField
      </div>
'@
if ($s.Contains($oldTop)) { $s = $s.Replace($oldTop, $newTop); "build : top fields -> 3 across" }

# budget now lives inside the 3-across row, so drop its standalone block
$s = $s.Replace("`$eventFields`$budgetField`$mediaFields", "`$eventFields`$mediaFields")
$s = $s.Replace(@'
          <div class="wk-field">
            <label for="f-budget">Budget <span class="req">*</span></label>
'@, @'
        <div class="wk-field">
          <label for="f-budget">Budget <span class="req">*</span></label>
'@)

[System.IO.File]::WriteAllText($p, $s, $utf8)
"done"
