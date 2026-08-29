#!/usr/bin/env python3
"""serve.py — a live page of this learner's per-round diffs, on localhost.

Why it exists: the tutor shows each diff as terminal text from `git diff HEAD~1`, which
is transient and can only ever reach the round you are standing in. This serves every
round's spec change and code change at a stable URL, so a learner in Round 4 can still
look at what Round 2 did, and Round 3's ~110-line diff can be read in a page instead of
scrolled past.

Two invariants this file must never break:

  1. It writes NOTHING into the repository. `git status --porcelain` is the tutor's
     mid-round resume signal, and course/PROTOCOL.md's resume table has exactly two legal
     values for the working-tree column. Every page is built as a string, per request.
  2. It uses only the standard library, so setup/requirements.txt and setup/check.sh
     stay untouched and nobody mid-course has to re-bootstrap.

Read-only: it runs `git log`, `git diff` and `git show`, and nothing else.
"""
import argparse
import html
import http.server
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

HEALTH_TOKEN = "snackbot-diffview-ok"
ROUNDS = (1, 2, 3, 4, 5)
# The same commit-name pattern setup/bootstrap.sh uses to decide if a course has started.
COURSE_COMMIT = re.compile(r"^round-([1-5]) (spec|build)$")

# What each round is about, so the page is legible to someone mid-course.
ROUND_TITLE = {
    1: "The meter — instrument before you optimise",
    2: "Deterministic memory — code invokes, every turn",
    3: "Agent-triggered memory — the model invokes, via tools",
    4: "Counting — one passing run proves nothing",
    5: "The per-operation decision — pin exactly one read",
}
# Which artifact each phase commit carries (course/PROTOCOL.md's table), and the path the
# diff must be scoped to. Scoping is required: round-1/build.md warns in its own words
# that "commits carry other artifacts too".
PHASES = (
    ("spec", "spec/spec.md", "spec/", "the requirement you argued into existence"),
    ("build", "src/snackbot.py", "src/", "the code that requirement demanded"),
)

REPO = Path(__file__).resolve().parent.parent.parent


# Neutralise whatever git configuration we happen to inherit, so the page renders the
# same text on every machine. Two problems, two different mechanisms:
#
#   colour   `color.ui = always` puts ANSI escapes into captured output (measured: 66
#            lines of escape codes). `-c color.ui=false` outranks any config file.
#   external a `diff.external` driver — delta, difftastic — replaces git's diff with its
#            own output. The fix is the `--no-ext-diff` flag on the diff-producing
#            commands, NOT `-c diff.external=`: an empty value makes git try to execute
#            the empty string and exit 128, which silently emptied every diff. The flag
#            also covers the GIT_EXTERNAL_DIFF environment variable, which no amount of
#            `-c` can reach.
GIT_FLAGS = ("-c", "color.ui=false")
NO_EXT = ("--no-ext-diff",)      # valid on diff/show/log; not on rev-parse
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS")


def git_env():
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    # POSIX-only, which matches the course's "use WSL on Windows" guidance.
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    return env


def git(*args):
    """Run git in the repo and return stdout. Never raises on a non-zero exit."""
    r = subprocess.run(("git", "-C", str(REPO)) + GIT_FLAGS + args,
                       capture_output=True, text=True, env=git_env())
    return r.stdout if r.returncode == 0 else ""


def course_commits():
    """{(round, phase): sha} for every phase commit the learner has made so far."""
    found = {}
    for line in git("log", "--format=%H%x00%s").splitlines():
        sha, _, subject = line.partition("\x00")
        m = COURSE_COMMIT.match(subject.strip())
        if m:
            found.setdefault((int(m.group(1)), m.group(2)), sha)
    return found


def scoped_diff(sha, path):
    """The change this commit made under `path`, or "" if it has no parent."""
    if not git("rev-parse", "--verify", "--quiet", f"{sha}^"):
        return git("show", *NO_EXT, "--format=", sha, "--", path)
    return git("diff", *NO_EXT, f"{sha}~1", sha, "--", path)


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
.sub{color:var(--dim);max-width:66ch;margin:0;font-size:15px}
.state{margin:20px 0 0;font-family:var(--mono);font-size:12.5px;color:var(--faint)}
details.src{margin:18px 0 0}
details.src>summary{cursor:pointer;font-family:var(--mono);font-size:12.5px;
  color:var(--faint);list-style:none;display:inline-flex;gap:8px;align-items:baseline}
details.src>summary::-webkit-details-marker{display:none}
details.src>summary::before{content:"\25B8"}
details.src[open]>summary::before{content:"\25BE"}
details.src>summary:hover{color:var(--dim)}
ul.matched{list-style:none;margin:10px 0 0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:2px 20px;
  font-family:var(--mono);font-size:12.5px;color:var(--dim);max-width:640px}
ul.matched code{background:none;border:0;padding:0;color:var(--petrol);font-weight:600}
p.note{margin:12px 0 0;font-size:13px;color:var(--faint);max-width:62ch}
.round{margin:44px 0 0}
.rhead{display:flex;gap:12px;align-items:baseline;border-bottom:1px solid var(--rule);
  padding-bottom:8px}
.rnum{font-family:var(--mono);font-size:20px;font-weight:600;color:var(--petrol);
  font-variant-numeric:tabular-nums}
.rttl{font-size:15px;color:var(--ink)}
.pending{color:var(--faint);font-size:14px;padding:14px 0 0;font-style:italic}
details.d{margin:16px 0 0;border:1px solid var(--rule);background:var(--surface)}
details.d>summary{cursor:pointer;padding:11px 14px;display:flex;gap:12px;
  align-items:baseline;font-family:var(--mono);font-size:13px}
details.d>summary::-webkit-details-marker{display:none}
details.d>summary::before{content:"\\25B8";color:var(--faint);flex:none}
details.d[open]>summary::before{content:"\\25BE"}
.file{color:var(--ink);font-weight:600;flex:none}
.what{color:var(--dim);font-family:var(--sans);font-size:13px;flex:1}
.n{font-variant-numeric:tabular-nums;flex:none;color:var(--faint)}
.n b{color:var(--moss);font-weight:600}.n i{color:var(--rust);font-style:normal;font-weight:600}
pre{margin:0;background:var(--sunken);color:var(--term-fg);font-family:var(--mono);
  font-size:12.5px;line-height:1.55;padding:14px;overflow-x:auto;white-space:pre;
  border-top:1px solid var(--rule)}
.add{color:var(--moss)}.del{color:var(--rust)}.hunk{color:var(--brass)}
.meta{color:var(--faint)}

/* View toggle. The inputs must stay direct siblings of .rounds for the sibling
   combinator below to reach the diffs, so they are not wrapped in a container. */
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
footer{margin:56px 0 0;padding-top:20px;border-top:1px solid var(--rule);
  font-size:13px;color:var(--faint)}
footer code{font-family:var(--mono);font-size:12px}
"""


def page():
    found = course_commits()
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
            f'<span class="rttl">{html.escape(ROUND_TITLE[n])}</span></div>'
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
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Your diffs, round by round</title>
<style>{CSS}</style></head><body>
<div class="wrap">
<header>
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
<footer>Read-only. Served from <code>tools/diffview/serve.py</code>; writes nothing.
Stop it with <code>bash tools/diffview/serve.sh --stop</code>.</footer>
</div>
<script>
// Remember the chosen view, so it survives the reload after every commit.
(function () {{
  var k = "snackbot-diffview-view";
  var uni = document.getElementById("v-uni"), spl = document.getElementById("v-split");
  if (localStorage.getItem(k) === "split") spl.checked = true;
  uni.addEventListener("change", function () {{ localStorage.setItem(k, "uni"); }});
  spl.addEventListener("change", function () {{ localStorage.setItem(k, "split"); }});
}})();
</script>
</div></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "snackbot-diffview"

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self.server.last_seen = time.time()
        if self.path.startswith("/healthz"):
            self._send(200, HEALTH_TOKEN, "text/plain; charset=utf-8")
        elif self.path.split("?")[0] in ("/", "/index.html"):
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
    ap.add_argument("--port", type=int, default=4000)
    ap.add_argument("--idle", type=int, default=60,
                    help="shut down after N idle minutes (0 disables)")
    a = ap.parse_args()

    if not git("rev-parse", "--git-dir"):
        print(f"FAIL  {REPO} is not a git repository — nothing to diff.")
        return 1
    try:
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    except OSError as e:
        print(f"FAIL  cannot bind port {a.port}: {e}")
        return 1
    httpd.last_seen = time.time()
    threading.Thread(target=reaper, args=(httpd, a.idle), daemon=True).start()
    print(f"PASS  diffview on http://localhost:{a.port}/  (idle timeout {a.idle} min)")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nNOTE  stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
