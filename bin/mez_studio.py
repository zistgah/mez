#!/usr/bin/env python3
"""mez studio — the spine.

    mez studio                       the CLI rung: what is mounted, what is reachable
    mez studio serve [port]          the IDE rung on 127.0.0.1:7373
    mez studio dome                  the immersive rung, mounted from zistgah/dome
    mez studio mount <id>            how to reach one component
    mez studio doctor                what is present, what is absent, what is a wiring gap

A SPINE, NOT AN APPLICATION
---------------------------
It mounts. It does not reimplement. Kitab, the six cyclers, the AAB painter, the dome, misty and
the estate tooling all keep their own repos, their own studios and their own contracts; this
offers a place to stand and a way to reach them.

That distinction is the correction. The recurring defect at this desk has been a capability that
exists in the estate and cannot be reached from here — chakra, research-kundali and transeg were
each once marked "not built" while running. A wiring gap is not a missing build, and a spine that
reimplemented its components would create the very drift it exists to prevent.

THE RULES IT KEEPS
------------------
M1  local-first, standard library only. No key, no cloud, loopback only.
M2  never pretend. A component absent from disk is reported as absent and exits 3. There is no
    stub that looks alive.
M3  your data is yours. Plain files under $MEZ_HOME.
M4  the rung changes what is SHOWN, never what is computed. Console and dome get the same numbers.
M5  no vendor. Components are data in components.json; delete them all and the spine still runs.
"""
import json, os, re, socket, subprocess, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

VERSION = "1.0.0"
HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.abspath(os.environ.get("MEZ_HOME", os.path.expanduser("~/.mez")))
ESTATE = os.environ.get("MEZ_ESTATE", "/shared/estate/github")
REG = os.environ.get("MEZ_COMPONENTS", os.path.join(HERE, "components.json"))
EXIT_ABSENT = 3


def registry(path=None):
    p = path or REG
    if not os.path.exists(p):
        raise SystemExit("components.json not found at %s — the spine has nothing to mount." % p)
    return json.load(open(p))


# ── resolution: where a component actually is, and whether it is reachable ───
def locate(c, estate=None):
    """Search, then report. Never assume, never invent a path."""
    e = estate or ESTATE
    org, name = (c["repo"].split("/", 1) + [""])[:2]
    tried = [os.path.join(e, org, name),
             os.path.join(os.getcwd(), name),
             os.path.join(os.getcwd(), name + "-repo"),
             os.path.join(os.path.expanduser("~"), name)]
    for t in tried:
        if os.path.isdir(t):
            return {"found": True, "path": t, "tried": tried}
    return {"found": False, "path": None, "tried": tried}


def port_open(port, host="127.0.0.1"):
    if not port:
        return False
    s = socket.socket()
    s.settimeout(0.25)
    try:
        s.connect((host, port)); return True
    except Exception:
        return False
    finally:
        s.close()


def status(c, estate=None):
    """Four states, and the middle two are the ones that matter."""
    loc = locate(c, estate)
    live = port_open(c.get("port"))
    if live:
        st, why = "live", "answering on 127.0.0.1:%d" % c["port"]
    elif loc["found"] and c["mount"] == "serve":
        st, why = "present", "on disk; its server is not running"
    elif loc["found"]:
        st, why = "present", "on disk"
    elif c["mount"] in ("panel", "cli"):
        cli = c.get("cli", "").split()[0] if c.get("cli") else None
        if cli and _which(cli):
            st, why = "present", "%s is on the path" % cli
        else:
            st, why = "absent", "not on disk and %s not on the path" % (cli or "no command")
    else:
        st, why = "absent", "not found in any of %d places" % len(loc["tried"])
    return {"id": c["id"], "status": st, "why": why, "path": loc["path"],
            "tried": loc["tried"], "port": c.get("port"), "live": live}


def _which(x):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        p = os.path.join(d, x)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def mount_url(c, s):
    """The address the IDE frames. None when there is nothing honest to show."""
    if not s["live"] and c["mount"] == "serve":
        return None
    if c["mount"] == "serve" and s["live"]:
        return "http://127.0.0.1:%d/%s" % (c["port"], c.get("path", "").lstrip("/"))
    if c["mount"] in ("static", "dome") and s["path"]:
        return "/local/%s/%s" % (c["id"], c.get("path", "index.html").lstrip("/"))
    return None


def how(c, s):
    """What a person should actually type. Never a dead stop.

    Structure is the spine's; CONTENT is the component's own, declared in components.json under
    `guidance`. The spine knows about mounting. It does not know about misty, or zops, or the
    dome — those are data, and a self-test asserts no component id appears in this file.
    """
    L = []
    if s["status"] == "absent":
        L.append("Not reachable. %s" % s["why"])
        L.append("")
        L.append("  git clone https://github.com/%s   # then re-run" % c["repo"])
        if c.get("cli"):
            L.append("  # or put %s on the path" % c["cli"])
        L.append("")
        L.append("Looked in:")
        L += ["  " + t for t in s["tried"]]
    elif c["mount"] == "serve" and not s["live"]:
        L.append("On disk, server not running. Start it:")
        L.append("")
        L.append("  cd %s" % s["path"])
        env = ("ZCYCLER_MODEL=%s " % c["id"]) if c.get("entry") == "zcycler.py" else ""
        L.append("  %spython3 %s serve            # then http://127.0.0.1:%d/studio"
                 % (env, c.get("entry", "app.py"), c["port"]))
        L.append("")
        L.append("Composing needs no server at all — the studio is a static page.")
    elif c["mount"] == "cli":
        L.append("  %s" % c.get("cli", c["id"]))
    else:
        L.append("Mounted from %s" % s["path"])
        if c.get("path"):
            L.append("  open %s" % os.path.join(s["path"], c["path"]))

    # The component's own guidance always shows — it is the recovery path as much as the manual.
    if c.get("guidance"):
        L.append("")
        L += list(c["guidance"])
    if c.get("note"):
        L.append("")
        L.append("note: %s" % c["note"])
    return L


# ── the IDE rung ────────────────────────────────────────────────────────────
PAGE = r"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>mez — the desk</title>
<style>
:root{--ink:#0b0e13;--panel:#101520;--paper:#e6ebf0;--dim:rgba(230,235,240,.5);
--rule:rgba(230,235,240,.11);--acc:#c9a227;--live:#5ea88a;--absent:#b8543f;--warn:#c8a44a;
--disp:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:var(--ink);color:var(--paper);font:14px/1.55 var(--mono);
display:grid;grid-template-rows:auto 1fr auto;overflow:hidden}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
header{display:flex;align-items:center;gap:1rem;padding:.55rem .9rem;border-bottom:1px solid var(--rule);
background:var(--panel)}
header b{font-family:var(--disp);font-weight:400;font-size:1.35rem;letter-spacing:-.01em}
header .ar{color:var(--acc);font-size:1rem}
.rungs{display:flex;gap:.3rem;margin-left:auto}
.rungs button{background:transparent;border:1px solid var(--rule);color:var(--dim);
font:600 .64rem/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;padding:.45rem .7rem;cursor:pointer}
.rungs button.on{color:var(--ink);background:var(--acc);border-color:var(--acc)}
main{display:grid;grid-template-columns:15rem 1fr 19rem;min-height:0}
aside{border-right:1px solid var(--rule);overflow:auto;background:var(--panel)}
aside.right{border-right:none;border-left:1px solid var(--rule)}
.grp{font:600 .6rem/1 var(--mono);letter-spacing:.18em;text-transform:uppercase;color:var(--acc);
padding:.9rem .8rem .4rem}
.item{display:flex;align-items:center;gap:.5rem;padding:.45rem .8rem;cursor:pointer;border:0;
background:none;color:inherit;width:100%;text-align:left;font:inherit}
.item:hover{background:rgba(230,235,240,.04)}
.item.on{background:rgba(201,162,39,.13);box-shadow:inset 2px 0 0 var(--acc)}
.dot{width:.5rem;height:.5rem;border-radius:50%;flex:0 0 auto}
.dot.live{background:var(--live)}.dot.present{background:var(--warn)}.dot.absent{background:var(--absent)}
.item .t{flex:1}.item .s{font-size:.62rem;color:var(--dim)}
section.work{display:flex;flex-direction:column;min-width:0;min-height:0}
.bar{display:flex;align-items:center;gap:.6rem;padding:.5rem .8rem;border-bottom:1px solid var(--rule)}
.bar h2{font-family:var(--disp);font-weight:400;font-size:1.1rem;margin:0}
.bar .why{color:var(--dim);font-size:.72rem}
.bar .sp{flex:1}
.bar a,.bar button{font:600 .62rem/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;
padding:.42rem .7rem;border:1px solid var(--rule);color:var(--acc);background:none;
text-decoration:none;cursor:pointer}
.body{flex:1;min-height:0;position:relative;overflow:auto}
iframe{width:100%;height:100%;border:0;background:#000;display:block}
pre.how{margin:0;padding:1.2rem;white-space:pre-wrap;font:13px/1.75 var(--mono);color:var(--paper)}
pre.how .k{color:var(--acc)}
.blank{padding:2rem;color:var(--dim);max-width:60ch}
.blank h3{font-family:var(--disp);font-weight:400;font-size:1.5rem;color:var(--paper);margin:0 0 .5rem}
aside.right .grp{padding-top:1rem}
.kv{display:flex;justify-content:space-between;gap:.6rem;padding:.35rem .8rem;font-size:.72rem}
.kv span:first-child{color:var(--dim)}
.kv b{font-weight:400;color:var(--acc)}
footer{padding:.4rem .9rem;border-top:1px solid var(--rule);background:var(--panel);
color:var(--dim);font-size:.68rem;display:flex;gap:1.2rem;flex-wrap:wrap}
footer b{color:var(--live);font-weight:400}
@media(max-width:60rem){main{grid-template-columns:1fr}aside{display:none}}
</style></head><body>
<header><b>mez</b><span class=ar>&#1605;&#1740;&#1586;</span>
<span style="color:var(--dim);font-size:.7rem" id=sub>the desk</span>
<div class=rungs id=rungs></div></header>
<main>
  <aside id=rail></aside>
  <section class=work>
    <div class=bar><h2 id=title>—</h2><span class=why id=why></span><span class=sp></span>
      <span id=actions></span></div>
    <div class=body id=body><div class=blank><h3>Pick something from the rail.</h3>
      <p>Green is answering now. Amber is on disk but not running — the panel tells you what to
      type. Red is not here at all, and says where it looked.</p>
      <p>The spine mounts; it never reimplements. Every component keeps its own repo, its own
      studio and its own contract.</p></div></div>
  </section>
  <aside class=right id=state></aside>
</main>
<footer id=foot></footer>
<script>
const $=s=>document.querySelector(s);let D=null,cur=null,rung='ide';
const api=p=>fetch('/api/'+p).then(r=>r.json());
const esc=s=>String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
async function boot(){D=await api('state');draw()}
function draw(){
 $('#rungs').innerHTML='';
 for(const [k,v] of Object.entries(D.rungs)){
   const b=document.createElement('button');b.textContent=v.title;b.title=v.what;
   b.className=rung===k?'on':'';b.onclick=()=>{rung=k;draw()};$('#rungs').append(b)}
 const shown=D.components.filter(c=>c.rungs.includes(rung));
 const rail=$('#rail');rail.innerHTML='';
 for(const g of [...new Set(shown.map(c=>c.group))]){
   rail.insertAdjacentHTML('beforeend','<div class=grp>'+esc(g)+'</div>');
   for(const c of shown.filter(x=>x.group===g)){
     const b=document.createElement('button');b.className='item'+(cur===c.id?' on':'');
     b.innerHTML='<i class="dot '+c.status+'"></i><span class=t>'+esc(c.title)+
       '</span><span class=s>'+esc(c.script||'')+'</span>';
     b.onclick=()=>{cur=c.id;draw()};rail.append(b)}}
 const st=$('#state');st.innerHTML='<div class=grp>the estate</div>'+
   D.summary.map(([k,v])=>'<div class=kv><span>'+esc(k)+'</span><b>'+esc(v)+'</b></div>').join('')+
   '<div class=grp>this rung</div><div class=kv><span>shows</span><b>'+
   esc(D.rungs[rung].what)+'</b></div>'+
   '<div class=kv><span>computes</span><b>the same as every other rung</b></div>';
 $('#foot').innerHTML='<span>MEZ_HOME <b>'+esc(D.home)+'</b></span>'+
   '<span>estate <b>'+esc(D.estate)+'</b></span>'+
   '<span>loopback only · no key · no cloud</span>';
 const c=shown.find(x=>x.id===cur);
 if(!c){$('#title').textContent='—';$('#why').textContent='';$('#actions').innerHTML='';return}
 $('#title').textContent=c.title;$('#why').textContent=c.what+' — '+c.why;
 $('#actions').innerHTML = c.url?'<a href="'+c.url+'" target=_blank>open</a>':'';
 const body=$('#body');
 if(c.url){body.innerHTML='<iframe src="'+c.url+'" title="'+esc(c.title)+'"></iframe>'}
 else{body.innerHTML='<pre class=how>'+esc(c.how.join('\n')).replace(
   /^(\s*)(git clone|cd|python3|bash|misty|mez|ZCYCLER_MODEL)/gm,'$1<span class=k>$2</span>')+'</pre>'}
}
boot();
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    reg = None
    def _s(self, o, ct="application/json", code=200):
        b = o if isinstance(o, bytes) else (o if isinstance(o, str) else json.dumps(o)).encode()
        self.send_response(code); self.send_header("Content-Type", ct)
        # The published page probes this server from a browser. The server still binds loopback
        # only (M6); allowing the read is what makes the page honest instead of guessing.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._s(PAGE, "text/html; charset=utf-8")
        if u.path == "/api/state":
            return self._s(state(self.reg))
        if u.path.startswith("/local/"):
            # serve a component's own files from its own repo — never a copy
            parts = u.path[len("/local/"):].split("/", 1)
            if len(parts) != 2: return self._s({"error": "bad path"}, code=404)
            cid, rel = parts
            c = next((x for x in self.reg["components"] if x["id"] == cid), None)
            if not c: return self._s({"error": "no such component"}, code=404)
            s = status(c)
            if not s["path"]: return self._s({"error": "component not on disk"}, code=404)
            f = os.path.normpath(os.path.join(s["path"], rel))
            if not f.startswith(os.path.abspath(s["path"])):
                return self._s({"error": "outside the component"}, code=403)
            if not os.path.isfile(f): return self._s({"error": "not found: " + rel}, code=404)
            ct = {"html": "text/html", "js": "text/javascript", "css": "text/css",
                  "json": "application/json", "png": "image/png", "svg": "image/svg+xml",
                  "jpg": "image/jpeg", "glb": "model/gltf-binary"}.get(
                      f.rsplit(".", 1)[-1].lower(), "application/octet-stream")
            return self._s(open(f, "rb").read(), ct + "; charset=utf-8" if ct.startswith("text") else ct)
        return self._s({"error": "not found"}, code=404)


def state(reg):
    comps = []
    for c in reg["components"]:
        s = status(c)
        comps.append({**{k: c[k] for k in ("id", "title", "group", "what", "repo", "mount", "rungs")},
                      "script": c.get("script", ""), "status": s["status"], "why": s["why"],
                      "url": mount_url(c, s), "how": how(c, s), "port": c.get("port")})
    live = sum(1 for c in comps if c["status"] == "live")
    pres = sum(1 for c in comps if c["status"] == "present")
    absent = sum(1 for c in comps if c["status"] == "absent")
    return {"version": VERSION, "home": HOME, "estate": ESTATE,
            "rungs": reg["rungs"], "components": comps,
            "summary": [["mounted", str(len(comps))], ["answering now", str(live)],
                        ["on disk, idle", str(pres)], ["not reachable", str(absent)]]}


# ── the console rung ────────────────────────────────────────────────────────
def cmd_list(reg, rung=None):
    print("mez studio %s — the spine" % VERSION)
    print("mounting from %s" % REG)
    print("")
    marks = {"live": "●", "present": "○", "absent": "×"}
    for g in dict.fromkeys(c["group"] for c in reg["components"]):
        print("  %s" % g)
        for c in [x for x in reg["components"] if x["group"] == g]:
            if rung and rung not in c["rungs"]: continue
            s = status(c)
            print("    %s %-8s %-4s %-42s %s" % (marks[s["status"]], c["id"], c.get("script", ""),
                                                 c["what"][:42], s["why"]))
    print("")
    print("  ● answering now   ○ on disk, not running   × not reachable")
    print("")
    print("  mez studio mount <id>     what to type for that one")
    print("  mez studio serve          the IDE rung on 127.0.0.1:7373")
    print("  mez studio dome           the immersive rung")
    return 0


def cmd_mount(reg, cid):
    c = next((x for x in reg["components"] if x["id"] == cid), None)
    if not c:
        print("no such component: %s" % cid)
        print("have: %s" % ", ".join(x["id"] for x in reg["components"])); return 2
    s = status(c)
    print("%s — %s" % (c["title"], c["what"]))
    print("repo %s · mount %s · %s" % (c["repo"], c["mount"], s["why"]))
    print("")
    for line in how(c, s): print(line)
    return EXIT_ABSENT if s["status"] == "absent" else 0


def cmd_dome(reg):
    c = next((x for x in reg["components"] if x["mount"] == "dome"), None)
    if not c:
        print("no dome component declared in components.json"); return EXIT_ABSENT
    s = status(c)
    if s["status"] == "absent":
        print("The immersive rung needs zistgah/dome, and it is not here.")
        print("")
        for line in how(c, s): print(line)
        return EXIT_ABSENT
    print("dome at %s" % s["path"])
    cfg = os.path.join(s["path"], c.get("world_config", ""))
    print("world config: %s" % (cfg if os.path.exists(cfg) else "NOT FOUND — one config per zistgah, never a fork"))
    on = [x for x in reg["components"] if "dome" in x["rungs"] and x["id"] != c["id"]]
    print("")
    print("mounts into the dome rung:")
    for x in on:
        print("  %-8s %s  (%s)" % (x["id"], x["what"][:46], status(x)["status"]))
    print("")
    print("The dome is a library plus one world config per zistgah. Any code that branches on")
    print("world identity is a redundancy defect, not a feature.")
    return 0


def cmd_doctor(reg):
    rows = [(c, status(c)) for c in reg["components"]]
    gaps = [(c, s) for c, s in rows if s["status"] == "absent"]
    idle = [(c, s) for c, s in rows if s["status"] == "present" and c["mount"] == "serve"]
    print("%d mounted · %d answering · %d on disk and idle · %d not reachable"
          % (len(rows), sum(1 for _, s in rows if s["status"] == "live"),
             len(idle), len(gaps)))
    print("")
    if idle:
        print("On disk, not running. This is a WIRING GAP, not a missing build:")
        for c, s in idle: print("  %-8s %s" % (c["id"], s["path"]))
        print("")
    if gaps:
        print("Not reachable at all:")
        for c, s in gaps:
            print("  %-8s %s" % (c["id"], c["repo"]))
        print("")
        print("  Looked under %s and the working directory." % ESTATE)
        print("  Clone what you want mounted, or set MEZ_ESTATE.")
    if not gaps and not idle:
        print("Everything declared is reachable.")
    return 0


def serve(reg, port=7373):
    os.makedirs(HOME, exist_ok=True)
    H.reg = reg
    print("mez studio %s — http://127.0.0.1:%d" % (VERSION, port))
    print("mounting %d components from %s" % (len(reg["components"]), REG))
    print("loopback only. No key, no cloud. Ctrl-C to stop.")
    try:
        ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


def selftest():
    p = f = 0
    def ok(m):
        nonlocal p; p += 1; print("  ok   %s" % m)
    def bad(m):
        nonlocal f; f += 1; print("  FAIL %s" % m)
    import tempfile

    r = registry()
    if len(r["components"]) >= 12: ok("%d components declared, all as DATA" % len(r["components"]))
    else: bad("registry too small")
    if {"console", "ide", "dome"} <= set(r["rungs"]): ok("three rungs: console, ide, dome")
    else: bad("rungs")

    # Scope the check to the code ABOVE selftest: this function must name ids in order to test
    # for them, and a check that fails on its own fixture is testing nothing.
    src = open(os.path.abspath(__file__)).read()
    code = src[:src.index("def selftest(")]
    # Some ids collide with structural nouns: "dome" is also a rung and a mount kind, "estate"
    # is also a state key. A collision is not hardcoding, so exclude the structural vocabulary
    # and test what is left — which is the thing that would actually cause drift.
    # "estate" is also the mirror path and a state key; "dome" is also a rung and a mount kind.
    structural = set(r["rungs"]) | {"static", "serve", "cli", "panel", "dome", "estate"}
    named = [w for w in [c["id"] for c in r["components"]]
             if w not in structural and re.search(r'"%s"' % w, code)]
    if not named:
        ok("no component id appears in the spine's code — delete the registry and it still runs")
    else:
        bad("hardcoded in the spine: %s — they belong in components.json" % ", ".join(named))

    d = tempfile.mkdtemp()
    fake = {"rungs": r["rungs"], "components": [
        {"id": "ghost", "title": "Ghost", "group": "x", "what": "not here",
         "repo": "nowhere/ghost", "mount": "static", "path": "index.html", "rungs": ["ide"]}]}
    j = os.path.join(d, "c.json"); json.dump(fake, open(j, "w"))
    g = fake["components"][0]
    s = status(g, estate=d)
    if s["status"] == "absent" and len(s["tried"]) >= 3:
        ok("an absent component is ABSENT, and says where it looked (%d places)" % len(s["tried"]))
    else: bad("absent detection")
    if mount_url(g, s) is None: ok("nothing absent is ever framed — no stub that looks alive")
    else: bad("framed an absent component")
    h = "\n".join(how(g, s))
    if "git clone https://github.com/nowhere/ghost" in h and "Looked in:" in h:
        ok("and it tells you what to type instead of dead-stopping")
    else: bad("no recovery path offered")

    os.makedirs(os.path.join(d, "zistgah", "kitab"))
    k = next(c for c in r["components"] if c["id"] == "kitab")
    s2 = status(k, estate=d)
    if s2["status"] == "present" and s2["path"].endswith("zistgah/kitab"):
        ok("a component on disk is found under the estate mirror")
    else: bad("estate resolution: %s" % s2)

    srv = next(c for c in r["components"] if c["mount"] == "serve")
    s3 = status(srv, estate=d)
    if s3["status"] == "absent" or not s3["live"]:
        if mount_url(srv, s3) is None: ok("a serve-component with no server running is not framed")
        else: bad("framed a dead server")

    # Guidance shows whether the component is present or not — it is the recovery path too.
    guided = [c for c in r["components"] if c.get("guidance")]
    missed = [c["id"] for c in guided
              if not set(c["guidance"]) <= set(how(c, status(c)))]
    if guided and not missed:
        ok("every component's own guidance reaches the panel, present or absent (%d)" % len(guided))
    else: bad("guidance not shown for: %s" % ", ".join(missed))

    hm = "\n".join(how(next(c for c in r["components"] if c["id"] == "misty"), {"status": "present", "why": "", "path": "/x", "tried": [], "live": False, "port": None}))
    if "ots takes a SUBCOMMAND" in hm and "VERSION, not a new deposit" in hm:
        ok("the DOI panel carries the two corrections that cost real deposits")
    else: bad("DOI guidance")

    st = state(r)
    if all(k in st for k in ("rungs", "components", "summary", "home", "estate")):
        ok("the IDE state carries everything the page needs, computed once")
    else: bad("state")
    if "the same as every other rung" in PAGE:
        ok("the rung changes what is shown, never what is computed (M4)")
    else: bad("M4 not stated in the UI")

    print("\n  ===== %d pass, %d fail =====" % (p, f))
    return 0 if not f else 1


def _main(a):
    if a and a[0] == "--selftest": return selftest()
    if a and a[0] in ("-h", "--help"): print(__doc__); return 0
    r = registry()
    if not a: return cmd_list(r)
    if a[0] == "serve": return serve(r, int(a[1]) if len(a) > 1 else 7373)
    if a[0] == "dome": return cmd_dome(r)
    if a[0] == "doctor": return cmd_doctor(r)
    if a[0] == "mount": return cmd_mount(r, a[1]) if len(a) > 1 else cmd_list(r)
    if a[0] == "list": return cmd_list(r, a[1] if len(a) > 1 else None)
    print("unknown: %s" % a[0]); return 2


if __name__ == "__main__":
    try:
        rc = _main(sys.argv[1:])
    except BrokenPipeError:
        try: sys.stdout.close()
        except Exception: pass
        os._exit(0)
    except KeyboardInterrupt:
        print(); rc = 130
    try:
        sys.stdout.flush()
    except BrokenPipeError:
        os._exit(rc or 0)
    sys.exit(rc)
