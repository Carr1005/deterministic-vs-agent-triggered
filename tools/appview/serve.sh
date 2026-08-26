#!/usr/bin/env bash
# serve.sh — start, reuse, or stop the local app status page.
#
# The tutor runs `--ensure` at the Round 1 scene-set and hands the learner a link.
# Because the tutor starts it rather than the learner, this script has to guarantee the
# process never becomes a nuisance:
#
#   --ensure   idempotent. If OUR server already answers, reuse it and start nothing.
#              Otherwise start one in the background and wait until it answers.
#   --stop     find it by port and kill it. No pid file is written; nothing in this
#              repo is ever written to, because `git status --porcelain` is the tutor's
#              mid-round resume signal (see course/PROTOCOL.md).
#
# The server also shuts itself down after 60 idle minutes, so a forgotten one expires.
# Background output goes to $TMPDIR, deliberately outside the repo.
set -u
cd "$(dirname "$0")/../.."

PORT=5000
IDLE=60
ACTION=""
LOG="${TMPDIR:-/tmp}/snackbot-appview.log"
TOKEN="snackbot-appview-ok"

usage() {
  echo "usage: bash tools/appview/serve.sh [--ensure|--stop|--foreground] [--port N] [--idle N]" >&2
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --ensure|--stop|--foreground) ACTION="$1" ;;
    --port) shift; [ $# -gt 0 ] || usage; PORT="$1" ;;
    --idle) shift; [ $# -gt 0 ] || usage; IDLE="$1" ;;
    -h|--help) usage ;;
    *) echo "unknown option: $1" >&2; usage ;;
  esac
  shift
done
[ -n "$ACTION" ] || ACTION="--ensure"

# Stdlib-only, so the venv is not required; prefer it anyway to match the course's rule
# that every Python command is `.venv/bin/python` (AGENTS.md boot step 5).
if   [ -x .venv/bin/python ];         then PY=".venv/bin/python"
elif [ -x .venv/Scripts/python.exe ]; then PY=".venv/Scripts/python.exe"
else PY="$(command -v python3 || command -v python)"; fi

# Is OUR server on this port? A magic token distinguishes it from anything else
# squatting — including tools/diffview, whose token differs on purpose.
ours() {
  local body
  body="$("$PY" - "$1" <<'PYEOF' 2>/dev/null
import sys, urllib.request
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/healthz", timeout=0.5) as r:
        print(r.read().decode().strip())
except Exception:
    pass
PYEOF
)"
  [ "$body" = "$TOKEN" ]
}

port_taken() {
  "$PY" - "$1" <<'PYEOF' 2>/dev/null
import socket, sys
s = socket.socket()
try:
    s.bind(("127.0.0.1", int(sys.argv[1]))); sys.exit(1)   # free
except OSError:
    sys.exit(0)                                            # taken
finally:
    s.close()
PYEOF
}

case "$ACTION" in
  --stop)
    if command -v lsof >/dev/null 2>&1; then
      pids="$(lsof -ti "tcp:$PORT" 2>/dev/null || true)"
      if [ -n "$pids" ]; then
        echo "$pids" | while read -r pid; do kill "$pid" 2>/dev/null; done
        echo "PASS  stopped whatever held port $PORT (pid: $(echo $pids | tr '\n' ' '))"
      else
        echo "NOTE  nothing is listening on port $PORT."
      fi
    else
      echo "FAIL  lsof not found; stop it from the terminal it is running in (Ctrl-C)."
      exit 1
    fi
    ;;

  --foreground)
    exec "$PY" tools/appview/serve.py --port "$PORT" --idle "$IDLE"
    ;;

  --ensure)
    if ours "$PORT"; then
      echo "PASS  already running: http://localhost:$PORT/"
      exit 0
    fi
    # Port occupied by something that is not ours: step aside rather than fight it.
    # (On macOS, 5000 is often AirPlay Receiver — the walk lands on 5001.)
    start="$PORT"
    while port_taken "$PORT"; do
      echo "NOTE  port $PORT is in use by another process."
      PORT=$((PORT + 1))
      if [ "$PORT" -gt $((start + 5)) ]; then
        echo "FAIL  ports $start-$((start + 5)) are all busy. Pass --port N to choose one."
        exit 1
      fi
      if ours "$PORT"; then
        echo "PASS  already running: http://localhost:$PORT/"
        exit 0
      fi
    done
    nohup "$PY" tools/appview/serve.py --port "$PORT" --idle "$IDLE" \
      >"$LOG" 2>&1 &
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      sleep 0.3
      if ours "$PORT"; then
        echo "PASS  appview on http://localhost:$PORT/  (stops itself after $IDLE idle min)"
        exit 0
      fi
    done
    echo "FAIL  did not come up within 3s. Last output:"
    tail -5 "$LOG" 2>/dev/null | sed 's/^/      /'
    exit 1
    ;;
esac
