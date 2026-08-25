# BMB Sandbox Server

Local staging host for BlackMarker.TV work in progress. **http://127.0.0.1:8790/**

Stdlib Python only — no `pip install`, no venv, no `requirements.txt`.

## Why it exists

Chat, and anything else that talks to Supabase, needs a real `http://` origin.
Double-clicking an HTML file gives you `file://`, where realtime subscriptions and
fetch behave differently than they will on the live site. This serves the files
the same way a web server does, so what you see is what you get.

## What it serves

| URL | Folder |
|---|---|
| `/sandbox/` | this folder — demo host pages built for the server |
| `/chat/` | `../bmtv-chat/` — widget, moderator panel, vMix overlay |
| `/preview/` | `../../blackmarker-tv-3-preview/` — the 18-page 3.0 preview site |
| `/build/` | `../blackmarker-tv-3-build/` — the 3.0 CMS build kit |

**Explicit mounts only.** Nothing else in the `AI SHIT` tree is reachable — no
financials, no business plans, no client files. Adding a folder means editing the
`MOUNTS` dict in `serve.py`; there is no way to reach one by guessing a URL.

Open `/` for a landing page with the shortcuts worth having.

## Two things it does that `python -m http.server` does not

**Server-side includes.** `<!--#include file="../bmtv-chat/chat-widget.html"-->`
in any served `.html` is replaced with that file's contents at request time.
This is how [`chat-demo.html`](chat-demo.html) shows the real chat widget without
holding a copy of it — edit the widget, refresh the demo, see the change. An
include is only followed if it resolves inside a mounted folder.

**No-cache on everything.** A browser refresh always shows the file as it is on
disk right now. No hard-refresh dance after every edit.

## Homepage live data

The 3.0 Live page fills three sections from real ChannelCast data. They do not
come from the same place, and the split is forced:

| Section | Source | Why |
|---|---|---|
| Now Playing | `channelcast.tv/api/v1/playback/timeseek/{channelId}` | Public, no auth, CORS `*` — the same feed the ChannelCast player uses. Read straight from the browser, accurate to the second. |
| Upcoming | `loop-data.json` + `timeseek` | No public playlist endpoint exists |
| Latest Shows | `loop-data.json` | No public media endpoint exists |

Everything except `timeseek` sits behind the ChannelCast MCP API, which
authenticates with the `cck_` token. **That token can `delete_media` and
`delete_playlist`, so it can never be in a page.** `build-loop-data.py` runs
server-side and writes `loop-data.json` — titles, schedule and poster URLs, and
nothing else.

`loop-data.json` and the loop builder's `config.json` are gitignored. The
config holds the token; do not commit it, and note the loop-builder folder is
deliberately **not** a sandbox mount, so no URL can reach it.

### Where the numbers come from — all looked up, none assumed

- **`list_schedules`** gives the real weekly timetable: 28 entries, each a
  `startUtc` and a `playlistId`. The page finds the airing block from these
  rather than assuming Eastern is UTC−4, so a schedule change or a DST shift
  needs no code edit. (The assumption happened to be right in August and would
  have broken in November.)
- **`list_playlist_items`** gives each item's `playsAtSeconds` in its block.
- **`list_category_items`** gives the newest episode per show — `sort` 0 is
  Eric's own running order, not a date scraped out of a filename.

The page cross-checks both sources every 30s and **trusts `timeseek` when they
disagree**, saying so in the note under the list. That is how you find out
`loop-data.json` has gone stale, instead of the page quietly lying.

### Keeping it current

Rebuilt **nightly at 4am** by the `BMB Loop Data Refresh` scheduled task, and on
demand from the **Rebuild now** button at http://127.0.0.1:8790/ (about 20
seconds, ~35 API calls). Rebuild after changing loops or publishing an episode.

The nightly run is `pythonw`, so its output goes nowhere — but a failed run
shows up on its own, because the sandbox home page reports how old
`loop-data.json` is and warns past 26 hours.

## Running it

**Automatic** — a per-user scheduled task, `BMB Sandbox Server`, starts it at
logon. No admin rights, same approach as the DuckDNS updater.

```
powershell -ExecutionPolicy Bypass -File install-autostart.ps1            # install / update
powershell -ExecutionPolicy Bypass -File install-autostart.ps1 -Remove    # uninstall
schtasks /run /tn "BMB Sandbox Server"                                    # start now
schtasks /end /tn "BMB Sandbox Server"                                    # stop
```

**By hand** — double-click `run.bat`. Opens a console you can watch requests in,
and opens the browser. If the scheduled task is already running, `run.bat` will
say the port is taken instead of failing cryptically; `schtasks /end` first.

## Logs

Running under the scheduled task there is no console, so requests append to
`serve.log` here (rotated to `serve.log.1` past 2 MB, gitignored). From `run.bat`
they go to the console instead and no file is written.

⚠️ **The `pythonw.exe` trap, already hit once.** The autostart task runs
`pythonw.exe` so no console window appears. Under `pythonw`, `sys.stdout` and
`sys.stderr` are `None`. `print()` handles that quietly, but a bare
`sys.stderr.write()` raises *inside the request handler* — the port still
listens, so the server looks fine, and every request dies with "connection
closed unexpectedly." This is the same trap the virtual-office service hit with
uvicorn's default logger. `log_message()` guards for it; keep that guard if this
file gets restructured.

## Port

`8790`. Override with `BMB_SANDBOX_PORT`. Current map on this machine:
`8765` loop builder · `8790` sandbox · `8934` virtual office.

Bound to `127.0.0.1` — this machine only. To reach it from outside the house it
would go behind the Caddy instance already running for the virtual office, not
by binding `0.0.0.0` directly.
