# Round 3 — BUILD brief

> **MODE: BUILD** — tag replies `[R3 · BUILD]`. Only `src/snackbot.py` changes; patch
> toward `reference/`; verify before commit.

**Precondition:** `round-3 spec` committed (S3.1–S3.3).

**Implements:** S3.1 (preload out; two search tools + tool-call loop in), S3.2 (writes
untouched), S3.3 (vector search via the course embedding model).

**Change:** patch toward `reference/snackbot.py`:
- remove the `user_facts` preload from the prompt (the `read_user_facts` *definition*
  stays — it returns in Round 5);
- add the semantic layer (`embed`, `cosine`, `semantic_search`) and the two tools
  (`search_memory`, `search_knowledge_base`);
- add the tool-call loop in `run_turn`;
- `save_turn` calls stay exactly where they are (S3.2).
Keep the `# S3.x` comments as in the reference.

**Scope:** only `src/snackbot.py`; the course's biggest diff (~110 lines) — plan to walk
it in three chunks, one per clause.

**Then:** `bash course/rounds/round-3/verify.sh` → commit `round-3 build` → **diff
dialogue** `[R3 · EXPAND]`: show `git diff HEAD~1 -- src/` in three chunks — red preload
= S3.1's deletion half; green TOOLS + loop = S3.1's addition half; the *untouched*
`save_turn` lines = S3.2 (what did NOT change is a clause too); embedder = S3.3. Then
invite questions (tool schemas, the loop, what an embedding is, why cosine) and answer
plainly — the similarity function is eight readable lines, so read it together.
Done → DEMO.
