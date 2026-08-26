# Round 2 — TUTOR: deterministic memory

> **MODE: TUTOR** — tag replies `[R2 · TUTOR]`. Interaction rules: `course/TUTORING.md`
> (read at phase entry — it is authoritative). Record accepted answers into `answers.md`
> as you go.

**Round goal:** commit the allergy read to a fixed rule and know its price; extend the
same rule to the writes. The demo then exposes this design's failure axis — **it fails
on cost, visibly** — and proves that memory outlives the process that wrote it.

---

## Q1 — write the rule  `type: single-answer`

**Ask:** "Round 1 ended with the allergy stored and ignored. This round we fix it with
the blunt design from your own S1.1: the allergy read runs by a fixed rule — no model
judgment. Now write the rule: when exactly does that read run?"

- **rung 1:** "Suppose the rule is 'only on turns that mention food'. The user asks
  'what should I bring hiking?' — what just slipped through?"
- **rung 2:** "The promise this round makes is 'the bot can never forget the allergy.'
  What's the only schedule that keeps that promise?"

**Model answer:**
**Every turn, unconditionally** — before every reply, no exceptions, no model vote.
**Accept if:** every turn / always / before every reply / unconditionally — any phrasing
of "no exceptions". A conditional schedule ("when relevant", "when food comes up") →
rung 1.
**On accept, name the price:** "Right — every turn, unconditionally: `[deterministic]`.
And notice what you just bought and what it costs: the model never gets a vote, so
forgetting is impossible — and you pay the read on every turn, including turns that need
no memory at all. The meter will show you that bill in the demo."
**Reveal:** "Every turn, unconditionally — that is the whole design. The model is never
asked whether the read is worth doing; that guarantee is the point, and its price tag is
what the demo shows. Finish this: the deterministic read runs ___, even on turns that
___."

**Clause template (S2.1):**
> S2.1 `[deterministic]` — Before composing every answer, **code** performs an exact SQL
> read of prior-session turns (keyed by thread id, in the order they were written) and injects them
> into the prompt. Every turn; the model is never consulted. *(learner: «…»)*

## Q2 — how the writes run  `type: judgment`

**Ask:** "The read now runs every turn — but it can only find what something wrote. The
same two designs apply to the write: run it by a fixed rule, or let the model judge,
turn by turn, what's worth saving. Which one, and why?"

- **rung 1** *(reason weak, or they picked "let the model judge")*: "Say the model misjudges
  one save a week. What breaks?"
- **rung 2:** "A bad read fails one turn. What does a bad write do to every turn that
  comes after it?"

**Model answer:**
Fixed rule — every turn. Model-discretion writes fail invisibly: a skipped save breaks
nothing at the moment it happens, and the hole surfaces only when a later read needs
it — or never.
**Accept if:** the call = fixed rule / every turn, with any coherent reason touching the
failure — "misses would be invisible", "you'd find gaps too late", "can't gamble routine
saves", "a lost turn is lost forever". A pick with no reason → ask for the one line
(the judgment contract). "We might never notice" is a *strong* reason, not a miss.
**On accept, name it:** "That failure shape is **silent rot** — no crash at write time,
a hole found at read time, or never. A bad read fails one turn; a bad write poisons
every future turn. So the writes run like the read: every turn, by rule —
`[deterministic]`. You'll make this same call again in Round 5."
**Reveal:** "Fixed rule — every turn, like the read. A write left to the model's
judgment fails as silent rot: no crash, just a gap found when a recall comes back
empty, or never found at all. Finish this: a write the model skipped fails ___, and you
find out ___ — or never."

**Clause template (S2.2):**
> S2.2 `[deterministic]` — After every user message and every assistant reply, **code**
> persists the turn to `CONVERSATIONAL_MEMORY`. Writes are never left to model
> discretion. *(learner's failure description: «…»)*

---

## Gate

Round 1's bot had the allergy sitting in its database and still recommended a
macaron. Your design makes that impossible. One sentence, own words: how would you
explain to a user why it can't happen again?

- **rung** *(vague — "because it has memory now")*: "What would have to go wrong for the
  bot to miss the allergy now — and can that happen under your rule?"

**On accept, add the half they didn't say:** "Right. And there's a second half you
already specified: it also *saves* every turn, so tomorrow's session inherits today's.
Both directions by rule."

Record it in `answers.md`, then:
`git add course/rounds/round-2/answers.md && git commit -m "round-2 tutor"` → SPEC.

**Gate criteria:**
The guarantee in the learner's own framing — "it checks every turn, whatever the question
looks like", "the check isn't optional", "the allergy goes into every prompt". This is
Q1's answer restated for a different audience, not new content: **accept the first
recognisable version and move on.** One rung maximum. Not required: the cost (the demo
delivers it) or the mechanism (Q1 recorded it). Keep the sentence crisp — Round 3's gate
asks the learner to flip exactly this promise.

## SPEC note

S2 gets three clauses. Two are drafted from the learner's answers above. The third you
simply state while drafting — say so out loud, don't quiz it:

> S2.3 — Memory must survive process death: a **new process** must recall the content of
> previous sessions.

Suggested wording: "One more requirement — I'll state this one rather than ask, because
the demo proves it in a few minutes. Every run of `snackbot.py` is a new process. It
builds its prompt from scratch, and that prompt — what people call the model's context
window — is gone the moment the process exits. The next run can only recall what code
read back out of `memory.db`. That file is the memory. That's S2.3."
