# Round 2 — DEMO: safe every time — and the bill

> **MODE: DEMO** — tag replies `[R2 · DEMO]`. Prediction before every run; the learner
> runs the commands.

**Precondition:** `round-2 build` committed, verify passed.

## Step 1 — the fix, measured

- **Predict:** "Same snack question as Round 1. Two predictions: safe or not — and what
  does the meter's `in` do versus your baseline of ~24?"
- **Run:** `.venv/bin/python src/snackbot.py "I'm in Paris — suggest a quick sweet snack for me."`
- **Observe (shape):** a safe suggestion; `[meter]` roughly `in≈106` — about **4× your
  Round-1 baseline**.

## Step 2 — process death

- **Predict:** "This next command is a brand-new process. Will it know what you asked
  before?"
- **Run:** `.venv/bin/python src/snackbot.py "What did I ask you in our last session?"`
- **Observe (shape):** it recalls prior-session content — S2.3. Then run `ls -l memory.db`
  and ask: which of those two things survived the process? Note in passing: Step 1's turn
  was *saved* (S2.2) and is now part of what gets recalled.

## Step 3 — the failure axis

- **Predict:** "The next question needs no memory at all. Does the preload run anyway?
  What will the meter show?"
- **Run:** `.venv/bin/python src/snackbot.py "Is it raining in Paris right now?"`
- **Observe (shape):** full preload cost for zero benefit — same ~4× range.
  Deterministic fails on **cost, visibly, every turn**. The number may even have grown:
  every demo turn is saved and re-read. Memory systems contaminate their own
  measurements — hold that thought for Round 5.

## Step 4 — open floor  `[R2 · EXPAND]`

Questions about anything observed — why input tokens dominate cost, what's in the
preload, latency changes. Answer plainly. Done → record.

## Step 5 — record

```
## round 2 — YYYY-MM-DD
- snack question input tokens: <in>   (~<n>× my round-1 baseline)
- weather question input tokens: <in>
- new process recalled last session? <yes/no>
- note: <one line, own words — the failure axis>
```

`git add course/demo-log.md && git commit -m "round-2 demo"`
Close: "one sentence — what does deterministic buy, and what does it cost?"
