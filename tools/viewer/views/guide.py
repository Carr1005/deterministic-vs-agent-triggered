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
import shell

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


# ---------------------------------------------------------------- the spec ----------
def _md(text):
    """The inline markdown a clause actually uses, and nothing else.

    Escaped FIRST, so nothing in the learner's own words can inject markup; the patterns
    below only ever wrap text that is already inert. Code spans run before emphasis, so
    an asterisk inside backticks stays literal.
    """
    out = html.escape(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", out)
    return out


def spec_clauses(n):
    """Round n's clauses from spec/spec.md, unwrapped into readable paragraphs.

    Two things make this less trivial than it looks. A tutor may write a clause as a
    blockquote (`> S1.1 — …`, the template's form) or bare (`S1.1 — …`, which is what a
    real session produced), so both are accepted. And the file is hard-wrapped mid
    sentence, so the lines of one clause are joined back into a paragraph — shown as
    stored, they read as broken lines rather than prose.
    """
    path = core.REPO / "spec/spec.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    section = re.search(rf"^## S{n} —.*?$(.*?)(?=^## S|\Z)", text, re.S | re.M)
    if not section:
        return []
    clauses, cur = [], None
    for ln in section.group(1).splitlines():
        body = ln[2:] if ln.startswith("> ") else ln.lstrip(">").strip() if ln.startswith(">") else ln
        if re.match(r"^\s*S[1-5]\.", body):
            if cur:
                clauses.append(" ".join(cur))
            cur = [body.strip()]
        elif cur is not None and body.strip():
            cur.append(body.strip())
        elif cur is not None:
            clauses.append(" ".join(cur))
            cur = None
    if cur:
        clauses.append(" ".join(cur))
    return clauses


def spec_html(n):
    cl = spec_clauses(n)
    if not cl:
        return ""
    items = "".join(f"<li>{_md(c)}</li>" for c in cl)
    return f'<ol class="spec">{items}</ol>'


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


def run_log_html(only_round=None, empty=None):
    """Cards for the runs of one round, or (only_round=None) the ones filed nowhere.

    A record made before the log carried a round has no home, so rather than guess one
    from `stage` — which counts builds, not rounds — those are listed under the overview.
    """
    records = [r for r in read_records() if r.get("round") == only_round]
    if not records:
        return _card(empty or "No runs in this round yet &mdash; when you ask your tutor "
                     "to run the app, it appears here. Runs you make in your own "
                     "terminal are yours alone.") if empty is not False else ""
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
    raw = "|".join((core.git_head(), _stat_sig(core.RUN_LOG), _stat_sig(core.db_path()),
                _stat_sig(core.REPO / "spec/spec.md")))
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


CSS = r"""
/* The round subtabs are this page's secondary bar, so anchored targets must clear it
   exactly as they do on the diffs page. */
:root{--sub-h:52px}
.bar-sub{top:var(--bar-top-h);height:var(--sub-h);z-index:20}
@media (max-width:699px){ :root{--sub-h:0px} .bar-sub{position:static;height:auto;
  padding-top:10px;padding-bottom:10px} }

h3{font-family:var(--sans);font-size:14.5px;font-weight:650;margin:26px 0 0;
  color:var(--base-content-secondary);letter-spacing:.01em}

/* A round band. Everything a round owns sits under one heading rule. */
.round{margin:38px 0 0;scroll-margin-top:calc(var(--bar-top-h) + var(--sub-h) + 14px)}
.rhead{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;
  border-bottom:1px solid var(--base-300);padding-bottom:10px}
.rnum{font-family:var(--mono);font-size:21px;font-weight:700;color:var(--accent);
  font-variant-numeric:tabular-nums;line-height:1}
.rttl{font-size:15.5px;color:var(--base-content);font-weight:550}
.hereis{font-family:var(--mono);font-size:11.5px;font-weight:650;
  color:var(--base-content);background:var(--tab-fill);border:1px solid var(--tab-edge);
  border-radius:999px;padding:2px 10px}

/* The spec, set to be read rather than diffed: prose measure, generous leading, and the
   clause number pulled into the margin so the sentence starts flush. */
ol.spec{list-style:none;counter-reset:cl;margin:12px 0 0;padding:0;
  display:flex;flex-direction:column;gap:12px;max-width:74ch}
ol.spec li{background:var(--base-100);border:1px solid var(--base-300);
  border-left:3px solid var(--accent);border-radius:10px;padding:14px 18px;
  font-size:15.5px;line-height:1.62;color:var(--base-content)}
ol.spec code{font-family:var(--mono);font-size:.88em;background:var(--base-200);
  border-radius:4px;padding:1px 5px}
ol.spec em{color:var(--base-content-secondary);font-style:italic}

.howto{margin:14px 0 0;max-width:74ch}
.howto p{margin:0 0 12px;color:var(--base-content-secondary);font-size:15px}
.howto dl{display:grid;grid-template-columns:auto 1fr;gap:8px 16px;margin:0;
  align-items:baseline}
.howto dt{font-family:var(--mono);font-size:var(--fs-small)}
.howto dt code{background:var(--base-200);border-radius:5px;padding:2px 7px;
  color:var(--base-content)}
.howto dd{margin:0;color:var(--base-content-secondary);font-size:var(--fs-small)}
@media (max-width:560px){ .howto dl{grid-template-columns:1fr;gap:2px 0}
  .howto dd{margin:0 0 8px} }

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


ROUND_ANCHORS = [("overview", "Overview")] + [(f"r{n}", f"R{n}") for n in range(1, 6)]

HOW_TO = """<div class="howto">
<p>The tutor runs these for you when you ask; anything it runs on your behalf lands in
that round's <em>Runs</em> below. What you run in your own terminal stays yours.</p>
<dl>
  <dt><code>src/snackbot.py "…"</code></dt><dd>one turn, with the meter line</dd>
  <dt><code>src/snackbot.py --x5</code></dt><dd>the same turn five times, counted</dd>
  <dt><code>setup/show_memory.py</code></dt><dd>prints the tables as they stand</dd>
  <dt><code>setup/reset_memory.py</code></dt><dd>restores the shipped 5/5/7 seed</dd>
</dl></div>"""


def round_section(n, commits, here, db_exists):
    """One round: what it is, and whatever of it exists yet.

    The diagram appears only once the round's build is committed — an unbuilt round has
    no state to draw, and drawing a future one would be showing something untrue. The
    spec arrives with its own commit, a round or a phase earlier.
    """
    built = (n, "build") in commits
    body = ""
    if (n, "spec") in commits and spec_html(n):
        body += f'<h3>What you specified</h3>{spec_html(n)}'
    if built:
        body += f'<h3>How the app worked after this round</h3>{diagram_svg(n, db_exists)}'
    runs = run_log_html(n, empty=False)
    if runs:
        body += f"<h3>Runs your tutor made</h3>{runs}"
    if not body:
        body = ('<p class="pending">Not reached yet &mdash; this round&rsquo;s spec, its '
                'diagram and its runs appear here as you get there.</p>')
    mark = ' <span class="hereis">you are here</span>' if n == here else ""
    return (f'<section class="round" id="r{n}">'
            f'<div class="rhead"><span class="rnum">{n}</span>'
            f'<span class="rttl">{html.escape(core.ROUND_TITLE[n])}</span>{mark}</div>'
            f'{body}</section>')


def render():
    stage = core.course_stage()
    commits = set(core.course_commits())
    here = core.course_round()
    db_exists = core.db_path().exists()
    if stage:
        stage_line = (f"App as built through Round {stage} of 5 — "
                      f"{html.escape(core.ROUND_TITLE[stage])}")
    else:
        stage_line = ("App at the Round-0 baseline — a bare LLM call. "
                      "Each round's build fills this page in.")
    if core.src_dirty():
        stage_line += " · src/snackbot.py has uncommitted edits"

    rounds = "".join(round_section(n, commits, here, db_exists) for n in range(1, 6))
    orphans = run_log_html(None, empty=False)
    return f"""<header>
  <h1>A guide to what you've built</h1>
  <p class="sub">The course round by round: what each one asks, what you specified, and
  how the app worked once you built it. Rounds you have not reached yet are listed so
  you can see where this is going.</p>
  <p class="stage">{stage_line}</p>
</header>
<div class="bar bar-sub">{shell.subtab_nav([(i, l, f"#{i}") for i, l in ROUND_ANCHORS], active=f"r{here}")}</div>
<section id="overview">
<h2>How to work with the app</h2>
{HOW_TO}
<h2>What the memory holds</h2>
{db_tables_html()}
{f'<h2>Earlier runs</h2>{orphans}' if orphans else ''}
</section>
{rounds}"""
