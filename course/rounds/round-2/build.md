# Round 2 — BUILD brief

> **MODE: BUILD** — tag replies `[R2 · BUILD]`. Only `src/snackbot.py` changes; patch
> toward `reference/`; verify before commit.

**Precondition:** `round-2 spec` committed (S2.1–S2.3).

**Implements:** S2.1 (exact SQL preload, every turn), S2.2 (save both sides of every
turn), S2.3 (file-backed, survives process death). Also introduces the CLI
(`.venv/bin/python src/snackbot.py "question"`), needed by this round's demo.

**Change:** patch toward `reference/snackbot.py`: the SQLite connection, `read_user_facts()`
(exact SQL, thread-keyed, time-ordered), `save_turn()`, `run_turn()` wiring that
preloads every call and saves both sides. Keep the `# S2.1` / `# S2.2` comments.

**Scope:** only `src/snackbot.py`; expected ≈ 40–45 changed lines. No new files, no
refactors, meter/seed untouched.

**Then:** `bash course/rounds/round-2/verify.sh` → commit `round-2 build` → **diff
dialogue** `[R2 · EXPAND]`: show `git diff HEAD~1 -- src/`, walk it clause by clause —
preload block = S2.1, the two `save_turn` calls = S2.2, the on-disk database (not an
in-process dict) = why S2.3 holds — then invite questions about anything on screen
(the `sqlite3` API, the SQL, `?` placeholders, thread ids) and answer plainly. Done → DEMO.
