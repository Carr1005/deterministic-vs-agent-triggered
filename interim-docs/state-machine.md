# state-machine.md — how git history carries course state

Not learner content. Course-developer notes, written for anyone building on top of this
repo — a sandbox that provisions learner copies, a dashboard, a second course in the same
format. The canonical protocol source is `course/PROTOCOL.md`; this file explains the
design, it does not redefine it.

## How state is maintained

**There is no state file. Git history *is* the state machine.** The tutor derives its
position on every boot from two read-only commands: `git log --oneline` and
`git status --porcelain`.

```
                      ships pristine (release branch, 1 commit)
                                      │
                 ┌────────────────────▼────────────────────┐
        Round N │  TUTOR ──► SPEC ──► BUILD ──► DEMO       │──► Round N+1
                 └───────────────────────────────────────--┘
  each phase ends in EXACTLY ONE commit carrying EXACTLY ONE artifact:

  phase   commit message      artifact committed
  ─────   ───────────────     ─────────────────────────────────
  TUTOR   "round-N tutor"     course/rounds/round-N/answers.md
  SPEC    "round-N spec"      spec/spec.md
  BUILD   "round-N build"     src/snackbot.py
  DEMO    "round-N demo"      course/demo-log.md
```

Resume = the last `round-N <phase>` commit in the log, plus one dirty-file check:

```
git log has…            git status shows…              you are at
──────────────          ─────────────────              ──────────
no round-N commit       clean                          R1 TUTOR, Q1   ← pristine clone
no round-N commit       round-1/answers.md modified    R1 TUTOR, mid-round
"round-(N-1) demo"      clean                          RN TUTOR, Q1
"round-N tutor"         —                              RN SPEC
"round-N spec"          —                              RN BUILD
"round-N build"         —                              RN DEMO
"round-5 demo"          —                              DONE
```

Two deliberate subtleties:

- **`answers.md` stays uncommitted during TUTOR** — the dirty file is itself the
  mid-round resume signal. That is why "no state file" holds even mid-question.
- **Any non-`round-N` commit is invisible to the machine** — authoring history doesn't
  count as state, which is why `main`'s full changelog and `release`'s single squash
  both boot to "course not started".

## Why a played clone is one-way

State is written into **tracked courseware**, not into ignored files: `answers.md` loses
its `(not yet answered)` placeholders, `spec/spec.md` gains clauses, `src/snackbot.py`
diverges from the round-0 baseline, `course/demo-log.md` gains entries — and the log
gains `round-N` commits. There is no "reset" operation anywhere in the repo, and
`setup/pristine.sh` exists precisely to *prove a copy unstarted* before it is shared: it
checks all 21 answer placeholders, the 29-line spec scaffold, byte-identity of
`src/snackbot.py` with `course/rounds/round-0/reference/`, and greps the log for
`round-[1-5]` commits.

```
release (1 pristine commit)
   │ clone                      ── the only sanctioned direction ──►
   ▼
learner sandbox ──plays──► round-N commits + filled courseware
                                │
                                ├─ ✅ still fine FOR THAT LEARNER: they can stop,
                                │    relaunch, resume mid-question — that's the point
                                └─ ❌ terminal for everything else:
                                     · can't host a second learner (tutor resumes THEIR course)
                                     · can't be developed on (pristine.sh FAILs → release.sh refuses)
                                     · can't be "un-played" — no reverse edge exists
```

## Session vs run — the clone's exact lifetime

Two terms, kept apart on purpose:

- **Session** = one launch of the agent (one terminal conversation with the tutor).
- **Run** = one complete playthrough of the course, Round 1 → Round 5, by one learner.

A run spans many sessions. The clone's lifetime is exactly **one run**:

```
clone of release
   │
   ├── session 1: R1 TUTOR, quit mid-question ──┐
   ├── session 2: resumes at that question ...──┤   all the SAME run —
   ├── session 3: R3 BUILD ...──────────────────┤   reuse across sessions
   └── session N: "round-5 demo" committed ─────┘   is what git-as-state buys
                        │
                        ▼
                   run is over. The clone is now spent:
                   ✗ a NEW run     — impossible: the tutor reads "round-5 demo" and says DONE;
                                     no reset exists, short of re-cloning
                   ✗ development   — impossible: pristine.sh fails, release.sh refuses
```

So, un-ambiguously:

- **Within one run: fully reusable.** Quit, relaunch, switch agents, get
  context-compacted — the next session re-derives position from `git log` and continues.
  This is the design goal.
- **After (or during) that run, for any other purpose: spent.** It can't start over for
  the same learner, can't serve a different learner, can't be contributed from. One
  clone = one run, then discard.

For a sandbox that hosts learners, that means: provision a fresh clone of `release`
**per learner-run**, and the same sandbox freely survives disconnects and restarts within
that run — but "reset my course" must be implemented as *re-clone*, not as anything
inside the repo. This matches the contract in `CONTRIBUTING.md`: nobody keeps a
long-lived clone of `release`.

## The developer escape hatch: `tools/replay.py`

Without it, working on Round 4 would mean playing Rounds 1–3 by hand, with real API
calls, every time — and burning a clone per attempt. Instead, `replay.py` synthesizes the
protocol commits into a throwaway clone under `$TMPDIR`: no model calls, the answers are
the course's own model-answer prose, and every commit body carries
`Synthesized by tools/replay.py — not a played round.` It refuses to write into any
target inside this repo, or into any repo with an `origin` remote — the guard that keeps
fake state out of real history.
