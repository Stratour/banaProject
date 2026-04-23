const CACHE_VERSION = 'bana-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGE_CACHE = `${CACHE_VERSION}-pages`;

const PRECACHE_ASSETS = [
  '/static/bana/css/animate.css',
  '/static/bana/css/footer.css',
  '/static/bana/js/toast.js',
  '/static/bana/js/modal.js',
  '/static/bana/js/top-mobile-menu.js',
  '/static/bana/img/icon/icon-192.png',
  '/static/bana/img/icon/icon-512.png',
  '/static/bana/img/icon/favicon.ico',
  '/static/bana/img/logo/Bana_logo_dark_green.svg',
  '/static/css/dist/styles.css',
  '/offline/',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(PRECACHE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key.startsWith('bana-') && key !== STATIC_CACHE && key !== PAGE_CACHE)
          .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET' || url.protocol === 'ws:' || url.protocol === 'wss:') return;

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(response => {
        const clone = response.clone();
        caches.open(STATIC_CACHE).then(cache => cache.put(request, clone));
        return response;
      }))
    );
    return;
  }

  if (request.headers.get('Accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          const clone = response.clone();
          caches.open(PAGE_CACHE).then(cache => cache.put(request, clone));
          return response;
        })
        .catch(() =>
          caches.match(request).then(cached => cached || caches.match('/offline/'))
        )
    );
  }
});
