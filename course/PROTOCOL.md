# PROTOCOL.md — the course state machine

Five rounds. Every round runs four phases, in order:

```
TUTOR  →  SPEC  →  BUILD  →  DEMO
```

- **TUTOR** — Socratic Q&A from `round-N/questions.md`; the learner's accepted answers
  are recorded into `round-N/answers.md` as they go. Ends when the gate passes.
- **SPEC** — recorded answers become clauses in `spec/spec.md` (learner confirms
  wording). Produces a spec diff.
- **BUILD** — the agent patches `src/snackbot.py` toward `round-N/reference/`, scoped by
  `round-N/build.md`, until `round-N/verify.sh` passes. Produces a code diff.
- **DEMO** — the learner operates the app per `round-N/demo.md`: predict → run →
  observe → record. Produces an entry in `course/demo-log.md`.

Modes, mode tags (`[R2 · TUTOR]`), and the EXPAND sub-mode are defined in AGENTS.md.

## Git is the state machine

No state file. Each phase ends in exactly one commit, carrying exactly one artifact:

| phase ends | commit name | contains |
|---|---|---|
| TUTOR (gate passes) | `round-N tutor` | `course/rounds/round-N/answers.md` |
| SPEC | `round-N spec` | `spec/spec.md` |
| BUILD | `round-N build` | `src/snackbot.py` |
| DEMO | `round-N demo` | `course/demo-log.md` |

Because commits carry different artifacts, **diffs shown to the learner are always
scoped** — each phase file states its exact command (`git diff HEAD~1 -- spec/`,
`git diff HEAD~1 -- src/`).

## Resume table

Derive position from the **last course commit** in `git log --oneline`, then check
`git status --porcelain`. A *course commit* is one named `round-N tutor|spec|build|demo`.
Any other commit in the log — the repo's own history — is not course state; **if there is
no course commit at all, the course has not started.**

| last course commit | working tree | you are at |
|---|---|---|
| none | `round-1/answers.md` modified | Round 1, TUTOR — resume at first unanswered question |
| none | clean | Round 1, TUTOR — first question |
| `round-(N-1) demo` | `round-N/answers.md` modified | Round N, TUTOR — resume at first unanswered question |
| `round-(N-1) demo` | clean | Round N, TUTOR — first question |
| `round-N tutor` | — | Round N, SPEC |
| `round-N spec` | — | Round N, BUILD |
| `round-N build` | — | Round N, DEMO |
| `round-5 demo` | — | DONE — offer the wrap-up in `round-5/demo.md` |

`answers.md` stays uncommitted during TUTOR on purpose: the dirty file is the mid-round
resume signal, and it is the learner's own record — not agent bookkeeping.

## Question types and groups

Every question carries `type: single-answer` or `type: judgment` (acceptance rules in
AGENTS.md). A **question group** is several sub-questions (`Q5.1`–`Q5.6`) sharing one
output artifact and one gate: ask one at a time, produce the artifact once. Round 5 is
an ordinary round containing one group of six judgment questions — no special protocol.

## Reconciliation rule

If the working tree disagrees with the last commit (the learner edited files outside
the loop): **git history is truth for position; the round's `reference/` is truth for
what `src/` should contain at each boundary.** Ask one question — "keep your changes or
restore the round state?" — then commit theirs as `round-N learner-edit` or restore.
Never silently discard learner work; never let untracked drift into a build diff.

## The honor system, stated once

Verify scripts check the build; nothing stops a learner from reading `tutor-notes.md`,
editing `answers.md` after a reveal, or skipping phases. By design — the course
optimizes for learning, not proctoring.
