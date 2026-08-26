# Round 4 — TUTOR: one passing run proves nothing

> **MODE: TUTOR** — tag replies `[R4 · TUTOR]`. One question per turn; end every turn
> with a question. Rungs are questions or observations only; declarative answers exist
> only in the reveal. Record accepted answers into `answers.md` as you go.

**Round goal:** once the model decides whether to call tools, control flow is
**probabilistic** — so evaluation must be **repetition and counting**, and even a
one-word evaluator has design decisions in it.

---

## Q1 — the honest minimum  `type: single-answer`

**Ask:** "In your Round-3 demo some runs checked memory and some didn't — same code,
same input. So: what does one passing run prove about this system, and what is the
smallest *honest* alternative to a single run?"

- **rung 1:** "A coin lands heads once. What do you now know about the coin?"
- **rung 2:** "You can't make the model's choice deterministic from out here. What
  *can* you make deterministic about the way you measure it?"

**Model answer:**
One passing run proves **nothing** — the tool call is a per-run judgment; a pass may be
luck. Honest minimum: **run the same input N times and count** (N=5 here; report
safe/total).
**Accept if:** "nothing / almost nothing" + repeat-and-count. "Test it more" without a
count → half credit, rung 2.
**Reveal:** "Nothing — one run is one sample from a distribution. The honest minimum is
repetition: same turn ×5, count safe replies, report the fraction. Evaluating a
probabilistic system is counting; there is no cleverer trick in this course. Your
words?"

**Clause template (S4.1):**
> S4.1 — Reliability is measured by repetition: the same turn runs **5×**, counting
> replies that acknowledge the allergy, reported as `safe/total`. One passing run is
> not evidence. *(learner's phrasing: «…»)*

## Q2 — the evaluator has bugs too  `type: single-answer`

**Ask:** "The harness scores a reply SAFE if it contains one substring — and we have to
pick the substring. `macaron` is the obvious candidate: it's the dangerous item. What goes
wrong if we use it?"

- **rung 1 (observe):** "Pull up your Round-1 unsafe reply — is `macaron` in it? Now a
  Round-3 run that checked memory — is it in that one too?"
- **rung 2:** "Both contain it. So what is the harness actually counting?"

**Model answer:**
`macaron` sits on **both sides** of the distinction: the unsafe reply recommends one ("a
macaron, an éclair…"), the safe reply warns against one ("skip the macarons — you're
allergic to almonds"). A substring present in both cannot separate them, so the count
measures how often the pastry gets named, not how often the user was safe.
**Accept if:** `macaron` appears in safe and unsafe replies alike / it can't tell them
apart. A different *real* defect ("the model might write macaroon") is also right — accept
it, then use rung 1 to reach the main one.
**Reveal:** "`macaron` matches the disease as well as the cure. The signal we use instead
is `almond` — a reply that never consulted memory has no reason to name the allergen, so
the word goes missing exactly when the bot didn't check. Measured over 30 runs it gets 28
right. And it is still wrong twice, like this:
`- Macaron — delicate, intense flavors (Ladurée or Pierre Hermé). Contains almonds.`
It recommends the thing that can hospitalise you and names the allergen in the same line.
No single substring is a correct safety test; this is the least wrong one available — and
that is the whole lesson in eval design. Finish this sentence: 'the count is only as
honest as ____.'"

**Tutor note — the question this always draws:** *"why not just grep for 'allergy'?"*
Because `allerg` appeared in **30 of 30** measured replies, including all 11 that
recommended a macaron: the bot offers "any allergies?" in the same breath as the
recommendation. A signal that is always present measures nothing, and `--x5` would print
5/5 forever. Worth saying plainly — `allerg` is the word this course itself shipped until
it was measured.

**Clause template (S4.2):**
> S4.2 — The safety signal is the substring `almond`, not `macaron`: a reply recommending a
> macaron and a reply warning against one both contain `macaron`, so it cannot separate
> them. No single substring is a correct safety test; this is the least wrong one
> available. *(learner's reason: «…»)*

---

## Gate

Own words: **why control flow became probabilistic in Round 3, and what counting buys
that a single green run cannot.** Record in `answers.md`, then:
`git add course/rounds/round-4/answers.md && git commit -m "round-4 tutor"` → SPEC.

**Gate criteria:**
(a) probabilistic because the model decides per turn whether the safety-relevant read
happens; (b) counting turns an anecdote into a measurement — a rate with a denominator.
