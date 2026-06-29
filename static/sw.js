// Probenplaner Service Worker
// Strategie: statische Dateien → Cache-First; HTML-Seiten → Network-First mit Cache-Fallback

var CACHE = 'probenplaner-v1';

var KERN_ASSETS = [
  '/static/style.css',
  '/static/eink.css',
  '/static/app.js',
  '/static/eink.js',
  '/static/manifest.json',
  '/static/icon.svg',
];

// Installation: statische Kern-Assets voraus-cachen
self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return cache.addAll(KERN_ASSETS);
    })
  );
  self.skipWaiting();
});

// Aktivierung: veraltete Caches aufräumen
self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) { return k !== CACHE; })
            .map(function (k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

// Fetch: nur GET-Anfragen derselben Origin abfangen
self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;

  var url = new URL(e.request.url);
  if (url.origin !== self.location.origin) return;

  var accept = e.request.headers.get('accept') || '';
  var istHTML = accept.indexOf('text/html') !== -1;

  if (istHTML) {
    // HTML-Seiten: Netzwerk zuerst → bei Fehler aus Cache
    e.respondWith(
      fetch(e.request).then(function (resp) {
        var klon = resp.clone();
        caches.open(CACHE).then(function (c) { c.put(e.request, klon); });
        return resp;
      }).catch(function () {
        return caches.match(e.request);
      })
    );
  } else {
    // Statische Dateien: Cache zuerst → bei Fehler Netzwerk
    e.respondWith(
      caches.match(e.request).then(function (cached) {
        return cached || fetch(e.request).then(function (resp) {
          var klon = resp.clone();
          caches.open(CACHE).then(function (c) { c.put(e.request, klon); });
          return resp;
        });
      })
    );
  }
});
