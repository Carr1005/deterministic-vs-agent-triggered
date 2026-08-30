# Round 3 — DEMO: sometimes it checks. sometimes it doesn't.

> **MODE: DEMO** — tag replies `[R3 · DEMO]`. Prediction before every run; the learner
> runs the commands.

**Precondition:** `round-3 build` committed, verify passed.

## Step 1 — three runs, same input

- **Predict:** "Same code, same question, three runs. Two predictions: will all three
  reach for memory — and where will the meter land against your Round-1 24 and Round-2 106?"
- **Run (three times):** `.venv/bin/python src/snackbot.py "I'm in Paris — suggest a quick sweet snack for me."`
- **Observe (shape):** **the runs differ.** Two shapes to name out loud:
  1. **A run with `[tool]` lines** reads the allergy and answers safely — roughly
     `in≈142`, *above* Round 2's preload, because a tool round-trip is two calls where the
     preload was one. Look at the query it wrote: something like *"user dietary
     restrictions allergies"*, while memory stores *"I'm allergic to almonds"*. No keyword
     in common — S3.3 working, and Q2's answer on screen.
  2. **A run with no tool line at all** is the cheapest turn in the course so far —
     roughly `in≈52`, *below* Round 2's 106 — **and it recommends a macaron**, because it
     never learned about the allergy. Nothing crashed. Nothing warned.
  Say the pairing out loud: **the cheapest run is the dangerous one.** If all three happen
  to behave the same, note it honestly — Round 4 exists because three runs is not a
  measurement.

## Step 2 — the semantic gap, live

- **Point at the evidence — no guessing game.** Both phrases are already on the table:
  Q2 was exactly this pair, and Step 1 put it on screen — memory stores *"I'm allergic
  to almonds"*, and the model searches in words of its own. One line of recap, then the
  real question.
- **Predict:** "Ask about a financier — nothing in the name says almond. Memory knows
  the person, the knowledge base knows the pastry: can either store alone flag it? And
  if the model checks, what will it search for *this* time?"
- **Run:** `.venv/bin/python src/snackbot.py "Is a financier a good snack for me?"`
- **Observe (shape):** when the model does reach for them, **both** fire —
  `search_memory(...)` for the allergy and `search_knowledge_base('financier … ingredients
  allergens')` for what a financier is — and the reply is a flat *"No — not safe for you.
  Financiers are traditionally made with almond flour."* Neither store alone could answer
  that: memory knows the person, the knowledge base knows the pastry, and no rule written
  in advance covers the pair. When it *doesn't* reach for them, you get a cheerful yes.

## Step 3 — open floor  `[R3 · EXPAND]`

Questions about anything observed — tool traces, why runs differ, temperature/sampling,
embedding distances. Answer plainly. Done → record.

## Step 4 — record

```
## round 3 — YYYY-MM-DD
- run 1/2/3: tool called? <y/n/y> · safe? <y/y/n>
- cheapest turn input tokens: <in>  (compare: round-2 preload turn)
- note: <one line, own words — e.g. "cheapest run was the dangerous one">
```

`git add course/demo-log.md && git commit -m "round-3 demo"`
Close: "one sentence — what did Round 2 guarantee that this design only *hopes* for?"
