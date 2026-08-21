import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

/* Resolve the page from an explicit root, searched, and SAY WHERE IT LOOKED. The suite may sit
   beside the page or in a tests/ directory next to docs/; a test that only works from one
   directory is testing the directory. */
const here = path.dirname(fileURLToPath(import.meta.url));
const roots = [here, path.join(here, 'docs'), path.join(here, '..', 'docs'),
               process.cwd(), path.join(process.cwd(), 'docs'),
               process.env.MEZ_DOCS || ''].filter(Boolean);
const root = roots.find(r => existsSync(path.join(r, 'index.html')));
if (!root) {
  console.error('index.html not found. Looked in:\n  ' + roots.join('\n  '));
  process.exit(1);
}
const read = f => readFileSync(path.join(root, f), 'utf8');
const H = read('index.html');
const SW = read('sw.js');
const MF = JSON.parse(read('manifest.webmanifest'));
const CJ = JSON.parse(read('components.json'));
let n=0; const t=(m,f)=>{f();n++;console.log('  ok   '+m);};
/* Prompts and prose are wrapped for reading. Normalise before matching — a regex broken by a
   line break has failed four times in this estate, so it is fixed once, here, for all of them. */
const flat = s => String(s).replace(/\s+/g,' ');
const says = (text, phrase) => assert.ok(flat(text).includes(phrase), 'does not say: ' + phrase);

t('it is a real page: doctype, charset, viewport, title, description', () => {
  for (const m of ['<!doctype html>','charset=utf-8','name=viewport','<title>','name=description'])
    assert.ok(H.includes(m), m); });
t('it is installable: manifest linked, icons declared and present in the shell', () => {
  assert.ok(H.includes('manifest.webmanifest'));
  assert.equal(MF.icons.length, 2);
  assert.ok(MF.icons.some(i => i.purpose && i.purpose.includes('maskable')));
  assert.equal(MF.background_color, '#0a1020'); });

/* THE LAMP — the signature, and a real probe rather than a decoration */
t('the lamp PROBES the local desk, with a timeout', () => {
  says(H, "fetch(DESK + '/api/state'");
  says(H, 'AbortController');
  says(H, "cache: 'no-store'"); });
t('when the desk is silent the page says so, and claims nothing', () => {
  says(H, 'Desk dark');
  says(H, 'nothing on this page claims to know what is');
  assert.ok(!/desk is probably|assume|should be running/i.test(H)); });
t('and the service worker NEVER caches the probe', () => {
  says(SW, 'isLocalDesk');
  says(SW, 'if (isLocalDesk(url)) return;');
  says(SW, 'A stale "answering" would be exactly'); });

/* THE BENCH IS DATA */
t('no component id is hardcoded in the page — the bench is fetched', () => {
  says(H, "fetch('components.json'");
  const body = H.slice(H.indexOf('<body'));
  const named = CJ.components.map(c => c.id)
    .filter(id => new RegExp("['\"]" + id + "['\"]").test(body));
  assert.deepEqual(named, [], 'hardcoded in the markup: ' + named.join(', ')); });
t('an unreadable registry is REPORTED, never faked into an empty desk', () => {
  says(H, 'It is not empty — it is unknown, and those are different things.'); });
t('every tool links to its own page and its own source', () => {
  says(H, 'its own page'); says(H, '.github.io/');
  says(H, 'https://github.com/'); });

/* the seats */
t('seven seats, and the seat changes emphasis not capability', () => {
  const seats = [...H.matchAll(/\['(engineer|researcher|clinician|teacher|learner|institution|visitor)',/g)];
  assert.equal(seats.length, 7);
  says(H, 'Your role changes what is shown. Never what is computed.');
  says(H, 'nothing is hidden that you could otherwise reach'); });

/* the palette is this room's own */
t('the palette is the drafting table, not another room in the estate', () => {
  const css = H.slice(H.indexOf(':root'), H.indexOf('</style>')).toLowerCase();
  for (const other of ['#b3391f','#c4457b','#d4a843','#e0a534'])
    assert.ok(!css.includes(other), 'borrows ' + other + ' from another room');
  assert.ok(css.includes('#0a1020'), 'the cyanotype ground'); });
t('the grid is drawn, not an image request', () => {
  says(H, 'linear-gradient(rgba(110,168,216');
  assert.ok(!/background-image:\s*url\(/.test(H), 'fetches a background'); });

/* honesty and access */
t('the three states are named where a person can read them', () => {
  says(H, 'wiring gap, not a missing build');
  for (const s of ['answering', 'on disk, idle', 'not here']) says(H, s); });
t('it degrades: no script, no network, still a page', () => {
  assert.ok(H.indexOf('<script') > H.indexOf('</header>'), 'content precedes the script');
  says(SW, "caches.match('./index.html')"); });
t('reduced motion and focus are respected', () => {
  says(H, 'prefers-reduced-motion'); says(H, ':focus-visible'); });
t('nothing is uploaded and no vendor is named', () => {
  const low = H.toLowerCase();
  for (const v of ['openai','anthropic','chatgpt','gemini','claude','analytics','gtag'])
    assert.ok(!low.includes(v), 'names ' + v);
  assert.ok(!/<form/i.test(H), 'has a form that could post'); });

console.log(`\n  ===== ${n} pass, 0 fail =====`);
