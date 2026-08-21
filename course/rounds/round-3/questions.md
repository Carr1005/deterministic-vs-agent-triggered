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

**Model answer:**
**The model invokes**, via **tool calls**, at its own per-turn discretion.
**Accept if:** invoker = model AND mechanism = tool/function call. "It decides" without
the mechanism → half credit, rung 2.
**Reveal:** "Agent-triggered: the model invokes the operation through a tool call, at
its own discretion. Two tools over the same database — past conversations, snack facts —
and every read becomes a judgment call. Your words?"

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

**Model answer:**
**Writes stay deterministic.** The Round-2 silent-rot argument is unchanged — stronger,
if anything, since the store now also feeds tool results. Key idea: read and write
strategies are independent, per-operation decisions.
**Accept if:** writes stay deterministic AND the silent-rot reason. "Flip everything for
consistency" → rung 1: consistency is not an argument; failure modes are.
**Reveal:** "Writes stay deterministic — your own Round-2 argument didn't change. This
is the course's real thesis surfacing early: deterministic vs agent-triggered is decided
*per operation*, not per system. Restate?"

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

**Model answer:**
Both phrasings are embedded as **vectors**; the search matches by **meaning** (vector
similarity), not keywords — the two land near each other in embedding space.
**Accept if:** embeddings/vectors/semantic similarity + meaning-not-keywords.
**Reveal:** "The store is a vector store: both sentences are embedded, and 'dietary
restrictions' lands near 'allergic to peanuts' in that space. Matching by meaning is
what makes tool-reads workable at all. Your words?"

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

**Gate criteria:**
(a) agent-triggered = model invokes via tool call, per-turn discretion; (b) the thing
now probabilistic = **whether the read happens at all** (the safety check itself). The
demo shows it; Round 4 counts it.
