# Round 1 — TUTOR: the failure, and the meter

> **MODE: TUTOR** — tag replies `[R1 · TUTOR]`. One question per turn; end every turn
> with a question. Rungs are questions or observations only; declarative answers exist
> only in the reveal. Record accepted answers into `answers.md` as you go.

**Round goal:** know what a "memory operation" is, know the one question that classifies
every one of them, and understand why the *meter* must exist before any memory design.

**Scene-set (say briefly before Q1):** the database shipped with a previous session
already in it — the peanut allergy is *already stored*, in two forms, before the learner
ran anything at all. Yet `src/snackbot.py` today is a bare LLM call. This round we don't
fix that; we name the problem and build the instrument.

---

## Q1 — the classification question  `type: single-answer`

**Ask:** "The database already knows about the allergy, and the bot will still recommend
peanut butter — we'll watch it happen shortly. To even discuss the fix we need a unit of
analysis. In your own words: what counts as a *memory operation*, and what single
question classifies every one of them?"

- **rung 1:** "Think in verbs — what are the only two things any system can do with a
  store of facts?"
- **rung 2 (observe):** "Open `src/snackbot.py` and count the memory operations in it.
  Zero — yet `.venv/bin/python setup/show_memory.py` shows a full store. So is the property that
  matters *what an operation does* — or something about what makes it run at all?"
- Two misses → reveal (tutor-notes) → own-words restatement → record → move on.

**Clause template (S1.1):**
> S1.1 — Every read or write SnackBot performs against its memory store is a *memory
> operation*. Each must be classified by who invokes it: `[deterministic]` (code
> invokes) or `[agent-triggered]` (model invokes). *(learner's phrasing: «…»)*

## Q2 — instrument before you optimize  `type: single-answer`

**Ask:** "Before we add a single memory operation, one thing must be built first — and
it stores nothing and remembers nothing. What is it, and why does it come first?"

- **rung 1:** "Every design in this course is a trade-off. What must exist before you
  can compare two trade-offs at all?"
- **rung 2 (observe):** "Run `.venv/bin/python src/snackbot.py` and read everything it prints.
  What did that turn cost — tokens, money, time? Can you answer from what's on screen?"

**Clause template (S1.2):**
> S1.2 — Every turn must report its own footprint: input tokens, output tokens,
> estimated cost, and latency, as a `[meter]` line. No memory change lands without the
> meter measuring it. *(learner's reason it comes first: «…»)*

---

## Gate

Ask for one or two sentences, own words: **what a memory operation is, who the two
possible invokers are, and why the meter precedes any memory.** Criteria in
tutor-notes.md. Record the restatement in `answers.md`, then:
`git add course/rounds/round-1/answers.md && git commit -m "round-1 tutor"` → SPEC.
