# ChannelCast.TV — Launch Punchout List

**For:** Jose
**Purpose:** Everything that needs to be updated/fixed on ChannelCast.TV before we launch to clients.
**Status:** 🟡 Jose shipped a first pass — API work verified, front-end pending Eric's test.
**Last updated:** 2026-07-14

---

## How to read this

**Priority**
- **P1 — Needed for Launch** (blocker) · **P2 — Important** · **P3 — Nice to Have**

**Status**
- **✓ Verified** — confirmed against the live ChannelCast API. Done.
- **◐ Partly landed** — some of it shipped, some is still missing.
- **🔍 Needs test** — front-end/visual. Eric has to look at it; can't be checked via API.

**Scorecard:** 7 verified · 1 partly landed · 13 need testing (21 items)
**No confirmed blockers left.** Remaining P1s are all untested front-end (CC-02 logo *display*, CC-03/04/05 scheduling, CC-14 domain verify).
**✅ Cleared Jul 16:** CC-19 (VOD play tracking now records) · CC-07 (image upload fixed platform-wide) — both confirmed by direct test.

---

## ⚑ Start here, Jose — CC-09 + CC-20 are probably one bug (CC-19 already cleared)

The on-demand page runs **two player instances that aren't aware of each other**: the inline **feature block**, and the **overlay/modal** that opens when you click a video. Several VOD problems trace back to that split:

- **CC-09** — both players run at once, so you get two videos and two audio tracks.
- **CC-19** ✅ *FIXED Jul 16* — VOD plays now record. The fix was getting the overlay player to fire the play event. *(Left here for context — likely the same code path as the two below.)*
- **CC-20** — plays double-logged, sometimes half a second apart. Two players / double event binding, one video. Note: the CC-19 fix may have *added* to this, since the overlay just started firing events — check they don't now double-count.

**Fix how those two players are wired and you likely close CC-09 and CC-20 too.** Worth doing before picking off anything else on the VOD side.

---

## ✓ Verified done (confirmed via API)

- [x] **CC-01 · P1 · Media Library — separate `filename` field, distinct from display `title`.**
  `list_media` returns `filename` and `title` as separate fields; `update_media` sets each independently. Existing items backfilled with filename mirroring title (correct).
  - 👁 Still worth a glance: confirm the **dashboard UI** exposes both fields for editing, not just the API.
- [x] **CC-15 · P2 · `update_schedule` + `delete_schedule`.** Both exist. `update_schedule` takes recurrence, `byWeekDay`, `interval`, `monthlyWeekOfMonth`, `untilUtc`.
- [x] **CC-16 · P3 · `delete_media` + `update_media`.** Both exist. `delete_media` also pulls the item from any playlists and VOD categories that referenced it — so the loop-builder's "archive" workaround can eventually go away.
- [x] **CC-17 · P3 · Category management.** All four exist: `list_category_items`, `remove_media_from_category`, `reorder_category_items`, `delete_category`.
- [x] **CC-07 · P1 · Image upload fixed platform-wide. ✅** *(was the last confirmed blocker)* Every image-upload control was dead — VOD detail thumbnails and the Channel Settings logo both refused to upload. **Confirmed working by Eric (Jul 16).** Root cause was the Blazor front-end circuit failing in production (Jose traced it to the shared `ImageDropzone.razor` — a deploy/asset issue, not the component code). Fixing the shared uploader cleared both this and the CC-02 logo control at once, as predicted.
  - ➡️ Unblocks **CC-02** (logo watermark) — logo can now be uploaded; what remains there is confirming it actually *displays* on the players.
- [x] **CC-12 · P2 · Broadcast/playlist plays counted separately from VOD.** `play_report` returns a `sourceSplit` and every play carries a `source` — and Eric confirmed the playlist plays now show on the analytics page.
  - ⚠️ *It's now inverted from the original complaint:* broadcast plays count, **VOD plays read zero**. That's **CC-19** — a real bug, not an empty dataset.

## ◐ Partly landed

- [ ] **CC-18 · P3 · Broaden `play_report`.**
  - ✓ Landed: history 7 days → **366**; `perEpisode=true` per-episode totals; every play carries a `source` with a **VOD-vs-broadcast split**; and as of **Jul 16 viewer geo is in** — each play now has `ip` + `geo` {city, region, country}. Clears the geo half of CC-11 and enables CC-21.
  - 👁 Only one thing still missing: **share counts**. No `shares` field in the raw log or per-episode view. (Raw log also still capped at 200 rows — `perEpisode` mode is the way around it.)

---

## 🔍 Needs Eric's manual test

### Playlists / Scheduling
- [ ] **CC-03 · P1 — Recurring schedules aren't recurring to the following week.**
  ✓ *Looks like it fired:* all 28 schedules read back as `Weekly` starting the week of Jul 6–12, and there are plays on Mon Jul 13 — including `TWI PRParadeWeekendCountdown` at 23:09 UTC, which is exactly the Monday Loop 4 opener (Loop 4 is scheduled 22:00 UTC).
  👁 *But confirm on screen:* every play is tagged `source: "channel"`, never `"schedule"` — so the API can't tell me whether the schedule fired or the channel is just grinding its default loop.
- [ ] **CC-04 · P1 — "Gap between videos" won't go to 0.** Set a playlist's gap to **0** and save. Does it stick, or snap back to 1s? If it sticks, a 6h loop should run 6:00:00, not ~6:02. *(The API has always accepted `gapSeconds` — the bug was the UI clamping to a 1s minimum, so I can't verify from my side.)*
- [ ] **CC-05 · P1 — Schedule screen should show the next recurring date.** *(`list_schedules` still returns no next-occurrence field — not proof it's missing, the UI may compute it.)*
- [ ] **CC-06 · P3 — Collapsible days on the schedule screen.**

### Video Player
- [ ] **CC-02 · P1 — Logo bug option on the video player.**
  A persistent channel logo/watermark overlaid on the video, like a TV network corner logo.

  ✅ **Update (Jul 16): UNBLOCKED — upload now works.** The image-upload bug that blocked this (CC-07) is fixed, so a logo can be uploaded. UI is built and correctly placed in Channel Settings. **What's left is confirming the watermark actually _displays_** on the players — see the test below.

  **Spec (decided — build it this way):**
  - **Where it lives:** a **per-channel setting**, in **Channel Settings**, alongside the channel hero and other branding. ✅ Jose put it here — correct.
  - **How to build it:** a **player-side overlay**, not a burned-in watermark. Draw the logo as a DOM/CSS layer on top of the video — cheap, instantly toggleable, no re-encoding. *(Burning it in via Mux would survive someone pulling the raw HLS stream, but costs encoding and can't be changed without re-processing every asset. Not worth it for launch; separate job if we ever need it.)*
  - **Controls:** on/off toggle · upload a **transparent PNG** (SVG welcome) · **corner** (TL / TR / BL / BR) · **size** · **opacity**.
  - **Behaviour:** size is a **% of player width**, not fixed pixels, so it scales with the player. Sits **above the video but below the player controls**, persists through **fullscreen**, and appears on **all three players** — live/broadcast, VOD, and the embeddable players clients drop on their own sites.

  👁 *Test now (unblocked):* upload a transparent PNG, set it bottom-right, confirm it actually shows on the **live stream**, on a **VOD**, and inside an **embed** — and that it survives **fullscreen**.

### Websites
- [ ] **CC-14 · P1 — Domain verification on the Websites tab.** Add a domain and take it all the way to **verified**.

### VOD / Embeds
- [ ] **CC-08 · P2 — Embed a single VOD category** (e.g. just *Can You Dig It!?*) rather than the whole catalog.
- [ ] **CC-09 · P2 — Clicking a VOD item plays two videos at once.** Does the background feature block pause now?
  🔎 *Jose — do this one together with CC-19 (and check CC-20 while you're in there). See the "Start here" callout at the top: they look like the same root cause.*
- [ ] **CC-10 · P2 — VOD embed theming** (background, tile, font colors).

### Live Monitor
- [ ] **CC-11 · P2 — Viewer/traffic analytics on the live monitor.** What does it show now — concurrent viewers? locations? *(Geo half is now unblocked — as of Jul 16 `play_report` returns per-play `ip` + `geo`. Question is whether the live monitor page surfaces it.)*

### Analytics
- [ ] **CC-13 · P3 — Full episode list, not just top 20.** ✓ *The data is live* — `perEpisode=true` returned all **160 episodes**. 👁 Does the page open up the full list? *(Share counts still missing from the API — see CC-18.)*

---

## 🆕 Found while verifying (new items)

- [x] **CC-19 · P1 — VOD play tracking now records on-demand plays. ✅ FIXED (Jul 16).**
  On-demand plays used to return a permanent, exact **zero** while broadcast plays recorded fine — a launch blocker. Now fixed.

  ✓ **Confirmed by direct test (Jul 16).** Eric played a VOD (`CUDI TitoPuenteJr…`) and it recorded correctly: `source: "vod"`, `sourceSplit {vod: 1, broadcast: 14}`, from his own IP. Before, 120 days showed a permanent exact zero — the dead code path is now alive.

  *What it was:* almost certainly the two-player split from CC-09 — the tracking hook lived on the feature-block player, not the overlay people actually watch in. ⚠️ *Watch the flip side:* now that the overlay tracks too, make sure it isn't feeding the double-logging in CC-20.

- [ ] **CC-20 · P2 — Plays are double-logged: one video counted several times in seconds.**
  Inflates every play count we show a client — the broadcast numbers that *are* working, and now the VOD numbers too.

  ✓ **Still happening as of Jul 16.** `MichaelaPaladio RunThisTownPart2` logged 3× in 55s (03:52:54 · 03:53:05 · 03:53:49); `Theolodge BoardingPlanes`, `AnaTijoux EnLaMia` and `SnowThaProduct ClaseDeIngles` each doubled the same hour. **Smoking gun (Jul 14):** `DVAliasKhryst NewJackCity` fired **twice 0.51s apart** (05:23:06.79 → 05:23:07.30). No human restarts a video in half a second.

  🔎 **Diagnosis for Jose.** Sub-second duplicates = a **double event binding**, not a real replay. Most likely, in order:
  1. The tracking call is bound to **more than one media event** — e.g. both `play` and `playing`, or `play` + `loadeddata`/`seeked` — so one real start fires it 2–3×.
  2. The listener is **re-attached on every render** (React re-render / StrictMode double-invoke), stacking handlers.
  3. Both players from CC-09 are mounted and each fires its own event.
  It hits **both broadcast and VOD**, so the bug is in the **shared tracking call / its binding**, not one player.

  🔬 **Fast confirm:** DevTools → Network, filter to the play-tracking request, start one video. If **2–3 identical requests fire in <1s**, it's the binding. Then check listener count on the `<video>` element (`getEventListeners($0)` in the console).

  🛠 **Two-part fix:**
  - **Client (root cause):** bind tracking to a single event (`play`), once per real start, debounced — ignore repeats of the same mediaId in the same session within ~2s; audit for duplicate / re-registered listeners.
  - **Server (safety net):** dedupe on ingest — collapse identical `(mediaId + session/IP)` events inside a short window — so stray duplicates never reach a client's numbers. Leave wider-spaced repeats (30–60s) alone; those may be genuine.

  ⚠️ *Ties into CC-19:* the overlay player just started tracking (CC-19 fix) — make sure it isn't adding to this.

- [ ] **CC-21 · P2 — Exclude internal / test IPs from analytics, with a toggle to see them.**
  Our own testing, editing and QA plays count as real plays, so every client-facing number is inflated by us. Exclude a known set of internal IPs from reporting **by default** — but keep the ability to **see that traffic on demand** (we need it for testing, e.g. we just used Eric's own play to confirm the CC-19 VOD fix).

  ✓ *The data already exists — this is a filter, not new instrumentation.* As of Jul 16 every play carries `ip` + `geo`. Eric's test plays all read `47.197.18.138 · Wesley Chapel, FL`, so they're trivially identifiable.

  **Spec:** a tenant-level **excluded-IP list** in settings (add / label / remove — e.g. "Eric home", "office WiFi"). Analytics **exclude those IPs by default**, with a clear **toggle "Include internal/test traffic"** to bring them back for QA. Prefer **labelling** excluded rows as 'internal' over hard-hiding, so it's always obvious what's being filtered and nothing looks silently missing.

  *Why it matters:* pairs with CC-20 — dedup fixes double-*fires*, this removes *our own* plays. Together they're what make the numbers we show a client trustworthy. Also lets us keep testing (CC-19, CC-02) without polluting stats.

---

## Open questions / needs decision
_(anything we're unsure about goes here so it doesn't get lost)_
