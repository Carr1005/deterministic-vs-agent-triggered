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

### 1. Demo punchlines are probabilistic
R1 assumes an unsafe baseline reply; R4 assumes ~2–4/5 SAFE. Demos treat outputs as shapes
("any honest number is data"), but the narrative payoff needs failure to actually appear.
First live evidence, one run on `gpt-5-mini`: with the allergy seeded in the database, the
round-0 baseline answered "apple slices with **peanut butter**" — R1's punchline fires.
One data point, not a rate.
- [ ] Measure the R1 unsafe-reply rate over ~10 runs, and the R4 distribution.
- [ ] If the model is "too safe", strengthen the seeded phrasing or the demo question —
      not the prose.

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
