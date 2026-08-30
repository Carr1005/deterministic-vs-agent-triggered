#!/usr/bin/env python3
"""serve.py — the course viewer: two pages on localhost:4000, one per tab.

    /diffs   every round's spec change and code change, from your own git history
    /guide   how the app works now, what its memory holds, what your tutor ran

Tabs are separate URLs rather than one document with a toggle, and that is a design
decision worth keeping: only one view's HTML, CSS and JavaScript is ever on the page, so
the two can grow in completely different directions without colliding — they already
share selector names like `.d`, `.what` and `pre`. It also means a request pays for one
view, and a view that fails cannot blank the other.

Invariants inherited by everything here (see core.py):
  1. Writes NOTHING into the repository. `git status --porcelain` is the tutor's
     mid-round resume signal (course/PROTOCOL.md), so every page is built as a string,
     per request. `run.py` is the one writer, and it writes one git-ignored file.
  2. Standard library only, so setup/requirements.txt and setup/check.sh stay untouched.
  3. A window, never a gate: nothing in the course consults this server. Delete
     tools/viewer entirely and the course runs identically.
"""
import argparse
import http.server
import sys
import threading
import time

import core
import shell

HEALTH_TOKEN = "snackbot-viewer-ok"

# A view id may not shadow an infra route. Asserted at startup, not hoped for.
RESERVED = {"healthz", "state", "index.html", "favicon.ico"}


class _BrokenView:
    """Stands in for a view that could not even be imported.

    Without this, one syntax error takes down a server that serves two pages — a
    regression against the two-process arrangement this replaced, where a broken viewer
    left the other one working.
    """

    def __init__(self, view_id, exc):
        self.ID = view_id
        self.LABEL = view_id.capitalize()
        self.TITLE = f"{view_id} — unavailable"
        self.FOOTER = "This page failed to load; the rest of the viewer is unaffected."
        self.CSS = ""
        self.JS = ""
        self._exc = exc

    def render(self):
        return shell.error_card(self._exc)

    def signature(self):
        return None


def _load(module_name, view_id):
    try:
        return __import__(f"views.{module_name}", fromlist=["*"])
    except Exception as e:                       # noqa: BLE001 — deliberate, see above
        print(f"WARN  view {view_id!r} failed to import: {type(e).__name__}: {e}")
        return _BrokenView(view_id, e)


# Tuple order IS tab order — no second source of truth to fall out of sync.
VIEWS = (_load("diffs", "diffs"), _load("guide", "guide"))
BY_ID = {v.ID: v for v in VIEWS}

TEXT = "text/plain; charset=utf-8"


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "snackbot-viewer"

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _redirect(self, to):
        # 302, never 301: browsers cache a permanent redirect per origin, which would pin
        # any future localhost:4000 project to /diffs. The Location carries no fragment,
        # so the browser applies the one the learner arrived with — that is what keeps
        # the older `http://localhost:4000/#r3-build` links working.
        self.send_response(302)
        self.send_header("Location", to)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self):
        head, _, query = self.path.partition("?")
        path = head.rstrip("/") or "/"

        if path == "/healthz":
            self.server.last_seen = time.time()
            # The repo path is part of the identity, not decoration: two checkouts of
            # this course — a trial clone beside the original, a replay sandbox — would
            # otherwise recognise each other's viewer as their own, and `--ensure` would
            # hand the learner a URL serving the wrong repository.
            return self._send(200, f"{HEALTH_TOKEN} {core.REPO}", TEXT)

        if path.startswith("/state/"):
            # A poll counts as activity only when the page says it is actually on screen.
            #
            # This route is a page asking "has anything changed?", which a tab does
            # whether or not a human is present — so treating every poll as activity
            # would mean a forgotten tab kept the server alive indefinitely, and the idle
            # shutdown would never fire. Treating none of them as activity was the
            # earlier rule, and it went too far the other way: a page being read right
            # now was indistinguishable from an abandoned one, so the server died under
            # the reader. The visibility flag is what makes "someone is watching"
            # expressible at all. A backgrounded or closed tab still expires.
            if query == "watching=1":
                self.server.last_seen = time.time()
            view = BY_ID.get(path[len("/state/"):])
            if view is None:
                return self._send(404, "not found", TEXT)
            try:
                return self._send(200, view.signature() or "", TEXT)
            except Exception as e:               # noqa: BLE001
                # A constant, so a changing error string cannot start a reload storm.
                print(f"WARN  {view.ID} signature failed: {type(e).__name__}: {e}")
                return self._send(200, "error", TEXT)

        if path in ("/", "/index.html"):
            self.server.last_seen = time.time()
            return self._redirect(f"/{VIEWS[0].ID}")

        view = BY_ID.get(path.lstrip("/"))
        if view is None:
            return self._send(404, "not found", TEXT)

        self.server.last_seen = time.time()
        try:
            body = view.render()
            sig = view.signature()
        except Exception as e:                   # noqa: BLE001
            # These views read a live git history and a live sqlite file, so they can
            # meet states the code has never seen. An error card with the tab bar still
            # above it leaves the other page one click away.
            print(f"WARN  {view.ID} render failed: {type(e).__name__}: {e}")
            body, sig = shell.error_card(e), None
        self._send(200, shell.page(view, VIEWS, body, sig))

    def log_message(self, fmt, *args):   # one tidy line, to stdout only
        sys.stdout.write("  %s %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()


def reaper(httpd, idle_minutes):
    """Shut down after idle_minutes with no requests, so an orphan cannot outlive its use."""
    if idle_minutes <= 0:
        return
    while True:
        time.sleep(15)
        if time.time() - httpd.last_seen > idle_minutes * 60:
            print(f"NOTE  idle for {idle_minutes} min — shutting down.")
            sys.stdout.flush()
            httpd.shutdown()
            return


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--port", type=int, default=4000)
    ap.add_argument("--idle", type=int, default=60,
                    help="shut down after N idle minutes (0 disables)")
    a = ap.parse_args()

    for v in VIEWS:
        if v.ID in RESERVED:
            print(f"FAIL  view id {v.ID!r} would shadow an infra route.")
            return 1

    if not core.is_repo():
        print(f"FAIL  {core.REPO} is not a git repository — no course to report on.")
        return 1
    try:
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    except OSError as e:
        print(f"FAIL  cannot bind port {a.port}: {e}")
        return 1
    httpd.last_seen = time.time()
    threading.Thread(target=reaper, args=(httpd, a.idle), daemon=True).start()
    tabs = " ".join(f"/{v.ID}" for v in VIEWS)
    print(f"PASS  viewer on http://localhost:{a.port}/  ({tabs}; idle timeout {a.idle} min)")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nNOTE  stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
