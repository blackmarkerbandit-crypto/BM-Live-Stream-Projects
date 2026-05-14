"""
BlackMarker.TV Clip Agent — Database Layer
"""
import sqlite3
import uuid
import time
import os
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "agent.db"
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", Path(__file__).parent / "output"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id              TEXT PRIMARY KEY,
            created_at      INTEGER NOT NULL,
            updated_at      INTEGER NOT NULL,
            status          TEXT NOT NULL DEFAULT 'pending',
            input_type      TEXT NOT NULL,
            input_path      TEXT NOT NULL,
            video_path      TEXT,
            show_name       TEXT NOT NULL DEFAULT '',
            episode         TEXT NOT NULL DEFAULT '',
            whisper_model   TEXT NOT NULL DEFAULT 'base',
            min_duration    INTEGER NOT NULL DEFAULT 45,
            max_duration    INTEGER NOT NULL DEFAULT 90,
            max_clips       INTEGER NOT NULL DEFAULT 10,
            srt_path        TEXT,
            clips_count     INTEGER DEFAULT 0,
            progress        INTEGER DEFAULT 0,
            error_message   TEXT
        );

        CREATE TABLE IF NOT EXISTS clips (
            id                  TEXT PRIMARY KEY,
            job_id              TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            created_at          INTEGER NOT NULL,
            clip_index          INTEGER NOT NULL,
            start_time          REAL NOT NULL,
            end_time            REAL NOT NULL,
            duration            REAL NOT NULL,
            title               TEXT NOT NULL DEFAULT '',
            summary             TEXT NOT NULL DEFAULT '',
            hook_line           TEXT NOT NULL DEFAULT '',
            clip_type           TEXT NOT NULL DEFAULT 'highlight',
            vibe_score          INTEGER NOT NULL DEFAULT 5,
            caption_instagram   TEXT,
            caption_tiktok      TEXT,
            caption_youtube     TEXT,
            video_path          TEXT,
            thumbnail_path      TEXT,
            srt_path            TEXT,
            status              TEXT NOT NULL DEFAULT 'pending',
            error_message       TEXT
        );

        CREATE TABLE IF NOT EXISTS logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            ts          INTEGER NOT NULL,
            level       TEXT NOT NULL DEFAULT 'info',
            stage       TEXT NOT NULL DEFAULT 'general',
            message     TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_logs_job_id ON logs(job_id);
        CREATE INDEX IF NOT EXISTS idx_clips_job_id ON clips(job_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        """)


def create_job(input_type, input_path, show_name, episode="", whisper_model="base",
               min_duration=45, max_duration=90, max_clips=10, srt_path=None):
    job_id = str(uuid.uuid4())
    now = int(time.time())
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO jobs (id, created_at, updated_at, status, input_type, input_path,
               show_name, episode, whisper_model, min_duration, max_duration, max_clips, srt_path)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (job_id, now, now, "pending", input_type, input_path,
             show_name, episode, whisper_model, min_duration, max_duration, max_clips, srt_path),
        )
    return job_id


def get_job(job_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None


def list_jobs():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def update_job(job_id, **kwargs):
    kwargs["updated_at"] = int(time.time())
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [job_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {fields} WHERE id=?", values)


def delete_job(job_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))


def create_clip(job_id, clip_index, start_time, end_time, title="", summary="",
                hook_line="", clip_type="highlight", vibe_score=5,
                caption_instagram=None, caption_tiktok=None, caption_youtube=None):
    clip_id = str(uuid.uuid4())
    now = int(time.time())
    duration = round(end_time - start_time, 2)
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO clips (id, job_id, created_at, clip_index, start_time, end_time,
               duration, title, summary, hook_line, clip_type, vibe_score,
               caption_instagram, caption_tiktok, caption_youtube, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending')""",
            (clip_id, job_id, now, clip_index, start_time, end_time, duration,
             title, summary, hook_line, clip_type, vibe_score,
             caption_instagram, caption_tiktok, caption_youtube),
        )
    return clip_id


def get_clip(clip_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT c.*, j.show_name, j.episode FROM clips c JOIN jobs j ON c.job_id=j.id WHERE c.id=?",
            (clip_id,)
        ).fetchone()
        return dict(row) if row else None


def list_clips(job_id=None, show_name=None, limit=200):
    sql = "SELECT c.*, j.show_name, j.episode FROM clips c JOIN jobs j ON c.job_id=j.id WHERE c.status='done'"
    params = []
    if job_id:
        sql += " AND c.job_id=?"
        params.append(job_id)
    if show_name:
        sql += " AND j.show_name=?"
        params.append(show_name)
    sql += " ORDER BY c.created_at DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def update_clip(clip_id, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [clip_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE clips SET {fields} WHERE id=?", values)


def get_job_clips(job_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM clips WHERE job_id=? ORDER BY clip_index", (job_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_log(job_id, message, level="info", stage="general"):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO logs (job_id, ts, level, stage, message) VALUES (?,?,?,?,?)",
            (job_id, int(time.time()), level, stage, message),
        )


def get_logs(job_id, limit=500):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM logs WHERE job_id=? ORDER BY id DESC LIMIT ?", (job_id, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


def get_stats():
    with get_conn() as conn:
        total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        total_clips = conn.execute("SELECT COUNT(*) FROM clips WHERE status='done'").fetchone()[0]
        week_ago = int(time.time()) - 7 * 86400
        clips_this_week = conn.execute(
            "SELECT COUNT(*) FROM clips WHERE status='done' AND created_at>=?", (week_ago,)
        ).fetchone()[0]
        avg = conn.execute("SELECT AVG(clips_count) FROM jobs WHERE status='done'").fetchone()[0]
        total_dur = conn.execute("SELECT SUM(duration) FROM clips WHERE status='done'").fetchone()[0]
        top_show = conn.execute(
            """SELECT j.show_name, COUNT(*) as cnt FROM clips c JOIN jobs j ON c.job_id=j.id
               WHERE c.status='done' GROUP BY j.show_name ORDER BY cnt DESC LIMIT 1"""
        ).fetchone()
    return {
        "total_jobs": total_jobs, "total_clips": total_clips,
        "clips_this_week": clips_this_week, "avg_clips_per_job": round(avg or 0, 1),
        "most_active_show": top_show[0] if top_show else "—",
        "total_duration_seconds": round(total_dur or 0, 0),
    }


def get_clips_by_show():
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT j.show_name, COUNT(*) as count FROM clips c JOIN jobs j ON c.job_id=j.id
               WHERE c.status='done' GROUP BY j.show_name ORDER BY count DESC"""
        ).fetchall()
        return [{"show": r[0], "count": r[1]} for r in rows]


def get_clips_per_week():
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y-W%W', datetime(created_at,'unixepoch')) as week, COUNT(*) as count
               FROM clips WHERE status='done' GROUP BY week ORDER BY week DESC LIMIT 12"""
        ).fetchall()
        return [{"week": r[0], "count": r[1]} for r in reversed(rows)]
