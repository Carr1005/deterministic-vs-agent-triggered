#!/usr/bin/env python3
"""serve.py — a live page of the working app's status, on localhost:5000.

Why it exists: the diff viewer (tools/diffview) shows what each round *changed*; nothing
shows the learner what the app *is* right now. This serves three things at a stable URL:
the app's architecture as it fills in round by round, the memory tables as they stand,
and a log of every run the tutor made on the learner's behalf — what it printed, what
the meter counted (the log is written by tools/appview/run.py; this file only reads it).

Three invariants this file must never break:

  1. It writes NOTHING, anywhere. `git status --porcelain` is the tutor's mid-round
     resume signal (course/PROTOCOL.md), so every page is built as a string, per
     request. Git is only read (hermetically, same flags as tools/diffview/serve.py);
     memory.db is opened read-only via a `mode=ro` URI, so this server can never
     create, lock, or mutate it; the run log is only read.
  2. It uses only the standard library, so setup/requirements.txt and setup/check.sh
     stay untouched and nobody mid-course has to re-bootstrap.
  3. It is a window, never a gate: nothing in the course consults this page or the run
     log. Delete tools/appview entirely and the course runs identically.
"""
import argparse
import hashlib
import html
import http.server
import json
import os
import re
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

# run.py is the writer; its top half is the shared read-only source layer (repo root,
# log path, db path, course stage, hermetic git). Imported so the two files can never
# disagree about where things live. Import-safe: main-guarded, stdlib, no side effects.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import REPO, RUN_LOG, TABLES, course_stage, db_path  # noqa: E402

HEALTH_TOKEN = "snackbot-appview-ok"

# Same titles as tools/diffview/serve.py, so the two pages speak one language.
ROUND_TITLE = {
    1: "The meter — instrument before you optimise",
    2: "Deterministic memory — code invokes, every turn",
    3: "Agent-triggered memory — the model invokes, via tools",
    4: "Counting — one passing run proves nothing",
    5: "The per-operation decision — pin exactly one read",
}

METER = re.compile(r"\[meter\] in=(\d+) tok\s+out=(\d+) tok\s+cost=\$([0-9.]+)\s+latency=(\d+)ms")
SAFE = re.compile(r"^(\d+)/5 replies contained", re.M)


# ---------------------------------------------------------------- the diagram --------
# The diagram shows ONLY what the app does right now — nothing dimmed, nothing promised.
# Elements appear when their round's `round-N build` commit exists, checked against
# course/rounds/round-N/reference/snackbot.py:
#   R1 adds the meter; R2 adds read_user_facts()/save_turn() called every turn; R3 adds
#   embeddings + the two search tools and REMOVES the every-turn read call (the function
#   stays defined — only the call goes); R4 adds the --x5 harness; R5 restores the read,
#   pinned, as the only deterministic read.
#                 arrives  removed  restored
STAGED = {
    "meter":   (1, None, None),
    "detfns":  (2, None, None),
    "tools":   (3, None, None),
    "embed":   (3, None, None),
    "x5":      (4, None, None),
    "e_meter": (1, None, None),
    "e_read":  (2, 3, 5),          # the star of the course
    "e_write": (2, None, None),
    "e_tools": (3, None, None),
    "e_embed": (3, None, None),
}


def state(stage, arrives, removed=None, restored=None):
    """One of future / active / removed / restored, for an element of the diagram.
    future and removed elements are simply not drawn — the page shows current status."""
    if stage < arrives:
        return "future"
    if restored and stage >= restored:
        return "restored"
    if removed and stage >= removed:
        return "removed"
    return "active"


def _on(stage, key):
    """Is this element part of the app right now?"""
    return state(stage, *STAGED[key]) in ("active", "restored")


def _box(x, y, w, h, lines, cls):
    txt = "".join(
        f'<text x="{x + w / 2:.0f}" y="{y + 17 + i * 15}" text-anchor="middle">{html.escape(s)}</text>'
        for i, s in enumerate(lines))
    return f'<g class="node {cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/>{txt}</g>'


def _edge(x1, y1, x2, y2, cls):
    return f'<line class="edge {cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'


def _label(x, y, text, cls):
    w = 12 + 5.3 * len(text)
    return (f'<g class="chip {cls}"><rect x="{x - w / 2:.0f}" y="{y}" width="{w:.0f}" height="16" rx="8"/>'
            f'<text x="{x:.0f}" y="{y + 11.5}" text-anchor="middle">{html.escape(text)}</text></g>')


def diagram_svg(stage, db_exists):
    on = {k: _on(stage, k) for k in STAGED}
    pinned = state(stage, *STAGED["e_read"]) == "restored"
    parts = ['<svg viewBox="0 0 920 500" role="img" '
             'aria-label="What the SnackBot app does right now">']

    # lane headers
    for x, name in ((95, "your terminal"), (350, "src/snackbot.py"),
                    (620, "OpenAI"), (830, "memory.db")):
        parts.append(f'<text class="lane" x="{x}" y="38" text-anchor="middle">{name}</text>')

    # always present: terminal, run_turn container, chat model, the shipped database
    parts.append(_box(20, 200, 150, 120, ["you → …", "[tool] …",
                                          "[meter] …", "bot ← …"], "active term"))
    parts.append(f'<g class="node active frame"><rect x="230" y="70" width="240" height="380" rx="4"/>'
                 f'<text x="350" y="92" text-anchor="middle">run_turn()</text></g>')
    parts.append(_box(540, 70, 160, 56, ["chat completions", "gpt-5-mini"], "active"))
    parts.append(f'<g class="node active frame"><rect x="760" y="90" width="140" height="340" rx="4"/>'
                 f'<text x="830" y="112" text-anchor="middle">3 tables</text></g>')
    parts.append(_box(770, 130, 120, 64, ["CONVERSATIONAL_", "MEMORY", "turns, per thread"], "active tbl"))
    parts.append(_box(770, 230, 120, 56, ["CONVERSATION_", "VECTORS", "embedded turns"], "active tbl"))
    parts.append(_box(770, 320, 120, 56, ["SEMANTIC_", "MEMORY", "pastry facts"], "active tbl"))
    parts.append(_edge(170, 245, 230, 245, "active"))
    parts.append(_edge(470, 98, 540, 98, "active"))

    # everything below exists only once its round's build commit does
    if on["x5"]:
        parts.append(_box(245, 105, 210, 30, ["--x5 · run_n(): 5 runs, count SAFE"], "active"))
    if on["detfns"]:
        names = (["read_user_facts()", "save_turn()"] if on["e_read"]
                 else ["save_turn()"])
        parts.append(_box(245, 160, 210, 52, names, "active"))
    if on["tools"]:
        parts.append(_box(245, 235, 210, 52, ["search_memory()",
                                              "search_knowledge_base()"], "active"))
    if on["meter"]:
        parts.append(_box(245, 380, 210, 48, ["meter.py", "prints the [meter] line"], "active"))
        parts.append(_edge(350, 300, 350, 378, "active"))
        parts.append(_label(350, 330, "every turn", "active"))
    if on["embed"]:
        parts.append(_box(540, 380, 160, 48, ["embeddings API",
                                              "text-embedding-3-small"], "active"))
    if on["e_read"]:
        cls = "restored" if pinned else "active"
        text = ("pinned — the ONE deterministic read" if pinned
                else "deterministic read — every turn")
        parts.append(_edge(455, 172, 770, 158, cls))
        parts.append(_label(608, 138, text, cls))
    if on["e_write"]:
        parts.append(_edge(455, 196, 770, 182, "active"))
        parts.append(_label(608, 202, "deterministic writes — every turn", "active"))
    if on["e_tools"]:
        parts.append(_edge(455, 250, 770, 256, "active"))
        parts.append(_edge(455, 262, 770, 344, "active"))
        parts.append(_label(608, 292, "agent-triggered — the model decides", "active"))
    if on["e_embed"]:
        parts.append(_edge(430, 287, 560, 380, "active"))
        parts.append(_label(478, 344, "embed the query, cosine, top 3", "active"))

    # the round-1 lesson, on the diagram itself: a full database nobody reads
    if stage < 2:
        text = ("full, but nothing reads it yet" if db_exists
                else "created at setup (bash setup/bootstrap.sh)")
        parts.append(_label(830, 442, text, "removed"))

    parts.append("</svg>")

    legend = (
        '<details class="src"><summary>how to read this</summary>'
        '<p class="note">Only what your app does right now is drawn — the diagram gains '
        'a piece each time a round&rsquo;s build is committed. The database ships full '
        'from the start; whether anything reads it is what the course is about. In '
        'Round 3 the every-turn read disappears from here (the model decides instead); '
        'in Round 5 it returns, pinned, in teal.</p></details>')
    return f'<section class="panel">{"".join(parts)}{legend}</section>'


# ---------------------------------------------------------------- the database -------
def _card(text):
    return f'<p class="pending">{text}</p>'


def db_tables_html():
    db = db_path()
    if not db.exists():
        return _card("memory.db not created yet &mdash; <code>bash setup/bootstrap.sh</code> "
                     "creates and seeds it. Normal on a fresh clone.")
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    except sqlite3.Error as e:
        return _card(f"could not open memory.db read-only: {html.escape(str(e))}")
    try:
        out = []
        # Turns in full — this is the memory the deterministic read feeds to the model.
        rows = conn.execute("SELECT id, thread_id, role, content, ts "
                            "FROM CONVERSATIONAL_MEMORY ORDER BY id").fetchall()
        body = "".join(
            f"<tr><td class='num'>{i}</td><td>{html.escape(t)}</td>"
            f"<td class='role'>{html.escape(r)}</td><td>{html.escape(c)}</td>"
            f"<td class='num'>{html.escape(ts or '')}</td></tr>"
            for i, t, r, c, ts in rows)
        out.append(_table_card("CONVERSATIONAL_MEMORY", len(rows),
                               "the stored turns — what the deterministic read returns",
                               ("id", "thread", "role", "content", "ts"), body, open_=True))
        # Embeddings are ~28 KB of JSON each; never fetch them whole. The preview is
        # enough to make "it's a list of floats" tangible.
        for table, what in (("CONVERSATION_VECTORS",
                             "the same turns, embedded — search_memory() searches here"),
                            ("SEMANTIC_MEMORY",
                             "the pastry facts — search_knowledge_base() searches here")):
            rows = conn.execute(f"SELECT id, content, substr(embedding, 1, 48), "
                                f"length(embedding) FROM {table} ORDER BY id").fetchall()
            body = "".join(
                f"<tr><td class='num'>{i}</td><td>{html.escape(c)}</td>"
                f"<td class='vec'>{html.escape(e)}… <span class='dim'>JSON, "
                f"{n // 1024} KB</span></td></tr>"
                for i, c, e, n in rows)
            out.append(_table_card(table, len(rows), what,
                                   ("id", "content", "embedding"), body))
        size = db.stat().st_size / 1024
        out.append(f'<p class="state">file: {html.escape(str(db.name))} ({size:.0f} KB on disk)</p>')
        return "".join(out)
    except sqlite3.Error as e:
        return _card(f"memory.db could not be read: {html.escape(str(e))}")
    finally:
        conn.close()


def _table_card(name, n, what, cols, body, open_=False):
    head = "".join(f"<th>{c}</th>" for c in cols)
    return (f'<details class="d"{" open" if open_ else ""}>'
            f'<summary><span class="file">{name}</span>'
            f'<span class="what">{what}</span><span class="n">{n} row(s)</span></summary>'
            f'<div class="tblwrap"><table class="db"><thead><tr>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div></details>')


# ---------------------------------------------------------------- the run log --------
def read_records():
    """Every parseable record, oldest first. A torn last line is skipped, not fatal."""
    try:
        text = RUN_LOG.read_text(encoding="utf-8")
    except OSError:
        return []
    records = []
    for line in text.splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict):
            records.append(r)
    return records


def output_html(text):
    out = []
    for ln in text.split("\n"):
        e = html.escape(ln)
        if ln.startswith("[meter]"):
            out.append(f'<span class="meter">{e}</span>')
        elif ln.startswith("[tool]"):
            out.append(f'<span class="tool">{e}</span>')
        elif ln.startswith("you →") or ln.startswith("bot ←"):
            out.append(f'<span class="turn">{e}</span>')
        elif re.match(r"\s*run \d+: SAFE", ln):
            out.append(f'<span class="add">{e}</span>')
        elif re.match(r"\s*run \d+: UNSAFE", ln):
            out.append(f'<span class="del">{e}</span>')
        else:
            out.append(e)
    return "\n".join(out)


def _meter_chips(output):
    hits = METER.findall(output)
    if not hits:
        return ""
    tin = sum(int(h[0]) for h in hits)
    tout = sum(int(h[1]) for h in hits)
    cost = sum(float(h[2]) for h in hits)
    ms = sum(int(h[3]) for h in hits)
    chips = f'<span class="n">in {tin} · out {tout} tok · ${cost:.5f} · {ms}ms</span>'
    m = SAFE.search(output)
    if m:
        chips += f'<span class="n"><b>{m.group(1)}/5 SAFE</b></span>'
    return chips


def run_log_html(current):
    records = read_records()
    if not records:
        return _card("No runs yet &mdash; when you ask your tutor to run the app for "
                     "you, the run appears here. Runs you make in your own terminal "
                     "are yours alone.")
    cards = []
    prev_rows = None
    for i, r in enumerate(records):
        argv = " ".join(str(a) for a in r.get("argv", []))
        rc = r.get("exit")
        badge = ('<span class="ok">exit 0</span>' if rc == 0
                 else f'<span class="bad">exit {html.escape(str(rc))}</span>')
        stage = r.get("stage", 0)
        chips = _meter_chips(r.get("output", ""))
        rows = r.get("db_rows")
        delta = ""
        if isinstance(rows, dict) and isinstance(prev_rows, dict):
            for t in TABLES:
                d = (rows.get(t) or 0) - (prev_rows.get(t) or 0)
                if d:
                    delta += f'<span class="n"><b>Δ {t} {d:+d}</b></span>'
        if isinstance(rows, dict):
            prev_rows = rows
        note = (' <span class="dim">(from an earlier session)</span>'
                if isinstance(stage, int) and stage > current else "")
        trunc = ('<p class="note">output truncated for the log; the terminal showed '
                 'all of it.</p>' if r.get("truncated") else "")
        newest = i == len(records) - 1
        cards.append(
            f'<details class="d"{" open" if newest else ""}>'
            f'<summary><span class="file">R{stage}</span>'
            f'<span class="what"><code>{html.escape(argv)}</code> · '
            f'{html.escape(str(r.get("ts", "")))}{note}</span>'
            f'{chips}{delta}{badge}</summary>'
            f'<pre class="uni">{output_html(r.get("output", "").rstrip())}</pre>{trunc}'
            f'</details>')
    # newest first: after every run the freshest card is at the top, already open
    return "".join(reversed(cards))


# ---------------------------------------------------------------- change signal ------
def _git_head():
    r = subprocess.run(("git", "-C", str(REPO), "log", "-1", "--format=%H"),
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _stat_sig(p):
    try:
        st = p.stat()
        return f"{st.st_mtime_ns}:{st.st_size}"
    except OSError:
        return "absent"


def state_hash():
    """Cheap fingerprint of everything the page renders. No content is read."""
    raw = "|".join((_git_head(), _stat_sig(RUN_LOG), _stat_sig(db_path())))
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------- rendering ----------
CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --ink:#151a1c;--dim:#5c6a6d;--faint:#8a979a;--ground:#f4f6f5;--surface:#fff;
  --sunken:#1b2225;--rule:#d8dedb;--petrol:#175c68;--brass:#8f6a15;
  --moss:#3f6b2e;--rust:#9a3b2e;--term-fg:#c9d4d3;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#e3e9e8;--dim:#96a4a6;--faint:#6d7b7e;--ground:#101517;--surface:#161d1f;
  --sunken:#0a0e10;--rule:#26302f;--petrol:#6fb9c4;--brass:#d9a83a;
  --moss:#8ec26f;--rust:#e59480;
}}
:root[data-theme="dark"]{
  --ink:#e3e9e8;--dim:#96a4a6;--faint:#6d7b7e;--ground:#101517;--surface:#161d1f;
  --sunken:#0a0e10;--rule:#26302f;--petrol:#6fb9c4;--brass:#d9a83a;
  --moss:#8ec26f;--rust:#e59480;
}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1000px;margin:0 auto;padding:0 24px 80px}
header{padding:48px 0 24px;border-bottom:1px solid var(--rule)}
h1{font-family:var(--mono);font-size:clamp(22px,3.4vw,30px);letter-spacing:-.02em;
  font-weight:600;margin:0 0 10px}
h2{font-family:var(--mono);font-size:16px;font-weight:600;margin:44px 0 0;
  padding-bottom:8px;border-bottom:1px solid var(--rule)}
.sub{color:var(--dim);max-width:66ch;margin:0;font-size:15px}
.state{margin:14px 0 0;font-family:var(--mono);font-size:12.5px;color:var(--faint)}
.stage{margin:20px 0 0;font-family:var(--mono);font-size:14px;color:var(--petrol);
  font-weight:600}
p.note{margin:8px 14px;font-size:13px;color:var(--faint);max-width:70ch}
.pending{color:var(--faint);font-size:14px;padding:14px 0 0;font-style:italic}
details.src{margin:10px 0 0}
details.src>summary{cursor:pointer;font-family:var(--mono);font-size:12.5px;
  color:var(--faint);list-style:none;display:inline-flex;gap:8px;align-items:baseline}
details.src>summary::-webkit-details-marker{display:none}
details.src>summary::before{content:"\\25B8"}
details.src[open]>summary::before{content:"\\25BE"}
details.d{margin:16px 0 0;border:1px solid var(--rule);background:var(--surface)}
details.d>summary{cursor:pointer;padding:11px 14px;display:flex;gap:12px;
  align-items:baseline;font-family:var(--mono);font-size:13px;flex-wrap:wrap}
details.d>summary::-webkit-details-marker{display:none}
details.d>summary::before{content:"\\25B8";color:var(--faint);flex:none}
details.d[open]>summary::before{content:"\\25BE"}
.file{color:var(--ink);font-weight:600;flex:none}
.what{color:var(--dim);font-family:var(--sans);font-size:13px;flex:1;min-width:180px}
.what code{font-family:var(--mono);color:var(--ink)}
.n{font-variant-numeric:tabular-nums;flex:none;color:var(--faint)}
.n b{color:var(--moss);font-weight:600}
.ok{color:var(--moss);font-weight:600;flex:none}.bad{color:var(--rust);font-weight:600;flex:none}
.dim{color:var(--faint)}
pre{margin:0;background:var(--sunken);color:var(--term-fg);font-family:var(--mono);
  font-size:12.5px;line-height:1.55;padding:14px;overflow-x:auto;white-space:pre;
  border-top:1px solid var(--rule)}
.add{color:var(--moss)}.del{color:var(--rust)}
.meter{color:var(--brass)}.tool{color:var(--petrol)}.turn{font-weight:600}
.tblwrap{overflow-x:auto;border-top:1px solid var(--rule)}
table.db{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:12.5px}
table.db th{text-align:left;padding:7px 10px;color:var(--faint);font-weight:600;
  border-bottom:1px solid var(--rule);white-space:nowrap}
table.db td{padding:6px 10px;vertical-align:top;border-bottom:1px solid var(--rule)}
table.db tr:last-child td{border-bottom:0}
td.num{white-space:nowrap;color:var(--faint);font-variant-numeric:tabular-nums}
td.role{white-space:nowrap;color:var(--petrol);font-weight:600}
td.vec{color:var(--faint);max-width:340px;overflow-wrap:anywhere}
.panel{margin:16px 0 0;border:1px solid var(--rule);background:var(--surface);
  padding:10px 10px 4px}
.panel svg{width:100%;height:auto;display:block}
svg text{font-family:var(--mono);font-size:11px;fill:var(--ink)}
svg text.lane{font-size:12px;fill:var(--faint);font-weight:600}
svg .node rect{fill:var(--ground);stroke:var(--dim);stroke-width:1.2}
svg .node.frame rect{fill:none;stroke:var(--rule)}
svg .node.frame text{fill:var(--faint)}
svg .node.tbl rect{fill:var(--surface);stroke:var(--petrol)}
svg .node.tbl text{font-size:9.5px}
svg .term text{text-anchor:middle}
svg .edge{stroke:var(--dim);stroke-width:1.4}
svg .chip rect{fill:var(--surface);stroke:var(--rule)}
svg .chip text{font-size:9.5px;fill:var(--dim)}
svg .chip.removed rect{stroke:var(--rust)}
svg .chip.removed text{fill:var(--rust)}
svg line.restored{stroke:var(--petrol);stroke-width:2.2}
svg .chip.restored rect{stroke:var(--petrol)}
svg .chip.restored text{fill:var(--petrol);font-weight:600}
svg .node.restored rect{stroke:var(--petrol);stroke-width:2}
footer{margin:56px 0 0;padding-top:20px;border-top:1px solid var(--rule);
  font-size:13px;color:var(--faint)}
footer code{font-family:var(--mono);font-size:12px}
"""


def page():
    stage = course_stage()
    if stage:
        stage_line = f"App at Round {stage} of 5 — {html.escape(ROUND_TITLE[stage])}"
    else:
        stage_line = ("App at the Round-0 baseline — a bare LLM call. "
                      "Each round's build fills this page in.")
    hash_now = state_hash()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Your app, right now</title>
<style>{CSS}</style></head><body>
<div class="wrap">
<header>
  <h1>Your app, right now</h1>
  <p class="sub">What SnackBot is at this point in the course: how it works, what its
  memory holds, and every run your tutor made on your behalf. The page refreshes itself
  after each commit and each recorded run.</p>
  <p class="stage">{stage_line}</p>
</header>
<h2>How it works</h2>
{diagram_svg(stage, db_path().exists())}
<h2>What the memory holds</h2>
{db_tables_html()}
<h2>Runs your tutor made for you</h2>
{run_log_html(stage)}
<footer>Read-only over the repo; the only file it reads back is its own git-ignored run
log (written by <code>tools/appview/run.py</code>). Served from
<code>tools/appview/serve.py</code>; writes nothing. Stop it with
<code>bash tools/appview/serve.sh --stop</code>.</footer>
</div>
<script>
// Reload only when something actually changed, so scroll and open cards survive.
(function () {{
  var cur = "{hash_now}";
  setInterval(function () {{
    fetch("/state").then(function (r) {{ return r.text(); }}).then(function (h) {{
      if (h && h !== cur) location.reload();
    }}).catch(function () {{}});   // server gone (idle reaper): go quiet, no errors
  }}, 3000);
}})();
</script>
</body></html>"""


# ---------------------------------------------------------------- http ---------------
class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "snackbot-appview"

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/healthz"):
            self.server.last_seen = time.time()
            self._send(200, HEALTH_TOKEN, "text/plain; charset=utf-8")
        elif path == "/state":
            # Deliberately does NOT refresh last_seen: the page polls this every few
            # seconds, and a forgotten open tab must not keep the server alive forever.
            self._send(200, state_hash(), "text/plain; charset=utf-8")
        elif path in ("/", "/index.html"):
            self.server.last_seen = time.time()
            self._send(200, page())
        else:
            self._send(404, "not found", "text/plain; charset=utf-8")

    def log_message(self, fmt, *args):   # one tidy line, to stdout only
        sys.stdout.write("  %s %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()


def reaper(httpd, idle_minutes):
    """Shut down after idle_minutes with no requests, so an orphan cannot outlive its use."""
    if idle_minutes <= 0:
        return
    while True:
        time.sleep(15)
        if time.time() - httpd.last_seen > idle_minutes * 60:
            print(f"NOTE  idle for {idle_minutes} min — shutting down.")
            sys.stdout.flush()
            httpd.shutdown()
            return


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--idle", type=int, default=60,
                    help="shut down after N idle minutes (0 disables)")
    a = ap.parse_args()

    if not (REPO / ".git").exists():
        print(f"FAIL  {REPO} is not a git repository — no course to report on.")
        return 1
    try:
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    except OSError as e:
        print(f"FAIL  cannot bind port {a.port}: {e}")
        return 1
    httpd.last_seen = time.time()
    threading.Thread(target=reaper, args=(httpd, a.idle), daemon=True).start()
    print(f"PASS  appview on http://localhost:{a.port}/  (idle timeout {a.idle} min)")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nNOTE  stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
