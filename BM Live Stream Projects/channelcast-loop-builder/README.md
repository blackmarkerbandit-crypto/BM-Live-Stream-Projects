# ChannelCast Loop Builder

A small local web app that builds, views, edits and pushes ChannelCast loop
playlists — so you can do the work yourself without spending Claude tokens.

It talks straight to ChannelCast with your API token, applies the same
scheduling rules we've been using by hand, and shows every loop as a
timestamped spreadsheet you can edit.

## What it does
- **Loops tab** — pick any loop; see it as a timestamped grid (plays-at, title,
  type, length). Reorder rows (↑/↓ then *Save order*) or remove them (✕). Edits
  sync back to ChannelCast immediately.
- **Generate tab** — build a new 6-hour loop with the rules baked in:
  ~6h (never over 6h15s), no repeated songs, same artist ≥ 2h apart, up to 3
  performance/interview *specials* each with the 19s plug intro spread evenly,
  the rest mostly music videos with the odd promo. Optionally start with a
  full-length show (opener). Preview it, then push to an empty loop.
  Specials don't repeat across loops until the pool is depleted, then it resets.
- **Library tab** — *Sync library* pulls the full media list (run it after
  uploading new videos). *Load a new video* adds an MP4/HLS URL to ChannelCast.
  Under *Media by type*, tick files (or *select all* within a section, which
  respects the active filter) and set the whole selection to one type in a
  single action. Sections stay expanded as you work — retyping a file no longer
  collapses the list you're working through.
- **Archive Cleanup tab** — three steps, in order:
  1. **Scan** reads every file's real ChannelCast status (Active / Archived —
     the one you set in the dashboard). ~2 minutes; it has to work around a
     100-row cap on the media API. Once scanned, archived files are excluded
     from every future loop the app builds.
  2. **Purge** re-reads all the loops live, audits every one against every rule,
     then offers two fixes per loop (the recommended one is preselected):
     - **Surgical** — cut out just the archived items and top the loop back up
       to 6h. A handful of API calls per loop instead of a few hundred;
       everything else is left alone. Its one cost is *drift*: removing a
       30-second promo shifts everything after it 30 seconds earlier, so an
       artist pair sitting right on the 2h line can land a little under it. The
       exact worst case is shown per loop, and anything past
       `spacing_tolerance_seconds` (default 5 min) is recommended for rebuild.
     - **Full rebuild** — regenerate the loop from scratch. Exact on every rule,
       but it reshuffles all the music and is ~60× slower. Note it also forces
       the loop back to 6h, so a deliberately longer loop (one built around a
       3-hour show) gets resized — the table warns when that applies.
     Both are safe to interrupt: a rebuild resumes where it stopped, and surgery
     re-reads each loop live as it reaches it.
  3. **Delete** removes the archived files from ChannelCast permanently, with a
     progress bar. Anything still in a loop is skipped (purge first). *Export
     CSV* gives you the list to work through by hand instead.

## First-time setup
1. Install **Python 3** from https://python.org (tick "Add to PATH").
2. Double-click **run.bat** (Windows). It installs the dependencies the first
   time, then opens http://127.0.0.1:8765 in your browser.
   - Not on Windows? Run: `pip install -r requirements.txt` then `python app.py`.
3. Go to the **Library** tab and click **Sync library** once.

## Notes / limits
- `config.json` holds your API token — keep this folder private, don't share it.
- Reorder/remove/generate all sync to ChannelCast live.
- Pushing a generated loop **appends**; push into an empty loop (or clear it
  first) to avoid mixing.
- The engine classifies media by title prefix (`MV `, `LP `/`LI `/`Performance `,
  `IA `/promos, `TWI `/`BMTV ` shows). Keep naming consistent and it stays tidy.

## Files
| file | purpose |
|---|---|
| `app.py` | web server + API |
| `scheduler.py` | the loop-building rules |
| `media_scan.py` | full-library status scan (works around the 100-row API cap) |
| `surgical.py` | loop rule audit + surgical repair planning |
| `channelcast_client.py` | talks to the ChannelCast API |
| `index.html` | the interface |
| `config.json` | your token + channel settings |
| `library.json` / `usage.json` | local caches (auto-created) |
| `media_status.json` | which media ChannelCast has archived (auto-created) |
