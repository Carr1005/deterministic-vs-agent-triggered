# AUTHORING.md — how to write a question that survives a real learner

This file is the **question-writing standard** — for curriculum authors editing
`course/rounds/*/questions.md`, not for the tutor at runtime (the tutor's rules live in
`course/TUTORING.md`). Every rule below was earned the hard way: each one names a wording
failure that a real learner actually hit, with the bad and the fixed version side by side.

Check every drafted Ask, rung, Accept-if and Reveal against all of them before it ships.

**Before you draft anything, finish the audit.** Read the round's every demo `Predict`
step, every naming step in its other questions, the gate of the round *after* this one
(it may depend on this round's output), and the clause the question must fill. Most bad
drafts are not bad writing — they are questions that duplicate a demo step, re-collect a
recorded answer, or fill a clause that already has its content. You cannot see any of
that from the question alone.

## 1. Plain developer speech

If you wouldn't say the word to a colleague at a whiteboard, it doesn't go in a question.
No methodology or academic vocabulary.

> ✗ "To even discuss the fix we need a **unit of analysis**."
> ✓ (deleted — the question didn't need a meta-term at all)

**Write questions as speech, not prose.** Short sentences, one clause each. The question
itself is the *last* sentence, kept short, with its subject named — never "each", "that
one", or a pronoun whose referent sits two sentences back. Read every Ask aloud once: if
you would rephrase it while saying it, it fails.

> ✗ "Where does each live, that one dies and the other doesn't?"
> ✓ "Where do a program's variables live while it runs?"

**Match the question word to the answer's category.** "Who" requests a person, so a
"who" question about a system component invites "me" or "the user". Ask "what part of
this system…" when the answer is a component.

> ✗ "Who could have known that read was pointless?"   (a learner can answer "I did")
> ✓ "What part of this system is reading the question when that read fires?"

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

And **never coin a term.** The naming step attaches names that already exist — a course
term or an industry term. A word invented while drafting is worse than jargon, because
nobody can look it up.

> ✗ "…no rule can preload the right **world-fact** for every question."  (invented here)
> ✓ "…facts about the user come from one store, facts about snacks from the other."

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

The same rule bans **fake anchors**: "on screen" / "in front of you" only when something
actually is. In a hypothetical, ask about the signal, not an imaginary display:

> ✗ "…and it misjudges one save a week. What appears on screen?"  (there is no screen)
> ✓ "…and it misjudges one save a week. What breaks?"

## 6. Never enumerate the answer inside the Ask

If the Ask lists the pieces, the rung that asks for them is dead on arrival and the
answer is half-given.

> ✗ Ask: "…nothing tells you what it cost: **no tokens, no dollars, no seconds**."
>   rung 2: "Name the numbers an engineer would want printed." (already named!)
> ✓ Ask: "…nothing on screen tells you what it cost." — the enumeration is the
>   learner's to produce at the rung, or the reveal's to give.

**Circularity is the same defect wearing a question mark.** If the answer is the Ask's
own words rearranged, nothing is produced. Test it by trying to answer using only words
already in the question.

> ✗ "Why doesn't flipping the reads force the writes to flip too?"
>   → "because they're independent decisions" — the question said it first
> ✓ ask for a consequence the learner has to work out, and let the principle be the
>   thing you attach afterwards

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

## 9. Ask what *is*, not what *isn't*

Absence questions — "what's missing", "what can't it do", "what must it survive" — force
an unbounded search: imagine everything that could be absent, then guess which gap the
author meant. Two of this course's worst questions had exactly this shape. Rewrite as a
positive question about what something *does*, or about which part does it.

> ✗ "What must the stored conversation survive?"
> ✗ "What can't Round 2's design answer here?"
> ✓ "Where do a program's variables live, and where does `memory.db` live?"

## 10. The expected answer must be the only good answer

Before shipping, write down three answers a sharp learner might actually give. If a
*good* one fails your Accept-if, the question is broken — not the learner. This is the
most common way a question that reads fine on paper collapses in a session.

> ✗ "When do you finally find out?" — with criteria accepting only "at recall time".
>   The best answer is **"maybe never"**, and it would have been scored a miss.
> ✗ "Code, or the model?" — a sharp learner answers **"it's all code in the end"**, and
>   they are right; the question had to be rebuilt around *what decides*, not who runs.

## 11. The naming step must pay its way

After accepting, say something the learner did not just say: the consequence, the cost,
the failure it prevents, or where this returns later in the course. Announcing that an
answer was important is applause, not teaching.

> ✗ "That's the course's real thesis showing up three rounds early."
> ✓ "…and this is worse than the Round 2 version: there, a skipped write left your
>   preload thin; here the model asks, hears silence, and treats silence as an answer."

---

**The test before shipping any question**, in order:

1. **Is it already answered?** Does a recorded answer, a naming step, or a demo step
   already cover it? If so, state it — don't ask it.
2. **Does the clause it fills still need content?** A clause whose body says "unchanged
   from …" usually does not.
3. **Three sharp answers.** Write them down. Do they all pass your Accept-if?
4. **Read the Ask aloud.** Would you rephrase it while speaking? Then rewrite it.
5. **Answer it using only the question's own words.** If you can, it is circular.
6. **Does the naming step add anything** beyond "that was important"?

Could a bored senior engineer answer it in one short sentence, from what's in front of
them, without knowing this course's internal vocabulary — and feel it was quick and fair
rather than a riddle? If not, it fails one of the rules above. Find which.
