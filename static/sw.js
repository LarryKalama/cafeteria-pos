// Service Worker for Cafeteria POS PWA
// Version: v7 - includes offline fallback page

const CACHE_NAME = 'cafeteria-pos-v7';

// Files to cache on install (static assets + key pages)
const urlsToCache = [
  '/',                              // Homepage
  '/static/manifest.json',
  '/static/sw.js',
  '/static/images/favicon.png',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png',
  '/offline.html',                  // Fallback page (must be here!)
  // Key dynamic pages (cached on first visit)
  '/accounts/login/',
  '/dashboard/home/',
  '/orders/list/',
  '/orders/create/',
  '/menu/items/'
  // Add more later if needed (e.g. '/inventory/', '/expenses/', etc.)
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache:', CACHE_NAME);
        console.log('Caching files:', urlsToCache);
        return cache.addAll(urlsToCache);
      })
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
  // Skip non-GET or non-http(s) requests
  if (event.request.method !== 'GET' || !event.request.url.startsWith('http')) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        // Return from cache if available
        if (cachedResponse) {
          return cachedResponse;
        }

        // Try network
        return fetch(event.request).catch(() => {
          // Always fallback to offline.html when offline
          return caches.match('/offline.html');
        });
      })
  );
});