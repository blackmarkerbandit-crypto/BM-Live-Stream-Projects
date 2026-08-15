# Black Marker Media — Agent Knowledge Base

Root context for every AI agent working in this tree. Read this before touching
any subfolder. Sections marked **[STABLE]** rarely change; **[LIVE]** sections go
stale and must be re-verified against the referenced files before you rely on them.

**Owner:** Eric Gomez · **Last updated:** 2026-08-15

---

## 1. Entity map — get these right [STABLE]

Agents confuse these constantly. They are four different things:

| Name | What it actually is |
|---|---|
| **Black Marker Media LLC** (BMB) | The company. Corporate/B2B identity. Sells Build + Produce services. Site: blackmarkermedia.com |
| **BlackMarker.TV** | The viewer-facing streaming network, branded **"Black Marker Bandit."** A consumer destination, NOT the corporate site. Different audience, different design language. |
| **ChannelCast** | The platform/CMS running BlackMarker.TV's 24/7 programmed loop channel. Has a real HTTP API (media + playlists). The thing loops get built *in*. |
| **The Free Loop** | The free viewing tier on BlackMarker.TV, fed by ChannelCast loops. |

"BMB" in Eric's writing means the company. Never render BlackMarker.TV as
"Black Marker TV" in copy — it is one word with a `.TV` suffix.

---

## 2. What the business is [STABLE]

Source: `black-marker-media/02-business-plans/bmb-core-positioning-strategy.md`

The streaming market splits into three isolated categories, and BMB's entire
thesis is that it operates all three at once:

- **BUILD** — streaming websites, branded platforms, video hosting/CMS, event
  registration, stores, SEO/PPC/social. Ongoing, not one-time.
- **PRODUCE** — multi-camera live production, hybrid events, on-site crew and
  gear, multi-platform distribution, encoding/switching/broadcast management.
- **OPERATE** — BMB runs its own network (BlackMarker.TV) as live proof the model
  works. Talk shows, music, comedy, podcasts, competitions. PPV + subscription +
  free tier.

The three compound: the network proves the model → wins client work → client work
sharpens the playbook → better network → stronger proof. Competitors operating one
layer cannot copy the loop without building the other two.

**Competitive framing:** SaaS platforms (Uscreen, Dacast, Vimeo, Muvi) sell tools
and leave. Production companies (Beverly Boy $10–25K, Varvid $5–11K) are
event-by-event vendors leaving nothing behind. Content networks (Twitch, Kick,
TrillerTV, Veeps, Rumble) own the audience relationship — creators are tenants.

**Target market:** event-driven orgs (schools, universities, churches, corporate),
venues, independent creators scaling a brand, businesses needing live presence
with no in-house capability.

### Core values (from the V/TO — use this voice)
`black-marker-media/02-business-plans/BMB-VTO.md`

1. **Earn It Every Time** — own results, no excuses, reliability is the proof
2. **Always Forward** — cutting-edge is a standard, not a style
3. **Your Win Is Our Win** — vested partners, not vendors; clients feel the outcome, never the effort
4. **Radical Honesty** — no yes-men, no filters, no politics; feedback in every direction
5. **Brand Before Self** — team win over personal credit

**10-year target (Apr 2036):** $5M/year, nationally recognized, proprietary
platform, HQ with in-house studio, business runs without the founder in the room.

**Proven process — The Black Marker Method:**
Discovery → Blueprint → Scout → Build → Go Live → Debrief → Partnership

---

## 3. Principals [STABLE]

- **Eric Gomez** — founder/owner. Also makes music. Directs all projects here.
- **DJ Charlie Chase (Cold Crush Brothers)** — **co-owner of BlackMarker.TV and one
  of Eric's main business partners.** NOT a contractor, NOT a booked act, NOT a
  hired DJ. He appears in the NYC Parade files with travel, lodging, and a DJ
  contract, which reads like a vendor relationship from the files alone — it is not.
  Cold Crush Brothers is foundational hip-hop; that legacy credibility is why BMB
  opens doors with veteran artists. His network is a **primary BMB asset** and the
  main channel for Chicago and hip-hop-world relationships. Reaching someone
  through him is an internal conversation, not a favor to ask.
- **Felix** — sales side (sales process input).
- **Los** — production / on-site.
- **Jose** — developer / implementation counterpart on BlackMarker.TV 3.0.

---

## 4. Where knowledge lives [STABLE]

```
AI SHIT/
├── black-marker-media/          Corporate: research, business plans, financials
│   ├── 01-research/             Competitor analysis, scaling strategies
│   ├── 02-business-plans/       ★ Positioning strategy, V/TO
│   ├── 03-tools-and-automation/ (mostly empty)
│   ├── 04-agents/               (empty — agent definitions go here)
│   ├── 05-reporting-and-analytics/  Revenue baseline
│   ├── 06-financials/  07-opportunities/
│   └── website/                 Corporate site build
├── BM Live Stream Projects/     Operational project work (git: BM-Live-Stream-Projects)
├── blackmarker-tv-3-preview/    BlackMarker.TV 3.0 preview site (18 pages) + build toolchain
└── EOS Research/                EOS/Traction operating-system research
```

### The broadcast knowledge base — start here for anything technical
`BM Live Stream Projects/venue-streaming-guide/` — 13 documents, the single
densest source of live-streaming know-how in this tree:

| Path | Covers |
|---|---|
| `01-streaming-platforms/` | Platform comparison, choosing a platform |
| `02-hardware-equipment/` | Cameras, encoders & switchers, starter kits |
| `03-software/` | vMix guide, OBS guide, overview |
| `04-network-bandwidth/` | Bandwidth requirements, redundancy, on-site networking |
| `05-multi-camera/` | Multi-cam planning and switching |
| `06-audio/` | FOH, stage, and audience capture methods |
| `07-monetization-ticketing/` | PPV, subscriptions, tipping, hybrid ticketing |
| `08-legal-licensing/` | Music rights, ASCAP/BMI/SESAC, privacy, ownership |

Also ships `Venue-Streaming-Playbook.pdf/.docx` (lead magnet), `landing-page.html`,
`quote-builder.html`, and a `clip-cutter/` tool.

### Other project folders
- `ATEM-Flypack/` — flypack panel design; DXF/SVG cut files + `bezel.py` generator
- `BMM-Growth/` — growth phase 1, V/TO, positioning, **`bmb-core-processes.md`**
- `channelcast-loop-builder/` — ★ see §6
- `CHI-TOWN-CNECT/` — ★ see §5
- `JAE RAE/` — ★ see §5
- `clip-agent/` — clip automation agent + SQLite DB + dashboard
- `live-chat-widget/` — chat widget + Apps Script backend
- `NYC-Parade-Weekend-June-2026/`, `PPV-April-2026-Marketing/` — event marketing
- `Design Training/` — design reference imagery
- `blackmarker-tv-3-build/` — 3.0 CMS build kit
- `BMTV CHANNELCAST/` — currently empty

---

## 5. Active projects [LIVE — verify before relying]

### BlackMarker.TV 3.0
Homepage/site redesign for the viewer-facing network. Build kit at
`BM Live Stream Projects/blackmarker-tv-3-build/` — `css/styles.css`, `js/main.js`,
`partials/header.html` + `footer.html`, `templates/home.html` + `page.html`,
`assets/`. Template macros are generic `{{ }}` placeholders — **ask which CMS**
before converting. Preview site (18 pages) lives in `blackmarker-tv-3-preview/`.
Jose is the implementation counterpart; punchlists tracked as dated HTML files at
`BM Live Stream Projects/ChannelCast-*.html` and in `NOTES FROM JOSE/`.
Live chat is deferred to a Supabase-backed build after the front end is locked.

⚠️ ChannelCast player embeds and chat only work in local files — published
artifacts block external scripts via CSP.

### CHI TOWN CNECT — Midwest expansion
Opened 2026-08-13. Anchored on a Chicago contact running **Intel Music Group (IMG)**
— a DJ collective with a streaming studio (verified: IG @intelmusicgroup, runs
"NO PROGRAM DIRECTOR" weekly on Twitch). Not corporate AV; they already have
livestream workflow experience.

He brings three assets at once: (1) a Chicago network of events/promoters/clients,
(2) IMG's existing AV client contracts, (3) original content, drops, and celebrity
interviews that can feed BlackMarker.TV / ChannelCast.

**Hard constraint:** he is resource-limited. No deal structure may require him to
front capital, buy gear, or carry payroll.

**Pilot #1 is decided and in motion** (Aug 15–16, 2026) — content track, backstage
at a Chicago event with Rah Digga, YoYo, and other female rappers. **Do not
re-litigate content-vs-AV-first.** Next checkpoint is footage arriving after Aug 16;
ask about delivery and clearance, not strategy. Scope is Midwest/regional anchored
on Chicago — Rockford IL and Racine WI are in-corridor, file them here rather than
opening new market projects. Relationship channel is Charlie Chase.

### Jae Rae Live 2026
Spiritual intuitive / tarot creator launching a luxury live show; BMB handles full
production. First live call-in show was 06-24-2026, 8pm EST. Stack: **vMix**
(everything must be vMix-compatible), 3× PTZ cameras with NDI + HDMI (PTZOptics
Move 4K; ObSbot Tail Air ruled out — no native NDI), Bitfocus Companion for camera
control, RØDECaster Pro II for audio, 1 Gbps symmetric on site, 4K target.
**No hardware switcher** — vMix switches over NDI. Three studio zones: host chair,
mystic desk, short-form wall; overhead cam for card/ritual table shots is critical.

---

## 6. ChannelCast operations [LIVE]

**The loop builder app is the go-forward tool.** `BM Live Stream Projects/channelcast-loop-builder/`
— FastAPI backend + vanilla-JS SPA, talks straight to the ChannelCast HTTP API.
Run `run.bat` → http://127.0.0.1:8765. **Direct Eric there for loop work instead of
building playlists call-by-call through an agent.**

Hard-won API facts (these cost real time to discover):

- Playlists are **fully editable** — `reorder_playlist`, `remove_playlist_item`,
  `delete_playlist`, `update_playlist`, `list_playlist_items` all exist. The
  "append-only" limitation was only ever the exposed MCP tool subset.
- `delete_media` exists and works (returns `{deleted: bool}`).
- Media carry a ChannelCast-side **status** of Active/Archived set in the dashboard.
  Archiving does **not** pull a file out of loops it is already in, and archived
  items are invisible to `list_media`'s default view — this silently kept archived
  files in rotation for months.
- `list_media` returns **at most 100 rows with no pagination** (limit/take/page/
  skip/offset are all ignored) but does return a true `total`. `%` and `_` in
  search behave as SQL LIKE wildcards. `media_scan.py` enumerates the full
  catalogue by splitting capped search terms — ~400 calls / 2 min for 1121 items.
- Library sync: 989 items (754 MV, 125 special, 64 show, 18 promo, 28 other).
  Classification is title-prefix based (MV / LP,LI,Performance / IA,Promo / TWI,BMTV).

**Scheduling rules** (`scheduler.py`): ~6h target (≤6h15s), no repeat songs, same
artist ≥2h apart, up to 3 specials each with a 19s plug intro spread evenly, the
rest mostly MVs + promos. Permanent artist exclusions: beselfliss / beselfless / aych.

⚠️ The scheduler places each artist at the *earliest legal* moment, so repeat plays
sit almost exactly on the 2h line. Removing anything mid-loop drags every later item
earlier and pushes those pairs slightly under 2h. Unavoidable without a full rebuild
— surgical mode reports **drift** instead of pass/fail (`spacing_tolerance_seconds`,
default 300).

⚠️ NDJSON progress protocol: progress lines carry `done` as an integer count; the
final summary carries `done: true`. JS must test `done === true` — a truthy test
silently eats every progress update.

---

## 7. Core processes [STABLE]

`BM Live Stream Projects/BMM-Growth/bmb-core-processes.md`

**Sales:** Discovery call → identify client type (Live Streaming / Screen Projection
/ PPV / Retainer) → identify specific needs → propose, confirm & close → contract +
invoice sent together → **confirm signed + paid (hard gate — nothing moves without
both)** → hand off to delivery.

**Production/Delivery:** **Scope review & resource confirmation (critical gate —
catch gaps and out-of-scope items early, before event day)** → gameplan & schedule →
execute → post-production finalization → financial closeout → budget debrief (feeds
future pricing).

---

## 8. How to work with Eric [STABLE]

- **Radical honesty is a stated company value — apply it to him.** He does not want
  hedging, padding, or yes-man agreement. If something will not work, say so.
- **Partner vetting: strip first-run briefs to the minimum.** When onboarding a new
  partner or vendor, give them only what is mission-critical and let them run on
  their own judgment. A detailed brief tells him nothing — if he coaches someone
  through it, he cannot tell a pro from someone following instructions. What he is
  measuring is **how far the person is from operating unsupervised**, because that
  determines how much he personally has to be on site, which drives budget and caps
  how many markets BMB can expand into at once.
  - **Keep:** delivery specs they could not guess (format, resolution, file
    handling), anything legally unrecoverable (releases/consent), and the
    deliverable itself.
  - **Cut:** technique coaching, scripts, question sets, checklists.
  - Tell him explicitly what each cut now tests. Flag any cut where being wrong
    costs the asset rather than just information — that one is his call.
  - Keep the full spec on file for later runs once the partner is established.
- Deliverables are frequently **standalone HTML documents** (briefs, punchlists,
  status reports) named with a date. Match that convention.
- Convert relative dates to absolute ones in anything written down.

---

## 9. Onboarding a new agent to this office

Point the agent at this file first, then the one or two folders its role owns:

| Role | Give it |
|---|---|
| Broadcast / production tech | §1, §5, `venue-streaming-guide/` (all 13 docs) |
| ChannelCast / programming | §1, §6, `channelcast-loop-builder/` |
| Web / 3.0 site | §1, §5, `blackmarker-tv-3-build/`, `blackmarker-tv-3-preview/` |
| Sales / growth | §2, §7, `black-marker-media/02-business-plans/`, `05-reporting-and-analytics/` |
| Partnerships / expansion | §2, §3, §8, `CHI-TOWN-CNECT/` |

Agent definitions belong in `black-marker-media/04-agents/`
(`research-agents/`, `marketing-agents/`, `ops-agents/`, `build-agents/`).

---

## 10. Native Claude Code subagents [STABLE]

Callable subagents live at `.claude/agents/` (AI SHIT root, same placement logic
as this file — covers all subtrees). Each reads this file first, then the
section(s) relevant to its role:

| Subagent | Category | Reads |
|---|---|---|
| `marketing-agent` | `marketing-agents/` | §1, §2 |
| `research-agent` | `research-agents/` | §2, §5 |
| `ops-agent` | `ops-agents/` | §7, §8 |
| `build-agent` | `build-agents/` | §4, §5, §6 |

A coordinator session in this tree should read this file, then delegate to the
matching subagent rather than doing marketing/research/ops/build work directly.
