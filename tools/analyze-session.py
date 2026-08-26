#!/usr/bin/env python3
"""analyze-session.py — AUTHOR TOOL. Measure how a tutoring session actually went.

The course's own lesson applies to the course: you cannot improve question wording
without an instrument. This reads a finished session and reports where the time and
the iterations went — per phase, per question — plus every moment the learner signalled
confusion. Change a question, run a trial, compare the numbers.

Input is a Claude Code session log (JSONL), e.g.:
    .venv/bin/python tools/analyze-session.py ~/.claude/projects/<dir>/<session>.jsonl
This format is Claude-Code-specific; trials run in other coding agents need their own
parser. Read-only; writes nothing.

Known baseline, for comparison (session 5de77997…, snackbot-trial-2, 2026-08-19):
    R1 TUTOR: 9 learner turns · R2 TUTOR: 18 learner turns
    R2 Q3 was abandoned after 5 rephrasings — the outcome this instrument exists to catch.
"""
import json
import re
import sys
from datetime import datetime

TAG = re.compile(r"\[(R\d)\s·\s([A-Z]+)\]")
QMARK = re.compile(r"\*\*(Q\d(?:\.\d)?)[.\s—]")
CONFUSION = (
    "i don't understand", "i dont understand", "too vague", "more hints",
    "what do you want me to say", "what should i answer", "i don't get this",
    "i just can't",
)
REVEAL_HINTS = ("**reveal", "here it is, no friction", "so here's the reveal")
RESTATE_HINTS = ("own words", "say it back", "say that back", "finish this sentence")


def load(path):
    """Ordered (role, text, timestamp) for real conversation messages."""
    out = []
    for line in open(path, encoding="utf-8"):
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("type") not in ("user", "assistant") or o.get("isMeta"):
            continue
        m = o.get("message") or {}
        c = m.get("content")
        blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])
        txt = " ".join(b.get("text", "") for b in blocks
                       if isinstance(b, dict) and b.get("type") == "text").strip()
        # <bash-input>/<bash-stdout> are the learner's terminal echoes, not utterances.
        if not txt or txt.startswith(("<system-reminder", "<command-", "<local-command",
                                      "<bash-", "Caveat:")):
            continue
        out.append((m.get("role"), txt, o.get("timestamp")))
    return out


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def main(path):
    msgs = load(path)
    if not msgs:
        print("FAIL  no conversation messages found in", path)
        return 1

    phase = None          # (round, mode) from the tutor's tags
    question = None       # current QN marker within a TUTOR phase
    phases = {}           # (round, mode) -> dict
    questions = {}        # (round, qid) -> dict
    confusions, gaps = [], []
    prev_t = None

    for role, txt, t in msgs:
        if role == "assistant":
            tag = TAG.search(txt)
            if tag:
                phase = (tag.group(1), tag.group(2))
                if phase[1] != "TUTOR":
                    question = None
            q = QMARK.search(txt)
            if q and phase and phase[1] == "TUTOR":
                question = (phase[0], q.group(1))
                questions.setdefault(question, {"tutor": 0, "learner": 0,
                                                "reveal": False, "restate": 0})
        if phase:
            p = phases.setdefault(phase, {"tutor": 0, "learner": 0, "secs": 0.0, "t0": None})
            key = "learner" if role == "user" else "tutor"
            p[key] += 1
            cur = ts(t)
            if p["t0"] and cur:
                p["secs"] += (cur - p["t0"]).total_seconds()
            p["t0"] = cur
            if question:
                questions[question][key] += 1
                low = txt.lower()
                if role == "assistant":
                    if any(h in low for h in REVEAL_HINTS):
                        questions[question]["reveal"] = True
                    if any(h in low for h in RESTATE_HINTS):
                        questions[question]["restate"] += 1
        if role == "user":
            low = txt.lower()
            hits = [c for c in CONFUSION if c in low]
            if hits:
                confusions.append((phase, question, txt[:90]))
        cur = ts(t)
        if prev_t and cur and role == "user":
            d = (cur - prev_t).total_seconds()
            if d >= 120:
                gaps.append((phase, d, txt[:60]))
        prev_t = ts(t) or prev_t

    print(f"session: {path}")
    print(f"messages: {len(msgs)}\n")

    print("== turns per phase (learner turns = iterations)")
    for (rnd, mode), p in sorted(phases.items()):
        mins = f"{p['secs']/60:.0f}m"
        print(f"  {rnd} · {mode:<7} learner {p['learner']:>3}  tutor {p['tutor']:>3}  wall {mins:>5}")

    print("\n== per question (TUTOR phases)")
    for (rnd, qid), q in sorted(questions.items()):
        flags = []
        if q["reveal"]:
            flags.append("reveal")
        if q["restate"]:
            flags.append(f"restate×{q['restate']}")
        print(f"  {rnd} {qid:<5} learner {q['learner']:>3}  tutor {q['tutor']:>3}  {' '.join(flags)}")

    print(f"\n== confusion markers from the learner: {len(confusions)}")
    for ph, qq, quote in confusions:
        where = f"{ph[0]}·{ph[1]}" if ph else "?"
        print(f"  [{where} {qq[1] if qq else '-'}] {quote}")

    print(f"\n== silences ≥2 min before a learner reply: {len(gaps)}")
    for ph, d, quote in gaps:
        where = f"{ph[0]}·{ph[1]}" if ph else "?"
        print(f"  [{where}] {d/60:.0f}m  then: {quote}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: tools/analyze-session.py <session.jsonl>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
