"""
Full-library media scan -- the only reliable way to read every item's status.

`list_media` takes a search string and returns AT MOST 100 rows, with no paging
parameter of any kind (limit/take/page/skip/offset are all ignored). It does
report `total`, the true number of matches, which is what makes a complete
enumeration possible: search each term, and whenever a term is capped, split it
into longer terms until every term comes back under the cap.

Two things keep that from exploding into thousands of calls:

  * seed terms -- the naming-convention prefixes the library already uses pick up
    the bulk of the catalogue in ~50 calls.
  * coverage pruning -- for any term we can count how many ALREADY-KNOWN items
    match it locally. Server search is a superset of a title/filename substring
    match, so local_count can never exceed `total`; when they are equal we hold
    every row that term could return and never have to expand it.

The scan is finished, provably, when the number of unique ids collected equals
the `total` reported for an unfiltered search.
"""

import string

# '%' and '_' are LIKE wildcards on the server (searching "%" returns the whole
# catalogue), so they can never be used as literal search characters. Everything
# else that actually shows up in filenames is fair game.
CHARSET = list(string.ascii_lowercase + string.digits) + [
    " ", "-", ".", "#", "(", ")", "&", "'", "!", "+", ",", "@"]

CAP = 100          # server's hard row limit per search
MAX_CALLS = 4000   # runaway guard


def _matches(item, term):
    """Local stand-in for the server's search: substring over title + filename,
    case-insensitive. Deliberately narrower than the server (which also searches
    tags), so a mismatch only ever causes an extra call, never a missed item."""
    t = term.lower()
    return t in item["_hay"]


def scan_all_media(client, seed_terms=(), on_progress=None):
    """Enumerate every media item with its status.

    on_progress(info) is called after each API call with
    {calls, found, total, term, complete}.

    Returns {"items": [...], "total": int, "complete": bool, "calls": int}
    where complete=True means the scan is provably exhaustive.
    """
    seen = {}
    calls = 0
    grand_total = None

    def fetch(term):
        """One search. Returns the server's `total` for the term, or None on error."""
        nonlocal calls, grand_total
        args = {"search": term} if term is not None else {"search": None}
        try:
            data = client.call_tool("list_media", args)
        except Exception:
            return None
        calls += 1
        total = data.get("total")
        if term is None:
            grand_total = total
        for m in data.get("media", []):
            mid = m["id"]
            if mid not in seen:
                name = m.get("filename") or m.get("title") or ""
                seen[mid] = {
                    "id": mid,
                    "title": m.get("title", ""),
                    "filename": name,
                    "status": m.get("status", ""),
                    "processing": m.get("processing", ""),
                    "durationSeconds": m.get("durationSeconds", 0),
                    "_hay": (name + " " + m.get("title", "")).lower(),
                }
        if on_progress:
            on_progress({"calls": calls, "found": len(seen),
                         "total": grand_total, "term": term or "(all)",
                         "complete": False})
        return total

    def covered(term, total):
        """True when everything this term could return is already in hand."""
        if total is None:
            return True
        return sum(1 for it in seen.values() if _matches(it, term)) >= total

    fetch(None)                                   # establishes the grand total
    for t in seed_terms:
        if calls < MAX_CALLS:
            fetch(t)

    # Breadth-first over search terms: only terms that come back capped AND are
    # not already fully covered get expanded by one character.
    queue = [c for c in CHARSET]
    while queue and calls < MAX_CALLS:
        if grand_total is not None and len(seen) >= grand_total:
            break
        term = queue.pop(0)
        total = fetch(term)
        if total is None or total < CAP:
            continue                              # term exhausted in one call
        if covered(term, total):
            continue                              # already have all of them
        queue.extend(term + c for c in CHARSET)

    complete = grand_total is not None and len(seen) >= grand_total
    items = []
    for it in seen.values():
        it = dict(it)
        it.pop("_hay", None)
        items.append(it)
    if on_progress:
        on_progress({"calls": calls, "found": len(items),
                     "total": grand_total, "term": "", "complete": complete})
    return {"items": items, "total": grand_total, "complete": complete,
            "calls": calls}
