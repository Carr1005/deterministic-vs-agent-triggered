#!/usr/bin/env python3
"""guide.py — the /guide page: a guide to the app the learner is building.

Three things the terminal cannot show them: how the app works right now (a diagram that
gains a piece with each round's build commit), what its memory actually holds, and a log
of every run the tutor made on their behalf — what it printed, what the meter counted.

Read-only over everything: git through `core.git`, `memory.db` through a `mode=ro` URI so
this process can never create or mutate it, and the run log (written only by
`tools/viewer/run.py`). Every page is built as a string, per request.

This page is expected to grow: a section per round, its own diagram per round, notes on
what to expect when you run each script. `render()` owns the whole body precisely so that
can happen here without touching the shell or the diffs page.
"""
import hashlib
import html
import json
import re
import sqlite3

import core

ID = "guide"
LABEL = "Guide"
TITLE = "A guide to what you've built"
FOOTER = ("Read-only over the repo; the only file it reads back is its own git-ignored "
          "run log (written by <code>tools/viewer/run.py</code>). Served from "
          "<code>tools/viewer/views/guide.py</code>; writes nothing. Stop the viewer with "
          "<code>bash tools/viewer/serve.sh --stop</code>.")

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
    parts.append(_box(770, 130, 120, 64, ["CONVERSATIONAL_", "MEMORY", "raw turns, per thread"], "active tbl"))
    parts.append(_box(770, 230, 120, 56, ["CONVERSATION_", "VECTORS", "the turns, embedded"], "active tbl"))
    parts.append(_box(770, 320, 120, 56, ["SEMANTIC_", "MEMORY", "the knowledge base"], "active tbl"))
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


def _table_card(name, n, what, cols, body, open_=False):
    head = "".join(f"<th>{c}</th>" for c in cols)
    # stable id so the shell can reopen this card across an auto-reload
    return (f'<details class="d" id="tbl-{name}"{" open" if open_ else ""}>'
            f'<summary><span class="file">{name}</span>'
            f'<span class="what">{what}</span><span class="n">{n} row(s)</span></summary>'
            f'<div class="tblwrap"><table class="db"><thead><tr>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div></details>')


def db_tables_html():
    db = core.db_path()
    if not db.exists():
        return _card("memory.db not created yet &mdash; <code>bash setup/bootstrap.sh</code> "
                     "creates and seeds it. Normal on a fresh clone.")
    try:
        conn = core.db_connect()
    except sqlite3.Error as e:
        return _card(f"could not open memory.db read-only: {html.escape(str(e))}")
    if conn is None:
        # The file existed a moment ago and does not now — a reset, or a sandbox being
        # deleted underneath us. Without this guard the first `conn.execute` raises
        # AttributeError, which the sqlite3.Error handler below cannot catch, and the
        # `finally` raises a second one that hides the first.
        return _card("memory.db is no longer there &mdash; it was removed while this "
                     "page was being built. Reload to try again.")
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
                             "the turns above again, embedded for search — search_memory() reads here"),
                            ("SEMANTIC_MEMORY",
                             "the knowledge base: pastry facts — search_knowledge_base() reads here")):
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
    except (sqlite3.Error, OSError) as e:
        # OSError too: db.stat() for the on-disk size is inside this block.
        return _card(f"memory.db could not be read: {html.escape(str(e))}")
    finally:
        conn.close()


# ---------------------------------------------------------------- the run log --------
def read_records():
    """Every parseable record, oldest first. A torn last line is skipped, not fatal."""
    try:
        text = core.RUN_LOG.read_text(encoding="utf-8")
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


def _meter_chips(output, elapsed_ms=None):
    """The meter figures for a run — plainly marked as a total when there are several.

    A `--x5` record holds five `[meter]` lines. Summing them is the right thing to show,
    but the chip borrowed src/meter.py's exact wording, so five runs added together read
    as one turn's footprint — and its summed latency was the latency of nothing at all.
    Elapsed comes from the record's own wall-clock instead.
    """
    hits = METER.findall(output)
    if not hits:
        return ""
    tin = sum(int(h[0]) for h in hits)
    tout = sum(int(h[1]) for h in hits)
    cost = sum(float(h[2]) for h in hits)
    lead = "" if len(hits) == 1 else f"{len(hits)} turns · total "
    took = (f" · {elapsed_ms}ms" if elapsed_ms is not None
            else f" · {sum(int(h[3]) for h in hits)}ms")
    chips = (f'<span class="n">{lead}in {tin} · out {tout} tok · ${cost:.5f}'
             f'{took}</span>')
    m = SAFE.search(output)
    if m:
        # Green only when nothing slipped through: 0/5 is the lesson of Round 4, and it
        # was rendering in the same colour as a pass.
        safe = int(m.group(1))
        tag = "b" if safe == 5 else "i"
        chips += f'<span class="n"><{tag}>{safe}/5 SAFE</{tag}></span>'
    return chips


def run_log_html():
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
        chips = _meter_chips(r.get("output", ""), r.get("ms"))
        rows = r.get("db_rows")
        delta = ""
        if isinstance(rows, dict) and isinstance(prev_rows, dict):
            for t in core.TABLES:
                d = (rows.get(t) or 0) - (prev_rows.get(t) or 0)
                if d:
                    # "since the previous recorded run", not "what this run did": runs
                    # the learner makes in their own terminal fall in the gap, and a
                    # reset shows up here as a large negative.
                    tag = "b" if d > 0 else "i"
                    delta += (f'<span class="n" title="change since the previous '
                              f'recorded run">Δ {t} <{tag}>{d:+d}</{tag}></span>')
        if isinstance(rows, dict):
            prev_rows = rows
        # The badge answers "which build printed this?", so it says `app R3`, never a
        # bare `R3` — a bare number reads as the round the learner is in, which it is
        # not: during round 1's TUTOR phase the app is still the R0 baseline, because
        # the build lands two phases later. `edited` covers the BUILD window, where the
        # code has changed but the commit has not happened yet.
        built = f"app R{stage}" + (" · edited" if r.get("src_dirty") else "")
        trunc = ('<p class="note">output truncated for the log; the terminal showed '
                 'all of it.</p>' if r.get("truncated") else "")
        newest = i == len(records) - 1
        # id from the timestamp: stable across reloads even as newer runs push it down
        rid = re.sub(r"[^0-9A-Za-z]", "", str(r.get("ts", ""))) or str(i)
        cards.append(
            f'<details class="d" id="run-{rid}"{" open" if newest else ""}>'
            f'<summary><span class="file" title="the build of src/snackbot.py that '
            f'printed this">{built}</span>'
            f'<span class="what"><code>{html.escape(argv)}</code> · '
            f'{html.escape(str(r.get("ts", "")))}</span>'
            f'{chips}{delta}{badge}</summary>'
            f'<pre class="uni">{output_html(r.get("output", "").rstrip())}</pre>{trunc}'
            f'</details>')
    # newest first: after every run the freshest card is at the top, already open
    return "".join(reversed(cards))


# ---------------------------------------------------------------- change signal ------
def _stat_sig(p):
    try:
        st = p.stat()
        return f"{st.st_mtime_ns}:{st.st_size}"
    except OSError:
        return "absent"


def signature():
    """Cheap fingerprint of everything this page renders. No content is read."""
    raw = "|".join((core.git_head(), _stat_sig(core.RUN_LOG), _stat_sig(core.db_path())))
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


CSS = r"""
h2{font-family:var(--mono);font-size:17px;font-weight:650;margin:42px 0 0;
  padding-bottom:10px;border-bottom:1px solid var(--base-300);letter-spacing:-.01em}
.stage{margin:18px 0 0;font-family:var(--mono);font-size:14px;color:var(--accent-ink);
  font-weight:650}

/* overrides of the shared vocabulary: this page uses these in denser contexts than
   the diffs page's header does */
.state{margin:14px 0 0}
details.src{margin:10px 0 0}
p.note{margin:10px 16px;max-width:70ch}

/* shell.py gives .n b the success colour; a short SAFE count or a negative row delta is
   not success, so those are marked with <i> instead. */
.n i{color:var(--danger-ink);font-style:normal;font-weight:650}
.what code{font-family:var(--mono);color:var(--base-content)}
.ok{color:var(--success-ink);font-weight:650;flex:none}
.bad{color:var(--danger-ink);font-weight:650;flex:none}
.dim{color:var(--base-content-secondary)}
.meter{color:var(--warning)}
.tool{color:var(--secondary-content)}
.turn{font-weight:650;color:var(--base-100)}

/* Tables scroll inside their own card rather than widening the page. */
.tblwrap{overflow-x:auto;border-top:1px solid var(--base-300)}
table.db{width:100%;border-collapse:collapse;font-family:var(--mono);
  font-size:var(--fs-small)}
table.db th{text-align:left;padding:9px 12px;color:var(--base-content-secondary);
  font-weight:650;border-bottom:1px solid var(--base-300);white-space:nowrap;
  background:var(--base-150)}
table.db td{padding:8px 12px;vertical-align:top;border-bottom:1px solid var(--hairline)}
table.db tr:last-child td{border-bottom:0}
td.num{white-space:nowrap;color:var(--base-content-secondary);
  font-variant-numeric:tabular-nums}
td.role{white-space:nowrap;color:var(--accent-ink);font-weight:650}
td.vec{color:var(--base-content-secondary);max-width:340px;overflow-wrap:anywhere}

/* The diagram panel. On a wide viewport it sits beside its own legend rather than
   stacking, which is the one place this page can spend horizontal room usefully. */
.panel{margin:16px 0 0;border:1px solid var(--base-300);background:var(--base-100);
  border-radius:12px;padding:14px 14px 6px}
.panel svg{width:100%;height:auto;display:block}
svg text{font-family:var(--mono);font-size:11px;fill:var(--base-content)}
svg text.lane{font-size:12px;fill:var(--base-content-secondary);font-weight:650}
svg .node rect{fill:var(--base-150);stroke:var(--base-content-secondary);
  stroke-width:1.2}
svg .node.frame rect{fill:none;stroke:var(--base-300)}
svg .node.frame text{fill:var(--base-content-secondary)}
svg .node.tbl rect{fill:var(--base-100);stroke:var(--accent)}
svg .node.tbl text{font-size:9.5px}
svg .term text{text-anchor:middle}
svg .edge{stroke:var(--base-content-secondary);stroke-width:1.4}
svg .chip rect{fill:var(--base-100);stroke:var(--base-300)}
svg .chip text{font-size:9.5px;fill:var(--base-content-secondary)}
svg .chip.removed rect{stroke:var(--primary)}
svg .chip.removed text{fill:var(--primary)}
svg line.restored{stroke:var(--accent);stroke-width:2.2}
svg .chip.restored rect{stroke:var(--accent)}
svg .chip.restored text{fill:var(--accent);font-weight:650}
svg .node.restored rect{stroke:var(--accent);stroke-width:2}
"""

JS = ""


def render():
    stage = core.course_stage()
    if stage:
        # "as built through", not "at": between a round's demo and the next round's
        # build the learner has moved on while the app has not, and a bare "Round N"
        # then contradicts the tutor's own round tag by two whole phases.
        stage_line = (f"App as built through Round {stage} of 5 — "
                      f"{html.escape(core.ROUND_TITLE[stage])}")
    else:
        stage_line = ("App at the Round-0 baseline — a bare LLM call. "
                      "Each round's build fills this page in.")
    if core.src_dirty():
        stage_line += " · src/snackbot.py has uncommitted edits"
    return f"""<header>
  <h1>A guide to what you've built</h1>
  <p class="sub">What you have built so far: how it works, what its memory holds, and
  every run your tutor made on your behalf. The page refreshes itself after each commit
  and each recorded run.</p>
  <p class="stage">{stage_line}</p>
</header>
<h2>How it works</h2>
{diagram_svg(stage, core.db_path().exists())}
<h2>What the memory holds</h2>
{db_tables_html()}
<h2>Runs your tutor made for you</h2>
{run_log_html()}"""
