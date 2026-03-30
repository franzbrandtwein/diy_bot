/* ── Gewächshaus Konfigurator – Service Worker ─────────────────────────── */
const CACHE   = 'gwh-v1';
const OFFLINE = '/offline';

/* Dateien, die beim Install sofort gecacht werden (App Shell) */
const PRECACHE = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

/* ── Install: App Shell vorhalten ─────────────────────────────────────── */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(c => c.addAll(PRECACHE))
  );
  self.skipWaiting();
});

/* ── Activate: alte Caches löschen ───────────────────────────────────── */
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

/* ── Fetch-Strategie ──────────────────────────────────────────────────── */
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  /* API-Calls und Build-Requests: immer Netzwerk, kein Cache */
  if (url.pathname.startsWith('/api/') || url.pathname === '/api/build') {
    return; // browser handles it directly
  }

  /* GLB / STL / PDF: Network-first, dann Cache */
  if (url.pathname.endsWith('.glb') ||
      url.pathname.endsWith('.stl') ||
      url.pathname.endsWith('.pdf')) {
    event.respondWith(
      fetch(event.request)
        .then(resp => {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(event.request, clone));
          return resp;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  /* Alles andere: Cache-first, Netzwerk als Fallback */
  event.respondWith(
    caches.match(event.request).then(cached => {
      const network = fetch(event.request).then(resp => {
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(event.request, clone));
        }
        return resp;
      });
      return cached || network;
    })
  );
});
