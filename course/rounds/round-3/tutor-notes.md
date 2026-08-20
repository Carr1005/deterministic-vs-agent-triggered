# Round 3 — tutor notes (SPOILERS)

## Q1 — model answer
**The model invokes**, via **tool calls**, at its own per-turn discretion.
**Accept if:** invoker = model AND mechanism = tool/function call. "It decides" without
the mechanism → half credit, rung 2.
**Reveal:** "Agent-triggered: the model invokes the operation through a tool call, at
its own discretion. Two tools over the same database — past conversations, snack facts —
and every read becomes a judgment call. Your words?"

## Q2 — model answer
**Writes stay deterministic.** The Round-2 silent-rot argument is unchanged — stronger,
if anything, since the store now also feeds tool results. Key idea: read and write
strategies are independent, per-operation decisions.
**Accept if:** writes stay deterministic AND the silent-rot reason. "Flip everything for
consistency" → rung 1: consistency is not an argument; failure modes are.
**Reveal:** "Writes stay deterministic — your own Round-2 argument didn't change. This
is the course's real thesis surfacing early: deterministic vs agent-triggered is decided
*per operation*, not per system. Restate?"

## Q3 — model answer
Both phrasings are embedded as **vectors**; the search matches by **meaning** (vector
similarity), not keywords — the two land near each other in embedding space.
**Accept if:** embeddings/vectors/semantic similarity + meaning-not-keywords.
**Reveal:** "The store is a vector store: both sentences are embedded, and 'dietary
restrictions' lands near 'allergic to peanuts' in that space. Matching by meaning is
what makes tool-reads workable at all. Your words?"

## Gate criteria
(a) agent-triggered = model invokes via tool call, per-turn discretion; (b) the thing
now probabilistic = **whether the read happens at all** (the safety check itself). The
demo shows it; Round 4 counts it.
