# Round 1 — tutor notes (SPOILERS — learner: reading this spoils the round)

## Q1 — model answer
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

## Q2 — model answer
The **meter**. Both memory styles fail on a measurable axis — deterministic on cost,
agent-triggered on reliability — and **a trade-off you cannot measure is a trade-off
you cannot reason about**. Without a baseline, Round 2's "5×" is invisible.
**Accept if:** names measurement/instrumentation AND a measure-before-optimize reason
(baseline / making the trade-off visible). "To debug" is half credit → rung 2.
**Reveal:** "The meter: tokens, cost, latency on every turn. It comes first because the
whole course is a cost-vs-reliability trade-off, and today's baseline is what makes
every later number mean something."

## Gate criteria
Both present, any phrasing: (a) operations classified by *who invokes* — code vs model;
(b) meter first because you can't evaluate what you can't measure.
