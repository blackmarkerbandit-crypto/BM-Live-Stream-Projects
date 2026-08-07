"""
Surgical loop repair -- pull specific items out of a live loop and top it back
up, instead of regenerating the whole thing.

Why this exists: removing four 30-second promos from a loop only leaves it a
couple of minutes short. Rebuilding all 120 items to fix that costs ~240 API
calls per loop and reshuffles every song on it. Removing the promos and
appending replacements costs about five calls and leaves the rest of the loop
exactly as it was.

The catch is that a rebuild gets the rules for free (the scheduler enforces
them), while surgery has to earn them:

  * `audit` checks a loop AS IT STANDS against every rule -- runtime window, no
    repeated songs, same artist >= 2h apart, no excluded artists, nothing
    archived. Run before and after, it proves the repair didn't introduce a
    violation, and it surfaces any that were already there.
  * `plan_topup` picks the filler with those same rules applied at the position
    the items will actually land -- appended to the tail -- so it can't create
    one.

A loop the audit reports as already broken is not something surgery can fix;
that one wants a full rebuild.
"""


def _timeline(items, by_id):
    """Walk a loop in play order, returning (total_seconds, last_seen) where
    last_seen maps a lowercased artist to the last second they started at."""
    ts = 0
    last = {}
    for it in items:
        m = by_id.get(it["mediaId"])
        if m and m.get("kind") == "mv":
            for a in m.get("artists", []):
                last[a.lower()] = ts
        ts += it.get("durationSeconds", 0)
    return ts, last


def audit(items, by_id, *, floor, ceil, gap, excluded_artists=(), archived=(),
          intro_id=None):
    """Check a live loop against every scheduling rule.

    items    : playlist items in play order [{mediaId, title, durationSeconds}]
    by_id    : library index {mediaId: {kind, title, artists, ...}}
    Returns a dict with the runtime, a per-kind breakdown and a `violations`
    list. `ok` is True only when the loop breaks nothing.
    """
    excl = [a.lower() for a in excluded_artists]
    archived = set(archived)
    ts = 0
    last = {}
    seen = set()
    kinds = {}
    violations = []
    unknown = 0

    for it in items:
        mid = it["mediaId"]
        m = by_id.get(mid)
        if m is None:
            unknown += 1
            kinds["unknown"] = kinds.get("unknown", 0) + 1
            ts += it.get("durationSeconds", 0)
            continue
        kind = m.get("kind", "other")
        kinds[kind] = kinds.get(kind, 0) + 1
        title = m.get("title") or it.get("title", "")

        if mid in archived:
            violations.append({"type": "archived", "title": title, "at": ts})

        if kind == "mv":
            if mid in seen:
                violations.append({"type": "duplicate", "title": title, "at": ts})
            seen.add(mid)
            low = title.lower()
            if any(a in low for a in excl):
                violations.append({"type": "excluded", "title": title, "at": ts})
            for a in m.get("artists", []):
                k = a.lower()
                if k in last and (ts - last[k]) < gap:
                    violations.append({"type": "spacing", "artist": a,
                                       "title": title, "at": ts,
                                       "since": ts - last[k]})
                last[k] = ts
        ts += it.get("durationSeconds", 0)

    if ts < floor:
        violations.append({"type": "short", "at": ts})
    elif ts > ceil:
        violations.append({"type": "long", "at": ts})

    return {"total_seconds": ts, "item_count": len(items), "kinds": kinds,
            "unknown": unknown, "violations": violations,
            "ok": not violations,
            # a runtime problem is the one thing surgery can fix on its own; the
            # rest mean the loop was already broken before we touched it
            "structural": [v for v in violations
                           if v["type"] in ("duplicate", "spacing", "excluded")]}


def plan_topup(items, by_id, mv_pool, promo_pool, *,
               floor, ceil, gap, wrap_check=True, max_items=40):
    """Choose what to append so a shortened loop lands back in [floor, ceil].

    Everything is picked for the tail position, under the live rules:
      * a music video is only eligible if it isn't already on the loop and none
        of its artists played within `gap` seconds of the end.
      * with wrap_check, its artists must also be clear of the loop's first
        `gap` seconds -- the tail plays straight into the head on repeat, which
        the original builder never accounted for.
      * promos carry no artist and are allowed to repeat, exactly as the
        scheduler's own floor-fill does.

    Prefers the longest thing that fits, so a gap closes in as few items as
    possible. Returns (picks, reached_floor).
    """
    running, last = _timeline(items, by_id)
    used = {it["mediaId"] for it in items}

    head = {}
    if wrap_check:
        # artists appearing in the opening `gap` seconds of the loop
        t = 0
        for it in items:
            if t >= gap:
                break
            m = by_id.get(it["mediaId"])
            if m and m.get("kind") == "mv":
                for a in m.get("artists", []):
                    head.setdefault(a.lower(), t)
            t += it.get("durationSeconds", 0)

    picks = []
    while running < floor and len(picks) < max_items:
        room = ceil - running
        choice = None

        mvs = [m for m in mv_pool
               if m["id"] not in used and m["duration"] <= room
               and all((a.lower() not in last or running - last[a.lower()] >= gap)
                       and a.lower() not in head
                       for a in m.get("artists", []))]
        if mvs:
            choice = max(mvs, key=lambda m: m["duration"])
        else:
            fits = [p for p in promo_pool if p["duration"] <= room]
            if fits:
                # a promo the loop isn't already running beats one it is
                fresh = [p for p in fits if p["id"] not in used]
                choice = max(fresh or fits, key=lambda p: p["duration"])

        if choice is None:
            break                       # nothing fits under the ceiling

        kind = by_id.get(choice["id"], {}).get("kind", "promo")
        picks.append({"id": choice["id"], "title": choice["title"],
                      "duration": choice["duration"], "kind": kind})
        used.add(choice["id"])
        if kind == "mv":
            for a in choice.get("artists", []):
                last[a.lower()] = running
        running += choice["duration"]

    return picks, running >= floor
