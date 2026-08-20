# Round 5 — tutor notes (SPOILERS)

Scoring: verdict + reason before any response from you. Rungs probe the reason.
Contested (Q5.5, Q5.6): any verdict with a coherent reason = full credit — **and the
reveal must name the cost of the side they chose.** No reason = miss; probe once, then
reveal.

**Q5.1 read_user_facts → deterministic.** Tiny, safety-critical, needed ~every turn —
and the **bootstrap argument**: the model cannot know whether memory holds something
relevant until a read has happened, so "let the model decide" is circular for the first
read. This is Round 4's silent failure, named.
*Reveal:* "Deterministic — pin it. Small, safety-critical, and no judgment can precede
it: the model can't know what's in memory until memory tells it. This is the read we
pin in today's build."

**Q5.2 search_memory → agent-triggered.** Unbounded corpus, occasional need; preloading
the long tail is Round 2's cost failure at scale.
*Reveal:* "Agent-triggered — exactly what tools are for: big corpus, rare need, and the
model knows its own question."

**Q5.3 write_conversational_memory → deterministic.** The Round-2/3 argument: model-
discretion writes rot silently.

**Q5.4 write_tool_log → deterministic.** An audit trail that depends on the audited
party's judgment is not an audit trail. (If this one lands well, point at the optional
stretch in build.md — after the demo.)

**Q5.5 write_entity → contested.** Deterministic pipeline: consistent coverage, pays
extraction cost every turn, stores junk too. Agent-triggered: model judges salience,
cheaper, misses silently.
*Reveal for a deterministic verdict:* "Defensible — your cost is a per-turn extraction
bill and a store that accumulates junk entities."
*Reveal for an agent-triggered verdict:* "Defensible — your cost is silent gaps: the
entities the model didn't find interesting are simply never there, and you learn it at
recall time."

**Q5.6 summarize_and_store → contested, with a twist.** The strongest answer separates
**who invokes** (code — every N turns / session end: deterministic trigger) from **who
does the work** (the model writes the summary). Classification is about the invocation
path. A learner who says "both" and explains that split has said the smartest thing in
the course — celebrate it.
*Reveal for deterministic:* "Defensible — you pay for summaries nobody may ever read,
on a schedule."
*Reveal for agent-triggered:* "Defensible — your cost is that a session which needed
summarizing may never get it, and nothing tells you."
*Either way, land the split:* invocation can be code even when the work is the model's.

## Gate criteria
1. Bootstrap in own words — the circularity of "model decides" for the first read.
2. Meta-lesson: per-operation, by invocation path + workload (frequency, size,
   safety-criticality) — never by the function's name or system ideology.

## Demo expectation (for the close)
After the pin: `--x5` → **5/5**; single-turn meter lands **between** the Round-1
baseline and the Round-2 preload. The trade-off was chosen, not stumbled into.
