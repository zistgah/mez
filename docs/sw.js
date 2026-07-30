/* mez desk — offline shell. Cache-first for the app files so the desk opens
   with no network; the user's data never enters the cache (it's loaded live
   from their own files each session). */
const CACHE = "mez-desk-v1";
const ASSETS = ["./","./index.html","./manifest.webmanifest",
  "./icons/icon-192.png","./icons/icon-512.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(()=>self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(
    ks.filter(k => k!==CACHE).map(k => caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (u.origin !== location.origin) return;           // never touch cross-origin
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).catch(
    () => caches.match("./index.html"))));
});
