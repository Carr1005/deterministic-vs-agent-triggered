#!/usr/bin/env python3
"""run.py — transparent wrapper: run a course script, and put the run on the status page.

The tutor uses this instead of calling the app directly WHEN — and only when — the
learner asks the tutor to run something on their behalf:

    .venv/bin/python tools/appview/run.py src/snackbot.py --x5
    .venv/bin/python tools/appview/run.py setup/show_memory.py

It spawns the same interpreter on the given script, streams every output line to the
terminal unchanged, and preserves the exit code — then appends one JSON line describing
the run to RUN_LOG, which tools/appview/serve.py renders at localhost:5000.

Contract, in order of precedence:

  1. THE RUN IS SACRED. The child's stdout/stderr reach the terminal verbatim and
     unbuffered, and its exit code is this process's exit code. Logging is best-effort:
     if the append fails for any reason, one NOTE line is printed and nothing else
     changes. Tooling must never break or alter a course run.
  2. It writes exactly ONE file — RUN_LOG, which is git-ignored. `git status
     --porcelain` is the tutor's mid-round resume signal (course/PROTOCOL.md), so
     nothing this file writes may ever show up as a working-tree change. The database
     is opened read-only, git is only read, no tracked file is touched.
  3. Stdlib only, same as tools/diffview/serve.py, so setup/requirements.txt and
     setup/check.sh stay untouched.

The record stores the RAW output; meter lines, tool lines and SAFE counts are parsed at
render time by serve.py, so there is exactly one source of truth for what a run printed.
"""
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
# The single place the log lives. Git-ignored (see .gitignore's rationale next to
# memory.db); relocating it — e.g. to ${TMPDIR} — is a one-line change here, and
# serve.py imports this constant rather than defining its own.
RUN_LOG = REPO / ".snackbot-runs.jsonl"
OUTPUT_CAP = 20_000          # chars kept per record; --x5 with tool spam fits well under
TABLES = ("CONVERSATIONAL_MEMORY", "CONVERSATION_VECTORS", "SEMANTIC_MEMORY")

# Same commit-name pattern as tools/diffview/serve.py and setup/bootstrap.sh: the git
# log is the course's only state, and `round-N build` commits say how far the app is.
COURSE_COMMIT = re.compile(r"^round-([1-5]) (spec|build)$")
GIT_FLAGS = ("-c", "color.ui=false")
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS")


def git_env():
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    return env


def git(*args):
    """Run git in the repo and return stdout. Never raises on a non-zero exit."""
    r = subprocess.run(("git", "-C", str(REPO)) + GIT_FLAGS + args,
                       capture_output=True, text=True, env=git_env())
    return r.stdout if r.returncode == 0 else ""


def course_stage():
    """Highest N with a `round-N build` commit — how far the app itself is. 0 = baseline."""
    stages = [int(m.group(1))
              for line in git("log", "--format=%s").splitlines()
              if (m := COURSE_COMMIT.match(line.strip())) and m.group(2) == "build"]
    return max(stages, default=0)


def db_path():
    p = Path(os.getenv("SNACKBOT_DB", "memory.db"))
    return p if p.is_absolute() else REPO / p


def db_counts():
    """{table: rows} via a read-only connection, or None if the db is absent/unreadable."""
    db = db_path()
    if not db.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    for t in TABLES}
        finally:
            conn.close()
    except sqlite3.Error:
        return None


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: .venv/bin/python tools/appview/run.py <script.py> [args ...]")
        return 2

    # -u so the learner sees the child's lines the moment they print, not at exit.
    cmd = [sys.executable, "-u", *sys.argv[1:]]
    start = time.perf_counter()
    kept, kept_len, truncated = [], 0, False

    proc = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE,
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
        "stage": course_stage(),
        "exit": rc,
        "ms": round((time.perf_counter() - start) * 1000),
        "output": output,
        "truncated": truncated,
        "db_rows": db_counts(),
    }
    try:
        # One write of the whole line, then flush: minimises the window for a torn
        # record if two wrapped runs ever overlap. serve.py skips unparseable lines.
        with open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
    except OSError as e:
        print(f"NOTE  appview could not record this run ({e}) — the run itself is unaffected.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
