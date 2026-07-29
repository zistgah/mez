"""
mez_gui — the web-first GUI.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
SPDX-License-Identifier: GPL-3.0-or-later

Web-FIRST, not web-as-a-fallback. This is the primary surface; the console is the
same data for a tty, and the immersive rung mounts this in the dome rather than
reimplementing it. One surface, three ways in.

Why the web and not a native toolkit: it is the only rung that already runs on
Ubuntu, Windows, Android and a headset without a second codebase, a build step,
a toolchain, a store, or anyone's SDK. Installable as a PWA, works offline, and
every line of it is ours (CONTRACT C32, M1).

No framework, no bundler, no CDN. Open the file and read it.
"""

APP_CSS = """
:root{
  --ink:#1b1a17; --mut:#6d6a5f; --acc:#2f6d4f; --acc2:#1f8a70; --warn:#b4531f;
  --err:#a32d1e; --line:#ddd4c0; --paper:#fffdf7; --bg:#fbf6e9; --sel:#e8f1ec;
}
@media (prefers-color-scheme: dark){
  :root{ --ink:#e9e4d6; --mut:#9a9484; --line:#3a382f; --paper:#22211c;
         --bg:#191814; --sel:#26332c; }
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);
 font:15px/1.55 "Iowan Old Style",Palatino,Georgia,serif;overscroll-behavior:none}
button,input,select,textarea{font:inherit;color:inherit}

/* shell */
.app{display:grid;grid-template-rows:auto 1fr auto;height:100%}
header{background:var(--paper);border-bottom:1px solid var(--line);
 padding:10px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;
 position:sticky;top:0;z-index:20}
header h1{margin:0;font-size:18px;letter-spacing:.02em}
header h1 small{color:var(--mut);font:11px system-ui;letter-spacing:.08em}
#q{flex:1;min-width:140px;padding:7px 12px;border:1px solid var(--line);
 border-radius:20px;background:var(--bg)}
select,button{padding:6px 11px;border:1px solid var(--line);border-radius:8px;
 background:var(--paper);cursor:pointer;font-size:13px;font-family:system-ui}
button.go{background:var(--acc);color:#fff;border-color:var(--acc)}
button:disabled{opacity:.4;cursor:not-allowed}

main{overflow:auto;padding:16px;max-width:1100px;margin:0 auto;width:100%}
.tabs{display:flex;gap:6px;padding:0 16px;background:var(--paper);
 border-bottom:1px solid var(--line);overflow-x:auto}
.tabs button{border:0;border-bottom:2px solid transparent;border-radius:0;
 background:none;padding:9px 12px;white-space:nowrap;color:var(--mut)}
.tabs button.on{color:var(--acc);border-bottom-color:var(--acc)}

.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;
 padding:15px 17px;margin-bottom:14px}
h2{font:12px system-ui;letter-spacing:.07em;text-transform:uppercase;
 color:var(--acc);margin:0 0 10px}
.grid{display:flex;gap:24px;flex-wrap:wrap}
.grid>div{min-width:88px}
.grid span{display:block;color:var(--mut);font:11px system-ui}
.grid b{font-size:25px;font-weight:500}
.warnbox{background:#fdf4ec;border-left:3px solid var(--warn);color:var(--warn);
 padding:9px 12px;border-radius:8px;font-size:13.5px;margin-top:10px}

/* work list */
.ws{margin:16px 0 4px;font-size:15px;display:flex;gap:8px;align-items:baseline}
.ws b{font-weight:600}.ws span{color:var(--mut);font:11px system-ui}
.row{display:grid;grid-template-columns:auto 46px 1fr 62px 108px 54px;gap:8px;
 align-items:start;padding:7px 6px;border-bottom:1px solid var(--line)}
.row:hover{background:var(--sel)}
.row.done .task{opacity:.45;text-decoration:line-through}
.row .id{color:var(--mut);font:11px ui-monospace;padding-top:3px}
.task{font-size:14px}
.task .d{color:var(--mut);font-size:12px;line-height:1.4}
.task .bl{color:var(--warn);font-size:11.5px;font-family:system-ui}
.row select{padding:3px 5px;font-size:11.5px;width:100%}
.who{font:10.5px system-ui;color:var(--mut);text-align:right;padding-top:5px}
.own{color:var(--acc2)}
@media(max-width:720px){
  .row{grid-template-columns:auto 1fr;gap:6px}
  .row .id,.who{display:none}
  .row select{display:inline-block;width:auto;margin:4px 6px 0 0}
}
.pill{display:inline-block;font:10.5px system-ui;padding:1px 7px;border-radius:20px;
 border:1px solid var(--line);color:var(--mut);margin-left:6px}
.pill.P0{background:#a32d1e;color:#fff;border-color:#a32d1e}
.pill.P1{background:#b4531f;color:#fff;border-color:#b4531f}
footer{background:var(--paper);border-top:1px solid var(--line);
 padding:9px 16px;color:var(--mut);font:11.5px system-ui;
 display:flex;gap:14px;align-items:center;flex-wrap:wrap}
#toast{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);
 background:var(--ink);color:var(--bg);font:13px system-ui;padding:9px 15px;
 border-radius:9px;opacity:0;transition:opacity .2s;pointer-events:none;z-index:40}
#toast.on{opacity:.95}
kbd{font:10.5px ui-monospace;border:1px solid var(--line);border-radius:4px;
 padding:1px 4px;color:var(--mut)}
.off{color:var(--mut)} .off b{color:var(--warn);font-weight:400}
"""

APP_JS = r"""
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
let S={}, ROWS=[], TAB='work', ROLE='engineer', Q='';

const esc=s=>String(s??'').replace(/[&<>"]/g,c=>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('on');
  clearTimeout(t._x);t._x=setTimeout(()=>t.classList.remove('on'),2200);}

async function api(p,o){const r=await fetch(p,o);
  if(!r.ok) throw new Error(p+' '+r.status); return r.json();}

async function load(){
  try{
    S=await api('/api/state');
    ROWS=(await api('/api/wbs?role='+encodeURIComponent(ROLE))).rows;
    render();
  }catch(e){ $('#main').innerHTML=
    '<div class="card"><h2>Cannot reach the desk</h2><p class="off">'+esc(e.message)+
    '. The server is local — if it is not running, start it with '+
    '<code>./mez serve</code>.</p></div>'; }
}

/* ---- editing. His cell, marked owned the moment he touches it. ---------- */
async function setField(id, field, value){
  const b=await api('/api/wbs/'+encodeURIComponent(id),
    {method:'POST', headers:{'Content-Type':'application/json'},
     body:JSON.stringify({[field]:value})});
  const i=ROWS.findIndex(r=>r.ID===id);
  if(i>=0) ROWS[i]=b.row;
  toast(id+' · '+field+' = '+(value||'—')+'  (yours now; an import will not clear it)');
  if(field==='Status') render();
}

const PRIOS=['','P0','P1','P2','P3'];
const STATUSES=['open','in-progress','built-not-run','blocked','done'];

function matches(r){
  if(!Q) return true;
  const q=Q.toLowerCase();
  return (r.ID+' '+r.Workstream+' '+r.Task+' '+(r.Detail||'')+' '+
          (r['Does it']||'')+' '+(r.Status||'')).toLowerCase().includes(q);
}

function workView(){
  const rows=ROWS.filter(matches);
  if(!rows.length) return '<div class="card off">Nothing matches. '+
    (S.wbs_rows?'':'<br>No breakdown loaded — <code>./mez wbs import WBS.csv</code>')+'</div>';
  const ws={}; rows.forEach(r=>(ws[r.Workstream]=ws[r.Workstream]||[]).push(r));
  let h='';
  for(const [name,rs] of Object.entries(ws)){
    const open=rs.filter(r=>r.Status!=='done').length;
    h+=`<div class="ws"><b>${esc(name)}</b><span>${open} open of ${rs.length}</span></div>`;
    h+='<div class="card" style="padding:4px 10px">';
    for(const r of rs){
      const owned=(S.owned[r.ID]||[]);
      h+=`<div class="row ${r.Status==='done'?'done':''}">
        <input type="checkbox" class="pick" value="${esc(r.ID)}">
        <div class="id">${esc(r.ID)}</div>
        <div class="task">${esc(r.Task)}
          ${r.Detail?`<div class="d">${esc(r.Detail)}</div>`:''}
          ${r['Blocked by']?`<div class="bl">blocked by ${esc(r['Blocked by'])}</div>`:''}
        </div>
        <select data-id="${esc(r.ID)}" data-f="Priority" class="${owned.includes('Priority')?'own':''}">
          ${PRIOS.map(p=>`<option value="${p}"${p===(r.Priority||'')?' selected':''}>${p||'—'}</option>`).join('')}
        </select>
        <select data-id="${esc(r.ID)}" data-f="Status" class="${owned.includes('Status')?'own':''}">
          ${STATUSES.map(s=>`<option value="${s}"${s===r.Status?' selected':''}>${s}</option>`).join('')}
        </select>
        <div class="who">${esc(r['Does it']||'')}</div>
      </div>`;
    }
    h+='</div>';
  }
  return h;
}

function bearingsView(){
  const b=S.bearings;
  const list=(t,a)=>a.length?`<div class="card"><h2>${t}</h2>`+
    a.map(r=>`<div>· <b>${esc(r.ID)}</b> ${esc(r.Task)}
      ${r.Priority?`<span class="pill ${esc(r.Priority)}">${esc(r.Priority)}</span>`:''}</div>`).join('')+
    '</div>':'';
  return `<div class="card"><h2>Bearings — ${esc(b.now)}</h2>
    <div class="grid">
      <div><span>at the desk</span><b>${b.elapsed_min}m</b></div>
      <div><span>since a break</span><b>${b.since_break_min}m</b></div>
      <div><span>unblocked</span><b>${b.ready}</b></div>
      <div><span>built, never run</span><b>${b.cheapest.length}</b></div>
      <div><span>yours alone</span><b>${b.yours.length}</b></div>
    </div>
    ${b.since_break_min>=90?`<div class="warnbox">${b.since_break_min} minutes at the
      desk without a logged break. <button id="brk">Log one</button></div>`:''}
  </div>
  ${list('P0 — unblocked', b.p0)}
  ${list('Cheapest — built, never run', b.cheapest)}
  ${list('Only you can', b.yours)}
  ${list('Blocked', b.blocked)}`;
}

function doctorView(){
  return `<div class="card"><h2>Built</h2>${
    S.caps.filter(c=>c[2]).map(c=>`<div>ok · <b>${esc(c[0])}</b> — ${esc(c[1])}</div>`).join('')}
  </div>
  <div class="card"><h2>Not built</h2>
    <p class="off">Named because they are coming. Marked because they are not here —
    a surface that pretends is worse than one that is honest.</p>
    ${S.caps.filter(c=>!c[2]).map(c=>
      `<div class="off">— <b>${esc(c[0])}</b> ${esc(c[1])}</div>`).join('')}
  </div>
  <div class="card"><h2>Tools on this machine</h2>${
    Object.entries(S.tools).map(([t,p])=>
      `<div>${p?'ok':'—'} · <b>${esc(t)}</b> <span class="off">${esc(p||'absent — its step is skipped, not faked')}</span></div>`
    ).join('')}
  </div>
  <div class="card"><h2>This surface</h2>
    <p class="off">Web-first, and deliberately: it is the only rung that runs on
    Ubuntu, Windows, Android and a headset without a second codebase, a build step,
    a store or anyone's SDK. Installable, works offline, every line ours.
    The immersive rung mounts <i>this</i> in the dome rather than reimplementing it.</p>
    <p class="off">Bound to <b>127.0.0.1</b> only. Exposing the desk to a network is a
    separate deliberate act with its own gate.</p>
  </div>`;
}

function render(){
  $('#roles').innerHTML=S.roles.map(r=>
    `<option value="${r}"${r===ROLE?' selected':''}>${r}</option>`).join('');
  $('#prov').innerHTML=S.providers.map(p=>
    `<option value="${p.id}">${p.name}${p.prefill?'':' ·copy'}</option>`).join('');
  $$('.tabs button').forEach(b=>b.classList.toggle('on', b.dataset.t===TAB));
  $('#main').innerHTML = TAB==='work'?workView() : TAB==='bearings'?bearingsView() : doctorView();
  $('#count').textContent=`${ROWS.filter(matches).length} of ${S.wbs_rows} · role ${ROLE}`;

  $$('#main select[data-f]').forEach(s=>s.onchange=()=>
    setField(s.dataset.id, s.dataset.f, s.value).catch(e=>toast('failed: '+e.message)));
  const brk=$('#brk');
  if(brk) brk.onclick=async()=>{await api('/api/break',{method:'POST'});await load();toast('break logged');};
}

/* ---- seeding: providers are data; remove them all and the desk still works */
async function seed(copyOnly){
  const ids=$$('.pick:checked').map(c=>c.value);
  if(!ids.length){ toast('Tick a row first'); return; }
  const r=await fetch('/api/prompt?ids='+encodeURIComponent(ids.join(',')));
  const text=await r.text();
  const p=S.providers.find(x=>x.id===$('#prov').value)||S.providers[0];
  if(copyOnly||!p.prefill||!p.url){
    try{ await navigator.clipboard.writeText(text); toast(
      copyOnly?'Prompt copied':'Prompt copied — paste it into '+p.name); }
    catch(e){ toast('Could not copy — the prompt is in the console'); console.log(text); }
    if(!copyOnly&&p.url) window.open(p.url,'_blank','noopener');
  } else window.open(p.url+encodeURIComponent(text),'_blank','noopener');
}

/* ---- wiring ------------------------------------------------------------- */
$$('.tabs button').forEach(b=>b.onclick=()=>{TAB=b.dataset.t;render();});
$('#roles').onchange=e=>{ROLE=e.target.value;load();};
$('#q').oninput=e=>{Q=e.target.value;render();};
$('#ask').onclick=()=>seed(false);
$('#copy').onclick=()=>seed(true);
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT') {
    if(e.key==='Escape') e.target.blur(); return; }
  if(e.key==='/'){e.preventDefault();$('#q').focus();}
  if(e.key==='1')$$('.tabs button')[0].click();
  if(e.key==='2')$$('.tabs button')[1].click();
  if(e.key==='3')$$('.tabs button')[2].click();
  if(e.key==='r')load();
});
if('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(()=>{});
load();
setInterval(()=>{ if(TAB==='bearings') load(); }, 60000);
"""

SW_JS = """/* mez service worker — the desk keeps working with the network gone. */
const C='mez-v1';
self.addEventListener('install',e=>{self.skipWaiting();
  e.waitUntil(caches.open(C).then(c=>c.addAll(['/','/app.css','/app.js'])));});
self.addEventListener('activate',e=>{e.waitUntil(clients.claim())});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(u.pathname.startsWith('/api/')) return;       /* never serve stale state */
  e.respondWith(fetch(e.request).then(r=>{
    const cp=r.clone(); caches.open(C).then(c=>c.put(e.request,cp)); return r;
  }).catch(()=>caches.match(e.request)));
});
"""

MANIFEST = """{
 "name": "mez — the desk",
 "short_name": "mez",
 "start_url": "/",
 "display": "standalone",
 "background_color": "#fbf6e9",
 "theme_color": "#2f6d4f",
 "description": "Local-first desk. No account, no vendor.",
 "icons": [{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"}]
}"""

ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#2f6d4f"/>
<rect x="12" y="26" width="40" height="5" rx="2" fill="#fffdf7"/>
<rect x="16" y="31" width="4" height="18" fill="#fffdf7"/>
<rect x="44" y="31" width="4" height="18" fill="#fffdf7"/>
<circle cx="32" cy="18" r="5" fill="#fffdf7" opacity=".9"/>
</svg>"""


def shell(version: str, built_with: str) -> str:
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>mez — the desk</title>
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/icon.svg">
<meta name="theme-color" content="#2f6d4f">
<link rel="stylesheet" href="/app.css">
</head><body>
<div class="app">
  <header>
    <h1>mez <small>میز</small></h1>
    <input id="q" placeholder="Search tasks, workstreams, status…  ( / )">
    <select id="roles"></select>
    <select id="prov"></select>
    <button class="go" id="ask">Ask</button>
    <button id="copy">Copy</button>
  </header>
  <div class="tabs">
    <button data-t="work" class="on">Work</button>
    <button data-t="bearings">Bearings</button>
    <button data-t="doctor">Doctor</button>
  </div>
  <main id="main"></main>
  <footer>
    <span id="count"></span>
    <span>mez {version} · {built_with}</span>
    <span>local only · no account · no vendor</span>
    <span><kbd>/</kbd> search <kbd>1</kbd><kbd>2</kbd><kbd>3</kbd> tabs <kbd>r</kbd> reload</span>
  </footer>
</div>
<div id="toast"></div>
<script src="/app.js"></script>
</body></html>"""
