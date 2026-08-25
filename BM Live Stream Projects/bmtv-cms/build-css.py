"""
Merge every <style> block in the 3.0 preview pages into one stylesheet.

WHY
    The CMS takes one CSS template. The preview pages each carry their own
    inline <style>, which is fine for standalone files and useless for a CMS.

WHAT IT GUARANTEES
    Two things are checked rather than hoped for, because a silent break here
    would show up as "some page looks wrong" days later:

    1. CONFLICTS. If the same selector is defined differently on different
       pages, merging them means the last one silently wins everywhere. Every
       such case is reported. (As of 2026-08-25 there is exactly one, and it is
       an artefact of moving the chat panel's styles into bmtv-chat.js.)

    2. CASCADE ORDER. Rules of equal specificity are resolved by order, so the
       merged file has to keep every page's rules in their original relative
       order. Unseen rules are inserted at the position they held on their own
       page, not appended, and the result is verified as a supersequence of
       all 18 pages before it is written.

RUN
    python build-css.py
"""

import os
import re
import glob
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
PREVIEW = os.path.join(os.path.dirname(os.path.dirname(HERE)), "blackmarker-tv-3-preview")
OUT = os.path.join(HERE, "blackmarker-tv.css")

AT_RULE = re.compile(r'@(media|supports|layer|container)\b')


def blocks(css, ctx=""):
    """Ordered stream of ('comment', text) and ('rule', ctx, selector, decls)."""
    out, i, n, buf = [], 0, len(css), ""
    while i < n:
        if css.startswith("/*", i):
            j = css.find("*/", i + 2)
            j = n if j < 0 else j + 2
            if not buf.strip():
                out.append(("comment", css[i:j]))
            i = j
            continue
        c = css[i]
        if c == "{":
            depth, j = 1, i + 1
            while j < n and depth:
                if css[j] == "{":
                    depth += 1
                elif css[j] == "}":
                    depth -= 1
                j += 1
            head = re.sub(r"\s+", " ", buf.strip())
            body = css[i + 1:j - 1]
            if head.startswith("@") and AT_RULE.match(head):
                out += blocks(body, head if not ctx else ctx + " and " + head)
            else:
                out.append(("rule", ctx, head, body.strip()))
            buf = ""
            i = j
        else:
            buf += c
            i += 1
    return out


def key_of(item):
    return ("c", item[1].strip()) if item[0] == "comment" else ("r", item[1], item[2])


def main():
    files = sorted(glob.glob(os.path.join(PREVIEW, "*.html")))
    pages = {}
    for f in files:
        html = open(f, encoding="utf-8", errors="replace").read()
        css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
        pages[os.path.basename(f)] = blocks(css)
    print("read %d pages" % len(pages))

    # --- conflicts ---------------------------------------------------------
    defs = {}
    for name, items in pages.items():
        for it in items:
            if it[0] != "rule":
                continue
            norm = ";".join(p.strip() for p in it[3].split(";") if p.strip())
            defs.setdefault((it[1], it[2]), {}).setdefault(norm, []).append(name)
    conflicts = {k: v for k, v in defs.items() if len(v) > 1}
    print("selectors: %d unique, %d defined differently by page"
          % (len(defs), len(conflicts)))
    for (ctx, sel), variants in conflicts.items():
        print("   CONFLICT %s%s" % (("[" + ctx + "] ") if ctx else "", sel))
        for d, names in variants.items():
            print("      %2d page(s): %s" % (len(names), ", ".join(n[:28] for n in names[:3])))
        print("      -> merged by union; check the result if these disagree on a property")

    # --- merge, keeping each page's relative order -------------------------
    # The homepage leads because it is the template everything else is built
    # from. An unseen rule is inserted right after the last rule already placed
    # from the same page, never appended, so relative order survives.
    lead = "BlackMarkerTV-3-LIVE-PREVIEW.html"
    order = ([lead] if lead in pages else []) + sorted(
        (p for p in pages if p != lead), key=lambda p: -len(pages[p]))

    merged, at = [], {}
    for name in order:
        cursor = -1
        for it in pages[name]:
            k = key_of(it)
            if k in at:
                cursor = at[k]
                continue
            cursor += 1
            merged.insert(cursor, it)
            for kk in at:
                if at[kk] >= cursor:
                    at[kk] += 1
            at[k] = cursor
    # Union the declarations of any selector defined differently by page.
    # Property-wise, not string concatenation: appending whole blocks would
    # repeat every shared property once per page. Order of first appearance is
    # kept, and a property redefined with a different value keeps the later one
    # (CSS semantics inside a block) and is reported.
    def decl_pairs(text):
        pairs = []
        for part in text.split(";"):
            part = part.strip()
            if not part or ":" not in part:
                continue
            prop, val = part.split(":", 1)
            pairs.append((prop.strip(), val.strip()))
        return pairs

    variants = {}
    for name in order:
        for it in pages[name]:
            if it[0] == "rule":
                variants.setdefault(key_of(it), []).append(it[3])

    for k, texts in variants.items():
        if len(set(texts)) < 2:
            continue
        ordered, seen_props = [], {}
        for t in texts:
            for prop, val in decl_pairs(t):
                if prop in seen_props:
                    if seen_props[prop] != val:
                        print("      note: %s redefines %s (%s -> %s); keeping the later value"
                              % (k[2], prop, seen_props[prop], val))
                        ordered[[p for p, _ in ordered].index(prop)] = (prop, val)
                        seen_props[prop] = val
                    continue
                seen_props[prop] = val
                ordered.append((prop, val))
        i = at[k]
        cur = merged[i]
        merged[i] = ("rule", cur[1], cur[2],
                     ";".join("%s:%s" % (p, v) for p, v in ordered) + ";")

    # --- verify ------------------------------------------------------------
    pos = {}
    for i, it in enumerate(merged):
        if it[0] == "rule":
            pos[(it[1], it[2])] = i
    bad = []
    for name, items in pages.items():
        seq = [pos[(it[1], it[2])] for it in items if it[0] == "rule"]
        if seq != sorted(seq):
            bad.append(name)
    print("cascade order preserved : %s"
          % ("YES for all %d pages" % len(pages) if not bad else "NO -> " + ", ".join(bad)))
    if bad:
        print("REFUSING to write a stylesheet that reorders rules.")
        return

    # --- write -------------------------------------------------------------
    # --- glyphs -> CSS escapes -------------------------------------------
    # The dropdown arrow is content:"▾" (U+25BE). Delivered as a raw character
    # it depends on the browser guessing UTF-8; if the CMS serves the stylesheet
    # as latin-1, or the page has no <meta charset>, it renders as mojibake.
    # A CSS escape carries no encoding assumption at all, so it always works.
    glyphs = 0
    for i, it in enumerate(merged):
        if it[0] != "rule" or "content" not in it[3]:
            continue
        def esc(m):
            global_count = m.group(0)
            return "".join(
                ("\\%04X " % ord(c)) if ord(c) > 127 else c for c in global_count)
        new = re.sub(r'content\s*:\s*"[^"]*"',
                     lambda m: esc(m) if any(ord(c) > 127 for c in m.group(0)) else m.group(0),
                     it[3])
        if new != it[3]:
            glyphs += 1
            merged[i] = ("rule", it[1], it[2], new)
    print("glyphs escaped in content: %d" % glyphs)

    # --- CMS override guard ----------------------------------------------
    # Pasted into someone else's CMS, the site's links compete with the CMS's
    # own global stylesheet, which may load after this one. Two symptoms seen
    # in practice: underlines appearing on hover, and hover colours changing.
    #
    # text-decoration is safe to force: it appears exactly once in this whole
    # design, as `none`. The design never underlines anything.
    #
    # Colour is not safe to force blindly -- 29 rules set deliberate hover
    # colours. So the guard resets links to `inherit`, then re-asserts every
    # colour the design sets on an anchor, at !important, after the reset.
    # The anchor class list is read out of the real HTML rather than guessed.
    anchor_classes = set()
    for f in files:
        html = open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'<a\b[^>]*\bclass\s*=\s*"([^"]+)"', html):
            anchor_classes.update(m.group(1).split())

    def targets_anchor(sel):
        for part in sel.split(","):
            part = part.strip()
            if re.search(r'(^|[\s>+~])a([.:\[\s>+~]|$)', part):
                return True
            for c in anchor_classes:
                if re.search(r'\.' + re.escape(c) + r'([.:\[\s>+~]|$)', part):
                    return True
        return False

    reasserts = []
    for it in merged:
        if it[0] != "rule":
            continue
        if not targets_anchor(it[2]):
            continue
        cols = [p.strip() for p in it[3].split(";")
                if p.strip().startswith("color:")]
        if not cols:
            continue
        val = cols[-1].split(":", 1)[1].strip()
        reasserts.append((it[1], it[2], val))

    guard = [
        "",
        "/* =====================================================================",
        "   CMS OVERRIDE GUARD  (generated -- keep this LAST in the stylesheet)",
        "",
        "   The CMS ships its own global styles and may load them after this",
        "   file. Without this block its rules win on any link that relies on",
        "   the bare `a{color:inherit}` -- the logo, the top-bar button, card",
        "   links, the footer logo -- which shows up as underlines on hover and",
        "   the wrong hover colour.",
        "",
        "   Underlines are forced off outright: text-decoration appears exactly",
        "   once in this entire design, as `none`. Nothing here is underlined by",
        "   intent, so there is nothing to lose.",
        "",
        "   Colour is handled the other way round -- reset to inherit, then every",
        "   colour the design deliberately sets on a link is re-asserted below.",
        "   ===================================================================== */",
        "a,a:link,a:visited,a:hover,a:active,a:focus{text-decoration:none !important;}",
        "a,a:link,a:visited,a:hover,a:active,a:focus{color:inherit !important;}",
        "a:focus-visible{outline:2px solid var(--red);outline-offset:2px;}",
        "",
        "/* the design's own link colours, re-asserted so the reset above cannot eat them */",
    ]
    # A re-assertion has to out-specify the reset above, and the reset carries
    # link pseudo-classes: a:link is (0,1,1), which beats a bare .topbar-btn at
    # (0,1,0). Both are !important, so specificity decides and the reset wins --
    # which is exactly how the Submit Your Music button ended up inheriting the
    # top bar's grey. Emitting the same pseudo-class states alongside each
    # selector lifts it above the reset in every state.
    STATES = (":link", ":visited", ":hover", ":active", ":focus")

    # Which selectors already have a deliberate hover COLOUR in the design?
    # Propagating a rest-state colour into :hover would override them --
    # .socials a.s-yt:hover at (0,3,1) beats .socials a:hover at (0,2,1), which
    # is how the social icons stopped turning white on hover while their
    # backgrounds still went brand-colour.
    hover_colour_sels = []
    for it in merged:
        if it[0] != "rule" or ":hover" not in it[2]:
            continue
        if not any(p.strip().startswith("color:") for p in it[3].split(";")):
            continue
        for one in it[2].split(","):
            one = one.strip()
            if ":hover" in one:
                hover_colour_sels.append(one.replace(":hover", ""))

    def compounds(sel):
        return [c for c in re.split(r'\s*[>+~]\s*|\s+', sel.strip()) if c]

    def simples(compound):
        return set(re.findall(r'(?:[.#]?[\w-]+|\[[^\]]*\]|::?[\w-]+(?:\([^)]*\))?)', compound))

    def generalises(general, specific):
        """True if `general` matches at least everything `specific` does."""
        g, s = compounds(general), compounds(specific)
        if not g or len(g) > len(s):
            return False
        if not simples(g[-1]) <= simples(s[-1]):
            return False
        # remaining ancestor parts must appear, in order, among s's ancestors
        gi = 0
        for part in s[:-1]:
            if gi < len(g) - 1 and simples(g[gi]) <= simples(part):
                gi += 1
        return gi == len(g) - 1

    def with_states(sel):
        parts = []
        for one in [s.strip() for s in sel.split(",") if s.strip()]:
            parts.append(one)
            if re.search(r':(link|visited|hover|active|focus)\b', one):
                continue
            # If the design defines a hover colour covering this element, add NO
            # pseudo variants at all -- not even :link. An unvisited anchor
            # matches :link the whole time, hover included, so
            # `.socials a.s-yt:link` (0,3,1) would outrank the design's
            # `.socials a:hover` (0,2,1) and pin the rest colour on hover.
            #
            # The bare selector is enough on its own: `.socials a.s-yt` (0,2,1)
            # still beats every reset line (highest is a:link at (0,1,1)), and
            # ties with `.socials a:hover`, which is emitted later and therefore
            # wins the tie exactly when it should.
            if any(generalises(h, one) for h in hover_colour_sels):
                continue
            parts += [one + st for st in STATES]
        return ",".join(parts)

    ctx2 = ""
    for c, sel, val in reasserts:
        if c != ctx2:
            if ctx2:
                guard.append("}")
            if c:
                guard.append(c + "{")
            ctx2 = c
        guard.append("%s%s{color:%s !important;}"
                     % ("  " if ctx2 else "", with_states(sel), val))
    if ctx2:
        guard.append("}")
    print("link colours re-asserted: %d" % len(reasserts))

    head = [
        '@charset "UTF-8";',
        "",
        "/* =====================================================================",
        "   BlackMarker.TV 3.0 — site stylesheet",
        "",
        "   Generated %s by bmtv-cms/build-css.py" % dt.date.today().isoformat(),
        "   Merged from the <style> blocks of %d preview pages." % len(pages),
        "   Verified: no rule reordering, %d selector conflict(s)." % len(conflicts),
        "",
        "   PASTE THIS WHOLE FILE into the CMS stylesheet template.",
        "",
        "   NOT IN HERE, on purpose:",
        "     * Chat panel styles. bmtv-chat.js injects its own, scoped under",
        "       .bmtv-chat, reading --red/--surface/--border from this file when",
        "       they exist. Nothing to paste for chat.",
        "     * Web fonts. There are none — the site uses the system UI stack.",
        "",
        "   IMAGES: no image files are referenced from this stylesheet. The only",
        "   url() values are inline SVG data URIs for a few small icons, which",
        "   stay as they are. The /images/<filename> rule applies to the HTML",
        "   sections (img src, script src), not to this file.",
        "   ===================================================================== */",
        "",
    ]

    out, ctx = [], ""
    for it in merged:
        if it[0] == "comment":
            if ctx:
                out.append("}")
                ctx = ""
            out.append("\n" + it[1])
            continue
        _, c, sel, decl = it
        if c != ctx:
            if ctx:
                out.append("}")
            if c:
                out.append("\n" + c + "{")
            ctx = c
        out.append("%s%s{%s}" % ("  " if ctx else "", sel, decl))
    if ctx:
        out.append("}")

    # Hand-written CMS-only CSS (the mobile menu lives here). Appended after
    # the generated rules so it can override them, and before the guard so the
    # guard stays last.
    extra = ""
    add_path = os.path.join(HERE, "additions.css")
    if os.path.exists(add_path):
        extra = "\n\n" + open(add_path, encoding="utf-8").read().rstrip() + "\n"
        print("appended additions.css  (%.1f KB)" % (len(extra) / 1024))

    body = "\n".join(head) + "\n".join(out) + "\n" + extra + "\n".join(guard) + "\n"
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(body)
    print("wrote %s  (%d rules, %.0f KB)"
          % (OUT, sum(1 for i in merged if i[0] == "rule"), len(body) / 1024))


if __name__ == "__main__":
    main()
