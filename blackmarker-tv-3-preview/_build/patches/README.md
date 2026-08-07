# One-off patch scripts

These already ran. Their changes are baked into `../src/` and the built pages —
they are kept for the record of *what* changed and *why* (the comments explain the
reasoning behind each design decision), not because they need running again.

| Script | What it did |
|---|---|
| `destartup.ps1` | Stripped all "small / early / build phase / startup" framing from the public copy |
| `form-sidebar.ps1` | Made the lead form a sticky right rail — **superseded, rejected** |
| `form-fullwidth.ps1` | Reverted that; form back below the content, full width, fields 3-across |
| `form-and-partners.ps1` | Form panel contrast + per-type icons/accents on the Partnerships cards |
| `advertising-update.ps1` | Placement icons + Eric's revised rate card |
| `production-update.ps1` | Event icons + replaced the two-box "us vs them" with a real comparison table |
| `submit-update.ps1` | Landing-card icons + rebuilt Do/Don't as a paired grid |
| `fix-vod-claims.ps1` | Removed every claim implying the Free Loop is an on-demand library |

Order matters if they were ever replayed: `form-sidebar` then `form-fullwidth`
(the second undoes the first).
