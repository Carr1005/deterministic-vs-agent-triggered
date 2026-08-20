# Round 1 — BUILD brief

> **MODE: BUILD** — tag replies `[R1 · BUILD]`. Only `src/snackbot.py` changes; patch
> toward `reference/`; verify before commit.

**Precondition:** last commits are `round-1 tutor` and `round-1 spec` (S1.1, S1.2).

**Implements:** S1.2 only. (S1.1 is a scope clause — it constrains every future build;
it doesn't produce code.)

**Change:** wire the developer-shipped `src/meter.py` into `src/snackbot.py`: import
`timed` and `report`, wrap the LLM call, report every turn — exactly as the reference
does, keeping its `# S1.2` comment.

**Scope:** only `src/snackbot.py`; ~2 hunks, under ~10 changed lines — bigger means
drift; re-read the reference. No refactors, no new files.

**Then:** `bash course/rounds/round-1/verify.sh` → commit `round-1 build` → **diff
dialogue** `[R1 · EXPAND]`: show `git diff HEAD~1 -- src/` (scoped — commits carry
other artifacts too), note that the whole green diff is S1.2 arriving — the instrument
before any memory — then invite questions about anything on screen and answer them
plainly. Learner says done → DEMO.
