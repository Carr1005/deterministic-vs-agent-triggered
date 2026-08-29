# Round 1 — TUTOR: the failure, and the meter

> **MODE: TUTOR** — tag replies `[R1 · TUTOR]`. Interaction rules: `course/TUTORING.md`
> (read at phase entry — it is authoritative). Record accepted answers into `answers.md`
> as you go.

**Round goal:** know what a "memory operation" is, know the two ways one can come to
run — a fixed rule, or the model's choice — and understand why the *meter* must exist
before any memory design.

**Scene-set (say briefly before Q1):** the database shipped with a previous session
already in it — the almond allergy is *already stored*. Yet `src/snackbot.py` today is a
bare LLM call. This round we don't fix that; we name the problem and build the
instrument.
First run `bash tools/viewer/serve.sh --ensure`, then add one line: you can always
check localhost:4000/guide for a guide to the app as it stands — if the script printed a
different URL, give that one.

---

## Q1 — memory operations, and what makes one run  `type: single-answer`

**Beat 1 — the term (quick win, keep it light):**

**Ask:** "SnackBot's memory lives in a database. What can code do with it?"

- **rung 1:** "Think in verbs — data goes in, data comes out."
- **Accept if:** read and write (any phrasing: query/insert, get/put, load/save).
- On accept, name it: "Right — and every read or write is a **memory operation**.
  Now the real question…" → beat 2. No recording yet; Q1 records once, after beat 2.

**Beat 2 — what determines it runs:**

**Ask:** "This store is already full — run `.venv/bin/python setup/show_memory.py` and
see for yourself (or ask me to run it). Yet `src/snackbot.py` — 26 lines, open it — has
zero reads or writes: a setup script fired those writes, unconditionally, before you
arrived. In Round 2 we add the missing read, and one design question comes before any
code: on a given turn, what determines whether that read actually runs? There are
exactly two possible designs — what are they?"

- **rung 1:** "One design is already in front of you: the seed writes ran no matter
  what — nothing weighed anything. Say that as a rule for our read."
- **rung 2:** "That's one. In Round 3, the bot will sometimes search memory mid-answer
  and sometimes not, with no line of code forcing either. What's making that call?"
- Two misses → reveal (the **Reveal** block below) → blank-to-finish → record → move on.

**Model answer:**
Two designs: **it runs by a fixed rule** (every turn / on a schedule / on a predefined
condition — decided before the turn, regardless of model judgment), or **it runs at the
model's choice** (exposed as a tool; fires only when the model asks).
**Accept if:** both designs described, any phrasing — "it always runs / hard-coded /
every turn / by a fixed rule" vs "the model decides / only when it asks / it's a tool".
One described → the other rung. Mechanics alone ("SQL vs vector search") is a miss —
that's what an operation does, not what makes it run.
**On accept, name it — and defuse the it's-all-code muddle head-on:** "Right. The
course tags those `[deterministic]` — *code invokes it*, meaning a rule fixed before
the turn — and `[agent-triggered]` — *the model invokes it*, by choosing to call a
tool. And yes: even the tool call is *executed* by code. Everything is, in the end.
The classification is about where the **decision** comes from — a rule written in
advance, or the model's output at runtime."
**Reveal:** "There are only two designs: the read runs by a fixed rule — every turn, no
judgment — or it runs when the model chooses to call it as a tool. The course tags them
`[deterministic]` and `[agent-triggered]`. Finish this: a memory operation runs either
because ___ says so, fixed in advance — or because ___ chose to, mid-answer."

**Clause template (S1.1):**
> S1.1 — Every read or write SnackBot performs against its memory store is a *memory
> operation*. Each must be classified by who invokes it: `[deterministic]` (code
> invokes) or `[agent-triggered]` (model invokes). *(learner's phrasing: «…»)*

## Q2 — instrument before you optimize  `type: single-answer`

**Ask:** "Run `.venv/bin/python src/snackbot.py` and read everything it prints (or ask
me to run it). That turn just called a paid API — and nothing on screen tells you what it
cost. What does this app need *before* we add a single memory operation?"

- **rung 1:** "Round 2 will deliberately make every turn several times more expensive.
  If we did that today, what on this screen would even change?"
- **rung 2:** "Name the numbers an engineer would want printed after every turn of a
  paid API call."

**Model answer:**
Measurement of what each turn costs — tokens, cost, latency printed every time. (The
*why it comes first* is the gate's question, not this one: both memory styles fail on a
measurable axis — deterministic **fails on cost, visibly**; agent-triggered **fails on
reliability, silently** — and a trade-off you cannot measure is a trade-off you cannot
reason about.)
**Accept if:** any phrasing that means "measure / record what each turn costs" —
metrics, logging, instrumentation, cost tracking, telemetry, "print the token count".
**The word "meter" is never required or expected.** "To debug" is half credit → rung 2.
**On accept, name it:** "Right — logging what every turn costs. In your codebase you'd
file this under metrics or usage logging; here it's one small module the course calls
the **meter** — `src/meter.py`, printing a `[meter]` line after every turn. Today's bare
call becomes the baseline every later number is compared against."
**Reveal:** "This app needs its costs *measured* before anything starts changing them —
tokens, cost, latency, printed every turn. We build that this round as the **meter**.
Finish this: without that baseline, Round 2's five-times-more-expensive turn would look
like ___."

**Clause template (S1.2):**
> S1.2 — Every turn must report its own footprint: input tokens, output tokens,
> estimated cost, and latency, as a `[meter]` line. No memory change lands without the
> meter measuring it. *(learner's reason it comes first: «…»)*

---

## Gate

One question, one sentence, own words: **why does the meter get built before any memory
operation?** Criteria in the **Gate criteria** block below. Record the answer in
`answers.md`, then:
`git add course/rounds/round-1/answers.md && git commit -m "round-1 tutor"` → SPEC.

**Gate criteria:**
A measure-before-optimize reason, any phrasing: without a baseline, the coming
cost-vs-reliability trade-off is invisible — you can't compare what you can't measure.
(The who-invokes classification is already on record from Q1; do not re-quiz it.)
