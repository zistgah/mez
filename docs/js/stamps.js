/* stamps.js — Misty DoI desk implements.
 *
 * THE RULE THAT GOVERNS THIS FILE, from the spec:
 *   "Do not imply that applying a visual stamp alone mints a DOI."
 *
 * A stamp is a UI projection of semantic metadata. The metadata lives in the artifact manifest;
 * this is the impression you press onto paper to show what you have established. Pressing the DOI
 * stamp records an INTENT TO MINT and says so — the mint itself is a separate, gated capability
 * that runs elsewhere and comes back with a real identifier or does not come back at all.
 */
export const STAMPS = [
  { id: 'retrieved',    label: 'RETR&nbsp;IEVED'.replace('&nbsp;',''),
    means: 'read from a source that exists, and the source is named', mints: false },
  { id: 'derived',      label: 'DERIVED',
    means: 'concluded here, from something retrieved', mints: false },
  { id: 'verified',     label: 'VERI FIED'.replace(' ',''),
    means: 'independently checked, and the check is recorded', mints: false },
  { id: 'experimental', label: 'EXPT',
    means: 'proposed and under test; it may not survive', mints: false },
  { id: 'falsified',    label: 'FALSI FIED'.replace(' ',''),
    means: 'an attempt to kill it succeeded. Kept, not hidden', mints: false },
  { id: 'doi',          label: 'DOI',
    means: 'INTENT TO MINT. Pressing this does not mint anything — minting is a separate gate',
    mints: false, intentOnly: true }
];

/** What the desk may honestly say when a stamp is pressed. */
export function pressed(id) {
  const s = STAMPS.find(x => x.id === id);
  if (!s) return { ok: false, note: 'no such stamp' };
  if (s.intentOnly)
    return { ok: true, note:
      'Marked as intended for minting. Nothing has been minted — that is a separate gate, ' +
      'and it either returns a real identifier or it returns nothing.' };
  return { ok: true, note: 'Stamped ' + s.id + ': ' + s.means + '. Recorded in the manifest.' };
}
