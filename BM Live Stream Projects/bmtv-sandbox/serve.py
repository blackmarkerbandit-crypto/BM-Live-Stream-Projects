"""
BMB Sandbox Server -- static host for BlackMarker.TV work-in-progress.

Stdlib only. No pip install, no venv, nothing to keep updated.

Serves several folders from around the tree under one origin so that pages
needing a real http:// origin (Supabase realtime, fetch, service workers)
behave the way they will on the live site. Explicit mounts only -- the rest
of the AI SHIT tree (financials, business plans) is never reachable.

Adds two things plain http.server does not have:
  * server-side includes -- <!--#include file="x.html"--> is replaced with
    the contents of x.html at request time, so a demo page can pull in the
    real widget file instead of holding a stale copy of it.
  * no-cache headers on everything, so a browser refresh always shows the
    file as it is on disk right now.

Start it: run.bat   (or: python serve.py)
"""

import os
import re
import sys
import posixpath
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.dirname(HERE)                 # BM Live Stream Projects
ROOT = os.path.dirname(PROJECTS)                 # AI SHIT

PORT = int(os.environ.get("BMB_SANDBOX_PORT", "8790"))
HOST = os.environ.get("BMB_SANDBOX_HOST", "127.0.0.1")

# Only used when there is no console to log to (the autostart task).
LOGFILE = os.path.join(HERE, "serve.log")

# url prefix -> (folder on disk, label for the index page)
MOUNTS = {
    "sandbox": (HERE, "Sandbox pages (demo hosts built for this server)"),
    "chat": (os.path.join(PROJECTS, "bmtv-chat"), "Live chat build -- widget, moderator panel, vMix overlay"),
    "preview": (os.path.join(ROOT, "blackmarker-tv-3-preview"), "BlackMarker.TV 3.0 preview site (18 pages)"),
    "build": (os.path.join(PROJECTS, "blackmarker-tv-3-build"), "3.0 CMS build kit -- css, js, partials, templates"),
}

# Shortcuts shown on the landing page: (url, title, note)
FEATURED = [
    ("/sandbox/chat-demo.html", "Live chat demo",
     "The real Supabase widget on a host page. Type here, moderate in the panel, watch it hit the overlay."),
    ("/chat/moderator.html", "Moderator panel",
     "Sign in with a moderator EMAIL account -- anonymous logins lose access when cookies clear."),
    ("/chat/vmix-overlay.html", "vMix overlay",
     "What a vMix Browser input shows. Only released messages appear. ?pos=top &hold=20 &size=1.25"),
    ("/preview/BlackMarkerTV-3-LIVE-PREVIEW.html", "3.0 Live page (preview)",
     "Still the placeholder chat -- local echo only. Injecting the real widget here is the next step."),
]

INCLUDE_RE = re.compile(rb'<!--#include\s+file="([^"]+)"\s*-->')


def _within_mounts(path):
    """True if an absolute path sits inside one of the mounted folders."""
    real = os.path.realpath(path)
    for folder, _ in MOUNTS.values():
        root = os.path.realpath(folder)
        if real == root or real.startswith(root + os.sep):
            return True
    return False


def _index_page():
    rows = []
    for url, title, note in FEATURED:
        rows.append(
            '<a class="card" href="' + escape(url) + '">'
            '<div class="t">' + escape(title) + '</div>'
            '<div class="n">' + escape(note) + '</div>'
            '<div class="u">' + escape(url) + '</div></a>'
        )
    mounts = []
    for prefix, (path, label) in MOUNTS.items():
        live = "ok" if os.path.isdir(path) else "missing"
        mounts.append(
            '<tr><td><a href="/' + prefix + '/">/' + prefix + '/</a></td>'
            '<td>' + escape(label) + '</td>'
            '<td class="' + live + '">' + live + '</td></tr>'
        )
    return (_INDEX_TMPL
            .replace("__HOSTPORT__", escape(HOST) + ":" + str(PORT))
            .replace("__CARDS__", "".join(rows))
            .replace("__MOUNTS__", "".join(mounts))
            .encode("utf-8"))


_INDEX_TMPL = """<!doctype html><html><head><meta charset="utf-8">
<title>BMB Sandbox</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--red:#E8181C;--bg:#0a0908;--surface:#141210;--surface2:#1c1917;
--border:#2a2622;--text:#F2EFEC;--muted:#8a827a;--ann:#37E0C8;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font:16px/1.55 system-ui,"Segoe UI",Roboto,Arial,sans-serif;
padding:38px 22px;-webkit-font-smoothing:antialiased}
.wrap{max-width:900px;margin:0 auto}
h1{font-size:23px;letter-spacing:-.02em;margin-bottom:5px}
h1 b{color:var(--red)}
.sub{color:var(--muted);font-size:13px;margin-bottom:30px}
h2{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ann);
margin:34px 0 13px;font-weight:800}
.card{display:block;background:var(--surface);border:1px solid var(--border);border-radius:11px;
padding:15px 17px;margin-bottom:10px;color:inherit;text-decoration:none;transition:.15s}
.card:hover{border-color:var(--red);background:var(--surface2)}
.card .t{font-weight:800;font-size:14.5px;margin-bottom:3px}
.card .n{color:var(--muted);font-size:12.5px}
.card .u{color:#6b645d;font-size:11px;font-family:ui-monospace,Consolas,monospace;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}
td{padding:9px 11px;border-bottom:1px solid var(--border);vertical-align:top}
td a{color:var(--red);text-decoration:none;font-family:ui-monospace,Consolas,monospace}
td.ok{color:#4ecb8b} td.missing{color:var(--red)}
.foot{margin-top:34px;padding-top:16px;border-top:1px solid var(--border);
color:#6b645d;font-size:11.5px;line-height:1.7}
code{font-family:ui-monospace,Consolas,monospace;color:var(--muted)}
</style></head><body><div class="wrap">
<h1><b>BMB</b> Sandbox</h1>
<div class="sub">Local staging for BlackMarker.TV work in progress &middot; __HOSTPORT__</div>
<h2>Start here</h2>
__CARDS__
<h2>Mounted folders</h2>
<table>__MOUNTS__</table>
<div class="foot">
Explicit mounts only &mdash; nothing else in the tree is reachable from this server.<br>
Every response is sent no-cache, so a browser refresh always shows the file on disk.<br>
<code>&lt;!--#include file="x.html"--&gt;</code> in any served .html is replaced at request time.
</div>
</div></body></html>"""

_LISTING_TMPL = """<!doctype html><meta charset="utf-8"><title>__PATH__</title>
<style>body{background:#0a0908;color:#F2EFEC;font:15px/1.7 ui-monospace,Consolas,monospace;padding:34px}
a{color:#E8181C;text-decoration:none}a:hover{text-decoration:underline}
h1{font-size:15px;color:#8a827a;font-weight:400;margin-bottom:16px}
ul{list-style:none}</style>
<h1>__PATH__</h1><ul><li><a href="../">../</a></li>__ITEMS__</ul>"""


class _Bytes:
    """send_head() must return a readable file object; wrap an in-memory body."""

    def __init__(self, data):
        self._data = data
        self._pos = 0

    def read(self, n=-1):
        if n is None or n < 0:
            out, self._pos = self._data[self._pos:], len(self._data)
        else:
            out = self._data[self._pos:self._pos + n]
            self._pos += len(out)
        return out

    def close(self):
        pass


class Handler(SimpleHTTPRequestHandler):
    server_version = "BMBSandbox/1.0"

    def translate_path(self, path):
        path = unquote(urlparse(path).path)
        parts = [p for p in posixpath.normpath(path).split("/") if p and p not in (".", "..")]
        if not parts:
            return None
        mount = MOUNTS.get(parts[0])
        if not mount:
            return None
        return os.path.join(mount[0], *parts[1:])

    def send_head(self):
        if self.path in ("/", "/index.html"):
            return self._send_body(_index_page(), "text/html; charset=utf-8")

        target = self.translate_path(self.path)
        if target is None:
            self.send_error(404, "Not a mounted path -- see / for the list")
            return None
        if os.path.isdir(target):
            if not self.path.endswith("/"):
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            index = os.path.join(target, "index.html")
            if os.path.isfile(index):
                return self._serve_file(index)
            return self._listing(target)
        if not os.path.isfile(target):
            self.send_error(404, "File not found")
            return None
        return self._serve_file(target)

    def _serve_file(self, target):
        try:
            with open(target, "rb") as fh:
                body = fh.read()
        except OSError:
            self.send_error(404, "File not found")
            return None

        ctype = mimetypes.guess_type(target)[0] or "application/octet-stream"
        if ctype == "text/html":
            body = self._expand_includes(body, os.path.dirname(target))
            ctype = "text/html; charset=utf-8"
        return self._send_body(body, ctype)

    def _expand_includes(self, body, base, depth=0):
        if depth > 5:
            return body

        def sub(m):
            name = m.group(1).decode("utf-8")
            # Resolve relative to the including file -- ".." is allowed so a
            # sandbox page can pull in the real file from a sibling folder --
            # then confirm the result still lands inside a mounted root.
            path = os.path.realpath(os.path.join(base, name.replace("/", os.sep)))
            if not _within_mounts(path):
                return ("<!-- include outside mounted roots: " + name + " -->").encode("utf-8")
            try:
                with open(path, "rb") as fh:
                    return self._expand_includes(fh.read(), os.path.dirname(path), depth + 1)
            except OSError:
                return ("<!-- include not found: " + name + " -->").encode("utf-8")

        return INCLUDE_RE.sub(sub, body)

    def _listing(self, target):
        names = sorted(os.listdir(target),
                       key=lambda n: (not os.path.isdir(os.path.join(target, n)), n.lower()))
        items = []
        for n in names:
            slash = "/" if os.path.isdir(os.path.join(target, n)) else ""
            items.append('<li><a href="' + escape(n) + slash + '">' + escape(n) + slash + '</a></li>')
        body = (_LISTING_TMPL
                .replace("__PATH__", escape(self.path))
                .replace("__ITEMS__", "".join(items))
                .encode("utf-8"))
        return self._send_body(body, "text/html; charset=utf-8")

    def _send_body(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        return _Bytes(body)

    def log_message(self, fmt, *args):
        # Under pythonw.exe (how the autostart task runs it) there is no
        # console and sys.stderr is None -- writing to it blindly raises
        # inside the handler and the browser sees the connection drop.
        # Same trap the virtual-office service hit with uvicorn's logger.
        line = "%s  %s\n" % (self.log_date_time_string(), fmt % args)
        if sys.stderr is not None:
            sys.stderr.write(line)
            return
        try:
            if os.path.exists(LOGFILE) and os.path.getsize(LOGFILE) > 2_000_000:
                os.replace(LOGFILE, LOGFILE + ".1")
            with open(LOGFILE, "a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError:
            pass


def main():
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("image/svg+xml", ".svg")
    try:
        srv = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        # Almost always the autostart task already holding the port.
        print("Could not bind %s:%d -- %s" % (HOST, PORT, exc))
        print("The sandbox is probably already running. Open http://%s:%d/" % (HOST, PORT))
        print("To take it over from a console: schtasks /end /tn \"BMB Sandbox Server\"")
        sys.exit(1)
    print("=" * 62)
    print("  BMB Sandbox Server")
    print("  http://%s:%d" % (HOST, PORT))
    print("=" * 62)
    for prefix, (path, _) in MOUNTS.items():
        flag = "" if os.path.isdir(path) else "   [MISSING]"
        print("  /%-9s -> %s%s" % (prefix + "/", path, flag))
    print("=" * 62)
    print("  Ctrl+C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        srv.server_close()


if __name__ == "__main__":
    main()
