#!/usr/bin/env bash
# check.sh — verify the environment before the course starts (or when a round misbehaves).
set -u
cd "$(dirname "$0")/.."
if   [ -x .venv/bin/python ];         then PY=".venv/bin/python"
elif [ -x .venv/Scripts/python.exe ]; then PY=".venv/Scripts/python.exe"
else PY="$(command -v python3 || command -v python)"; fi
fail=0

if [ -n "${OPENAI_API_KEY:-}" ]; then echo "PASS  OPENAI_API_KEY is set"
else echo "FAIL  OPENAI_API_KEY is not set in this shell"; fail=1; fi

"$PY" - <<'PYEOF' || fail=1
import importlib.util, sys
missing = [m for m in ("openai", "tiktoken") if importlib.util.find_spec(m) is None]
if missing:
    print(f"FAIL  missing packages: {', '.join(missing)} — run: bash setup/bootstrap.sh")
    sys.exit(1)
print("PASS  openai + tiktoken importable")
PYEOF

"$PY" - <<'PYEOF' || fail=1
import sqlite3, sys
from pathlib import Path
db = Path("memory.db")
if not db.exists():
    print("FAIL  memory.db not found — run: bash setup/bootstrap.sh"); sys.exit(1)
conn = sqlite3.connect(db)
try:
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("CONVERSATIONAL_MEMORY", "CONVERSATION_VECTORS", "SEMANTIC_MEMORY")}
except sqlite3.OperationalError as e:
    print(f"FAIL  memory.db is missing tables ({e}) — run: .venv/bin/python setup/reset_memory.py"); sys.exit(1)
if min(counts.values()) == 0:
    print(f"FAIL  memory.db has empty tables {counts} — run: .venv/bin/python setup/reset_memory.py"); sys.exit(1)
# The stored vectors must match the model semantic_search embeds queries with. cosine()
# uses zip(), which truncates silently on a length mismatch, so a fixture built with a
# different model would degrade Round 3's search into nonsense with no error at all.
import json
dims = len(json.loads(conn.execute("SELECT embedding FROM SEMANTIC_MEMORY LIMIT 1").fetchone()[0]))
if dims != 1536:
    print(f"FAIL  stored embeddings are {dims}-dimensional, expected 1536 "
          f"(text-embedding-3-small) — the seed fixture and the runtime model disagree"); sys.exit(1)
print(f"PASS  memory.db seeded {counts}, embeddings {dims}-dim")
PYEOF

if [ -n "${OPENAI_API_KEY:-}" ]; then
"$PY" - <<'PYEOF' || fail=1
import sys
try:
    from openai import OpenAI
    r = OpenAI().chat.completions.create(model="gpt-5.6-luna",
        messages=[{"role": "user", "content": "reply with the single word: ok"}])
    print(f"PASS  live API call succeeded (model replied {r.choices[0].message.content!r})")
except Exception as e:
    print(f"FAIL  live API call failed: {e}"); sys.exit(1)
PYEOF
fi

command -v git >/dev/null && echo "PASS  git available" || { echo "FAIL  git not found"; fail=1; }

[ $fail -eq 0 ] && echo "CHECK: PASS — environment is good." || { echo "CHECK: FAIL"; exit 1; }
