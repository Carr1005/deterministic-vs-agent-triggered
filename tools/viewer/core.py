#!/usr/bin/env python3
"""core.py — where the course's state lives, and how to read it. Nothing else.

Every view is a pure function of three things on disk: the learner's git history, their
`memory.db`, and the run log that `run.py` appends to. This module is the only place that
knows where those are and how to get at them safely. It emits no HTML (that is
`shell.py`), knows nothing about routes (that is `serve.py`), and holds no opinion about
what any of it means (that is a view).

Two rules that keep the whole tool honest, and that anything added here must respect:

  1. **Read-only, always.** `git status --porcelain` is the tutor's mid-round resume
     signal (course/PROTOCOL.md), so nothing under `tools/viewer/serve.py` may ever write
     into the repository. The database is opened through a `mode=ro` URI, so this process
     cannot create, lock, or mutate it even by accident. `run.py` is the one writer, and
     it writes one git-ignored file.
  2. **No module-level mutable state, and no caching.** Pages are rebuilt from disk per
     request. A cache would be a second source of truth, and the first thing anyone would
     want to do with one is persist it — which rule 1 forbids.

Standard library only, so setup/requirements.txt and setup/check.sh stay untouched and
nobody mid-course has to re-bootstrap.
"""
import os
import re
import sqlite3
import subprocess
from pathlib import Path

# tools/viewer/core.py → tools/viewer → tools → the repo root.
# Views must import REPO from here rather than re-deriving it: they sit one directory
# deeper, so a copied `.parent.parent.parent` would silently point at `tools/`.
REPO = Path(__file__).resolve().parent.parent.parent

# The run log lives at the repo root, git-ignored under the same rationale as memory.db
# (see .gitignore). Relocating it is a one-line change here; `run.py` and the guide view
# both import this constant rather than defining their own.
RUN_LOG = REPO / ".snackbot-runs.jsonl"

TABLES = ("CONVERSATIONAL_MEMORY", "CONVERSATION_VECTORS", "SEMANTIC_MEMORY")

# The same commit-name pattern setup/bootstrap.sh uses to decide if a course has started.
COURSE_COMMIT = re.compile(r"^round-([1-5]) (spec|build)$")

# What each round is about, so a page is legible to someone mid-course.
ROUND_TITLE = {
    1: "The meter — instrument before you optimise",
    2: "Deterministic memory — code invokes, every turn",
    3: "Agent-triggered memory — the model invokes, via tools",
    4: "Counting — one passing run proves nothing",
    5: "The per-operation decision — pin exactly one read",
}


# Neutralise whatever git configuration we happen to inherit, so a page renders the same
# text on every machine. Two problems, two different mechanisms:
#
#   colour   `color.ui = always` puts ANSI escapes into captured output (measured: 66
#            lines of escape codes). `-c color.ui=false` outranks any config file.
#   external a `diff.external` driver — delta, difftastic — replaces git's diff with its
#            own output. The fix is the `--no-ext-diff` flag on the diff-producing
#            commands, NOT `-c diff.external=`: an empty value makes git try to execute
#            the empty string and exit 128, which silently emptied every diff. The flag
#            also covers the GIT_EXTERNAL_DIFF environment variable, which no amount of
#            `-c` can reach.
GIT_FLAGS = ("-c", "color.ui=false")
NO_EXT = ("--no-ext-diff",)      # valid on diff/show/log; not on rev-parse
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS")


def git_env():
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    # POSIX-only, which matches the course's "use WSL on Windows" guidance.
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    return env


def git(*args):
    """Run git in the repo and return stdout. Never raises on a non-zero exit."""
    r = subprocess.run(("git", "-C", str(REPO)) + GIT_FLAGS + args,
                       capture_output=True, text=True, env=git_env())
    return r.stdout if r.returncode == 0 else ""


def is_repo():
    return bool(git("rev-parse", "--git-dir"))


def git_head():
    """The current commit sha, or "" — the cheap half of a view's change fingerprint."""
    return git("log", "-1", "--format=%H").strip()


def course_commits():
    """{(round, phase): sha} for every phase commit the learner has made so far."""
    found = {}
    for line in git("log", "--format=%H%x00%s").splitlines():
        sha, _, subject = line.partition("\x00")
        m = COURSE_COMMIT.match(subject.strip())
        if m:
            found.setdefault((int(m.group(1)), m.group(2)), sha)
    return found


def course_stage():
    """Highest N with a `round-N build` commit — how far the app itself is. 0 = baseline."""
    return max((n for (n, phase) in course_commits() if phase == "build"), default=0)


def course_position():
    """(round, phase) of the last course commit, or (0, "") before the course starts."""
    for line in git("log", "--format=%s").splitlines():
        m = re.match(r"^round-([1-5]) (tutor|spec|build|demo)$", line.strip())
        if m:
            return int(m.group(1)), m.group(2)
    return 0, ""


def course_round():
    """Which round the learner is IN — not how far the app is built.

    `course_stage()` answers a different question and lags this by two phases: a round's
    build lands after its tutor and spec, so during Round 4's TUTOR the app is still the
    Round 3 build. Anything filed under "what the learner was doing" needs this one.
    """
    n, phase = course_position()
    if not n:
        return 1
    return n + 1 if phase == "demo" and n < 5 else n


def src_dirty():
    """Has src/snackbot.py been edited since the last build commit?

    During BUILD the app is written before it is committed, so `course_stage()` alone
    would describe a run made in that window as coming from the *previous* round's build
    — a card reading R0 beside output only R1's code can produce. This says when the
    stage is a floor rather than the whole truth.
    """
    return bool(git("status", "--porcelain", "--", "src/snackbot.py").strip())


def db_path():
    p = Path(os.getenv("SNACKBOT_DB", "memory.db"))
    return p if p.is_absolute() else REPO / p


def db_connect():
    """A read-only connection, or None if the db is absent. Caller closes it.

    `mode=ro` is load-bearing, not defensive: it makes it impossible for this process to
    create the file, take a write lock, or alter a single byte. Connections are opened
    per request and never shared — sqlite3 objects must not cross threads, and the server
    is threaded.
    """
    db = db_path()
    if not db.exists():
        return None
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def db_counts():
    """{table: rows}, or None if the db is absent or unreadable."""
    try:
        conn = db_connect()
        if conn is None:
            return None
        try:
            return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    for t in TABLES}
        finally:
            conn.close()
    except sqlite3.Error:
        return None
