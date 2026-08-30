# Round 1 — DEMO: watch it fail, with the meter running

> **MODE: DEMO** — tag replies `[R1 · DEMO]`. Prediction before every run; the learner
> runs the commands and reports what they see.

**Precondition:** `round-1 build` committed, verify passed.

## Step 1 — the failure

- **Point at the evidence — no guessing game.** The learner has already seen what memory
  holds: they ran `.venv/bin/python setup/show_memory.py` during tutoring, and the guide
  page's *What the memory holds* shows it live — prior-session rows where the user says
  they are **allergic to almonds**, and knowledge-base rows that say which pastries
  contain almonds. One line of recap, not a quiz: the facts exist; storage is not the
  problem.
- **Predict:** "The allergy is in the database. Will the snack suggestion respect it?"
- **Run:** `.venv/bin/python src/snackbot.py`
- **Observe (shape):** a suggestion — typically including a **macaron**, which is made of
  almond flour. If it happens to
  be safe, ask: "memory, or luck? how would you tell?" — either outcome teaches the
  same thing. Plus a `[meter]` line, roughly `in≈24 tok`.
  Land: **zero memory operations ran.** The database knew; nothing read it.

## Step 2 — open floor  `[R1 · EXPAND]`

Invite questions about anything observed — the meter line, the OpenAI call, the seeded
rows, tokens vs characters. Answer plainly and completely. Learner says done → record.

## Step 3 — record

Append to `course/demo-log.md`:

```
## round 1 — YYYY-MM-DD
- baseline input tokens: <in from your meter line>
- reply safe? <yes/no>
- note: <one line, own words — e.g. "fact was stored, nothing read it">
```

`git add course/demo-log.md && git commit -m "round-1 demo"`
Close: "one sentence — what did the meter just buy us for the rest of the course?"
