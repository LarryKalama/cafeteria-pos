// Service Worker for Cafeteria POS PWA
// Caches essential static assets for offline support

const CACHE_NAME = 'cafeteria-pos-v1';

// List of files to cache on install
// IMPORTANT: Do NOT cache Bootstrap here - it's loaded from CDN
const urlsToCache = [
  '/',                              // Root page
  '/static/manifest.json',          // PWA manifest
  '/static/images/favicon.png',     // Favicon
  // Add more local files as needed (custom CSS, images, offline pages, etc.)
  // Example:
  // '/static/css/custom.css',
  // '/static/js/custom.js',
  // '/offline.html'   // optional offline fallback page
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache:', CACHE_NAME);
        return cache.addAll(urlsToCache);
      })
      .catch(error => {
        console.error('Cache addAll failed:', error);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return from cache if found
        if (response) {
          return response;
        }

        // Otherwise fetch from network
        return fetch(event.request).catch(() => {
          // Optional: fallback to offline page or message
          // return caches.match('/offline.html');
          console.warn('Fetch failed, possibly offline:', event.request.url);
        });
      })
  );
});