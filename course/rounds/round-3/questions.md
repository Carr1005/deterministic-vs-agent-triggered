# Round 3 — TUTOR: agent-triggered memory

> **MODE: TUTOR** — tag replies `[R3 · TUTOR]`. One question per turn; end every turn
> with a question. Rungs are questions or observations only; declarative answers exist
> only in the reveal. Record accepted answers into `answers.md` as you go.

**Round goal:** define *agent-triggered* (the model invokes, via tools, at its own
discretion), see why the writes do NOT flip, and how semantic search bridges wordings
that share no keywords. The demo exposes the failure axis: **reliability, silently.**

---

## Q1 — the flip  `type: single-answer`

**Ask:** "Round 2's guarantee cost 5× on every turn — including 'is it raining?'. The
opposite design deletes the every-turn preload entirely. If code no longer invokes the
reads: who does, and by what mechanism?"

- **rung 1:** "Your S1.1 names two invokers and code just resigned. Who's left — and is
  'being left' enough, or do they need a mechanism to actually fire a read?"
- **rung 2:** "What is the one mechanism an LLM has for making anything happen outside
  its own text?"

**Clause template (S3.1):**
> S3.1 `[agent-triggered]` — The every-turn preload is removed. The **model** invokes
> reads at its own discretion, via tool calls. Two tools over the same database:
> `search_memory` (past conversations) and `search_knowledge_base` (snack & allergen
> facts). *(learner's phrasing: «…»)*

## Q2 — what does NOT flip  `type: single-answer`

**Ask:** "We're flipping the reads. Do the writes flip too? Defend your answer with the
failure you named in Round 2."

- **rung 1 (observe):** "Open `course/rounds/round-2/answers.md` and read back your own
  Q2 answer. Does flipping the *reads* change a word of it?"
- **rung 2:** "Round 4 will count how often read-judgment fails. If *write*-judgment
  fails at the same rate — when, and how, would you ever find out?"

**Clause template (S3.2):**
> S3.2 `[deterministic]` — Writes remain deterministic, unchanged from S2.2. Read
> strategy and write strategy are **independent, per-operation decisions**.
> *(learner's reason: «…»)*

## Q3 — the semantic gap  `type: single-answer`

**Ask:** "The model will ask memory for the user's *'dietary restrictions'*. Memory
contains *'I'm allergic to peanuts'*. Zero keywords in common. Why can the search still
find it?"

- **rung 1:** "`WHERE content LIKE '%dietary%'` returns zero rows here. So whatever
  matches them isn't comparing words. What else can two sentences have in common?"
- **rung 2 (observe):** "Open `src/seed_memory.py` and look at what gets stored next to
  each piece of text. What is that second column, and what could you compute with two
  of them that you could never compute with two strings?"

**Clause template (S3.3):**
> S3.3 — Both searches are **semantic**: vector similarity over embeddings, matching by
> meaning rather than keywords, so the model's phrasing need not match the stored
> phrasing. *(learner's phrasing: «…»)*

---

## Gate

Own words: **what agent-triggered means (who invokes, via what)** — and name **the
thing that was a guarantee in Round 2 and just became probabilistic.** Record in
`answers.md`, then:
`git add course/rounds/round-3/answers.md && git commit -m "round-3 tutor"` → SPEC.
