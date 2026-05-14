"""
Clip Cutter — Opus Pro Replacement
Automatically segments long-form video into 1-2 minute clips using transcript analysis.

Usage:
    python clip_cutter.py <video_file> <transcript_file> [options]

    python clip_cutter.py myvideo.mp4 myvideo.srt
    python clip_cutter.py myvideo.mp4 myvideo.srt --min-duration 45 --max-duration 120
    python clip_cutter.py myvideo.mp4 myvideo.srt --preview-only
    python clip_cutter.py myvideo.mp4 myvideo.srt --output-dir ./clips --format mp4
    python clip_cutter.py myvideo.mp4 myvideo.srt --export-json segments.json
    python clip_cutter.py myvideo.mp4 myvideo.srt --open-ui

Requirements:
    pip install srt
    FFmpeg must be installed and available on PATH.
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Transcript parsing
# ---------------------------------------------------------------------------

@dataclass
class Caption:
    index: int
    start: float       # seconds
    end: float         # seconds
    text: str

    @property
    def duration(self):
        return self.end - self.start


def parse_timestamp_srt(ts: str) -> float:
    """Parse SRT timestamp '00:01:23,456' -> seconds."""
    ts = ts.strip().replace(',', '.')
    parts = ts.split(':')
    h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    return h * 3600 + m * 60 + s


def parse_timestamp_vtt(ts: str) -> float:
    """Parse VTT timestamp '00:01:23.456' -> seconds."""
    ts = ts.strip()
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s
    elif len(parts) == 2:
        m, s = float(parts[0]), float(parts[1])
        return m * 60 + s
    return 0.0


def parse_srt(text: str) -> list[Caption]:
    """Parse SRT format transcript."""
    captions = []
    blocks = re.split(r'\n\s*\n', text.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        try:
            index = int(lines[0].strip())
        except ValueError:
            continue
        ts_match = re.match(r'(.+?)\s*-->\s*(.+)', lines[1])
        if not ts_match:
            continue
        start = parse_timestamp_srt(ts_match.group(1))
        end = parse_timestamp_srt(ts_match.group(2))
        content = ' '.join(lines[2:]).strip()
        content = re.sub(r'<[^>]+>', '', content)  # strip HTML tags
        captions.append(Caption(index=index, start=start, end=end, text=content))
    return captions


def parse_vtt(text: str) -> list[Caption]:
    """Parse WebVTT format transcript."""
    captions = []
    # Remove WEBVTT header and metadata
    text = re.sub(r'^WEBVTT.*?\n\n', '', text, flags=re.DOTALL)
    text = re.sub(r'NOTE.*?\n\n', '', text, flags=re.DOTALL)
    blocks = re.split(r'\n\s*\n', text.strip())
    idx = 0
    for block in blocks:
        lines = block.strip().split('\n')
        ts_line = None
        text_lines = []
        for line in lines:
            if '-->' in line:
                ts_line = line
            elif ts_line is not None:
                text_lines.append(line)
        if not ts_line:
            continue
        ts_match = re.match(r'(.+?)\s*-->\s*(.+?)(\s|$)', ts_line)
        if not ts_match:
            continue
        start = parse_timestamp_vtt(ts_match.group(1))
        end = parse_timestamp_vtt(ts_match.group(2))
        content = ' '.join(text_lines).strip()
        content = re.sub(r'<[^>]+>', '', content)
        idx += 1
        captions.append(Caption(index=idx, start=start, end=end, text=content))
    return captions


def parse_text_with_timestamps(text: str) -> list[Caption]:
    """Parse plain text with timestamps like '[00:01:23] Some text...'"""
    captions = []
    pattern = r'\[?(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d+)?)\]?\s*(.*?)(?=\[?\d{1,2}:\d{2}|$)'
    matches = list(re.finditer(pattern, text, re.DOTALL))
    for i, match in enumerate(matches):
        ts_str = match.group(1)
        content = match.group(2).strip()
        if not content:
            continue
        start = parse_timestamp_vtt(ts_str)
        end = matches[i + 1].start() if i + 1 < len(matches) else start + 5.0
        if i + 1 < len(matches):
            end = parse_timestamp_vtt(matches[i + 1].group(1))
        captions.append(Caption(index=i + 1, start=start, end=end, text=content))
    return captions


def parse_plain_text(text: str, video_duration: float) -> list[Caption]:
    """
    Parse plain text (no timestamps) by splitting into sentences
    and distributing them evenly across the video duration.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return []

    duration_per = video_duration / len(sentences)
    captions = []
    for i, sentence in enumerate(sentences):
        captions.append(Caption(
            index=i + 1,
            start=i * duration_per,
            end=(i + 1) * duration_per,
            text=sentence,
        ))
    return captions


def load_transcript(filepath: str, video_duration: float = 0) -> list[Caption]:
    """Auto-detect format and parse a transcript file."""
    path = Path(filepath)
    text = path.read_text(encoding='utf-8', errors='replace')

    ext = path.suffix.lower()
    if ext == '.srt':
        return parse_srt(text)
    elif ext == '.vtt':
        return parse_vtt(text)
    elif '-->' in text[:500]:
        # Auto-detect SRT or VTT
        if 'WEBVTT' in text[:20]:
            return parse_vtt(text)
        return parse_srt(text)
    elif re.search(r'\[\d{1,2}:\d{2}', text[:200]):
        return parse_text_with_timestamps(text)
    else:
        return parse_plain_text(text, video_duration)


# ---------------------------------------------------------------------------
# Segment detection (the brain)
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    id: int
    start: float
    end: float
    title: str
    text: str
    score: float = 0.0
    tags: list[str] = field(default_factory=list)

    @property
    def duration(self):
        return self.end - self.start


# Signal words/phrases that indicate high-value content
HOOK_PATTERNS = [
    (r'\b(here\'?s?\s+(the\s+)?(thing|deal|truth|secret|problem|key))', 'hook', 3),
    (r'\b(the\s+(biggest|number\s+one|most\s+important|first|worst|best))', 'hook', 3),
    (r'\b(let\s+me\s+(tell|show|explain|break))', 'hook', 2),
    (r'\b(what\s+(most|nobody|people\s+don\'?t))', 'hook', 3),
    (r'\b(stop\s+doing|you\s+need\s+to|you\s+should)', 'advice', 2),
    (r'\b(mistake|myth|misconception|wrong|lie)', 'myth-bust', 2),
    (r'\b(tip|trick|hack|strategy|framework|method|step)', 'tactical', 2),
    (r'\b(how\s+to|how\s+do|how\s+I)', 'how-to', 2),
    (r'\b(why\s+(you|most|this|it|we))', 'explainer', 2),
    (r'\b(for\s+example|in\s+other\s+words|think\s+of\s+it)', 'example', 1),
    (r'\b(story|when\s+I|one\s+time|I\s+remember)', 'story', 2),
    (r'\b(data|research|study|statistic|percent|survey)', 'data', 2),
    (r'\b(first(ly)?|second(ly)?|third(ly)?|number\s+\d|step\s+\d)', 'list', 2),
    (r'\b(question|ask\s+(me|yourself))', 'engagement', 2),
    (r'\b(money|revenue|profit|income|cost|save|dollar|pricing)', 'money', 2),
    (r'\b(I\s+was\s+wrong|changed\s+my\s+mind|plot\s+twist|but\s+then)', 'twist', 3),
]

# Sentence-ending patterns
SENTENCE_END = re.compile(r'[.!?]\s*$')
QUESTION = re.compile(r'\?\s*$')


def score_text(text: str) -> tuple[float, list[str]]:
    """Score a block of text for 'clip-worthiness'. Returns (score, [tags])."""
    score = 0.0
    tags = set()
    lower = text.lower()

    for pattern, tag, points in HOOK_PATTERNS:
        if re.search(pattern, lower):
            score += points
            tags.add(tag)

    # Reward questions (engagement hooks)
    questions = len(re.findall(r'\?', text))
    if questions:
        score += questions * 1.0
        tags.add('question')

    # Reward shorter, punchier sentences (avg under 15 words)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if sentences:
        avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_words < 12:
            score += 1.5
            tags.add('punchy')
        elif avg_words < 18:
            score += 0.5

    # Reward moderate word count (a good clip has substance)
    word_count = len(text.split())
    if 80 < word_count < 300:
        score += 1.0
    elif word_count < 40:
        score -= 1.0  # too short to be useful

    return score, list(tags)


def find_sentence_boundary(captions: list[Caption], target_time: float, search_range: float = 15.0) -> float:
    """
    Find the nearest sentence ending to target_time within search_range seconds.
    Returns the best boundary time.
    """
    best_time = target_time
    best_dist = search_range + 1

    for cap in captions:
        if abs(cap.end - target_time) > search_range:
            continue
        # Check if this caption ends with sentence-ending punctuation
        if SENTENCE_END.search(cap.text):
            dist = abs(cap.end - target_time)
            if dist < best_dist:
                best_dist = dist
                best_time = cap.end
    return best_time


def detect_segments(
    captions: list[Caption],
    min_duration: float = 45,
    max_duration: float = 120,
    target_duration: float = 75,
    max_segments: int = 50,
    overlap_threshold: float = 10,
) -> list[Segment]:
    """
    Analyze transcript and identify optimal clip segments.

    Strategy:
    1. Build a sliding window across the transcript
    2. Score each window for clip-worthiness
    3. Snap boundaries to sentence endings
    4. De-duplicate overlapping segments
    5. Return top segments ranked by score
    """
    if not captions:
        return []

    total_duration = captions[-1].end
    candidates: list[Segment] = []
    seg_id = 0

    # Pass 1: Sliding window with multiple sizes
    for window_sec in [60, 75, 90, 105, 120]:
        if window_sec < min_duration or window_sec > max_duration:
            continue

        step = max(15, window_sec // 4)  # slide by ~25% of window
        t = 0.0

        while t + min_duration <= total_duration:
            window_end = min(t + window_sec, total_duration)

            # Gather captions in this window
            window_caps = [c for c in captions if c.start >= t - 2 and c.end <= window_end + 2]
            if not window_caps:
                t += step
                continue

            window_text = ' '.join(c.text for c in window_caps)

            # Score the content
            score, tags = score_text(window_text)

            # Bonus: reward windows that start at sentence boundaries
            first_cap = window_caps[0]
            if first_cap.text and first_cap.text[0].isupper():
                score += 0.5

            # Bonus: reward windows closer to target duration
            dur = window_end - t
            dur_diff = abs(dur - target_duration) / target_duration
            score -= dur_diff * 1.5

            # Snap boundaries to sentence endings
            snap_start = find_sentence_boundary(captions, t, search_range=8)
            # For the start, we want the beginning of a sentence, so look for the
            # previous sentence end and start just after it
            start = snap_start if snap_start <= t + 5 else t

            snap_end = find_sentence_boundary(captions, window_end, search_range=10)
            end = snap_end if snap_end >= window_end - 10 else window_end

            # Ensure duration constraints
            if end - start < min_duration:
                end = start + min_duration
            if end - start > max_duration:
                end = start + max_duration

            # Clamp to video bounds
            start = max(0, start)
            end = min(total_duration, end)

            if end - start < min_duration:
                t += step
                continue

            # Generate title from the first strong sentence
            title = generate_title(window_caps)

            seg_id += 1
            candidates.append(Segment(
                id=seg_id,
                start=round(start, 2),
                end=round(end, 2),
                title=title,
                text=window_text,
                score=round(score, 2),
                tags=tags,
            ))

            t += step

    # Pass 2: De-duplicate overlapping segments (keep highest scored)
    candidates.sort(key=lambda s: s.score, reverse=True)
    final: list[Segment] = []

    for candidate in candidates:
        overlaps = False
        for existing in final:
            overlap_start = max(candidate.start, existing.start)
            overlap_end = min(candidate.end, existing.end)
            overlap_dur = overlap_end - overlap_start
            if overlap_dur > overlap_threshold:
                overlaps = True
                break
        if not overlaps:
            final.append(candidate)
        if len(final) >= max_segments:
            break

    # Sort by time order and re-number
    final.sort(key=lambda s: s.start)
    for i, seg in enumerate(final):
        seg.id = i + 1

    return final


def generate_title(captions: list[Caption]) -> str:
    """Generate a short title from the first meaningful sentence in the captions."""
    full_text = ' '.join(c.text for c in captions[:5])
    # Find the first complete sentence
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    for s in sentences:
        s = s.strip()
        if len(s.split()) >= 4:
            # Truncate if too long
            words = s.split()
            if len(words) > 10:
                return ' '.join(words[:10]) + '...'
            return s
    # Fallback
    words = full_text.split()[:8]
    return ' '.join(words) + '...' if words else 'Untitled Segment'


# ---------------------------------------------------------------------------
# Video cutting with FFmpeg
# ---------------------------------------------------------------------------

def format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS.mmm for FFmpeg."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def cut_segment(video_path: str, segment: Segment, output_path: str,
                video_format: str = 'mp4', reencode: bool = False) -> bool:
    """Cut a segment from the video using FFmpeg."""
    start_ts = format_time(segment.start)
    duration = segment.duration

    if reencode:
        cmd = [
            'ffmpeg', '-y',
            '-ss', start_ts,
            '-i', video_path,
            '-t', str(duration),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
            '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart',
            output_path,
        ]
    else:
        # Fast copy (no re-encode) — may have slight keyframe offset
        cmd = [
            'ffmpeg', '-y',
            '-ss', start_ts,
            '-i', video_path,
            '-t', str(duration),
            '-c', 'copy',
            '-movflags', '+faststart',
            output_path,
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        print(f"  Error cutting segment: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def export_json(segments: list[Segment], output_path: str):
    """Export segments as JSON (for web UI)."""
    data = []
    for seg in segments:
        data.append({
            'id': seg.id,
            'start': seg.start,
            'end': seg.end,
            'duration': round(seg.duration, 2),
            'title': seg.title,
            'text': seg.text,
            'score': seg.score,
            'tags': seg.tags,
            'startFormatted': format_time(seg.start),
            'endFormatted': format_time(seg.end),
        })
    Path(output_path).write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(f"Exported {len(data)} segments to {output_path}")


def export_ffmpeg_commands(segments: list[Segment], video_path: str, output_dir: str):
    """Export a shell script with FFmpeg commands for each segment."""
    lines = ['#!/bin/bash', f'# Auto-generated clip commands for: {video_path}', '']
    for seg in segments:
        safe_title = re.sub(r'[^\w\s-]', '', seg.title)[:50].strip().replace(' ', '_')
        filename = f"clip_{seg.id:02d}_{safe_title}.mp4"
        output = os.path.join(output_dir, filename)
        lines.append(f'# Clip {seg.id}: {seg.title}')
        lines.append(f'ffmpeg -y -ss {format_time(seg.start)} -i "{video_path}" '
                      f'-t {seg.duration:.2f} -c copy -movflags +faststart "{output}"')
        lines.append('')
    script_path = os.path.join(output_dir, 'cut_clips.sh')
    Path(script_path).write_text('\n'.join(lines), encoding='utf-8')
    print(f"Exported FFmpeg script to {script_path}")


def print_segments(segments: list[Segment]):
    """Pretty-print segments to console."""
    print(f"\n{'='*70}")
    print(f"  DETECTED {len(segments)} CLIP SEGMENTS")
    print(f"{'='*70}\n")

    for seg in segments:
        dur_str = f"{int(seg.duration//60)}:{int(seg.duration%60):02d}"
        tag_str = ', '.join(seg.tags[:4]) if seg.tags else 'general'
        print(f"  Clip {seg.id:2d}  |  {format_time(seg.start)} → {format_time(seg.end)}  |  {dur_str}  |  Score: {seg.score}")
        print(f"           |  {seg.title}")
        print(f"           |  Tags: {tag_str}")
        print(f"           |  {textwrap.shorten(seg.text, width=80, placeholder='...')}")
        print()


# ---------------------------------------------------------------------------
# Web UI launcher
# ---------------------------------------------------------------------------

def open_ui(video_path: str, transcript_path: str, segments: list[Segment]):
    """Generate a JSON file and open the web UI."""
    ui_dir = Path(__file__).parent
    json_path = ui_dir / 'segments_data.json'

    data = {
        'videoPath': os.path.abspath(video_path),
        'videoName': os.path.basename(video_path),
        'transcriptName': os.path.basename(transcript_path),
        'segments': [asdict(s) for s in segments],
    }
    json_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(f"\nSegment data written to {json_path}")
    print(f"Open clip-cutter-ui.html in your browser and load the video + segments_data.json")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Clip Cutter — Cut long-form video into short segments using transcript analysis.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python clip_cutter.py video.mp4 transcript.srt
          python clip_cutter.py video.mp4 transcript.srt --min-duration 45 --max-duration 90
          python clip_cutter.py video.mp4 transcript.srt --preview-only
          python clip_cutter.py video.mp4 transcript.srt --export-json segments.json
          python clip_cutter.py video.mp4 transcript.srt --open-ui
        """)
    )

    parser.add_argument('video', help='Path to the video file')
    parser.add_argument('transcript', help='Path to the transcript file (.srt, .vtt, or .txt)')
    parser.add_argument('--min-duration', type=float, default=45, help='Minimum clip duration in seconds (default: 45)')
    parser.add_argument('--max-duration', type=float, default=120, help='Maximum clip duration in seconds (default: 120)')
    parser.add_argument('--target-duration', type=float, default=75, help='Ideal clip duration in seconds (default: 75)')
    parser.add_argument('--max-segments', type=int, default=20, help='Maximum number of segments to detect (default: 20)')
    parser.add_argument('--output-dir', type=str, default='./clips', help='Output directory for clips (default: ./clips)')
    parser.add_argument('--format', type=str, default='mp4', help='Output format (default: mp4)')
    parser.add_argument('--reencode', action='store_true', help='Re-encode clips (slower but frame-accurate)')
    parser.add_argument('--preview-only', action='store_true', help='Only show detected segments, don\'t cut')
    parser.add_argument('--export-json', type=str, help='Export segments to JSON file')
    parser.add_argument('--export-script', action='store_true', help='Export FFmpeg commands as shell script')
    parser.add_argument('--open-ui', action='store_true', help='Generate data for the web UI')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.isfile(args.video):
        print(f"Error: Video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.transcript):
        print(f"Error: Transcript file not found: {args.transcript}", file=sys.stderr)
        sys.exit(1)

    print(f"Video:      {args.video}")
    print(f"Transcript: {args.transcript}")

    # Get video duration
    video_duration = get_video_duration(args.video)
    if video_duration:
        mins = int(video_duration // 60)
        secs = int(video_duration % 60)
        print(f"Duration:   {mins}m {secs}s ({video_duration:.1f}s)")
    else:
        print("Warning: Could not detect video duration. Proceeding with transcript only.")
        video_duration = 0

    # Parse transcript
    print(f"\nParsing transcript...")
    captions = load_transcript(args.transcript, video_duration)
    print(f"Found {len(captions)} caption blocks")

    if not captions:
        print("Error: No captions found in transcript.", file=sys.stderr)
        sys.exit(1)

    # Detect segments
    print(f"Analyzing transcript for optimal clip points...")
    segments = detect_segments(
        captions,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        target_duration=args.target_duration,
        max_segments=args.max_segments,
    )

    if not segments:
        print("No segments detected. Try adjusting duration parameters.")
        sys.exit(0)

    print_segments(segments)

    # Export JSON
    if args.export_json:
        export_json(segments, args.export_json)

    # Export FFmpeg script
    if args.export_script:
        os.makedirs(args.output_dir, exist_ok=True)
        export_ffmpeg_commands(segments, args.video, args.output_dir)

    # Open UI
    if args.open_ui:
        open_ui(args.video, args.transcript, segments)

    # Cut clips
    if not args.preview_only and not args.open_ui:
        os.makedirs(args.output_dir, exist_ok=True)
        print(f"\nCutting {len(segments)} clips to {args.output_dir}/...")
        print(f"Mode: {'re-encode (frame-accurate)' if args.reencode else 'stream copy (fast)'}\n")

        for seg in segments:
            safe_title = re.sub(r'[^\w\s-]', '', seg.title)[:50].strip().replace(' ', '_')
            filename = f"clip_{seg.id:02d}_{safe_title}.{args.format}"
            output_path = os.path.join(args.output_dir, filename)

            print(f"  [{seg.id}/{len(segments)}] Cutting: {seg.title[:50]}")
            print(f"    {format_time(seg.start)} → {format_time(seg.end)} ({seg.duration:.0f}s)")

            success = cut_segment(args.video, seg, output_path, args.format, args.reencode)
            if success:
                print(f"    ✓ Saved: {filename}")
            else:
                print(f"    ✗ Failed: {filename}")

        print(f"\nDone! {len(segments)} clips saved to {args.output_dir}/")


if __name__ == '__main__':
    main()
