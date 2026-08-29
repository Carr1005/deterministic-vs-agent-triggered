#!/usr/bin/env python3
"""shell.py — what every page's frame looks like. Nothing else.

The theme tokens, the shared component vocabulary, the tab bar, and the document that
wraps a view's fragment. It knows a view only through the small contract in
`views/__init__.py`: an id, a label, a title, a footer, some CSS and JS, and a body.

It emits no course knowledge of its own — where the diffs or the memory tables come from
is `core.py`'s business, and what they mean is the view's.
"""
import html

# A RAW string, deliberately. The CSS below contains `\25B8` and `\25BE` (the disclosure
# triangles), and in an ordinary Python string `\25` is an *octal* escape — the old
# tools/diffview/serve.py shipped a literal \x15 control character into its stylesheet
# for exactly this reason. Raw means what you type is what the browser gets.
CSS = r"""
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

/* Text tabs, underlined — deliberately NOT bordered pills. The diffs view carries a
   segmented Unified / Side-by-side control a few lines below this bar, and two adjacent
   pill groups would read as one control with two unrelated jobs. */
nav.tabs{display:flex;gap:24px;padding:26px 0 0;font-family:var(--mono);font-size:13px}
nav.tabs a{color:var(--faint);text-decoration:none;padding:0 1px 7px;
  border-bottom:2px solid transparent}
nav.tabs a:hover{color:var(--dim)}
nav.tabs a.on{color:var(--ink);font-weight:600;border-bottom-color:var(--petrol)}
nav.tabs a:focus-visible{outline:2px solid var(--brass);outline-offset:3px}

header{padding:26px 0 24px;border-bottom:1px solid var(--rule)}
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
p.note{margin:12px 0 0;font-size:13px;color:var(--faint);max-width:62ch}
.pending{color:var(--faint);font-size:14px;padding:14px 0 0;font-style:italic}
details.d{margin:16px 0 0;border:1px solid var(--rule);background:var(--surface)}
details.d>summary{cursor:pointer;padding:11px 14px;display:flex;gap:12px;
  align-items:baseline;font-family:var(--mono);font-size:13px;flex-wrap:wrap}
details.d>summary::-webkit-details-marker{display:none}
details.d>summary::before{content:"\25B8";color:var(--faint);flex:none}
details.d[open]>summary::before{content:"\25BE"}
.file{color:var(--ink);font-weight:600;flex:none}
.what{color:var(--dim);font-family:var(--sans);font-size:13px;flex:1;min-width:180px}
.n{font-variant-numeric:tabular-nums;flex:none;color:var(--faint)}
.n b{color:var(--moss);font-weight:600}
pre{margin:0;background:var(--sunken);color:var(--term-fg);font-family:var(--mono);
  font-size:12.5px;line-height:1.55;padding:14px;overflow-x:auto;white-space:pre;
  border-top:1px solid var(--rule)}
.add{color:var(--moss)}.del{color:var(--rust)}
.err{margin:24px 0 0;border:1px solid var(--rust);background:var(--surface);padding:16px}
.err h2{margin:0 0 8px;font-family:var(--mono);font-size:15px;color:var(--rust)}
.err p{margin:0 0 10px;color:var(--dim);font-size:14px;max-width:66ch}
footer{margin:56px 0 0;padding-top:20px;border-top:1px solid var(--rule);
  font-size:13px;color:var(--faint)}
footer code{font-family:var(--mono);font-size:12px}
"""

# Reload only when something actually changed, so scroll position and open cards survive.
# A view with no signature() gets no script at all — see views/diffs.py for why that is a
# feature rather than an omission.
POLL_JS = """
<script>
(function () {
  var cur = "__SIG__";
  setInterval(function () {
    fetch("/state/__ID__").then(function (r) { return r.text(); }).then(function (h) {
      if (h && h !== cur) location.reload();
    }).catch(function () {});   // server gone (idle reaper): go quiet, no errors
  }, 3000);
})();
</script>
"""


def tab_nav(active_id, views):
    links = []
    for v in views:
        on = ' class="on"' if v.ID == active_id else ""
        links.append(f'<a href="/{v.ID}"{on}>{html.escape(v.LABEL)}</a>')
    return f'<nav class="tabs">{"".join(links)}</nav>'


def error_card(view_id, exc):
    """What a view renders as when it raises. The tab bar stays above it.

    These views read a live git history and a live sqlite file, so they can meet states
    the code has never seen — a rebase in flight, a locked database, a half-written log
    line. A traceback in $TMPDIR and a dropped connection is a dead end for a learner;
    this leaves the other page one click away. A window, never a gate.
    """
    detail = html.escape("{}: {}".format(type(exc).__name__, exc))
    return ('<section class="err"><h2>This page could not be built</h2>'
            '<p>The rest of the viewer still works, and nothing about your course is '
            'affected — this page only reads.</p>'
            f'<pre>{detail}</pre></section>')


def page(view, views, body, signature):
    poll = "" if signature is None else (
        POLL_JS.replace("__SIG__", signature).replace("__ID__", view.ID))
    # The view's fragment is spliced in UNWRAPPED, as a direct child sequence of .wrap.
    # Do not add a container: views/diffs.py's toggle uses the general-sibling selector
    # `#v-split:checked~.rounds`, and a wrapper would silently break side-by-side while
    # leaving unified working — a failure nobody notices for weeks.
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(view.TITLE)}</title>
<style>{CSS}{view.CSS}</style></head><body>
<div class="wrap">
{tab_nav(view.ID, views)}
{body}
<footer>{view.FOOTER}</footer>
</div>
{poll}{view.JS}
</body></html>"""
