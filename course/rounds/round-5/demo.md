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
  skipped. Then read the `[meter]` lines *down the batch*: the first run sits near
  `in≈134` and the fifth is past `in≈1300`, climbing roughly **+300 tokens per turn**.
  Every turn's deterministic write becomes part of the next turn's pinned read. Round 2's
  write rule and this round's read pin are compounding in front of them — the one cost in
  this course that grows with use instead of staying flat.

## Step 2 — the cost

- **Predict:** "Round 3 gave you two numbers: `in≈52` when it skipped memory, `in≈142`
  when it checked. Round 2 was `in≈106`, safe every time. With the read pinned — where
  does a single turn land?"
- **Run:** `.venv/bin/python setup/reset_memory.py` — again, and not as decoration: they
  just watched the batch inflate its own input.
- **Run:** `.venv/bin/python src/snackbot.py "I'm walking down Rue Bonaparte in Saint-Germain — suggest a sweet to pick up nearby."`
- **Observe (shape):** **`in≈134`** — *above* Round 2's 106, because the memory-aware
  system prompt rides along on every turn; nearer `in≈240` if this turn also reached for a
  tool. Say the honest version out loud: **they did not buy a cheaper design.** They bought
  one whose failure mode they chose. And Round 3's `in≈52` was never purchasable — it was
  cheap only because it skipped the check. Read all three of their own demo-log numbers.

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

## Demo expectation (for the close)
After the pin: `--x5` → **5/5**, with the meter climbing across the batch as each write
feeds the next read. A single turn on a fresh reset lands `in≈134` — **above** Round 2's
106, not between it and the baseline. The trade-off was chosen, not stumbled into: the
cheap Round-3 turn was only ever cheap because it skipped the check.

## Wrap-up

Ask for their one-sentence version, then offer this shape to compare against:
**classify every memory operation by who invokes it; pin what must never fail; tool the
long tail; let the meter and the counter tell you whether you chose right.** Point back
at their own numbers as proof. Offer the optional stretch (build.md). Course DONE.
