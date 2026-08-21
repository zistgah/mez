/* sw.js — an offline shell for the desk.
 *
 * ONE RULE ABOVE ALL: the loopback probe is NEVER cached. A stale "answering" would be exactly
 * the pretence the contract forbids — a page insisting the desk is up when it is not. Anything
 * addressed to 127.0.0.1 or localhost goes straight to the network, every time, and a failure is
 * allowed to fail.
 */
const CACHE = 'mez-desk-v1';
const SHELL = ['./', './index.html', './components.json', './manifest.webmanifest',
               './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

function isLocalDesk(url) {
  return /^https?:\/\/(127\.0\.0\.1|localhost|\[::1\])(:\d+)?\//.test(url);
}

self.addEventListener('fetch', e => {
  const url = e.request.url;
  if (e.request.method !== 'GET') return;
  if (isLocalDesk(url)) return;                 // never cached, never intercepted
  e.respondWith(
    fetch(e.request)
      .then(r => {
        if (r && r.ok && new URL(url).origin === self.location.origin)
          caches.open(CACHE).then(c => c.put(e.request, r.clone()));
        return r;
      })
      .catch(() => caches.match(e.request).then(m => m || caches.match('./index.html')))
  );
});
