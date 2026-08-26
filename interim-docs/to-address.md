# to-address.md — known risks & open work (course developer notes)

Not learner content. Items land here when flagged in design review; remove when resolved.

## Resolved in this version
- **Oracle dropped.** Audit found no Oracle API that makes deterministic-vs-agent-triggered
  easier to see: the classification is a property of *application control flow* (which line
  of Python fires the call), and no database feature exposes it. Storage is now one SQLite
  file; embeddings come from the OpenAI API. Removed: Docker, ~4 GB image, `sqlplus` user
  creation, the 420 MB local embedding model, torch, `langchain-*`, `oracledb`.
  Dependencies are now `openai` + `tiktoken`. Setup is ~2 minutes on any OS.
- **Setup attrition** (was item 1): `setup/check.sh` verifies key, packages, seeded rows,
  and one live API call. SETUP.md is 6 short steps with no platform-specific risk.
- **Pedagogical gain from the swap:** R3's semantic search is now eight readable lines
  (`embed` + `cosine` + `semantic_search`) instead of an opaque `similarity_search` call,
  so "matches by meaning, not keywords" is something the learner can *read*. R2's
  process-death test gained `ls -l memory.db` — the surviving artifact is visible.
- **Duplicability, and setup reduced to one step.** A clone arrives with the seeded
  database already committed at `setup/fixtures/memory-seed.db`, and needs no baseline
  commit: the resume rule is "no `round-N` commit in the log means the course has not
  started", so any repo history works and neither seeding nor git init is a learner step.
  What remains is `setup/bootstrap.sh` — python → `.venv` → packages → key → copy the
  seed → check — plus the irreducible `export OPENAI_API_KEY`. `setup/init.sh` survives
  as the fallback for channels where git does not travel (zip, folder copy, template);
  the clone case previously dead-ended, since the old script exited early whenever `.git`
  already existed. All course commands are pinned to `.venv/bin/python`, so the same
  string works in the learner's terminal and in an agent's non-persistent bash shell.
  `setup/pristine.sh` proves a copy is unstarted before it is shared.
- **A live diff viewer, verified end to end.** `tools/diffview` serves every round's spec
  and code change at `localhost:4000`, read from the learner's own git history, with
  unified and side-by-side views. Both views are rendered from the same text so they
  cannot drift. It writes nothing into the repo — `git status --porcelain` is the tutor's
  resume signal, and neither SPEC nor BUILD has a scoped `git add` anywhere. Its git calls
  are hermetic (`-c color.ui=false`, `--no-ext-diff`), tested against a repo with
  `color.ui=always`, `diff.external`, `GIT_EXTERNAL_DIFF`, `GIT_CONFIG_*` injection and a
  bogus `GIT_DIR` set at once. **The tutor's rule was also confirmed live**: it offered the
  link at a diff dialogue in a real session.
- **Two-branch publishing.** `main` is authoring history and is never rewritten;
  `release` is one squashed commit, rebuilt per share by `tools/release.sh` and set as
  GitHub's default branch. See `interim-docs/CONTRIBUTING.md`.
- **One instruction file, vendor-neutral.** `AGENTS.md` holds every rule. `CLAUDE.md` is
  one line (`@AGENTS.md`), `.gemini/settings.json` and `.aider.conf.yml` are equivalent
  one-line pointers; Codex, Cursor, Cline, Windsurf, Zed and Copilot read `AGENTS.md`
  unaided. No pointer contains a rule, so none can drift. The universal boot line —
  "Read AGENTS.md and start the course" — names only the neutral file and works anywhere.

## Open

### 1. Demo punchlines are probabilistic — R1 measured and fixed; R3/R4 still open
**R1: resolved.** The old question `"Suggest a quick snack for me."` scored 10/10 unsafe on
`gpt-5-mini`, but only because peanut butter happened to be that model's modal answer —
a coincidence that any model update could erase. Measured alternatives, 10 runs each:

| input | allergen item in the reply |
|---|---|
| `"I'm in Paris — suggest a quick snack for me."` | 6/10 |
| **`"I'm in Paris — suggest a quick sweet snack for me."`** | **10/10** ← adopted |
| `"I'm in Paris — suggest a quick pastry for me."` | 0/10 (collapses to croissant) |
| `"I'm in Lisbon — …"` (pastel de nata / egg) | 8/8 |
| `"I'm in Istanbul — …"` (simit / sesame) | 8/8 |

Paris/almond/macaron won because the allergen is **hidden**: "almond" appeared in only
1/10 replies, so the knowledge base is required to detect the danger — where "peanut
butter" and "sesame-crusted simit" name themselves and leave the KB decorative.

**R3/R4: both resolved, by two measurements.**
- **Tool-call drought — fixed at the prompt level.** `gpt-5-mini` called `search_memory`
  **0 of 20 times** while the system prompt said nothing about memory. Adding one sentence
  ("You have memory of past conversations… You may consult them if useful") took it to
  **19 of 30**, and an *earlier, stronger* wording ("consult them when they would make your
  answer more accurate") pinned it at 10/10 — too reliable to leave R4 anything to count.
  The committed prompt is the weaker one. So the rate is **not** binary, as this file
  previously recorded: 63% is a genuine middle, and R3's "runs differ" holds — with the
  caveat that R3's *three* runs come out uniform `0.63³ + 0.37³ ≈ 30%` of the time.
- **The `allerg` signal was inert — replaced by `almond`.** Confirmed at 30 runs: `allerg`
  appeared in **30/30** replies, including all 11 that recommended a macaron, because the
  bot offers "any allergies?" in the same breath. `--x5` could only ever print 5/5.
  `macaron` scores identically (19/30 — it is present in safe and unsafe replies alike).
  `almond` scores **28/30** and is present in 21/30, so `--x5` prints 3–4 of 5, and R5's
  pinned read measured **10/10**, preserving R5's 5/5 and the R4→R5 comparison. Ground
  truth was hand-adjudicated and corroborated: `avoid` is present in exactly the 19 safe
  runs and absent from all 11 dangerous ones.
- [x] Fix the drought at the prompt level.
- [x] Redesign R4's Q2 and the S4.2 signal around what the model actually writes.
- [x] Q1 split into two beats, each with one Accept-if, and its premise replaced with
      Round 3's *design* ("the read happens only if the model decides to call the tool"),
      which is true whatever the learner's three runs did.
- [x] The Gate keeps both restatements but adopts Round 5's declared format — numbered,
      one criterion each — and gains the anti-drag guard the other four gates all had and
      R4 alone lacked ("accept the first recognisable version of each, one rung max").
- [x] S4.1 no longer names the criterion: it counts "the replies the signal marks safe"
      and leaves the signal to S4.2, and `run_n` now prints `N/5 replies contained
      'almond'` — the output names its own test instead of claiming the reply
      acknowledged anything. R4's demo also gained the missing caveat: a SAFE verdict is
      not proof, since ~2 runs in 30 score SAFE without ever consulting memory.
- **R4 is closed.**
- [x] **R5's cost story was false by construction, not by contamination.** Step 2 asked
      "near ~24, near ~106, or between?" and answered "between". But
      `round-2/reference/snackbot.py:47,51` and `round-5/reference/snackbot.py:109,113` are
      byte-identical — same `read_user_facts()`, same message composition — and both meters
      join the same messages. The only difference is the system prompt (R2 one sentence
      ~10 tok, R5 three ~45), so **R5 = R2 + ~35 tok before any tool result**. Measured on
      a fresh seed: `in=134` (no tool) / ~238 (with tools) against R2's 106. Step 2 now
      compares against Round 3's two numbers and says the true thing: the pin does not buy
      a cheaper design, and Round 3's `in≈52` was never purchasable because it was cheap
      only by skipping the check. Fixed as narrative, not design — see the next item.
- [x] **Step 2's reset moved.** Step 1's `--x5` writes 10 rows the pinned read then loads,
      so Step 2 printed `in≈1573`. It now resets immediately before measuring; measured
      134 → (batch climbs to 1729) → reset → 134, exactly reproducible.
- [x] **Step 1 gained the compounding cost**, which no round had ever mentioned: across a
      `--x5` batch the meter climbs ~**+300 tok per turn** (measured 470 → 799 → 1098 →
      1422 → 1729), because each turn's deterministic write becomes part of the next turn's
      pinned read. The only cost in the course that grows with use.
- [x] **R5's authoring gaps:** Q5.3 and Q5.4 gained the reveals the other four had; the six
      operations gained one authored Ask template in the group header (previously the tutor
      improvised all six of the course's central prompts); and Q5.6's orphaned Verdict
      block — stranded below a `---` while the text pointed "above" — was reunited with its
      question.
- **R5 is closed.**

**Two R5 findings recorded but deliberately not fixed:**
- **Q5.1's description does not match its code.** It says `read_user_facts` "loads the
  user's stored facts (allergies, preferences)"; the function does
  `SELECT role, content FROM CONVERSATIONAL_MEMORY` — the entire transcript, assistant
  turns included. Narrowing it would make the preload genuinely "small" and would let the
  old "between the extremes" claim stand, but `read_user_facts` is shared with Round 2, so
  R2's documented `in≈106` and its "about 4× your baseline" claim would both move, and
  BUILD's payoff line ("two lines, exactly where the learner's own Q5.1 verdict put them")
  would stop being true. Not worth a cascade into a closed round.
- **The compounding cost has no ceiling.** Nothing truncates the pinned read, so a long
  session's preload grows without bound. Out of scope for a five-round course, but it is
  the obvious next design question and Q5.6's summarize-and-store is where it belongs.

### 2. Drift repair path (partially addressed — monitor in trials)
Mode tags on every reply, re-anchor after compaction / ~15 turns, learner levers
("explain" / "stop telling, ask me" / "just tell me"). The learner is the detector.
- [ ] If trials show drift anyway: add a post-round self-audit, or escalate to per-turn
      re-injection of the phase file (token cost).

### 3. Setup verified live; the five-round course trial is still outstanding
**Verified against the real stack**, in throwaway copies of all four distribution
channels: `bootstrap.sh` end to end (venv, packages, seed of 5/5/7 rows, one live API
call), `init.sh` on clone / template / zip / folder-copy, idempotent re-runs, the
missing-key path exiting before it spends or commits, the carried-over-database guard,
the mid-course guard that must *not* re-seed, all five `verify.sh` passing against their
references, and one live baseline turn.

**Not yet done:** nobody has played the course itself — five rounds of TUTOR → SPEC →
BUILD → DEMO with a live tutor. That is the remaining unknown, and it is the part the
format is judged on.
- [ ] One developer completes all five rounds in a fresh copy, start to finish.
- [ ] Confirm embedding dimensions/pricing assumptions and the `[meter]` numbers in
      README's round table (baseline ~21 / preload ~118) against that run.

### 4. Onboarding friction is the top risk to a format evaluation
Anyone assessing the *format* meets the setup first, so friction there gets scored as a
verdict on the format. Largely addressed: one command, `bash setup/bootstrap.sh`, and a
tutor that offers to run it on first contact. The irreducible step is an
`OPENAI_API_KEY` exported in the terminal the agent is launched from.
- [ ] Consider `interim-docs/FORMAT-WALKTHROUGH.md`: the four-phase loop shown with real
      captured outputs, so a reviewer can judge the pattern in two minutes without any
      setup. (Real-stack stays the only *course* path — a faked demo can't teach a
      measured lesson.)

### 5. Round 5 optional stretch
`write_tool_log` build is offered but unverified by verify.sh. Decide: add a check, or keep
free-form (currently free-form, committed as `round-5 learner-edit`).

### 6. For the future course-generator guidance doc
- Question-group pacing cap: groups >6 sub-questions should split across phases or rounds
  (R5's six is the tested ceiling).
- Per-question knob is `type: single-answer | judgment` (+ `contested`); rounds are never
  special-cased.
- Rung rule: every rung is a question or an observation; declaration only at reveal.
- Prefer "go measure it" rungs wherever the running app can supply evidence — the
  structural advantage of this format over chat-only tutors.
- Infrastructure earns its place only if it makes the *concept* easier to see. The Oracle
  audit above is the worked example: real stack, zero conceptual contribution, high setup
  cost → replaced with the smallest thing that keeps the lesson honest.

### 7. Vendor sub-agent adapters (progressive enhancement, post-validation only)
Instruction-file pointers are done (see "Resolved" above) — this item is now only about
**sub-agents**: an optional `.claude/agents/` read-only verifier, a Codex `.codex/agents/`
equivalent, Cline Plan/Act mapping. Only after the single-agent flow is validated by the
five-round trial — sub-agents must never carry the interactive tutoring dialogue (they
cannot ask the learner questions).
