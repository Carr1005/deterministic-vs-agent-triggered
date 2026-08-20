# SnackBot — an interactive course you run inside a coding agent

**Topic:** every memory operation an AI agent performs is classified by one question —
*who invokes it?* Your **code** (deterministic) or the **model** (agent-triggered).
Each choice fails differently: deterministic fails on **cost, visibly**; agent-triggered
fails on **reliability, silently**. The skill this course teaches is making that choice
**per operation**, with a meter and a counter telling you whether you chose right.

You don't read this course. You build it — in five rounds, with a coding agent as your
Socratic tutor, against a real LLM and a real database. Your numbers will differ from
everyone else's. That is part of the lesson.

## The pedagogical pattern

Every round runs the same loop. Each phase ends in a git commit carrying exactly one
artifact, so the repository itself is the courseware:

```
 TUTOR ────────► SPEC ──────► BUILD ─────► DEMO
   │               │             │            │
 answers.md     spec.md        src/       demo-log.md
 your words      diff           diff      your numbers
```

1. **Socratic question.** The tutor asks — one question per turn, rungs (narrower
   questions, or "go look at this") before answers, never a lecture. Each question is
   authored so that *its correct answer is a specification clause*. Your accepted
   answers are written into the round's `answers.md` as you go — in your words.
2. **Your right answer fills the scaffolded spec.** The tutor drafts each clause from
   *your* recorded words, you confirm the wording, and it lands in `spec/spec.md`.
3. **Observe the spec diff.** `git diff` shows exactly which requirements your answers
   just created. The spec was not handed to you — you argued it into existence.
4. **The coding agent builds against the spec.** A minimal diff to one file
   (`src/snackbot.py`), each changed line carrying the ID of the clause — *your
   answer* — that demanded it.
5. **Observe the code diff and the round's demo.** After every diff comes the **diff
   dialogue**: the one place the tutor drops the Socratic act and answers questions
   about anything on screen — a term, a library, a line of syntax — plainly and
   completely.
6. **Operate the demo yourself.** Predict → run → observe → record. The round's
   pedagogical goal becomes something you *measured*, not something you were told.

## Steering the tutor

The tutor tags every reply with its mode — `[R2 · TUTOR]`, `[R3 · EXPAND]` — so you can
always see which hat it's wearing. Three phrases it must always honor:

- **"explain"** — drop the Socratic act and answer plainly, until you say done
- **"stop telling, ask me"** — snap back to questioning, immediately
- **"just tell me"** — reveal the current answer, no friction, and move on

If the tags drift (it's explaining during `TUTOR` without being asked), say so — that's
the design working, not failing.

## The five rounds

| Round | You learn | You build | The demo shows |
|---|---|---|---|
| 1 | What a memory operation is; instrument before you optimize | The meter | Allergy **already in the database** — bot still recommends peanut butter. Baseline ~21 input tokens |
| 2 | Deterministic: *code invokes* — reads **and** writes, every turn | Exact SQL read + write by rule | Safe every time; survives process death; ~5× tokens **every** turn — fails on **cost, visibly** |
| 3 | Agent-triggered: *model invokes*, via tools; semantic search matches by meaning | Preload out, two search tools in | Sometimes it checks memory, sometimes not — cheapest turn *and* most dangerous reply |
| 4 | One passing run proves nothing; count | The five-run harness | `--x5` → typically 2–4 of 5 SAFE. Fails on **reliability, silently** |
| 5 | The per-operation decision; the bootstrap argument | Pin **one** read (a two-line diff) | `--x5` → 5/5, at a cost between the extremes |

Round 5's questions are a judgment drill — six real operations (Q5.1–Q5.6), and you
commit to a classification *and a written reason* before each verdict is revealed. Two
of the six are legitimately contested: the point is not the "right" answer but choosing
knowingly, and hearing what your choice costs.

## Quickstart

**1 — Clone your own copy.** The course records your progress as git commits inside the
copy you run it in, so take a fresh one — and name it after your run, not after the
course:

```bash
git clone https://github.com/Carr1005/deterministic-vs-agent-triggered.git snackbot-my-run
cd snackbot-my-run
```

You need Python 3.10+, git, and an OpenAI API key. (A downloaded ZIP or a plain folder
copy also works — `setup/bootstrap.sh` handles all of them.)

*Working on the course itself rather than taking it? Clone `-b main` — that branch carries
the full authoring history. The default branch is a single squashed commit, so a learner's
`git log` reads as the course.*

**2 — Export your API key.** In the terminal you are about to start your agent from:

```bash
export OPENAI_API_KEY=sk-...
```

That is the only setup you do. Everything else the tutor handles on its first turn: it
builds the Python environment (about twenty seconds, once) and puts the seeded database
in place. The seeded "previous session" the whole course rests on already ships in
`setup/fixtures/memory-seed.db`, and your clone is already a git repo, so there is
nothing to initialise.

(Prefer to do it yourself first? `bash setup/bootstrap.sh` — same thing, one command,
always safe to re-run. Step by step: `setup/SETUP.md`. On Windows, use WSL.)

**3 — Open your coding agent in this folder** — from that same terminal, so it inherits
`OPENAI_API_KEY` — and say:

> **Read AGENTS.md and start the course.**

That line works in **any** agent, because it names only `AGENTS.md` — the vendor-neutral
instruction file this course keeps all its rules in. If the agent says the copy isn't set
up, let it run `setup/bootstrap.sh` for you.

Plain `start the course` also works wherever the agent loads `AGENTS.md` by itself:

| agent | how it finds `AGENTS.md` |
|---|---|
| Codex · Cursor · Cline · Windsurf · Zed · Copilot | automatically, no config |
| Claude Code | `CLAUDE.md` in this repo is one line: `@AGENTS.md` |
| Gemini CLI | `.gemini/settings.json` in this repo points it at `AGENTS.md` |
| Aider | `.aider.conf.yml` in this repo does the same |
| anything else | use the boot line above |

Those three files contain **no rules** — only a pointer to `AGENTS.md`, so there is
exactly one place tutoring behaviour is defined. If the first reply has no mode tag
(`[R1 · TUTOR]`), the instructions didn't load: paste the boot line.

Stop anytime. Progress lives in git commit names (plus your in-progress `answers.md`),
not in the chat — a new session, or a *different* coding agent, resumes from
`git log` + `git status`. Start Round 1 in Claude Code, finish Round 5 in Codex.

## What's in this folder

```
README.md            you are here (for humans)
AGENTS.md            the agent's constitution: modes, tags, tutoring/build/demo rules
CLAUDE.md            one line: @AGENTS.md — a pointer, never a second rulebook
.gemini/, .aider.conf.yml   same idea for Gemini CLI and Aider
course/PROTOCOL.md   the state machine: phases, commits, resume table
course/demo-log.md   your recorded numbers, round by round
course/rounds/N/     questions (with rungs + clause templates), answers.md (yours),
                     tutor-notes (spoilers), build brief, demo script, reference/,
                     verify.sh
course/rounds/round-0/reference/  the pristine baseline src, for restores
spec/spec.md         the living spec — empty scaffold; your answers fill it
src/                 a runnable app from minute one (snackbot.py, meter.py, seed)
memory.db            copied from setup/fixtures/ at setup; git-ignored (this IS the memory)
setup/               bootstrap.sh (the one command), SETUP.md, check.sh,
                     init.sh (fallback), pristine.sh (author tool), requirements.txt,
                     fixtures/memory-seed.db (the shipped 'previous session')
tools/diffview/      optional: serves your round-by-round diffs at localhost:4000
interim-docs/        course-developer notes (not part of the learner experience)
```

Two honor-system notes: `course/rounds/*/tutor-notes.md` contain the answers — reading
ahead spoils the round for you and only you. And the tutor never blocks: two honest
attempts earn a reveal, and "just tell me" earns it immediately.
