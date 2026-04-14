"""
BlackMarker.TV Clip Agent — FastAPI Server
Run: python server.py
Then open http://localhost:8000
"""

import asyncio
import json
import os
import time
import shutil
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database as db
import agent as ag

db.init_db()
app = FastAPI(title="BlackMarker.TV Clip Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="clip-agent")
_sse_queues: dict[str, list] = defaultdict(list)
_loop: Optional[asyncio.AbstractEventLoop] = None


@app.on_event("startup")
async def startup():
    global _loop
    _loop = asyncio.get_event_loop()
    for job in db.list_jobs():
        if job["status"] in ("pending", "downloading", "transcribing", "analyzing", "cutting"):
            db.update_job(job["id"], status="error", error_message="Server restarted while job was running")


def emit(job_id: str, payload: dict):
    payload["job_id"] = job_id
    payload["ts"] = int(time.time())
    msg = f"data: {json.dumps(payload)}\n\n"
    for q in list(_sse_queues.get(job_id, [])):
        try:
            _loop.call_soon_threadsafe(q.put_nowait, msg)
        except Exception:
            pass


def make_emitter(job_id: str):
    def _emit(payload: dict):
        emit(job_id, payload)
    return _emit


class JobCreate(BaseModel):
    input_type: str = "file"
    input_path: str
    show_name: str
    episode: str = ""
    whisper_model: str = "base"
    min_duration: int = 45
    max_duration: int = 90
    max_clips: int = 10
    srt_path: Optional[str] = None


@app.post("/api/jobs")
async def create_job(body: JobCreate):
    if body.input_type not in ("file", "youtube"):
        raise HTTPException(400, "input_type must be 'file' or 'youtube'")
    if body.input_type == "file" and not Path(body.input_path).exists():
        raise HTTPException(400, f"File not found: {body.input_path}")
    if not body.show_name.strip():
        raise HTTPException(400, "show_name is required")

    job_id = db.create_job(
        input_type=body.input_type, input_path=body.input_path,
        show_name=body.show_name, episode=body.episode,
        whisper_model=body.whisper_model, min_duration=body.min_duration,
        max_duration=body.max_duration, max_clips=body.max_clips, srt_path=body.srt_path,
    )
    emitter = make_emitter(job_id)
    asyncio.get_event_loop().run_in_executor(executor, ag.run_job, job_id, emitter)
    return {"job_id": job_id}


@app.get("/api/jobs")
async def list_jobs():
    jobs = db.list_jobs()
    for job in jobs:
        job["clips"] = db.get_job_clips(job["id"])
    return jobs


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job["clips"] = db.get_job_clips(job_id)
    job["logs"] = db.get_logs(job_id)
    return job


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    db.delete_job(job_id)
    job_dir = ag.OUTPUT_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)
    return {"deleted": True}


@app.get("/api/clips")
async def list_clips(job_id: Optional[str] = None, show_name: Optional[str] = None):
    return db.list_clips(job_id=job_id, show_name=show_name)


@app.get("/api/clips/{clip_id}")
async def get_clip(clip_id: str):
    clip = db.get_clip(clip_id)
    if not clip:
        raise HTTPException(404, "Clip not found")
    return clip


@app.get("/api/clips/{clip_id}/download")
async def download_clip(clip_id: str):
    clip = db.get_clip(clip_id)
    if not clip or not clip.get("video_path"):
        raise HTTPException(404, "Clip file not found")
    p = Path(clip["video_path"])
    if not p.exists():
        raise HTTPException(404, "File missing from disk")
    return FileResponse(str(p), media_type="video/mp4", filename=p.name,
                        headers={"Content-Disposition": f'attachment; filename="{p.name}"'})


@app.get("/api/clips/{clip_id}/thumbnail")
async def clip_thumbnail(clip_id: str):
    clip = db.get_clip(clip_id)
    if not clip or not clip.get("thumbnail_path"):
        raise HTTPException(404, "Thumbnail not found")
    p = Path(clip["thumbnail_path"])
    if not p.exists():
        raise HTTPException(404, "Thumbnail missing from disk")
    return FileResponse(str(p), media_type="image/jpeg")


@app.get("/api/jobs/{job_id}/stream")
async def stream_job(job_id: str):
    q: asyncio.Queue = asyncio.Queue(maxsize=500)
    _sse_queues[job_id].append(q)

    async def event_generator():
        # Replay existing logs for reconnecting clients
        for entry in db.get_logs(job_id):
            msg = {"type": "log", "level": entry["level"], "stage": entry["stage"],
                   "message": entry["message"], "job_id": job_id, "ts": entry["ts"]}
            yield f"data: {json.dumps(msg)}\n\n"

        job = db.get_job(job_id)
        if job and job["status"] in ("done", "error"):
            payload = {"type": "job_done" if job["status"] == "done" else "job_error",
                       "job_id": job_id, "status": job["status"], "ts": int(time.time())}
            yield f"data: {json.dumps(payload)}\n\n"
            _sse_queues[job_id].remove(q)
            return

        try:
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield msg
                    data = json.loads(msg[5:])
                    if data.get("type") in ("job_done", "job_error"):
                        break
                except asyncio.TimeoutError:
                    hb = {"type": "heartbeat", "job_id": job_id, "ts": int(time.time())}
                    yield f"data: {json.dumps(hb)}\n\n"
        finally:
            if q in _sse_queues.get(job_id, []):
                _sse_queues[job_id].remove(q)

    return StreamingResponse(
        event_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@app.get("/api/reports/stats")
async def report_stats():
    return db.get_stats()


@app.get("/api/reports/clips-by-show")
async def report_by_show():
    return db.get_clips_by_show()


@app.get("/api/reports/clips-per-week")
async def report_per_week():
    return db.get_clips_per_week()


@app.get("/api/shows")
async def list_shows():
    return ag.SHOWS


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_path = Path(__file__).parent / "dashboard.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import uvicorn
    print("BlackMarker.TV Clip Agent")
    print(f"Output directory: {ag.OUTPUT_DIR}")
    print("Open http://localhost:8000 in your browser")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
