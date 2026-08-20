# Round 3 — DEMO: sometimes it checks. sometimes it doesn't.

> **MODE: DEMO** — tag replies `[R3 · DEMO]`. Prediction before every run; the learner
> runs the commands.

**Precondition:** `round-3 build` committed, verify passed.

## Step 1 — three runs, same input

- **Predict:** "Same code, same question, three runs. Will the three transcripts match?
  Will the model call a memory tool every time?"
- **Run (three times):** `.venv/bin/python src/snackbot.py "Suggest a quick snack for me."`
- **Observe (shape):** runs differ. Some show `[tool] search_memory(...)` and answer
  safely; a run may show **no tool line at all** — and that run is both the **cheapest**
  on the meter *and* the one that can recommend peanuts. If all three behave the same,
  note it honestly — Round 4 exists because three runs is not a measurement.

## Step 2 — the semantic gap, live

- **Predict:** "Ask about trail mix. If the model checks memory, what phrase will *it*
  search for — and what phrase is actually stored?"
- **Run:** `.venv/bin/python src/snackbot.py "Is trail mix a good snack for me?"`
- **Observe (shape):** the `[tool]` line shows the *model's* wording (dietary
  restrictions / allergies) yet surfaces the stored 'allergic to peanuts' — S3.3
  working. Trail mix may compose **both** tools (memory: allergy; knowledge base: trail
  mix contains peanuts).

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
