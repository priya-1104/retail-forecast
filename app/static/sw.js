const CACHE_NAME = 'demandai-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/auth.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap'
];

// Install Service Worker and cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching app shell and static resources');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate Service Worker and clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[Service Worker] Clearing old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Interceptor
self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url);

  // Network-only for API calls and dynamic database operations
  if (requestUrl.pathname.startsWith('/api/') || 
      requestUrl.pathname.startsWith('/auth/') || 
      requestUrl.pathname.startsWith('/products/') ||
      requestUrl.pathname.startsWith('/sales/') ||
      requestUrl.pathname.startsWith('/forecasting/') ||
      requestUrl.pathname.startsWith('/inventory/') ||
      requestUrl.pathname.startsWith('/alerts/') ||
      requestUrl.pathname.startsWith('/reports/') ||
      requestUrl.pathname === '/users' ||
      event.request.method !== 'GET') {
    event.respondWith(fetch(event.request));
    return;
  }

  // Cache-first for static resources & app shell, falling back to network
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response; // Return from cache
        }
        
        // Fetch and cache dynamic static assets if applicable (e.g. uploaded images, icons)
        return fetch(event.request).then((networkResponse) => {
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
            return networkResponse;
          }

          // Cache newly loaded static assets on the fly (excluding third-party CDNs unless needed)
          if (requestUrl.pathname.startsWith('/static/')) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache);
            });
          }

          return networkResponse;
        });
      }).catch(() => {
        // Fallback for offline page if fetch fails and asset isn't cached
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      })
  );
});
