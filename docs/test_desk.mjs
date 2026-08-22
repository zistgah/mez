import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const here = path.dirname(fileURLToPath(import.meta.url));
const roots = [here, path.join(here,'docs'), path.join(here,'..','docs'), process.cwd()];
const root = roots.find(r => existsSync(path.join(r,'desk.html')));
if (!root) { console.error('desk.html not found. Looked in:\n  ' + roots.join('\n  ')); process.exit(1); }
const read = f => readFileSync(path.join(root,f),'utf8');
const H = read('desk.html');
const F = JSON.parse(read('workflows.json'));
const { WORK } = await import(path.join(root,'js/work.js'));
const { PROVIDERS, ADAPTERS } = await import(path.join(root,'js/providers.js'));
const { STAMPS, pressed, LAYERS, MARKS, blockedBy } = await import(path.join(root,'js/stamps.js'));
let n=0; const t=(m,f)=>{f();n++;console.log('  ok   '+m);};
const flat = s => String(s).replace(/\s+/g,' ');
const says = (x,p) => assert.ok(flat(x).includes(p), 'does not say: '+p);
globalThis.localStorage = { _:{}, getItem(k){return this._[k]??null}, setItem(k,v){this._[k]=v} };
const W = () => WORK.restore(F);

/* ── the retrieved sequences, unmodified ── */
t('all six cyclers, canonical sequences, 62 stages with 62 prompts', () => {
  assert.deepEqual(Object.keys(F).sort(), ['awaz','khwab','matba','pench','tilasm','yadein']);
  const total = Object.values(F).reduce((a,f)=>a+f.stages.length,0);
  assert.equal(total, 62);
  for (const f of Object.values(F)) {
    assert.equal(f.stages.length, f.sequence.length, f.id+' stages != sequence');
    assert.ok(f.invariants.length, f.id+' has no invariants');
    for (const s of f.stages) assert.ok(s.prompt.length > 200, f.id+'/'+s.id+' has no prompt');
  } });
t('the sequences are the SPEC\'s, not invented', () => {
  assert.deepEqual(F.matba.sequence,
    ['intake','inspect','organize','describe','compose','check','review','seal','publish','mint']);
  assert.equal(F.pench.sequence.length, 12);
  assert.ok(F.yadein.sequence.includes('consent gate')); });
t('no workflow inherits another\'s semantics', () => {
  const sig = Object.values(F).map(f=>f.sequence.join('>'));
  assert.equal(new Set(sig).size, sig.length); });

/* ── the separation the spec insists on ── */
t('workflow state lives in work.js, never in the page', () => {
  const body = H.slice(H.indexOf('<body'));
  for (const id of Object.keys(F))
    assert.ok(!new RegExp("['\"]"+id+"['\"]").test(body), id+' hardcoded in the page');
  says(H, "fetch('workflows.json'"); });
t('no workflow semantics in CSS', () => {
  const css = H.slice(H.indexOf(':root'), H.indexOf('</style>'));
  for (const id of Object.keys(F)) assert.ok(!css.includes(id), id+' in CSS'); });

/* ── three densities over ONE model, per-stage overridable ── */
t('easy, mid and pro are projections of the same state', () => {
  const w = W(); w.openCase('khwab');
  for (const d of ['easy','mid','pro']) { w.setDensity(d);
    assert.equal(w.stage().id, F.khwab.stages[0].id, 'density changed the model at '+d); } });
t('a single stage can be expanded while the rest stays simple', () => {
  const w = W(); w.openCase('khwab'); w.setDensity('easy');
  w.goto(3); w.flipStageDensity();
  assert.equal(w.densityFor(3), 'pro');
  assert.equal(w.densityFor(0), 'easy', 'the flip leaked to another stage'); });

/* ── zero-credential handoff, no vendor owned ── */
t('three providers exposed, none preferred, plus one you name yourself', () => {
  const names = PROVIDERS.map(p=>p.name);
  for (const v of ['ChatGPT','Claude','Gemini']) assert.ok(names.includes(v), v+' missing');
  assert.ok(!PROVIDERS.some(p=>p.default), 'a provider is marked default');
  assert.ok(names.includes('Another AI')); });
t('clipboard is the zero-credential default; the other adapters are optional', () => {
  const d = ADAPTERS.filter(a=>a.default);
  assert.equal(d.length, 1); assert.equal(d[0].id, 'clipboard'); assert.ok(d[0].keyless);
  assert.ok(ADAPTERS.find(a=>a.id==='local').keyless); });
t('the external boundary is shown BEFORE anything is offered', () => {
  says(H, 'This is where the desk ends.');
  says(H, 'Nothing has been sent.');
  assert.ok(H.indexOf('boundary') < H.indexOf('Hand it to whichever AI')); });
t('no key is ever requested and no credential is in the prompt', () => {
  const w = W(); w.openCase('matba'); w.setIntent('a paper');
  const p = w.prompt();
  says(p, 'carries no credentials');
  says(p, 'Do not ask for keys');
  assert.ok(!/api[_ ]?key|token|secret/i.test(p.replace(/keys\./,''))); });

/* ── the layered prompt contract ── */
t('the prompt is assembled from the packet, not one giant universal template', () => {
  const w = W(); w.openCase('pench'); w.goto(6); w.setIntent('a reach manoeuvre');
  const p = w.prompt();
  says(p, "stage 'safety envelope'");
  says(p, 'WORKFLOW CONTRACT — PENCH');
  says(p, 'Never invent operating limits');
  says(p, 'USER INTENT FOR THIS STAGE');
  assert.equal(w.assemblyOrder().length, 10); });
t('accepted prior stages travel forward; unaccepted ones do not', () => {
  const w = W(); w.openCase('awaz'); w.setResult('x'); w.accept();
  says(w.prompt(), 'ALREADY ACCEPTED IN THIS CYCLE'); });

/* ── human authority at the boundary ── */
t('the wheel will NOT turn through a gate', () => {
  const w = W(); w.openCase('matba'); w.goto(7);            // seal
  assert.ok(w.isGate(F.matba.stages[7]));
  const r = w.advance();
  assert.equal(r.ok, false);
  says(r.note, 'the wheel does not turn through a boundary'); });
t('accepting into a gate stops there and says whose call it is', () => {
  const w = W(); w.openCase('yadein'); w.goto(6); w.setResult('done');
  const before = w.stageIndex(); const r = w.accept();
  assert.equal(w.stageIndex(), before, 'advanced through a consent gate');
  says(r.note, 'only you can cross'); });
t('nothing is accepted on an empty result', () => {
  const w = W(); w.openCase('khwab');
  assert.equal(w.accept().ok, false); });
t('a data field never shadows a method — that shipped once', () => {
  const w = W();
  for (const k of ['routeTo','accept','advance','prompt','addFiles','stamp','predict'])
    assert.equal(typeof w[k], 'function', k + ' is shadowed by a data field'); });
t('validation failure routes to repair; ambiguity routes to clarify', () => {
  const w = W(); w.openCase('khwab'); w.routeTo('repair');
  assert.equal(w.predict().title, 'repair');
  w.routeTo('clarify'); assert.equal(w.predict().title, 'clarify'); });

/* ── artifacts: a file in a folder is not evidence ── */
t('an added file records that YOU chose it — origin is not asserted', () => {
  const w = W(); w.openCase('khwab');
  w.addFiles([{ name:'city.png', size:9, type:'image/png' }]);
  const a = w.artifacts[0];
  assert.equal(a.provenance, 'chosen by the operator; origin not asserted');
  assert.ok(!/generated|produced|created by/i.test(a.provenance)); });
t('and the desk says so out loud', () => {
  const w = W(); w.openCase('khwab');
  says(w.addFiles([{name:'a.png',size:1,type:'image/png'}]).note,
       'it does not claim to know what made them'); });

/* ── stamps: the rule that matters ── */
t('FOUR systems, not one stamp — seal, clear, attest, mint', () => {
  assert.deepEqual(LAYERS.map(l=>l.id), ['seal','clear','attest','mint']);
  assert.deepEqual(LAYERS.map(l=>l.system),
    ['Tok DOI','spiguard','Candor','Misty DoI']);
  for (const l of LAYERS) { assert.ok(l.asserts, l.id); assert.ok(l.denies, l.id+' denies nothing'); } });
t('the order is enforced, not decorative', () => {
  assert.deepEqual(blockedBy('mint', []), ['seal','clear','attest']);
  assert.deepEqual(blockedBy('mint', ['seal','clear','attest']), []);
  assert.equal(pressed('clear', []).ok, false);
  says(pressed('clear', []).note, 'seal'); });
t('the disclosure gate fails closed, and says why', () => {
  says(pressed('mint', ['seal']).note, 'fails closed on purpose');
  assert.equal(LAYERS.find(l=>l.id==='clear').failsClosed, true); });
t('pressing MINT records readiness and mints NOTHING', () => {
  const r = pressed('mint', ['seal','clear','attest']);
  assert.ok(r.ok); assert.equal(r.intentOnly, true);
  says(r.note, 'Nothing has been minted');
  says(r.note, 'IRREVERSIBLE');
  says(r.note, 'newversion, not publish'); });
t('a DOI is named as a dated public disclosure, with the patent gate', () => {
  says(pressed('mint',['seal','clear','attest']).note, 'dated public disclosure');
  says(pressed('mint',['seal','clear','attest']).note, 'pre-filing'); });
t('only mint reaches the world; only mint is irreversible', () => {
  assert.deepEqual(LAYERS.filter(l=>!l.reversible).map(l=>l.id), ['mint']);
  assert.deepEqual(LAYERS.filter(l=>l.gated).map(l=>l.id), ['mint']);
  for (const l of LAYERS.filter(x=>x.id!=='mint'))
    assert.ok(!/world/.test(l.reaches), l.id+' claims to reach the world'); });
t('epistemic marks are kept APART from publication layers', () => {
  assert.equal(MARKS.length, 5);
  for (const m of MARKS) {
    const r = pressed(m.id);
    says(r.note, 'not a publication state');
    says(r.note, 'Nothing left this machine'); }
  assert.equal(STAMPS.filter(s=>s.mints).length, 1, 'exactly one implement is the mint'); });
t('falsified is kept, not hidden', () => {
  says(STAMPS.find(s=>s.id==='falsified').means, 'Kept, not hidden'); });

/* ── it is a desk, not a dashboard ── */
t('the metaphor holds: tray of cases, a desk, toolboxes, sheets, implements', () => {
  for (const w of ['tray','case','toolbox','desk','sheet','stamp','parchment'])
    assert.ok(H.includes(w), 'missing the '+w); });
t('none of the forbidden idioms', () => {
  const css = H.slice(H.indexOf(':root'), H.indexOf('</style>')).toLowerCase();
  assert.ok(!/backdrop-filter/.test(css), 'glassmorphism');
  assert.ok(!/#0ff|#f0f|#39ff14/.test(css), 'neon');
  const low = H.toLowerCase();
  for (const w of ['dashboard','kanban','chatbot']) assert.ok(!low.includes(w), w); });
t('wood, leather, brass and parchment are the materials', () => {
  const css = H.slice(H.indexOf(':root'), H.indexOf('</style>'));
  for (const v of ['--wood','--leather','--brass','--parch']) assert.ok(css.includes(v), v); });
t('state survives: the packet is the only thing persisted', () => {
  const w = W(); w.openCase('tilasm'); w.goto(2); w.setIntent('a hall'); w.save();
  const w2 = WORK.restore(F);
  assert.equal(w2.open, 'tilasm'); assert.equal(w2.stageIndex(), 2);
  assert.equal(w2.stageState().intent, 'a hall'); });
t('a new cycler needs no change to the desk', () => {
  const F2 = { ...F, newone: { id:'newone', title:'NEWONE', domain:'Test', sequence:['a','b'],
    invariants:['x'], input:'i', output:'o',
    stages:[{id:'a',title:'A',objective:'o',prompt:'p'.repeat(210)},
            {id:'b',title:'B',objective:'o',prompt:'p'.repeat(210)}] } };
  const w = WORK.restore(F2); w.openCase('newone');
  assert.equal(w.stage().id, 'a');
  assert.ok(w.prompt().includes('WORKFLOW CONTRACT — NEWONE')); });

console.log(`\n  ===== ${n} pass, 0 fail =====`);
