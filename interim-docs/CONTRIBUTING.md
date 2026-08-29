# CONTRIBUTING — how this repo is managed

Not learner content. If you are here to *take* the course, close this and read `README.md`.

## Two branches, two jobs

| branch | job | rewritten? |
|---|---|---|
| **`main`** | authoring history. Where all work happens. | **never** — always safe to pull |
| **`release`** | what learners clone. One squashed commit, GitHub's default branch. | **every release**, force-pushed |

Why the split: a learner's `git log` should read as the course — `round-1 tutor`, `round-1
spec`, and so on — not as our changelog. Squashing `main` would achieve that and break
anyone holding a clone. Publishing a separate branch achieves it and breaks nobody.

Force-pushing `release` is safe *by construction*: nobody keeps a long-lived clone of it,
because `README.md` tells learners to take a fresh copy per run.

Nothing functional depends on the short history. The tutor's resume rule is "no `round-N`
commit means the course has not started" (`course/PROTOCOL.md`), so any amount of authoring
history works. This is presentation only.

## Working on it

```bash
git clone -b main https://github.com/Carr1005/deterministic-vs-agent-triggered.git
# already have a clone? nothing was rewritten, so it fast-forwards:
git fetch origin && git checkout main
```

A plain `git clone` gives you `release` — a single commit with no history. Don't work there.

## Adding something

```bash
git checkout -b my-thing main
# … commit as you like; ordinary history is welcome on main …
git checkout main && git merge my-thing
git push origin main            # required: the release guard refuses if main isn't pushed
bash tools/release.sh           # publishes release
git branch -d my-thing
```

You do **not** need to squash-merge. `main` is never what a learner sees, so a feature's
full commit history is worth keeping — that is where the reasoning lives. (The diff viewer
was squashed only because it landed before this split existed.)

## Publishing

`bash tools/release.sh`, from `main`, with a clean-ish worktree. It:

1. refuses unless you are on `main`
2. refuses if `main` is ahead of `origin/main` — otherwise the published course would
   contain commits nobody else can see
3. runs `setup/pristine.sh` and **stops** if it fails
4. rebuilds `release` with `git commit-tree` from `main`'s committed tree
5. asserts the release tree matches `main` and that its history is exactly one commit
6. force-pushes `release`

Step 4 matters more than it looks. It builds the commit straight from a tree object and
**cannot see the working directory**, so untracked files can never leak into what learners
clone. Do not replace it with `git checkout --orphan` plus `git add -A`: at the time of
writing, `interim-docs/trial-2/` is ~930 KB of untracked session log that `add -A` would
happily ship.

## If you are here to test it

Take the course first. Clone it, play it, and tell us what happened:

```bash
git clone https://github.com/Carr1005/deterministic-vs-agent-triggered.git snackbot-my-run
cd snackbot-my-run
export OPENAI_API_KEY=sk-...
claude
```

Then say `start the course`. You need Python 3.10+, git, and an OpenAI API key — nothing
else to install. A few cents of API cost for the whole thing.

**Reporting back.** Open an issue and name the version you tested (`v0.1`, and so on — see
the Releases page). If you reached a demo, paste your numbers from `course/demo-log.md`.
Those numbers are the most useful thing you can send, because everyone's differ and that
difference is the lesson.

**One rule.** The copy you played in is not the copy you contribute from. Playing fills in
your answers, writes the spec, changes `src/snackbot.py`, and adds `round-N` commits. If any
of that reaches the shared repo, every future learner's tutor thinks the course is already
underway. So to change something, start clean:

```bash
git clone -b main https://github.com/Carr1005/deterministic-vs-agent-triggered.git
```

then branch, commit, and open a pull request. If you can't push, fork it first — that is
expected, and it is why testers get read access rather than write.

## Working on one round: `tools/replay.py`

Developing Round 4 — its questions, its build brief, how it looks on the viewer — used to
mean playing Rounds 1-3 by hand first, with real API calls, every time. Instead:

```bash
python3 tools/replay.py --round 4          # tutor resumes at Round 4, first question
python3 tools/replay.py --through "round-4 spec"   # any phase boundary, precisely
python3 tools/replay.py --round 4 --mid-tutor      # …answers.md left uncommitted
python3 tools/replay.py --round 4 --serve          # …and serve the viewer there
```

It clones the repo to a throwaway directory under `$TMPDIR`, replays the course into it
one protocol commit at a time, seeds `memory.db` from the shipped fixture, and prints the
path plus the resume position. `cd` there and launch your agent and the tutor picks up at
the round you are working on. Your **uncommitted** edits are overlaid into the sandbox
before the replay, so a clause template you are still editing is the one that gets staged.

It writes nothing here: every git write goes through `git -C <sandbox>`, and a target
inside this repo, or one with an `origin` remote, is refused outright. That guard is the
second convention below, mechanised — a `round-N` commit in real history would make the
tutor resume mid-course.

**It does not produce a played course.** No model is called, and the answers are the
course's own model-answer prose rather than a learner's words, so `answers.md` reads in
the wrong voice by construction. Every commit it makes carries
`Synthesized by tools/replay.py — not a played round.` in its body, and the subjects stay
protocol-exact only because the resume table and the viewer match on them. The five-round
trial in `to-address.md` is still outstanding and this tool cannot close it.

## Two rules that are convention, not enforcement

GitHub branch protection needs a Pro plan or a public repo — this one is private on a free
plan, so both of these rest on us remembering:

1. **Never force-push `main`.** If you feel the urge, something has gone wrong; the whole
   point of the split is that `main` stays safe to pull.
2. **Never publish a played copy.** `setup/pristine.sh` is the gate, and `release.sh` runs
   it, but only if you use `release.sh`. A copy that has been through a round carries the
   learner's answers, a filled spec, and a built `src/snackbot.py` — and a `round-N` commit
   in published history makes every learner's tutor resume mid-course.

## The one place docs cannot hide

`main` and `release` point at the *same tree object*, which `release.sh` asserts. So every
file added for us is also in every learner's clone. That is why this file lives under
`interim-docs/`, which `README.md` already labels "course-developer notes (not part of the
learner experience)". There is no collaborator-only corner of this repo, and buying one
would mean breaking the tree-identity check that keeps releases honest.
