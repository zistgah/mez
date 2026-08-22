/* stamps.js — what stamping actually means.
 *
 * I had ONE implement called "Misty DoI" that recorded an intent. That was wrong: it collapsed
 * four separate systems, each with its own repository, its own contract and its own reason to
 * change, into a single gesture. Retrieved, they are:
 *
 *   1. TOK DOI      the ATOMIC layer.  "Register cryptographic proof, not publications."
 *                   artifact → SHA-256 → OpenTimestamps → AyeSHA encoding → registry → record.
 *                   Browser-first, no backend, keyless. The raw .ots is never stored, only its
 *                   AyeSHA encoding. Free, instant, and asserts exactly one thing: this existed
 *                   by this time. It does not say the thing is right, or yours, or published.
 *
 *   2. SPIGUARD     the GATE, and a separate component ON PURPOSE. "Misty is not the place for
 *                   the IPR filter — think CBE, don't conflate contracts and roles." Disclosure
 *                   rules change with law and compliance; minting mechanics change with the
 *                   provenance platform. Different reasons to change, different components.
 *                   spiguard JUDGES (secrets, third-party PII, IPR leakage, plagiarism, patent
 *                   language, clean-room) and emits an HMAC clearance over the subject digest —
 *                   metadata plus every file hash. It FAILS CLOSED.
 *
 *   3. CANDOR       the ATTESTATION. in-toto Statement v1 + OTS. A signed statement of intent
 *                   carrying a short digest and a REASON, so an irreversible act is one human
 *                   command with its justification attached rather than a wall of prompts.
 *                   Receipts are append-only.
 *
 *   4. MISTY DOI    the PUBLICATION layer, and the only one that reaches the outside world.
 *                   `misty publish` mints a NEW record. `misty newversion -r <latest> ...`
 *                   mints beneath an existing CONCEPT DOI. Using publish where newversion was
 *                   meant is how a lineage splits, and a split lineage cannot be merged without
 *                   the registrar. This estate already carries that scar twice.
 *
 * THE ORDER IS NOT DECORATIVE:  seal → clear → attest → mint.
 * misty verifies that a signed clearance covers THIS EXACT artifact; it knows nothing about what
 * spiguard checked. They meet at that one interface and nowhere else.
 *
 * And the thing the desk must never imply: A DOI IS A DATED PUBLIC DISCLOSURE. The MASI gate is
 * explicit — minting is blocked while a linked patent matter is pre-filing, unless defensive
 * publication is deliberately asserted. Pressing a picture of a stamp does none of this.
 */

export const LAYERS = [
  { id: 'seal',   system: 'Tok DOI',  repo: 'project-ilm/tok-doi',   order: 1,
    label: 'SEAL',  cli: 'browser, keyless — or misty ots stamp <path>',
    asserts: 'this artifact existed in this exact form by this time',
    denies:  'that it is correct, that it is yours, or that anyone has seen it',
    reversible: true, reaches: 'local + a public timestamp chain', needs: [] },

  { id: 'clear',  system: 'spiguard', repo: 'project-ilm/spiguard',  order: 2,
    label: 'CLEAR', cli: 'spiguard scan',
    asserts: 'no secrets, third-party PII, IPR leakage or unattributed material was found HERE',
    denies:  'that none exists — a scan finds what it looks for and no more',
    reversible: true, reaches: 'local only', needs: ['seal'], failsClosed: true },

  { id: 'attest', system: 'Candor',   repo: 'project-ilm/tok-doi (attest/)', order: 3,
    label: 'ATTEST', cli: 'attest/mint.sh — one command, with a reason',
    asserts: 'a named person intends this act, and said why',
    denies:  'that the act has happened',
    reversible: true, reaches: 'local, append-only receipts', needs: ['seal', 'clear'] },

  { id: 'mint',   system: 'Misty DoI', repo: 'project-ilm/misty-doi', order: 4,
    label: 'MINT', cli: 'misty newversion -r <latest> -m meta.json -f artifact',
    asserts: 'a public, dated, citable record now exists and can be resolved by anyone',
    denies:  'that it is correct — a DOI is an address, not a verdict',
    reversible: false, reaches: 'the whole world, permanently',
    needs: ['seal', 'clear', 'attest'], gated: true } ];

/* Epistemic marks. These describe the CLAIM, not the publication state, and none of them
   touches a registrar. Kept separate so pressing "verified" can never be mistaken for minting. */
export const MARKS = [
  { id: 'retrieved',    label: 'RETRIEVED',
    means: 'read from a source that exists, and the source is named' },
  { id: 'derived',      label: 'DERIVED',
    means: 'concluded here, from something retrieved' },
  { id: 'verified',     label: 'VERIFIED',
    means: 'independently checked, and the check is recorded' },
  { id: 'experimental', label: 'EXPT',
    means: 'proposed and under test; it may not survive' },
  { id: 'falsified',    label: 'FALSIFIED',
    means: 'an attempt to kill it succeeded. Kept, not hidden' } ];

/* Backwards compatible surface for the desk, now honest about which is which. */
export const STAMPS = [
  ...MARKS.map(m => ({ ...m, kind: 'mark', mints: false })),
  ...LAYERS.map(l => ({ id: l.id, label: l.label, kind: 'layer', mints: l.id === 'mint',
                        means: l.system + ' — ' + l.asserts })) ];

/** Which layers are missing before this one may be pressed. */
export function blockedBy(id, held) {
  const l = LAYERS.find(x => x.id === id);
  if (!l) return [];
  return l.needs.filter(n => !(held || []).includes(n));
}

/** What the desk may honestly say. Nothing here performs the act — it records intent to. */
export function pressed(id, held) {
  const m = MARKS.find(x => x.id === id);
  if (m) return { ok: true, kind: 'mark',
    note: 'Marked ' + m.id + ': ' + m.means + '. This is a claim about the work, ' +
          'not a publication state. Nothing left this machine.' };

  const l = LAYERS.find(x => x.id === id);
  if (!l) return { ok: false, note: 'no such implement' };

  const missing = blockedBy(id, held);
  if (missing.length)
    return { ok: false, note:
      l.label + ' comes after ' + missing.join(' and ') + '. ' +
      (missing.includes('clear')
        ? 'The disclosure gate fails closed on purpose: what has not been checked is not cleared.'
        : 'The order is seal → clear → attest → mint, and it is not decorative.') };

  if (l.id === 'mint')
    return { ok: true, kind: 'layer', intentOnly: true, note:
      'Recorded as READY TO MINT. Nothing has been minted. ' +
      'Minting runs ' + l.cli + ' outside this page, is IRREVERSIBLE, and publishes a dated ' +
      'public disclosure — which is why it is blocked while a linked patent matter is pre-filing ' +
      'unless defensive publication is deliberately asserted. ' +
      'Use newversion, not publish, or the lineage splits and cannot be merged.' };

  return { ok: true, kind: 'layer', intentOnly: true, note:
    l.label + ' (' + l.system + ') recorded as intended. It asserts: ' + l.asserts + '. ' +
    'It does NOT assert: ' + l.denies + '. The act itself runs in ' + l.repo + '.' };
}
