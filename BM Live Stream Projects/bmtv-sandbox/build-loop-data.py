"""
Build loop-data.json for the BlackMarker.TV homepage.

WHY THIS EXISTS
    The homepage needs three things live: what is playing now, what is coming
    up, and the newest episode of each show.

    Only the first is available to a browser. ChannelCast exposes
    /api/v1/playback/timeseek/{channelId} publicly, no auth, CORS '*' -- that
    is the now-playing feed and the page calls it directly.

    Everything else is behind the ChannelCast MCP API, which authenticates with
    the cck_ token. That token can delete_media and delete_playlist, so it must
    never reach a browser. This script runs server-side and writes a JSON file
    containing nothing but titles, durations and poster URLs.

WHERE THE NUMBERS COME FROM -- all authoritative, none inferred
    list_schedules      the real weekly timetable: 28 entries, each a startUtc
                        and a playlistId. The page derives the airing loop from
                        these rather than assuming a fixed Eastern offset, so a
                        schedule change or a DST shift needs no code edit.
    list_playlist_items each item's playsAtSeconds inside its six-hour block.
    list_category_items ChannelCast's own categories, where sort 0 is the
                        newest -- Eric's editorial order, not a date parsed out
                        of a filename.

RUN
    python build-loop-data.py                 # live from the API
    python build-loop-data.py --skip-shows    # loops only, far fewer calls
"""

import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.join(os.path.dirname(HERE), "channelcast-loop-builder")
OUT = os.path.join(HERE, "loop-data.json")

sys.path.insert(0, BUILDER)

# Editorial order for the Latest Shows row, by ChannelCast category name.
# Performance Battles is deliberately absent -- it lives in the Event Streams
# dropdown only.
SHOW_CATEGORIES = [
    "Can You Dig It!? Live Music Review",
    "The Weekly Interrupt",
    "For The Record",
    "The Alien Podcast",
    "Talking Tipsy",
    "Special Interrupts",
]

# Display names, where the category name is longer than the row can carry.
SHORT_NAME = {"Can You Dig It!? Live Music Review": "Can You Dig It!?"}

WEEK = 7 * 86400


# ----------------------------------------------------------------------------
# Titles
#
# Stored titles are filename-shaped: "MV Doechii Pacer". Split them into artist
# and song so the page can style the two differently. Show titles are already
# human-written and only need their trailing date removed.
# ----------------------------------------------------------------------------
CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
TRAILING_DATE = re.compile(r"\s*[|-]?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s*$")

CONTRACTIONS = {
    "Dont": "Don't", "Cant": "Can't", "Wont": "Won't", "Aint": "Ain't",
    "Im": "I'm", "Ive": "I've", "Yall": "Y'all", "Thats": "That's",
    "Whats": "What's", "Didnt": "Didn't", "Doesnt": "Doesn't",
    "Isnt": "Isn't", "Youre": "You're", "Theyre": "They're",
}


def split_words(chunk):
    """'ApolloBrownNSkyzoo' -> 'Apollo Brown & Skyzoo'"""
    words = CAMEL.sub(" ", chunk).replace("_", " ").strip().split()
    out = []
    for i, w in enumerate(words):
        # 'FT' introduces a feature credit and the camel split usually glues it
        # to the guest's name: 'FTJTMoney' -> 'feat. JTMoney'
        if w in ("FT", "Ft", "Feat"):
            out.append("feat.")
            continue
        if w.startswith("FT") and len(w) > 2 and w[2].isupper():
            out += ["feat.", w[2:]]
            continue
        if w == "N" and 0 < i < len(words) - 1:
            out.append("&")
            continue
        if w == "X" and 0 < i < len(words) - 1:
            out.append("x")
            continue
        out.append(CONTRACTIONS.get(w, w))
    return " ".join(out)


def clean_track(raw, artists=None):
    """Return (artist, song) for a music-video style title."""
    t = (raw or "").strip()
    for p in ("MV ", "LP ", "LI ", "IA ", "Promo ", "Performance "):
        if t.startswith(p):
            t = t[len(p):]
            break
    t = TRAILING_DATE.sub("", t)
    t = re.sub(r"\s+\d{8}$", "", t)

    if artists:
        squashed_a = re.sub(r"\W+", "", artists[0]).lower()
        if re.sub(r"\W+", "", t).lower().startswith(squashed_a):
            seen, i = "", 0
            while i < len(t) and len(re.sub(r"\W+", "", seen)) < len(squashed_a):
                seen += t[i]
                i += 1
            return split_words(artists[0]), split_words(t[i:].strip())
        return split_words(artists[0]), split_words(t)

    parts = t.split(" ", 1)
    if len(parts) == 2:
        return split_words(parts[0]), split_words(parts[1])
    return "", split_words(t)


def episode_date(raw):
    """ISO date parsed out of a show title, or ''."""
    m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", raw or "")
    if m:
        try:
            return dt.date(int(m.group(3)), int(m.group(1)), int(m.group(2))).isoformat()
        except ValueError:
            pass
    m = re.search(r"\b(\d{2})(\d{2})(\d{4})\b", raw or "")
    if m:
        try:
            return dt.date(int(m.group(3)), int(m.group(1)), int(m.group(2))).isoformat()
        except ValueError:
            pass
    return ""


def unwrap(res, *keys):
    """MCP replies are {"<thing>": [...]}; pull the list out."""
    if isinstance(res, list):
        return res
    if not isinstance(res, dict):
        return []
    for k in keys:
        if isinstance(res.get(k), list):
            return res[k]
    for v in res.values():
        if isinstance(v, list):
            return v
    return []


# ----------------------------------------------------------------------------
def artists_by_id():
    path = os.path.join(BUILDER, "library.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        lib = json.load(fh)
    return {i["id"]: i.get("artists") or [] for i in lib.get("items", [])}


def build_blocks(client, channel_id):
    """The weekly timetable, as offsets from Monday 00:00 UTC."""
    scheds = unwrap(client.call_tool("list_schedules", {"channelId": channel_id}),
                    "schedules", "items")
    blocks = []
    for s in scheds:
        start, pid = s.get("startUtc"), s.get("playlistId")
        if not start or not pid:
            continue
        try:
            d = dt.datetime.fromisoformat(start.replace("Z", ""))
        except ValueError:
            continue
        # Weekly recurrence: the date fixes the weekday, the time fixes the slot.
        offset = d.weekday() * 86400 + d.hour * 3600 + d.minute * 60 + d.second
        blocks.append({"o": offset, "p": pid})
    blocks.sort(key=lambda b: b["o"])

    # Each block runs until the next one starts, wrapping around the week. Taking
    # the gap rather than assuming six hours means an uneven schedule still works.
    for i, b in enumerate(blocks):
        nxt = blocks[(i + 1) % len(blocks)]["o"]
        b["len"] = (nxt - b["o"]) % WEEK or WEEK
    return blocks


def build_loops(client, wanted_ids, arts):
    loops = {}
    for pid in wanted_ids:
        items = unwrap(client.call_tool("list_playlist_items", {"playlistId": pid}),
                       "items", "playlistItems")
        rows = []
        for it in items:
            mid = it.get("mediaId") or it.get("id")
            artist, song = clean_track(it.get("title", ""), arts.get(mid))
            rows.append({
                "i": mid, "a": artist, "s": song,
                "d": int(it.get("durationSeconds") or 0),
                "t": int(it.get("playsAtSeconds") or 0),
            })
        rows.sort(key=lambda r: r["t"])
        loops[pid] = rows
        print("   %-38s %3d items" % (pid[:38], len(rows)))
    return loops


def build_shows(client, channel_id):
    cats = unwrap(client.call_tool("list_categories", {"channelId": channel_id}), "categories")
    by_name = {c["name"]: c for c in cats}
    rows, need = [], {}

    for name in SHOW_CATEGORIES:
        cat = by_name.get(name)
        if not cat:
            print("   %-24s no such category" % name[:24])
            continue
        items = unwrap(client.call_tool("list_category_items", {"categoryId": cat["id"]}),
                       "items", "media")
        if not items:
            print("   %-24s empty" % name[:24])
            continue
        # sort 0 is the newest -- ChannelCast's own editorial order.
        items.sort(key=lambda x: x.get("sort", 999))
        top = items[0]
        raw = top.get("title") or ""
        row = {
            "category": SHORT_NAME.get(name, name),
            "title": TRAILING_DATE.sub("", raw).strip(),
            "date": episode_date(raw),
            "poster": "", "duration": 0,
            "_id": top.get("mediaId"),
        }
        rows.append(row)
        need[row["_id"]] = row
        print("   %-24s %s" % (row["category"][:24], row["title"][:44]))

    # Category items carry no poster, so resolve each one through list_media.
    # Search is a SQL LIKE over the title, so a multi-word phrase fails the
    # moment any punctuation sits between the words -- probe with single long
    # words instead, longest first, since those are the most distinctive.
    # '%' and '_' are LIKE wildcards and would match far too much.
    for row in rows:
        words = re.findall(r"[A-Za-z0-9]{4,}", row["title"])
        words.sort(key=len, reverse=True)
        for probe in words[:4]:
            if "%" in probe or "_" in probe:
                continue
            try:
                media = unwrap(client.list_media(search=probe), "media")
            except Exception as exc:
                print("   poster lookup failed for %s: %s" % (row["category"], str(exc)[:50]))
                break
            hit = next((m for m in media if m.get("id") == row["_id"]), None)
            if hit:
                row["poster"] = hit.get("posterUrl") or ""
                row["duration"] = int(hit.get("durationSeconds") or 0)
                break

    for row in rows:
        row.pop("_id", None)
        if not row["poster"]:
            print("   NOTE: no poster resolved for %s" % row["category"])
    return rows


# ----------------------------------------------------------------------------
def main():
    with open(os.path.join(BUILDER, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)

    from channelcast_client import ChannelcastClient
    client = ChannelcastClient(cfg["base_url"], cfg["token"])
    arts = artists_by_id()

    print("Schedule:")
    blocks = build_blocks(client, cfg["channel_id"])
    print("   %d blocks across the week" % len(blocks))
    if not blocks:
        print("   ABORT: no schedules returned; nothing to build.")
        return

    print("Loops:")
    loops = build_loops(client, sorted({b["p"] for b in blocks}), arts)

    shows = []
    if "--skip-shows" not in sys.argv:
        print("Shows:")
        shows = build_shows(client, cfg["channel_id"])

    data = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "channel_id": cfg["channel_id"],
        "channel_name": cfg.get("channel_name", ""),
        "blocks": blocks,
        "loops": loops,
        "shows": shows,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, separators=(",", ":"))

    total = sum(len(v) for v in loops.values())
    print("\nWrote %s" % OUT)
    print("   %d blocks, %d loops, %d items, %d shows, %.0f KB"
          % (len(blocks), len(loops), total, len(shows), os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
