#!/usr/bin/env python3
"""run.py — transparent wrapper: run a course script, and put the run on the guide page.

The tutor uses this instead of calling the app directly WHEN — and only when — the
learner asks the tutor to run something on their behalf:

    .venv/bin/python tools/viewer/run.py src/snackbot.py --x5
    .venv/bin/python tools/viewer/run.py setup/show_memory.py

It spawns the same interpreter on the given script, streams every output line to the
terminal unchanged, and preserves the exit code — then appends one JSON line describing
the run to core.RUN_LOG, which the guide page at localhost:4000/guide renders.

Contract, in order of precedence:

  1. THE RUN IS SACRED. The child's stdout/stderr reach the terminal verbatim and
     unbuffered, and its exit code is this process's exit code. Logging is best-effort:
     if the append fails for any reason, one NOTE line is printed and nothing else
     changes. Tooling must never break or alter a course run.
  2. It writes exactly ONE file — the run log, which is git-ignored. `git status
     --porcelain` is the tutor's mid-round resume signal (course/PROTOCOL.md), so
     nothing this file writes may ever show up as a working-tree change. The database
     is opened read-only, git is only read, no tracked file is touched.
  3. Stdlib only, so setup/requirements.txt and setup/check.sh stay untouched.

The record stores the RAW output; meter lines, tool lines and SAFE counts are parsed at
render time by views/guide.py, so there is exactly one source of truth for what a run
printed.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone

import core
from core import RUN_LOG

OUTPUT_CAP = 20_000          # chars kept per record; --x5 with tool spam fits well under


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: .venv/bin/python tools/viewer/run.py <script.py> [args ...]")
        return 2

    # -u so the learner sees the child's lines the moment they print, not at exit.
    cmd = [sys.executable, "-u", *sys.argv[1:]]
    start = time.perf_counter()
    kept, kept_len, truncated = [], 0, False

    proc = subprocess.Popen(cmd, cwd=core.REPO, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace",
                            bufsize=1)
    try:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if kept_len < OUTPUT_CAP:
                kept.append(line)
                kept_len += len(line)
            else:
                truncated = True
        rc = proc.wait()
    except KeyboardInterrupt:
        # Ctrl-C mid-run: stop the child, but still record what it printed so far.
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        rc = 130

    output = "".join(kept)
    if len(output) > OUTPUT_CAP:
        output, truncated = output[:OUTPUT_CAP], True

    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "argv": sys.argv[1:],
        "stage": core.course_stage(),
        "exit": rc,
        "ms": round((time.perf_counter() - start) * 1000),
        "output": output,
        "truncated": truncated,
        "db_rows": core.db_counts(),
    }
    try:
        # One write of the whole line, then flush: minimises the window for a torn
        # record if two wrapped runs ever overlap. serve.py skips unparseable lines.
        with open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
    except OSError as e:
        print(f"NOTE  the viewer could not record this run ({e}) — the run itself is unaffected.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
