#!/usr/bin/env bash
# Round 5 verify — checks src/ against this round's contract. Report-only, no writes.
set -u
cd "$(dirname "$0")/../../.."
PY="$(command -v python3 || command -v python)"
fail=0
need()   { if grep -qF "$2" src/snackbot.py; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }
absent() { if grep -qF "$2" src/snackbot.py; then echo "FAIL  $1"; fail=1; else echo "PASS  $1"; fi; }

want="meter.py
seed_memory.py
snackbot.py"
got="$(ls src | grep -v __pycache__ | sort)"
if [ "$want" = "$got" ]; then echo "PASS  src/ file list unchanged"; else echo "FAIL  src/ file list changed:"; echo "$got"; fail=1; fi

"$PY" -m py_compile src/snackbot.py src/meter.py src/seed_memory.py && echo "PASS  py_compile" || { echo "FAIL  py_compile"; fail=1; }

need   "pinned deterministic read (S5.1)"   'user_facts = read_user_facts()'
need   "memory search still a tool (S5.1)"  'def search_memory'
need   "kb search still a tool (S5.1)"      'def search_knowledge_base'
need   "writes stay deterministic (S5.1)"   'def save_turn'
need   "harness intact (S4.1)"              'def run_n'
need   "meter intact (S1.2)"                'report('
if diff -q src/snackbot.py course/rounds/round-5/reference/snackbot.py >/dev/null 2>&1; then
  echo "NOTE  identical to the round-5 reference"
else
  echo "NOTE  differs from the round-5 reference (allowed if checks pass):"
  echo "      diff src/snackbot.py course/rounds/round-5/reference/snackbot.py"
fi

[ $fail -eq 0 ] && echo "VERIFY: PASS" || { echo "VERIFY: FAIL"; exit 1; }
