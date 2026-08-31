# SETUP — the manual path (you probably don't need this)

**The tutor does all of this for you** on its first turn. The only thing you must do is
`export OPENAI_API_KEY=sk-...` in the terminal you start your agent from, then say
"start the course". This page is for doing it by hand, or for debugging when something
went wrong.

The course runs against a **real LLM** (OpenAI `gpt-5.6-luna` plus embeddings) and a
**real database** — but the database is a single SQLite file that ships already seeded.
No Docker, no database server, no local model download. Two pip packages.

**Expect ~2 minutes.** Total API cost for the whole course is typically a few cents.

## The short version

```bash
export OPENAI_API_KEY=sk-...
bash setup/bootstrap.sh
```

That is every step below, in order, idempotently. The rest of this page is the manual
path — read it if bootstrap failed, or if you'd rather see each step happen.

## 0. Prerequisites

- Python 3.10+
- git
- An OpenAI API key

## 1. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # optional — every course command names .venv/bin/python
.venv/bin/python -m pip install -r setup/requirements.txt
```

## 2. OpenAI key

```bash
export OPENAI_API_KEY=sk-...     # add to your shell profile to survive new terminals
```

Windows PowerShell: `$env:OPENAI_API_KEY = "sk-..."` — but run the course itself inside
WSL. Every command here is written `.venv/bin/python …`; a native-Windows venv puts the
interpreter at `.venv\Scripts\python.exe`, and you'd be translating every command.

## 3. The memory is already seeded — nothing to do

The course's opening premise ships with the repo. `setup/fixtures/memory-seed.db` holds
a *previous session* — including the user's almond allergy — in three tables:
`CONVERSATIONAL_MEMORY` (exact lookups) plus `CONVERSATION_VECTORS` and
`SEMANTIC_MEMORY` (the two the search tools read). Bootstrap copies it to `memory.db`,
so the allergy is stored **before you ever run the bot**. Round 1 is built on that.

`memory.db` itself stays git-ignored: from Round 2 on, every turn writes to it, and a
tracked file that changes every turn would destroy the tutor's mid-round resume signal.

To regenerate the fixture (author only — this is the one thing that costs embedding
calls): `SNACKBOT_DB=setup/fixtures/memory-seed.db .venv/bin/python src/seed_memory.py`

## 4. Check everything works

```bash
bash setup/check.sh
```

Verifies the key, one live API call, the database file, the seeded rows, and that the
stored embeddings are the right size. Fix anything it reports before continuing — a
failure here is the only thing that can quietly break a later round.

## 5. Nothing to initialize either

Your clone is already a git repo, and that is all the course needs: it records each phase
as a commit named `round-N tutor|spec|build|demo`, and the tutor knows the course hasn't
started because none of those exist yet. No baseline commit, no git step.

Only if git did *not* travel with your copy — an unzipped download, or a plain folder
copy — run `bash setup/init.sh` once to create a repo. No API calls.

## 6. Start

Open your coding agent **in this folder** and say:

> Read COURSE.md and start the course.

That line names only `COURSE.md`, the file all the rules live in, so it works in any
agent. Where the agent loads the rules on its own — Codex, Cursor and friends via
`AGENTS.md`, here a one-line pointer to `COURSE.md`; Claude Code, Gemini CLI and Aider
via the one-line pointers committed here — plain `start the course` is enough. See the
table in `README.md`.

## Troubleshooting

- **`OPENAI_API_KEY` errors** — the variable must be set in the *same shell* where you
  run commands, including the shell your coding agent uses.
- **`No memory database`** — run `.venv/bin/python setup/reset_memory.py` from the repo
  root; it restores the shipped seed, instantly and with no API calls.
- **Want a clean slate mid-course?** `.venv/bin/python setup/reset_memory.py` restores `memory.db`
  and re-seeds. (Round 5 uses this deliberately.)
- **`memory.db` is git-ignored** on purpose: it is state, not courseware, and it would
  otherwise pollute the diffs you read each round.
- **Agent says there's no git repo** — you unzipped or copied the folder rather than
  cloning it. Run `bash setup/init.sh` once, then start a new agent session.
- **`command not found: python`** — expected on macOS. Every command in this course
  names `.venv/bin/python` explicitly; if you typed bare `python`, retype it with the
  prefix, from the repo root.
