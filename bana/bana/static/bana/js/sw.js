const CACHE_VERSION = 'bana-v4';
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

const APP_PREFIXES = [
  '/fr/accounts/', '/fr/trajets/', '/fr/chat/', '/fr/profil/',
  '/fr/bana_admin/', '/fr/bug_tracker/',
  '/en/accounts/', '/en/trajets/',
  '/nl/accounts/', '/nl/trajets/',
  '/admin/',
];

function isAppUrl(pathname) {
  return APP_PREFIXES.some(prefix => pathname.startsWith(prefix));
}

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(PRECACHE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => k.startsWith('bana-') && k !== STATIC_CACHE && k !== PAGE_CACHE)
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET' || url.protocol === 'ws:' || url.protocol === 'wss:') return;

  // Assets statiques — cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(res => {
        caches.open(STATIC_CACHE).then(c => c.put(request, res.clone()));
        return res;
      }))
    );
    return;
  }

  if (!request.headers.get('Accept')?.includes('text/html')) return;

  // Pages app — réseau, fallback offline
  if (isAppUrl(url.pathname)) {
    event.respondWith(
      fetch(request)
        .catch(() => caches.match('/offline/'))
    );
    return;
  }

  // Pages vitrine — network-first, mise en cache au fil des visites
  event.respondWith(
    fetch(request)
      .then(res => {
        if (res.ok) caches.open(PAGE_CACHE).then(c => c.put(request, res.clone()));
        return res;
      })
      .catch(() => caches.match(request).then(cached => cached || caches.match('/offline/')))
  );
});
