#!/usr/bin/env bash
# bootstrap.sh — ONE command: any fresh copy of this folder → ready to start the course.
#
#   export OPENAI_API_KEY=sk-...
#   bash setup/bootstrap.sh
#
# Safe to re-run at any point, including mid-course. Steps:
#   API key → python → .venv → packages → memory.db → check.sh
# Step-by-step equivalent, if you'd rather do it by hand: setup/SETUP.md
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"

ASSUME_YES=0
case "${1:-}" in
  -y|--yes) ASSUME_YES=1 ;;
  "") ;;
  *) echo "usage: bash setup/bootstrap.sh [--yes]" >&2; exit 2 ;;
esac

say() { printf "\n== %s\n" "$1"; }

# A non-interactive caller (a coding agent, CI) answers "no" unless --yes was passed,
# so nothing destructive ever happens without a human deciding it.
ask() {
  if [ "$ASSUME_YES" = 1 ]; then return 0; fi
  if [ ! -t 0 ]; then echo "      (non-interactive: assuming no — re-run with --yes to accept)"; return 1; fi
  printf "%s [y/N] " "$1"
  read -r reply
  case "$reply" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}

# ---------------------------------------------------------------- 1. api key
say "1/6  OPENAI_API_KEY"
if [ -z "${OPENAI_API_KEY:-}" ]; then
  cat <<'EOF'
FAIL  OPENAI_API_KEY is not set in this shell.

      Set it and re-run this script:

          export OPENAI_API_KEY=sk-...          # macOS / Linux / WSL / Git Bash
          $env:OPENAI_API_KEY = "sk-..."        # Windows PowerShell

      Add the export line to your shell profile (~/.zshrc, ~/.bashrc) as well.
      Your coding agent runs commands in a shell that inherits the environment of
      the terminal you launched it from — a key exported in some OTHER terminal,
      or set inside the agent's own bash calls, will not be visible to the course.
EOF
  exit 1
fi
echo "PASS  set (${#OPENAI_API_KEY} characters)"

# ---------------------------------------------------------------- 2. python
say "2/6  Python 3.10+"
PY_BOOT=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 \
     && "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 10) else 1)' 2>/dev/null; then
    PY_BOOT="$c"; break
  fi
done
if [ -z "$PY_BOOT" ]; then
  echo "FAIL  no Python 3.10 or newer on PATH (tried: python3, python)."
  echo "      Install one, reopen your terminal, then re-run: bash setup/bootstrap.sh"
  exit 1
fi
echo "PASS  $PY_BOOT  ($("$PY_BOOT" -c 'import sys; print(sys.version.split()[0])'))"

# ---------------------------------------------------------------- 3. venv
say "3/6  Virtual environment (.venv)"
if   [ -x .venv/bin/python ];         then VENV_PY=".venv/bin/python"
elif [ -x .venv/Scripts/python.exe ]; then VENV_PY=".venv/Scripts/python.exe"
else VENV_PY=""
fi

if [ -n "$VENV_PY" ] && ! "$VENV_PY" -c 'pass' >/dev/null 2>&1; then
  echo "WARN  .venv exists but its interpreter will not run."
  echo "      (Typical after copying this folder from another machine.)"
  if ask "      delete .venv and rebuild it?"; then rm -rf .venv; VENV_PY=""
  else echo "FAIL  delete .venv by hand, then re-run this script."; exit 1; fi
fi

if [ -z "$VENV_PY" ]; then
  echo "creating .venv …"
  if ! "$PY_BOOT" -m venv .venv; then
    echo "FAIL  could not create a virtualenv."
    echo "      Debian/Ubuntu: sudo apt install python3-venv  — then re-run."
    exit 1
  fi
  if [ -x .venv/bin/python ]; then VENV_PY=".venv/bin/python"; else VENV_PY=".venv/Scripts/python.exe"; fi
fi
echo "PASS  $VENV_PY"

if [ "$VENV_PY" != ".venv/bin/python" ]; then
  echo "NOTE  Windows-layout venv. Every command in this course is written"
  echo "      '.venv/bin/python …' — on this machine type '$VENV_PY …' instead."
  echo "      (Smoothest path on Windows: run the whole course inside WSL.)"
fi

# ---------------------------------------------------------------- 4. packages
say "4/6  Packages (openai, tiktoken)"
# Captured, so a network hiccup shows six readable lines instead of a pip traceback.
PIP_LOG="$(mktemp)"
if ! "$VENV_PY" -m pip install --quiet --disable-pip-version-check \
       --timeout 60 --retries 5 -r setup/requirements.txt >"$PIP_LOG" 2>&1; then
  echo "FAIL  pip install failed. Last lines:"
  tail -6 "$PIP_LOG" | sed 's/^/      /'
  echo
  echo "      Usually a slow network — just re-run: bash setup/bootstrap.sh"
  echo "      Debian/Ubuntu: sudo apt install python3-pip python3-venv, delete .venv, re-run."
  rm -f "$PIP_LOG"
  exit 1
fi
rm -f "$PIP_LOG"
echo "PASS  installed from setup/requirements.txt"


# ---------------------------------------------------------------- 5. memory.db
say "5/6  memory.db — the seeded 'previous session'"

db_state() {
  "$VENV_PY" - <<'PYEOF'
import sqlite3, sys
from pathlib import Path
p = Path("memory.db")
if not p.exists():
    print("none"); sys.exit(0)
try:
    c = sqlite3.connect(p)
    print(" ".join(str(c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
                   for t in ("CONVERSATIONAL_MEMORY", "CONVERSATION_VECTORS", "SEMANTIC_MEMORY")))
except sqlite3.Error:
    print("bad")
PYEOF
}

# Has any round actually been run in this copy? Rounds 2-4 write a row every turn, so
# "not 5/5/7" is EXPECTED mid-course — and re-seeding then would destroy the very
# accumulation Round 5's demo is built on.
COURSE_STARTED=0
if [ -d .git ] && git log --format=%s 2>/dev/null \
     | grep -qE '^round-[1-5] (tutor|spec|build|demo)$'; then COURSE_STARTED=1; fi

COUNTS="$(db_state)"
case "$COUNTS" in
  none)
    echo "no memory.db yet — restoring the shipped seed (no API calls)."
    "$VENV_PY" setup/reset_memory.py
    ;;
  "5 5 7")
    echo "PASS  memory.db already holds the clean seed (5 / 5 / 7)"
    ;;
  *)
    if [ "$COURSE_STARTED" = 1 ]; then
      echo "PASS  memory.db holds $COUNTS rows, not 5/5/7 — expected: the course has"
      echo "      started, and from Round 2 on every turn writes to memory."
      echo "      Leaving it exactly as it is. (Round 5 resets it deliberately.)"
    else
      echo "WARN  memory.db holds '$COUNTS' rows; a clean seed is 5 / 5 / 7 — and no"
      echo "      round has been run in this copy. This database was probably carried"
      echo "      over when the folder was copied. Round 1's demo depends on the"
      echo "      clean seed, so its numbers would be wrong."
      if ask "      delete memory.db and re-seed it?"; then
        "$VENV_PY" setup/reset_memory.py
      else
        echo "      left as is — restore later with: $VENV_PY setup/reset_memory.py"
      fi
    fi
    ;;
esac

# ---------------------------------------------------------------- 6. check
say "6/6  Environment check (includes one live API call)"
bash setup/check.sh

cat <<EOF

============================================================
READY.

  1. Open your coding agent in this folder:
       $ROOT
     Launch it from THIS terminal, so it inherits OPENAI_API_KEY.

  2. Copy this line and send it as your first message:

     ┌────────────────────────────────────────────────┐
     │  Read AGENTS.md and start the course.          │
     └────────────────────────────────────────────────┘

     Works in every coding agent. If the reply has no mode
     tag like [R1 · TUTOR], the instructions didn't load —
     send the line again.

Re-running 'bash setup/bootstrap.sh' at any time is safe.
============================================================
EOF
