# Round 5 — BUILD brief

> **MODE: BUILD** — tag replies `[R5 · BUILD]`. Only `src/snackbot.py` changes; patch
> toward `reference/`; verify before commit.

**Precondition:** `round-5 spec` committed (decision card + S5.1 + S5.2).

**Implements:** S5.1 — pin exactly one read. Deliberately the **smallest diff of the
course**: two changed lines plus a comment.

**Change:** patch toward `reference/snackbot.py`:
- in `run_turn`, call `user_facts = read_user_facts()` before composing messages (the
  function has sat unused since Round 3 — it returns);
- include `user_facts` in the user message content;
- both search tools and all `save_turn` calls remain exactly as they are.
Keep the `# S5.1` comment.

**Scope:** only `src/snackbot.py`; a diff beyond ~5 lines means drift.

**Then:** `bash course/rounds/round-5/verify.sh` → commit `round-5 build` → **diff
dialogue** `[R5 · EXPAND]`: show `git diff HEAD~1 -- src/` and let the smallness land —
five rounds of argument, two lines of code, sitting exactly where the learner's own
Q5.1 verdict put them. Invite questions, answer plainly. Done → DEMO.

## Optional stretch (offer only after the demo, if the learner asks)

Implement their Q5.4 verdict, `write_tool_log`: inside the tool-call loop, append one
line per invocation (tool name, query, timestamp) to a table or local file —
deterministically, in code, never by asking the model to log itself. Not covered by
verify.sh; commit as `round-5 learner-edit` if kept.
