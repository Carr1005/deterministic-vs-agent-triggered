#!/usr/bin/env python3
"""Render raw.jsonl (a Claude Code session log) into a readable HTML transcript.

EXTRACTION RULE — edit these two regexes to change what the page shows:
  RUN          commands whose output is expanded by default (it ran something)
  DROP_OUTPUT  commands whose output is hidden (the tutor reading its own files)
Everything else: learner turns, tutor turns, every command line, and all other
tool output, collapsed.
"""
import json, re, html

RUN = re.compile(r'src/snackbot\.py|setup/show_memory|setup/reset_memory'
                 r'|verify\.sh|git (?:--no-pager )?diff|git log|bootstrap\.sh|--x5')
DROP_OUTPUT = re.compile(
    r'^\s*(?:cat|sed -n|head|tail)\b(?![^\n]*-n src/)[^\n]*'
    r'(?:PROTOCOL\.md|questions\.md|tutor-notes\.md|build\.md|demo\.md'
    r'|answers\.md|spec/spec\.md|demo-log\.md)'
    r'|^\s*ls -d|^\s*cp course/rounds|^\s*cat > /private/tmp')

def inline(s):
    s = html.escape(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\[(R\d\s·\s[A-Z]+)\]', r'<span class="tag">\1</span>', s)
    s = re.sub(r'<code>(<span class="tag">[^<]+</span>)</code>', r'\1', s)
    return s

def code_body(t):
    """Colour diff hunks only when the block really is a diff; always highlight
    PASS/FAIL and the [meter] line, which are what the learner reacts to."""
    is_diff = ('@@' in t) or ('diff --git' in t)
    out = []
    for ln in t.split("\n"):
        e = html.escape(ln)
        if is_diff:
            if ln.startswith("@@"):
                out.append(f'<span class="hunk">{e}</span>'); continue
            if ln.startswith("+") and not ln.startswith("+++"):
                out.append(f'<span class="add">{e}</span>'); continue
            if ln.startswith("-") and not ln.startswith("---"):
                out.append(f'<span class="del">{e}</span>'); continue
        e = re.sub(r'\b(PASS|SAFE)\b', r'<span class="ok">\1</span>', e)
        e = re.sub(r'\b(FAIL|UNSAFE|WARN)\b', r'<span class="bad">\1</span>', e)
        e = re.sub(r'(\[meter\].*)$', r'<span class="meter">\1</span>', e)
        out.append(e)
    return "\n".join(out)

def md(t):
    out, i, L = [], 0, t.split("\n")
    while i < len(L):
        ln = L[i]
        if ln.startswith("```"):
            buf = []; i += 1
            while i < len(L) and not L[i].startswith("```"):
                buf.append(L[i]); i += 1
            i += 1
            out.append(f'<pre class="code">{code_body(chr(10).join(buf))}</pre>'); continue
        if re.match(r'^\s*[-*]\s+', ln):
            items = []
            while i < len(L) and re.match(r'^\s*[-*]\s+', L[i]):
                items.append(inline(re.sub(r'^\s*[-*]\s+', '', L[i]))); i += 1
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"); continue
        if re.match(r'^\s*\d+\.\s+', ln):
            items = []
            while i < len(L) and re.match(r'^\s*\d+\.\s+', L[i]):
                items.append(inline(re.sub(r'^\s*\d+\.\s+', '', L[i]))); i += 1
            out.append("<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"); continue
        if ln.startswith(">"):
            buf = []
            while i < len(L) and L[i].startswith(">"):
                buf.append(L[i].lstrip("> ")); i += 1
            out.append(f"<blockquote>{inline(' '.join(buf))}</blockquote>"); continue
        m = re.match(r'^(#{1,4})\s+(.*)', ln)
        if m:
            out.append(f"<h4>{inline(m.group(2))}</h4>"); i += 1; continue
        if not ln.strip():
            i += 1; continue
        buf = []
        while i < len(L) and L[i].strip() and not L[i].startswith(("```", ">", "#")) \
              and not re.match(r'^\s*(?:[-*]|\d+\.)\s+', L[i]):
            buf.append(L[i]); i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")
    return "".join(out)

def load(path="raw.jsonl"):
    """Return an ordered list of events: learner / tutor / tool."""
    results, events = {}, []
    recs = []
    for line in open(path):
        try: recs.append(json.loads(line))
        except Exception: pass
    for o in recs:
        c = (o.get("message") or {}).get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    t = b.get("content")
                    if isinstance(t, list):
                        t = "\n".join(x.get("text", "") for x in t if isinstance(x, dict))
                    results[b.get("tool_use_id")] = t or ""
    n = 0
    for o in recs:
        if o.get("type") not in ("user", "assistant") or o.get("isMeta"): continue
        role = (o.get("message") or {}).get("role")
        c = (o.get("message") or {}).get("content")
        blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c if isinstance(c, list) else [])
        for b in blocks:
            if not isinstance(b, dict): continue
            if b.get("type") == "text":
                t = (b.get("text") or "").strip()
                if not t or t.startswith(("<system-reminder>", "<command-", "<local-command", "Caveat:")):
                    continue
                events.append({"kind": "learner" if role == "user" else "tutor", "text": t})
            elif b.get("type") == "tool_use":
                n += 1
                inp = b.get("input") or {}
                cmd = inp.get("command") or inp.get("file_path") or ""
                events.append({"kind": "tool", "n": n, "name": b.get("name", "?"),
                               "cmd": cmd, "out": results.get(b.get("id"), ""),
                               "show": not DROP_OUTPUT.search(cmd),
                               "open": bool(RUN.search(cmd))})
    return events

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --ink:#151a1c; --dim:#5c6a6d; --faint:#8a979a;
  --ground:#f4f6f5; --surface:#ffffff; --sunken:#1b2225; --rule:#d8dedb;
  --petrol:#175c68; --brass:#8f6a15; --moss:#3f6b2e; --rust:#9a3b2e;
  --term-fg:#c9d4d3; --term-dim:#7d8c8e;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#e3e9e8; --dim:#96a4a6; --faint:#6d7b7e;
  --ground:#101517; --surface:#161d1f; --sunken:#0a0e10; --rule:#26302f;
  --petrol:#6fb9c4; --brass:#d9a83a; --moss:#8ec26f; --rust:#e59480;
  --term-fg:#c9d4d3; --term-dim:#7d8c8e;
}}
:root[data-theme="dark"]{
  --ink:#e3e9e8; --dim:#96a4a6; --faint:#6d7b7e;
  --ground:#101517; --surface:#161d1f; --sunken:#0a0e10; --rule:#26302f;
  --petrol:#6fb9c4; --brass:#d9a83a; --moss:#8ec26f; --rust:#e59480;
  --term-fg:#c9d4d3; --term-dim:#7d8c8e;
}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;padding:0 24px 96px}

header.top{padding:64px 0 32px;border-bottom:1px solid var(--rule)}
h1{font-family:var(--mono);font-size:clamp(26px,4.2vw,40px);letter-spacing:-.02em;
  font-weight:600;margin:0 0 12px;text-wrap:balance}
.sub{color:var(--dim);max-width:64ch;margin:0}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));
  gap:1px;background:var(--rule);border:1px solid var(--rule);margin:32px 0 0}
.fact{background:var(--surface);padding:14px 16px}
.fact b{display:block;font-family:var(--mono);font-size:21px;font-weight:600;
  font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.fact span{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:var(--faint)}

nav.idx{margin:32px 0 0;font-family:var(--mono);font-size:13px}
nav.idx a{display:inline-block;color:var(--petrol);text-decoration:none;
  padding:4px 10px;border:1px solid var(--rule);margin:0 6px 6px 0;border-radius:2px}
nav.idx a:hover,nav.idx a:focus-visible{border-color:var(--petrol);outline:none}

.phase{position:sticky;top:0;z-index:5;background:var(--ground);
  border-bottom:1px solid var(--rule);padding:14px 0 10px;margin:56px 0 0}
.phase h2{font-family:var(--mono);font-size:15px;font-weight:600;margin:0;
  letter-spacing:.02em;color:var(--petrol)}
.phase p{margin:2px 0 0;font-size:12.5px;color:var(--faint)}

.turn{display:grid;grid-template-columns:76px minmax(0,1fr);gap:20px;
  padding:22px 0;border-bottom:1px solid var(--rule)}
.who{font-family:var(--mono);font-size:11px;text-transform:uppercase;
  letter-spacing:.08em;color:var(--faint);padding-top:5px;
  display:flex;flex-direction:column;align-items:flex-start;gap:7px}
.who .tag{text-transform:none;letter-spacing:0}
.turn.learner .who{color:var(--petrol)}
.turn.learner .body{border-left:2px solid var(--petrol);padding-left:16px}
.body>*:first-child{margin-top:0}.body>*:last-child{margin-bottom:0}
.body{min-width:0;max-width:70ch}
.body p{margin:0 0 12px}
.body ul,.body ol{margin:0 0 12px;padding-left:22px}
.body li{margin:0 0 5px}
.body h4{font-size:15px;margin:18px 0 8px;font-weight:600}
.body blockquote{margin:0 0 12px;padding:2px 0 2px 14px;border-left:2px solid var(--rule);
  color:var(--dim)}
code{font-family:var(--mono);font-size:.88em;background:var(--surface);
  border:1px solid var(--rule);border-radius:2px;padding:.08em .3em}
.tag{font-family:var(--mono);font-size:11px;font-weight:600;color:var(--petrol);
  border:1px solid var(--petrol);border-radius:2px;padding:.1em .4em;white-space:nowrap}

.tool{margin:22px 0;border:1px solid var(--rule);background:var(--surface)}
.tool>summary{cursor:pointer;padding:9px 14px;font-family:var(--mono);font-size:12.5px;
  color:var(--dim);display:flex;gap:10px;align-items:baseline}
.tool>summary::-webkit-details-marker{display:none}
.tool>summary::before{content:"▸";color:var(--faint);flex:none}
.tool[open]>summary::before{content:"▾"}
.tool>summary .cmd{color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tool>summary .no{color:var(--faint);flex:none;font-variant-numeric:tabular-nums}
.noout{border-style:dashed;background:none}
pre.code,pre.out{margin:0;background:var(--sunken);color:var(--term-fg);
  font-family:var(--mono);font-size:12.5px;line-height:1.55;padding:14px;
  overflow-x:auto;white-space:pre;border-top:1px solid var(--rule)}
.body pre.code{border:1px solid var(--rule);border-radius:2px;margin:0 0 12px}
.add{color:var(--moss)}.del{color:var(--rust)}.hunk{color:var(--brass)}
.ok{color:var(--moss);font-weight:600}.bad{color:var(--rust);font-weight:600}
.meter{color:var(--brass)}
footer{margin:72px 0 0;padding-top:24px;border-top:1px solid var(--rule);
  font-size:13px;color:var(--faint)}

.fig{margin:40px 0 0;padding:0}
.fig svg{max-width:100%;height:auto;color:var(--ink);display:block}
.fig svg text{font-family:var(--mono)}
.fig svg .band{font-size:10px;letter-spacing:.1em;fill:var(--faint)}
.fig svg .n{font-size:12px;font-weight:600;fill:var(--ink)}
.fig svg .d{font-size:10.5px;fill:var(--dim)}
.fig svg .e{font-size:10px;fill:var(--faint)}
.fig svg .p{font-size:13px;font-weight:600;fill:var(--ink);text-anchor:middle;letter-spacing:.04em}
.fig svg .a{font-size:11.5px;fill:var(--dim);text-anchor:middle}
.fig svg .ac{font-size:11.5px;font-weight:600;fill:var(--petrol);text-anchor:middle}
.fig svg .w{font-size:10px;fill:var(--faint);text-anchor:middle}
.fig svg .ro{fill:none;stroke:var(--rule);stroke-dasharray:3 3}
.fig svg .ph{fill:var(--surface);stroke:var(--rule)}
.fig figcaption{margin:14px 0 0;font-size:13px;color:var(--dim);max-width:70ch}
.fig svg .s{font-family:var(--sans);font-size:11px;fill:var(--dim);text-anchor:middle}
.fig svg .k{font-size:9.5px;fill:var(--petrol);text-anchor:middle;letter-spacing:.02em}
.fig svg .ex{fill:none;stroke:var(--rule)}
.fig svg .dash{fill:none;stroke:currentColor;stroke-dasharray:3 3}
.rt{width:100%;border-collapse:collapse;margin:40px 0 0;font-size:14px}
.rt caption{text-align:left;font-family:var(--mono);font-size:10px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--faint);padding:0 0 8px}
.rt th,.rt td{border:1px solid var(--rule);padding:9px 12px;text-align:left;vertical-align:top}
.rt thead th{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;color:var(--faint);background:var(--surface)}
.rt tbody th{font-family:var(--mono);font-size:15px;width:60px;color:var(--dim)}
.rt td b{display:block;font-family:var(--mono);font-variant-numeric:tabular-nums;
  font-size:14px;color:var(--petrol)}
.rt td span{display:block;font-size:12.5px;color:var(--dim);margin-top:2px}
.rt tr.np td{color:var(--faint);font-size:13px}
.fn{margin:12px 0 0;font-size:12.5px;color:var(--faint);max-width:74ch}
@media (max-width:640px){
  .turn{grid-template-columns:1fr;gap:8px}
  .who{padding-top:0}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

OVERVIEW = """
<figure class="fig">
<svg viewBox="0 0 760 380" role="img" preserveAspectRatio="xMidYMid meet"
     aria-label="Everything except the spec and the app is already in the folder. Each round the tutor asks questions until you answer them, your answers become the spec, the app is patched to match, and you run it and measure. You can step aside at any point to ask anything, then come back to the round's question. Five rounds.">
  <defs>
    <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="currentColor"/>
    </marker>
  </defs>

  <text class="band" x="0" y="12">IN THE FOLDER BEFORE YOU START &#8212; YOU NEVER EDIT THESE</text>
  <rect class="ro" x="0"   y="22" width="240" height="56" rx="2"/>
  <text class="n"  x="12"  y="42">memory.db</text>
  <text class="d"  x="12"  y="58">A conversation that already</text>
  <text class="d"  x="12"  y="71">happened, stored &#8212; allergy included</text>

  <rect class="ro" x="256" y="22" width="200" height="56" rx="2"/>
  <text class="n"  x="268" y="42">meter.py, seed_memory.py</text>
  <text class="d"  x="268" y="58">Finished code. It measures and</text>
  <text class="d"  x="268" y="71">it seeds; you never touch it.</text>

  <rect class="ro" x="472" y="22" width="288" height="56" rx="2"/>
  <text class="n"  x="484" y="42">the round&#8217;s materials</text>
  <text class="d"  x="484" y="58">The tutor&#8217;s questions and answer key, the</text>
  <text class="d"  x="484" y="71">checker, and the finished app to aim at</text>

  <line x1="380" y1="84" x2="380" y2="112" stroke="currentColor" marker-end="url(#ah)"/>
  <text class="e" x="388" y="102">the tutor reads these as it goes</text>

  <text class="band" x="0" y="130">EACH ROUND RUNS THESE FOUR STEPS, IN ORDER</text>
  <rect class="ph" x="0"   y="140" width="178" height="40" rx="2"/><text class="p" x="89"  y="165">TUTOR</text>
  <rect class="ph" x="194" y="140" width="178" height="40" rx="2"/><text class="p" x="283" y="165">SPEC</text>
  <rect class="ph" x="388" y="140" width="178" height="40" rx="2"/><text class="p" x="477" y="165">BUILD</text>
  <rect class="ph" x="582" y="140" width="178" height="40" rx="2"/><text class="p" x="671" y="165">DEMO</text>
  <line x1="180" y1="160" x2="192" y2="160" stroke="currentColor" marker-end="url(#ah)"/>
  <line x1="374" y1="160" x2="386" y2="160" stroke="currentColor" marker-end="url(#ah)"/>
  <line x1="568" y1="160" x2="580" y2="160" stroke="currentColor" marker-end="url(#ah)"/>

  <text class="s" x="89"  y="196">It asks one question at a</text>
  <text class="s" x="89"  y="209">time, and nudges rather than</text>
  <text class="s" x="89"  y="222">tells, until you answer it.</text>
  <text class="s" x="283" y="196">Your own answer is written</text>
  <text class="s" x="283" y="209">in as the next clause of a</text>
  <text class="s" x="283" y="222">spec that shipped blank.</text>
  <text class="s" x="477" y="196">The app is changed to do</text>
  <text class="s" x="477" y="209">what the clause you just</text>
  <text class="s" x="477" y="222">wrote now demands.</text>
  <text class="s" x="671" y="196">You guess what will happen,</text>
  <text class="s" x="671" y="209">run it, and write down the</text>
  <text class="s" x="671" y="222">number you actually got.</text>

  <line x1="89"  y1="232" x2="89"  y2="252" stroke="currentColor" marker-end="url(#ah)"/>
  <line x1="283" y1="232" x2="283" y2="252" stroke="currentColor" marker-end="url(#ah)"/>
  <line x1="477" y1="232" x2="477" y2="252" stroke="currentColor" marker-end="url(#ah)"/>
  <line x1="671" y1="232" x2="671" y2="252" stroke="currentColor" marker-end="url(#ah)"/>
  <text class="a"  x="89"  y="266">answers.md</text>
  <text class="ac" x="283" y="266">spec/spec.md</text>
  <text class="ac" x="477" y="266">src/snackbot.py</text>
  <text class="a"  x="671" y="266">demo-log.md</text>
  <text class="k"  x="283" y="280">you read exactly what changed</text>
  <text class="k"  x="477" y="280">you read exactly what changed</text>

  <path class="dash" d="M283,288 L283,306" marker-end="url(#ah)"/>
  <path class="dash" d="M477,306 L477,288" marker-end="url(#ah)"/>
  <text class="e" x="291" y="301">say &#8220;explain&#8221;</text>
  <text class="e" x="469" y="301" text-anchor="end">back to the question</text>
  <rect class="ex" x="60" y="308" width="640" height="36" rx="2"/>
  <text class="n"  x="76"  y="331">EXPAND</text>
  <text class="d"  x="146" y="331">Step aside at any point and ask anything on screen &#8212; answered plainly, no quizzing &#8212; then carry on.</text>

  <path class="dash" d="M756,180 L756,362 L4,362 L4,184" marker-end="url(#ah)"/>
  <text class="e" x="380" y="376" text-anchor="middle">then the next round &#8212; five in all</text>
</svg>
<figcaption>The course arrives with the memory already filled and the supporting code
finished. What is left blank is the spec, and an app that does not yet meet it. Each round
the tutor questions you until you can state the next requirement yourself, writes it into
the spec in your words, changes the app to satisfy it, and hands you the numbers to check
it against &#8212; showing you the exact diff at each step.</figcaption>
</figure>

<table class="rt">
<caption>What each played round did to those two files</caption>
<thead><tr><th>round</th><th>spec/spec.md</th><th>src/snackbot.py</th></tr></thead>
<tbody>
<tr><th>1</th>
  <td><b>+13 / &#8722;1</b><span>S1.1, S1.2 arrive</span></td>
  <td><b>+7 / &#8722;2</b><span>26 &#8594; 31 lines &#183; the meter</span></td></tr>
<tr><th>2</th>
  <td><b>+15 / &#8722;1</b><span>S2.1, S2.2, S2.3 arrive</span></td>
  <td><b>+37 / &#8722;3</b><span>31 &#8594; 65 lines &#183; SQL read + write</span></td></tr>
<tr class="np"><th>3&#8211;5</th>
  <td colspan="2">not played &#8212; this run stopped after round 2</td></tr>
</tbody>
</table>
<p class="fn">The single deletion in each spec commit is that round&#8217;s placeholder line,
<code>*(clauses arrive in Round N &#8212; written from your own answers)*</code>, being
replaced by the clauses. Numbers are <code>git show</code> on each commit in the played
repo; every commit carries exactly one artifact.</p>
"""

PHASE_NOTE = {
 "R0 · SETUP":"First contact. The tutor checks the copy and builds the environment itself.",
 "R1 · TUTOR":"Socratic Q&A. One question per turn; rungs before answers.",
 "R1 · SPEC" :"The learner's own words become spec clauses.",
 "R1 · BUILD":"A minimal patch to src/snackbot.py, then the diff dialogue.",
 "R1 · DEMO" :"Predict, run, observe, record. The learner runs the commands.",
 "R1 · EXPAND":"The one mode with no Socratic rules — questions answered plainly.",
 "R2 · TUTOR":"Socratic Q&A. One question per turn; rungs before answers.",
 "R2 · SPEC" :"The learner's own words become spec clauses.",
 "R2 · BUILD":"A minimal patch to src/snackbot.py, then the diff dialogue.",
 "R2 · DEMO" :"Predict, run, observe, record. The learner runs the commands.",
 "R2 · EXPAND":"The one mode with no Socratic rules — questions answered plainly.",
}

def render(events):
    tags = re.compile(r'\[(R\d\s·\s[A-Z]+)\]')
    body, seen, cur = [], [], None
    def phase_open(tag):
        slug = tag.lower().replace(" · ", "-").replace(" ", "")
        n_same = sum(1 for t, _ in seen if t == tag)
        if n_same: slug = f"{slug}-{n_same+1}"
        seen.append((tag, slug))
        body.append(f'<div class="phase" id="{slug}"><h2>{html.escape(tag)}</h2>'
                    f'<p>{html.escape(PHASE_NOTE.get(tag,""))}</p></div>')
    for e in events:
        if e["kind"] == "tutor":
            txt = e["text"]
            lead = re.match(r'^`?\[(R\d\s·\s[A-Z]+)\]`?[ \t]*\n?', txt)
            chip = ""
            if lead:
                tag = lead.group(1); txt = txt[lead.end():].lstrip("\n")
                chip = f'<span class="tag">{html.escape(tag)}</span>'
                if tag != cur:
                    cur = tag; phase_open(cur)
            else:
                m = tags.search(txt)
                if m and m.group(1) != cur:
                    cur = m.group(1); phase_open(cur)
            body.append(f'<div class="turn tutor"><div class="who">tutor{chip}</div>'
                        f'<div class="body">{md(txt)}</div></div>')
        elif e["kind"] == "learner":
            body.append(f'<div class="turn learner"><div class="who">learner</div>'
                        f'<div class="body">{md(e["text"])}</div></div>')
        else:
            cmd = re.sub(r'\s+', ' ', e["cmd"]).strip()
            head = (f'<summary><span class="no">{e["n"]:02d}</span>'
                    f'<span class="cmd">{html.escape(cmd[:150])}</span></summary>')
            if e["show"] and e["out"].strip():
                op = " open" if e["open"] else ""
                body.append(f'<details class="tool"{op}>{head}'
                            f'<pre class="out">{code_body(e["out"].rstrip())}</pre></details>')
            else:
                body.append(f'<details class="tool noout">{head}</details>')
    # body keeps every phase transition (the mode churn is real); the index is unique
    uniq, done = [], set()
    for t, sl in seen:
        if t not in done: done.add(t); uniq.append((t, sl))
    idx = "".join(f'<a href="#{sl}">{html.escape(t)}</a>' for t, sl in uniq)
    n_l = sum(1 for e in events if e["kind"] == "learner")
    n_t = sum(1 for e in events if e["kind"] == "tutor")
    n_c = sum(1 for e in events if e["kind"] == "tool")
    return f"""<title>SnackBot Playthrough</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{CSS}</style>
<div class="wrap">
<header class="top">
  <h1>SnackBot Playthrough</h1>
  <p class="sub">Rounds 1 and 2 of the course, played end to end against
  <code>gpt-5-mini</code> on 19 August 2026 &mdash; the first time anyone had run it.
  Every learner turn, every tutor turn, and every command the tutor ran, in order.
  Machine output is shown where the learner reacted to it: the demo runs, the build
  diffs, the verifier, the meter.</p>
  <div class="facts">
    <div class="fact"><b>{n_l}</b><span>learner turns</span></div>
    <div class="fact"><b>{n_t}</b><span>tutor turns</span></div>
    <div class="fact"><b>{n_c}</b><span>commands run</span></div>
  </div>
  {OVERVIEW}
  <nav class="idx">{idx}</nav>
</header>
{"".join(body)}
<footer>Generated from the raw session log by <code>build_html.py</code>.
Collapsed rows are commands whose output was the tutor reading its own course files.</footer>
</div>"""

STANDALONE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
{head}
</head>
<body>
{body}
</body>
</html>
"""

if __name__ == "__main__":
    frag = render(load())
    # the artifact host supplies its own doctype/head, so this file stays a fragment
    open("playthrough.html", "w").write(frag)
    # ...and a self-contained copy for opening from the filesystem (charset matters:
    # the mode tags contain U+00B7 and the prose contains em dashes)
    cut = frag.index("<div class=\"wrap\">")
    open("playthrough-local.html", "w").write(
        STANDALONE.format(head=frag[:cut].strip(), body=frag[cut:].strip()))
    print("wrote playthrough.html (artifact fragment) + playthrough-local.html (standalone)")
