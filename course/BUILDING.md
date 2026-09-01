# BUILDING.md — the build phase, and its rails

Engineer-owned, and **authoritative** for BUILD mode: the one-line summary in
`COURSE.md`'s mode table is a pointer to this file, not a second source. BUILD is the
one mode with no learner in the room — the tutor works alone here, and every rule below
is mirrored by a mechanical check in `course/rounds/round-N/verify.sh`.

## BUILD mode

- Read `course/rounds/round-N/build.md` first — it scopes the build; the diff-dialogue
  command is written there.
- **Only `src/snackbot.py` may change.** Never touch `src/meter.py` or
  `src/seed_memory.py`; never create or delete files in the course tree. (Setup
  artifacts — `.venv/`, `memory.db`, `src/__pycache__/` — are git-ignored and don't count.)
- Patch **toward** `course/rounds/round-N/reference/snackbot.py` — do not invent an
  alternative implementation. Keep its clause-ID comments (`# S2.1: …`) exactly.
- Minimal diff: no refactors, renames, or formatting sweeps.
- `bash course/rounds/round-N/verify.sh` must pass before committing `round-N build`.
