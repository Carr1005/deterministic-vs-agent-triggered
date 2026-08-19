# Round 2 — TUTOR: deterministic memory

> **MODE: TUTOR** — tag replies `[R2 · TUTOR]`. One question per turn; end every turn
> with a question. Rungs are questions or observations only; declarative answers exist
> only in the reveal. Record accepted answers into `answers.md` as you go.

**Round goal:** define *deterministic* precisely (code invokes — every turn, by rule,
regardless of model judgment), extend it to writes, and know the test separating memory
from a context window. The demo then exposes its failure axis: **cost, visibly.**

---

## Q1 — who invokes, and when  `type: single-answer`

**Ask:** "Round 1 ended with a stored fact nobody read. The first fix is the blunt one:
make the read *deterministic*. Precisely: who invokes a deterministic operation, and
when does it run?"

- **rung 1:** "Your own S1.1 names exactly two candidate invokers. Which one fires this
  read — and does the other get a vote?"
- **rung 2:** "Suppose the read ran only when the model judged it useful. Could you
  still promise 'the bot never forgets the allergy'? What has to be true about *when it
  runs* for that promise to hold?"

**Clause template (S2.1):**
> S2.1 `[deterministic]` — Before composing every answer, **code** performs an exact SQL
> read of prior-session turns (keyed by thread id, in the order they were written) and injects them
> into the prompt. Every turn; the model is never consulted. *(learner: «…»)*

## Q2 — the writes  `type: single-answer`

**Ask:** "Reads recall the past — but something has to *create* the past. Should the
write of each turn be deterministic too, or left to the model's judgment? What goes
wrong in the second case?"

- **rung 1:** "If the model chose, turn by turn, what was worth saving — and misjudged
  once a week — what would you see at the moment of each miss?"
- **rung 2:** "Nothing crashes; no error prints. So *when* do you discover the gap —
  and how long has it existed by then?"

**Clause template (S2.2):**
> S2.2 `[deterministic]` — After every user message and every assistant reply, **code**
> persists the turn to `CONVERSATIONAL_MEMORY`. Writes are never left to model
> discretion. *(learner's failure description: «…»)*

## Q3 — memory vs context window  `type: single-answer`

**Ask:** "What separates *memory* from a long context window — and what concrete test
proves this system has the real thing?"

- **rung 1:** "What event kills a context window instantly, but must not kill memory?"
- **rung 2:** "Design the proof as two shell commands: what runs first, what runs
  second, and what must the second one show?"

**Clause template (S2.3):**
> S2.3 — Memory must survive process death: a **new process** must recall the content of
> previous sessions. *(learner's test: «…»)*

---

## Gate

Own words: **what makes an operation deterministic (who invokes, when)** — plus a
prediction: **what will the meter show in the demo versus your Round-1 baseline?** Any
directionally-right prediction passes; the demo supplies the number. Record both in
`answers.md`, then:
`git add course/rounds/round-2/answers.md && git commit -m "round-2 tutor"` → SPEC.
