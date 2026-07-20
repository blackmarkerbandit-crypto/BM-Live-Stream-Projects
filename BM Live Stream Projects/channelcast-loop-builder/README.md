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
| `channelcast_client.py` | talks to the ChannelCast API |
| `index.html` | the interface |
| `config.json` | your token + channel settings |
| `library.json` / `usage.json` | local caches (auto-created) |
