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
/* Inserted by the poll script after the tab bar; never present in the served markup, so
   it cannot disturb the sibling chain views/diffs.py's toggle depends on. */
/* A status, not an error — neutral, and injected by script after the tab bar, so it is
   absent from the served markup and cannot disturb the sibling chain the diffs page's
   unified/side-by-side toggle depends on. */
.notice{margin:14px 0 0;padding:9px 13px;border:1px solid var(--rule);
  border-left:3px solid var(--faint);background:var(--surface);
  font-family:var(--mono);font-size:12.5px;color:var(--dim)}
.err{margin:24px 0 0;border:1px solid var(--rust);background:var(--surface);padding:16px}
.err h2{margin:0 0 8px;font-family:var(--mono);font-size:15px;color:var(--rust)}
.err p{margin:0 0 10px;color:var(--dim);font-size:14px;max-width:66ch}
footer{margin:56px 0 0;padding-top:20px;border-top:1px solid var(--rule);
  font-size:13px;color:var(--faint)}
footer code{font-family:var(--mono);font-size:12px}
"""

# Poll for change and rebuild the page when it moves, so a page left open follows the
# course on its own. A view with no signature() gets no script at all.
#
# Reloading would ordinarily throw away what the reader had opened — the diffs page is
# entirely closed-by-default <details> cards — so the open ones and the scroll position
# are stashed first and restored on the way back in. Cards are matched by id, which is
# why views give theirs stable ones.
#
# The poll doubles as the signal that keeps the server alive while a page is on screen
# (serve.py's /state route). It can still die under a page — a laptop asleep past the
# idle hour, or `serve.sh --stop` at the end of the day — and a page that simply goes
# quiet is indistinguishable from one that is up to date, so sustained silence says so.
POLL_JS = """
<script>
(function () {
  var cur = "__SIG__", key = "snackbot-open-__ID__", fails = 0, note = null;

  try {                                     // coming back from our own reload
    var was = JSON.parse(sessionStorage.getItem(key) || "null");
    if (was) {
      sessionStorage.removeItem(key);
      was.open.forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.open = true;
      });
      window.scrollTo(0, was.y);
    }
  } catch (e) {}

  function reload() {
    try {
      var open = [];
      Array.prototype.forEach.call(document.querySelectorAll("details[id]"), function (d) {
        if (d.open) open.push(d.id);
      });
      sessionStorage.setItem(key, JSON.stringify({ open: open, y: window.scrollY }));
    } catch (e) {}
    location.reload();
  }

  function check() {
    // The flag is what keeps the server alive while someone is actually reading, without
    // a tab forgotten in a background window doing the same. See serve.py's /state route.
    var seen = document.visibilityState !== "hidden";
    fetch("/state/__ID__" + (seen ? "?watching=1" : "")).then(function (r) {
      return r.text();
    }).then(function (h) {
      fails = 0;
      if (note) { note.remove(); note = null; }   // it answered again; stop saying it did not
      if (h && h !== cur) reload();
    }).catch(function () {
      // Only after 30s of silence. Restarting the server takes a second or two, and a
      // warning that flashes during an ordinary restart costs more trust than one that
      // arrives half a minute late.
      if (++fails === 10) {
        note = document.querySelector("nav.tabs")
          .insertAdjacentElement("afterend", document.createElement("div"));
        note.className = "notice";
        note.textContent = "The viewer has stopped, so this page is no longer updating.";
      }
    });
  }

  setInterval(check, 3000);
  // Coming back to a backgrounded tab: revive it and refresh at once, rather than
  // showing whatever was on screen for up to another three seconds.
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") check();
  });
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
