#!/usr/bin/env bash
# Round 2 verify — checks src/ against this round's contract. Report-only, no writes.
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

need   "deterministic read exists (S2.1)"    'def read_user_facts'
need   "read invoked every turn (S2.1)"      'user_facts = read_user_facts()'
need   "deterministic write exists (S2.2)"   'def save_turn'
need   "both sides saved (S2.2)"             'save_turn("assistant"'
need   "exact SQL over the store (S2.1)"     'FROM CONVERSATIONAL_MEMORY'
need   "persistent file, not memory (S2.3)"  'sqlite3.connect(DB_PATH)'
need   "meter still reporting (S1.2)"        'report('
if diff -q src/snackbot.py course/rounds/round-2/reference/snackbot.py >/dev/null 2>&1; then
  echo "NOTE  identical to the round-2 reference"
else
  echo "NOTE  differs from the round-2 reference (allowed if checks pass):"
  echo "      diff src/snackbot.py course/rounds/round-2/reference/snackbot.py"
fi

[ $fail -eq 0 ] && echo "VERIFY: PASS" || { echo "VERIFY: FAIL"; exit 1; }
