/* work.js — the Work Interaction API.
 *
 * THE SEPARATION THE SPEC INSISTS ON:
 *   presentation → UX/session → Work Interaction API → Work IR → cycle configuration
 *
 * So: no UI component invents workflow state, and no workflow semantics live in a layout
 * component. The page asks this module questions; this module owns the packet. The same packet
 * would answer a CLI, a Pro inspector or a headset without changing meaning.
 *
 * Stages are DECLARED (workflows.json, extracted from the specification) — never hard-coded here.
 */
import { pressed } from './stamps.js';

const KEY = 'mez.work.v1';

/* Stages that cross a human authority boundary. The spec: prediction must never carry the user
   across ambiguity, publication, external transmission, deployment, safety or privacy. */
const GATE_WORDS = ['publish', 'mint', 'seal', 'deploy', 'consent', 'export',
                    'optional publication', 'package', 'safety envelope', 'review'];

/* The layered prompt contract, canonical in the spec. Not a giant universal prompt: a template
   whose variables come from the current work packet. */
const ASSEMBLY = ['system contract', 'workflow contract', 'stage contract', 'current context',
                  'relevant artifacts', 'user intent', 'constraints', 'expected output schema',
                  'evidence requirements', 'safety / privacy rules'];

function blank() {
  return { open: null, density: 'mid', stageDensity: {}, cursor: {}, stages: {},
           artifacts: [], stamps: {}, routed: null };
}

class Work {
  constructor(flows, s) { this.flows = flows; Object.assign(this, blank(), s || {}); }

  /* ── session ── */
  save() { try { localStorage.setItem(KEY, JSON.stringify(this._plain())); } catch (e) {} }
  _plain() { const { flows, ...rest } = this; return rest; }
  static restore(flows) {
    let s = null;
    try { s = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) {}
    return new Work(flows, s);
  }

  /* ── navigation ── */
  openCase(id) { this.open = id; if (id && this.cursor[id] == null) this.cursor[id] = 0; this.save(); }
  flow() { return this.flows[this.open] || null; }
  stageIndex() { return this.open ? (this.cursor[this.open] || 0) : 0; }
  stage() { const f = this.flow(); return f ? f.stages[this.stageIndex()] : null; }
  goto(i) { if (this.open) { this.cursor[this.open] = i; this.save(); } }

  /* ── density: three projections of one model, overridable per stage ── */
  setDensity(d) { this.density = d; this.save(); }
  densityFor(i) {
    const k = this.open + ':' + (i == null ? this.stageIndex() : i);
    return this.stageDensity[k] || this.density;
  }
  flipStageDensity() {
    const k = this.open + ':' + this.stageIndex();
    const now = this.densityFor();
    this.stageDensity[k] = now === 'pro' ? 'mid' : 'pro';
    this.save();
  }

  /* ── stage state ── */
  _k() { return this.open + ':' + this.stageIndex(); }
  stageState() { return this.stages[this._k()] || {}; }
  _set(p) { this.stages[this._k()] = Object.assign(this.stageState(), p); this.save(); }
  setIntent(v) { this._set({ intent: v }); }
  setResult(v) { this._set({ result: v }); }
  isDone(i) { const s = this.stages[this.open + ':' + i]; return !!(s && s.accepted); }
  isGate(s) { return GATE_WORDS.some(w => (s.id + ' ' + s.title).toLowerCase().includes(w)); }
  markExternal() { const s = this.stageState(); this._set({ external: (s.external || 0) + 1 }); }

  /* ── the prompt: assembled, never a giant universal one ── */
  assemblyOrder() { return ASSEMBLY; }
  prompt() {
    const f = this.flow(), s = this.stage();
    if (!f || !s) return '';
    const st = this.stageState();
    const prior = f.stages.slice(0, this.stageIndex())
      .map((x, i) => { const p = this.stages[this.open + ':' + i];
                       return p && p.accepted ? '  · ' + x.title + ': accepted' : null; })
      .filter(Boolean);
    const L = [];
    L.push(s.prompt.trim());
    L.push('');
    L.push('WORKFLOW CONTRACT — ' + f.title + ' (' + f.domain + ')');
    L.push('  canonical input: ' + (f.input || 'declared by the work'));
    L.push('  canonical output: ' + (f.output || 'declared by the work'));
    L.push('  domain invariants, which you may not breach:');
    for (const i of f.invariants) L.push('    · ' + i);
    if (prior.length) { L.push(''); L.push('ALREADY ACCEPTED IN THIS CYCLE:'); L.push(...prior); }
    if (this.artifacts.length) {
      L.push(''); L.push('ARTIFACTS ON THE DESK:');
      for (const a of this.artifacts.slice(-8))
        L.push('  · ' + a.name + ' (' + a.kind + ', ' + a.size + ' bytes) — ' + a.provenance);
    }
    if (st.intent) { L.push(''); L.push('USER INTENT FOR THIS STAGE:'); L.push('  ' + st.intent); }
    L.push('');
    L.push('SAFETY / PRIVACY: this prompt was assembled on the user\'s own machine. It carries no');
    L.push('credentials and no file contents beyond what is named above. Do not ask for keys.');
    return L.join('\n');
  }

  /* ── artifacts: a visible file is NOT evidence that an AI produced it ── */
  addFiles(files) {
    for (const f of files)
      this.artifacts.push({
        name: f.name, size: f.size, kind: (f.type || 'file').split('/')[0],
        stage: this.stage() ? this.stage().id : null,
        // The spec is explicit: never assume a Downloads file came from the preceding action.
        provenance: 'chosen by the operator; origin not asserted',
        at: new Date().toISOString()
      });
    this.save();
    return { ok: true, note: files.length + ' added. The desk records that you chose them — ' +
             'it does not claim to know what made them.' };
  }

  /* ── stamps ── */
  stamp(id) {
    /* The order is enforced here, not in the page: what is already held on this stage decides
       whether the next implement may be pressed at all. */
    const r = pressed(id, this.stampsOn());
    if (!r.ok) return r;
    const k = this._k();
    this.stamps[k] = [...new Set([...(this.stamps[k] || []), id])];
    this.save();
    return r;
  }
  stampsOn() { return this.stamps[this._k()] || []; }

  /* ── prediction: offered, never imposed at a boundary ── */
  predict() {
    const f = this.flow(); if (!f) return null;
    const i = this.stageIndex();
    if (this.routed) return { title: this.routed, gate: false, routed: true };
    if (i + 1 >= f.stages.length) return null;
    const n = f.stages[i + 1];
    return { id: n.id, title: n.title, gate: this.isGate(n) };
  }
  routeTo(kind) { this.routed = kind; this.save(); }
  clearRoute() { this.routed = null; this.save(); }

  accept() {
    const st = this.stageState();
    if (!st.result || !st.result.trim())
      return { ok: false, note: 'Nothing captured yet. Paste what came back, or add a file.' };
    this._set({ accepted: true });
    const n = this.predict();
    if (!n) return { ok: true, note: 'Accepted. The cycle is complete.' };
    if (n.gate)
      return { ok: true, note: 'Accepted. Next is ' + n.title +
        ', which crosses a boundary only you can cross — it will not advance on its own.' };
    this.goto(this.stageIndex() + 1);
    return { ok: true, note: 'Accepted. Moved to ' + n.title + '.' };
  }

  advance() {
    const f = this.flow(); if (!f) return { ok: false };
    const n = this.predict();
    if (!n) return { ok: true, note: 'The cycle is complete.' };
    if (n.gate)
      return { ok: false, note: n.title + ' is a gate. Open it and say so yourself; ' +
               'the wheel does not turn through a boundary.' };
    this.goto(this.stageIndex() + 1);
    return { ok: true, note: 'Now at ' + n.title + '.' };
  }
}

export const WORK = Work;
