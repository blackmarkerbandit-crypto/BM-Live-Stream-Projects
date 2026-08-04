# ============================================================================
# SINGLE SOURCE OF TRUTH for the BlackMarker.TV 3.0 preview site.
# Dot-sourced by build-nav.ps1 and build-show-pages.ps1.
#
# TO ADD A NEW SHOW:
#   1. add it to the right $NAV group below (controls the dropdowns)
#   2. if we generate its page, add a matching entry to $GENERATED
#   3. run build-show-pages.ps1  (it calls build-nav.ps1 at the end)
# ============================================================================

# ---------------------------------------------------------------- navigation
# "Exclusive Shows" dropdown = recurring block, then a .sep rule, then archive block.
# "Event Streams"   dropdown = one-off / event programming.
# ORDER IS EDITORIAL PRIORITY, set by Eric 2026-08-04. Everything downstream
# (dropdowns, homepage Latest Videos, schedule cards) follows this same ranking:
#   1 Can You Dig It!?  2 The Weekly Interrupt  3 For The Record
#   4 The Alien Podcast 5 Talking Tipsy  6 Special Interrupts  7 Performance Battles
# Archive shows are unranked and sit below the divider.
$NAV = [ordered]@{
  exclusiveRecurring = @(
    @{ f="BlackMarkerTV-3-CAN-YOU-DIG-IT.html";   n="Can You Dig It!? Live Music Review" }  # 1
    @{ f="BlackMarkerTV-3-WEEKLY-INTERRUPT.html"; n="The Weekly Interrupt" }                # 2
    @{ f="BlackMarkerTV-3-FOR-THE-RECORD.html";   n="For The Record" }                      # 3
    @{ f="BlackMarkerTV-3-ALIEN-PODCAST.html";    n="The Alien Podcast" }                   # 4
    @{ f="BlackMarkerTV-3-TALKING-TIPSY.html";    n="Talking Tipsy" }                       # 5
  )
  exclusiveArchive = @(
    @{ f="BlackMarkerTV-3-2-BAFOONZ.html";   n="2 Bafoonz, 1 Lagoon" }
    @{ f="BlackMarkerTV-3-DUH-DIGGITY.html"; n="Duh Diggity Show" }
  )
  events = @(
    @{ f="BlackMarkerTV-3-SPECIAL-INTERRUPTS.html";  n="Special Interrupts" }   # 6
    @{ f="BlackMarkerTV-3-PERFORMANCE-BATTLES.html"; n="Performance Battles" }  # 7
  )
}

# ------------------------------------------------------------ generated pages
# Only pages this toolchain builds. The original show pages (Weekly Interrupt,
# CUDI, Talking Tipsy, Alien Podcast, For The Record, Performance Battles) are
# hand-built and Eric has tweaked them -- do NOT add them here, they'd be overwritten.
#
#   art       = filename in scratchpad\sched-art\  (see README note: live CDN is
#               https://files.stablerack.com/webfiles/91215/<file>)
#   cat       = ChannelCast VOD category name, VERBATIM -- the OTT filter is name-based
#   s1n/s1l   = first stat tile; count comes from the live MRSS feed, re-check on rebuild
$GENERATED = @(
  @{
    file="BlackMarkerTV-3-2-BAFOONZ.html"; title="2 Bafoonz, 1 Lagoon"
    cat="2 Bafoonz, 1 Lagoon"; art="VODCategoryLandscape49.jpg"; slug="bafoonz"
    crumb="Exclusive Shows"; kicker="Exclusive Shows &middot; Archive"
    desc='Two dudes, one lagoon, zero filter. One of the first shows on the network &mdash; <b>Dirk</b> and ' +
         '<b>Shawn</b> ran trivia, cracked jokes, lived it up and served straight lagoon life comedy once a ' +
         'month. The whole run is archived right here, on demand whenever you want it.'
    s1n="5"; s1l="Episodes"; s2n="Archive"; s2l="On Demand Only"; s3n="No"; s3l="Live Broadcasts"
  }
  @{
    file="BlackMarkerTV-3-DUH-DIGGITY.html"; title="Duh Diggity Show"
    cat="Duh Diggity Show"; art="VODCategoryLandscape48.jpg"; slug="diggity"
    crumb="Exclusive Shows"; kicker="Exclusive Shows &middot; Archive"
    desc='Where it all started. Two pilot episodes shot while the network was young &mdash; ' +
         '<b>Los Diggity</b> on the mic, building the antics on camera. ' +
         'Both pilots live here as an exclusive on-demand archive.'
    s1n="2"; s1l="Pilot Episodes"; s2n="Archive"; s2l="On Demand Only"; s3n="No"; s3l="Live Broadcasts"
  }
  @{
    file="BlackMarkerTV-3-SPECIAL-INTERRUPTS.html"; title="Special Interrupts"
    cat="Special Interrupts"; art="SpecialInterrupts-placeholder.jpg"; slug="interrupts"
    crumb="Event Streams"; kicker="Event Streams &middot; One-Off Specials"
    desc='When something&rsquo;s worth breaking the schedule for, we interrupt it. Listening sessions, ' +
         'documentary screenings, road trips and whatever else the network rolls out on short notice &mdash; ' +
         'one-off broadcasts that don&rsquo;t belong to any one show, kept here after they air.'
    s1n="4"; s1l="Specials"; s2n="One-Off"; s2l="Event Streams"; s3n="No"; s3l="Fixed Schedule"
  }
)
