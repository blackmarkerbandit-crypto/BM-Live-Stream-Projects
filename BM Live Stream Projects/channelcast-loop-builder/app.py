"""
ChannelCast Loop Builder -- local web app.

Run:  python app.py     (then open http://127.0.0.1:8765 )

Everything talks to ChannelCast directly with your token, so once this is
running you can view, edit, generate and push loops without spending Claude
tokens.
"""

import os
import json
import time
import random
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

# streaming responses must not be buffered, or progress bars sit blank until the end
NDJSON_HEADERS = {"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}

from channelcast_client import ChannelcastClient, ChannelcastError
import scheduler

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
LIBRARY_PATH = os.path.join(HERE, "library.json")
USAGE_PATH = os.path.join(HERE, "usage.json")
PLAYLISTS_PATH = os.path.join(HERE, "playlists_cache.json")
OVERRIDES_PATH = os.path.join(HERE, "overrides.json")  # mediaId -> type (manual reclassify / archive)
IMPORTED_S3_PATH = os.path.join(HERE, "imported_s3.json")  # list of S3 keys already imported
JOB_PATH = os.path.join(HERE, "job_state.json")  # in-flight loop rebuild, for resume-after-crash

client = ChannelcastClient(CONFIG["base_url"], CONFIG["token"])
app = FastAPI(title="ChannelCast Loop Builder")


# ---- small json-file helpers ---------------------------------------------
def load_json(path, default):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return default


def save_json(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), indent=2)


# ---- classification -------------------------------------------------------
SHOW_PREFIXES = tuple(CONFIG.get(
    "show_prefixes", ["TWI ", "BMTV ", "FTR ", "CUDI ", "TT ", "TAP "]))


def classify(title: str) -> str:
    t = title
    if t.startswith("MV "):
        return "mv"
    if (t.startswith("LP ") or t.startswith("LI ") or t.startswith("Performance ")
            or ("Showcase" in t and ("Performance" in t or "Interview" in t))
            or "CloseOutParty Interview" in t or "RoundsOn7th Interview" in t
            or "RoundsOn7th Interviews" in t):
        return "special"
    if t.startswith(SHOW_PREFIXES):        # full-length programs (openers)
        return "show"
    if t.startswith("IA ") or "Promo" in t or "LoopVideo" in t:
        return "promo"
    return "other"


SEARCH_TERMS = (
    [f"MV {c}" for c in "abcdefghijklmnopqrstuvwxyz0123456789"]
    + ["MV ", "LP ", "LI ", "Performance ", "Showcase", "CloseOutParty",
       "RoundsOn7th", "Interview", "IA ", "Promo"]
    + [p.strip() + " " for p in SHOW_PREFIXES]
)


# ---- routes ---------------------------------------------------------------
@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "index.html"))


@app.get("/api/config")
def get_config():
    return {
        "channel_id": CONFIG["channel_id"],
        "channel_name": CONFIG.get("channel_name", ""),
        "excluded_artists": CONFIG.get("excluded_artists", []),
        "target_seconds": CONFIG.get("target_seconds", 21600),
        "gap_seconds": CONFIG.get("gap_seconds", 7200),
        "intro_media_id": CONFIG.get("intro_media_id", ""),
    }


@app.get("/api/channels")
def channels():
    return client.list_channels()


@app.get("/api/playlists")
def playlists(channelId: str = None):
    return client.list_playlists(channelId or CONFIG["channel_id"])


@app.get("/api/playlist/{playlist_id}/items")
def playlist_items(playlist_id: str):
    data = client.list_playlist_items(playlist_id)
    items = data.get("items", data if isinstance(data, list) else [])
    total = sum(i.get("durationSeconds", 0) for i in items)
    return {"items": items, "total_seconds": total, "count": len(items)}


@app.post("/api/sync-playlists-stream")
async def sync_playlists_stream():
    """Pull every playlist and its items, cache them, and build a
    media -> [playlists it appears in] usage index. Streams progress."""
    async def gen():
        pls = await run_in_threadpool(client.list_playlists, CONFIG["channel_id"])
        pls = pls.get("playlists", pls)
        n = len(pls)
        out, usage = [], {}
        for i, p in enumerate(pls):
            items = []
            data = await run_in_threadpool(client.list_playlist_items, p["id"])
            for it in data.get("items", []):
                items.append({
                    "mediaId": it["mediaId"], "title": it["title"],
                    "playlistItemId": it["playlistItemId"],
                    "durationSeconds": it.get("durationSeconds", 0),
                    "playsAtSeconds": it.get("playsAtSeconds", 0),
                })
                usage.setdefault(it["mediaId"], []).append({
                    "playlistId": p["id"], "playlistName": p["name"],
                    "playlistItemId": it["playlistItemId"],
                })
            total = sum(x["durationSeconds"] for x in items)
            out.append({"id": p["id"], "name": p["name"],
                        "count": len(items), "total_seconds": total, "items": items})
            yield json.dumps({"i": i + 1, "n": n, "name": p["name"],
                              "count": len(items)}) + "\n"
        save_json(PLAYLISTS_PATH, {"synced_at": time.time(),
                                   "playlists": out, "usage": usage})
        yield json.dumps({"done": True, "playlists": len(out),
                          "with_items": sum(1 for p in out if p["count"] > 0)}) + "\n"
    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=NDJSON_HEADERS)


@app.get("/api/playlists-cache")
def playlists_cache():
    return load_json(PLAYLISTS_PATH, {"synced_at": None, "playlists": [], "usage": {}})


def _sync_collect(seen, term):
    try:
        data = client.list_media(term)
    except ChannelcastError:
        return
    for m in data.get("media", []):
        mid = m["id"]
        if mid in seen:
            continue
        # ChannelCast now keeps the naming-convention `filename` separate from the
        # viewer-facing `title`. Everything here -- classification, artist spacing,
        # show prefixes, exclusions -- keys off the convention, so `title` in our
        # library IS the filename; the display name rides along separately.
        # Without this, a friendly title like "Tito Puente, Jr | Can You Dig It??"
        # classifies as "other" and silently drops out of the show/opener logic.
        name = m.get("filename") or m["title"]
        kind = classify(name)
        entry = {"id": mid, "title": name, "displayTitle": m["title"],
                 "duration": m.get("durationSeconds", 0), "kind": kind}
        if kind == "mv":
            entry["artists"] = scheduler.artist_tokens(name)
        seen[mid] = entry


@app.post("/api/sync-library")
def sync_library():
    seen = {}
    for term in SEARCH_TERMS:
        _sync_collect(seen, term)
    library = list(seen.values())
    save_json(LIBRARY_PATH, {"synced_at": time.time(), "items": library})
    return summarize(library)


@app.post("/api/sync-library-stream")
async def sync_library_stream():
    """Same sync, but streams one NDJSON progress line per search term so the
    browser can show a live progress bar."""
    async def gen():
        seen = {}
        n = len(SEARCH_TERMS)
        for i, term in enumerate(SEARCH_TERMS):
            await run_in_threadpool(_sync_collect, seen, term)
            yield json.dumps({"i": i + 1, "n": n, "term": term.strip(),
                              "items": len(seen)}) + "\n"
        library = list(seen.values())
        save_json(LIBRARY_PATH, {"synced_at": time.time(), "items": library})
        yield json.dumps({"done": True, **summarize(library)}) + "\n"
    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=NDJSON_HEADERS)


def summarize(library):
    by_kind = {}
    for m in library:
        by_kind[m["kind"]] = by_kind.get(m["kind"], 0) + 1
    return {"total": len(library), "by_kind": by_kind}


def apply_overrides(items):
    """Return items with manual type overrides applied (and an 'overridden' flag).
    Mutates the passed dicts, which are freshly parsed each request."""
    ov = load_json(OVERRIDES_PATH, {})
    for m in items:
        k = ov.get(m["id"])
        if k:
            m["kind"] = k
            m["overridden"] = True
            if k == "mv" and "artists" not in m:
                m["artists"] = scheduler.artist_tokens(m["title"])
    return items


@app.get("/api/library")
def get_library():
    lib = load_json(LIBRARY_PATH, {"items": []})
    items = apply_overrides(lib.get("items", []))
    return {"synced_at": lib.get("synced_at"), **summarize(items), "items": items}


class OverrideReq(BaseModel):
    mediaId: str
    type: str  # mv|special|promo|show|other|archive ; "" or "clear" removes the override


@app.get("/api/overrides")
def get_overrides():
    return load_json(OVERRIDES_PATH, {})


@app.post("/api/override")
def set_override(req: OverrideReq):
    ov = load_json(OVERRIDES_PATH, {})
    if req.type in ("", "clear", "auto", None):
        ov.pop(req.mediaId, None)
    else:
        ov[req.mediaId] = req.type
    save_json(OVERRIDES_PATH, ov)
    return {"ok": True, "count": len(ov)}


class GenerateReq(BaseModel):
    channelId: Optional[str] = None
    targetHours: float = 6.0
    gapHours: float = 2.0
    numSpecials: int = 3
    reshuffle: bool = True
    avoidPlaylistIds: list = []
    openers: list = []          # [{mediaId, hour}, ...] - full shows at set times
    seed: Optional[int] = None
    promoEvery: int = 8


def build_library_pools():
    lib = load_json(LIBRARY_PATH, {"items": []}).get("items", [])
    if not lib:
        raise HTTPException(400, "Library is empty -- click 'Sync Library' first.")
    lib = apply_overrides(lib)                        # manual type overrides
    lib = [m for m in lib if m["kind"] != "archive"]  # drop archived (out of rotation)
    excl = [a.lower() for a in CONFIG.get("excluded_artists", [])]
    by_id = {m["id"]: m for m in lib}
    intro_id = CONFIG["intro_media_id"]
    mv_pool = [m for m in lib if m["kind"] == "mv"]
    promo_pool = [m for m in lib if m["kind"] == "promo" and m["id"] != intro_id]
    special_pool = [m for m in lib if m["kind"] == "special"
                    and not scheduler.is_excluded(m["title"], excl)]
    intro = by_id.get(intro_id)
    if not intro:
        raise HTTPException(400, "Intro plug clip not found in library; re-sync.")
    intro = {"id": intro["id"], "title": intro["title"], "duration": intro["duration"]}
    return by_id, mv_pool, promo_pool, special_pool, intro


def generate_sequence(openers_spec, num_specials=3, reshuffle=True, avoid_ids=None,
                      seed=None, target_hours=6.0, gap_hours=2.0, promo_every=8,
                      must_ids=None, keep_special_ids=None):
    """Shared loop builder used by /api/generate, the show-update workflow and the
    music-drop workflow.

    must_ids        : music videos that MUST land in this loop, spread across it
                      (a new-music drop assigns these per loop).
    keep_special_ids: reuse this loop's existing performances/interviews instead of
                      drawing new ones, so a regeneration only refreshes the music.
    """
    by_id, mv_pool, promo_pool, special_pool, intro = build_library_pools()
    avoid = set(avoid_ids or [])
    depleted = False
    if keep_special_ids:
        specials = [{"id": by_id[s]["id"], "title": by_id[s]["title"],
                     "duration": by_id[s]["duration"]}
                    for s in keep_special_ids if s in by_id]
    else:
        usage = load_json(USAGE_PATH, {"specials": []})
        used_specials = set(usage.get("specials", []))
        available = [s for s in special_pool if s["id"] not in used_specials]
        if len(available) < num_specials:
            depleted = True
            available = list(special_pool)
        random.Random(seed or int(time.time())).shuffle(available)
        chosen = available[:num_specials]
        specials = [{"id": s["id"], "title": s["title"], "duration": s["duration"]}
                    for s in chosen]
    must_mvs = [m for m in mv_pool if m["id"] in set(must_ids or [])]
    openers = []
    for spec in (openers_spec or []):
        mid = spec.get("mediaId")
        if mid and mid in by_id:
            o = by_id[mid]
            openers.append({"id": o["id"], "title": o["title"], "duration": o["duration"],
                            "hour": float(spec.get("hour", 0) or 0)})
    floor = int(target_hours * 3600)
    seq, report = scheduler.build_loop(
        mv_pool, promo_pool, intro, specials,
        floor=floor, ceil=floor + 10, gap=int(gap_hours * 3600),
        excluded_artists=CONFIG.get("excluded_artists", []),
        seed=seed if seed is not None else int(time.time()),
        openers=openers, avoid_mv_ids=avoid, promo_every=promo_every,
        special_gap=CONFIG.get("special_gap_seconds", 3600),
        must_mvs=must_mvs)
    ts = 0
    for s in seq:
        s["playsAtSeconds"] = ts
        ts += s["duration"]
    return {"sequence": seq, "report": report, "specials_depleted_reset": depleted,
            "media_ids": [s["id"] for s in seq],
            "chosen_special_ids": [s["id"] for s in specials]}


@app.post("/api/generate")
def generate(req: GenerateReq):
    avoid = set()
    if not req.reshuffle:
        for pid in req.avoidPlaylistIds:
            for it in client.list_playlist_items(pid).get("items", []):
                avoid.add(it["mediaId"])
    return generate_sequence(req.openers, req.numSpecials, req.reshuffle, avoid,
                             req.seed, req.targetHours, req.gapHours, req.promoEvery)


class PushReq(BaseModel):
    playlistId: str
    mediaIds: list
    specialIds: list = []
    openerMediaId: Optional[str] = None


@app.post("/api/push")
def push(req: PushReq):
    added = 0
    for mid in req.mediaIds:
        client.add_media_to_playlist(req.playlistId, mid)
        added += 1
    # record specials used so the next generate won't repeat them
    usage = load_json(USAGE_PATH, {"specials": []})
    used = set(usage.get("specials", []))
    used.update(req.specialIds)
    save_json(USAGE_PATH, {"specials": list(used)})
    return {"added": added}


class PushOneReq(BaseModel):
    playlistId: str
    mediaId: str


@app.post("/api/push-one")
def push_one(req: PushOneReq):
    """Add a single item -- lets the browser drive a progress bar."""
    client.add_media_to_playlist(req.playlistId, req.mediaId)
    return {"ok": True}


class RecordSpecialsReq(BaseModel):
    specialIds: list = []


@app.post("/api/record-specials")
def record_specials(req: RecordSpecialsReq):
    usage = load_json(USAGE_PATH, {"specials": []})
    used = set(usage.get("specials", []))
    used.update(req.specialIds)
    save_json(USAGE_PATH, {"specials": list(used)})
    return {"recorded": len(req.specialIds)}


class ReorderReq(BaseModel):
    playlistId: str
    orderedMediaIds: list


@app.post("/api/reorder")
def reorder(req: ReorderReq):
    # Fast path only works when every media id is unique. Real loops repeat the
    # intro/promos, which ChannelCast's reorder rejects -- use /api/reorder-rebuild.
    return client.reorder_playlist(req.playlistId, req.orderedMediaIds)


@app.post("/api/reorder-rebuild")
async def reorder_rebuild(req: ReorderReq):
    """Position-based reorder that works even when media repeat: append every
    item in the desired order, then delete the originals. Order-safe -- if it's
    interrupted nothing is lost (worst case leaves recoverable duplicates).
    Streams progress."""
    async def gen():
        cur = await run_in_threadpool(client.list_playlist_items, req.playlistId)
        old_ids = [it["playlistItemId"] for it in cur.get("items", [])]
        new = req.orderedMediaIds
        total = len(new) + len(old_ids)
        done = 0
        for mid in new:
            await run_in_threadpool(client.add_media_to_playlist, req.playlistId, mid)
            done += 1
            yield json.dumps({"phase": "add", "done": done, "total": total}) + "\n"
        for iid in old_ids:
            await run_in_threadpool(client.remove_playlist_item, iid)
            done += 1
            yield json.dumps({"phase": "remove", "done": done, "total": total}) + "\n"
        yield json.dumps({"done": True, "items": len(new)}) + "\n"
    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=NDJSON_HEADERS)


class RemoveReq(BaseModel):
    playlistItemId: str


@app.post("/api/remove")
def remove(req: RemoveReq):
    return client.remove_playlist_item(req.playlistItemId)


class AddMediaReq(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    filename: Optional[str] = None      # naming-convention key; defaults to title


@app.post("/api/add-media")
def add_media(req: AddMediaReq):
    res = client.add_media(req.title, req.url, req.description, req.filename)
    return res


# ---- S3 auto-import -------------------------------------------------------
import urllib.parse

_s3_client = None


def s3():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3", region_name=CONFIG.get("s3_region") or "us-east-1")
    return _s3_client


def s3_public_url(bucket, region, key):
    q = urllib.parse.quote(key)
    if region in (None, "", "us-east-1"):
        return f"https://{bucket}.s3.amazonaws.com/{q}"
    return f"https://{bucket}.s3.{region}.amazonaws.com/{q}"


def clean_title(key):
    name = key.rsplit("/", 1)[-1]
    for ext in CONFIG.get("s3_extensions", [".mp4", ".m3u8"]):
        if name.lower().endswith(ext):
            name = name[: -len(ext)]
            break
    # Match ChannelCast's manual-import behaviour: dashes become spaces
    # (confirmed against 978/1118 existing titles), then collapse whitespace.
    return " ".join(name.replace("-", " ").split())


@app.get("/api/s3/list")
def s3_list():
    bucket = CONFIG.get("s3_bucket", "")
    if not bucket:
        raise HTTPException(400, "No S3 bucket set. Add 's3_bucket' to config.json.")
    region = CONFIG.get("s3_region") or "us-east-1"
    prefix = CONFIG.get("s3_prefix", "") or ""
    exts = tuple(e.lower() for e in CONFIG.get("s3_extensions", [".mp4", ".m3u8"]))
    imported = set(load_json(IMPORTED_S3_PATH, []))
    # existing library titles, to also flag things already in ChannelCast
    lib_titles = {m["title"].lower() for m in load_json(LIBRARY_PATH, {"items": []}).get("items", [])}
    try:
        paginator = s3().get_paginator("list_objects_v2")
        objs = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for o in page.get("Contents", []):
                key = o["Key"]
                if key.endswith("/") or not key.lower().endswith(exts):
                    continue
                title = clean_title(key)
                objs.append({
                    "key": key, "title": title,
                    "size": o.get("Size", 0),
                    "lastModified": o["LastModified"].isoformat() if o.get("LastModified") else "",
                    "url": s3_public_url(bucket, region, key),
                    "alreadyImported": key in imported or title.lower() in lib_titles,
                })
    except Exception as e:
        raise HTTPException(400, f"S3 error: {e}")
    objs.sort(key=lambda x: x["lastModified"], reverse=True)
    return {"bucket": bucket, "prefix": prefix, "count": len(objs), "objects": objs}


class S3ImportReq(BaseModel):
    items: list  # [{key, title, url}]


@app.post("/api/s3/import")
async def s3_import(req: S3ImportReq):
    async def gen():
        imported = set(load_json(IMPORTED_S3_PATH, []))
        n = len(req.items)
        ok = 0
        errors = []
        for i, it in enumerate(req.items):
            title = it.get("title") or clean_title(it["key"])
            url = it.get("url")
            err = None
            try:
                # title and filename both start as the naming-convention name;
                # a friendlier display title can be set later in ChannelCast.
                res = await run_in_threadpool(client.add_media, title, url, None, title)
                mid = res.get("mediaId") or res.get("id")
                if mid:
                    ok += 1
                    imported.add(it["key"])
                else:
                    err = f"no media id in response: {res}"
            except Exception as e:
                err = str(e)
            if err:
                errors.append({"title": title, "error": err})
            yield json.dumps({"i": i + 1, "n": n, "title": title, "error": err}) + "\n"
        save_json(IMPORTED_S3_PATH, list(imported))
        yield json.dumps({"done": True, "imported": ok, "total": n,
                          "failed": len(errors), "errors": errors[:10]}) + "\n"
    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=NDJSON_HEADERS)


# ---- resumable rebuild jobs -----------------------------------------------
# Rebuilding a loop means "append the whole new order, then delete the old
# items" -- 200+ API calls that used to stream straight through the browser. If
# that stream died halfway (tab closed, network blip, server restart) the loop
# was left holding old AND new content, and nothing remembered where it stopped.
#
# So every rebuild is now a job checkpointed to disk after each individual API
# call. A job records, per loop: the exact generated order, how many of those
# items are already added, the exact old playlist-item ids captured before we
# started, and how many are already removed. Resuming replays only what's left,
# which makes an interrupted run recoverable instead of destructive.

def load_job():
    return load_json(JOB_PATH, None)


def save_job(job):
    job["updated"] = time.time()
    save_json(JOB_PATH, job)


def clear_job():
    try:
        os.remove(JOB_PATH)
    except OSError:
        pass


def job_done(job):
    return bool(job) and all(l["status"] == "done" for l in job["loops"])


def job_progress(job):
    loops = job["loops"]
    calls_total = sum(len(l.get("mediaIds") or []) + len(l.get("oldItemIds") or [])
                      for l in loops)
    calls_done = sum(l.get("added", 0) + l.get("removed", 0) for l in loops)
    return {
        "id": job["id"], "kind": job["kind"], "label": job.get("label", ""),
        "loopsDone": sum(1 for l in loops if l["status"] == "done"),
        "loopsTotal": len(loops),
        "callsDone": calls_done, "callsTotal": calls_total,
        "remaining": [l["loop"] for l in loops if l["status"] != "done"],
        "updated": job.get("updated"),
        "complete": job_done(job),
    }


def new_job(kind, label, loops):
    """loops: [{loop, playlistId, gen:{openers,numSpecials,mustIds,keepFromLive}}]"""
    for l in loops:
        l.setdefault("status", "pending")
        l.setdefault("added", 0)
        l.setdefault("removed", 0)
    job = {"id": "%d" % int(time.time()), "kind": kind, "label": label,
           "created": time.time(), "loops": loops}
    save_job(job)
    return job


async def run_job_stream(job):
    """Drive a rebuild job to completion, yielding NDJSON progress lines.

    Safe to call on a partially-finished job: finished loops are skipped and a
    half-done loop picks up at the exact item it stopped on.
    """
    n = len(job["loops"])
    for li, L in enumerate(job["loops"]):
        name, pid = L["loop"], L["playlistId"]
        if L["status"] == "done":
            continue

        # ---- plan this loop (only once; a resume reuses the frozen order) ----
        if L["status"] == "pending":
            yield json.dumps({"phase": "generate", "loop": name,
                              "i": li + 1, "n": n}) + "\n"
            g = L.get("gen", {})
            keep = g.get("keepSpecialIds")
            cur = await run_in_threadpool(client.list_playlist_items, pid)
            items = cur.get("items", [])
            if g.get("keepFromLive"):
                keep = await run_in_threadpool(_specials_in, items)
            openers = g.get("openers") or []
            if g.get("openersFromLive"):     # keep whatever shows the loop already pins
                openers = [{"mediaId": s["mediaId"], "hour": s["hour"]}
                           for s in await run_in_threadpool(_shows_in, items)]
            res = await run_in_threadpool(
                generate_sequence, openers,
                num_specials=g.get("numSpecials", 3), reshuffle=True,
                must_ids=g.get("mustIds"), keep_special_ids=keep)
            L["mediaIds"] = res["media_ids"]
            L["oldItemIds"] = [it["playlistItemId"] for it in items]
            L["added"] = L["removed"] = 0
            L["totalSeconds"] = res["report"]["total_seconds"]
            L["violations"] = len(res["report"].get("violations", []))
            L["specialIds"] = res["chosen_special_ids"]
            L["unplaced"] = res["report"].get("must_unplaced", [])
            L["status"] = "writing"
            await run_in_threadpool(save_job, job)

        total = len(L["mediaIds"]) + len(L["oldItemIds"])

        # ---- write the new order --------------------------------------------
        if L["status"] == "writing":
            ids = L["mediaIds"]
            while L["added"] < len(ids):
                await run_in_threadpool(client.add_media_to_playlist, pid, ids[L["added"]])
                L["added"] += 1
                await run_in_threadpool(save_job, job)
                yield json.dumps({"phase": "write", "loop": name, "i": li + 1, "n": n,
                                  "done": L["added"] + L["removed"], "total": total}) + "\n"
            L["status"] = "clearing"
            await run_in_threadpool(save_job, job)

        # ---- drop the old items ---------------------------------------------
        if L["status"] == "clearing":
            olds = L["oldItemIds"]
            while L["removed"] < len(olds):
                try:
                    await run_in_threadpool(client.remove_playlist_item, olds[L["removed"]])
                except ChannelcastError:
                    pass          # already gone (e.g. removed before a crash) -- fine
                L["removed"] += 1
                await run_in_threadpool(save_job, job)
                yield json.dumps({"phase": "clear", "loop": name, "i": li + 1, "n": n,
                                  "done": L["added"] + L["removed"], "total": total}) + "\n"
            usage = load_json(USAGE_PATH, {"specials": []})
            used = set(usage.get("specials", []))
            used.update(L.get("specialIds") or [])
            save_json(USAGE_PATH, {"specials": list(used)})
            L["status"] = "done"
            await run_in_threadpool(save_job, job)
            yield json.dumps({"phase": "loopdone", "loop": name,
                              "total_seconds": L.get("totalSeconds"),
                              "violations": L.get("violations", 0)}) + "\n"

    unplaced = [{"loop": l["loop"], "title": u["title"]}
                for l in job["loops"] for u in (l.get("unplaced") or [])]
    await run_in_threadpool(clear_job)
    yield json.dumps({"done": True, "loops": n, "unplaced": unplaced}) + "\n"


@app.get("/api/job")
def get_job():
    """Any unfinished rebuild, so the UI can offer to resume it."""
    job = load_job()
    if not job or job_done(job):
        return {"job": None}
    return {"job": job_progress(job)}


@app.post("/api/job/clear")
def post_job_clear():
    clear_job()
    return {"ok": True}


@app.post("/api/job/resume")
async def post_job_resume():
    job = load_job()
    if not job or job_done(job):
        raise HTTPException(400, "No unfinished job to resume.")
    return StreamingResponse(run_job_stream(job), media_type="application/x-ndjson",
                             headers=NDJSON_HEADERS)


# ---- show-update workflows ------------------------------------------------
# Each show defines where a new episode lands and how older ones cascade.
# new_loops: {loop, hour} the new episode is placed at.
# cascade:   {from, to, hour} the from-loop's show-at-hour moves to the to-loop.
# Any OTHER shows already on an affected loop are preserved at their own hours.
SHOW_WORKFLOWS = {
    "TWI": {"label": "The Weekly Interrupt", "prefix": "TWI ",
            "new_loops": [{"loop": "Friday Loop 4", "hour": 0},
                          {"loop": "Tuesday Loop 4", "hour": 0}],
            "cascade": [{"from": "Tuesday Loop 4", "to": "Monday Loop 4", "hour": 0},
                        {"from": "Monday Loop 4", "to": "Sunday Loop 4", "hour": 0},
                        {"from": "Sunday Loop 4", "to": "Saturday Loop 4", "hour": 0}]},
    "FTR": {"label": "For The Record", "prefix": "FTR ",
            "new_loops": [{"loop": "Wednesday Loop 4", "hour": 0}], "cascade": []},
    "TAP": {"label": "The Alien Podcast", "prefix": "TAP ",
            "new_loops": [{"loop": "Thursday Loop 4", "hour": 0}], "cascade": []},
    "TT": {"label": "Talking Tipsy", "prefix": "TT ",
           "new_loops": [{"loop": "Sunday Loop 4", "hour": 2}], "cascade": []},
    "CUDI": {"label": "Can You Dig It!?", "prefix": "CUDI ",
             "new_loops": [{"loop": "Sunday Loop 3", "hour": 0}],
             "cascade": [{"from": "Sunday Loop 3", "to": "Saturday Loop 3", "hour": 0}]},
}

SHOW_PREFIXES_T = None


def _show_prefixes():
    return tuple(CONFIG.get("show_prefixes", ["TWI ", "BMTV ", "FTR ", "CUDI ", "TT ", "TAP "]))


def _loop_map():
    pls = client.list_playlists(CONFIG["channel_id"]).get("playlists", [])
    return {p["name"]: p for p in pls}


def _shows_in(items):
    """All full-show opener items in a loop, with their inferred hour mark.

    Matches on the library's naming-convention name rather than the playlist
    item's title -- playlist items carry the viewer-facing title, which may no
    longer start with "TWI "/"CUDI " at all.
    """
    lib = load_json(LIBRARY_PATH, {"items": []}).get("items", [])
    names = {m["id"]: m["title"] for m in lib}
    out = []
    for it in items:
        name = names.get(it["mediaId"], it["title"])
        if name.startswith(_show_prefixes()):
            out.append({"mediaId": it["mediaId"], "title": name,
                        "hour": round(it.get("playsAtSeconds", 0) / 3600)})
    return out


def _match(shows, prefix, hour):
    for s in shows:
        if s["title"].startswith(prefix) and s["hour"] == hour:
            return s
    return None


def build_show_plan(show_key, new_media_id=None):
    wf = SHOW_WORKFLOWS.get(show_key)
    if not wf:
        raise HTTPException(400, f"Unknown show '{show_key}'")
    prefix = wf["prefix"]
    lib = apply_overrides(load_json(LIBRARY_PATH, {"items": []}).get("items", []))
    by_id = {m["id"]: m for m in lib}
    episodes = sorted([m for m in lib if m["title"].startswith(prefix)],
                      key=lambda m: m["id"], reverse=True)
    if not episodes:
        raise HTTPException(400, f"No '{prefix}' shows in the library -- sync first.")
    new_show = by_id.get(new_media_id) if new_media_id else episodes[0]
    if not new_show:
        new_show = episodes[0]

    loops = _loop_map()
    involved = {nl["loop"] for nl in wf["new_loops"]} | \
        {c["from"] for c in wf["cascade"]} | {c["to"] for c in wf["cascade"]}
    shows_by = {}
    for name in involved:
        if name not in loops:
            raise HTTPException(400, f"Loop '{name}' not found on the channel.")
        shows_by[name] = _shows_in(client.list_playlist_items(loops[name]["id"]).get("items", []))

    # what each affected loop should have at the workflow's hour (snapshot up front)
    incoming = {}   # loop -> {"mediaId","title","hour"}
    for nl in wf["new_loops"]:
        incoming[nl["loop"]] = {"mediaId": new_show["id"], "title": new_show["title"], "hour": nl["hour"]}
    for c in wf["cascade"]:
        src = _match(shows_by[c["from"]], prefix, c["hour"])
        if src:
            incoming[c["to"]] = {"mediaId": src["mediaId"], "title": src["title"], "hour": c["hour"]}

    from_loops = {(c["from"], c["hour"]) for c in wf["cascade"]}
    removed = []
    plan = []
    for name in sorted(incoming.keys()):
        inc = incoming[name]
        replaced = _match(shows_by[name], prefix, inc["hour"])
        if replaced and (name, inc["hour"]) not in from_loops:
            removed.append(replaced["title"])
        # Never keep a second copy of the show being placed. A rebuild that dies
        # partway leaves the new episode already on the loop; without this guard a
        # re-run "preserves" that copy AND adds the incoming one, scheduling the
        # same show twice. This is what makes re-running after a failure safe.
        preserved = [s for s in shows_by[name]
                     if s["mediaId"] != inc["mediaId"]
                     and not (replaced and s["mediaId"] == replaced["mediaId"]
                              and s["hour"] == replaced["hour"])]
        openers = [{"mediaId": s["mediaId"], "hour": s["hour"]} for s in preserved]
        openers.append({"mediaId": inc["mediaId"], "hour": inc["hour"]})
        seen_op = set()                      # belt-and-braces: unique media per loop
        openers = [o for o in openers
                   if not (o["mediaId"] in seen_op or seen_op.add(o["mediaId"]))]
        plan.append({
            "loop": name,
            "hour": inc["hour"],
            "replaced": replaced["title"] if replaced else None,
            "incoming": inc["title"],
            "preserved": [{"title": s["title"], "hour": s["hour"]} for s in preserved],
            "openers": openers,
        })
    return {"show": show_key, "label": wf["label"],
            "newShow": {"id": new_show["id"], "title": new_show["title"], "duration": new_show["duration"]},
            "newShowOptions": [{"id": m["id"], "title": m["title"]} for m in episodes[:25]],
            "removed": [r for r in removed if r],
            "plan": plan}


@app.get("/api/show-update/preview")
def show_update_preview(show: str = "TWI", newMediaId: str = None):
    return build_show_plan(show, newMediaId)


@app.get("/api/show-update/shows")
def show_update_shows():
    return [{"key": k, "label": v["label"]} for k, v in SHOW_WORKFLOWS.items()]


class ShowUpdateReq(BaseModel):
    show: str = "TWI"
    newMediaId: Optional[str] = None


@app.post("/api/show-update/execute")
async def show_update_execute(req: ShowUpdateReq):
    plan = await run_in_threadpool(build_show_plan, req.show, req.newMediaId)  # snapshot up front
    loops = await run_in_threadpool(_loop_map)
    job = new_job("show-update",
                  "%s -> %s" % (plan["label"], plan["newShow"]["title"]),
                  [{"loop": e["loop"], "playlistId": loops[e["loop"]]["id"],
                    "gen": {"openers": e["openers"], "numSpecials": 3}}
                   for e in plan["plan"]])
    return StreamingResponse(run_job_stream(job), media_type="application/x-ndjson",
                             headers=NDJSON_HEADERS)


# --- Music drop -------------------------------------------------------------
# Spreads a batch of freshly imported music videos across the whole week. Each
# new video plays once a day (7x/week) and rotates loop slots as the week goes
# on -- video i lands on loop (i + day) % 4 -- so it never plays at the same
# point of the schedule twice. Every touched loop is regenerated with a fresh
# music shuffle around its EXISTING show openers and performances/interviews, so
# only the music changes.
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LOOPS_PER_DAY = 4


def _week_loops():
    loops = _loop_map()
    out = []
    for day in DAY_ORDER:
        for n in range(1, LOOPS_PER_DAY + 1):
            name = f"{day} Loop {n}"
            if name in loops:
                out.append({"day": day, "num": n, "name": name, "id": loops[name]["id"]})
    return out


@app.get("/api/music-drop/candidates")
def music_drop_candidates():
    """Music videos in the library that aren't on a single loop yet -- i.e.
    everything freshly imported and not in rotation. Needs a playlist sync."""
    lib = apply_overrides(load_json(LIBRARY_PATH, {"items": []}).get("items", []))
    cache = load_json(PLAYLISTS_PATH, {"usage": {}, "synced_at": None})
    usage = cache.get("usage", {})
    excl = [a.lower() for a in CONFIG.get("excluded_artists", [])]
    out = [{"id": m["id"], "title": m["title"], "duration": m["duration"]}
           for m in lib
           if m["kind"] == "mv" and m["id"] not in usage
           and not scheduler.is_excluded(m["title"], excl)]
    out.sort(key=lambda m: m["id"], reverse=True)      # UUIDv7 -> newest first
    return {"candidates": out, "synced_at": cache.get("synced_at")}


def _artists_of(m):
    return {a.lower() for a in (m.get("artists") or scheduler.artist_tokens(m["title"]))}


def _deal_by_artist(items, k=LOOPS_PER_DAY):
    """Deal the batch into the k loop-slots it rotates through.

    Videos that share a slot always share a loop, so two songs by the same artist
    in one slot spend the whole week fighting the 2h spacing rule -- and one of
    them gets squeezed out. Deal artist-aware (fullest credit lists first, since
    they collide most), then interleave so position i lands in slot i % k.
    """
    buckets = [[] for _ in range(k)]
    claimed = [set() for _ in range(k)]
    for m in sorted(items, key=lambda x: -len(_artists_of(x))):
        mine = _artists_of(m)
        best = min(range(k), key=lambda b: (len(mine & claimed[b]), len(buckets[b])))
        buckets[best].append(m)
        claimed[best] |= mine
    out = []
    for i in range(max((len(b) for b in buckets), default=0)):
        for b in buckets:
            if i < len(b):
                out.append(b[i])
    return out


def build_music_plan(media_ids):
    lib = apply_overrides(load_json(LIBRARY_PATH, {"items": []}).get("items", []))
    by_id = {m["id"]: m for m in lib}
    picked = _deal_by_artist([by_id[m] for m in media_ids if m in by_id])
    if not picked:
        raise HTTPException(400, "No music videos selected.")
    week = _week_loops()
    if not week:
        raise HTTPException(400, "No 'Day Loop N' playlists found on the channel.")

    assign = {l["name"]: [] for l in week}
    for i, m in enumerate(picked):
        for d, day in enumerate(DAY_ORDER):
            name = f"{day} Loop {(i + d) % LOOPS_PER_DAY + 1}"
            if name in assign:
                assign[name].append({"id": m["id"], "title": m["title"]})

    plan = [{"loop": l["name"], "day": l["day"], "num": l["num"], "id": l["id"],
             "adds": assign[l["name"]]}
            for l in week if assign[l["name"]]]
    return {"newCount": len(picked), "loops": len(plan),
            "plays": len(picked) * len(DAY_ORDER),
            "plan": plan}


@app.get("/api/music-drop/preview")
def music_drop_preview(mediaIds: str = ""):
    ids = [i for i in mediaIds.split(",") if i]
    return build_music_plan(ids)


class MusicDropReq(BaseModel):
    mediaIds: list = []


def _specials_in(items):
    """Performances/interviews already on a loop, in play order, deduped."""
    lib = apply_overrides(load_json(LIBRARY_PATH, {"items": []}).get("items", []))
    kinds = {m["id"]: m["kind"] for m in lib}
    out = []
    for it in items:
        if kinds.get(it["mediaId"]) == "special" and it["mediaId"] not in out:
            out.append(it["mediaId"])
    return out


@app.post("/api/music-drop/execute")
async def music_drop_execute(req: MusicDropReq):
    plan = await run_in_threadpool(build_music_plan, req.mediaIds)
    # Openers and existing performances are read live per loop as it starts, so a
    # 28-loop drop doesn't act on a snapshot that's an hour stale by the end.
    job = new_job("music-drop",
                  "%d new music video(s) across %d loops"
                  % (plan["newCount"], plan["loops"]),
                  [{"loop": e["loop"], "playlistId": e["id"],
                    "gen": {"numSpecials": 3, "keepFromLive": True,
                            "mustIds": [a["id"] for a in e["adds"]],
                            "openersFromLive": True}}
                   for e in plan["plan"]])
    return StreamingResponse(run_job_stream(job), media_type="application/x-ndjson",
                             headers=NDJSON_HEADERS)


if __name__ == "__main__":
    import uvicorn
    print("\n  ChannelCast Loop Builder running at  http://127.0.0.1:8765\n")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
