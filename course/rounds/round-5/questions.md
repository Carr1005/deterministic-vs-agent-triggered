# Round 5 — TUTOR: decide per operation

> **MODE: TUTOR** — tag replies `[R5 · TUTOR]`. One question per turn; end every turn
> with a question. Rungs are questions or observations only; declarative answers exist
> only in the reveal. Record each verdict + reason into `answers.md` as you go.

**Round goal:** the course's actual skill — classify each memory operation **on its
own**, by invocation path and workload, not by system-wide ideology. Then apply it: pin
exactly one read, keep the rest as tools, measure the result.

**This round's questions form one group (Q5.1–Q5.6):** six real operations from a
production memory manager, sharing one output artifact (the decision card) and one
gate. All six are `type: judgment` — the learner must commit to a **verdict and a
one-line reason before you respond to either**. Q5.5 and Q5.6 are `contested`: any
verdict passes with a coherent reason, and your reveal must name what their chosen side
*costs*.

**Shared rungs** (use when the verdict comes without a reason, or the reason doesn't
hold; probe the reason, never the verdict):
- **rung 1 (workload):** "Two numbers first: how often must this run, and how big is
  what it touches? Do your numbers support your verdict?"
- **rung 2 (bad day):** "Give your choice a bad day — the model misjudges, or the bill
  arrives. What breaks, who notices, and when?"

---

## The six operations — one at a time, verdict + reason first

**Q5.1 — `read_user_facts`** — load the user's stored facts (allergies, preferences) at
the start of a turn.
- Follow-up probe, whichever way they answer: "Before the *first* read has happened,
  what does the model know about what memory contains? Can a judgment call be made from
  zero information?" (the bootstrap argument)

**Q5.2 — `search_memory`** — recall arbitrary past-conversation content (the long tail).

**Q5.3 — `write_conversational_memory`** — persist each turn.

**Q5.4 — `write_tool_log`** — record every tool invocation the model makes.

**Q5.5 — `write_entity`** *(contested)* — extract entities/facts from the conversation
and store them.

**Q5.6 — `summarize_and_store`** *(contested)* — periodically summarize the session
into long-term memory.
- Extra probe if they hesitate: "Separate two things: who *invokes* the summary, and
  who *writes* it. Must they be the same party?"

Verdicts, acceptance, and reveal text (including the cost each contested side pays):
`tutor-notes.md`.

---

## Gate — two restatements, own words

1. Why at least one read must be deterministic **in principle** (the bootstrap
   argument).
2. The group's meta-lesson: classification belongs to the **invocation path and
   workload**, not the operation's name or the system's ideology.

Record both in `answers.md`, then:
`git add course/rounds/round-5/answers.md && git commit -m "round-5 tutor"` → SPEC.

## SPEC note

S5 gets the **decision card** — a six-row table straight from the learner's
`answers.md` (their verdicts, their reasons; contested rows keep *their* choice, marked
`contested`):

> | operation | verdict | reason (learner's words) | status |
> |---|---|---|---|

Then two clauses:

> S5.1 `[mixed]` — Exactly **one** read is pinned deterministic: the user-facts
> preload. Both searches remain agent-triggered tools. All writes remain deterministic.
>
> S5.2 — Bootstrap principle: at least one read must be deterministic, because the
> model cannot know what memory holds until memory tells it. *(learner: «…»)*
