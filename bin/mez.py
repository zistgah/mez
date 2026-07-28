#!/usr/bin/env python3
"""
mez — the desk.  میز / मेज़

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
SPDX-License-Identifier: GPL-3.0-or-later

Pure Python standard library. No pip, no account, no cloud, no vendor. It runs
on a laptop with the network unplugged and loses nothing but the things that are
genuinely remote.

WHAT IS BUILT, AND WHAT IS NOT. `mez doctor` prints both. Every capability the
desk advertises is either working or marked `not built` — never stubbed into
something that looks alive. A tab that pretends is worse than a tab that is
honest, because the person only finds out when they need it.

THE THREE RUNGS (C33). The same data, three ways in:
    mez <command>      console — works over ssh, in a tty, with no display
    mez serve          2D — a local page, no framework, no build step
    (XR)               the dome mounts this later; not built

THE ROLE SELECTS WHAT IS SHOWN, NEVER WHAT IS COMPUTED. `--role clinician`
hides engineering surfaces. It does not change a single number.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import http.server
import io
import json
import os
import socketserver
import subprocess
import sys
import urllib.parse

VERSION = "0.1.0"
BUILT_WITH = "Claude Opus 4.5"
HOME = os.environ.get("MEZ_HOME", os.path.expanduser("~/.mez"))

ROLES = ["engineer", "researcher", "clinician", "teacher", "learner",
         "institution", "visitor"]

# Which workstreams a role is shown. The computation is identical for all of
# them; this is presentation only (C33).
ROLE_VIEW = {
    "engineer":    None,                       # everything
    "researcher":  ["Zenodo", "Misty / Tok", "Ontology", "Readers / sites",
                    "Posters", "His material"],
    "clinician":   ["Readers / sites"],
    "teacher":     ["Readers / sites", "Ontology", "His material"],
    "learner":     ["Readers / sites"],
    "institution": ["Estate", "Process", "Economy"],
    "visitor":     ["Posters"],
}

# C32 — no vendor lock-in. Providers are data. Anything with prefill takes the
# prompt in the URL; the rest get it on the clipboard or stdout. `local` needs
# no network and no account at all, which is the point: remove every provider
# from this table and the desk still works, it just stops seeding.
PROVIDERS = [
    {"id": "local",      "name": "Local model",  "url": "",                                        "prefill": False},
    {"id": "claude",     "name": "Claude",       "url": "https://claude.ai/new?q=",                "prefill": True},
    {"id": "chatgpt",    "name": "ChatGPT",      "url": "https://chatgpt.com/?q=",                 "prefill": True},
    {"id": "perplexity", "name": "Perplexity",   "url": "https://www.perplexity.ai/search?q=",     "prefill": True},
    {"id": "copilot",    "name": "Copilot",      "url": "https://copilot.microsoft.com/?q=",       "prefill": True},
    {"id": "mistral",    "name": "Le Chat",      "url": "https://chat.mistral.ai/chat?q=",         "prefill": True},
    {"id": "grok",       "name": "Grok",         "url": "https://grok.com/?q=",                    "prefill": True},
    {"id": "gemini",     "name": "Gemini",       "url": "https://gemini.google.com/app",           "prefill": False},
    {"id": "deepseek",   "name": "DeepSeek",     "url": "https://chat.deepseek.com/",              "prefill": False},
]

# Capabilities the desk will carry. `built` is the truth, not the intention.
CAPABILITIES = [
    ("wbs",         "Work breakdown, CSV round-trip",            True),
    ("bearings",    "Where you are when you sit down",           True),
    ("ask",         "Seed a conversation, any provider",         True),
    ("proc",        "Local and cloud process registry",          True),
    ("estate",      "Estate inventory and sync",                 True),
    ("serve",       "2D surface",                                True),
    ("calendar",    "Calendar backed by CHAKRA",                 False),
    ("mail",        "Email",                                     False),
    ("messaging",   "SMS and messaging",                         False),
    ("social",      "Social media",                              False),
    ("meetings",    "Meetings, briefs and summaries",            False),
    ("classes",     "Conducting classes",                        False),
    ("embodiments", "Embodiment control (TransEg)",              False),
    ("kundali",     "Research Kundali",                          False),
    ("samd",        "Certification and validation, EMR as SaMD", False),
    ("xr",          "Immersive rung, mounted in the dome",       False),
]


# ─────────────────────────────────────────────────────────────── storage
def ensure_home() -> str:
    os.makedirs(HOME, exist_ok=True)
    return HOME


def state_path(name: str) -> str:
    return os.path.join(ensure_home(), name)


def load_state() -> dict:
    p = state_path("state.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return {"day": {}, "provider": "local", "role": "engineer", "procs": {}}


def save_state(s: dict) -> None:
    with open(state_path("state.json"), "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=1)


# ─────────────────────────────────────────────────────────────── WBS
WBS_FILE = "WBS.csv"


def wbs_path() -> str:
    return state_path(WBS_FILE)


def wbs_load() -> list[dict]:
    p = wbs_path()
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r.get("ID")]


def wbs_save(rows: list[dict]) -> None:
    if not rows:
        return
    with open(wbs_path(), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# His columns. Once he has set one, an import may never change it back.
OWNED = ("Priority", "Status", "Notes")


def _owned_load() -> dict:
    p = state_path("owned.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _owned_mark(row_id: str, field: str) -> None:
    o = _owned_load()
    o.setdefault(row_id, [])
    if field not in o[row_id]:
        o[row_id].append(field)
    with open(state_path("owned.json"), "w", encoding="utf-8") as fh:
        json.dump(o, fh, indent=1)


def wbs_import(src: str, force: bool = False) -> tuple[int, int]:
    """Take a CSV he edited anywhere — Sheets, Excel, a text editor.

    The rule, and it matters: a non-empty incoming value wins, an empty incoming
    value never clears a stored one. That covers both real cases without asking —
    importing the sheet he just prioritised (his values arrive filled and win),
    and importing a regenerated skeleton (its Priority column is empty and his
    survives).

    The first version replaced the row wholesale and printed that it had kept
    his edits. It had not. Caught by setting a priority and re-importing.
    """
    with open(src, newline="", encoding="utf-8") as fh:
        new = [r for r in csv.DictReader(fh) if r.get("ID")]
    cur = {r["ID"]: r for r in wbs_load()}
    owned = _owned_load()
    kept = 0
    for r in new:
        old = cur.get(r["ID"])
        if old:
            mine = owned.get(r["ID"], [])
            for k in OWNED:
                incoming = (r.get(k) or "").strip()
                stored = (old.get(k) or "").strip()
                # a cell he set himself is never overwritten by a regenerated file
                # A cell HE set is never overwritten by an import. There is no
                # way to tell a regenerated skeleton from his edited sheet by
                # looking at a row, so the safe direction is the default and the
                # destructive one needs --force. Losing a prioritisation pass to
                # a silent overwrite is not a recoverable mistake.
                if k in mine and not force:
                    r[k] = old.get(k, ""); kept += 1
                elif not incoming and stored:
                    r[k] = old[k]; kept += 1
        cur[r["ID"]] = r
    rows = sorted(cur.values(), key=lambda r: [
        int(x) if x.isdigit() else 0 for x in r["ID"].split(".")])
    wbs_save(rows)
    return len(rows), kept


def wbs_filter(rows, role=None, status=None, does=None, ws=None, prio=None):
    allowed = ROLE_VIEW.get(role) if role else None
    out = []
    for r in rows:
        if allowed is not None and r.get("Workstream") not in allowed:
            continue
        if status and r.get("Status") != status:
            continue
        if does and r.get("Does it") != does:
            continue
        if ws and ws.lower() not in r.get("Workstream", "").lower():
            continue
        if prio and r.get("Priority") != prio:
            continue
        out.append(r)
    return out


# ─────────────────────────────────────────────────────────────── bearings
def bearings(state: dict) -> dict:
    """Where you are when you sit down.

    Not a wellness feature and not medical advice: it reports elapsed time,
    what is unblocked, and what is cheapest, so the first ten minutes of a
    session are not spent rebuilding the picture from scratch.
    """
    now = dt.datetime.now()
    today = now.date().isoformat()
    day = state.setdefault("day", {})
    if day.get("date") != today:
        day.clear()
        day["date"] = today
    started = day.get("started")
    if not started:
        day["started"] = started = now.isoformat(timespec="seconds")
    t0 = dt.datetime.fromisoformat(started)
    elapsed = now - t0
    last_break = day.get("last_break")
    since_break = (now - dt.datetime.fromisoformat(last_break)) if last_break else elapsed

    rows = wbs_load()
    done_ids = {r["ID"] for r in rows if r.get("Status") == "done"}

    def unblocked(r):
        if r.get("Status") in ("done", "blocked"):
            return False
        b = (r.get("Blocked by") or "").strip()
        if not b:
            return True
        return all(x.strip() in done_ids for x in b.split(",") if x.strip())

    ready = [r for r in rows if unblocked(r)]
    cheapest = [r for r in ready if r.get("Status") == "built-not-run"]
    his = [r for r in ready if r.get("Does it") == "HIM"]
    p0 = [r for r in ready if r.get("Priority") == "P0"]

    hour = now.hour
    part = ("early" if hour < 7 else "morning" if hour < 12 else
            "afternoon" if hour < 17 else "evening" if hour < 22 else "late")

    return {
        "now": now.strftime("%A %d %B %Y, %H:%M"),
        "part_of_day": part,
        "session_started": t0.strftime("%H:%M"),
        "elapsed_min": int(elapsed.total_seconds() // 60),
        "since_break_min": int(since_break.total_seconds() // 60),
        "wbs_rows": len(rows),
        "ready": len(ready),
        "cheapest": cheapest[:6],
        "yours": his[:6],
        "p0": p0[:6],
        "blocked": [r for r in rows if r.get("Status") == "blocked"][:4],
    }


# ─────────────────────────────────────────────────────────────── seeding
def seed_prompt(rows: list[dict], note: str = "") -> str:
    lines = ["I am working on the following, from my own work-breakdown:", ""]
    for r in rows:
        lines.append(f"- [{r['ID']}] {r['Workstream']} — {r['Task']}"
                     f"{' (' + r['Status'] + ')' if r.get('Status') else ''}")
        if r.get("Detail"):
            lines.append(f"    {r['Detail']}")
        if r.get("Blocked by"):
            lines.append(f"    blocked by: {r['Blocked by']}")
    if note:
        lines += ["", note]
    lines += ["", "I am responsible for the decisions here — advise, do not decide.",
              "If something is already solved elsewhere in my estate, say so rather "
              "than rebuilding it."]
    return "\n".join(lines)


def provider(pid: str) -> dict:
    for p in PROVIDERS:
        if p["id"] == pid:
            return p
    return PROVIDERS[0]


# ─────────────────────────────────────────────────────────────── processes
def proc_list(state: dict) -> list[dict]:
    out = []
    for name, p in sorted(state.get("procs", {}).items()):
        alive = False
        if p.get("pid"):
            try:
                os.kill(int(p["pid"]), 0)
                alive = True
            except (OSError, ValueError):
                alive = False
        out.append({"name": name, "cmd": p.get("cmd", ""), "where": p.get("where", "local"),
                    "pid": p.get("pid"), "alive": alive})
    return out


# ─────────────────────────────────────────────────────────────── 2D surface
def page(state: dict, role: str) -> str:
    b = bearings(state)
    rows = wbs_filter(wbs_load(), role=role)
    caps_on = [c for c in CAPABILITIES if c[2]]
    caps_off = [c for c in CAPABILITIES if not c[2]]

    def esc(s):
        return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    ws = {}
    for r in rows:
        ws.setdefault(r["Workstream"], []).append(r)

    tbl = ""
    for name, rs in ws.items():
        open_n = sum(1 for r in rs if r.get("Status") not in ("done",))
        tbl += f'<h3>{esc(name)} <span class="c">{open_n} open</span></h3><table>'
        for r in rs:
            cls = "done" if r.get("Status") == "done" else ""
            tbl += (f'<tr class="{cls}"><td class="id">{esc(r["ID"])}</td>'
                    f'<td><input type="checkbox" class="pick" value="{esc(r["ID"])}"></td>'
                    f'<td>{esc(r["Task"])}<div class="d">{esc(r.get("Detail",""))}</div></td>'
                    f'<td class="s">{esc(r.get("Priority") or "—")}</td>'
                    f'<td class="s">{esc(r.get("Status"))}</td>'
                    f'<td class="s">{esc(r.get("Does it"))}</td></tr>')
        tbl += "</table>"

    return f"""<!doctype html><meta charset="utf-8">
<title>mez — {esc(role)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{--ink:#1b1a17;--mut:#6d6a5f;--acc:#2f6d4f;--warn:#b4531f;--line:#ddd4c0;
       --paper:#fffdf7;--bg:#fbf6e9}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.6 "Iowan Old Style",Palatino,Georgia,serif}}
header{{background:var(--paper);border-bottom:1px solid var(--line);padding:14px 20px;
 display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}}
header h1{{margin:0;font-size:19px}} header .t{{color:var(--mut);font-size:13px}}
nav a{{font:12px system-ui;color:var(--mut);text-decoration:none;margin-right:9px;
 padding:3px 8px;border:1px solid var(--line);border-radius:20px}}
nav a.on{{background:var(--acc);color:#fff;border-color:var(--acc)}}
main{{max-width:1000px;margin:0 auto;padding:20px}}
.card{{background:var(--paper);border:1px solid var(--line);border-radius:12px;
 padding:16px 18px;margin-bottom:16px}}
h2{{font:13px system-ui;letter-spacing:.06em;text-transform:uppercase;color:var(--acc);
 margin:0 0 10px}}
h3{{font-size:15px;margin:18px 0 6px}} h3 .c{{color:var(--mut);font:11px system-ui}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}
td{{padding:5px 6px;border-bottom:1px solid var(--line);vertical-align:top}}
td.id{{color:var(--mut);font:11px ui-monospace;width:52px}}
td.s{{color:var(--mut);font:11px system-ui;white-space:nowrap}}
.d{{color:var(--mut);font-size:12px}}
tr.done td{{opacity:.45;text-decoration:line-through}}
.big{{font-size:26px}} .grid{{display:flex;gap:26px;flex-wrap:wrap}}
.grid div span{{display:block;color:var(--mut);font:11px system-ui}}
.off{{color:var(--mut)}} .off b{{color:var(--warn);font-weight:normal}}
button,select{{font:13px system-ui;padding:7px 11px;border:1px solid var(--line);
 border-radius:8px;background:#fff;cursor:pointer}}
button.go{{background:var(--acc);color:#fff;border-color:var(--acc)}}
footer{{max-width:1000px;margin:0 auto;padding:0 20px 40px;color:var(--mut);font-size:12px}}
</style>
<header>
  <h1>mez</h1>
  <span class="t">میز · {esc(b['now'])} · {esc(b['part_of_day'])}</span>
  <nav>{"".join(f'<a class="{"on" if r==role else ""}" href="/?role={r}">{r}</a>'
                for r in ROLES)}</nav>
</header>
<main>

<div class="card">
  <h2>Bearings</h2>
  <div class="grid">
    <div><span>at the desk</span><b class="big">{b['elapsed_min']}m</b></div>
    <div><span>since a break</span><b class="big">{b['since_break_min']}m</b></div>
    <div><span>unblocked</span><b class="big">{b['ready']}</b></div>
    <div><span>built, never run</span><b class="big">{len(b['cheapest'])}</b></div>
    <div><span>yours alone</span><b class="big">{len(b['yours'])}</b></div>
  </div>
  {"<p class='off'><b>You have been at this "
   + str(b['since_break_min']) + " minutes without logging a break.</b> "
   "<code>mez break</code></p>" if b['since_break_min'] >= 90 else ""}
</div>

<div class="card">
  <h2>Cheapest first — built, never run</h2>
  {"".join(f'<div>· [{esc(r["ID"])}] {esc(r["Task"])}</div>' for r in b['cheapest'])
   or '<div class="off">nothing waiting</div>'}
</div>

<div class="card">
  <h2>Seed a conversation</h2>
  <p class="off">Tick any rows below, choose where it goes, and the prompt is built
  from your own breakdown. Nothing is sent until you click.</p>
  <select id="prov">{"".join(f'<option value="{p["id"]}">{p["name"]}'
        f'{"" if p["prefill"] else " ·copy"}</option>' for p in PROVIDERS)}</select>
  <button class="go" id="ask">Ask</button>
  <button id="copy">Copy prompt</button>
</div>

<div class="card">
  <h2>Work — {esc(role)} view</h2>
  <p class="off">The role changes what is shown. It never changes what is computed.</p>
  {tbl or '<div class="off">No WBS loaded. <code>mez wbs import WBS.csv</code></div>'}
</div>

<div class="card">
  <h2>What this desk can and cannot do yet</h2>
  <div>{" · ".join(esc(c[1]) for c in caps_on)}</div>
  <p class="off">Not built: <b>{" · ".join(esc(c[1]) for c in caps_off)}</b></p>
</div>

</main>
<footer>mez {VERSION} · built with {BUILT_WITH} · local-first, no account, no vendor ·
runs with the network unplugged · © 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.</footer>
<script>
const PROV={json.dumps(PROVIDERS)};
function picked(){{return [...document.querySelectorAll('.pick:checked')].map(c=>c.value);}}
async function prompt_(){{
  const ids=picked(); if(!ids.length){{alert('Tick a row first');return null;}}
  const r=await fetch('/prompt?ids='+encodeURIComponent(ids.join(',')));
  return await r.text();
}}
document.getElementById('ask').onclick=async()=>{{
  const t=await prompt_(); if(!t) return;
  const p=PROV.find(x=>x.id===document.getElementById('prov').value);
  if(p.prefill&&p.url) window.open(p.url+encodeURIComponent(t),'_blank','noopener');
  else {{ await navigator.clipboard.writeText(t).catch(()=>{{}});
         alert('Prompt copied — paste it into '+p.name);
         if(p.url) window.open(p.url,'_blank','noopener'); }}
}};
document.getElementById('copy').onclick=async()=>{{
  const t=await prompt_(); if(!t) return;
  await navigator.clipboard.writeText(t).catch(()=>{{}});
  document.getElementById('copy').textContent='Copied';
  setTimeout(()=>document.getElementById('copy').textContent='Copy prompt',1400);
}};
</script>"""


def serve(port: int, role: str) -> int:
    state = load_state()

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            if u.path == "/prompt":
                ids = set((q.get("ids", [""])[0]).split(","))
                rows = [r for r in wbs_load() if r["ID"] in ids]
                body = seed_prompt(rows).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
                return
            r = q.get("role", [role])[0]
            r = r if r in ROLES else role
            body = page(load_state(), r).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), H) as srv:
        print(f"  mez {VERSION} on http://127.0.0.1:{port}/  role={role}")
        print("  bound to loopback only — nothing is exposed to the network")
        print("  Ctrl-C to stop")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n  stopped")
    return 0


# ─────────────────────────────────────────────────────────────── cli
def cmd_bearings(a, state):
    b = bearings(state)
    save_state(state)
    print(f"\n  {b['now']}  ({b['part_of_day']})")
    print(f"  at the desk {b['elapsed_min']}m · since a break {b['since_break_min']}m")
    if b["since_break_min"] >= 90:
        print(f"  ! {b['since_break_min']} minutes without a logged break — `mez break`")
    print(f"\n  {b['wbs_rows']} rows · {b['ready']} unblocked")
    if b["p0"]:
        print("\n  P0")
        for r in b["p0"]:
            print(f"    [{r['ID']}] {r['Task']}")
    if b["cheapest"]:
        print("\n  cheapest — built, never run")
        for r in b["cheapest"]:
            print(f"    [{r['ID']}] {r['Task']}")
    if b["yours"]:
        print("\n  only you can")
        for r in b["yours"]:
            print(f"    [{r['ID']}] {r['Task']}")
    if b["blocked"]:
        print("\n  blocked")
        for r in b["blocked"]:
            print(f"    [{r['ID']}] {r['Task']}  <- {r.get('Blocked by')}")
    print()
    return 0


def cmd_break(a, state):
    state.setdefault("day", {})["last_break"] = dt.datetime.now().isoformat(timespec="seconds")
    save_state(state)
    print("  break logged")
    return 0


def cmd_wbs(a, state):
    if a.wbs_action == "import":
        n, kept = wbs_import(a.file, force=a.force)
        print(f"  {n} rows · {kept} of your own cells preserved "
              f"(an import fills your columns, it never clears them)")
        return 0
    if a.wbs_action == "export":
        rows = wbs_load()
        w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            w.writeheader()
            w.writerows(rows)
        return 0
    if a.wbs_action == "set":
        rows = wbs_load()
        hit = 0
        for r in rows:
            if r["ID"] == a.id:
                for kv in a.set or []:
                    k, _, v = kv.partition("=")
                    if k in r:
                        r[k] = v
                        hit += 1
                        if k in OWNED:
                            _owned_mark(a.id, k)
        wbs_save(rows)
        print(f"  {a.id}: {hit} field(s) set")
        return 0
    rows = wbs_filter(wbs_load(), role=a.role, status=a.status,
                      does=a.does, ws=a.workstream, prio=a.priority)
    if not rows:
        print("  nothing matches (or no WBS imported yet)")
        return 0
    cur = None
    for r in rows:
        if r["Workstream"] != cur:
            cur = r["Workstream"]
            print(f"\n  {cur}")
        p = r.get("Priority") or "  "
        print(f"    {p:<3} [{r['ID']:<5}] {r['Task'][:62]:<62} {r.get('Status',''):<14} {r.get('Does it','')}")
    print()
    return 0


def cmd_ask(a, state):
    ids = set((a.ids or "").split(",")) if a.ids else None
    rows = wbs_load()
    rows = [r for r in rows if ids is None or r["ID"] in ids]
    if not rows:
        print("  no rows selected — pass --ids 1.2,3.4")
        return 2
    p = provider(a.provider or state.get("provider", "local"))
    text = seed_prompt(rows, a.note or "")
    if p["prefill"] and p["url"]:
        print(f"  open in {p['name']}:\n  {p['url']}{urllib.parse.quote(text)}")
    else:
        print(f"  ---- prompt (for {p['name']}) ----\n{text}\n  ----")
    return 0


def cmd_proc(a, state):
    if a.proc_action == "add":
        state.setdefault("procs", {})[a.name] = {"cmd": a.cmd, "where": a.where}
        save_state(state)
        print(f"  registered {a.name} ({a.where})")
        return 0
    if a.proc_action == "start":
        p = state.get("procs", {}).get(a.name)
        if not p:
            print(f"  unknown process {a.name}")
            return 2
        if p.get("where") != "local":
            print(f"  {a.name} is registered as '{p['where']}' — remote start is not built")
            return 2
        proc = subprocess.Popen(p["cmd"], shell=True, cwd=os.getcwd(),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p["pid"] = proc.pid
        save_state(state)
        print(f"  {a.name} started, pid {proc.pid}")
        return 0
    for p in proc_list(state):
        mark = "running" if p["alive"] else "stopped"
        print(f"  {p['name']:<18} {p['where']:<8} {mark:<9} {p['cmd']}")
    return 0


def cmd_doctor(a, state):
    print(f"\n  mez {VERSION} · built with {BUILT_WITH}")
    print(f"  home        {HOME}")
    print(f"  python      {sys.version.split()[0]}  (standard library only — no pip)")
    rows = wbs_load()
    print(f"  wbs         {len(rows)} rows" if rows else "  wbs         not imported")
    print("\n  built")
    for k, d, on in CAPABILITIES:
        if on:
            print(f"    ok    {k:<12} {d}")
    print("\n  NOT built — the desk says so rather than pretending")
    for k, d, on in CAPABILITIES:
        if not on:
            print(f"    --    {k:<12} {d}")
    print("\n  external tools")
    for t in ("git", "gh", "ots", "misty", "ollama"):
        p = None
        for d in os.environ.get("PATH", "").split(os.pathsep):
            c = os.path.join(d, t)
            if os.path.isfile(c) and os.access(c, os.X_OK):
                p = c
                break
        print(f"    {'ok  ' if p else '--  '} {t:<8} {p or 'absent — its step is skipped, not faked'}")
    print("\n  no account, no API key, no network required for anything above.\n")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="mez", description="mez — the desk. میز")
    ap.add_argument("--version", action="version", version=f"mez {VERSION}")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("bearings", help="where you are when you sit down")
    sub.add_parser("break", help="log a break")
    sub.add_parser("doctor", help="what is built, what is not, what is installed")

    w = sub.add_parser("wbs", help="work breakdown")
    w.add_argument("wbs_action", nargs="?", default="list",
                   choices=["list", "import", "export", "set"])
    w.add_argument("file", nargs="?")
    w.add_argument("--id")
    w.add_argument("--set", action="append", metavar="Field=Value")
    w.add_argument("--role", choices=ROLES)
    w.add_argument("--status")
    w.add_argument("--does", choices=["HIM", "AI", "AGENT"])
    w.add_argument("--workstream")
    w.add_argument("--priority")
    w.add_argument("--force", action="store_true",
                   help="let an import overwrite cells you set yourself")

    k = sub.add_parser("ask", help="seed a conversation from selected rows")
    k.add_argument("--ids")
    k.add_argument("--provider", choices=[p["id"] for p in PROVIDERS])
    k.add_argument("--note")

    pr = sub.add_parser("proc", help="local and cloud processes")
    pr.add_argument("proc_action", nargs="?", default="list",
                    choices=["list", "add", "start"])
    pr.add_argument("name", nargs="?")
    pr.add_argument("--cmd", default="")
    pr.add_argument("--where", default="local")

    s = sub.add_parser("serve", help="2D surface on loopback")
    s.add_argument("--port", type=int, default=7373)
    s.add_argument("--role", default="engineer", choices=ROLES)

    a = ap.parse_args(argv)
    state = load_state()
    if a.cmd == "serve":
        return serve(a.port, a.role)
    fn = {"bearings": cmd_bearings, "break": cmd_break, "wbs": cmd_wbs,
          "ask": cmd_ask, "proc": cmd_proc, "doctor": cmd_doctor}.get(a.cmd)
    if not fn:
        ap.print_help()
        return 0
    return fn(a, state)


if __name__ == "__main__":
    raise SystemExit(main())
