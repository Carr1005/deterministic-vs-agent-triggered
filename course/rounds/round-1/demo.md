# Round 1 — DEMO: watch it fail, with the meter running

> **MODE: DEMO** — tag replies `[R1 · DEMO]`. Prediction before every run; the learner
> runs the commands and reports what they see.

**Precondition:** `round-1 build` committed, verify passed.

## Step 1 — see what memory already holds

- **Predict:** "This database already held a previous session before you ever ran the
  bot — it shipped that way. What do you think is in there?"
- **Run:** `.venv/bin/python setup/show_memory.py`
- **Observe (shape):** prior-session rows — including the user saying they are
  **allergic to peanuts**. Land the point: the fact exists; storage is not the problem.

## Step 2 — the failure

- **Predict:** "The allergy is in the database. Will the snack suggestion respect it?"
- **Run:** `.venv/bin/python src/snackbot.py`
- **Observe (shape):** a suggestion — typically containing **peanuts**. If it happens to
  be safe, ask: "memory, or luck? how would you tell?" — either outcome teaches the
  same thing. Plus a `[meter]` line, roughly `in≈21 tok`.
  Land: **zero memory operations ran.** The database knew; nothing read it.

## Step 3 — open floor  `[R1 · EXPAND]`

Invite questions about anything observed — the meter line, the OpenAI call, the seeded
rows, tokens vs characters. Answer plainly and completely. Learner says done → record.

## Step 4 — record

Append to `course/demo-log.md`:

```
## round 1 — YYYY-MM-DD
- baseline input tokens: <in from your meter line>
- reply safe? <yes/no>
- note: <one line, own words — e.g. "fact was stored, nothing read it">
```

`git add course/demo-log.md && git commit -m "round-1 demo"`
Close: "one sentence — what did the meter just buy us for the rest of the course?"
