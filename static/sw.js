const CACHE_NAME = 'cafeteria-pos-v4'; // bump version to force update

// Static assets + entry points to cache on install
const urlsToCache = [
  '/',                              // homepage
  '/static/manifest.json',
  '/static/sw.js',
  '/static/images/favicon.png',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png',
  '/static/images/offline.png',
  '/accounts/login/',
  '/dashboard/home/',
  '/orders/list/',
  '/orders/create/',
  '/menu/items/',
  '/offline.html'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
      .catch(err => console.error('Cache install failed:', err))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(key => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  // Skip non-GET requests and non-http(s) requests
  if (event.request.method !== 'GET' || !event.request.url.startsWith('http')) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) return cachedResponse;

        return fetch(event.request).then(networkResponse => {
          // Only cache successful responses
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
            return networkResponse;
          }

          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME)
            .then(cache => cache.put(event.request, responseToCache));

          return networkResponse;
        }).catch(() => {
          // Fallback to offline page for HTML requests
          if (event.request.headers.get('accept').includes('text/html')) {
            return caches.match('/offline.html');
          }
          // For other requests (images, etc.) → fail silently
          return new Response('', { status: 503 });
        });
      })
  );
});