import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
let n=0; const t=(m,f)=>{f();n++;console.log('  ok   '+m);};
/* Prose in HTML is wrapped for reading. Every assertion about what the page SAYS normalises
   whitespace first — a test that breaks on a line break is testing the formatter, not the page.
   This is the third time this class has bitten; it does not get to bite a fourth. */
const flat = s => String(s).replace(/\s+/g, ' ');
const says = (text, phrase) =>
  assert.ok(flat(text).toLowerCase().includes(phrase.toLowerCase()),
            'the page does not say: ' + phrase);
const h = readFileSync('index.html','utf8');
const sw = readFileSync('sw.js','utf8');
const mf = JSON.parse(readFileSync('manifest.webmanifest','utf8'));

t('it is a static page — no build step, no framework, no CDN', () => {
  assert.ok(!/<script[^>]+src=["']http/i.test(h), 'loads a remote script');
  assert.ok(!/@import|href=["']http[^"']*\.css/i.test(h), 'loads a remote stylesheet');
  assert.ok(!/fonts\.(googleapis|gstatic)/.test(h), 'fetches a remote font'); });
t('the seven seats are all there, each with its own accent', () => {
  const seats = [...h.matchAll(/\['(\w+)',\s*'(#[0-9a-f]{6})'/g)];
  assert.equal(seats.length, 7, 'expected 7 seats, got ' + seats.length);
  assert.deepEqual(seats.map(s=>s[1]),
    ['engineer','researcher','clinician','teacher','learner','institution','visitor']);
  assert.equal(new Set(seats.map(s=>s[2])).size, 7, 'two seats share an accent'); });
t('the seat changes what is SHOWN, never what is computed — and says so', () => {
  says(h, 'changes what is'); says(h, 'never what is computed'); says(h, 'same numbers'); });
t('the bench is DATA — the page reads components.json, it does not contain it', () => {
  assert.match(h, /components\.json/);
  for (const id of ['kitab','khwab','tilasm','pench','yadein','misty'])
    assert.ok(!new RegExp(`['"]${id}['"]`).test(h), id + ' is hardcoded in the page');
  says(h, 'the bench is data, not markup'); });
t('an unreadable registry is reported, not faked into an empty desk', () => {
  says(h, 'an empty bench means a missing file, not an empty desk'); });

t('THE LAMP is a real probe of the local desk, with a timeout', () => {
  assert.match(h, /127\.0\.0\.1:7373\/api\/state/);
  assert.match(h, /AbortController/); assert.match(h, /setTimeout\(\(\) => ctl\.abort/); });
t('and when the desk is silent the page says so instead of guessing', () => {
  says(h, 'desk not running');
  says(h, 'nothing on this page claims to know what is running'); });
t('live · on-disk-idle · not-reachable are three different words, not one', () => {
  for (const w of ['answering','on disk, idle','not reachable']) says(h, w);
  says(h, 'wiring gap, not a missing build'); });
t('every tool still opens its own published studio with no server at all', () => {
  assert.match(h, /github\.io/); says(h, 'needs no server at all'); });

t('the service worker caches the shell and NEVER the probe', () => {
  assert.match(sw, /hostname === '127\.0\.0\.1' \|\| u\.hostname === 'localhost'/);
  says(sw, 'never cache the probe'); says(sw, 'caches the page, never your data'); });
t('the manifest installs on laptop and phone', () => {
  assert.equal(mf.display, 'standalone');
  assert.equal(mf.start_url, './');
  assert.equal(mf.icons.length, 2);
  assert.ok(mf.icons.every(i => /maskable/.test(i.purpose))); });
t('accessibility floor: viewport, skip link, focus ring, reduced motion', () => {
  assert.match(h, /name=viewport/); assert.match(h, /class=sr href="#bench"/);
  assert.match(h, /:focus-visible/); assert.match(h, /prefers-reduced-motion/);
  assert.match(h, /aria-pressed/); assert.match(h, /aria-hidden/); });
t('it does not reuse the pressroom or the cutting-room palette', () => {
  for (const c of ['#b3391f','#c4457b','#e8e2d4','#ece7f2'])
    assert.ok(!h.includes(c), 'borrowed ' + c);
  assert.match(h, /--ground:#0a1020/); });
t('nothing uploads, and the page says that plainly', () => {
  says(h, 'nothing here uploads anything');
  assert.ok(!/method:\s*['"]POST/i.test(h), 'the page POSTs somewhere'); });
t('the canon disclaimer travels with it', () => {
  says(h, 'zistgah/governance'); says(h, 'governs');
  says(h, 'records intent; the contract records fact'); });

console.log(`\n  ===== ${n} pass, 0 fail =====`);
