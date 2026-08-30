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
/* ---------------------------------------------------------------- tokens ---------
   Tier 1 semantic tokens are the only colours in this stylesheet. Nothing below this
   block writes a hex value: anything that needs a lighter or tinted variant derives it
   with color-mix() from a token, so the palette stays the single source of truth.

   Contrast was measured, not eyeballed, and it shaped two decisions. `warning` fails
   WCAG AA on every light surface here (2.7:1), so orange is only ever a fill or a
   border on light, never small text. `accent` reaches 4.1:1 on white — under AA for
   body sizes — so an active tab is signalled by its FILL and weight, with the label
   left at `base-content`, rather than by colouring the text. On the dark code panel
   success / primary / warning all clear AA (5.4, 5.6, 6.4), which is why the code
   blocks keep their colours unchanged. */
:root{
  --primary:#F65B66;      --primary-content:#FEF2F2;
  --secondary:#0891B2;    --secondary-content:#CFFAFE;
  --accent:#0284C7;       --accent-content:#E0F2FE;
  --base-100:#FFFFFF;     --base-150:#F8FAFC;
  --base-200:#F1F5F9;     --base-300:#E2E8F0;
  --base-content:#0F172A; --base-content-secondary:#64748B;
  --neutral:#171717;      --neutral-content:#E5E5E5;
  --success:#16A34A;      --success-content:#DCFCE7;
  --warning:#F97316;      --warning-content:#FFEDD5;
  --info:#9333EA;         --info-content:#F3E8FF;

  /* derived, so no second palette creeps in */
  --code-dim:color-mix(in srgb, var(--neutral-content) 58%, var(--neutral));
  --tab-fill:color-mix(in srgb, var(--accent) 14%, var(--base-100));
  --tab-edge:color-mix(in srgb, var(--accent) 28%, var(--base-100));
  --hairline:color-mix(in srgb, var(--base-300) 70%, var(--base-100));
  /* `success` and `primary` are only ~3.2:1 on a white card — below AA for the small
     bold marks that use them. Darkened toward the body ink they reach 5.3 and 6.3. */
  --success-ink:color-mix(in srgb, var(--success) 72%, var(--base-content));
  --danger-ink:color-mix(in srgb, var(--primary) 62%, var(--base-content));
  /* accent is 3.9:1 on the page — fine for a large numeral, under AA for small text,
     so anything set small uses the darkened ink instead. One blue family, two weights
     of it, and no second hue. */
  --accent-ink:color-mix(in srgb, var(--accent) 80%, var(--base-content));

  --mono:ui-monospace,"SF Mono",SFMono-Regular,"JetBrains Mono",Menlo,Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;

  /* Type scale. Code is 14px/1.62 — the size editors and code hosts settle on, and a
     real step up from the 12.5px this page used to serve. */
  --fs-code:14px;   --lh-code:1.62;
  --fs-body:16px;   --fs-small:13.5px;   --fs-label:15px;
  --wrap:1100px;    --gutter:16px;

  /* Sticky bar heights, declared rather than measured: the secondary bar parks exactly
     below the primary one, and an anchored target clears both. A view with a secondary
     bar sets --sub-h from its own stylesheet; the guide has none, so it stays 0. */
  --bar-top-h:60px; --sub-h:0px;
}

/* ---------------------------------------------------------------- shell ----------
   Portrait first: one column, full-bleed padding, nothing that needs width to work.
   Wider viewports widen the measure in steps rather than stretching prose lines. */
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--base-150);color:var(--base-content);
  font-family:var(--sans);font-size:var(--fs-body);line-height:1.6;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:var(--wrap);margin:0 auto;padding:0 var(--gutter) 72px}
@media (min-width:700px){ :root{--gutter:28px} .wrap{padding-bottom:88px} }

/* A URL anchor scrolls its target to the very top, which is precisely where the sticky
   bars are — so every anchorable thing reserves their height. Without this, a deep link
   from the tutor lands with the card it named hidden behind the tabs. */
.round,details.d{scroll-margin-top:calc(var(--bar-top-h) + var(--sub-h) + 14px)}

/* The bars are full-bleed: they cancel the wrap's gutter so nothing scrolls through the
   margins beside a rounded pill. */
.bar{position:sticky;z-index:30;display:flex;align-items:center;
  margin:0 calc(var(--gutter) * -1);padding:0 var(--gutter);
  background:var(--base-150);border-bottom:1px solid var(--base-300)}
.bar-top{top:0;height:var(--bar-top-h)}
/* the pill is a flex child now, so it must be told to fill the bar — otherwise it
   collapses to its own content and the full-width tabs stop being full width */
.bar-top>nav.tabs{flex:1 1 auto;min-width:0}
@media (min-width:1500px){ :root{--wrap:1320px} }

/* ---------------------------------------------------------------- tabs -----------
   A segmented control: the bar is one tinted track, the active segment a filled pill.
   Full-width halves in portrait, content-width on wider screens so it does not stretch
   into a banner. `.subtabs` is the same component one step quieter — the guide page's
   secondary navigation drops straight into it. */
nav.tabs{display:flex;gap:4px;padding:4px;
  background:var(--base-200);border:1px solid var(--base-300);border-radius:999px}
@media (min-width:1200px){ .bar-top>nav.tabs{flex:0 0 auto;display:inline-flex} }
nav.tabs a{flex:1 1 0;display:inline-flex;align-items:center;justify-content:center;
  gap:9px;padding:10px 20px;border-radius:999px;text-decoration:none;
  font-size:var(--fs-label);font-weight:600;color:var(--base-content-secondary);
  white-space:nowrap;transition:background .15s,color .15s}
nav.tabs a:hover{color:var(--base-content)}
nav.tabs a.on{background:var(--tab-fill);color:var(--base-content);
  box-shadow:inset 0 0 0 1px var(--tab-edge)}
nav.tabs a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
nav.tabs svg{width:17px;height:17px;flex:none}
nav.tabs a .dot{display:inline-flex;align-items:center;justify-content:center;
  width:22px;height:22px;border-radius:999px;background:transparent;flex:none}
nav.tabs a.on .dot{background:var(--base-content);color:var(--base-100)}

nav.subtabs{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 0}
nav.subtabs a{display:inline-flex;align-items:center;gap:7px;padding:6px 14px;
  border-radius:999px;text-decoration:none;font-size:var(--fs-small);font-weight:600;
  color:var(--base-content-secondary);background:var(--base-200);
  border:1px solid transparent}
nav.subtabs a:hover{color:var(--base-content)}
nav.subtabs a.on{background:var(--tab-fill);color:var(--base-content);
  border-color:var(--tab-edge)}
nav.subtabs a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* ---------------------------------------------------------------- header ---------- */
header{padding:26px 0 22px;border-bottom:1px solid var(--base-300)}
h1{font-family:var(--mono);font-size:clamp(25px,5.2vw,33px);letter-spacing:-.022em;
  font-weight:650;margin:0 0 12px;line-height:1.18;text-wrap:balance}
.sub{color:var(--base-content-secondary);max-width:64ch;margin:0;font-size:15.5px}
.state{margin:18px 0 0;font-family:var(--mono);font-size:var(--fs-small);
  color:var(--base-content-secondary)}
details.src{margin:16px 0 0}
details.src>summary{cursor:pointer;font-family:var(--mono);font-size:var(--fs-small);
  color:var(--base-content-secondary);list-style:none;display:inline-flex;gap:8px;
  align-items:baseline}
details.src>summary::-webkit-details-marker{display:none}
details.src>summary::before{content:"\25B8"}
details.src[open]>summary::before{content:"\25BE"}
details.src>summary:hover{color:var(--base-content)}
p.note{margin:12px 0 0;font-size:var(--fs-small);color:var(--base-content-secondary);
  max-width:62ch}
.pending{color:var(--base-content-secondary);font-size:15px;padding:16px 0 0;
  font-style:italic}

/* ---------------------------------------------------------------- cards ----------- */
details.d{margin:14px 0 0;border:1px solid var(--base-300);background:var(--base-100);
  border-radius:12px;overflow:hidden}
details.d>summary{cursor:pointer;padding:13px 16px;display:flex;gap:12px;
  align-items:baseline;font-family:var(--mono);font-size:var(--fs-small);
  flex-wrap:wrap}
details.d>summary::-webkit-details-marker{display:none}
details.d>summary::before{content:"\25B8";color:var(--base-content-secondary);flex:none}
details.d[open]>summary::before{content:"\25BE"}
details.d>summary:hover{background:var(--base-150)}
.file{color:var(--base-content);font-weight:650;flex:none}
.what{color:var(--base-content-secondary);font-family:var(--sans);
  font-size:var(--fs-small);flex:1;min-width:180px}
.n{font-variant-numeric:tabular-nums;flex:none;color:var(--base-content-secondary)}
.n b{color:var(--success-ink);font-weight:650}

/* ---------------------------------------------------------------- code -----------
   The dark panel survives the palette because the palette ships one: `neutral` with
   `neutral-content` is the token pair meant for dark surfaces, so this is inside the
   system rather than an exception to it. */
pre{margin:0;background:var(--neutral);color:var(--neutral-content);
  font-family:var(--mono);font-size:var(--fs-code);line-height:var(--lh-code);
  padding:16px;overflow-x:auto;white-space:pre;
  border-top:1px solid var(--base-300);
  -webkit-font-smoothing:auto;font-variant-ligatures:none;tab-size:4}
.add{color:var(--success-content)}
.del{color:var(--primary)}

/* ---------------------------------------------------------------- notice ---------
   A status, not an error — injected by script after the tab bar, so it is absent from
   the served markup and cannot disturb the sibling chain the diffs page's
   unified/side-by-side toggle depends on. */
.notice{margin:14px 0 0;padding:11px 15px;border:1px solid var(--base-300);
  border-left:3px solid var(--warning);background:var(--base-100);border-radius:10px;
  font-family:var(--mono);font-size:var(--fs-small);
  color:var(--base-content-secondary)}
.err{margin:22px 0 0;border:1px solid var(--base-300);border-left:3px solid var(--primary);
  background:var(--base-100);padding:18px;border-radius:12px}
.err h2{margin:0 0 8px;font-family:var(--mono);font-size:16px;color:var(--base-content)}
.err p{margin:0 0 12px;color:var(--base-content-secondary);font-size:15px;max-width:64ch}
footer{margin:56px 0 0;padding-top:20px;border-top:1px solid var(--base-300);
  font-size:var(--fs-small);color:var(--base-content-secondary)}
footer code{font-family:var(--mono);font-size:13px}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
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
    // `=== "visible"`, not `!== "hidden"`: were the API ever missing, the negative form
    // would send the flag forever and keep a forgotten tab's server alive, which is the
    // one thing it exists to prevent. Absent means "do not count", the safe direction.
    var seen = document.visibilityState === "visible";
    fetch("/state/__ID__" + (seen ? "?watching=1" : "")).then(function (r) {
      return r.text();
    }).then(function (h) {
      fails = 0;
      if (note) { note.remove(); note = null; }   // it answered again; stop saying it did not
      if (h && h !== cur) reload();
    }).catch(function () {
      // Ten failed polls — 30s at the interval, sooner if a tab switch checks off
      // cadence. Restarting the server takes a second or two, and a warning that flashes
      // during an ordinary restart costs more trust than one that arrives late.
      if (++fails === 10) {
        var anchor = document.querySelector(".bar-top") ||
                     document.querySelector("nav.tabs");
        note = anchor.insertAdjacentElement("afterend", document.createElement("div"));
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


# Two 17px line icons, inline because the page must work with no network and no
# external asset. A view may name its own with an ICON attribute; these are the
# fallbacks, keyed by view id.
ICONS = {
    "diffs": '<path d="M3.5 6.5h6M6.5 3.5v6M10.5 14.5h6" stroke="currentColor" '
             'stroke-width="1.8" stroke-linecap="round" fill="none"/>',
    "guide": '<path d="M3 4.5h5a2 2 0 0 1 2 2V15a1.6 1.6 0 0 0-1.6-1.6H3zM17 4.5h-5a2 2 '
             '0 0 0-2 2V15a1.6 1.6 0 0 1 1.6-1.6H17z" stroke="currentColor" '
             'stroke-width="1.5" fill="none" stroke-linejoin="round"/>',
}
FALLBACK_ICON = ('<circle cx="10" cy="10" r="6.5" stroke="currentColor" '
                 'stroke-width="1.6" fill="none"/>')


def _icon(view):
    body = getattr(view, "ICON", None) or ICONS.get(view.ID, FALLBACK_ICON)
    return f'<svg viewBox="0 0 20 20" aria-hidden="true">{body}</svg>'


def tab_nav(active_id, views):
    """The top-level segmented control: one tinted track, the active segment filled."""
    links = []
    for v in views:
        on = " on" if v.ID == active_id else ""
        cur = ' aria-current="page"' if v.ID == active_id else ""
        links.append(f'<a class="tab{on}" href="/{v.ID}"{cur}>'
                     f'<span class="dot">{_icon(v)}</span>{html.escape(v.LABEL)}</a>')
    return f'<nav class="tabs" aria-label="Views">{"".join(links)}</nav>'


def subtab_nav(items, active=None):
    """Secondary navigation *within* a view — the guide page's sections, shortly.

    Same component one step quieter, so a view gains sub-navigation without inventing
    another control. `items` is (id, label, href) triples.
    """
    out = []
    for ident, label, href in items:
        on = " on" if ident == active else ""
        cur = ' aria-current="true"' if ident == active else ""
        out.append(f'<a class="subtab{on}" href="{href}"{cur}>{html.escape(label)}</a>')
    return f'<nav class="subtabs" aria-label="Sections">{"".join(out)}</nav>'


def error_card(exc):
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
<div class="bar bar-top">{tab_nav(view.ID, views)}</div>
{body}
<footer>{view.FOOTER}</footer>
</div>
{poll}{view.JS}
</body></html>"""
