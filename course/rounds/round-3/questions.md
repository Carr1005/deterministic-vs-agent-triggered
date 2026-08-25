# Round 3 — TUTOR: agent-triggered memory

> **MODE: TUTOR** — tag replies `[R3 · TUTOR]`. Interaction rules: `course/TUTORING.md`
> (read at phase entry — it is authoritative). Record accepted answers into `answers.md`
> as you go.

**Round goal:** hand the reads to the model as tools it decides when to call, and find out
what that trade costs. Semantic matching is what makes tool-reads workable at all; the
writes stay on their rule. The demo shows both stores composing on one question — and the
meter going *up*, not down. Nothing now guarantees the read happens; **whether it happens
is the model's call**, which is what Round 4 sets out to measure.

---

## Q1 — who fires the read now  `type: single-answer`

**Ask:** "Your Round 2 bot reads the last conversation before every single reply. You
watched it pay full price on 'is it raining in Paris' — a turn that needed no memory at
all. Code fired that read because your rule said so. We need something that can judge,
turn by turn, whether a read is worth doing. What do we already have?"

- **rung 1:** "What part of this system is actually reading the question when that read
  fires?"

**Model answer:**
**The model** — it is the one reading the question, so it is the only part of the system
that can judge whether this turn needs a read.
**Accept if:** the model / the LLM / the agent. One word is enough. Anything else in the
system ("the database", "the meter") or a person ("me", "the user") → rung 1; the user
isn't the one deciding whether to hit the database.
**On accept, name it:** "Right — the model is the thing reading the question, so it's the
only thing that can judge whether a read is worth doing. So we stop firing reads from
code and hand them over as tools: `search_memory` over past conversations,
`search_knowledge_base` over snack and allergen facts. Each fires only when the model
calls it. That's `[agent-triggered]`."
**Reveal:** "The model. It's the one reading the question, so it's the one that can tell
whether this turn needs memory — and from here the reads are tools it may call:
`search_memory` and `search_knowledge_base`. Finish this: in Round 2 the read was fired
by ___; from now on it's fired by ___."

**Clause template (S3.1):**
> S3.1 `[agent-triggered]` — The every-turn preload is removed. The reads are **offered**
> to the model as tools, and the **model** invokes them at its own discretion. Two tools
> over the same database:
> `search_memory` (past conversations) and `search_knowledge_base` (snack & allergen
> facts). *(learner's phrasing: «…»)*

## Q2 — the semantic gap  `type: single-answer`

**Ask:** "The model will ask memory for the user's *'dietary restrictions'*. Memory
contains *'I'm allergic to almonds'*. Zero keywords in common. Why can the search still
find it?"

- **rung 1:** "`WHERE content LIKE '%dietary%'` returns zero rows here. So whatever
  found it wasn't comparing words. What else can two sentences have in common?"
- **rung 2:** "Open `src/seed_memory.py`. Every piece of text gets stored with something
  else beside it. What is that second thing?"

**Model answer:**
Both phrasings are embedded as **vectors**; the search matches by **meaning** (vector
similarity), not keywords — the two land near each other in embedding space.
**Accept if:** the match located in **meaning rather than words** — "it compares
meaning", "semantic search", "they're embedded as vectors and the vectors are close".
Vector vocabulary is welcome but **not required**. An answer still about words → rung 1.
**On accept, name it:** "Right — and this is what makes tool-reads possible at all. The
model has no idea what words are sitting in your database. If the search compared words,
it would have to guess your exact phrasing to find anything. Comparing meaning means it
can ask for 'dietary restrictions' and still find 'allergic to almonds'. That's why every
row in the store has a vector beside it."
**Reveal:** "The store keeps a vector beside every row — a list of numbers standing for
what the text means. 'dietary restrictions' and 'allergic to almonds' land close together
in that space, so the search finds one from the other. Finish this: the search compares
___, not ___."

**Clause template (S3.3):**
> S3.3 — Both searches are **semantic**: vector similarity over embeddings, matching by
> meaning rather than keywords, so the model's phrasing need not match the stored
> phrasing. *(learner's phrasing: «…»)*

---

## Gate

**Ask:** "What does this round's design guarantee about the allergy check?"

- **rung:** "What has to happen before the allergy gets looked up at all?"

**On accept:** "Right — nothing. It can look, and often will, but nothing forces it.
Round 2's rule made forgetting *impossible*; this design makes it *unlikely*. Round 4
exists to measure the distance between those two words."

Record it in `answers.md`, then:
`git add course/rounds/round-3/answers.md && git commit -m "round-3 tutor"` → SPEC.

**Gate criteria:**
Nothing is guaranteed — "nothing", "only that it *can* look", "that it might check, not
that it will". A confident "it always checks" → the rung. One rung max. Not required:
the mechanism (Q1 recorded it) or the cost (the demo delivers it).

## SPEC note

S3 gets three clauses: **S3.1 from Q1, S3.3 from Q2** (the question numbers and clause
numbers do not line up in this round). **S3.2 you state while drafting** — say so out
loud, don't quiz it:

> S3.2 `[deterministic]` — Writes remain deterministic, unchanged from S2.2. Read
> strategy and write strategy are **independent, per-operation decisions**.

Suggested wording: "One more clause, and I'll state this one rather than ask — you
already argued it in Round 2. The writes don't change: you put them on a fixed rule
because a skipped save fails silently, and handing the reads to the model doesn't touch
that argument. Notice what just happened, though. You changed the read's design and left
the write's alone. Same system, two operations, two different answers — that's the move
Round 5 asks you to make six times."
