#!/usr/bin/env bash
# pristine.sh — AUTHOR TOOL. Run this before you duplicate, zip, push, or share this
# folder. It proves the copy is unstarted, so whoever receives it begins at Round 1.
# Read-only: it changes nothing, ever.
#
# ---------------------------------------------------------------------------
# THE TWO STANDING RULES FOR THIS REPO, both enforced by the checks below:
#
#   1. Never publish a commit named `round-1`…`round-5` anything. Those names
#      belong to the learner's copy: the tutor reads `git log` for them, and
#      finding none is what tells it the course has not started. Ship one and
#      every learner resumes mid-course, or is told the course is finished.
#      Your own commit messages are otherwise unconstrained.
#
#   2. Never publish a copy someone has played. The learner's artifacts
#      (answers.md, spec/spec.md, demo-log.md, src/snackbot.py) are tracked
#      courseware, so a test run's residue travels silently and nothing else
#      in the repo checks for it.
#
# The ritual, then, is one line before you push or share:
#      bash setup/pristine.sh && echo "ok to share"
# ---------------------------------------------------------------------------
set -u
cd "$(dirname "$0")/.."
fail=0
ok()  { echo "PASS  $1"; }
bad() { echo "FAIL  $1"; fail=1; }
# grep -c prints "0" AND exits 1 when there are no matches, so `|| echo 0` would
# double it. Swallow the status instead and default only when grep printed nothing.
count() { local n; n="$(grep -cE "$1" "$2" 2>/dev/null || true)"; echo "${n:-0}"; }

echo "== answers (every question must still hold its placeholder)"
expected="3 4 4 3 8"; i=1; total=0
for want in $expected; do
  got="$(count '\(not yet answered\)' "course/rounds/round-$i/answers.md")"
  if [ "$got" = "$want" ]; then ok "round-$i/answers.md — $want placeholders"
  else bad "round-$i/answers.md — $got placeholders, expected $want (questions were answered here)"; fi
  total=$((total + got)); i=$((i + 1))
done
if [ "$total" = 22 ]; then ok "22 placeholders in total"; else bad "$total placeholders in total, expected 22"; fi

echo "== spec (must be the empty scaffold)"
n="$(count '^> S[1-5]\.' spec/spec.md)"
if [ "$n" = 0 ]; then ok "spec/spec.md holds no clauses"
else bad "spec/spec.md holds $n clause line(s) — the spec has been filled in"; fi
lines="$(wc -l < spec/spec.md | tr -d ' ')"
if [ "$lines" = 29 ]; then ok "spec/spec.md is the 29-line scaffold"
else bad "spec/spec.md is $lines lines, expected the 29-line scaffold"; fi

echo "== demo log (must hold no recorded rounds)"
n="$(count '^## round [1-5] — [0-9]{4}' course/demo-log.md)"
if [ "$n" = 0 ]; then ok "course/demo-log.md has no recorded rounds"
else bad "course/demo-log.md has $n recorded round(s) — someone ran the demos"; fi

echo "== source (must be the round-0 baseline)"
if grep -q 'Round-0 baseline' src/snackbot.py; then ok "src/snackbot.py carries the Round-0 banner"
else bad "src/snackbot.py has lost its 'Round-0 baseline' banner"; fi
if grep -q 'from meter import' src/snackbot.py; then bad "src/snackbot.py imports meter — this is a Round-1-or-later build"
else ok "src/snackbot.py imports no meter"; fi
if [ -f course/rounds/round-0/reference/snackbot.py ]; then
  if diff -q src/snackbot.py course/rounds/round-0/reference/snackbot.py >/dev/null 2>&1; then
    ok "src/snackbot.py is byte-identical to the round-0 reference"
  else
    bad "src/snackbot.py differs from course/rounds/round-0/reference/snackbot.py:"
    diff src/snackbot.py course/rounds/round-0/reference/snackbot.py | sed 's/^/      /'
  fi
else
  echo "NOTE  no course/rounds/round-0/reference/snackbot.py to diff against"
fi

echo "== git history (a clone must not resume mid-course)"
if [ -d .git ]; then
  if git log --format=%s 2>/dev/null | grep -qE '^round-[1-5] '; then
    bad "git history contains PLAYED-course commits — a clone would resume mid-course:"
    git log --oneline 2>/dev/null | grep -E ' round-[1-5] ' | head -5 | sed 's/^/      /'
  else
    ok "git history contains no round-1..5 commits"
  fi
  dirty="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$dirty" = 0 ]; then ok "working tree is clean"
  else echo "NOTE  $dirty uncommitted change(s) — fine for a zip/copy, but they will NOT"
       echo "      travel with a clone or a GitHub template:"
       git status --short | sed 's/^/      /'
  fi
else
  ok "no .git — setup/init.sh will create one (fallback path)"
fi

echo "== carried-over state (harmless for clone/template; matters for zip and cp -r)"
if [ -e memory.db ]; then
  echo "NOTE  memory.db present — git-ignored, so a clone is safe, but DELETE IT before"
  echo "      zipping or copying this folder: Round 1's demo assumes a clean 5/5/7 seed."
  echo "      (setup/fixtures/memory-seed.db is the tracked seed — that one SHOULD ship.)"
else ok "no memory.db"; fi
if [ -e .venv ]; then
  echo "NOTE  .venv present — git-ignored; delete before zipping (large, machine-specific)."
else ok "no .venv"; fi

echo
if [ $fail -eq 0 ]; then echo "PRISTINE: PASS — safe to duplicate."
else echo "PRISTINE: FAIL — do not duplicate this copy."; exit 1; fi
