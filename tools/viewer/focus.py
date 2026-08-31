#!/usr/bin/env python3
"""focus.py — point an already-open viewer page at a section.

    python3 tools/viewer/focus.py r3
    python3 tools/viewer/focus.py r3-spec
    python3 tools/viewer/focus.py --page diffs r3-build

The tutor cites a URL in the terminal; a page that is already on screen scrolls itself
there, opening the card if it is collapsed. One thing it cannot do, and no page can:
**bring the browser to the front.** Raising a window needs a user gesture, so if the
learner is looking at the terminal, nothing visible happens until they switch over — at
which point they find the right section instead of the top of the page.

Writes one file in $TMPDIR and nothing else. Never touches the repository:
`git status --porcelain` is the tutor's mid-round resume signal (course/PROTOCOL.md), and
serve.sh already fixes the rule that viewer state lives outside the tree. So this cannot
dirty a working copy, needs no .gitignore entry, and is safe to run mid-round.

A window, never a gate (serve.py's third invariant): if no viewer is running, this writes
the pointer, says so, and changes nothing about the course.
"""
import argparse
import json
import sys
import time
import urllib.request

import core

DEFAULT_PAGE = "guide"


def viewer_answers(port):
    """Is one of OUR viewers on this port? Repo path is part of the identity, as in
    serve.sh's `ours()` — a trial clone's viewer must not be mistaken for this one."""
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/healthz", timeout=0.4) as r:
            return r.read().decode().strip() == f"snackbot-viewer-ok {core.REPO}"
    except Exception:                            # noqa: BLE001 — absence is the answer
        return False


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("anchor", nargs="?", default="",
                    help="section id, e.g. r3 or r3-spec (omit for the top of the page)")
    ap.add_argument("--page", default=DEFAULT_PAGE, choices=("guide", "diffs"))
    ap.add_argument("--port", type=int, default=4000)
    a = ap.parse_args()

    anchor = a.anchor.lstrip("#")
    target = f"/{a.page}" + (f"#{anchor}" if anchor else "")
    if not core.FOCUS_TARGET.match(target):
        print(f"FAIL  {target!r} is not a section on this viewer.")
        return 1

    # time_ns, not a counter: monotonic without reading the previous file, so a lost or
    # hand-deleted file cannot make the next pointer look older than one already seen.
    path = core.focus_path()
    try:
        path.write_text(json.dumps({"seq": time.time_ns(), "target": target,
                                    "repo": str(core.REPO)}), encoding="utf-8")
    except OSError as e:
        print(f"FAIL  could not write {path}: {e}")
        return 1

    url = f"http://localhost:{a.port}{target}"
    if viewer_answers(a.port):
        print(f"PASS  pointed the open page at {url}")
        print("      A visible tab follows within ~3s. A background tab cannot raise "
              "itself; it will be in the right place when the learner switches to it.")
    else:
        print(f"NOTE  no viewer of this repo on port {a.port} — pointer saved, nothing to "
              f"move yet.\n      Start one with: bash tools/viewer/serve.sh --ensure")
        print(f"      {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
