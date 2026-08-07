# Builds the four "Work With Us" footer pages, each with a lead form.
# Field names deliberately match the Contact page so the CMS form tool maps one set.
$ErrorActionPreference = "Stop"
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$SCR = $PSScriptRoot
$SRC = Join-Path $PSScriptRoot "src"   # page bodies + css live here in the repo layout
$utf8 = New-Object System.Text.UTF8Encoding($false)

$bak = Join-Path $PREVIEW ("_backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Get-ChildItem $PREVIEW -Filter "*.html" | Copy-Item -Destination $bak
"backed up : $bak"

# ---------------------------------------------------------------- page table
$PAGES = @(
  @{ file="BlackMarkerTV-3-PARTNERSHIPS.html"; body="wk-partnerships.html"
     title="Partnership Opportunities"; kicker="Work With Us &middot; Partnerships"
     desc="Content partners, event sponsors, production partners and investors. Black Marker Media builds streaming infrastructure, produces live events, and operates its own broadcast network &mdash; <b>BlackMarker.TV</b>. If any one of those overlaps what you&rsquo;re building, there&rsquo;s a conversation here."
     formH="Start the conversation"; topicLabel="What kind of partnership?"
     topics=@("Content partnership &mdash; a show or catalogue","Event sponsorship","Production partnership","Investment enquiry","Something else")
     budget=$false; media=$false; event=$false }

  @{ file="BlackMarkerTV-3-ADVERTISING.html"; body="wk-advertising.html"
     title="Advertising &amp; Promotions"; kicker="Work With Us &middot; Advertising"
     desc="Run on the 24/7 Free Loop, sponsor a show, put your name on a live event broadcast, or promote your own event to our audience. Rates below, held for twelve months from signing."
     formH="Book a spot"; topicLabel="What are you interested in?"
     topics=@("Free Loop rotation spot","Show sponsorship","Live event broadcast sponsor","Event promotion package","Network Partner (everything)","Not sure &mdash; talk it through")
     budget=$true; media=$false; event=$false }

  @{ file="BlackMarkerTV-3-PRODUCTION.html"; body="wk-production.html"
     title="Streaming Production Services"; kicker="Black Marker Media &middot; Production"
     desc="Multi-camera live production for battles, sporting events, festivals, parades and conferences &mdash; bundled with promotion on <b>BlackMarker.TV</b> so your event doesn&rsquo;t disappear the moment the stream ends."
     formH="Tell us about the event"; topicLabel="What are we producing?"
     topics=@("Rap battle / league card","Sporting event","Festival or concert","Parade or street event","Conference or panel","Studio production","Something else")
     budget=$true; media=$false; event=$true }

  @{ file="BlackMarkerTV-3-SUBMIT-MUSIC.html"; body="wk-submit.html"
     title="Submit Your Music"; kicker="Artists &middot; Managers &middot; Labels"
     desc="For consideration on the <b>Free Loop</b>, our live broadcasts, or the <b>Live Music Review</b> on Can You Dig It!?. Submitting is free. Video gets you further than audio &mdash; a plain YouTube link is perfectly fine."
     formH="Send it over"; topicLabel="Where do you want it?"
     topics=@("Free Loop rotation","Played on a live broadcast","Live Music Review &mdash; Can You Dig It!?","Wherever it fits")
     budget=$false; media=$true; event=$false }
)

function Esc([string]$s){ return $s }

foreach ($p in $PAGES) {
  # ------------------------------------------------ form fields (per page)
  $opts = ($p.topics | ForEach-Object { "              <option>$_</option>" }) -join "`n"

  $budgetField = ""
  if ($p.budget) {
    $budgetField = @"
        <div class="wk-field">
          <label for="f-budget">Budget <span class="req">*</span></label>
            <select id="f-budget" name="budget" required>
              <option value="">Select a range&hellip;</option>
              <option>Under &#36;500</option>
              <option>&#36;500 &ndash; &#36;1,500</option>
              <option>&#36;1,500 &ndash; &#36;3,500</option>
              <option>&#36;3,500 &ndash; &#36;7,500</option>
              <option>&#36;7,500 &ndash; &#36;15,000</option>
              <option>&#36;15,000+</option>
              <option>Not sure yet &mdash; advise me</option>
            </select>
            <div class="wk-help">A range is enough. It tells us straight away whether we can do this well at that number.</div>
          </div>
"@
  }

  $eventFields = ""
  if ($p.event) {
    $eventFields = @"
          <div class="wk-row">
            <div class="wk-field">
              <label for="f-date">Event date</label>
              <input type="date" id="f-date" name="event_date">
            </div>
            <div class="wk-field">
              <label for="f-venue">Venue / location</label>
              <input type="text" id="f-venue" name="event_location" placeholder="City, state &mdash; venue if booked">
            </div>
          </div>
"@
  }

  $mediaFields = ""
  if ($p.media) {
    $mediaFields = @"
          <div class="wk-field">
            <label for="f-video">Video Link <span class="req">*</span></label>
            <input type="url" id="f-video" name="video_url" placeholder="https://youtube.com/watch?v=..." required>
            <div class="wk-help">YouTube, Vimeo, or any public link that plays without a login or download.</div>
          </div>
          <div class="wk-row">
            <div class="wk-field">
              <label for="f-audio">Audio / streaming link</label>
              <input type="url" id="f-audio" name="audio_url" placeholder="Spotify, Apple Music, SoundCloud&hellip;">
            </div>
            <div class="wk-field">
              <label for="f-work">Track / project title</label>
              <input type="text" id="f-work" name="work_title" placeholder="What are we listening to?">
            </div>
          </div>
          <label class="wk-check" for="f-rights">
            <input type="checkbox" id="f-rights" name="rights_ok" required>
            <span>I own or control the rights to this material and give Black Marker TV permission to play, review and
            broadcast it on air and across its channels. <span class="req">*</span></span>
          </label>
"@
  }

  $form = @"
<section class="section wrap" id="lead-form">
  <div class="ann" data-ann="CMS FORM &mdash; replace with form-tool markup">
    <!-- ================= BEGIN CMS FORM =================
         Field names match the Contact page so one mapping covers every form:
           topic, name, email, phone, entity, message, consent
         Page-specific:
           budget        select    required on Advertising + Production
           event_date    date      Production only
           event_location text     Production only
           video_url     url       required on Submit Your Music
           audio_url     url
           work_title    text
           rights_ok     checkbox  required on Submit Your Music
         ================================================== -->
    <form class="wk-form" novalidate>
      <div class="wk-form-head">
        <h2 class="sec-title">$($p.formH)</h2>
        <p class="wk-form-sub">Fields marked <span class="req">*</span> are required.</p>
      </div>

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
$eventFields$mediaFields
      <div class="wk-field">
        <label for="f-message">Message <span class="req">*</span></label>
        <textarea id="f-message" name="message" rows="6" placeholder="Tell us what you&rsquo;re working with." required></textarea>
      </div>

      <label class="wk-check" for="f-consent">
        <input type="checkbox" id="f-consent" name="consent">
        <span>Keep me posted on show drops, events and network news.</span>
      </label>

      <div class="wk-submit-row">
        <button type="submit" class="btn btn-red">Send It</button>
        <span class="wk-submit-note">Inquiries answered within 1&ndash;2 business days.</span>
      </div>
    </form>
    <!-- ================== END CMS FORM ================== -->
    <span class="ann-note">Replaced by the CMS form tool. Keep the field names above &mdash; they match the Contact page,
    so one field mapping covers all five forms on the site.</span>
  </div>
</section>
"@

  # ------------------------------------------------ assemble the page
  $hero = @"
<!-- WORK WITH US HERO -->
<section class="wk-hero">
  <div class="wrap">
    <div class="wk-crumb"><a href="BlackMarkerTV-3-LIVE-PREVIEW.html">Home</a> <span class="sep">/</span> <span>$($p.title)</span></div>
    <div class="wk-kicker">$($p.kicker)</div>
    <h1 class="wk-title">$($p.title)</h1>
    <p class="wk-desc">$($p.desc)</p>
  </div>
</section>
"@

  $content = [System.IO.File]::ReadAllText((Join-Path $SRC $p.body), [System.Text.Encoding]::UTF8)

  $body = $hero + "`n" + $content + "`n" + $form

  $base = [System.IO.File]::ReadAllText((Join-Path $PREVIEW "BlackMarkerTV-3-CAN-YOU-DIG-IT.html"), [System.Text.Encoding]::UTF8)
  $s = $base.IndexOf("<!-- SHOW HERO -->")
  $e = $base.IndexOf("<!-- ============ FOOTER (no chat support) ============ -->")
  if ($s -lt 0 -or $e -le $s) { throw "content boundaries not found" }
  $c = $base.Substring(0, $s) + $body + "`n`n" + $base.Substring($e)

  $css = [System.IO.File]::ReadAllText((Join-Path $SRC "workwithus.css"), [System.Text.Encoding]::UTF8)
  $i = $c.LastIndexOf("</style>")
  $c = $c.Substring(0, $i) + "`n" + $css + "`n" + $c.Substring($i)

  $plain = ($p.title -replace '&amp;','and')
  $c = [regex]::Replace($c, '<title>.*?</title>', "<title>$plain &mdash; BlackMarker.TV</title>")

  $out = Join-Path $PREVIEW $p.file
  [System.IO.File]::WriteAllText($out, $c, $utf8)
  "built     : $($p.file) ($([Math]::Round((Get-Item $out).Length/1KB)) KB)"
}

# ------------------------------------------------ wire the footer links site-wide
$map = @{
  "Partnership Opportunities"    = "BlackMarkerTV-3-PARTNERSHIPS.html"
  "Advertising &amp; Promotions" = "BlackMarkerTV-3-ADVERTISING.html"
  "Streaming Production Services"= "BlackMarkerTV-3-PRODUCTION.html"
  "Submit Your Music"            = "BlackMarkerTV-3-SUBMIT-MUSIC.html"
}
foreach ($f in Get-ChildItem $PREVIEW -Filter "BlackMarkerTV-3-*.html") {
  $t = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8); $b = $t
  foreach ($k in $map.Keys) {
    $t = [regex]::Replace($t, '<a href="[^"]*">' + [regex]::Escape($k) + '</a>', '<a href="' + $map[$k] + '">' + $k + '</a>')
  }
  if ($t -ne $b) { [System.IO.File]::WriteAllText($f.FullName, $t, $utf8); "footer    : $($f.Name)" }
}

& (Join-Path $SCR 'build-nav.ps1')
