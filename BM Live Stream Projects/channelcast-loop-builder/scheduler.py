"""
Playlist scheduling engine -- the same logic used to hand-build the Monday and
Tuesday loops, packaged as a reusable function.

Rules honoured:
  * total runtime targets ~6h without exceeding 6h15s (configurable)
  * no repeated songs within a loop
  * the same artist is never played within GAP seconds (default 2h)
  * up to N Live Performance / Interview "specials", each preceded by a short
    plug intro, spread evenly across the runtime
  * the rest is mostly music videos with occasional small promo bumpers
  * excluded artists are never placed
  * an optional full-length opener (e.g. a TWI episode) can start the loop
"""

import re
import random
import itertools


def artist_tokens(title: str):
    """Best-effort split of an 'MV ArtistBlock SongName' title into artist
    tokens so we can enforce spacing between same/related artists."""
    body = title[3:] if title.startswith("MV ") else title
    parts = body.rsplit(" ", 1)
    artist_block = parts[0] if len(parts) == 2 else body
    tokens = re.split(r'(?i)\bFT\b|FT|xft|X|x(?=[A-Z])', artist_block)
    tokens = [t.strip() for t in tokens if len(t.strip()) >= 3]
    return tokens or [artist_block.strip()]


def is_excluded(title: str, excluded_artists):
    t = title.lower()
    return any(a in t for a in excluded_artists)


def build_loop(mv_pool, promo_pool, intro, specials,
               *,
               floor=21600, ceil=21610, gap=7200,
               excluded_artists=None, seed=0,
               openers=None, avoid_mv_ids=None,
               promo_every=8, special_gap=3600,
               must_mvs=None):
    """
    mv_pool     : list of dicts {id,title,duration,artists}
    promo_pool  : list of dicts {id,title,duration}
    intro       : dict {id,title,duration} - the plug shown before each special
    specials    : list of dicts {id,title,duration} - already unique for this loop
    openers     : optional list of full shows to drop in at set times, each
                  {id,title,duration,hour}. hour = start mark (0 = top of loop,
                  2 = top of 2nd hour, 2.5 = 2h30m). Each is clamped so it still
                  ends by the floor; a show lands at the first item boundary at or
                  after its mark. Multiple shows are placed in hour order.
    avoid_mv_ids: set of media ids to skip (e.g. already used earlier in the day)

    Returns (sequence, report). sequence items are dicts with a 'kind' of
    opener|mv|promo|intro|special plus id/title/dur.
    """
    excluded_artists = [a.lower() for a in (excluded_artists or [])]
    avoid = set(avoid_mv_ids or [])

    # Music videos that MUST land in this loop (e.g. a new-music drop). They are
    # placed at spread targets below and pulled out of the general pool so they
    # can't also be picked at random.
    must = [m for m in (must_mvs or [])
            if not is_excluded(m["title"], excluded_artists)]
    must_ids = {m["id"] for m in must}

    pool = [m for m in mv_pool
            if m["id"] not in avoid and m["id"] not in must_ids
            and not is_excluded(m["title"], excluded_artists)]
    random.Random(seed).shuffle(pool)
    promo_cycle = itertools.cycle(promo_pool) if promo_pool else itertools.cycle([None])

    seq = []
    running = 0
    last_seen = {}

    def can_use(artists, now):
        return all(a.lower() not in last_seen or (now - last_seen[a.lower()]) >= gap
                   for a in artists)

    def mark(artists, now):
        for a in artists:
            last_seen[a.lower()] = now

    # Specials spread evenly across the loop for any count N, and never less
    # than `special_gap` (default 1h) apart -- enforced below so a long opener
    # can't cause overdue specials to stack back-to-back.
    n_special = len(specials)
    targets = [round(floor * (i + 1) / (n_special + 1)) for i in range(n_special)]
    last_special_end = -special_gap

    # Openers (full shows) are timed inserts, each clamped so it still finishes
    # by the floor, processed in hour order.
    prepared_openers = []
    for o in sorted(openers or [], key=lambda x: x.get("hour", 0)):
        tgt = max(0, min(round(o.get("hour", 0) * 3600), floor - o["duration"]))
        prepared_openers.append({"id": o["id"], "title": o["title"],
                                 "duration": o["duration"], "_target": tgt})
    opener_i = 0
    opener_placements = []

    def opener_due():
        return opener_i < len(prepared_openers) and running >= prepared_openers[opener_i]["_target"]

    def place_opener():
        nonlocal running, opener_i, mv_since_promo
        o = prepared_openers[opener_i]
        opener_placements.append({"title": o["title"], "placed_at": running})
        seq.append({"id": o["id"], "title": o["title"],
                    "duration": o["duration"], "kind": "opener"})
        running += o["duration"]
        opener_i += 1
        mv_since_promo = 0

    # Must-play music videos (a new-music drop) get evenly spread targets across
    # the loop and are placed at them.
    must_targets = [round(floor * (i + 1) / (len(must) + 1)) for i in range(len(must))]
    must_artists = [{a.lower() for a in m["artists"]} for m in must]
    must_left = list(range(len(must)))

    def must_pick():
        """First overdue must-play whose artists are clear right now. We scan all
        of them rather than working a strict queue: otherwise one song stuck
        behind the 2h artist rule holds up every must-play after it, and they all
        pile up at the end of the loop."""
        for j in must_left:
            if (running >= must_targets[j]
                    and running + must[j]["duration"] <= ceil
                    and can_use(must[j]["artists"], running)):
                return j
        return None

    def blocks_must(artists):
        """True if playing these artists now would push a pending must-play past
        its slot -- the random pool otherwise steals the artist slot a must-play
        needs and shoves it 2h down the loop."""
        mine = {a.lower() for a in artists}
        return any(must_targets[j] < running + gap and (mine & must_artists[j])
                   for j in must_left)

    special_i = 0
    mv_since_promo = 0
    stall = 0

    def special_due():
        return (special_i < len(specials)
                and running >= targets[special_i]
                and (running - last_special_end) >= special_gap)

    while running < floor:
        if opener_due():
            place_opener()
            continue

        j = must_pick()
        if j is not None:
            m = must[j]
            seq.append({**m, "kind": "mv"})
            mark(m["artists"], running)
            running += m["duration"]
            must_left.remove(j)
            mv_since_promo += 1
            stall = 0
            continue
        if special_due():
            s = specials[special_i]
            seq.append({**intro, "kind": "intro"})
            running += intro["duration"]
            seq.append({**s, "kind": "special"})
            running += s["duration"]
            last_special_end = running
            special_i += 1
            mv_since_promo = 0
            stall = 0
            continue

        placed = False
        if mv_since_promo >= promo_every and promo_pool:
            p = next(promo_cycle)
            if p and running + p["duration"] <= ceil:
                seq.append({**p, "kind": "promo"})
                running += p["duration"]
                mv_since_promo = 0
                placed = True

        if not placed:
            found = None
            for i, m in enumerate(pool):
                if running + m["duration"] > ceil:
                    continue
                if can_use(m["artists"], running) and not blocks_must(m["artists"]):
                    found = i
                    break
            if found is not None:
                m = pool.pop(found)
                seq.append({**m, "kind": "mv"})
                mark(m["artists"], running)
                running += m["duration"]
                mv_since_promo += 1
                stall = 0
                placed = True

        if not placed:
            # No compliant music video fits under the ceiling right now. Bridge
            # once with a promo, otherwise stop the music-video body -- the floor
            # guarantee below tops it off to at least 6h.
            if stall == 0 and promo_pool:
                p = next(promo_cycle)
                if p and running + p["duration"] <= ceil:
                    seq.append({**p, "kind": "promo"})
                    running += p["duration"]
                    mv_since_promo = 0
                stall += 1
            else:
                break

    # Safety: place any openers that didn't get reached in the body.
    while opener_i < len(prepared_openers):
        place_opener()

    # --- floor guarantee: never end below 6h -------------------------------
    # Fill any remaining gap with promo bumpers, largest-that-fits first, so the
    # loop lands in [floor, ceil]. Since the smallest bumper is < (ceil - running)
    # whenever running < floor, this always crosses the floor without exceeding
    # the ceiling. Falls back to the shortest available media if promos run out.
    running = _fill_to_floor(seq, running, promo_pool, mv_pool, pool,
                             floor, ceil, excluded_artists)

    report = verify(seq, gap, excluded_artists, avoid)
    report["total_seconds"] = running
    report["specials_placed"] = special_i
    report["specials_requested"] = len(specials)
    report["opener_placements"] = opener_placements
    report["below_floor"] = running < floor
    report["must_requested"] = len(must)
    report["must_placed"] = len(must) - len(must_left)
    report["must_unplaced"] = [{"id": must[j]["id"], "title": must[j]["title"]}
                               for j in must_left]
    return seq, report


def _fill_to_floor(seq, running, promo_pool, mv_pool, remaining_pool,
                   floor, ceil, excluded_artists):
    promos = sorted(promo_pool, key=lambda p: p["duration"], reverse=True)
    guard = 0
    while running < floor and guard < 50:
        guard += 1
        pick = None
        for p in promos:
            if running + p["duration"] <= ceil:
                pick = p
                break
        if pick is None:
            # Ceiling too tight for any promo (rare). Honour the FLOOR over the
            # ceiling and add the shortest promo so we never end under 6h.
            if promos:
                pick = promos[-1]
        if pick is None:
            break
        seq.append({**pick, "kind": "promo"})
        running += pick["duration"]
    return running


def verify(seq, gap, excluded_artists, avoid):
    ts = 0
    last = {}
    seen = set()
    violations = []
    for s in seq:
        if s.get("kind") == "mv":
            for a in s.get("artists", []):
                k = a.lower()
                if k in last and (ts - last[k]) < gap:
                    violations.append({"type": "spacing", "artist": a, "at": ts})
                last[k] = ts
            if s["id"] in seen:
                violations.append({"type": "duplicate", "id": s["id"], "at": ts})
            seen.add(s["id"])
            if is_excluded(s["title"], excluded_artists):
                violations.append({"type": "excluded", "title": s["title"]})
            if s["id"] in avoid:
                violations.append({"type": "repeat_from_prior", "title": s["title"]})
        ts += s["duration"]
    return {
        "violations": violations,
        "ok": not violations,
        "item_count": len(seq),
        "mv_count": sum(1 for s in seq if s.get("kind") == "mv"),
    }
