# Round 4 — DEMO: count it

> **MODE: DEMO** — tag replies `[R4 · DEMO]`. Prediction before every run; the learner
> runs the commands.

**Precondition:** `round-4 build` committed, verify passed.

## Step 1 — commit to a number

- **Predict:** "Five runs of the snack question. Write the number down before you run:
  how many of five will acknowledge the allergy?"
- **Run:** `.venv/bin/python src/snackbot.py --x5`
- **Observe (shape):** per-run SAFE/UNSAFE lines and a final count — typically **2–4 of
  5**, but *any* honest count is data. Two things to say out loud:
  1. the UNSAFE runs did not crash, log, or warn — the failure is **silent**;
  2. their number vs their prediction.

## Step 2 — only if you rolled 5/5

- "Does 5/5 overturn Round 3?" — run `--x5` once more. The point isn't forcing a
  failure; it's that one batch is also a sample. 5/5 twice → record both, move on;
  Round 5's comparison still stands, from a clean reset.

## Step 3 — open floor  `[R4 · EXPAND]`

Questions about anything observed — the distribution, sampling, why counts differ
between batches. Answer plainly. Done → record.

## Step 4 — record

```
## round 4 — YYYY-MM-DD
- prediction: <x>/5 · observed: <y>/5  (second batch, if run: <z>/5)
- note: <one line, own words — the failure axis of agent-triggered>
```

`git add course/demo-log.md && git commit -m "round-4 demo"`
Close: "one sentence — Round 2 failed on ____, visibly; this design fails on ____,
silently." Then: Round 5 decides *per operation* — and fixes this without giving back
all of Round 2's cost.
