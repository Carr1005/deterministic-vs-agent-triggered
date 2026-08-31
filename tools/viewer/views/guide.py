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
    "semsearch": (3, None, None),
    "embed":   (3, None, None),
    "x5":      (4, None, None),
    "e_meter": (1, None, None),
    "e_read":  (2, 3, 5),          # the star of the course
    "e_write": (2, None, None),
    "e_sem":   (3, None, None),
    "e_tools": (3, None, None),
    "e_embed": (3, None, None),
    "e_back":  (3, None, None),
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


# ---- geometry ------------------------------------------------------------------------
# Three columns, not four. That is the whole reason the previous layout tangled: four
# columns of boxes left ~48px between them, and a label like "the model decides" is 111px
# wide, so every label landed on top of whatever was already there. Three columns leave a
# 130px and a 120px gap — room for the widest label with margin to spare.
#
#   PAD | left 124 |  gap 130  | app 190 |  gap 120  | right 200 | PAD
#
# Widths are per column, not per card, so cards line up. Text has to fit: a mono glyph
# advances 0.6em, so a title costs len·7.2 + 18px of padding and a subtitle len·6.3 + 18.
# The layout harness re-checks every string against its box at every stage — see
# scratchpad/test_layout.py. Height is kept tight because the SVG scales to fit its
# column: a shorter canvas renders larger.
CANVAS_W, CANVAS_H = 780, 440
PAD = 8

# Nodes are neutral; only their fill says what kind of thing they are, so colour is left
# free to mean what TRAVELS (see EDGES). One border, one radius, one padding, title at the
# top-left of every card — the terminal, the API and a table are the same component with
# different contents, and should not look like three unrelated widgets.
#
# meter.py sits in the left column, NOT inside the src/snackbot.py frame: it is a separate
# file, and what it prints goes to the terminal it now sits under.
#      id            x    y    w    h   kind       title                    subtitle
NODES = {
    "term":    (  8, 120, 124,  62, "surface", "your terminal",        "you \u2192 / bot \u2190"),
    "meter":   (  8, 216, 124,  58, "code",    "meter.py",             "prints [meter]"),
    "app":     (262,  34, 190, 314, "frame",   "src/snackbot.py",      ""),
    "x5":      (274,  62, 166,  44, "code",    "--x5 \u00b7 run_n()",      "5 runs, count SAFE"),
    "detfns":  (274, 118, 166,  44, "code",    "read_user_facts()",    "save_turn()"),
    "tools":   (274, 174, 166,  44, "code",    "search_memory()",      "search_knowledge_base()"),
    # Both tools are one function underneath, and that function is where the sequence
    # lives: embed the query through the API, read the WHOLE table back, rank the rows
    # here in Python. Drawn as a card because a reader cannot otherwise tell why one
    # embeddings box serves two searches — or that the database does no searching at all.
    "semsearch":(274, 258, 166,  62, "code",   "semantic_search()",    "embed \u2192 read \u2192 rank"),
    "llm":     (572,  34, 200,  48, "service", "chat completions",     "gpt-5.6-luna"),
    "db":      (572, 110, 200, 180, "frame",   "memory.db",            ""),
    # One line per table now that the column is wide enough to hold the whole name. The
    # old CONVERSATIONAL_ / MEMORY split existed only to survive a 106px card.
    "convo":   (584, 142, 176,  34, "store",   "CONVERSATIONAL_MEMORY", ""),
    "vectors": (584, 190, 176,  34, "store",   "CONVERSATION_VECTORS",  ""),
    "facts":   (584, 238, 176,  34, "store",   "SEMANTIC_MEMORY",       ""),
    "embed":   (572, 352, 200,  52, "service", "embeddings",           "text-embedding-3-small"),
}

# channel  = what travels, and therefore the colour: api (blue) or memory (teal).
# invoked  = who decides it runs, and therefore the line: "code" solid, "model" dashed.
#            Dashed reads as conditional, which is what agent-triggered means — so the
#            course's own distinction keeps a channel of its own rather than living only
#            in the words.
# A qualifier survives on exactly the two edges that carry the contrast — the pinned
# every-turn read, and the moment a tool call actually happens. The legend already tells
# the reader that a solid line means every turn, so repeating it on write and measure was
# noise that cost the labels room they did not have. "the model decides" sits on e_sem
# rather than on the table reads because that is where the decision takes effect;
# everything downstream of it inherits the dashed line.
#           key         from      to        verb          qualifier             channel  invoked
EDGES = {
    "e_in":   ("term",   "app",    "you type",    "",                    "plain", "code"),
    "e_api":  ("app",    "llm",    "request",     "",                    "api",   "code"),
    "e_out":  ("llm",    "app",    "response",    "",                    "api",   "code"),
    "e_meter":("app",    "meter",  "measure",     "",                    "plain", "code"),
    "e_read": ("detfns", "convo",  "read",        "every turn",          "mem",   "code"),
    "e_write":("detfns", "convo",  "write",       "",                    "mem",   "code"),
    # "read all rows", not "search": semantic_search() runs SELECT content, embedding
    # FROM <table> with no WHERE, and cosine-ranks the result in Python. The query vector
    # never reaches SQL, so calling this a search would tell the reader the database does
    # matching it does not do — and would hide the cost the meter is there to measure.
    "e_sem":  ("tools",  "semsearch","both call", "the model decides",   "plain", "model"),
    "e_tools":("semsearch","vectors","read all rows", "",                "mem",   "model"),
    "e_kb":   ("semsearch","facts",  "read all rows", "",                "mem",   "model"),
    "e_embed":("semsearch","embed",  "embed query",   "",                "api",   "model"),
    # An API call is drawn as a round trip, the way chat completions already is on this
    # canvas - the returned value is the point. Here it is doubly so: the vector that comes
    # back is what cosine() ranks the rows against, so without this arrow the card's
    # "embed -> read -> rank" has a middle step with nowhere to happen. Memory operations
    # keep a single arrow: "read" already implies rows coming back, and doubling those
    # would bury the read/write distinction the whole course is about.
    "e_back": ("embed",  "semsearch","the vector", "",                   "api",   "model"),
}

# Where each edge attaches, kept apart from what it means. A side midpoint was the bug:
# on the 226px-tall app frame it put the API call halfway down the box and sent the line
# diagonally across the canvas, crossing everything. An explicit y per end lets a line
# leave at the height of the thing it is talking to, so edges run near-horizontal and
# stop crossing. `t` is how far along the line the label sits — two parallel edges use
# different values so their labels cannot collide.
#            key        from side, y    to side, y     t
ROUTE = {
    "e_in":    (("r", 151), ("l", 151), 0.50),
    "e_api":   (("r",  48), ("l",  48), 0.42),
    "e_out":   (("l",  72), ("r",  72), 0.42),
    "e_meter": (("l", 245), ("r", 245), 0.50),
    "e_read":  (("r", 122), ("l", 144), 0.50),
    "e_write": (("r", 158), ("l", 174), 0.50),
    # The three edges leave semantic_search() at 270/285/298 and land at 207/252/342 —
    # monotone in both, which is what makes crossing impossible rather than merely absent.
    "e_sem":   (("b", 357), ("t", 357), 0.50),
    "e_tools": (("r", 268), ("l", 200), 0.50),
    "e_kb":    (("r", 286), ("l", 258), 0.50),
    "e_embed": (("r", 296), ("l", 364), 0.50),
    # The return lands on the card's BOTTOM edge, not its right. Run as a parallel pair
    # the two lines stayed ~27px apart and each label covered both of them; leaving from
    # one side and arriving at another makes them diverge, so each label masks its own.
    "e_back":  (("l", 396), ("b", 400), 0.42),
}


def _node(nid, override=None):
    x, y, w, h, kind, title, sub = NODES[nid]
    if override:
        title, sub = override
    # A frame labels itself at the TOP - its middle belongs to the cards nested inside
    # it. A card centres what it holds: two lines straddling the middle, one line on
    # it. For the common 44px card these land at +19/+34, where they already were.
    if kind == "frame":
        ty = y + 19
    elif sub:
        ty = y + h / 2 - 3
    else:
        ty = y + h / 2 + 4
    t = f'<text class="ttl" x="{x + 10}" y="{ty:.0f}">{html.escape(title)}</text>'
    if sub:
        t += f'<text class="sub" x="{x + 10}" y="{ty + 15:.0f}">{html.escape(sub)}</text>'
    return (f'<g class="node {kind}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>{t}</g>')


def _anchor(nid, side, at):
    """A point on one side of a node, at an explicit y (for l/r) or x (for t/b)."""
    x, y, w, h, *_ = NODES[nid]
    return {"l": (x, at), "r": (x + w, at), "t": (at, y), "b": (at, y + h)}[side]


def _arrow(a, b, key, mk=""):
    """One edge: a directional line, and its verb sitting on the line rather than near it."""
    _, _, verb, qual, channel, invoked = EDGES[key]
    (sa, ya), (sb, yb), t = ROUTE[key]
    x1, y1 = _anchor(a, sa, ya)
    x2, y2 = _anchor(b, sb, yb)
    cls = f"edge {channel}" + ("" if invoked == "code" else " model")
    line = (f'<line class="{cls}" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'marker-end="url(#ar-{channel}{mk})"/>')
    return line + _chip(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, verb, qual, channel)


def _chip(cx, cy, verb, qual, channel):
    """A label that masks the line it belongs to, and can never leave the canvas.

    Sized from the text it actually holds: .v renders at 11px and .q at 9.5px, so the
    advances are 6.6 and 5.7. The old formula used 5.6 for both and every chip was a few
    pixels narrower than its own words.
    """
    w = max(14 + 6.6 * len(verb), 14 + 5.7 * len(qual) if qual else 0)
    h = 26 if qual else 16
    x = min(max(cx - w / 2, PAD), CANVAS_W - w - PAD)
    y = cy - h / 2
    t = f'<text class="v" x="{x + w / 2:.0f}" y="{y + (11 if qual else 11.5):.0f}">{html.escape(verb)}</text>'
    if qual:
        t += f'<text class="q" x="{x + w / 2:.0f}" y="{y + 22:.0f}">{html.escape(qual)}</text>'
    return (f'<g class="chip {channel}">'
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h}" rx="7"/>{t}</g>')


def _markers(suffix):
    """One arrowhead per channel, with ids unique to this panel.

    The page draws six diagrams — five rounds plus the overview — and every one used to
    define `ar-mem`/`ar-api`/`ar-plain`. Duplicate ids are invalid, and `url(#ar-mem)`
    resolves to whichever comes FIRST in the document, so all six panels were quietly
    borrowing the first panel's markers. It rendered right only because the definitions
    were identical; the day one of them needs to differ, it would fail silently.
    """
    return "".join(
        f'<marker id="ar-{k}{suffix}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse" class="mk {k}">'
        f'<path d="M0 0 L10 5 L0 10 z"/></marker>'
        for k in ("plain", "api", "mem"))


def diagram_svg(stage, db_exists, key=None):
    # Markers are defined per panel and referenced by id, so each panel needs its own
    # suffix; `arrow` closes over it rather than repeating it at ten call sites.
    mk = f"-{key or stage}"

    def arrow(a, b, k):
        return _arrow(a, b, k, mk)

    on = {k: _on(stage, k) for k in STAGED}
    pinned = state(stage, *STAGED["e_read"]) == "restored"
    p = [f'<svg viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img" '
         f'aria-label="What the SnackBot app does right now">',
         f"<defs>{_markers(mk)}</defs>"]

    for nid in ("app", "db", "term", "llm", "convo", "vectors", "facts"):
        p.append(_node(nid))
    p.append(arrow("term", "app", "e_in"))
    p.append(arrow("app", "llm", "e_api"))
    p.append(arrow("llm", "app", "e_out"))

    if on["x5"]:
        p.append(_node("x5"))
    if on["detfns"]:
        # The card lists what RUNS, not what is defined: Round 3 leaves read_user_facts()
        # in the file but stops calling it every turn, so it drops off here until Round 5
        # pins it back.
        p.append(_node("detfns", None if on["e_read"] else ("save_turn()", "")))
    if on["tools"]:
        p.append(_node("tools"))
    if on["semsearch"]:
        p.append(_node("semsearch"))
        p.append(arrow("tools", "semsearch", "e_sem"))
    if on["meter"]:
        p.append(_node("meter"))
        p.append(arrow("app", "meter", "e_meter"))
    if on["embed"]:
        p.append(_node("embed"))
    if on["e_read"]:
        p.append(arrow("detfns", "convo", "e_read"))
    if on["e_write"]:
        p.append(arrow("detfns", "convo", "e_write"))
    if on["e_tools"]:
        p.append(arrow("semsearch", "vectors", "e_tools"))
        p.append(arrow("semsearch", "facts", "e_kb"))
    if on["e_embed"]:
        p.append(arrow("semsearch", "embed", "e_embed"))
        p.append(arrow("embed", "semsearch", "e_back"))

    if stage < 2:
        # The round-1 lesson, on the diagram itself: a database that is full, and unread.
        note = ("full — nothing reads it yet" if db_exists
                else "created by bash setup/bootstrap.sh")
        p.append(_chip(650, 418, note, "", "warn"))

    p.append("</svg>")
    return "".join(p)


# Just the key. What any of it MEANS is the tutor's job — a page that explains its own
# diagram is doing Socratic work badly, and this one used to carry two paragraphs of it.
LEGEND = (
    '<div class="dlegend">'
    '<span><i class="k-mem"></i>memory</span>'
    '<span><i class="k-api"></i>API</span>'
    '<span><i class="k-solid"></i>deterministic &mdash; code invokes, every turn</span>'
    '<span><i class="k-dash"></i>agent-triggered &mdash; the model invokes</span>'
    '</div>')


# ---- what one turn does, in order ----------------------------------------------------
# The question a box-and-arrow map is structurally unable to answer. Three properties of a
# turn are invisible on the canvas: `chat completions` runs TWICE (before a search and
# again with its results), the search is conditional, and the whole thing is a loop. A
# reader left to infer order from box positions reconstructs the retrieve-then-generate
# order — which is precisely the one Round 3 exists to overturn.
#
# Every step is gated by the SAME STAGED key the diagram uses, so the map and the list
# cannot drift apart about what exists. `agent-triggered` is what makes a step conditional
# — that is the course's own definition, not a rendering flag, so it is read off the tag.
#         id        gate       call                        tag                target                                     channel
TURN = (
    ("read",  "e_read",  "read_user_facts()",         "deterministic",   "CONVERSATIONAL_MEMORY",                   "mem"),
    ("write", "e_write", 'save_turn("user", \u2026)',      "deterministic",   "CONVERSATIONAL_MEMORY",                   "mem"),
    ("llm",   "",        "chat completions",          "every turn",      "gpt-5.6-luna",                              "api"),
    ("tools", "e_tools", "semantic_search()",         "agent-triggered", "embeddings, then every row of one table",  "mem"),
    ("write", "e_write", 'save_turn("assistant", \u2026)', "deterministic",   "CONVERSATIONAL_MEMORY",                   "mem"),
    # "your terminal" was wrong here: report() prints exactly one thing, the [meter] line.
    # Naming the device instead of the output also contradicted the map, where this same
    # step points at meter.py / "prints [meter]".
    ("meter", "e_meter", "report(\u2026)",                "every turn",      "the [meter] line",                        "plain"),
)


def turn_html(stage, key=None):
    """The order of one turn, as a numbered list the browser numbers itself.

    Flat, deliberately: the conditional step is marked rather than nested, so the numbers
    stay continuous however many steps a round happens to have. Its note names no step
    number for the same reason — "back to the model" cannot go stale, "back to 3" can.
    """
    rows = []
    for sid, gate, call, tag, target, channel in TURN:
        if gate and not _on(stage, gate):
            continue
        cond = tag == "agent-triggered"
        lead = ('<span class="tif">only if the model asks for a tool</span>'
                if cond else "")
        note = ('<span class="tnote">\u2026 then back to the model with the results, '
                'up to 5&times;</span>') if cond else ""
        # built outside the f-strings: 3.10 forbids backslashes inside an expression part
        li_cls = ' class="cond"' if cond else ""
        tag_cls = "agent" if cond else "det"
        rows.append(
            f'<li data-step="{sid}"{li_cls}>{lead}'
            f'<code class="tcall">{html.escape(call)}</code>'
            f'<span class="ttag {tag_cls}">{tag}</span>'
            f'<span class="ttarget {channel}">&rarr; {html.escape(target)}</span>'
            f'{note}</li>')
    # The answer itself is not a step, because it is not inside the turn: run_turn()
    # returns the reply and its caller prints it. Saying so is better than leaving a list
    # of "one turn, in order" that never mentions where your answer comes from.
    out = ('<p class="tout"><code>run_turn()</code> then returns the reply, and '
           '<code>bot &larr; …</code> prints it. That happens after the turn, not '
           'inside it &mdash; which is why it carries no number.</p>')
    foot = ('<p class="tfoot"><code>--x5</code> runs this whole turn five times over and '
            'counts how many of the replies are safe.</p>') if _on(stage, "x5") else ""
    # Closed by default: the map answers "what is there" at a glance and should stay
    # open, while the order is a question you go looking for. The id lets POLL_JS restore
    # it across an auto-reload like every other disclosure on the page — and it must be
    # UNIQUE, because the overview draws the current stage's panel a second time. Two
    # elements with one id and getElementById silently restores only the first.
    return (f'<details class="src turnbox" id="turn-{key or stage}">'
            f'<summary>One turn, in order</summary>'
            f'<ol class="turn">{"".join(rows)}</ol>{out}{foot}</details>')


def app_panel(stage, db_exists, key=None):
    """The map, its key, the order of a turn, and how to read all three.

    Two views of one subject, so they share a panel: the diagram says what exists, the
    list says what happens. Neither can do the other's job.

    `key` distinguishes the overview's copy ("right now") from the round section's ("after
    this round") in the DOM. The two are the same picture whenever they show the same
    stage; the headings above them are what say why it appears twice.
    """
    return (f'<section class="panel">{diagram_svg(stage, db_exists, key)}'
            f'{LEGEND}{turn_html(stage, key)}</section>')



# ---------------------------------------------------------------- the database -------
def _card(text):
    return f'<p class="pending">{text}</p>'


def _table_card(name, n, what, cols, body):
    """One table, closed. The summary already carries the useful glance — which
    tables exist, what each is for, how many rows it holds — and five turns of
    conversation unrolled above the other two was more page than that is worth."""
    head = "".join(f"<th>{c}</th>" for c in cols)
    # stable id so the shell can reopen this card across an auto-reload
    return (f'<details class="d" id="tbl-{name}">'
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
        # These descriptions say what a table HOLDS and never who reads it. Naming
        # `search_memory()` here told a Round-1 reader about code that will not exist for
        # two more rounds — the same promising-the-future the diagram is built to avoid.
        # The diagram is now the only place that shows who touches what, and it only ever
        # draws reads that already exist. "message", not "turn": save_turn() runs twice a
        # turn, so a row is one message, not an exchange.
        out.append(_table_card("CONVERSATIONAL_MEMORY", len(rows),
                               "every message, yours and the bot&rsquo;s",
                               ("id", "thread", "role", "content", "ts"), body))
        # Embeddings are ~28 KB of JSON each; never fetch them whole. The preview is
        # enough to make "it's a list of floats" tangible.
        # "a list of numbers" is the course's own gloss for an embedding — see the comment
        # above EMBED_MODEL in the round-3 reference implementation.
        for table, what in (("CONVERSATION_VECTORS",
                             "the same messages, each as a list of numbers"),
                            ("SEMANTIC_MEMORY",
                             "snack and allergen facts, each as a list of numbers")):
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


# ---------------------------------------------------------------- the file map ------
# What each file is FOR — nothing about its current state, and no live figures.
#
# This map answers "which part is which". Sizes were here once: they told the reader
# little (meter.py's line count is not something a learner acts on) and each duplicated
# something rendered in full further down the page — the diagram shows the app growing,
# the spec sections list the clauses, the tables show the rows. Anything not rendered
# cannot fall out of sync, so the cheapest way to keep this honest is to say less.
#                 path,                     role
FILES = (
    ("dir",  "src/", ""),
    ("you",  "src/snackbot.py",       "the conversation itself &mdash; the one file "
                                      "you change, every round"),
    ("file", "src/meter.py",          "measures every turn: tokens, cost, latency"),
    ("file", "src/seed_memory.py",    "builds the starting database; ran once, at setup"),
    ("dir",  "spec/", ""),
    ("file", "spec/spec.md",          "the requirements you argue into existence, "
                                      "round by round"),
    ("dir",  "setup/", ""),
    ("file", "setup/show_memory.py",  "prints what the memory holds right now"),
    ("file", "setup/reset_memory.py", "restores the original seeded database"),
    # at the repo root, so it is not indented under the directory above it
    ("root", "memory.db",             "the memory &mdash; where turns and facts are "
                                      "stored"),
)


def file_tree_html():
    rows = []
    for kind, rel, role in FILES:
        if kind == "dir":
            rows.append(f'<div class="fdir">{html.escape(rel)}</div>')
            continue
        name = rel.rsplit("/", 1)[-1] if "/" in rel else rel
        cls = {"you": "frow yours", "root": "frow root"}.get(kind, "frow")
        rows.append(f'<div class="{cls}">'
                    f'<span class="fname">{html.escape(name)}</span>'
                    f'<span class="farrow" aria-hidden="true">&rarr;</span>'
                    f'<span class="frole">{role}</span></div>')
    return (f'<div class="ftree">{"".join(rows)}</div>'
            '<p class="note">Ask your tutor to run any of these and the output lands '
            'under that round&rsquo;s <em>Runs</em>. What you run in your own terminal '
            'stays yours.</p>')


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

/* The file map. A four-column grid so names, sizes and roles line up down the page;
   below 620px the role drops to its own line rather than squeezing to two words. */
.ftree{margin:14px 0 0;border:1px solid var(--base-300);background:var(--base-100);
  border-radius:12px;padding:14px 16px;font-family:var(--mono);
  font-size:var(--fs-small);display:grid;
  grid-template-columns:auto auto 1fr;align-items:baseline;gap:2px 0}
.fdir{grid-column:1/-1;color:var(--base-content-secondary);margin-top:8px}
.fdir:first-child{margin-top:0}
.frow{grid-column:1/-1;display:grid;grid-template-columns:subgrid;
  padding:3px 0;border-radius:6px}
.frow.root{margin-top:8px}
.frow.root .fname{padding-left:0}
.fname{color:var(--base-content);font-weight:650;padding-left:18px;
  padding-right:14px;white-space:nowrap}
.farrow{color:var(--base-content-secondary);padding-right:10px}
.frole{color:var(--base-content-secondary);font-family:var(--sans);line-height:1.5}
/* the one file the learner edits, marked so the map answers "which part is mine" */
.frow.yours .fname{color:var(--accent-ink)}
.frow.yours .frole{color:var(--base-content)}
@media (max-width:619px){
  .ftree{display:block}
  .frow{display:block;padding:6px 0}
  .fname{padding-left:14px}
  .farrow{display:none}
  .frole{display:block;padding-left:14px;margin-top:2px}
}

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

/* The diagram panel, in two steps rather than one.

   Below 720px it goes full-bleed, which buys back the gutter on both sides — at 719px
   that is 691px of drawing width, and a 780-wide canvas scaled to fit still renders its
   12px type at 10.6px. So it scales, and nothing is cut off.

   Only below 680px would that type drop under 10px. There the canvas stops shrinking and
   the reader pans instead. Three columns made this possible: the four-column canvas had
   to scroll from 719px down. */
.panel{margin:16px 0 0;border:1px solid var(--base-300);background:var(--base-100);
  border-radius:12px;padding:14px 14px 10px}
.panel svg{width:100%;height:auto;display:block}
@media (max-width:719px){
  .panel{margin-left:calc(var(--gutter) * -1);margin-right:calc(var(--gutter) * -1);
    border-radius:0;border-left:0;border-right:0;overflow-x:auto}
}
@media (max-width:679px){
  .panel svg{width:760px;max-width:none}
}

/* The turn list. Same two channels as the canvas, carried the same way: colour says what
   travels (teal memory, blue API), and border style says who invokes it — solid for
   deterministic, dashed for agent-triggered. The conditional step gets the dashed rule
   down its left edge for the same reason its arrows are dashed on the map: it is the one
   step that may not happen. */
/* details.turnbox, not .turnbox: shell.py's `details.src` carries its own margin at the
   same specificity, and a bare class would lose to it. */
details.turnbox{margin:16px 0 2px;padding:14px 0 0;border-top:1px solid var(--base-300)}
ol.turn{margin:11px 0 0;padding:0 0 0 24px;font-family:var(--mono)}
ol.turn>li{margin:0 0 8px;padding:2px 0 2px 8px;font-size:13px;line-height:1.5;
  display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 14px;align-items:baseline}
ol.turn>li::marker{color:var(--base-content-secondary);font-weight:650}
ol.turn>li.cond{border-left:2px dashed var(--secondary);padding-left:10px;
  margin-left:-2px;padding-top:4px;padding-bottom:4px}
.tcall{font-weight:650;color:var(--base-content)}
.tif,.tnote{grid-column:1/-1;font-size:11px;color:var(--base-content-secondary)}
.tif{margin-bottom:2px;font-style:normal;color:var(--secondary)}
.ttag{grid-column:2;justify-self:end;white-space:nowrap;font-size:10.5px;font-weight:600;
  padding:1px 8px;border-radius:999px;border:1px solid var(--base-300);
  color:var(--base-content-secondary)}
.ttag.agent{border-style:dashed;border-color:var(--secondary);color:var(--secondary)}
.ttarget{grid-column:1;color:var(--base-content-secondary)}
.ttarget.mem{color:var(--secondary)}
.ttarget.api{color:var(--accent)}
.tout,.tfoot{margin:10px 0 0;font-size:12px;color:var(--base-content-secondary)}
.tout code,.tfoot code{font-family:var(--mono);background:var(--base-200);padding:1px 5px;
  border-radius:4px}
@media (max-width:719px){
  ol.turn>li{grid-template-columns:1fr}
  .ttag{grid-column:1;justify-self:start;margin-top:2px}
}

/* ONE card rule. Every node has the same border, radius and title position; only the fill
   says what kind of thing it is, which leaves colour free to mean what travels. */
svg text{font-family:var(--mono);font-size:12px;fill:var(--base-content)}
svg .node rect{fill:var(--base-100);stroke:var(--base-300);stroke-width:1.3}
svg .node .ttl{font-weight:650}
svg .node .sub{fill:var(--base-content-secondary);font-size:10.5px}
svg .node.surface rect{fill:var(--base-200)}
svg .node.frame rect{fill:none;stroke-dasharray:3 3}
svg .node.frame .ttl{fill:var(--base-content-secondary);font-weight:600}
svg .node.service rect{stroke:var(--accent)}
svg .node.store rect{stroke:var(--secondary)}

/* Colour = what travels. Line = who decides: solid means code invokes it every turn,
   dashed means the model may or may not. Red is kept for warnings only. */
svg .edge{stroke:var(--base-content-secondary);stroke-width:1.5;fill:none}
svg .edge.api{stroke:var(--accent)}
svg .edge.mem{stroke:var(--secondary)}
svg .edge.model{stroke-dasharray:6 4}
svg .mk path{fill:var(--base-content-secondary)}
svg .mk.api path{fill:var(--accent)}
svg .mk.mem path{fill:var(--secondary)}

/* A verb sits ON its line, masking it, so it reads as belonging to that arrow. */
svg .chip rect{fill:var(--base-100);stroke:var(--base-300)}
svg .chip .v{font-size:11px;text-anchor:middle;font-weight:600}
svg .chip .q{font-size:9.5px;text-anchor:middle;fill:var(--base-content-secondary)}
svg .chip.api rect{stroke:var(--accent)}
svg .chip.api .v{fill:var(--accent-ink)}
svg .chip.mem rect{stroke:var(--secondary)}
svg .chip.mem .v{fill:var(--secondary)}
svg .chip.warn rect{stroke:var(--primary)}
svg .chip.warn .v{fill:var(--danger-ink)}

.dlegend{display:flex;flex-wrap:wrap;gap:6px 18px;margin:10px 2px 0;
  font-family:var(--mono);font-size:11.5px;color:var(--base-content-secondary)}
.dlegend span{display:inline-flex;align-items:center;gap:7px}
.dlegend i{width:18px;height:0;border-top:2px solid var(--base-content-secondary)}
.dlegend i.k-mem{border-color:var(--secondary)}
.dlegend i.k-api{border-color:var(--accent)}
.dlegend i.k-dash{border-top-style:dashed}
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
        body += f'<h3 id="r{n}-spec">What you specified</h3>{spec_html(n)}'
    if built:
        body += (f'<h3 id="r{n}-app">How the app worked after this round</h3>'
                     f'{app_panel(n, db_exists)}')
    runs = run_log_html(n, empty=False)
    if runs:
        body += f'<h3 id="r{n}-runs">Runs your tutor made</h3>{runs}'
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

    # The overview's third question, beside "what is it made of" and "what its memory
    # holds" — and like those two it describes the app as it SHIPS, not as it stands today.
    # Stage 0 deliberately, never course_stage(): every round section below is headed "how
    # the app worked after this round", so the current build already has a home and drawing
    # it here would only duplicate one of them. What was missing is the starting point they
    # are all departures from.
    base = ('<h2>What the app does before Round 1</h2>'
            '<p class="note">One call to the model. Nothing read from memory, nothing '
            'written to it &mdash; and the database is already full.</p>'
            f'{app_panel(0, db_exists, key="base")}')

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
<h2>What the app is made of</h2>
{file_tree_html()}
{base}
<h2>What the memory holds right now</h2>
{db_tables_html()}
{f'<h2>Earlier runs</h2>{orphans}' if orphans else ''}
</section>
{rounds}"""
