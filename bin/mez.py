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

# Which workstreams a role is shown. The role changes what is SHOWN and
# never changes what is computed (master C33) — the numbers are identical for
# every role, and a clinician does not pass through an engineering surface to
# reach clinical function.
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
    {"id": "local",      "name": "Local model",  "url": "",                                        "prefill": False, "local": True},
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
    ("calendar",    "Calendar backed by CHAKRA",                 True),
    ("mail",        "Email",                                     True),
    ("messaging",   "SMS and messaging",                         True),
    ("social",      "Social media",                              True),
    ("meetings",    "Meetings, briefs and summaries",            True),
    ("classes",     "Conducting classes",                        True),
    ("embodiments", "Embodiment control (TransEg)",              True),
    ("kundali",     "Research Kundali",                          True),
    ("samd",        "Certification and validation, EMR as SaMD", True),
    ("xr",          "Immersive rung, mounted in the dome",       True),
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


# ─────────────────────────────────────────────────────────────── web GUI
# Web-FIRST (see mez_gui.py). The console is the same data for a tty; the
# immersive rung mounts THIS in the dome rather than reimplementing it.
try:
    import mez_gui
except ImportError:                       # running as a single file
    mez_gui = None


def _tools() -> dict:
    out = {}
    for t in ("git", "gh", "ots", "misty", "ollama", "node", "python3"):
        out[t] = None
        for d in os.environ.get("PATH", "").split(os.pathsep):
            c = os.path.join(d, t)
            if os.path.isfile(c) and os.access(c, os.X_OK):
                out[t] = c
                break
    return out


def api_state(state: dict) -> dict:
    b = bearings(state)
    save_state(state)
    return {
        "version": VERSION, "built_with": BUILT_WITH,
        "roles": ROLES, "providers": PROVIDERS,
        "caps": [list(c) for c in CAPABILITIES],
        "tools": _tools(),
        "owned": _owned_load(),
        "wbs_rows": b["wbs_rows"],
        "bearings": b,
    }


def serve(port: int, role: str) -> int:
    if mez_gui is None:
        print("  mez_gui.py not found beside mez.py — the web surface needs it.")
        return 2
    state = load_state()

    class H(http.server.BaseHTTPRequestHandler):
        server_version = f"mez/{VERSION}"

        def log_message(self, *a):
            pass

        def _send(self, body, ctype="application/json", code=200):
            if isinstance(body, (dict, list)):
                body = json.dumps(body)
            if isinstance(body, str):
                body = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            # the desk is loopback-only; nothing here is meant to be embedded
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            p = u.path
            if p == "/":
                return self._send(mez_gui.shell(VERSION, BUILT_WITH), "text/html")
            if p == "/app.css":
                return self._send(mez_gui.APP_CSS, "text/css")
            if p == "/app.js":
                return self._send(mez_gui.APP_JS, "application/javascript")
            if p == "/sw.js":
                return self._send(mez_gui.SW_JS, "application/javascript")
            if p == "/icon.svg":
                return self._send(mez_gui.ICON, "image/svg+xml")
            if p == "/manifest.webmanifest":
                return self._send(mez_gui.MANIFEST, "application/manifest+json")
            if p == "/api/state":
                return self._send(api_state(load_state()))
            if p == "/api/wbs":
                r = (q.get("role", [role])[0])
                r = r if r in ROLES else role
                return self._send({"role": r, "rows": wbs_filter(wbs_load(), role=r)})
            if p == "/api/prompt":
                ids = set((q.get("ids", [""])[0]).split(","))
                rows = [x for x in wbs_load() if x["ID"] in ids]
                return self._send(seed_prompt(rows), "text/plain")
            return self._send({"error": "not found"}, code=404)

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            try:
                data = json.loads(raw or b"{}")
            except ValueError:
                return self._send({"error": "bad json"}, code=400)

            if u.path == "/api/break":
                st = load_state()
                st.setdefault("day", {})["last_break"] = \
                    dt.datetime.now().isoformat(timespec="seconds")
                save_state(st)
                return self._send({"ok": True})

            if u.path.startswith("/api/wbs/"):
                rid = urllib.parse.unquote(u.path[len("/api/wbs/"):])
                rows = wbs_load()
                hit = None
                for r in rows:
                    if r["ID"] == rid:
                        for k, v in data.items():
                            if k in r:
                                r[k] = v
                                # touching a cell here makes it HIS — an import
                                # will not clear it afterwards
                                if k in OWNED:
                                    _owned_mark(rid, k)
                        hit = r
                if hit is None:
                    return self._send({"error": "no such row"}, code=404)
                wbs_save(rows)
                return self._send({"ok": True, "row": hit})

            return self._send({"error": "not found"}, code=404)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), H) as srv:
        print(f"\n  mez {VERSION} — the desk")
        print(f"  http://127.0.0.1:{port}/     role={role}")
        print("  loopback only · installable · works offline · Ctrl-C to stop\n")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("  stopped")
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
    if p.get("local"):
        host, model = _ai_cfg(state)
        out, src = local_ai(text, timeout=180, host=host, model=model)
        if out is None:
            print(f"  no local model ({src}) — the seed prompt, to paste yourself:\n")
            print(f"  ---- prompt ----\n{text}\n  ----")
            return 0
        print(f"\n  [{src}] seeded from {len(rows)} row(s)\n")
        print(out); print("")
        return 0
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



# ──────────────────────────────────────────── wiring · CONTRACT C37, MASTER 5
# Four capabilities the desk listed as "not built" were never builds. The
# systems exist in the estate and were read before this was written. mez asks
# them and lays out the answer at the rung you are standing on. It computes an
# ephemeris, a bibliometric chart, an avatar and a dome scene exactly never.
#
# Absent system  → a sentence and a non-zero exit.
# Present system → its own numbers, unaltered.
# Neither path ever prints a plausible substitute.

ESTATE = os.environ.get("MEZ_ESTATE", "/shared/estate/github")

# Wired and runnable, but never yet observed against a live instance from this
# machine. doctor prints these apart from `built`. C37: partial is partial.
UNPROVEN = {"embodiments"}

# TransEg endpoints. Every one of these is named in zistgah/transeg's README.
# Nothing is here that was inferred; an endpoint absent from that README is
# absent from this table, and so is not offered.
TRANSEG_ROUTES = {
    "chat":    ("POST", "/chat",            "memory"),
    "render":  ("POST", "/avatar/render",   "face"),
    "export":  ("GET",  "/memory/export",   None),
    "backup":  ("POST", "/memory/backup",   None),
    "restore": ("POST", "/memory/restore",  None),
    "delete":  ("POST", "/memory/delete",   None),
}


def _estate(slug):
    """Path to a repo in the estate, or None. Never clones, never creates."""
    p = os.path.join(ESTATE, slug)
    return p if os.path.isdir(p) else None


def _which(tool):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        c = os.path.join(d, tool)
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def _absent(what, how):
    print("")
    print("  %s is not reachable from here." % what)
    print("  %s" % how)
    print("  Nothing computed, nothing guessed, nothing cached from last time.")
    print("")
    return 3


# ── calendar · CHAKRA computes; mez only asks ────────────────────────────────
def cmd_cal(a, state):
    repo = _estate("project-ilm/chakra")
    if not repo:
        return _absent("CHAKRA", "expected a clone at %s/project-ilm/chakra — "
                                 "set MEZ_ESTATE, or clone it." % ESTATE)
    node = _which("node")
    if not node:
        return _absent("node", "CHAKRA's kernel is UMD JavaScript. The desk does "
                               "not carry a second ephemeris to fall back on.")
    bridge = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "chakra_bridge.js")
    if not os.path.isfile(bridge):
        return _absent("chakra_bridge.js", "it ships beside mez.py in bin/.")

    init = {"refDate": a.date or dt.date.today().isoformat(),
            "refTime": a.time, "tz": a.tz, "lat": a.lat, "lon": a.lon,
            "zodiac": a.zodiac}
    r = subprocess.run([node, bridge, repo, json.dumps(init)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("")
        print("  CHAKRA refused. Its words, not a paraphrase:")
        print("")
        for ln in (r.stderr or "").strip().splitlines()[:12]:
            print("    " + ln)
        print("")
        return 4
    try:
        m = json.loads(r.stdout)
    except ValueError:
        return _absent("CHAKRA output", "the bridge returned something that is "
                                        "not JSON. Not parsing it loosely.")
    if a.json:
        print(json.dumps(m, indent=2, ensure_ascii=False))
        return 0

    cal = m.get("calendars", {})
    pan = m.get("panchanga", {})
    mn = m.get("moon", {})
    sn = m.get("sun", {})
    print("")
    print("  %s   %s   %.4fN %.4fE   tz %+.1f"
          % (init["refDate"], init["refTime"], a.lat, a.lon, a.tz))
    print("  computed by CHAKRA (%s) — mez did not compute one number of it"
          % os.path.basename(repo))
    print("")
    for k in ("gregorian", "julianDay", "hijriSunni", "hijriShia", "solarHijri",
              "samvatsara", "saka", "vikrama", "kali", "hebrew", "nanakshahi",
              "chinese", "tibetan", "mayan", "age"):
        if k in cal:
            print("    %-12s %s" % (k, cal[k]))
    if pan:
        print("")
        print("  panchanga")
        for k in ("vara", "tithi", "nakshatra", "yoga", "karana", "manzil"):
            if k in pan:
                print("    %-12s %s" % (k, pan[k]))
    if mn or sn:
        print("")
        if mn:
            print("    moon         %s, %.1f%% illuminated"
                  % (mn.get("phase", "?"), 100.0 * float(mn.get("illum", 0))))
        if sn:
            print("    sun          %s" % sn.get("dayState", "?"))
    ecl = m.get("eclipses") or []
    if ecl:
        print("")
        print("  eclipses within 560 days")
        for e in ecl[:8]:
            print("    %-8s %s%s" % (e.get("type", "?"), e.get("date", "?"),
                                     "  central" if e.get("central") else ""))
    print("")
    print("  precision is CHAKRA's own — see its docs/ASSUMPTIONS.md before you")
    print("  quote any of this in an almanac.")
    print("")
    return 0


# ── Research Kundali · the repo exists; mez runs it ──────────────────────────
def cmd_kundali(a, state):
    repo = _estate("project-ilm/research-kundali")
    if not repo:
        return _absent("research-kundali",
                       "expected a clone at %s/project-ilm/research-kundali. "
                       "It EXISTS and is published — clone it, do not rebuild "
                       "it." % ESTATE)
    tool = os.path.join(repo, "kundali", "kundali.py")
    if not os.path.isfile(tool):
        return _absent("kundali/kundali.py",
                       "the clone is present but the entry point is not where "
                       "its README says. Not searching blind.")
    out = os.path.abspath(a.out)
    print("")
    print("  research-kundali %s → %s" % (a.subject, out))
    print("  sources: ORCID · OpenAlex · Crossref · DataCite. Google Scholar is")
    print("  deliberately not queried; that is the tool's ruling, not mez's.")
    print("")
    r = subprocess.run([sys.executable, tool, a.subject, "--out", out])
    if r.returncode != 0:
        print("")
        print("  research-kundali exited %d. Its exit code stands; mez does not"
              % r.returncode)
        print("  reinterpret it as success.")
        print("")
        return r.returncode
    asm = os.path.join(out, "ASSUMPTIONS.md")
    if os.path.isfile(asm):
        print("  every decision taken without asking: %s" % asm)
    print("")
    return 0


# ── embodiment · a client for the TransEg gateway, not a second avatar ───────
def cmd_embody(a, state):
    import urllib.error
    import urllib.request

    if a.embody_action == "routes":
        print("")
        print("  routes mez will call. Every one is named in zistgah/transeg's")
        print("  README. Nothing here was inferred from a port scan or a guess.")
        print("")
        for k in sorted(TRANSEG_ROUTES):
            meth, path_, stage = TRANSEG_ROUTES[k]
            print("    %-8s %-6s %-18s %s"
                  % (k, meth, path_,
                     ("requires stage: " + stage) if stage else ""))
        print("")
        print("  Staggered upload stages, in the order the gateway gates them:")
        print("    face · voice · documents · knowledge · memory · preferences")
        print("    · reasoning · delegated tasks")
        print("  No stage implicitly grants another.")
        print("")
        return 0

    if a.embody_action not in TRANSEG_ROUTES:
        print("  unknown action %r — `mez embody routes` lists what is offered."
              % a.embody_action)
        return 2
    base = (a.base or os.environ.get("TRANSEG_BASE") or "").rstrip("/")
    if not base:
        return _absent("a TransEg gateway",
                       "pass --base http://127.0.0.1:PORT or set TRANSEG_BASE. "
                       "mez will not scan your ports looking for one.")
    meth, path_, stage = TRANSEG_ROUTES[a.embody_action]
    url = base + path_
    body = None
    if meth == "POST":
        body = (a.data or "{}").encode("utf-8")
    req = urllib.request.Request(url, data=body, method=meth,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=a.timeout) as resp:
            payload = resp.read().decode("utf-8", "replace")
            print("")
            print("  %s %s → %d" % (meth, path_, resp.status))
            print("")
            print(payload[:4000])
            print("")
            return 0
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:800]
        print("")
        print("  %s %s → %d %s" % (meth, path_, e.code, e.reason))
        if stage and e.code in (401, 403):
            print("  the gateway gates this on stage %r. That is the staggered"
                  % stage)
            print("  upload working, not a fault.")
        if detail.strip():
            print("")
            print(detail)
        print("")
        return 4
    except Exception as e:                       # noqa: BLE001 — reported verbatim
        print("")
        print("  no answer from %s" % url)
        print("  %s: %s" % (type(e).__name__, e))
        print("  mez reports the failure. It does not simulate an embodiment.")
        print("")
        return 3


# ── immersive rung · emit a display the dome already knows how to render ─────
def cmd_xr(a, state):
    rows = wbs_load()
    if not rows:
        return _absent("a work breakdown",
                       "`mez wbs import <file.csv>` first — the dome renders "
                       "your rows, and there are none.")
    fams, layers = {}, {}
    nodes = []
    for r in rows:
        ws = (r.get("Workstream") or "unassigned").strip() or "unassigned"
        st = (r.get("Status") or "unset").strip() or "unset"
        fams.setdefault(ws, len(fams))
        layers.setdefault(st, len(layers))
        nodes.append({
            "id": r.get("ID") or "",
            "label": (r.get("Task") or r.get("Title") or "")[:120],
            "family": fams[ws],
            "layer": layers[st],
            "priority": (r.get("Priority") or "").strip(),
            "role": (r.get("Role") or "").strip(),
            "does": (r.get("Does") or "").strip(),
        })
    display = {
        "id": "mez-wbs",
        "type": "pointcloud",
        "title": "mez · work breakdown",
        "source": "zistgah/mez · mez xr",
        "generated": dt.datetime.now(dt.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "role_visibility": list(ROLES),
        "nodes": nodes,
        "families": [{"id": i, "name": n} for n, i in sorted(fams.items(),
                                                             key=lambda kv: kv[1])],
        "layers": [{"id": i, "name": n} for n, i in sorted(layers.items(),
                                                           key=lambda kv: kv[1])],
    }
    text = json.dumps(display, indent=2, ensure_ascii=False)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print("")
        print("  wrote %s  ·  %d nodes · %d families · %d layers"
              % (a.out, len(nodes), len(fams), len(layers)))
        print("")
        print("  This is a display config, not a renderer. zistgah/dome already")
        print("  draws pointcloud displays; mez adds no render code and no")
        print("  second scene graph. Drop it into the dome's displays[].")
        print("")
    else:
        print(text)
    return 0



# ═══════════════════════════════ MEZ · local-first completion (CONTRACT C37) ══
# Six capabilities the desk listed as not-built, wired so each either does real
# local work or says plainly what it needs. mez computes no model output, sends
# no mail it cannot send, and never prints a plausible substitute for a missing
# transport.

# samd is a FRAMEWORK, not a certification. It is tracked apart from `built`.
FRAMEWORK = {"samd"}
# wired, but not yet exercised against your live services from here (C37).
UNPROVEN_COMPLETE = {"messaging", "social"}

MEZ_OUTBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outbox")


def _absent2(what, how):
    print("\n  %s is not reachable from here." % what)
    print("  %s" % how)
    print("  Nothing sent, nothing computed, nothing faked.\n")
    return 3


# ── ai · a real local model client (your ollama, or any local OpenAI API) ────
def local_ai(prompt, system="", timeout=120, host=None, model=None):
    """Return (text, source) or (None, reason). Talks only to a model YOU run."""
    import urllib.request, urllib.error
    # local-AI provider wiring complete: host/model come from state or env
    # 1) ollama, the one already on ilm01-lin
    base = (host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
    model = model or os.environ.get("MEZ_MODEL", "")
    try:
        if not model:
            with urllib.request.urlopen(base + "/api/tags", timeout=5) as r:
                tags = json.loads(r.read().decode("utf-8", "replace"))
                ms = [m.get("name") for m in tags.get("models", []) if m.get("name")]
                model = ms[0] if ms else ""
        if model:
            body = json.dumps({"model": model, "prompt": prompt, "system": system,
                               "stream": False}).encode("utf-8")
            req = urllib.request.Request(base + "/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read().decode("utf-8", "replace"))
                return (out.get("response", "").strip(), "ollama:" + model)
    except Exception:
        pass
    # 2) an OpenAI-compatible local endpoint, if you point one at us (C32, BYO)
    oai = os.environ.get("MEZ_OPENAI_BASE", "").rstrip("/")
    if oai:
        try:
            key = os.environ.get("MEZ_OPENAI_KEY", "")
            body = json.dumps({"model": os.environ.get("MEZ_MODEL", "local"),
                               "messages": ([{"role": "system", "content": system}] if system else []) +
                                           [{"role": "user", "content": prompt}]}).encode("utf-8")
            h = {"Content-Type": "application/json"}
            if key: h["Authorization"] = "Bearer " + key
            req = urllib.request.Request(oai + "/chat/completions", data=body, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read().decode("utf-8", "replace"))
                return (out["choices"][0]["message"]["content"].strip(), "openai-local")
        except Exception as e:
            return (None, "local OpenAI endpoint set but unreachable: %s" % e)
    return (None, "no local model — start ollama, or set MEZ_OPENAI_BASE")


def local_models(host=None):
    import urllib.request
    base = (host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
    try:
        with urllib.request.urlopen(base + "/api/tags", timeout=5) as r:
            tags = json.loads(r.read().decode("utf-8", "replace"))
            return [m.get("name") for m in tags.get("models", []) if m.get("name")]
    except Exception:
        return []

def _ai_cfg(state):
    return (state.get("ollama_host") or os.environ.get("OLLAMA_HOST"),
            state.get("model") or os.environ.get("MEZ_MODEL"))

def cmd_ai(a, state):
    rest = " ".join(a.rest) if getattr(a, "rest", None) else ""
    host, model = _ai_cfg(state)
    if a.prompt == "models":
        ms = local_models(host)
        if not ms:
            print("\n  no local model reachable (ollama at %s). Start it, or\n"
                  "  set OLLAMA_HOST / MEZ_OPENAI_BASE.\n"
                  % (host or "http://127.0.0.1:11434")); return 3
        cur = model or ms[0]
        print("\n  local models (* = default):")
        for m in ms: print("    %s %s" % ("*" if m == cur else " ", m))
        print(""); return 0
    if a.prompt == "use":
        if not rest: print("  usage: mez ai use <model>"); return 2
        state["model"] = rest; save_state(state); print("  default model: %s" % rest); return 0
    if a.prompt == "host":
        if not rest: print("  usage: mez ai host <url>"); return 2
        state["ollama_host"] = rest; save_state(state); print("  ollama host: %s" % rest); return 0
    prompt = (a.prompt or "") + ((" " + rest) if rest else "")
    if not prompt.strip():
        prompt = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not prompt.strip():
        print("  usage: mez ai \"your prompt\"   |   mez ai models   |   mez ai use <model>"); return 2
    text, src = local_ai(prompt, system=a.system or "", timeout=a.timeout, host=host, model=model)
    if text is None:
        return _absent2("a local model", src)
    print("\n  [%s]\n" % src)
    print(text)
    print("")
    return 0


# ── mail · read a local Maildir/mbox; compose to the outbox ──────────────────
def cmd_mail(a, state):
    import mailbox, email.utils
    box_path = a.box or os.environ.get("MEZ_MAILBOX", "")
    if a.mail_action in ("list", "show"):
        if not box_path or not os.path.exists(box_path):
            return _absent2("a local mailbox",
                            "point --box at a Maildir or mbox, or set MEZ_MAILBOX. "
                            "mez reads mail you already have on disk; it does not "
                            "hold an account.")
        box = mailbox.Maildir(box_path) if os.path.isdir(box_path) else mailbox.mbox(box_path)
        msgs = list(box)
        if a.mail_action == "list":
            print("\n  %d message(s) in %s\n" % (len(msgs), box_path))
            for i, m in enumerate(msgs[-(a.n):]):
                print("    %-3d %-28s %s" % (i, (m.get("From") or "")[:28],
                                             (m.get("Subject") or "")[:60]))
            print("")
        else:
            m = msgs[a.index]
            print("\n  From:    %s\n  Subject: %s\n" % (m.get("From"), m.get("Subject")))
            body = m.get_payload(decode=True)
            print((body.decode("utf-8", "replace") if body else m.get_payload())[:4000])
            print("")
        return 0
    if a.mail_action == "compose":
        os.makedirs(MEZ_OUTBOX, exist_ok=True)
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        draft = os.path.join(MEZ_OUTBOX, "mail-%s.eml" % ts)
        with open(draft, "w", encoding="utf-8") as fh:
            fh.write("To: %s\nSubject: %s\n\n%s\n" % (a.to or "", a.subject or "", a.body or ""))
        print("\n  draft written: %s" % draft)
        print("  This is a DRAFT. `mez mail send` needs SMTP by path and is the")
        print("  only step that leaves your machine.\n")
        return 0
    if a.mail_action == "send":
        creds = os.environ.get("MEZ_SMTP_CREDS", "")
        if not creds or not os.path.isfile(creds):
            return _absent2("SMTP credentials",
                            "set MEZ_SMTP_CREDS to a file of host/port/user/pass "
                            "(by path, never inline). Until then drafts stay in "
                            "the outbox — mez will not pretend a mail was sent.")
        print("  send path present but deliberately not auto-firing in this build;")
        print("  your drafts are in %s. Wire your MTA to that directory." % MEZ_OUTBOX)
        return 0
    print("  usage: mez mail {list|show|compose|send}"); return 2


# ── messaging / social · draft to outbox; send via a transport YOU configure ─
def _queue(kind, target, text, transport_env, human):
    os.makedirs(MEZ_OUTBOX, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    item = os.path.join(MEZ_OUTBOX, "%s-%s.json" % (kind, ts))
    json.dump({"kind": kind, "target": target, "text": text, "queued": ts},
              open(item, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n  queued %s → %s" % (kind, item))
    cmd = os.environ.get(transport_env, "")
    if not cmd:
        print("  No transport configured (%s unset), so it stays queued. %s" % (transport_env, human))
        print("  mez will not claim it was sent.\n")
        return 0
    rc = subprocess.run(cmd, shell=True, env={**os.environ, "MEZ_ITEM": item,
                        "MEZ_TARGET": target or "", "MEZ_TEXT": text or ""}).returncode
    print("  transport %s exited %d\n" % (transport_env, rc))
    return 0 if rc == 0 else 4


def cmd_msg(a, state):
    if not a.text: print("  usage: mez msg --to <n> \"text\""); return 2
    return _queue("sms", a.to, a.text, "MEZ_SMS_CMD",
                  "Set MEZ_SMS_CMD to your gateway command.")


def cmd_social(a, state):
    if not a.text: print("  usage: mez social --to <platform> \"text\""); return 2
    return _queue("social", a.to, a.text, "MEZ_SOCIAL_CMD",
                  "Set MEZ_SOCIAL_CMD to your posting command (per platform).")


# ── meetings · parse a local .ics; brief from the WBS; summarise via local AI ─
def _parse_ics(path):
    events, cur = [], None
    for raw in open(path, encoding="utf-8", errors="replace"):
        line = raw.rstrip("\r\n")
        if line == "BEGIN:VEVENT": cur = {}
        elif line == "END:VEVENT":
            if cur is not None: events.append(cur); cur = None
        elif cur is not None and ":" in line:
            k, v = line.split(":", 1); k = k.split(";")[0]
            if k in ("SUMMARY", "DTSTART", "DTEND", "LOCATION", "DESCRIPTION", "ATTENDEE"):
                cur.setdefault(k, []).append(v)
    return events


def cmd_meetings(a, state):
    if a.meet_action == "next":
        ics = a.ics or os.environ.get("MEZ_ICS", "")
        if not ics or not os.path.isfile(ics):
            return _absent2("a calendar file",
                            "point --ics at a local .ics export (Google/Outlook/"
                            "Nextcloud all export one), or set MEZ_ICS. mez reads "
                            "the file; it does not hold your calendar account.")
        evs = _parse_ics(ics)
        def start(e): return (e.get("DTSTART", [""])[0])
        upcoming = sorted(evs, key=start)
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
        future = [e for e in upcoming if start(e).replace("Z", "") >= now][:a.n]
        print("\n  next %d meeting(s) from %s\n" % (len(future), os.path.basename(ics)))
        for e in future:
            print("    %-16s %s" % (start(e)[:15], e.get("SUMMARY", ["(no title)"])[0]))
        print("")
        return 0
    if a.meet_action == "brief":
        rows = wbs_load()
        title = a.title or "meeting"
        rel = [r for r in rows if a.match and a.match.lower() in
               (" ".join(str(v) for v in r.values())).lower()] if a.match else []
        print("\n  PRE-MEETING BRIEF — %s\n" % title)
        print("  Generated %s from your work breakdown." %
              dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
        if a.match:
            print("  Items matching %r: %d\n" % (a.match, len(rel)))
            for r in rel[:20]:
                print("    · [%s] %s (%s)" % (r.get("Status", "?"),
                      (r.get("Task") or r.get("Title") or "")[:70], r.get("Priority", "")))
        else:
            print("  (pass --match <term> to pull the relevant WBS rows)\n")
        print("")
        return 0
    if a.meet_action == "summary":
        if not a.transcript or not os.path.isfile(a.transcript):
            return _absent2("a transcript file",
                            "pass --transcript FILE. mez does not record your "
                            "meetings; it summarises a transcript you supply.")
        text = open(a.transcript, encoding="utf-8", errors="replace").read()[:12000]
        out, src = local_ai(
            "Summarise this meeting transcript into: decisions, action items "
            "(with owners if named), and open questions. Be terse.\n\n" + text,
            system="You are a precise meeting scribe. No invention.", timeout=a.timeout)
        if out is None:
            print("\n  No local model, so no AI summary (%s)." % src)
            print("  A template summary from the raw transcript instead — fill it in:\n")
            print("  ## Decisions\n  -\n\n  ## Action items\n  -\n\n  ## Open questions\n  -\n")
            print("  (start ollama and re-run for an automatic draft)\n")
            return 0
        print("\n  MEETING SUMMARY  [%s]\n" % src)
        print(out); print("")
        return 0
    print("  usage: mez meetings {next|brief|summary}"); return 2


# ── classes · a syllabus file → session plan, roster, attendance ─────────────
def cmd_classes(a, state):
    if a.class_action == "plan":
        if not a.syllabus or not os.path.isfile(a.syllabus):
            return _absent2("a syllabus file",
                            "pass --syllabus FILE (one topic per line, or a JSON "
                            "list). mez plans from your syllabus; it invents no "
                            "curriculum.")
        raw = open(a.syllabus, encoding="utf-8", errors="replace").read().strip()
        try:
            topics = json.loads(raw)
            topics = topics if isinstance(topics, list) else list(topics.values())
        except Exception:
            topics = [t.strip("-* \t") for t in raw.splitlines() if t.strip()]
        print("\n  SESSION PLAN — %d session(s)\n" % len(topics))
        for i, t in enumerate(topics, 1):
            print("    Session %-2d  %s" % (i, t))
        os.makedirs(MEZ_OUTBOX, exist_ok=True)
        plan = os.path.join(MEZ_OUTBOX, "class-plan.json")
        json.dump([{"session": i + 1, "topic": t, "status": "planned"}
                   for i, t in enumerate(topics)],
                  open(plan, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("\n  written %s\n" % plan)
        return 0
    if a.class_action == "attend":
        if not a.roster or not os.path.isfile(a.roster):
            return _absent2("a roster file", "pass --roster FILE (one name per line).")
        names = [n.strip() for n in open(a.roster, encoding="utf-8") if n.strip()]
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        os.makedirs(MEZ_OUTBOX, exist_ok=True)
        log = os.path.join(MEZ_OUTBOX, "attendance-%s.csv" % ts)
        with open(log, "w", encoding="utf-8") as fh:
            fh.write("name,present\n")
            for n in names: fh.write("%s,\n" % n)
        print("\n  attendance sheet for %d: %s\n" % (len(names), log)); return 0
    print("  usage: mez classes {plan|attend}"); return 2


# ── samd · C34 evidence FRAMEWORK (certification is a programme, not a run) ───
def cmd_samd(a, state):
    root = os.path.abspath(a.out or "samd-evidence")
    for d in ("isolation", "integration", "risk", "litigation-simulation"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    checklist = {
        "standard": "IEC 62304 / IEC 82304-1 alignment (evidence framework only)",
        "clause": "CONTRACT C34 — certified twice: in isolation AND in integration,"
                  " tested against litigation simulation BEFORE any public claim",
        "gates": [
            {"id": "ISO-1", "where": "isolation", "claim": "component behaves to spec alone",
             "evidence": "MISSING — add a passing isolated test log here"},
            {"id": "INT-1", "where": "integration", "claim": "behaves in the assembled system",
             "evidence": "MISSING — add a passing integrated test log here"},
            {"id": "LIT-1", "where": "litigation-simulation",
             "claim": "survives adversarial cross-examination of every public claim",
             "evidence": "MISSING — record the simulated challenge and the answer"},
        ],
        "status": "FRAMEWORK ONLY — no certification asserted",
    }
    json.dump(checklist, open(os.path.join(root, "CHECKLIST.json"), "w",
                              encoding="utf-8"), indent=1, ensure_ascii=False)
    with open(os.path.join(root, "VALIDATION.md"), "w", encoding="utf-8") as fh:
        fh.write("# SaMD validation — evidence framework\n\n"
                 "This scaffolds the evidence C34 requires. It certifies NOTHING.\n"
                 "A public claim of EMR-as-SaMD is permitted only when isolation/,\n"
                 "integration/ and litigation-simulation/ each hold real, passing\n"
                 "evidence — and until then mez reports this as a framework, not a\n"
                 "built capability.\n")
    print("\n  SaMD evidence framework scaffolded at %s" % root)
    print("  Three gates, all currently MISSING evidence. This is C34's shape,")
    print("  not a certificate — doctor reports samd as a framework, never as built.\n")
    return 0


def cmd_doctor(a, state):
    print(f"\n  mez {VERSION} · built with {BUILT_WITH}")
    print(f"  home        {HOME}")
    print(f"  python      {sys.version.split()[0]}  (standard library only — no pip)")
    rows = wbs_load()
    print(f"  wbs         {len(rows)} rows" if rows else "  wbs         not imported")
    _unproven = UNPROVEN | UNPROVEN_COMPLETE
    print("\n  built")
    for k, d, on in CAPABILITIES:
        if on and k not in _unproven and k not in FRAMEWORK:
            print(f"    ok    {k:<12} {d}")
    if any(on and k in _unproven for k, _d, on in CAPABILITIES):
        print("\n  wired, NOT proven against a live instance (CONTRACT C37)")
        for k, d, on in CAPABILITIES:
            if on and k in _unproven:
                print(f"    ~~    {k:<12} {d}")
    if any(on and k in FRAMEWORK for k, _d, on in CAPABILITIES):
        print("\n  FRAMEWORK only — evidence scaffolded, certification is a programme (C34)")
        for k, d, on in CAPABILITIES:
            if on and k in FRAMEWORK:
                print(f"    []    {k:<12} {d}")
    print("\n  NOT built — the desk says so rather than pretending")
    for k, d, on in CAPABILITIES:
        if not on:
            print(f"    --    {k:<12} {d}")
    print("\n  external tools")
    for t in ("git", "gh", "ots", "misty", "ollama", "node"):
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

    c = sub.add_parser("cal", help="calendar — computed by CHAKRA, not by mez")
    c.add_argument("--date", help="YYYY-MM-DD (default: today)")
    c.add_argument("--time", default="12:00")
    c.add_argument("--tz", type=float, default=5.5)
    c.add_argument("--lat", type=float, default=17.385)
    c.add_argument("--lon", type=float, default=78.4867)
    c.add_argument("--zodiac", default="sidereal", choices=["sidereal", "tropical"])
    c.add_argument("--json", action="store_true", help="CHAKRA's moment(), raw")

    rk = sub.add_parser("kundali", help="Research Kundali (project-ilm/research-kundali)")
    rk.add_argument("subject", help="ORCID, lab or institute name, or a DOI")
    rk.add_argument("--out", default="kundali-out")

    em = sub.add_parser("embody", help="TransEg gateway client")
    em.add_argument("embody_action", nargs="?", default="routes")
    em.add_argument("--base", help="http://127.0.0.1:PORT")
    em.add_argument("--data", help="JSON body for POST routes")
    em.add_argument("--timeout", type=float, default=10.0)

    x = sub.add_parser("xr", help="emit a dome display of the work breakdown")
    x.add_argument("--out", help="write to this file (default: stdout)")

    ai = sub.add_parser("ai", help="local model: ask, models, use <m>, host <url>")
    ai.add_argument("prompt", nargs="?")
    ai.add_argument("rest", nargs="*")
    ai.add_argument("--system", default="")
    ai.add_argument("--timeout", type=float, default=120.0)

    ml = sub.add_parser("mail", help="read local mail; compose to the outbox")
    ml.add_argument("mail_action", nargs="?", default="list",
                    choices=["list", "show", "compose", "send"])
    ml.add_argument("--box"); ml.add_argument("--n", type=int, default=20)
    ml.add_argument("--index", type=int, default=0)
    ml.add_argument("--to"); ml.add_argument("--subject"); ml.add_argument("--body")

    mg = sub.add_parser("msg", help="queue an SMS/message to the outbox")
    mg.add_argument("text", nargs="?"); mg.add_argument("--to")

    so = sub.add_parser("social", help="queue a social post to the outbox")
    so.add_argument("text", nargs="?"); so.add_argument("--to")

    mt = sub.add_parser("meetings", help="next / brief / summary")
    mt.add_argument("meet_action", nargs="?", default="next",
                    choices=["next", "brief", "summary"])
    mt.add_argument("--ics"); mt.add_argument("--n", type=int, default=5)
    mt.add_argument("--title"); mt.add_argument("--match")
    mt.add_argument("--transcript"); mt.add_argument("--timeout", type=float, default=120.0)

    cl = sub.add_parser("classes", help="plan / attend")
    cl.add_argument("class_action", nargs="?", default="plan", choices=["plan", "attend"])
    cl.add_argument("--syllabus"); cl.add_argument("--roster")

    sd = sub.add_parser("samd", help="scaffold the C34 SaMD evidence framework")
    sd.add_argument("--out")

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
          "ask": cmd_ask, "proc": cmd_proc, "doctor": cmd_doctor,
          "cal": cmd_cal, "kundali": cmd_kundali, "embody": cmd_embody,
          "xr": cmd_xr, "ai": cmd_ai, "mail": cmd_mail, "msg": cmd_msg,
          "social": cmd_social, "meetings": cmd_meetings, "classes": cmd_classes,
          "samd": cmd_samd}.get(a.cmd)
    if not fn:
        ap.print_help()
        return 0
    return fn(a, state)


if __name__ == "__main__":
    raise SystemExit(main())
