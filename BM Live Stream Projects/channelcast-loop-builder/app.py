"""
ChannelCast Loop Builder -- local web app.

Run:  python app.py     (then open http://127.0.0.1:8765 )

Everything talks to ChannelCast directly with your token, so once this is
running you can view, edit, generate and push loops without spending Claude
tokens.

Login is required for every route except /login (see the auth block below) --
this app can push, delete, and rewrite ChannelCast media using a token stored
in config.json, so it must not sit open once it's reachable from outside the
house. Accounts are NOT stored here: it reads the same users.json the BMB
Virtual Office uses (../virtual-office/users.json), so staff log into both
tools with the same username/password. Create/manage accounts from
../virtual-office/manage_users.py -- there is nothing to run in this folder.
"""

import os
import json
import time
import random
import secrets
from typing import Optional

import bcrypt
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse, Response, RedirectResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

PORT = 8765  # kept in a named constant so service.py can import it directly

# streaming responses must not be buffered, or progress bars sit blank until the end
NDJSON_HEADERS = {"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}

# NDJSON progress protocol: a progress line carries "done" as an integer COUNT,
# while the final summary carries "done": true. Readers must test `done === true`
# -- a truthy test reads the first progress line as the summary, which silently
# swallowed every write/clear update the progress bars were meant to show.

from channelcast_client import ChannelcastClient, ChannelcastError
import scheduler
import media_scan
import surgical

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
LIBRARY_PATH = os.path.join(HERE, "library.json")
USAGE_PATH = os.path.join(HERE, "usage.json")
PLAYLISTS_PATH = os.path.join(HERE, "playlists_cache.json")
OVERRIDES_PATH = os.path.join(HERE, "overrides.json")  # mediaId -> type (manual reclassify / archive)
IMPORTED_S3_PATH = os.path.join(HERE, "imported_s3.json")  # list of S3 keys already imported
JOB_PATH = os.path.join(HERE, "job_state.json")  # in-flight loop rebuild, for resume-after-crash
MEDIA_STATUS_PATH = os.path.join(HERE, "media_status.json")  # ChannelCast Active/Archived per media

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


# ---- auth: shared login with the BMB Virtual Office ------------------------
# users.json lives in the sibling virtual-office folder -- this app reads it
# (login only) rather than owning a copy, so one account works for both
# tools. If that folder is ever moved without updating this path, login here
# breaks; see SERVICE_INSTALL.md.
VIRTUAL_OFFICE_DIR = os.path.join(HERE, "..", "virtual-office")
USERS_PATH = os.path.join(VIRTUAL_OFFICE_DIR, "users.json")
SECRET_KEY_PATH = os.path.join(HERE, "secret_key.txt")
SESSION_MAX_AGE = 7 * 24 * 60 * 60  # a week -- fine for an internal tool this size


def load_or_create_secret_key() -> str:
    """Signing key for session cookies. Own file, own key -- session cookies
    are scoped per-domain by the browser anyway, so there's no benefit to
    sharing the Virtual Office's key, only a needless coupling."""
    if os.path.exists(SECRET_KEY_PATH):
        with open(SECRET_KEY_PATH, encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    key = secrets.token_hex(32)
    with open(SECRET_KEY_PATH, "w", encoding="utf-8") as f:
        f.write(key)
    return key


def find_user(username: str):
    for u in load_json(USERS_PATH, []):
        if u.get("username") == username:
            return u
    return None


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# Default-deny: every route requires a session except /login itself. Unlike
# the Virtual Office there's only one HTML page ("/") and no server-to-server
# hook routes to exempt.
LOGIN_EXEMPT_PATHS = {"/login"}
PAGE_PATHS = {"/"}


@app.middleware("http")
async def enforce_login(request: Request, call_next):
    path = request.url.path
    if path in LOGIN_EXEMPT_PATHS:
        return await call_next(request)
    user = request.session.get("user")
    if not user:
        if path in PAGE_PATHS:
            return RedirectResponse(url="/login", status_code=303)
        return JSONResponse({"detail": "Login required."}, status_code=401)
    request.state.user = user
    return await call_next(request)


# Registered AFTER enforce_login is defined, deliberately -- Starlette wraps
# middleware last-registered-outermost, so SessionMiddleware must be the last
# add_middleware call for request.session to already be populated by the time
# enforce_login's dispatch reads it (same gotcha noted in the Virtual Office's
# app.py; verified there the hard way).
app.add_middleware(SessionMiddleware, secret_key=load_or_create_secret_key(),
                    max_age=SESSION_MAX_AGE, same_site="lax")


@app.get("/login")
def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=303)
    return FileResponse(os.path.join(HERE, "login.html"),
                        headers={"Cache-Control": "no-store, must-revalidate"})


class LoginReq(BaseModel):
    username: str
    password: str


@app.post("/login")
def login_submit(req: LoginReq, request: Request):
    user = find_user(req.username.strip())
    if not user or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(401, "Invalid username or password.")
    request.session["user"] = {"username": user["username"], "role": user["role"]}
    return {"username": user["username"], "role": user["role"]}


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@app.get("/api/me")
def api_me(request: Request):
    return request.state.user


# ---- routes ---------------------------------------------------------------
@app.get("/")
def index():
    # no-store, or the browser heuristically caches the page and keeps showing an
    # old build after an update -- FileResponse only sends ETag/Last-Modified,
    # which a browser is free to ignore until its own heuristic expiry.
    return FileResponse(os.path.join(HERE, "index.html"),
                        headers={"Cache-Control": "no-store, must-revalidate"})


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


async def _sync_playlists():
    """Pull every playlist and its items, cache them, and build a
    media -> [playlists it appears in] usage index.

    Yields one progress dict per playlist, then a final {"_saved": cache}. The
    archive purge reuses this so it acts on live membership rather than on a
    usage index that may be days old.
    """
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
        yield {"i": i + 1, "n": n, "name": p["name"], "count": len(items)}
    cache = {"synced_at": time.time(), "playlists": out, "usage": usage}
    await run_in_threadpool(save_json, PLAYLISTS_PATH, cache)
    yield {"_saved": cache}


@app.post("/api/sync-playlists-stream")
async def sync_playlists_stream():
    """Pull every playlist and its items and cache them. Streams progress."""
    async def gen():
        async for msg in _sync_playlists():
            if "_saved" in msg:
                out = msg["_saved"]["playlists"]
                yield json.dumps({"done": True, "playlists": len(out),
                                  "with_items": sum(1 for p in out if p["count"] > 0)}) + "\n"
            else:
                yield json.dumps(msg) + "\n"
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
    # Duration 0 almost always means ChannelCast hadn't finished processing the
    # clip yet when this sync ran. Left unnoticed, a generation happily schedules
    # it as free runtime -- that's the exact bug that pushed every loop on the
    # network past the 6h ceiling in Aug 2026. Surfacing it here, at sync time,
    # is the cheapest place to catch it: re-sync once the clip finishes
    # processing, before it ever reaches a loop.
    pending = [m["title"] for m in library
               if m["kind"] in ("mv", "promo", "special") and m.get("duration", 0) <= 0]
    return {"total": len(library), "by_kind": by_kind,
            "duration_pending_count": len(pending), "duration_pending": pending[:20]}


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


def _apply_override(ov, media_id, kind):
    if kind in ("", "clear", "auto", None):
        ov.pop(media_id, None)
    else:
        ov[media_id] = kind


@app.post("/api/override")
def set_override(req: OverrideReq):
    ov = load_json(OVERRIDES_PATH, {})
    _apply_override(ov, req.mediaId, req.type)
    save_json(OVERRIDES_PATH, ov)
    return {"ok": True, "count": len(ov)}


class OverrideBulkReq(BaseModel):
    mediaIds: list = []
    type: str      # same values as OverrideReq; "" / "clear" removes the override


@app.post("/api/override-bulk")
def set_override_bulk(req: OverrideBulkReq):
    """Retype a whole selection at once -- one file write instead of one per
    item, so reclassifying fifty promos doesn't mean fifty round trips."""
    ov = load_json(OVERRIDES_PATH, {})
    for mid in req.mediaIds:
        _apply_override(ov, mid, req.type)
    save_json(OVERRIDES_PATH, ov)
    return {"ok": True, "changed": len(req.mediaIds), "count": len(ov)}


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
    lib = [m for m in lib if m["kind"] != "archive"]  # locally archived
    arch = archived_ids()                             # Archived in ChannelCast itself
    lib = [m for m in lib if m["id"] not in arch]
    excl = [a.lower() for a in CONFIG.get("excluded_artists", [])]
    by_id = {m["id"]: m for m in lib}
    intro_id = CONFIG["intro_media_id"]
    # A clip ChannelCast hasn't finished processing yet reports duration 0/missing.
    # Scheduling it costs the loop its real runtime while the scheduler's own math
    # counts it as free -- exactly how 32 such clips pushed every loop on the
    # network past the 6h ceiling in Aug 2026 with a perfectly clean-looking
    # generation report. by_id above is left unfiltered (generate_sequence needs
    # it to detect and report a *requested* must-play that's stuck this way,
    # rather than have it silently vanish); only the general pools exclude them.
    mv_pool = [m for m in lib if m["kind"] == "mv" and m.get("duration", 0) > 0]
    promo_pool = [m for m in lib if m["kind"] == "promo" and m["id"] != intro_id
                  and m.get("duration", 0) > 0]
    special_pool = [m for m in lib if m["kind"] == "special"
                    and not scheduler.is_excluded(m["title"], excl)
                    and m.get("duration", 0) > 0]
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
    # duration>0 guard: a kept special ChannelCast hasn't finished processing yet
    # is treated the same as one that's been archived out from under us -- the
    # backfill below (`need`) redraws a replacement from the (duration-checked)
    # special_pool instead of silently keeping a clip that would miscount.
    specials = [{"id": by_id[s]["id"], "title": by_id[s]["title"],
                 "duration": by_id[s]["duration"]}
                for s in (keep_special_ids or [])
                if s in by_id and by_id[s].get("duration", 0) > 0]
    # How many slots still need filling. A plain generate keeps nothing and draws
    # the full count. A "keep what's on the loop" rebuild normally draws none --
    # unless one of those specials has since been archived out of the pool, in
    # which case we backfill just that hole instead of leaving the loop short.
    if keep_special_ids:
        need = min(len(keep_special_ids), num_specials) - len(specials)
    else:
        need = num_specials
    if need > 0:
        have = {s["id"] for s in specials}
        usage = load_json(USAGE_PATH, {"specials": []})
        used_specials = set(usage.get("specials", []))
        available = [s for s in special_pool
                     if s["id"] not in used_specials and s["id"] not in have]
        if len(available) < need:
            depleted = True
            available = [s for s in special_pool if s["id"] not in have]
        random.Random(seed or int(time.time())).shuffle(available)
        specials += [{"id": s["id"], "title": s["title"], "duration": s["duration"]}
                     for s in available[:need]]
    want_must = set(must_ids or [])
    must_mvs = [m for m in mv_pool if m["id"] in want_must]
    # mv_pool already excludes duration<=0 clips, which is exactly wrong for a
    # must-play: a new-music drop is the single most likely thing to still be
    # duration 0 (freshly imported, not yet processed by ChannelCast), and
    # silently dropping it off the loop is worse than silently overrunning was.
    # Surface it as pending instead so it's visible, not vanished.
    found_must = {m["id"] for m in must_mvs}
    must_duration_pending = [{"id": mid, "title": by_id[mid]["title"]}
                             for mid in want_must
                             if mid in by_id and mid not in found_must
                             and by_id[mid].get("duration", 0) <= 0]

    openers = []
    opener_duration_pending = []
    for spec in (openers_spec or []):
        mid = spec.get("mediaId")
        if mid and mid in by_id:
            o = by_id[mid]
            if o.get("duration", 0) <= 0:
                opener_duration_pending.append({"id": o["id"], "title": o["title"]})
                continue
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
    report["must_duration_pending"] = must_duration_pending
    report["opener_duration_pending"] = opener_duration_pending
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
            L["unplaced"] = (res["report"].get("must_unplaced", [])
                             + res["report"].get("must_duration_pending", [])
                             + res["report"].get("opener_duration_pending", [])
                             + res["report"].get("opener_unplaced", []))
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
                except ChannelcastError as e:
                    # A resume-after-crash re-removing an item a prior attempt
                    # already cleared is fine and expected -- that's what this
                    # except exists for. Anything else (rate limit, timeout, a
                    # real API error) must not be swallowed the same way: doing
                    # so used to leave stale items mixed into an otherwise-clean
                    # rebuild with no signal anywhere. Let a genuine failure stop
                    # the job here, in "clearing", with an accurate removed-count
                    # so /api/job/resume picks it back up cleanly.
                    msg = str(e).lower()
                    if "not found" not in msg and "does not exist" not in msg:
                        raise
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
    longer start with "TWI "/"CUDI " at all. Archived shows are dropped: a
    rebuild that "keeps the existing openers" must not put one back.
    """
    lib = load_json(LIBRARY_PATH, {"items": []}).get("items", [])
    names = {m["id"]: m["title"] for m in lib}
    arch = archived_ids()
    out = []
    for it in items:
        if it["mediaId"] in arch:
            continue
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
    """Performances/interviews already on a loop, in play order, deduped.
    Archived ones are dropped -- generate_sequence tops the loop back up to the
    requested count from the fresh pool."""
    lib = apply_overrides(load_json(LIBRARY_PATH, {"items": []}).get("items", []))
    kinds = {m["id"]: m["kind"] for m in lib}
    arch = archived_ids()
    out = []
    for it in items:
        if (kinds.get(it["mediaId"]) == "special" and it["mediaId"] not in out
                and it["mediaId"] not in arch):
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


# ---- archive cleanup ------------------------------------------------------
# ChannelCast media carry their own status (Active / Archived), set in the
# dashboard -- separate from this app's local "archive" type override. Archiving
# something there does NOT pull it out of the loops it is already in, and the
# builder never knew the field existed, so archived files kept getting scheduled.
#
# The tab this drives does three things in order:
#   1. scan   -- read every media item's real status (see media_scan.py)
#   2. purge  -- rebuild every loop holding an archived file, by the normal rules
#   3. delete -- remove the archived files themselves, or export the list

def load_status():
    return load_json(MEDIA_STATUS_PATH,
                     {"scanned_at": None, "archived": {}, "total": 0,
                      "active": 0, "complete": False})


def archived_ids():
    """Media ChannelCast itself has archived. Empty until the first scan, which
    keeps every existing workflow behaving exactly as before."""
    return set(load_status().get("archived", {}).keys())


def archive_report():
    """The archived list, annotated with what each file is and where it still
    plays. Loop membership comes from the playlist cache, so the report carries
    its timestamp and the UI can say how fresh it is."""
    st = load_status()
    cache = load_json(PLAYLISTS_PATH, {"usage": {}, "synced_at": None})
    usage = cache.get("usage", {})
    ov = load_json(OVERRIDES_PATH, {})
    out = []
    for mid, m in st.get("archived", {}).items():
        u = usage.get(mid, [])
        name = m.get("filename") or m.get("title") or ""
        out.append({
            "id": mid,
            "filename": name,
            "title": m.get("title", ""),
            "duration": m.get("durationSeconds", 0),
            "kind": ov.get(mid) or classify(name),
            "spots": len(u),
            "loops": sorted({e["playlistName"] for e in u}),
        })
    # still-in-a-loop first: those are the ones the purge has to deal with
    out.sort(key=lambda x: (-x["spots"], x["filename"].lower()))
    return {
        "scanned_at": st.get("scanned_at"),
        "complete": st.get("complete", False),
        "total": st.get("total", 0),
        "active": st.get("active", 0),
        "archived": out,
        "inLoops": sum(1 for x in out if x["spots"]),
        "spots": sum(x["spots"] for x in out),
        "usage_synced_at": cache.get("synced_at"),
    }


@app.get("/api/archive/list")
def archive_list():
    return archive_report()


@app.post("/api/archive/scan-stream")
async def archive_scan_stream():
    """Read every media item's status straight from ChannelCast and cache the
    archived ones. Streams a progress line per API call."""
    import queue
    import threading

    q = queue.Queue()

    def work():
        try:
            res = media_scan.scan_all_media(client, SEARCH_TERMS, on_progress=q.put)
            q.put({"_result": res})
        except Exception as e:                      # noqa: BLE001 - surfaced to UI
            q.put({"_error": str(e)})
        finally:
            q.put(None)

    threading.Thread(target=work, daemon=True).start()

    async def gen():
        while True:
            msg = await run_in_threadpool(q.get)
            if msg is None:
                break
            if "_error" in msg:
                yield json.dumps({"error": msg["_error"]}) + "\n"
                break
            if "_result" in msg:
                res = msg["_result"]
                archived = {m["id"]: m for m in res["items"] if m["status"] != "Active"}
                save_json(MEDIA_STATUS_PATH, {
                    "scanned_at": time.time(),
                    "total": len(res["items"]),
                    "active": len(res["items"]) - len(archived),
                    "complete": res["complete"],
                    "calls": res["calls"],
                    "archived": archived,
                })
                yield json.dumps({"done": True, **archive_report()}) + "\n"
                continue
            yield json.dumps(msg) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=NDJSON_HEADERS)


def build_purge_plan():
    """Which loops still hold an archived file, off the cached playlist sync."""
    arch = archived_ids()
    cache = load_json(PLAYLISTS_PATH, {"playlists": [], "synced_at": None})
    plan = []
    for p in cache.get("playlists", []):
        hits = [it for it in p.get("items", []) if it["mediaId"] in arch]
        if hits:
            plan.append({"loop": p["name"], "id": p["id"], "spots": len(hits),
                         "titles": sorted({it["title"] for it in hits})})
    plan.sort(key=lambda x: x["loop"])
    return {"plan": plan, "loops": len(plan),
            "spots": sum(x["spots"] for x in plan),
            "synced_at": cache.get("synced_at")}


@app.post("/api/archive/purge-plan-stream")
async def archive_purge_plan_stream():
    """Re-read every loop live, then report which ones need rebuilding. The
    live re-read matters: acting on a stale usage index could rebuild loops that
    are already clean and miss ones that aren't."""
    async def gen():
        async for msg in _sync_playlists():
            if "_saved" in msg:
                yield json.dumps({"done": True, **build_purge_plan()}) + "\n"
            else:
                yield json.dumps({"phase": "scan", **msg}) + "\n"
    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=NDJSON_HEADERS)


@app.get("/api/archive/purge-plan")
def archive_purge_plan():
    return build_purge_plan()


class PurgeReq(BaseModel):
    loops: list = []          # loop names to rebuild; empty = every affected loop


@app.post("/api/archive/purge-execute")
async def archive_purge_execute(req: PurgeReq = None):
    """Rebuild every affected loop from scratch under the normal rules.

    A rebuild regenerates the whole loop rather than snipping the archived items
    out, which is the only way to land back inside the 6h window with the artist
    spacing and no-repeat rules intact -- pulling three promos out of a loop
    otherwise leaves it minutes short. Each loop keeps its own shows and
    performances (minus any that are themselves archived); only the music is
    redrawn. Archived media can't come back because the pools now exclude them.
    """
    plan = await run_in_threadpool(build_purge_plan)
    entries = plan["plan"]
    if req and req.loops:
        want = set(req.loops)
        entries = [e for e in entries if e["loop"] in want]
    if not entries:
        raise HTTPException(400, "No loops contain archived media -- run the scan first.")
    job = new_job("archive-purge",
                  "Purge archived media from %d loop(s)" % len(entries),
                  [{"loop": e["loop"], "playlistId": e["id"],
                    "gen": {"numSpecials": 3, "keepFromLive": True,
                            "openersFromLive": True}}
                   for e in entries])
    return StreamingResponse(run_job_stream(job), media_type="application/x-ndjson",
                             headers=NDJSON_HEADERS)


# --- surgical purge ---------------------------------------------------------
# The fast path: cut the archived items out of a loop and top it back up,
# leaving everything else untouched. Roughly 5 calls per loop instead of 240.
# See surgical.py for how the rules are held up without a full regeneration.

def _audit_args():
    floor = int(CONFIG.get("target_seconds", 21600))
    return {"floor": floor, "ceil": floor + 10,
            "gap": int(CONFIG.get("gap_seconds", 7200)),
            "excluded_artists": CONFIG.get("excluded_artists", []),
            "archived": archived_ids()}


def _loop_index():
    """Library indexed by id, with overrides applied -- what the audit reads
    kinds and artists from."""
    lib = apply_overrides(load_json(LIBRARY_PATH, {"items": []}).get("items", []))
    for m in lib:
        if m["kind"] == "mv" and "artists" not in m:
            m["artists"] = scheduler.artist_tokens(m["title"])
    return {m["id"]: m for m in lib}


def _vkey(v):
    return (v["type"], v.get("artist", ""), v.get("title", ""))


def plan_surgical_loop(items, by_id, pools=None):
    """Work out the repair for one loop from its live items.

    Returns removals, what to append, and an audit of the loop before and after.
    The audits are the point: diffing them shows exactly what the repair changed,
    separating problems it introduced from ones that were already there.

    One effect is worth understanding, because it shows up on real loops. The
    builder places an artist at the earliest legal moment, so repeat plays sit at
    almost exactly the 2h line. Cutting a 30-second promo out of the middle pulls
    everything after it 30 seconds earlier, which drops those pairs a few seconds
    under the line. That is unavoidable for any edit that isn't a full rebuild,
    and it is reported as `worstDrift` -- how far under 2h the closest pair ends
    up -- rather than as a plain pass/fail, so it can be judged on size.
    """
    arch = archived_ids()
    args = _audit_args()
    gap = args["gap"]
    tol = int(CONFIG.get("spacing_tolerance_seconds", 300))

    before = surgical.audit(items, by_id, intro_id=CONFIG["intro_media_id"], **args)
    removals = [{"playlistItemId": it["playlistItemId"], "mediaId": it["mediaId"],
                 "title": by_id.get(it["mediaId"], {}).get("title") or it["title"],
                 "duration": it.get("durationSeconds", 0)}
                for it in items if it["mediaId"] in arch]
    kept = [it for it in items if it["mediaId"] not in arch]

    if pools is None:
        _, mv_pool, promo_pool, _, _ = build_library_pools()
    else:
        mv_pool, promo_pool = pools
    picks, reached = surgical.plan_topup(
        kept, by_id, mv_pool, promo_pool,
        floor=args["floor"], ceil=args["ceil"], gap=gap)

    projected = kept + [{"mediaId": p["id"], "title": p["title"],
                         "durationSeconds": p["duration"]} for p in picks]
    after = surgical.audit(projected, by_id, intro_id=CONFIG["intro_media_id"], **args)

    had = {_vkey(v) for v in before["violations"]}
    new = [v for v in after["violations"]
           if _vkey(v) not in had and v["type"] != "archived"]
    drifts = [gap - v["since"] for v in new if v["type"] == "spacing"]
    worst_drift = max(drifts) if drifts else 0
    hard = [v for v in new if v["type"] in ("duplicate", "excluded")]

    # A loop already outside the runtime window is one a rebuild would resize --
    # e.g. a 9h loop built around a 3h show gets forced back to 6h, dropping
    # hours of music. Worth knowing before choosing to rebuild it.
    rebuild_resizes = before["total_seconds"] > args["ceil"]

    ok_surgical = not hard and reached and worst_drift <= tol
    return {"removals": removals, "topups": picks, "reachedFloor": reached,
            "before": before, "after": after,
            "newViolations": new, "worstDrift": worst_drift,
            "hardViolations": hard, "rebuildResizes": rebuild_resizes,
            "surgicalOk": ok_surgical,
            "recommend": "surgical" if (ok_surgical or rebuild_resizes) else "rebuild"}


def build_surgical_plan():
    """The repair for every loop that still holds archived media, off the
    cached playlist sync."""
    arch = archived_ids()
    by_id = _loop_index()
    _, mv_pool, promo_pool, _, _ = build_library_pools()
    cache = load_json(PLAYLISTS_PATH, {"playlists": [], "synced_at": None})
    out = []
    for p in cache.get("playlists", []):
        items = p.get("items", [])
        if not any(it["mediaId"] in arch for it in items):
            continue
        r = plan_surgical_loop(items, by_id, pools=(mv_pool, promo_pool))
        out.append({"loop": p["name"], "id": p["id"], **r})
    out.sort(key=lambda x: x["loop"])
    calls = sum(1 + len(e["removals"]) + len(e["topups"]) for e in out)
    # what the same job would cost as full rebuilds, for an honest comparison
    rebuild_calls = sum(2 * e["before"]["item_count"] for e in out)
    return {
        "plan": out,
        "loops": len(out),
        "removals": sum(len(e["removals"]) for e in out),
        "topups": sum(len(e["topups"]) for e in out),
        "calls": calls,
        "rebuildCalls": rebuild_calls,
        "tolerance": int(CONFIG.get("spacing_tolerance_seconds", 300)),
        "worstDrift": max([e["worstDrift"] for e in out], default=0),
        "recommendRebuild": [e["loop"] for e in out if e["recommend"] == "rebuild"],
        "resizeWarn": [e["loop"] for e in out if e["rebuildResizes"]],
        "synced_at": cache.get("synced_at"),
    }


@app.get("/api/archive/surgical-plan")
def archive_surgical_plan():
    return build_surgical_plan()


@app.post("/api/archive/surgical-plan-stream")
async def archive_surgical_plan_stream():
    """Re-read every loop live, then plan the surgical repair for each."""
    async def gen():
        async for msg in _sync_playlists():
            if "_saved" in msg:
                plan = await run_in_threadpool(build_surgical_plan)
                yield json.dumps({"done": True, **plan}) + "\n"
            else:
                yield json.dumps({"phase": "scan", **msg}) + "\n"
    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=NDJSON_HEADERS)


@app.get("/api/archive/audit")
def archive_audit():
    """Rule check for every loop as it stands, off the cached sync. Nothing is
    changed -- this is the 'is the rest of the loop actually clean?' report."""
    by_id = _loop_index()
    args = _audit_args()
    cache = load_json(PLAYLISTS_PATH, {"playlists": [], "synced_at": None})
    out = []
    for p in cache.get("playlists", []):
        items = p.get("items", [])
        if not items:
            continue
        a = surgical.audit(items, by_id, intro_id=CONFIG["intro_media_id"], **args)
        out.append({"loop": p["name"], "id": p["id"], **a})
    out.sort(key=lambda x: x["loop"])
    return {"loops": out, "synced_at": cache.get("synced_at"),
            "clean": sum(1 for e in out if e["ok"]),
            "total": len(out)}


class SurgicalReq(BaseModel):
    loops: list = []          # loop names to repair; empty = every planned loop


@app.post("/api/archive/surgical-execute")
async def archive_surgical_execute(req: SurgicalReq):
    """Do the repair, one loop at a time, streaming progress.

    Each loop is re-read immediately before it's touched and its plan recomputed
    from that -- so this is safe to re-run after an interruption (a loop already
    repaired simply has nothing left to remove) and never acts on a snapshot
    that went stale while an earlier loop was being processed.
    """
    async def gen():
        arch = await run_in_threadpool(archived_ids)
        by_id = await run_in_threadpool(_loop_index)
        pools = await run_in_threadpool(build_library_pools)
        pools = (pools[1], pools[2])
        cache = load_json(PLAYLISTS_PATH, {"playlists": []})
        targets = [p for p in cache.get("playlists", [])
                   if any(it["mediaId"] in arch for it in p.get("items", []))]
        if req.loops:
            want = set(req.loops)
            targets = [p for p in targets if p["name"] in want]
        targets.sort(key=lambda p: p["name"])

        n = len(targets)
        done_loops, removed, added = 0, 0, 0
        results = []
        for i, p in enumerate(targets):
            yield json.dumps({"phase": "read", "loop": p["name"],
                              "i": i + 1, "n": n}) + "\n"
            live = await run_in_threadpool(client.list_playlist_items, p["id"])
            items = live.get("items", [])
            r = await run_in_threadpool(plan_surgical_loop, items, by_id, pools)
            total = len(r["removals"]) + len(r["topups"])
            step = 0

            for rem in r["removals"]:
                try:
                    await run_in_threadpool(client.remove_playlist_item,
                                            rem["playlistItemId"])
                    removed += 1
                except ChannelcastError:
                    pass            # already gone -- a re-run after a crash
                step += 1
                yield json.dumps({"phase": "remove", "loop": p["name"], "i": i + 1,
                                  "n": n, "done": step, "total": total,
                                  "title": rem["title"]}) + "\n"

            for t in r["topups"]:
                await run_in_threadpool(client.add_media_to_playlist, p["id"], t["id"])
                added += 1
                step += 1
                yield json.dumps({"phase": "add", "loop": p["name"], "i": i + 1,
                                  "n": n, "done": step, "total": total,
                                  "title": t["title"]}) + "\n"

            done_loops += 1
            results.append({"loop": p["name"],
                            "removed": len(r["removals"]),
                            "added": len(r["topups"]),
                            "seconds": r["after"]["total_seconds"],
                            "ok": r["after"]["ok"],
                            "violations": r["after"]["violations"]})
            yield json.dumps({"phase": "loopdone", "loop": p["name"],
                              "total_seconds": r["after"]["total_seconds"],
                              "violations": len(r["after"]["violations"])}) + "\n"

        yield json.dumps({"done": True, "loops": done_loops, "removed": removed,
                          "added": added, "results": results}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=NDJSON_HEADERS)


class ArchiveDeleteReq(BaseModel):
    mediaIds: list = []
    force: bool = False          # delete even if the file is still in a loop


@app.post("/api/archive/delete-stream")
async def archive_delete_stream(req: ArchiveDeleteReq):
    """Delete media from ChannelCast for good. Streams one line per file.

    Anything still sitting in a loop is skipped unless force is set -- deleting
    it out from under a playlist is how you end up with loops full of dead
    entries. Run the purge first and the skip list will be empty.
    """
    async def gen():
        cache = load_json(PLAYLISTS_PATH, {"usage": {}})
        usage = cache.get("usage", {})
        n = len(req.mediaIds)
        st = load_status()
        names = st.get("archived", {})
        deleted, skipped, failed = 0, [], []
        for i, mid in enumerate(req.mediaIds):
            meta = names.get(mid, {})
            title = meta.get("filename") or meta.get("title") or mid
            spots = len(usage.get(mid, []))
            if spots and not req.force:
                skipped.append({"id": mid, "title": title, "spots": spots})
                yield json.dumps({"i": i + 1, "n": n, "title": title,
                                  "skipped": f"still in {spots} loop spot(s)"}) + "\n"
                continue
            err = None
            try:
                res = await run_in_threadpool(client.call_tool, "delete_media",
                                              {"mediaId": mid})
                if res.get("deleted"):
                    deleted += 1
                    names.pop(mid, None)
                else:
                    err = "ChannelCast reported deleted=false"
            except Exception as e:                  # noqa: BLE001 - surfaced to UI
                err = str(e)
            if err:
                failed.append({"id": mid, "title": title, "error": err})
            yield json.dumps({"i": i + 1, "n": n, "title": title, "error": err}) + "\n"
        # forget what's gone, so the list reflects reality without a full re-scan
        st["archived"] = names
        await run_in_threadpool(save_json, MEDIA_STATUS_PATH, st)
        yield json.dumps({"done": True, "deleted": deleted,
                          "skipped": skipped, "failed": failed,
                          **archive_report()}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=NDJSON_HEADERS)


@app.get("/api/archive/export")
def archive_export(ids: str = ""):
    """CSV of the archived files, for deleting by hand in the dashboard."""
    wanted = {i for i in ids.split(",") if i}
    rows = [r for r in archive_report()["archived"]
            if not wanted or r["id"] in wanted]

    def esc(v):
        v = str(v)
        return '"%s"' % v.replace('"', '""') if any(c in v for c in ',"\n') else v

    lines = ["Filename,Display Title,Type,Length,In Loops,Loops,Media ID"]
    for r in rows:
        lines.append(",".join(esc(x) for x in [
            r["filename"], r["title"], r["kind"],
            time.strftime("%H:%M:%S", time.gmtime(r["duration"])),
            r["spots"], "; ".join(r["loops"]), r["id"]]))
    stamp = time.strftime("%Y-%m-%d")
    return Response("\n".join(lines), media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="channelcast-archived-{stamp}.csv"'})


if __name__ == "__main__":
    import uvicorn
    print(f"\n  ChannelCast Loop Builder running at  http://127.0.0.1:{PORT}\n")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
