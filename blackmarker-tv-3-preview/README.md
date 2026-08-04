# BlackMarker.TV 3.0 — Preview Site

High-fidelity preview of the new **www.blackmarker.tv**. Every page is a standalone HTML file
(styles inline, images base64 or live CDN URLs) so it opens by double-clicking — no server needed.

Working copy lives at `C:\Users\imagi\OneDrive\Desktop\BlackMarkerTV-Preview\`.
This folder is the committed snapshot. `_backup-*` folders in the working copy are **not** tracked.

## Pages (18)

| Page | File |
|---|---|
| Homepage | `BlackMarkerTV-3-LIVE-PREVIEW.html` |
| Schedule | `BlackMarkerTV-3-SCHEDULE.html` |
| Contact | `BlackMarkerTV-3-CONTACT.html` |
| The Bodega | `BlackMarkerTV-3-BODEGA.html` |
| Account | `BlackMarkerTV-3-ACCOUNT.html` |
| **Exclusive Shows** | `-CAN-YOU-DIG-IT` · `-WEEKLY-INTERRUPT` · `-FOR-THE-RECORD` · `-ALIEN-PODCAST` · `-TALKING-TIPSY` |
| *(archive)* | `-2-BAFOONZ` · `-DUH-DIGGITY` |
| **Event Streams** | `-SPECIAL-INTERRUPTS` · `-PERFORMANCE-BATTLES` |
| **Work With Us** | `-PARTNERSHIPS` · `-ADVERTISING` · `-PRODUCTION` · `-SUBMIT-MUSIC` |

## Rebuilding

Scripts are PowerShell and assume the working copy path above. Run from `_build/`.

| Script | What it does |
|---|---|
| `site-data.ps1` | **Single source of truth** — nav structure + generated-page specs. Edit this first. |
| `build-nav.ps1` | Owns the entire `<div class="nav-in">` on every page, incl. the active-item highlight. **Run after anything that adds a page.** |
| `build-show-pages.ps1` | Builds the generated show pages, then calls `build-nav.ps1`. |
| `build-schedule.ps1` | Schedule page. Card order = editorial priority. |
| `build-contact.ps1` / `build-bodega.ps1` / `build-account.ps1` / `build-workwithus.ps1` | The standalone pages. |
| `refresh-homepage.ps1` | Re-pulls the MRSS feed and rebuilds Latest Videos + Trending with live thumbnails. **Re-run after uploads.** |
| `refresh-upcoming.ps1` | Regenerates the Upcoming loop snapshot (needs `src/loop-items.csv` + `$env:BM_BLOCK_START`). |
| `prep-art.ps1` / `make-interrupts-art.ps1` | Generate show art and branded placeholders. |

`src/` holds the page bodies and CSS the build scripts splice in. `art/` holds show artwork
(most of it mirrors `https://files.stablerack.com/webfiles/91215/`).

## Notes for implementation

- Every form is wrapped in `BEGIN CMS FORM` / `END CMS FORM` comments listing its field names.
  **All five forms share one field-name set** so the CMS form tool needs a single mapping.
- Integration annotations default to **off** (`<body class="no-ann">`); the wireframe banner toggles them.
- Pending ChannelCast work is tracked in `../BM Live Stream Projects/ChannelCast-Punchlist-for-Jose_v4.html`
  (CC-22 through CC-30).
