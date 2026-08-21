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

**Model answer:**
**Code invokes**, running **every turn** (or on a fixed schedule / predefined
condition), **regardless of model judgment** — the model gets no vote.
**Accept if:** invoker = code/app AND timing = every turn / by rule / unconditionally.
"Automatic" alone → automatic according to whom? "SQL" is mechanics, not classification.
**Reveal:** "Deterministic: your *code* invokes it, every turn, by rule. The model is
never asked whether the read is worth doing. That guarantee is the point — and its price
tag is what the demo shows. Your words?"

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

**Model answer:**
Deterministic. Model-discretion writes create **silent gaps** — nothing crashes; the
store quietly rots and you discover a hole only when a recall fails weeks later.
**Accept if:** deterministic AND silent/quiet failure. "It might miss things" is half
credit → rung 2 (how would you notice, and when?).
**Reveal:** "Deterministic — every turn, by rule. Model-discretion writes fail as silent
rot: no crash, just gaps found only when a recall comes back empty. A bad *read* fails
one turn; a bad *write* poisons every future turn. Restate that?"

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

**Model answer:**
Memory **survives process death**; a context window dies with its process. Test: run
once, kill the process, run a **new process** and ask about the previous session — it
must answer.
**Accept if:** process death / restart / new-session recall named. "It's on disk"
without the test → half credit, rung 2.
**Reveal:** "A context window, however long, dies with the process. Memory survives it.
The proof is two commands: run, then run again as a new process and ask what was said
before. The demo does exactly this. Say the test back?"

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

**Gate criteria:**
(a) deterministic = code invokes, every turn, no model vote; (b) any prediction of a
substantial per-turn cost increase (demo shows ~5× baseline, even for questions needing
no memory).
