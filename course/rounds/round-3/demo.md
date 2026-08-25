# Round 3 — DEMO: sometimes it checks. sometimes it doesn't.

> **MODE: DEMO** — tag replies `[R3 · DEMO]`. Prediction before every run; the learner
> runs the commands.

**Precondition:** `round-3 build` committed, verify passed.

## Step 1 — three runs, same input

- **Predict:** "Same code, same question, three runs. Two predictions: will the model
  reach for memory — and where will the meter land against your Round-1 24 and Round-2 106?"
- **Run (three times):** `.venv/bin/python src/snackbot.py "I'm in Paris — suggest a quick sweet snack for me."`
- **Observe (shape):** `[tool]` lines on every run, and safe answers. Two things to say
  out loud:
  1. **the query is the model's own words.** It searched for something like *"user
     dietary restrictions allergies preferences"*; memory stores *"I'm allergic to
     almonds"*. No keyword in common — that is S3.3 working, and Q2's answer on screen.
  2. **the meter went up, not down** — roughly `in≈158`, *above* Round 2's ~106. A tool
     round-trip sends the schemas, then sends the results back: two calls where the
     preload made one. Agent-triggered is not automatically cheaper.
  Nothing here *guarantees* the read: the model could skip it and answer from priors. On
  this model it doesn't — which is why Round 4 counts rather than trusting three runs.

## Step 2 — the semantic gap, live

- **Predict:** "Ask about a financier — nothing in the name says almond. If the model
  checks memory, what phrase will *it* search for, and what phrase is actually stored?"
- **Run:** `.venv/bin/python src/snackbot.py "Is a financier a good snack for me?"`
- **Observe (shape):** **both** tools fire — `search_memory(...)` for the allergy and
  `search_knowledge_base('financier … ingredients allergens')` for what a financier is —
  and the reply is a flat *"No — not safe for you. Financiers are traditionally made with
  almond flour."* Neither store alone could answer that: memory knows the person, the
  knowledge base knows the pastry. No rule written in advance covers it.

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
