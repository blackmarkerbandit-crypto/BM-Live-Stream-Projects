"""
BlackMarker.TV Clip Agent — Core Pipeline
Orchestrates: download → transcribe → analyze → cut → brand → thumbnail
"""

import os
import re
import json
import time
import subprocess
import shutil
from pathlib import Path
from typing import Callable

import anthropic
import database as db

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", Path(__file__).parent / "output"))

SHOWS = [
    "The Weekly Interrupt",
    "Can You Dig It!? Live Music Review",
    "Talking Tipsy",
    "The Alien Podcast",
    "For The Record",
    "Duh Diggity Show",
    "2 Bafoonz, 1 Lagoon",
    "Other / Custom",
]

SYSTEM_PROMPT = """You are a content producer for BlackMarker.TV, a Tampa-based independent streaming network
specializing in hip-hop culture, battle rap, current events commentary, music reviews, and comedy.

Your task is to analyze a video transcript and identify the best moments to cut as short-form clips
for Instagram Reels, YouTube Shorts, and TikTok.

You understand what makes content pop on these platforms for a Black cultural audience:
- Battle rap: punchlines, multis, crowd reactions, post-battle analysis
- Hip-hop commentary: hot takes, ranking debates, industry news reactions
- Comedy: punchlines, callbacks, crowd energy moments
- Music reviews: the verdict moment, the standout bar breakdown, the comparison burn
- Current events: the strong opinion, the receipts moment, the "I told you" payoff

Always return valid JSON only. No preamble. No explanation. No markdown fences."""

USER_PROMPT_TEMPLATE = """VIDEO METADATA
==============
Show: {show_name}
Episode: {episode}
Total duration: {total_duration_str}
Requested clip range: {min_duration}–{max_duration} seconds
Maximum clips to find: {max_clips}

TRANSCRIPT
==========
{transcript_text}

TASK
====
Identify between 5 and {max_clips} clip moments that would perform best as short-form social media
content for BlackMarker.TV. For each clip provide:

- start_time: float seconds (align to natural sentence or pause boundary)
- end_time: float seconds (align to natural sentence or pause boundary)
- title: string max 60 chars, punchy, social-ready
- summary: string 1-2 sentences explaining why this moment works
- hook_line: exact first sentence of the clip
- clip_type: one of bar|highlight|reaction|commentary|comedy|review|debate
- vibe_score: integer 1-10 (10 = must-post)
- caption_instagram: 150-300 chars with 5-8 hashtags (use \\n for newlines)
- caption_tiktok: under 150 chars, 3-4 hashtags
- caption_youtube: title + 2-3 sentence description + tags

Constraints:
- Each clip must be between {min_duration} and {max_duration} seconds
- No two clips may overlap by more than 10 seconds
- start_time and end_time must be within 0 and {total_duration_float}

Return ONLY a valid JSON array. No wrapper. No markdown:

[{{"start_time":0,"end_time":0,"title":"","summary":"","hook_line":"","clip_type":"highlight","vibe_score":5,"caption_instagram":"","caption_tiktok":"","caption_youtube":""}}]"""


def fmt_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s"


def fmt_srt_ts(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def segments_to_text(segments: list, max_chars: int = 80000) -> str:
    lines = []
    for seg in segments:
        start = seg.get("start", 0)
        h = int(start // 3600)
        m = int((start % 3600) // 60)
        sc = int(start % 60)
        lines.append(f"[{h:02d}:{m:02d}:{sc:02d}] {seg['text'].strip()}")
    text = "\n".join(lines)
    if len(text) > max_chars:
        cut = int(max_chars * 0.4)
        text = text[:cut] + "\n...[middle trimmed for length]...\n" + text[-(max_chars - cut):]
    return text


def segments_to_srt(segments: list) -> str:
    lines = []
    idx = 1
    for seg in segments:
        words = seg.get("words", [])
        if not words:
            words = [{"word": seg["text"], "start": seg["start"], "end": seg["end"]}]
        chunk_size = 8
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i + chunk_size]
            if not chunk:
                continue
            start = chunk[0].get("start", seg["start"])
            end = chunk[-1].get("end", seg["end"])
            text = " ".join(w.get("word", "").strip() for w in chunk).strip()
            if not text:
                continue
            lines.append(f"{idx}\n{fmt_srt_ts(start)} --> {fmt_srt_ts(end)}\n{text}\n")
            idx += 1
    return "\n".join(lines)


def extract_clip_captions(segments: list, start_s: float, end_s: float) -> list:
    result = []
    for seg in segments:
        words = seg.get("words", [])
        if not words:
            words = [{"word": seg["text"], "start": seg["start"], "end": seg["end"]}]
        chunk_size = 8
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i + chunk_size]
            if not chunk:
                continue
            cs = chunk[0].get("start", seg["start"])
            ce = chunk[-1].get("end", seg["end"])
            if ce < start_s or cs > end_s:
                continue
            text = " ".join(w.get("word", "").strip() for w in chunk).strip()
            if not text:
                continue
            result.append({
                "text": text,
                "start": max(0.0, round(cs - start_s, 3)),
                "end": round(min(ce, end_s) - start_s, 3),
            })
    return result


def escape_drawtext(text: str) -> str:
    return (text
            .replace("\\", "\\\\")
            .replace("'", "\u2019")
            .replace(":", "\\:")
            .replace("[", "\\[")
            .replace("]", "\\]"))


def build_brand_filter(captions: list, show_name: str, episode: str) -> str:
    filters = []
    for cap in captions:
        safe = escape_drawtext(cap["text"])
        s = cap["start"]
        e = cap["end"]
        filters.append(
            f"drawtext=text='{safe}':"
            f"fontfile='C\\:/Windows/Fonts/arial.ttf':"
            f"fontsize=48:fontcolor=white:borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y=h-th-80:"
            f"box=1:boxcolor=black@0.50:boxborderw=12:"
            f"enable='between(t,{s},{e})'"
        )
    filters.append(
        "drawtext=text='BlackMarker.TV':"
        "fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        "fontsize=26:fontcolor=white@0.80:borderw=2:bordercolor=black@0.5:"
        "x=w-tw-20:y=18"
    )
    bug = escape_drawtext(f"{show_name} | {episode}" if episode else show_name)
    filters.append(
        f"drawtext=text='{bug}':"
        f"fontfile='C\\:/Windows/Fonts/arial.ttf':"
        f"fontsize=20:fontcolor=white@0.75:borderw=1:bordercolor=black@0.5:"
        f"x=16:y=h-th-16"
    )
    return ",".join(filters)


def download_youtube(url: str, job_dir: Path, emit: Callable, job_id: str) -> str:
    emit({"type": "log", "level": "info", "stage": "download", "message": f"Downloading: {url}"})
    raw_dir = job_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_tmpl = str(raw_dir / "source.%(ext)s")
    cmd = [
        "yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4", "--no-playlist", "--newline", "-o", out_tmpl, url,
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout:
        line = line.strip()
        m = re.search(r'\[download\]\s+([\d.]+)%', line)
        if m:
            emit({"type": "download_progress", "percent": float(m.group(1))})
        elif line:
            emit({"type": "log", "level": "info", "stage": "download", "message": line[:200]})
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp failed with exit code {proc.returncode}")
    for f in raw_dir.iterdir():
        if f.name.startswith("source."):
            return str(f)
    raise FileNotFoundError("yt-dlp ran but output file not found")


def transcribe_video(video_path: str, model_size: str, emit: Callable, job_id: str) -> list:
    emit({"type": "log", "level": "info", "stage": "transcribe",
          "message": f"Loading Whisper model '{model_size}'..."})
    try:
        import whisper
    except ImportError:
        raise RuntimeError("openai-whisper not installed. Run: pip install openai-whisper")
    model = whisper.load_model(model_size)
    emit({"type": "log", "level": "info", "stage": "transcribe",
          "message": "Transcribing audio — this may take several minutes..."})
    result = model.transcribe(
        video_path, verbose=False, word_timestamps=True, language="en",
        condition_on_previous_text=True,
        initial_prompt="BlackMarker.TV. Hip-hop. Battle rap. Current events. Tampa Florida. Urban culture.",
    )
    segments = result["segments"]
    emit({"type": "transcribe_progress", "segments_done": len(segments),
          "segments_total": len(segments), "message": f"Transcribed {len(segments)} segments"})
    emit({"type": "log", "level": "success", "stage": "transcribe",
          "message": f"Transcription complete — {len(segments)} segments"})
    return segments


def analyze_with_claude(segments, show_name, episode, min_duration, max_duration, max_clips, emit, job_id):
    emit({"type": "log", "level": "info", "stage": "analyze",
          "message": "Sending transcript to Claude for clip analysis..."})
    total_duration = segments[-1]["end"] if segments else 0
    transcript_text = segments_to_text(segments)
    prompt = USER_PROMPT_TEMPLATE.format(
        show_name=show_name, episode=episode or "—",
        total_duration_str=fmt_duration(total_duration),
        total_duration_float=round(total_duration, 1),
        min_duration=min_duration, max_duration=max_duration,
        max_clips=max_clips, transcript_text=transcript_text,
    )
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=4096,
        system=SYSTEM_PROMPT, messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
    clips_data = json.loads(raw)
    if isinstance(clips_data, dict) and "clips" in clips_data:
        clips_data = clips_data["clips"]
    clips_data.sort(key=lambda c: c.get("vibe_score", 0), reverse=True)
    clips_data = clips_data[:max_clips]
    emit({"type": "analyze_complete", "clips_identified": len(clips_data),
          "message": f"Claude identified {len(clips_data)} clips"})
    emit({"type": "log", "level": "success", "stage": "analyze",
          "message": f"Found {len(clips_data)} clips. Top vibe: {max((c.get('vibe_score',0) for c in clips_data), default=0)}/10"})
    return clips_data


def cut_and_brand_clip(video_path, clip_data, clip_index, clip_id, segments, job_dir, show_name, episode, emit, job_id):
    clips_dir = job_dir / "clips"
    thumbs_dir = job_dir / "thumbs"
    raw_dir = job_dir / "raw"
    for d in (clips_dir, thumbs_dir, raw_dir):
        d.mkdir(parents=True, exist_ok=True)

    start = float(clip_data["start_time"])
    end = float(clip_data["end_time"])
    duration = end - start
    safe_title = re.sub(r'[^\w\s-]', '', clip_data.get("title", "clip"))[:40].strip().replace(" ", "_")
    base = f"clip_{clip_index:02d}_{safe_title}"
    raw_path = str(raw_dir / f"{base}_raw.mp4")
    final_path = str(clips_dir / f"{base}.mp4")
    thumb_path = str(thumbs_dir / f"{base}.jpg")

    emit({"type": "log", "level": "info", "stage": "cut",
          "message": f"[{clip_index}] Cutting {fmt_duration(duration)}: {clip_data.get('title','')[:50]}"})

    # Pass 1: stream-copy rough cut
    cmd_cut = ["ffmpeg", "-y", "-ss", str(start), "-i", video_path,
                "-t", str(duration), "-c", "copy", "-movflags", "+faststart", raw_path]
    r = subprocess.run(cmd_cut, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg cut failed: {r.stderr[-400:]}")

    # Pass 2: brand pass
    emit({"type": "log", "level": "info", "stage": "brand",
          "message": f"[{clip_index}] Applying branding and captions..."})
    captions = extract_clip_captions(segments, start, end)
    vf = build_brand_filter(captions, show_name, episode)
    cmd_brand = [
        "ffmpeg", "-y", "-i", raw_path, "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        final_path,
    ]
    r2 = subprocess.run(cmd_brand, capture_output=True, text=True, timeout=600)
    if r2.returncode != 0:
        emit({"type": "log", "level": "warn", "stage": "brand",
              "message": f"Branding pass failed, using raw cut. Error: {r2.stderr[-200:]}"})
        shutil.copy2(raw_path, final_path)

    # Thumbnail
    seek = min(2.0, duration * 0.1)
    cmd_thumb = [
        "ffmpeg", "-y", "-ss", str(seek), "-i", final_path, "-vframes", "1",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-q:v", "3", thumb_path,
    ]
    subprocess.run(cmd_thumb, capture_output=True, timeout=60)
    return final_path, thumb_path


def parse_srt_to_segments(srt_path: str) -> list:
    text = Path(srt_path).read_text(encoding="utf-8", errors="replace")
    segments = []
    def parse_ts(ts):
        ts = ts.strip().replace(",", ".")
        p = ts.split(":")
        return float(p[0]) * 3600 + float(p[1]) * 60 + float(p[2])
    blocks = re.split(r'\n\s*\n', text.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        match = re.match(r'(.+?)\s*-->\s*(.+)', lines[1])
        if not match:
            continue
        start = parse_ts(match.group(1))
        end = parse_ts(match.group(2))
        content = re.sub(r'<[^>]+>', '', ' '.join(lines[2:]).strip())
        segments.append({"start": start, "end": end, "text": content,
                          "words": [{"word": content, "start": start, "end": end}]})
    return segments


def run_job(job_id: str, emit: Callable):
    job = db.get_job(job_id)
    if not job:
        return

    def log(msg, level="info", stage="general"):
        db.add_log(job_id, msg, level, stage)
        emit({"type": "log", "level": level, "stage": stage, "message": msg})

    def stage(name, progress):
        db.update_job(job_id, status=name, progress=progress)
        emit({"type": "stage_change", "stage": name, "progress": progress})

    try:
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        emit({"type": "job_started", "status": "pending",
              "show_name": job["show_name"], "episode": job["episode"]})

        # Step 1: Get video
        video_path = job.get("video_path") or job["input_path"]
        if job["input_type"] == "youtube":
            stage("downloading", 5)
            video_path = download_youtube(job["input_path"], job_dir, emit, job_id)
            db.update_job(job_id, video_path=video_path)
            log(f"Downloaded: {Path(video_path).name}", "success", "download")
        else:
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            db.update_job(job_id, video_path=video_path)

        # Step 2: Transcribe
        stage("transcribing", 15)
        srt_path = job.get("srt_path")
        if srt_path and Path(str(srt_path)).exists():
            log(f"Using provided transcript: {Path(srt_path).name}", "info", "transcribe")
            segments = parse_srt_to_segments(srt_path)
        else:
            segments = transcribe_video(video_path, job["whisper_model"], emit, job_id)
            srt_path = str(job_dir / "transcript.srt")
            Path(srt_path).write_text(segments_to_srt(segments), encoding="utf-8")
            db.update_job(job_id, srt_path=srt_path)
            log("Transcript saved: transcript.srt", "success", "transcribe")

        # Step 3: Analyze
        stage("analyzing", 40)
        clips_data = analyze_with_claude(
            segments, job["show_name"], job["episode"],
            job["min_duration"], job["max_duration"], job["max_clips"], emit, job_id,
        )

        clip_ids = []
        for i, c in enumerate(clips_data, 1):
            cid = db.create_clip(
                job_id=job_id, clip_index=i,
                start_time=float(c["start_time"]), end_time=float(c["end_time"]),
                title=c.get("title", ""), summary=c.get("summary", ""),
                hook_line=c.get("hook_line", ""), clip_type=c.get("clip_type", "highlight"),
                vibe_score=int(c.get("vibe_score", 5)),
                caption_instagram=c.get("caption_instagram"),
                caption_tiktok=c.get("caption_tiktok"),
                caption_youtube=c.get("caption_youtube"),
            )
            clip_ids.append(cid)

        # Step 4: Cut and brand
        stage("cutting", 50)
        n = len(clips_data)
        for i, (clip_data, clip_id) in enumerate(zip(clips_data, clip_ids), 1):
            db.update_job(job_id, progress=50 + int((i / n) * 45))
            emit({"type": "clip_start", "clip_index": i,
                  "clip_title": clip_data.get("title", ""),
                  "start_time": clip_data["start_time"], "end_time": clip_data["end_time"]})
            try:
                db.update_clip(clip_id, status="cutting")
                vid, thumb = cut_and_brand_clip(
                    video_path, clip_data, i, clip_id, segments,
                    job_dir, job["show_name"], job["episode"], emit, job_id,
                )
                db.update_clip(clip_id, status="done", video_path=vid, thumbnail_path=thumb)
                log(f"[{i}/{n}] Done: {clip_data.get('title','')[:50]}", "success", "cut")
                emit({"type": "clip_done", "clip_index": i, "clip_id": clip_id,
                      "video_path": vid, "thumbnail_path": thumb})
            except Exception as e:
                err = str(e)
                db.update_clip(clip_id, status="error", error_message=err)
                log(f"[{i}/{n}] Clip failed: {err[:200]}", "error", "cut")
                emit({"type": "clip_error", "clip_index": i, "error": err})

        done_count = sum(1 for cid in clip_ids if (db.get_clip(cid) or {}).get("status") == "done")
        db.update_job(job_id, status="done", progress=100, clips_count=done_count)
        log(f"Job complete — {done_count}/{n} clips ready", "success")
        emit({"type": "job_done", "clips_count": done_count, "status": "done"})

    except Exception as e:
        err = str(e)
        db.update_job(job_id, status="error", error_message=err)
        db.add_log(job_id, f"Fatal error: {err}", "error")
        emit({"type": "job_error", "error_message": err})
