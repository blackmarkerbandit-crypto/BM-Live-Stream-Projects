# Clip Cutter

An Opus Pro replacement that automatically segments long-form video into 1-2 minute clips using transcript analysis.

## Two Ways to Use It

### 1. Web UI (No Install Required)

Open `clip-cutter-ui.html` in your browser.

1. **Load video** — drag & drop or click "Load Video"
2. **Load transcript** — upload an `.srt`, `.vtt`, or `.txt` file
3. **Click "Auto-Detect Segments"** — the AI scoring engine identifies the best clips
4. **Review segments** — preview each clip, remove bad ones, reorder
5. **Export** — generates FFmpeg commands to cut the clips

### 2. Python CLI (Batch Processing)

```bash
pip install srt   # optional, only needed if you want the srt library

# Preview detected segments (no cutting)
python clip_cutter.py video.mp4 transcript.srt --preview-only

# Auto-detect and cut all clips
python clip_cutter.py video.mp4 transcript.srt --output-dir ./clips

# Custom duration range
python clip_cutter.py video.mp4 transcript.srt --min-duration 45 --max-duration 90

# Export JSON for the web UI
python clip_cutter.py video.mp4 transcript.srt --export-json segments.json

# Export a shell script of FFmpeg commands
python clip_cutter.py video.mp4 transcript.srt --export-script

# Re-encode for frame-accurate cuts (slower)
python clip_cutter.py video.mp4 transcript.srt --reencode
```

**Requires:** Python 3.10+ and FFmpeg on PATH.

## How the Scoring Engine Works

The segment detector uses a sliding window approach with content scoring:

- **Hook patterns** — detects strong opening phrases ("here's the thing", "the biggest mistake", "let me tell you")
- **Content signals** — questions, stories, data references, actionable advice, myth-busting
- **Sentence structure** — rewards punchy short sentences, penalizes thin content
- **Boundary snapping** — cuts align to sentence endings, not mid-thought
- **De-duplication** — overlapping high-scoring segments are merged, keeping the best

Each segment gets a **score** and **tags** so you can quickly identify the strongest clips.

## Supported Transcript Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| SubRip | `.srt` | Most common, from YouTube/Premiere/DaVinci |
| WebVTT | `.vtt` | Web standard, from YouTube auto-captions |
| Timestamped text | `.txt` | `[00:01:23] Some text...` format |
| Plain text | `.txt` | No timestamps — evenly distributed across video duration |
| Segments JSON | `.json` | Pre-computed segments from Python CLI |

## Getting Transcripts

- **YouTube** — use `yt-dlp --write-subs --sub-lang en VIDEO_URL`
- **Premiere Pro** — File > Export > Captions (.srt)
- **DaVinci Resolve** — Deliver page, export subtitles
- **Whisper AI** — `whisper video.mp4 --output_format srt` (free, local, highly accurate)
- **Descript** — export transcript as .srt

## Keyboard Shortcuts (Web UI)

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `Left Arrow` | Skip back 5s |
| `Right Arrow` | Skip forward 5s |
| `Shift + Left` | Skip back 1s |
| `Shift + Right` | Skip forward 1s |
