# AUTHORING.md — how to write a question that survives a real learner

This file is the **question-writing standard** — for curriculum authors editing
`course/rounds/*/questions.md`, not for the tutor at runtime (the tutor's rules live in
`course/TUTORING.md`). Every rule below was earned the hard way: each one names a wording
failure that a real learner actually hit, with the bad and the fixed version side by side.

Check every drafted Ask, rung, Accept-if and Reveal against all eight before it ships.

## 1. Plain developer speech

If you wouldn't say the word to a colleague at a whiteboard, it doesn't go in a question.
No methodology or academic vocabulary.

> ✗ "To even discuss the fix we need a **unit of analysis**."
> ✓ (deleted — the question didn't need a meta-term at all)

## 2. Produce, don't pick

Never end an Ask with an either/or whose correct option *is* the answer — the learner can
pass by echoing option B without reasoning. The learner must generate the substance.

> ✗ "…which property carries the weight: *what it does* — or *what makes it run at all?*"
> ✓ "…on a given turn, what determines whether that read actually runs? There are
>   exactly two possible designs — what are they?"

## 3. Substance first, term second

The learner produces the idea in their own words; the tutor then attaches the course
term. Never ask a question *about the course's own framing* — a "question about a
question" is meta-shaped and reads as a riddle in dialogue, even when the same sentence
works fine in one-way narration.

> ✗ "…and what **single question classifies** every one of them?"
>   (the half that broke in every trial: "I don't understand your second question")
> ✓ learner says "the code, or the model" → tutor: "that's the classification the course
>   runs on — **who invokes it**: `[deterministic]` / `[agent-triggered]`."

The same rule covers **course-brand words** — *meter*, *rung*, *clause*: never expect the
learner to produce one (no developer says "we need a meter"; they say metrics, logging,
cost tracking). Accept their word, then attach the course's — and when attaching, bridge
to the industry term so the learner leaves with both:

> ✓ "In your codebase you'd file this under metrics or usage logging; here it's one
>   small module the course calls the **meter**."

## 4. Match effort to difficulty

A question developers answer instantly gets one plain line — no evidence scaffolding, no
puzzle dressing. Spend the anchoring on the question that carries the lesson.

> ✗ "Two facts sit on your disk. Fact one: … Fact two: … In plain verbs, what happened
>   in fact one, and what's missing in fact two?"
> ✓ "SnackBot's memory lives in a database. What can code do with it?"

## 5. The framing must not fight the answer

Check every noun in the Ask against the expected answer. A framing that pre-satisfies
half the answer biases the learner away from the other half.

> ✗ "…the only two things any program can do with a **stored pile of facts**?"
>   (already *stored* → the learner has no reason to say "write")
> ✓ "…What can code do with it?" (neutral: read and write are equally live)

## 6. Never enumerate the answer inside the Ask

If the Ask lists the pieces, the rung that asks for them is dead on arrival and the
answer is half-given.

> ✗ Ask: "…nothing tells you what it cost: **no tokens, no dollars, no seconds**."
>   rung 2: "Name the numbers an engineer would want printed." (already named!)
> ✓ Ask: "…nothing on screen tells you what it cost." — the enumeration is the
>   learner's to produce at the rung, or the reveal's to give.

## 7. Never cite the video; share its terms only

"The video said…" points at an experience the learner may not have had — the course never
assumes the video was watched, only that its *terms* are the course's terms (memory
operation · who invokes it · code invokes it / the model invokes it · deterministic /
agent-triggered · fails on cost, visibly / fails on reliability, silently). Alignment is
at the term level: never mirror the narration's sentence shapes — narration explains
forward, dialogue extracts. The video is a regenerable prototype
(`make_video.py` rebuilds it from the VTT): better phrasing found here is candidate
feedback *to* the video, never a constraint *from* it.

> ✗ "**The video called** a memory operation any read or write…"
> ✓ the same fact, stated as course ground truth or produced by the learner

## 8. A question slot may run as beats

"One answerable thing per Ask" does not mean one Ask per question slot. When a clause
needs two halves (S1.1 needs the definition *and* the classification), run the slot as
sequential **beats**: each beat is one Ask with its own single Accept-if; accept each
beat on its own; record once, at the end of the slot, into the question's single
`answers.md` entry. Never one compound Ask, and never compound Accept-if criteria —
"X AND Y" criteria force the tutor to chase a correct answer's missing half, which is
how rounds drag.

> ✗ "What counts as a memory operation, **and** what single question classifies them?"
>   with Accept-if: "reads-and-writes AND the classification located in…"
> ✓ beat 1: the term (one line, one accept) → beat 2: who invokes (one Ask, one accept)

---

**The test before shipping any question:** could the learner answer it from what's on
screen, in one short sentence, without knowing this course's internal vocabulary? Would
a bored senior engineer find it quick-but-fair rather than riddle-like? If either answer
is no, it fails one of the eight — find which.
