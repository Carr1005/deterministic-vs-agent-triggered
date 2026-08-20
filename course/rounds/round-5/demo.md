# Round 5 — DEMO: the pin, measured — and the wrap-up

> **MODE: DEMO** — tag replies `[R5 · DEMO]`. Prediction before every run; the learner
> runs the commands.

**Precondition:** `round-5 build` committed, verify passed.

## Step 0 — reset (and know why)

- **Predict/ask:** "Rounds 2–4 have been *writing* every demo turn into memory, and the
  pinned preload reads that table. What would today's bloated table do to a measured
  trial?"
- **Run:** `.venv/bin/python setup/reset_memory.py`  (deletes `memory.db` and restores
  the shipped seed — instant, no API calls)
- Land: memory systems contaminate their own measurements. Clean fixture, then measure.

## Step 1 — the count

- **Predict:** "Round 4 you observed <their number>/5. With the pinned read: how many
  of five now?"
- **Run:** `.venv/bin/python src/snackbot.py --x5`
- **Observe (shape):** **5/5** — the pinned read is not a judgment call; it cannot be
  skipped.

## Step 2 — the cost

- **Predict:** "Where does the meter land — near your Round-1 ~21, your Round-2 ~118,
  or between?"
- **Run:** `.venv/bin/python src/snackbot.py "Suggest a quick snack for me."`
- **Observe (shape):** between the extremes — a pinned *small* preload plus tools only
  on demand. Read all three of the learner's own demo-log numbers out loud.

## Step 3 — open floor  `[R5 · EXPAND]`

Questions about anything across the whole course are fair game here. Answer plainly.
Done → record.

## Step 4 — record

```
## round 5 — YYYY-MM-DD
- after pin: <y>/5 safe (round 4 was: <x>/5)
- single-turn input tokens: <in>  (round 1: <a> · round 2: <b>)
- course, one sentence, own words: <…>
```

`git add course/demo-log.md && git commit -m "round-5 demo"`

## Wrap-up

Ask for their one-sentence version, then offer this shape to compare against:
**classify every memory operation by who invokes it; pin what must never fail; tool the
long tail; let the meter and the counter tell you whether you chose right.** Point back
at their own numbers as proof. Offer the optional stretch (build.md). Course DONE.
