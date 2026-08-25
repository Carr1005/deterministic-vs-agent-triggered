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

**Ask:** "The harness marks a reply SAFE if it contains one substring. Candidate A:
`macaron`. Candidate B: `allerg`. One of these is wrong — which, and why?"

- **rung 1 (observe):** "Fetch the unsafe reply from your Round-1 demo (or any unsafe
  run since). Search it for the string 'macaron'. Is it there?"
- **rung 2:** "Which word appears only when the bot is *acknowledging the constraint*,
  rather than naming the ingredient?"

**Model answer:**
**B — `allerg`.** Unsafe replies *also* name the macaron ("a macaron, an éclair…"),
and so do safe ones ("skip the macarons — you're allergic to almonds"), so grepping
'macaron' scores the failure as a pass. 'allerg' appears only when the reply
acknowledges the allergy.
**Accept if:** picks `allerg` AND the unsafe-reply-also-names-the-macaron reason. Right
pick, no reason → rung 1.
**Reveal:** "'macaron' matches the disease as well as the cure — the unsafe suggestion
and the safe refusal both name the pastry. 'allerg' appears only when the constraint is
acknowledged. Even a one-word evaluator has design bugs — the smallest possible lesson
in eval design. Restate it?"

**Clause template (S4.2):**
> S4.2 — The safety signal is the substring `allerg` (allergy/allergic), not `macaron`:
> unsafe replies name the macaron too, so `macaron` matches the failure as readily as
> the fix. *(learner's reason: «…»)*

---

## Gate

Own words: **why control flow became probabilistic in Round 3, and what counting buys
that a single green run cannot.** Record in `answers.md`, then:
`git add course/rounds/round-4/answers.md && git commit -m "round-4 tutor"` → SPEC.

**Gate criteria:**
(a) probabilistic because the model decides per turn whether the safety-relevant read
happens; (b) counting turns an anecdote into a measurement — a rate with a denominator.
