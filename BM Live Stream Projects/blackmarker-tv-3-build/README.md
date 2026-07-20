# BlackMarker.TV 3.0 — Front-End Build Kit

Template-ready pieces split out of the design wireframe, so the homepage and the
shared header/footer can drop into the CMS and get wired to dynamic data.

## Folder structure

```
blackmarker-tv-3-build/
├─ css/styles.css        ← ONE stylesheet for the whole site (import this globally)
├─ js/main.js            ← interactions: subscribe modal, chat toggle, share (load on every page)
├─ assets/
│  ├─ logo-white.png     ← the title logo (transparent padding already cropped)
│  └─ header-bg.jpg      ← header background (referenced by .head-bg in styles.css)
├─ partials/
│  ├─ header.html        ← TOP BAR + logo/socials/subscribe + MAIN MENU + subscribe modal
│  └─ footer.html        ← FOOTER
├─ templates/
│  ├─ home.html          ← HOMEPAGE body (between header & footer) with macro slots
│  └─ page.html          ← universal interior-page shell with an EMPTY body container
├─ index.html            ← QA preview: header + home + footer assembled (see note below)
└─ README.md
```

## How the pieces fit

Every page = **header partial** + page body + **footer partial**, all sharing
**css/styles.css** and **js/main.js**.

- **Home page** → use `templates/home.html` as the body.
- **All other pages** → use `templates/page.html`; its `<main class="page-body">`
  is the universal empty container — render interior content inside it.
- Replace the `<!-- {% include "partials/header.html" %} -->` comments with your
  CMS's real include directive.

## Assets

Host the two files in `assets/` on your CDN / media path and update the URLs:
- `partials/header.html` and `partials/footer.html` reference `assets/logo-white.png`
- `css/styles.css` references `assets/header-bg.jpg` via `.head-bg` (path is `../assets/…`
  relative to the stylesheet — adjust to your asset base URL).

## Dynamic data (the macro slots)

Dynamic regions in `home.html` are marked with `{{ tokens }}` and
`BEGIN/END LOOP` comments. Swap them for your CMS macro syntax.

| Region | Element / id | Fields |
|---|---|---|
| Now playing title | `#pbTitle` | `now_playing_title` |
| Upcoming loop list | `#upcomingList` (`.up-row`, first row `.now`) | `when, artist, song, duration` |
| Latest per category | `#latestGrid` (`.card`) | `category, title, meta, duration, poster_url, href` |
| Trending in music | `#trendingRail` (`.card`) | `title, meta, duration, poster_url, href` |
| Live chat messages | `#chatBody` (`.msg`) | rendered by the realtime backend |

**One backend endpoint feeds Now Playing + Upcoming + Latest.** It should resolve
the currently-active ChannelCast schedule → active loop → now/next, plus the newest
item per On Demand category, and return JSON. (The ChannelCast MCP endpoints are
token-authenticated and can't be called from a public page, so this endpoint is the
public read-only shim.) Scheduling logic: 4 daily loops per day starting 00:00 / 06:00 /
12:00 / 18:00 ET (stored 04/10/16/22 UTC); cursor = now − blockStart.

## ChannelCast live player

The homepage embeds the live channel. The `#cc-player-…` div is in `home.html`; the
two `<script>` tags at the bottom of `home.html` load and mount it:

```html
<script src="https://channelcast.tv/embed/player.js"></script>
<script>ChannelCastPlayer.mount({ target:'#cc-player-019eba4dbb24746eafa619f8fea1e9aa', channelId:'019eba4d-bb24-746e-afa6-19f8fea1e9aa', apiBase:'https://channelcast.tv' });</script>
```

## Thumbnails

Cards ship with branded gradient placeholder tiles (play button + category glyph).
When real posters are available, add `<img class="thumb-img" src="{{ poster_url }}" alt="">`
as the first child of `.thumb` — `.thumb-img` is already styled to cover. (Real posters
are being wired up separately — "option C".)

## Latest Videos background

`home.html` has an empty `<div class="latest-bg" id="latestBg">` behind the Latest
section. Set a `background-image` on it, or drop `<img class="latest-bg-img" src="…">`
inside it (already styled to cover). Image TBD.

## Live chat

The chat is a styled placeholder with **local echo only** (messages don't broadcast).
Planned: a **Supabase-backed realtime chat** keeping this exact markup — check whether
ChannelCast ships a native chat embed first.

## Nav active state

Set `class="on"` on the current page's menu link (Home is marked in the partial as the example).

## QA preview (index.html)

`index.html` stitches header + home + footer so you can open it and confirm the split
still renders. Because it's the raw template, `{{ tokens }}` appear literally until the
CMS fills them — that's expected. The ChannelCast player + external assets load when
opened over http(s). For the fully-populated visual, use the design wireframe.
