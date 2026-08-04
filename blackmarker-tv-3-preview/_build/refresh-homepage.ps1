# Refreshes the homepage "Latest Videos" + "Trending in Music" cards with live
# ChannelCast data and REAL thumbnails (posterUrl / media:thumbnail).
#
# Thumbnails are referenced as live https URLs, not base64: they stay current on
# their own, keep the file small, and are the same URLs the real site will use.
$ErrorActionPreference = "Stop"
$PREVIEW = "C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview"
$SCR = "C:\Users\imagi\AppData\Local\Temp\claude\d--Dropbox-WORK-FILES-BMB-AI-SHIT-BM-Live-Stream-Projects\bba4b6cc-109c-4e11-ab1d-221c18f2d1f9\scratchpad"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$HOMEPG = Join-Path $PREVIEW "BlackMarkerTV-3-LIVE-PREVIEW.html"

$bak = Join-Path $PREVIEW ("_backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Get-ChildItem $PREVIEW -Filter "*.html" | Copy-Item -Destination $bak
"backed up : $bak"

# ---------- pull a fresh feed so durations/thumbs are current
$src = [System.IO.File]::ReadAllText((Join-Path $PREVIEW "BlackMarkerTV-3-TALKING-TIPSY.html"), [System.Text.Encoding]::UTF8)
$feedUrl = [regex]::Match($src, 'feedUrl:\s*"([^"]+)"').Groups[1].Value
Invoke-WebRequest -Uri $feedUrl -OutFile "$SCR\feed-live.xml" -UseBasicParsing -TimeoutSec 60
[xml]$x = Get-Content "$SCR\feed-live.xml" -Raw -Encoding UTF8
$ns = New-Object System.Xml.XmlNamespaceManager($x.NameTable); $ns.AddNamespace("m","http://search.yahoo.com/mrss/")
$byGuid = @{}
foreach ($it in $x.rss.channel.item) {
  $byGuid[$it.guid] = [pscustomobject]@{
    title = $it.title
    thumb = $it.SelectSingleNode("m:thumbnail",$ns).GetAttribute("url")
    dur   = [int]$it.SelectSingleNode("m:content",$ns).GetAttribute("duration")
    link  = $it.link
  }
}
"feed      : $($byGuid.Count) items"

function Fmt([int]$s) {
  # [Math]::Floor, NOT [int] -- an [int] cast ROUNDS in PowerShell ([int](226/60) = 4)
  if ($s -ge 3600) { return "{0}:{1:00}:{2:00}" -f [Math]::Floor($s/3600), [Math]::Floor(($s%3600)/60), ($s%60) }
  return "{0}:{1:00}" -f [Math]::Floor($s/60), ($s%60)
}
function Esc([string]$t) { return ($t -replace '&','&amp;' -replace '<','&lt;' -replace '>','&gt;' -replace '"','&quot;') }

# ---------- LATEST VIDEOS: newest item per category.
# "Newest" = the category's LOWEST sort index (curated order in ChannelCast).
# pubDate can't be used -- the feed still stamps most items with the bulk-import
# time, and feed order is alphabetical (see CC-29 on the punchlist).
# Card order = Eric's editorial priority (2026-08-04). Performance Battles (7) was
# dropped from the homepage and now lives only in the Event Streams dropdown;
# Special Interrupts (6) takes its slot.
$latest = @(
  @{ tag="Can You Dig It!?"; guid="019fbbd1ba26723e801ebb5aaab8dcf4"
     title="De La Klutch x Current Live Music Landscape"; meta="Newest episode &middot; Jul 31" }
  @{ tag="The Weekly Interrupt"; guid="019f2680f519757fb68238c7d337c8a4"
     title="Ep 169 &mdash; PR Parade Weekend Countdown x MJ Movie x Gov Spyware"; meta="Newest episode &middot; May 19" }
  @{ tag="For The Record"; guid="019f26806f757dd88d59af7865f96fe5"
     title="Ep 010 &mdash; A Tribe Called Quest: Midnight Marauders"; meta="Newest episode &middot; Jun 29" }
  @{ tag="The Alien Podcast"; guid="019f2680ed4172278047f248f1bad62f"
     title="New Government Alien Files Release x Personal Encounter"; meta="Newest episode &middot; May 17" }
  @{ tag="Talking Tipsy"; guid="019f2680ec0f7a68a601402d4b88e3c6"
     title="Ep 011 &mdash; Mother&rsquo;s Day Special Edition"; meta="Newest episode &middot; May 9" }
  @{ tag="Special Interrupts"; guid="019fbbd1bdac7b70a80b15b18e2495c6"
     title="ReeBaby LIVE Listening Session"; meta="Newest special &middot; Jul 24" }
)

# ---------- TRENDING IN MUSIC: real library music videos (posterUrl from list_media)
$POSTER = "https://channelcast.tv/uploads/019eb9feacc37d939dbb4677a5b9ef9f/media-thumb/"
$trending = @(
  @{ title="Method Man ft. Carlton Fisk x Chunk Bizza &mdash; King of New York"; sec=149; img="019f26d4a8dd7ccd8452c18dae122072.jpg" }
  @{ title="Cambatta &mdash; The Shaman";                                        sec=198; img="019f26c7c6a277e49aacef8b41ec2f03.jpg" }
  @{ title="GATS &mdash; Stuntman";                                              sec=226; img="019f26e9b8897c4c9bf9517bff5fb97b.jpg" }
  # single-quoted: in a double-quoted PS string "$$" is the automatic variable and vanishes
  @{ title='Joey Bada$$ ft. Ab-Soul x Rapsody &mdash; Still';                    sec=206; img="019f26b58b8c7acfa1bd610884686783.jpg" }
  @{ title="Doechii &mdash; Anxiety";                                            sec=252; img="019f26aee9097ab49a431fe59321bde0.jpg" }
  @{ title="Snow Tha Product &mdash; Jump";                                      sec=153; img="019f26b481ce77a89092f24fb271077f.jpg" }
)

# ---------- build card markup
$latestCards = foreach ($l in $latest) {
  $f = $byGuid[$l.guid]
  if (-not $f) { throw "guid $($l.guid) ($($l.tag)) not in feed" }
  '        <div class="card full"><div class="thumb"><span class="cat-tag">{0}</span><img class="thumb-img" src="{1}" alt="{2}" loading="lazy"><span class="dur">{3}</span></div><div class="c-title">{4}</div><div class="c-meta">{5}</div></div>' -f `
    $l.tag, $f.thumb, (Esc $f.title), (Fmt $f.dur), $l.title, $l.meta
}
$trendCards = foreach ($t in $trending) {
  '    <div class="card"><div class="thumb"><img class="thumb-img" src="{0}{1}" alt="" loading="lazy"><span class="dur">{2}</span></div><div class="c-title">{3}</div><div class="c-meta">Music Video</div></div>' -f `
    $POSTER, $t.img, (Fmt $t.sec), $t.title
}

# ---------- splice
$c = [System.IO.File]::ReadAllText($HOMEPG, [System.Text.Encoding]::UTF8)

$oldLatest = [regex]::Match($c, '(?s)<div class="grid-cat">.*?</div>\s*\r?\n\s*<span class="ann-note">').Value
if (-not $oldLatest) { throw "grid-cat block not found" }
$newLatest = "<div class=`"grid-cat`">`n" + ($latestCards -join "`n") + "`n      </div>`n      <span class=`"ann-note`">"
$c = $c.Replace($oldLatest, $newLatest)

$oldTrend = [regex]::Match($c, '(?s)<div class="rail">.*?</div>\s*\r?\n\s*</div>\s*\r?\n</section>').Value
if (-not $oldTrend) { throw "rail block not found" }
$newTrend = "<div class=`"rail`">`n" + ($trendCards -join "`n") + "`n  </div>`n  </div>`n</section>"
$c = $c.Replace($oldTrend, $newTrend)

# ---------- thumbnail image styling (sits under the gradient + play button)
if ($c -notmatch '\.thumb-img\{') {
  $css = ".thumb .thumb-img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;}`n"
  $i = $c.IndexOf('.thumb .ph-ico{')
  if ($i -lt 0) { throw "ph-ico rule not found" }
  $c = $c.Substring(0, $i) + $css + $c.Substring($i)
}

[System.IO.File]::WriteAllText($HOMEPG, $c, $utf8)
"latest    : $($latestCards.Count) cards"
"trending  : $($trendCards.Count) cards"
"written   : BlackMarkerTV-3-LIVE-PREVIEW.html ($([Math]::Round((Get-Item $HOMEPG).Length/1KB)) KB)"
