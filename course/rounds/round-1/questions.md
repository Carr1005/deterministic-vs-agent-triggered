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
- Two misses → reveal (the **Reveal** block below) → own-words restatement → record → move on.

**Model answer:**
A memory operation is **any read or write** against the memory store. The classifying
question is **"who invokes it?"** — `deterministic`: *code* invokes (every turn, on a
schedule, on a predefined condition), regardless of model judgment; `agent-triggered`:
*the model* invokes, via a tool call, at its own discretion.
**Accept if:** reads-and-writes (or equivalent) AND the classification located in *who
causes it to run* (code vs model / rule vs judgment). "Read vs write" alone, or "SQL vs
vector search", is a miss — mechanics, not invocation. Near-miss "whether it's
automatic" → ask: automatic according to whom?
**Reveal:** "A memory operation is any read or write against the store. The classifying
question: who invokes it? Code firing it by rule — deterministic. The model firing it by
choosing to call a tool — agent-triggered. Same database, different invoker, completely
different failure modes. Say it back in your own words?"

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

**Model answer:**
The **meter**. Both memory styles fail on a measurable axis — deterministic on cost,
agent-triggered on reliability — and **a trade-off you cannot measure is a trade-off
you cannot reason about**. Without a baseline, Round 2's "5×" is invisible.
**Accept if:** names measurement/instrumentation AND a measure-before-optimize reason
(baseline / making the trade-off visible). "To debug" is half credit → rung 2.
**Reveal:** "The meter: tokens, cost, latency on every turn. It comes first because the
whole course is a cost-vs-reliability trade-off, and today's baseline is what makes
every later number mean something."

**Clause template (S1.2):**
> S1.2 — Every turn must report its own footprint: input tokens, output tokens,
> estimated cost, and latency, as a `[meter]` line. No memory change lands without the
> meter measuring it. *(learner's reason it comes first: «…»)*

---

## Gate

Ask for one or two sentences, own words: **what a memory operation is, who the two
possible invokers are, and why the meter precedes any memory.** Criteria in
the **Gate criteria** block below. Record the restatement in `answers.md`, then:
`git add course/rounds/round-1/answers.md && git commit -m "round-1 tutor"` → SPEC.

**Gate criteria:**
Both present, any phrasing: (a) operations classified by *who invokes* — code vs model;
(b) meter first because you can't evaluate what you can't measure.
