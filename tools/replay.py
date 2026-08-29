#!/usr/bin/env python3
"""replay.py — AUTHOR TOOL. Stage a throwaway copy of this course at a chosen round.

Developing Round 4 — its questions, its build brief, its page on the viewer — normally
means playing Rounds 1-3 by hand first, with real API calls, every time. This builds a
disposable sandbox outside the repo, replays the course into it commit by commit, and
hands back a directory where the tutor resumes exactly where you want to work:

    python3 tools/replay.py --round 4            # tutor resumes at Round 4, first question
    python3 tools/replay.py --through "round-4 spec"   # any phase boundary, precisely
    python3 tools/replay.py --round 4 --mid-tutor      # …mid-round, answers.md uncommitted
    python3 tools/replay.py --round 4 --serve          # …and serve the viewer there

WHAT THIS IS NOT. A replayed sandbox is for development and review. It is **not** a
played course and is never evidence that the course works: no model is ever called, and
the answers are the course's own model-answer prose rather than a learner's words.
`interim-docs/to-address.md` still lists the five-round trial as outstanding, and this
tool cannot close it. Every commit it makes says so in its body.

Four rules it will not break:

  1. **It cannot stage into this repository.** Every git write goes through
     `git -C <sandbox>`; a target path inside the repo, or one carrying an `origin`
     remote, is refused. A `round-N` commit in real history would make the tutor resume
     mid-course and would poison any copy shared from it — the hazard
     `interim-docs/CONTRIBUTING.md` warns about.
  2. **It carries no course content of its own.** Every artifact it writes is extracted
     at run time from files already committed here — the per-round `reference/`
     snackbot, the clause templates and model answers in `questions.md`, the record
     template in `demo.md`. There is no second copy of the curriculum to drift.
  3. **It only reads this repo.** `git status --porcelain` here is the tutor's mid-round
     resume signal, so nothing is written inside the repo, ever.
  4. Standard library only, like the rest of `tools/`.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PHASES = ("tutor", "spec", "build", "demo")
ARTIFACT = {
    "tutor": "course/rounds/round-{n}/answers.md",
    "spec": "spec/spec.md",
    "build": "src/snackbot.py",
    "demo": "course/demo-log.md",
}
TRAILER = "Synthesized by tools/replay.py — not a played round."
PLACEHOLDER = "(not yet answered)"
REPLAY_NOTE = ("> Replayed by `tools/replay.py`: the course's own model-answer prose, "
               "not a learner's words.")


def git(cwd, *args, check=True):
    r = subprocess.run(("git", "-C", str(cwd)) + args,
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"FAIL  git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


# ------------------------------------------------------------------ extraction -------
# Everything below reads the SANDBOX's copy of the course files, so uncommitted edits
# you overlaid are what gets replayed.

def clause_blocks(questions_md):
    """Every `> S<n>.<m>` clause in a round's questions.md, with its continuation lines.

    Keyed on the blockquote itself, not on the `**Clause template**` label: S2.3, S3.2,
    S5.1 and S5.2 are bare quotes under `## SPEC note` and carry no label at all.
    """
    blocks, cur = [], None
    for ln in questions_md.splitlines():
        if re.match(r"^> S[1-5]\.", ln):
            if cur:
                blocks.append(cur)
            cur = [ln]
        elif cur is not None and ln.startswith(">"):
            cur.append(ln)
        elif cur is not None:
            blocks.append(cur)
            cur = None
    if cur:
        blocks.append(cur)
    return ["\n".join(b) for b in blocks]


def answer_blocks(questions_md):
    """The model answer / verdict / gate-criteria bodies, in document order."""
    starts = ("**Model answer:**", "**Verdict (model answer):**", "**Gate criteria:**")
    stops = ("**", "*Reveal", "## ", "---")
    out, lines = [], questions_md.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip() not in starts:
            continue
        body = []
        for nxt in lines[i + 1:]:
            if nxt.startswith(stops) or nxt.startswith("> "):
                break
            body.append(nxt)
        text = "\n".join(body).strip()
        if text:
            out.append(text)
    return out


def build_spec(scaffold, clauses_by_round, upto):
    """The 29-line scaffold with rounds 1..upto filled in under their headings."""
    out, lines, i = [], scaffold.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^## S([1-5]) — ", ln)
        out.append(ln)
        i += 1
        if not m:
            continue
        n = int(m.group(1))
        # skip the italic "(clauses arrive in Round N …)" placeholder, which spans one
        # line for S1-S4 and two for S5
        while i < len(lines) and lines[i].startswith("*("):
            while i < len(lines):
                done = lines[i].rstrip().endswith(")*")
                i += 1
                if done:
                    break
        if n <= upto and clauses_by_round.get(n):
            out.append("")
            out.append("\n\n".join(clauses_by_round[n]))
            if n == 5:
                out.append("")
                out.append("*(the Round 5 decision card is written from the learner's own "
                           "verdicts and is not replayed.)*")
        else:
            out.append(f"*(clauses arrive in Round {n} — written from your own answers)*")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def fill_answers(template, answers):
    """Replace each `(not yet answered)` with the k-th extracted block."""
    out, k = [], 0
    for ln in template.splitlines():
        if ln.strip() == PLACEHOLDER:
            if answers:
                # Rounds 4 and 5 have two gate restatement slots but one criteria block;
                # reusing the last block is closer to the truth than leaving it empty.
                out.append(answers[min(k, len(answers) - 1)])
            else:
                out.append("(replayed — no model answer is authored for this slot)")
            k += 1
        else:
            out.append(ln)
    text = "\n".join(out)
    # one visible note, right under the heading
    lines = text.splitlines()
    lines.insert(1, "\n" + REPLAY_NOTE)
    return "\n".join(lines).rstrip() + "\n"


def demo_entry(demo_md, n, when):
    """The round's own record template, with its placeholders filled from the same file."""
    lines = demo_md.splitlines()
    start = next((i for i, l in enumerate(lines)
                  if re.match(rf"^## round {n} — YYYY-MM-DD", l)), None)
    if start is None:
        return f"## round {n} — {when}\n- note: replayed; no record template found\n"
    block = []
    for ln in lines[start:]:
        if ln.strip().startswith("```"):
            break
        block.append(ln)
    tok = re.search(r"in≈(\d+)", demo_md)
    eg = re.search(r'e\.g\. "([^"]+)"', demo_md)

    def fill(m):
        inner = m.group(1).lower()
        if "own words" in inner or "note" in inner:
            return eg.group(1) if eg else "replayed"
        if "yes/no" in inner:
            return "yes"
        if "tok" in inner or "meter" in inner:
            return tok.group(1) if tok else "0"
        if "/5" in inner or inner in ("x", "y", "z"):
            return "3"
        return "replayed"

    text = "\n".join(block).replace("YYYY-MM-DD", when)
    return re.sub(r"<([^<>]*)>", fill, text).rstrip() + "\n"


# ------------------------------------------------------------------ the sandbox ------
def guard(dest):
    dest = dest.resolve()
    if dest == REPO or REPO in dest.parents or dest in REPO.parents:
        raise SystemExit(f"FAIL  {dest} is inside this repository. The sandbox must live "
                         f"outside it — a round-N commit here would make the tutor resume "
                         f"mid-course.")
    if (dest / ".git").exists():
        origin = git(dest, "remote", "get-url", "origin", check=False).strip()
        if origin:
            raise SystemExit(f"FAIL  {dest} is a clone of {origin}. Refusing to replay "
                             f"into a repository with a remote.")
    return dest


def build_sandbox(dest, fresh):
    if dest.exists():
        if not fresh:
            raise SystemExit(f"FAIL  {dest} already exists. Pass --fresh to rebuild it.")
        shutil.rmtree(dest)
    played = [l for l in git(REPO, "log", "--format=%s").splitlines()
              if re.match(r"^round-[1-5] ", l.strip())]
    if played:
        raise SystemExit("FAIL  this repo's history already contains round-N commits "
                         f"(e.g. {played[0]!r}). Replay expects an unplayed base.")
    print(f"NOTE  cloning into {dest}")
    subprocess.run(("git", "clone", "--quiet", str(REPO), str(dest)), check=True)
    git(dest, "config", "user.name", "replay")
    git(dest, "config", "user.email", "replay@localhost")
    git(dest, "remote", "remove", "origin", check=False)
    overlay(dest)
    seed = REPO / "setup/fixtures/memory-seed.db"
    if seed.exists():
        shutil.copy(seed, dest / "memory.db")
    venv = REPO / ".venv"
    if venv.exists() and not (dest / ".venv").exists():
        # A symlink shares the packages with no install. `rm -rf` on the sandbox removes
        # the link, never the real venv behind it.
        os.symlink(venv, dest / ".venv")


def overlay(dest):
    """Copy this repo's uncommitted work into the clone, so the file you are editing
    right now is the one that gets replayed and tested.

    Committed immediately, under a subject that is deliberately NOT `round-N …`: an
    overlaid file left uncommitted would dirty the sandbox's working tree, and a dirty
    tree is precisely the mid-TUTOR resume signal this tool has to reproduce faithfully.
    """
    copied = 0
    for ln in git(REPO, "status", "--porcelain").splitlines():
        path = ln[3:]
        if path.endswith("/"):
            continue
        src = REPO / path
        if not src.is_file():
            continue
        (dest / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest / path)
        copied += 1
    if copied:
        git(dest, "add", "-A")
        git(dest, "commit", "--quiet", "-m",
            "replay: overlay the author's uncommitted working tree", "-m", TRAILER)
        print(f"NOTE  overlaid {copied} uncommitted file(s) from the working tree")


# ------------------------------------------------------------------ the replay -------
def replay(dest, upto_round, upto_phase):
    scaffold = (dest / "spec/spec.md").read_text(encoding="utf-8")
    clauses, answers, templates, demos = {}, {}, {}, {}
    for n in range(1, 6):
        q = dest / f"course/rounds/round-{n}/questions.md"
        d = dest / f"course/rounds/round-{n}/demo.md"
        a = dest / f"course/rounds/round-{n}/answers.md"
        clauses[n] = clause_blocks(q.read_text(encoding="utf-8")) if q.exists() else []
        answers[n] = answer_blocks(q.read_text(encoding="utf-8")) if q.exists() else []
        templates[n] = a.read_text(encoding="utf-8") if a.exists() else ""
        demos[n] = d.read_text(encoding="utf-8") if d.exists() else ""

    made = []
    for n in range(1, upto_round + 1):
        for phase in PHASES:
            if n == upto_round and PHASES.index(phase) > PHASES.index(upto_phase):
                break
            rel = ARTIFACT[phase].format(n=n)
            path = dest / rel
            if phase == "tutor":
                path.write_text(fill_answers(templates[n], answers[n]), encoding="utf-8")
            elif phase == "spec":
                path.write_text(build_spec(scaffold, clauses, n), encoding="utf-8")
            elif phase == "build":
                ref = dest / f"course/rounds/round-{n}/reference/snackbot.py"
                shutil.copy(ref, path)
            else:
                when = (date.today() - timedelta(days=(6 - n))).isoformat()
                with open(path, "a", encoding="utf-8") as f:
                    f.write("\n" + demo_entry(demos[n], n, when) + "\n---\n")
            git(dest, "add", "--", rel)
            git(dest, "commit", "--quiet", "-m", f"round-{n} {phase}", "-m", TRAILER)
            made.append(f"round-{n} {phase}")
    return made


def resume_line(dest):
    """The position the tutor would derive: last course commit + working-tree state."""
    last = ""
    for s in git(dest, "log", "--format=%s").splitlines():
        if re.match(r"^round-[1-5] (tutor|spec|build|demo)$", s.strip()):
            last = s.strip()
            break
    dirty = [l for l in git(dest, "status", "--porcelain").splitlines() if l.strip()]
    if not last:
        return "Round 1 TUTOR, first question (no course commit yet)"
    n, phase = int(last.split()[0][-1]), last.split()[1]
    if phase == "demo":
        nxt = f"Round {n + 1} TUTOR" if n < 5 else "DONE — round-5 demo is the last phase"
        if dirty:
            nxt += ", resuming mid-round (answers.md is modified)"
        else:
            nxt += ", first question" if n < 5 else ""
        return nxt
    return {"tutor": f"Round {n} SPEC", "spec": f"Round {n} BUILD",
            "build": f"Round {n} DEMO"}[phase]


def main():
    ap = argparse.ArgumentParser(
        description="Stage a throwaway copy of the course at a chosen round.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--round", type=int, choices=range(1, 6),
                   help="start of round N: history ends at `round-(N-1) demo`")
    g.add_argument("--through", metavar='"round-N phase"',
                   help="replay through this commit exactly, e.g. 'round-4 spec'")
    ap.add_argument("--dir", help="sandbox path (default: under $TMPDIR)")
    ap.add_argument("--fresh", action="store_true", help="rebuild if it already exists")
    ap.add_argument("--mid-tutor", action="store_true",
                    help="leave the next round's answers.md modified but uncommitted")
    ap.add_argument("--serve", action="store_true",
                    help="also start the viewer there")
    ap.add_argument("--port", type=int, default=4100)
    a = ap.parse_args()

    if a.round:
        upto_round, upto_phase, label = a.round - 1, "demo", f"r{a.round}"
        if a.round == 1:
            upto_round = 0
    else:
        m = re.match(r"^round-([1-5]) (tutor|spec|build|demo)$", a.through.strip())
        if not m:
            raise SystemExit('FAIL  --through wants e.g. "round-4 spec"')
        upto_round, upto_phase = int(m.group(1)), m.group(2)
        label = f"r{upto_round}-{upto_phase}"

    tmp = Path(os.environ.get("TMPDIR", "/tmp"))
    dest = guard(Path(a.dir) if a.dir else tmp / f"snackbot-replay-{label}")
    build_sandbox(dest, a.fresh)
    made = replay(dest, upto_round, upto_phase) if upto_round else []

    if a.mid_tutor:
        n = upto_round + 1 if upto_phase == "demo" else upto_round
        rel = f"course/rounds/round-{n}/answers.md"
        p = dest / rel
        if p.exists():
            t = p.read_text(encoding="utf-8")
            p.write_text(t.replace(PLACEHOLDER, "(replayed mid-round answer)", 1),
                         encoding="utf-8")
            print(f"NOTE  left {rel} modified — the mid-TUTOR resume signal")

    print(f"\nPASS  sandbox ready ({len(made)} commit(s) replayed)")
    print(f"  path    {dest}")
    print(f"  resume  {resume_line(dest)}")
    print(f"\n  cd {dest} && claude          # play the round with a real tutor")
    print(f"  bash tools/viewer/serve.sh --ensure --port {a.port}   # (from there)")
    print("\nNOTE  This is a synthesized state for development, not a played course —")
    print("      no model was called and the answers are the course's own prose.")

    if a.serve:
        subprocess.run(("bash", "tools/viewer/serve.sh", "--ensure",
                        "--port", str(a.port)), cwd=dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
