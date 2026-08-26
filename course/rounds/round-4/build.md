# Round 4 — BUILD brief

> **MODE: BUILD** — tag replies `[R4 · BUILD]`. Only `src/snackbot.py` changes; patch
> toward `reference/`; verify before commit.

**Precondition:** `round-4 spec` committed (S4.1–S4.2).

**Implements:** S4.1 (five-run harness `run_n`) and S4.2 (the `almond` signal). **No
memory behavior changes** — reads stay agent-triggered, writes deterministic. Like
Round 1, this build is an *instrument*.

**Change:** patch toward `reference/snackbot.py`:
- add `run_n(n=5, question=..., signal="almond")`, printing per-run SAFE/UNSAFE and the
  final count, with the `# S4.1` / `# S4.2` comments;
- extend `__main__`: `--x5` runs the harness; the CLI question path is unchanged.
  (Documented deviation from the source video, whose final main runs only the harness —
  we keep the CLI so later demos can still ask single questions.)

**Scope:** only `src/snackbot.py`; ≈ 25 lines; `run_turn` and the tools untouched.

**Then:** `bash course/rounds/round-4/verify.sh` → commit `round-4 build` → **diff
dialogue** `[R4 · EXPAND]`: show `git diff HEAD~1 -- src/`; say out loud that the whole
green block is *measurement, not behavior*; invite questions (substring matching,
`.lower()`, why 5) and answer plainly. Done → DEMO.
