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
- **The tutor can point an open guide page at a section.** `tools/viewer/focus.py` writes
  a target to `$TMPDIR`; `/focus` reports it; a page that is on screen scrolls itself there
  within ~3s, opening the card first if it is collapsed. Per-round sub-anchors were added
  for it (`#rN-spec`, `#rN-app`, `#rN-runs`; only `#rN` existed). Verified end to end on a
  clean clone, plus 8 checks in a node harness: a pointer older than the tab is ignored, a
  newer one opens collapsed ancestors, the same pointer twice does not re-scroll, a
  cross-page target navigates, an unknown id is ignored quietly. It writes nothing into the
  repo — the pointer lives in `$TMPDIR`, keyed by a hash of the repo path the way
  `/healthz` reports it, so it cannot touch `git status --porcelain` and a trial clone
  cannot steer the original's tab. It is also absent from `signature()` on purpose, so a
  pointer never masquerades as a content change and forces a reload. **Known boundary:** a
  page cannot raise its own window, so this works when the page is visible — a second
  monitor, or side by side. A fully occluded window is reported `hidden` and its timers are
  throttled, so it catches up when next looked at rather than before.
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

## Closed 2026-08-31

- **Drift repair path** (was item 2). Shipped and standing: mode tags on every reply,
  re-anchor after compaction / ~15 turns, learner levers ("explain" / "stop telling, ask
  me" / "just tell me") — the learner is the detector. No trial has shown drift that the
  levers couldn't repair, so the escalations (post-round self-audit, per-turn phase-file
  re-injection) stay unbuilt. Reopen only if a live run drifts unrecoverably.
- **The five-round trial** (was item 3). Setup had already been verified live in all four
  distribution channels (bootstrap end to end, init.sh variants, idempotent re-runs, the
  guards, all five verify.sh, one live baseline turn). The remaining unknown — five rounds
  with a live tutor — now belongs to the sandbox model: learners run in fresh clones of
  `release`, one clone per run (`interim-docs/state-machine.md`), and those runs are the
  trial. Confirm the README `[meter]` numbers (baseline ~21 / preload ~118) against the
  first such run.
- **Onboarding friction** (was item 4). Addressed as far as it goes: one command
  (`bash setup/bootstrap.sh`), a tutor that runs setup itself on first contact, and the
  irreducible `export OPENAI_API_KEY`. The optional `FORMAT-WALKTHROUGH.md` is declined —
  the sandbox model gives a reviewer a real run instead of a captured one.
- **Round 5 optional stretch** (was item 5). Decided: `write_tool_log` stays free-form,
  committed as `round-5 learner-edit`, with no verify.sh check — the stretch is an
  invitation, not a gate.
- **Vendor sub-agent adapters** (was item 7). Declined. Instruction-file pointers (see
  "Resolved" above) are the whole vendor story; sub-agents must never carry the tutoring
  dialogue (they cannot ask the learner questions), and no validated need for a read-only
  verifier agent has appeared.

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

### 7. Nothing tells the tutor the page pointer exists

The mechanism shipped and works (see Resolved). What is missing is the caller:
**`COURSE.md` mentions `focus.py`, `viewer` and `:4000` zero times.** Measured in a real
Round-3 session (`/private/tmp/r3`): asked to point out Round 2 in the guide, the tutor
correctly cited `#r2`, `#r2-app` and `#r2-spec` and printed them as links, but `focus.py`
appears 0 times in that transcript, so the learner clicked. One line in `COURSE.md` closes
it — and that file is a cross-branch collision, so it wants its own small fast commit.

**Optional, for the occluded case:** a `focus.py --raise` would write the pointer, then use
AppleScript to *select the guide tab and activate Chrome* — no navigation, therefore no new
tab, and the tab becoming visible is itself what applies the pointer. `open <url>` is the
cross-platform fallback but reuses a tab only on an exact URL match, which cannot happen
while that tab is throttled, so it spawns tabs. Behind a flag either way: a tutor stealing
the window mid-conversation is worse than a click.

**Scope ceiling, which the pointer does not introduce.** The agent's shell and the browser
must be on one machine — already true of the whole viewer, since `localhost:4000` is
meaningless otherwise. Claude Code on the web or in a cloud sandbox cannot reach it; over
SSH the pointer lands on the wrong machine. `osascript` would narrow the raise further, to
macOS + Chrome. Worth weighing first: in VS Code or JetBrains the guide could open in the
IDE's built-in browser pane, as an editor tab beside the code — always visible, never
occluded, no window to raise.

**Smaller:** `focus.py --port` defaults to 4000, but `serve.sh` steps aside to 4001 when
4000 is taken (observed: :4000 the trial clone, :4001 the sandbox). The pointer is keyed by
repo path and each page polls its own origin, so the port affects only the health probe and
the printed URL — the message misleads, the behaviour is right. Probe a small range as
`serve.sh` already does.

### 8. `.gitignore`'s `.venv/` misses replay's symlink — every sandbox reads dirty

`replay.py` symlinks the source repo's `.venv` into the sandbox, so the entry is a
symlink, not a directory. `.gitignore:2` is `.venv/`, and a trailing slash matches a
*directory*; git treats a symlink as a file, so the pattern misses it and
`git status --porcelain` reports `?? .venv` for the life of the sandbox.

That is the tutor's mid-round resume signal (`course/PROTOCOL.md`) reading dirty in every
replay sandbox — precisely the state the signal exists to distinguish. Observed in
`/private/tmp/r3`. Pre-existing; unrelated to the viewer work that found it.

Fix: `.venv/` → `.venv` in `.gitignore`, which matches both, or have `replay.py` add the
line to the sandbox's `.git/info/exclude` instead. `.gitignore` is also a cross-branch
collision file, so land it small and fast.

## 2026-08-31 — rulebook renamed `AGENTS.md` → `COURSE.md`

The course now also deploys inside DeepLearning.AI's managed chat IDE, which writes its
own environment rules to `/workspace/AGENTS.md` on every container boot — anything the
course ships under that name is silently overwritten. The rulebook therefore moved to
`COURSE.md` (a name no platform reserves) and `AGENTS.md` became one more thin pointer,
joining `CLAUDE.md`, `.gemini/settings.json` and `.aider.conf.yml` — all of which now
route to `COURSE.md` directly. Earlier entries in this log that say `AGENTS.md` describe
the layout as it was then; they are left unrewritten. The universal boot line is now
"Read COURSE.md and start the course."
