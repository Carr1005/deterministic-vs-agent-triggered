# Round 2 — tutor notes (SPOILERS)

## Q1 — model answer
**Code invokes**, running **every turn** (or on a fixed schedule / predefined
condition), **regardless of model judgment** — the model gets no vote.
**Accept if:** invoker = code/app AND timing = every turn / by rule / unconditionally.
"Automatic" alone → automatic according to whom? "SQL" is mechanics, not classification.
**Reveal:** "Deterministic: your *code* invokes it, every turn, by rule. The model is
never asked whether the read is worth doing. That guarantee is the point — and its price
tag is what the demo shows. Your words?"

## Q2 — model answer
Deterministic. Model-discretion writes create **silent gaps** — nothing crashes; the
store quietly rots and you discover a hole only when a recall fails weeks later.
**Accept if:** deterministic AND silent/quiet failure. "It might miss things" is half
credit → rung 2 (how would you notice, and when?).
**Reveal:** "Deterministic — every turn, by rule. Model-discretion writes fail as silent
rot: no crash, just gaps found only when a recall comes back empty. A bad *read* fails
one turn; a bad *write* poisons every future turn. Restate that?"

## Q3 — model answer
Memory **survives process death**; a context window dies with its process. Test: run
once, kill the process, run a **new process** and ask about the previous session — it
must answer.
**Accept if:** process death / restart / new-session recall named. "It's on disk"
without the test → half credit, rung 2.
**Reveal:** "A context window, however long, dies with the process. Memory survives it.
The proof is two commands: run, then run again as a new process and ask what was said
before. The demo does exactly this. Say the test back?"

## Gate criteria
(a) deterministic = code invokes, every turn, no model vote; (b) any prediction of a
substantial per-turn cost increase (demo shows ~5× baseline, even for questions needing
no memory).
