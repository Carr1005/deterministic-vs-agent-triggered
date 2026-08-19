# Round 4 — tutor notes (SPOILERS)

## Q1 — model answer
One passing run proves **nothing** — the tool call is a per-run judgment; a pass may be
luck. Honest minimum: **run the same input N times and count** (N=5 here; report
safe/total).
**Accept if:** "nothing / almost nothing" + repeat-and-count. "Test it more" without a
count → half credit, rung 2.
**Reveal:** "Nothing — one run is one sample from a distribution. The honest minimum is
repetition: same turn ×5, count safe replies, report the fraction. Evaluating a
probabilistic system is counting; there is no cleverer trick in this course. Your
words?"

## Q2 — model answer
**B — `allerg`.** Unsafe replies *also* contain 'peanut' ("peanut butter energy
balls"), so grepping 'peanut' scores the failure as a pass. 'allerg' appears only when
the reply acknowledges the allergy.
**Accept if:** picks `allerg` AND the unsafe-reply-contains-peanut reason. Right pick,
no reason → rung 1.
**Reveal:** "'peanut' matches the disease as well as the cure — an unsafe suggestion
literally names the ingredient. 'allerg' appears only when the constraint is
acknowledged. Even a one-word evaluator has design bugs — the smallest possible lesson
in eval design. Restate it?"

## Gate criteria
(a) probabilistic because the model decides per turn whether the safety-relevant read
happens; (b) counting turns an anecdote into a measurement — a rate with a denominator.
