#!/usr/bin/env bash
# serve.sh — start, reuse, or stop the local course viewer (two tabs on one port).
#
# The tutor runs `--ensure` at the Round 1 scene-set and at each diff dialogue, and hands
# the learner a link. Because the tutor starts it rather than the learner, this script has
# to guarantee the process never becomes a nuisance:
#
#   --ensure   idempotent. If OUR server already answers, reuse it and start nothing.
#              Otherwise start one in the background and wait until it answers.
#   --stop     find it by health token and kill it. No pid file is written; nothing in
#              this repo is ever written to, because `git status --porcelain` is the
#              tutor's mid-round resume signal (see course/PROTOCOL.md).
#
# The server shuts itself down after 60 minutes with no page on screen — a poll from a
# visible tab counts as activity, a backgrounded or closed one does not, so a viewer left
# open in the foreground stays up and a forgotten one still expires.
# Background output goes to $TMPDIR, deliberately outside the repo.
set -u
cd "$(dirname "$0")/../.."

PORT=4000
IDLE=60
ACTION=""
LOG="${TMPDIR:-/tmp}/snackbot-viewer.log"
TOKEN="snackbot-viewer-ok"

# Servers from before the two viewers were merged. They answer on ports we now want, with
# tokens we no longer mint, so without this list `--ensure` would mistake our own old
# process for a stranger, step aside to 4001, and leave :4000 serving the old tab-less
# page at the URL everyone already has. Deletable once a release has shipped.
# Bare "snackbot-viewer-ok" is here too: it is what our own server replied before the
# health check began naming its repository.
LEGACY_TOKENS="snackbot-diffview-ok snackbot-appview-ok snackbot-viewer-ok"
LEGACY_PORTS="4000 4001 4002 4003 4004 4005 5050 5051 5052 5053 5054 5055 5000"

usage() {
  echo "usage: bash tools/viewer/serve.sh [--ensure|--stop|--foreground] [--port N] [--idle N]" >&2
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

# Whatever answers /healthz on this port, or "" — a magic token distinguishes our server
# from anything else squatting.
probe() {
  "$PY" - "$1" <<'PYEOF' 2>/dev/null
import sys, urllib.request
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/healthz", timeout=0.5) as r:
        print(r.read().decode().strip())
except Exception:
    pass
PYEOF
}

# Ours means this token AND this repository: a trial clone or a replay sandbox running
# beside the original must not adopt its viewer and serve the wrong tree.
ours()   { [ "$(probe "$1")" = "$TOKEN $(pwd -P)" ]; }

legacy() {
  local body; body="$(probe "$1")"
  [ -n "$body" ] || return 1
  for t in $LEGACY_TOKENS; do [ "$body" = "$t" ] && return 0; done
  return 1
}

kill_port() {
  local pids; pids="$(lsof -ti "tcp:$1" 2>/dev/null || true)"
  [ -n "$pids" ] || return 1
  echo "$pids" | while read -r pid; do kill "$pid" 2>/dev/null; done
  return 0
}

# SO_REUSEADDR matters here: http.server.HTTPServer sets allow_reuse_address, so the real
# server can bind a port still holding TIME_WAIT entries from a just-killed predecessor.
# Probing without it is stricter than the server itself, and would send --ensure walking
# away from a port it could have had — which is exactly what happens right after we
# replace a legacy server on this port.
port_taken() {
  "$PY" - "$1" <<'PYEOF' 2>/dev/null
import socket, sys
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
    if ! command -v lsof >/dev/null 2>&1; then
      echo "FAIL  lsof not found; stop it from the terminal it is running in (Ctrl-C)."
      exit 1
    fi
    stopped=0
    seen=""
    # Stop ANY viewer of ours, whichever checkout it serves, and name that checkout so
    # nothing is silent. `--ensure` stays strictly repo-scoped — adopting another tree's
    # server would quietly show the wrong content — but `--stop` is an explicit act, and
    # scoping it left an orphan unstoppable: delete a replay sandbox while its viewer
    # runs and no directory matches its path any more.
    for p in $(seq "$PORT" $((PORT + 5))) $LEGACY_PORTS; do
      case " $seen " in *" $p "*) continue ;; esac      # LEGACY_PORTS overlaps the range
      seen="$seen $p"
      body="$(probe "$p")"
      case "$body" in
        "$TOKEN"*|snackbot-diffview-ok*|snackbot-appview-ok*) ;;
        *) continue ;;
      esac
      served="${body#* }"
      if kill_port "$p"; then
        if [ "$served" = "$body" ]; then
          echo "PASS  stopped the viewer on port $p"
        else
          echo "PASS  stopped the viewer on port $p (was serving $served)"
        fi
        stopped=1
      fi
    done
    [ "$stopped" = 1 ] || echo "NOTE  no viewer of ours found on ports $PORT-$((PORT + 5))
      or $LEGACY_PORTS."
    ;;

  --foreground)
    exec "$PY" tools/viewer/serve.py --port "$PORT" --idle "$IDLE"
    ;;

  --ensure)
    if ours "$PORT"; then
      echo "PASS  already running: http://localhost:$PORT/diffs"
      exit 0
    fi
    # An old pre-merge server of ours on this port: it is identified by a token we
    # minted, so take the port back rather than stepping aside — stepping aside is only
    # correct for a genuine stranger, and here it would leave a stale page on the URL
    # the learner already has.
    if legacy "$PORT" && command -v lsof >/dev/null 2>&1; then
      kill_port "$PORT" && echo "NOTE  replaced an older SnackBot viewer on port $PORT."
      sleep 0.5
    fi
    start="$PORT"
    while port_taken "$PORT"; do
      echo "NOTE  port $PORT is in use by another process."
      PORT=$((PORT + 1))
      if [ "$PORT" -gt $((start + 5)) ]; then
        echo "FAIL  ports $start-$((start + 5)) are all busy. Pass --port N to choose one."
        exit 1
      fi
      if ours "$PORT"; then
        echo "PASS  already running: http://localhost:$PORT/diffs"
        exit 0
      fi
    done
    nohup "$PY" tools/viewer/serve.py --port "$PORT" --idle "$IDLE" \
      >"$LOG" 2>&1 &
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      sleep 0.3
      if ours "$PORT"; then
        echo "PASS  viewer on http://localhost:$PORT/diffs and http://localhost:$PORT/guide"
        echo "      (stops itself after $IDLE idle min)"
        exit 0
      fi
    done
    echo "FAIL  did not come up within 3s. Last output:"
    tail -5 "$LOG" 2>/dev/null | sed 's/^/      /'
    exit 1
    ;;
esac
