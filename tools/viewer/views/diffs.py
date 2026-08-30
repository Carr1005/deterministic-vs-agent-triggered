#!/usr/bin/env python3
"""diffs.py — the /diffs page: every round's spec change and code change.

Why it exists: the tutor shows each diff as terminal text from `git diff HEAD~1`, which
is transient and can only ever reach the round you are standing in. This serves every
round's spec change and code change at a stable URL, so a learner in Round 4 can still
look at what Round 2 did, and Round 3's ~110-line diff can be read in a page instead of
scrolled past.

Read-only: it runs `git log`, `git diff` and `git show` through `core.git`, and nothing
else. Every page is built as a string, per request — `git status --porcelain` is the
tutor's mid-round resume signal, so this must never write into the repository.
"""
import html
import re

import core

ID = "diffs"
LABEL = "Diffs"
TITLE = "Your diffs, round by round"
FOOTER = ("Read-only. Served from <code>tools/viewer/views/diffs.py</code>; writes "
          "nothing. Stop the viewer with <code>bash tools/viewer/serve.sh --stop</code>.")

ROUNDS = (1, 2, 3, 4, 5)

# Which artifact each phase commit carries (course/PROTOCOL.md's table), and the path the
# diff must be scoped to. Scoping is required: round-1/build.md warns in its own words
# that "commits carry other artifacts too".
PHASES = (
    ("spec", "spec/spec.md", "spec/", "the requirement you argued into existence"),
    ("build", "src/snackbot.py", "src/", "the code that requirement demanded"),
)


def scoped_diff(sha, path):
    """The change this commit made under `path`, or "" if it has no parent."""
    if not core.git("rev-parse", "--verify", "--quiet", f"{sha}^"):
        return core.git("show", *core.NO_EXT, "--format=", sha, "--", path)
    return core.git("diff", *core.NO_EXT, f"{sha}~1", sha, "--", path)


def counts(diff):
    # The trailing space is load-bearing: a file header is always `--- a/path` or
    # `+++ b/path`, while a *removed* line that itself reads `---` arrives as `----`.
    # Matching the bare prefix mistook that deletion for a header, so it went uncounted
    # here and grey in diff_html while split_html drew it red — the two views
    # disagreeing, which the docstring below promises cannot happen.
    add = sum(1 for l in diff.splitlines()
              if l.startswith("+") and not l.startswith("+++ "))
    rm = sum(1 for l in diff.splitlines()
             if l.startswith("-") and not l.startswith("--- "))
    return add, rm


def diff_html(diff):
    """One block per line, so a change reads as a full-width wash rather than as tinted
    text — the encoding the side-by-side view already used, which is why the two views
    now look alike. Coloured text was the inconsistency: a pale addition on a dark panel
    is nearly white, so additions barely registered.

    Joined with no separator on purpose. The blocks supply the line breaks; a newline
    between them would be rendered too, and every line would carry double leading.

    The lines sit inside one `.dlw` wrapper sized to max-content. A block line is only as
    wide as the panel's *visible* box, so on a diff wide enough to scroll, a wash would
    stop at the fold and the rest of the line would sit on bare background; filling a
    max-content wrapper instead makes it span the whole scroll width.
    """
    out = []
    for ln in diff.split("\n"):
        if ln.startswith("@@"):
            cls = "dl hunk"
        elif ln.startswith("+") and not ln.startswith("+++ "):
            cls = "dl ins"
        elif ln.startswith("-") and not ln.startswith("--- "):
            cls = "dl rem"
        elif ln.startswith(("diff --git", "index ", "+++ ", "--- ")):
            cls = "dl meta"
        else:
            cls = "dl"
        out.append(f'<span class="{cls}">{html.escape(ln)}</span>')
    return f'<span class="dlw">{"".join(out)}</span>' 


HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def split_rows(diff):
    """Re-pair a unified diff into (old_no, old_text, new_no, new_text, kind) rows.

    Derived from the same text the unified view renders, so the two can never disagree.
    Within a hunk, consecutive removals and additions are collected and then paired
    positionally; whichever side is shorter gets padding rows. `kind` is one of
    same / change / del / add / pad-left / pad-right.
    """
    rows, dels, adds = [], [], []
    old_no = new_no = 0
    # A trailing newline would otherwise split into a final "" that reads as a context
    # line and inflates both counters by one.
    diff = diff.rstrip("\n")
    if not diff:
        return rows

    def flush():
        nonlocal dels, adds, old_no, new_no
        for i in range(max(len(dels), len(adds))):
            d = dels[i] if i < len(dels) else None
            a = adds[i] if i < len(adds) else None
            if d is not None:
                old_no += 1
            if a is not None:
                new_no += 1
            kind = ("change" if d is not None and a is not None
                    else "del" if a is None else "add")
            rows.append((old_no if d is not None else None, d,
                         new_no if a is not None else None, a, kind))
        dels, adds = [], []

    for ln in diff.split("\n"):
        if ln.startswith("@@"):
            flush()
            m = HUNK.match(ln)
            if m:
                old_no, new_no = int(m.group(1)) - 1, int(m.group(2)) - 1
            rows.append((None, ln, None, None, "hunk"))
        elif ln.startswith(("diff --git", "index ", "--- ", "+++ ", "new file", "deleted file",
                            "similarity index", "rename ")):
            continue                      # the filename is already in the summary
        elif ln.startswith("-"):
            dels.append(ln[1:])
        elif ln.startswith("+"):
            adds.append(ln[1:])
        else:
            flush()
            old_no += 1
            new_no += 1
            rows.append((old_no, ln[1:] if ln.startswith(" ") else ln,
                         new_no, ln[1:] if ln.startswith(" ") else ln, "same"))
    flush()
    return rows


def split_html(diff):
    def cell(no, text, cls):
        if text is None:
            return f'<td class="ln pad"></td><td class="tx pad"></td>'
        return (f'<td class="ln">{no if no else ""}</td>'
                f'<td class="tx {cls}">{html.escape(text) or "&nbsp;"}</td>')

    out = ['<table class="sbs"><colgroup><col class="cln"><col><col class="cln"><col>'
           "</colgroup><tbody>"]
    for old_no, old_t, new_no, new_t, kind in split_rows(diff):
        if kind == "hunk":
            out.append(f'<tr><td class="hunkrow" colspan="4">{html.escape(old_t)}</td></tr>')
            continue
        lcls = "" if kind == "same" else "o"
        rcls = "" if kind == "same" else "n"
        out.append("<tr>" + cell(old_no, old_t, lcls) + cell(new_no, new_t, rcls) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


CSS = r"""
ul.matched{list-style:none;margin:10px 0 0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:3px 22px;
  font-family:var(--mono);font-size:var(--fs-small);
  color:var(--base-content-secondary);max-width:700px}
ul.matched code{background:none;border:0;padding:0;color:var(--accent-ink);font-weight:650}

/* A round is a titled band. The number carries the colour so the title can stay at
   full-contrast body ink. */
.round{margin:40px 0 0}
.rhead{display:flex;gap:12px;align-items:baseline;
  border-bottom:1px solid var(--base-300);padding-bottom:10px}
.rnum{font-family:var(--mono);font-size:21px;font-weight:700;color:var(--accent);
  font-variant-numeric:tabular-nums;line-height:1}
.rttl{font-size:15.5px;color:var(--base-content);font-weight:550}
.n i{color:var(--danger-ink);font-style:normal;font-weight:650}

/* Unified view. Same washes, same hunk band and same legible body text as the
   side-by-side table below, mixed from the same tokens — the two views render the same
   diff, so they should not encode it differently. inline-block + min-width:100% makes a
   wash span the full scroll width, not just the visible box. */
pre .dlw{display:block;width:max-content;min-width:100%}
/* block, NOT inline-block: `pre` sets white-space:pre, which disables wrapping, and an
   inline-level box only moves to a new line by wrapping — so inline-block put every line
   of the diff on one endless row. min-width does not break lines; only a block box does. */
pre .dl{display:block}
pre .dl:empty::after{content:"\00a0"}
pre .dl.ins{background:color-mix(in srgb, var(--success) 26%, transparent)}
pre .dl.rem{background:color-mix(in srgb, var(--primary) 22%, transparent)}
pre .dl.hunk{color:var(--warning);
  background:color-mix(in srgb, var(--neutral-content) 7%, transparent)}
pre .dl.meta{color:var(--code-dim)}

/* View toggle — the `.subtabs` component from shell.py, one step quieter than the
   top-level tabs so two segmented controls never compete. The inputs must stay direct
   siblings of .rounds for the sibling combinator below to reach the diffs, so they are
   not wrapped in a container — and shell.py splices this fragment in unwrapped for the
   same reason. */
input[name="v"]{position:absolute;opacity:0;pointer-events:none}
label[for^="v-"]{display:inline-flex;align-items:center;gap:7px;padding:6px 15px;
  margin:20px 0 0;cursor:pointer;border-radius:999px;user-select:none;
  color:var(--base-content-secondary);background:var(--base-200);
  border:1px solid transparent;font-family:var(--mono);font-size:var(--fs-small);
  font-weight:600}
label[for="v-split"]{margin-left:6px}
label[for^="v-"]:hover{color:var(--base-content)}
input[name="v"]:checked+label{background:var(--tab-fill);color:var(--base-content);
  border-color:var(--tab-edge)}
input[name="v"]:focus-visible+label{outline:2px solid var(--accent);outline-offset:2px}
table.sbs{display:none}
#v-split:checked~.rounds pre.uni{display:none}
#v-split:checked~.rounds table.sbs{display:table}

/* Portrait: two columns of code in a phone-width column is unreadable, so side by side
   is a wide-viewport affordance. The control is hidden and unified always wins — the
   radio keeps its state, so rotating to landscape restores the choice untouched. */
@media (max-width:699px){
  label[for^="v-"]{display:none}
  #v-split:checked~.rounds pre.uni{display:block}
  #v-split:checked~.rounds table.sbs{display:none}
}

/* Side-by-side. Sits on the same dark panel as the unified view, so the washes are
   mixed from the palette rather than invented: a tint of the token that already means
   added or removed, laid over the code surface. */
table.sbs{width:100%;table-layout:fixed;border-collapse:collapse;
  background:var(--neutral);font-family:var(--mono);font-size:var(--fs-code);
  line-height:var(--lh-code);border-top:1px solid var(--base-300)}
table.sbs col.cln{width:3.4em}
table.sbs td{vertical-align:top;padding:0 10px;color:var(--neutral-content);
  white-space:pre-wrap;overflow-wrap:anywhere}
table.sbs td.ln{text-align:right;color:var(--code-dim);
  font-variant-numeric:tabular-nums;user-select:none;padding:0 8px}
table.sbs td.tx.o{background:color-mix(in srgb, var(--primary) 22%, transparent)}
table.sbs td.tx.n{background:color-mix(in srgb, var(--success) 26%, transparent)}
table.sbs td.pad{background:color-mix(in srgb, var(--neutral-content) 4%, transparent)}
table.sbs td.hunkrow{color:var(--warning);padding:4px 10px;
  background:color-mix(in srgb, var(--neutral-content) 7%, transparent)}
"""

JS = """
<script>
// Remember the chosen view, so it survives the reload after every commit.
(function () {
  // Still the pre-merge key on purpose: renaming it would silently reset the toggle for
  // every learner who had already chosen side-by-side.
  var k = "snackbot-diffview-view";
  var uni = document.getElementById("v-uni"), spl = document.getElementById("v-split");
  if (localStorage.getItem(k) === "split") spl.checked = true;
  uni.addEventListener("change", function () { localStorage.setItem(k, "uni"); });
  spl.addEventListener("change", function () { localStorage.setItem(k, "split"); });
})();
</script>
"""


def signature():
    """HEAD is the whole story here — this page renders from commits and nothing else."""
    return core.git_head()


def render():
    found = core.course_commits()
    body = []
    for n in ROUNDS:
        anchors = []
        for phase, artifact, scope, what in PHASES:
            sha = found.get((n, phase))
            if not sha:
                continue
            d = scoped_diff(sha, scope)
            add, rm = counts(d)
            anchors.append(
                f'<details class="d" id="r{n}-{phase}">'
                f'<summary><span class="file">{html.escape(artifact)}</span>'
                f'<span class="what">{html.escape(what)}</span>'
                f'<span class="n"><b>+{add}</b> / <i>&minus;{rm}</i></span></summary>'
                f'<pre class="uni">{diff_html(d.rstrip()) or "(no change under this path)"}</pre>'
                f'{split_html(d.rstrip())}'
                f'</details>')
        inner = "".join(anchors) or (
            '<p class="pending">Not reached yet &mdash; this round&rsquo;s spec and code '
            'appear here once you commit them.</p>')
        body.append(
            f'<section class="round" id="r{n}">'
            f'<div class="rhead"><span class="rnum">{n}</span>'
            f'<span class="rttl">{html.escape(core.ROUND_TITLE[n])}</span></div>'
            f'{inner}</section>')

    if found:
        # Ordered the way the course runs — SPEC then BUILD — not alphabetically.
        order = sorted(found.items(), key=lambda kv: (kv[0][0], kv[0][1] != "spec"))
        items = "".join(f'<li><code>{sha[:7]}</code> round-{n} {ph}</li>'
                        for (n, ph), sha in order)
        state = (f'<details class="src"><summary>Built from {len(found)} commits in your '
                 f'git history</summary>'
                 f'<ul class="matched">{items}</ul>'
                 f'<p class="note">Each is a commit your tutor made at the end of a phase. '
                 f'The tutor and demo commits are not listed: they carry your answers and '
                 f'your recorded numbers rather than a change to the spec or the app.</p>'
                 f'</details>')
    else:
        state = ('<p class="state">No round committed yet &mdash; the course has not '
                 'started.</p>')

    return f"""<header>
  <h1>Your diffs, round by round</h1>
  <p class="sub">Every requirement you wrote, and every change it caused in the app.
  This reads your own git history, so it is always current &mdash; reload after any
  commit. Earlier rounds stay here; you can come back to Round 2 from Round 5.</p>
  {state}
</header>
<input type="radio" name="v" id="v-uni" checked><label for="v-uni">Unified</label>
<input type="radio" name="v" id="v-split"><label for="v-split">Side by side</label>
<div class="rounds">
{"".join(body)}
</div>"""
