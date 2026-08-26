"""
Build the local _TEST-*.html preview pages.

WHY THIS IS A FILE AND NOT A ONE-LINER
    The CMS files use absolute asset paths (/images/x.jpg) because that is what
    the CMS needs. Opened off disk, a leading slash resolves to the drive root
    and every asset silently 404s. So the preview has to rewrite those paths to
    relative -- and doing that inline, inside a shell heredoc, is exactly how a
    quoting slip once made the rewrite a no-op and left the CTA photo missing
    with no error anywhere.

    It also VERIFIES the rewrite afterwards rather than trusting it.

RUN
    python make-test.py
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read(name):
    return io.open(os.path.join(HERE, name), encoding="utf-8").read()


def localise(text):
    """Absolute CMS asset paths -> paths that work from this folder."""
    text = text.replace("url('/images/", "url('images/")
    text = text.replace('url("/images/', 'url("images/')
    text = text.replace('src="/images/', 'src="images/')
    text = text.replace("src='/images/", "src='images/")
    return text


PAGE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
{css}
</style></head><body>
{header}
<div class="page-body">
{body}
</div>
{footer}
</body></html>
"""

PLACEHOLDER = """
<div class="wrap" style="padding:60px 0;">
  <div style="border:1px dashed #37E0C8;border-radius:11px;padding:26px;color:#8a827a;font:14px/1.7 system-ui;">
    <b style="color:#37E0C8;">BODY PLACEHOLDER</b><br>
    Narrow below 900px for the mobile header and menu; below 680px for the
    centred footer.
  </div>
</div>
"""


def build(outfile, title, body):
    css = localise(read("blackmarker-tv.css"))
    header = localise(read("1-HEADER.html"))
    footer = localise(read("3-FOOTER.html")).replace(
        '<script src="images/bmtv-chat.js" defer></script>',
        "<!-- chat script omitted in this local test: it needs a real http:// origin -->",
    )
    html = PAGE.format(title=title, css=css, header=header,
                       body=localise(body), footer=footer)
    io.open(os.path.join(HERE, outfile), "w", encoding="utf-8").write(html)

    # --- verify, rather than assume ---------------------------------------
    problems = []
    for m in re.finditer(r"""(?:url\(['"]?|(?:src|href)=['"])(/[^'")\s>]+)""", html):
        ref = m.group(1)
        if ref.startswith("/images/") or ref.startswith("/chat/"):
            problems.append(ref)

    missing = []
    for m in re.finditer(r"""(?:url\(['"]?|src=['"])(images/[^'")\s>]+)""", html):
        p = os.path.join(HERE, m.group(1))
        if not os.path.exists(p):
            missing.append(m.group(1))

    print("  %-26s %6.0f KB" % (outfile, len(html) / 1024))
    if problems:
        print("     *** %d absolute path(s) left, will 404 off disk: %s"
              % (len(problems), sorted(set(problems))))
    if missing:
        print("     *** %d asset(s) referenced but not on disk: %s"
              % (len(missing), sorted(set(missing))))
    if not problems and not missing:
        refs = sorted(set(re.findall(r"""(?:url\(['"]?|src=['"])(images/[^'")\s>]+)""", html)))
        print("     all %d asset(s) resolve: %s" % (len(refs), ", ".join(refs)))
    return not (problems or missing)


def main():
    ok = True
    ok &= build("_TEST-header-footer.html", "CMS test - header + footer", PLACEHOLDER)
    for src, out, title in [
        ("4-BODY-CONTACT.html",  "_TEST-contact.html",  "CMS test - Contact page"),
        ("7-BODY-CALENDAR.html", "_TEST-calendar.html", "CMS test - Calendar page"),
        ("10-BODY-SCHEDULE.html", "_TEST-schedule.html", "CMS test - Schedule page"),
        ("11-BODY-BODEGA.html",  "_TEST-bodega.html",   "CMS test - The Bodega"),
        ("12-BODY-PARTNERSHIPS.html", "_TEST-partnerships.html", "CMS test - Partnerships"),
        ("13-BODY-ADVERTISING.html",  "_TEST-advertising.html",  "CMS test - Advertising"),
        ("14-BODY-PRODUCTION.html",   "_TEST-production.html",   "CMS test - Production"),
        ("15-BODY-SUBMIT-MUSIC.html", "_TEST-submit-music.html", "CMS test - Submit Your Music"),
        ("16-BODY-ACCOUNT.html",      "_TEST-account.html",      "CMS test - Account"),
        ("26-HOME-1-PLAYER-CHAT.html","_TEST-home1.html",       "CMS test - Home section 1"),
        ("17-BODY-CAN-YOU-DIG-IT.html","_TEST-cudi.html",       "CMS test - Can You Dig It"),
        ("18-BODY-WEEKLY-INTERRUPT.html", "_TEST-weekly-interrupt.html", "CMS test - Weekly Interrupt"),
        ("19-BODY-FOR-THE-RECORD.html", "_TEST-for-the-record.html", "CMS test - For The Record"),
        ("20-BODY-ALIEN-PODCAST.html", "_TEST-alien-podcast.html", "CMS test - Alien Podcast"),
        ("21-BODY-TALKING-TIPSY.html", "_TEST-talking-tipsy.html", "CMS test - Talking Tipsy"),
        ("22-BODY-DUH-DIGGITY.html", "_TEST-duh-diggity.html", "CMS test - Duh Diggity"),
        ("23-BODY-2-BAFOONZ.html", "_TEST-2-bafoonz.html", "CMS test - 2 Bafoonz"),
        ("24-BODY-PERFORMANCE-BATTLES.html", "_TEST-performance-battles.html", "CMS test - Performance Battles"),
        ("25-BODY-SPECIAL-INTERRUPTS.html", "_TEST-special-interrupts.html", "CMS test - Special Interrupts"),
    ]:
        if os.path.exists(os.path.join(HERE, src)):
            ok &= build(out, title, read(src))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
