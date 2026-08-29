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
    add = sum(1 for l in diff.splitlines()
              if l.startswith("+") and not l.startswith("+++"))
    rm = sum(1 for l in diff.splitlines()
             if l.startswith("-") and not l.startswith("---"))
    return add, rm


def diff_html(diff):
    out = []
    for ln in diff.split("\n"):
        e = html.escape(ln)
        if ln.startswith("@@"):
            out.append(f'<span class="hunk">{e}</span>')
        elif ln.startswith("+") and not ln.startswith("+++"):
            out.append(f'<span class="add">{e}</span>')
        elif ln.startswith("-") and not ln.startswith("---"):
            out.append(f'<span class="del">{e}</span>')
        elif ln.startswith(("diff --git", "index ", "+++", "---")):
            out.append(f'<span class="meta">{e}</span>')
        else:
            out.append(e)
    return "\n".join(out)


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
  grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:2px 20px;
  font-family:var(--mono);font-size:12.5px;color:var(--dim);max-width:640px}
ul.matched code{background:none;border:0;padding:0;color:var(--petrol);font-weight:600}
.round{margin:44px 0 0}
.rhead{display:flex;gap:12px;align-items:baseline;border-bottom:1px solid var(--rule);
  padding-bottom:8px}
.rnum{font-family:var(--mono);font-size:20px;font-weight:600;color:var(--petrol);
  font-variant-numeric:tabular-nums}
.rttl{font-size:15px;color:var(--ink)}
.n i{color:var(--rust);font-style:normal;font-weight:600}
.hunk{color:var(--brass)}
.meta{color:var(--faint)}

/* View toggle. The inputs must stay direct siblings of .rounds for the sibling
   combinator below to reach the diffs, so they are not wrapped in a container — and
   shell.py splices this fragment in unwrapped for the same reason. */
input[name="v"]{position:absolute;opacity:0;pointer-events:none}
label[for^="v-"]{display:inline-block;border:1px solid var(--rule);padding:5px 12px;
  margin:20px 0 0;cursor:pointer;color:var(--dim);background:var(--surface);
  font-family:var(--mono);font-size:12px;user-select:none}
label[for="v-uni"]{border-radius:2px 0 0 2px}
label[for="v-split"]{border-radius:0 2px 2px 0;border-left:0;margin-left:-4px}
input[name="v"]:checked+label{background:var(--petrol);border-color:var(--petrol);color:#fff}
input[name="v"]:focus-visible+label{outline:2px solid var(--brass);outline-offset:1px}
table.sbs{display:none}
#v-split:checked~.rounds pre.uni{display:none}
#v-split:checked~.rounds table.sbs{display:table}

/* side-by-side. The code panel is dark in both themes, so these washes need no
   theme branching. */
table.sbs{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--sunken);
  font-family:var(--mono);font-size:12.5px;line-height:1.55;
  border-top:1px solid var(--rule)}
table.sbs col.cln{width:3.2em}
table.sbs td{vertical-align:top;padding:0 8px;color:var(--term-fg);
  white-space:pre-wrap;overflow-wrap:anywhere}
table.sbs td.ln{text-align:right;color:#5f6f72;font-variant-numeric:tabular-nums;
  user-select:none;padding:0 6px}
table.sbs td.tx.o{background:rgba(224,90,70,.16)}
table.sbs td.tx.n{background:rgba(110,190,90,.15)}
table.sbs td.pad{background:rgba(255,255,255,.028)}
table.sbs td.hunkrow{color:var(--brass);background:rgba(255,255,255,.05);padding:3px 8px}
"""

JS = """
<script>
// Remember the chosen view, so it survives the reload after every commit.
(function () {
  var k = "snackbot-diffview-view";
  var uni = document.getElementById("v-uni"), spl = document.getElementById("v-split");
  if (localStorage.getItem(k) === "split") spl.checked = true;
  uni.addEventListener("change", function () { localStorage.setItem(k, "uni"); });
  spl.addEventListener("change", function () { localStorage.setItem(k, "split"); });
})();
</script>
"""


def signature():
    """No auto-refresh, on purpose — this is a feature, not an omission.

    `location.reload()` collapses every <details> that was not rendered open, and this
    page is entirely closed-by-default cards. Polling would slam shut every diff the
    learner had opened, at exactly the moment a commit lands and they are most likely
    reading them. The guide page can poll because its two most-wanted cards render open.
    """
    return None


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
