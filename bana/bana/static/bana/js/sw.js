const CACHE_VERSION = 'bana-v3';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGE_CACHE = `${CACHE_VERSION}-pages`;

// Pages vitrine précachées à l'installation
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

const VITRINE_URLS = [
  '/fr/',
  '/fr/devenir-yaya/',
  '/fr/comment-ca-marche/',
  '/fr/parent/',
  '/fr/contact/',
  '/fr/a-propos/',
  '/en/',
  '/nl/',
];

// Préfixes d'URL qui appartiennent à l'app connectée
const APP_PREFIXES = [
  '/fr/accounts/',
  '/fr/trajets/',
  '/fr/chat/',
  '/fr/profil/',
  '/fr/bana_admin/',
  '/fr/bug_tracker/',
  '/en/accounts/',
  '/en/trajets/',
  '/nl/accounts/',
  '/nl/trajets/',
  '/admin/',
];

function isAppUrl(pathname) {
  return APP_PREFIXES.some(prefix => pathname.startsWith(prefix));
}

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const staticCache = await caches.open(STATIC_CACHE);
    await staticCache.addAll(PRECACHE_ASSETS);
    const pageCache = await caches.open(PAGE_CACHE);
    await Promise.allSettled(VITRINE_URLS.map(url => pageCache.add(url)));
    await self.skipWaiting();
  })());
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

  // Assets statiques — cache-first
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

  if (!request.headers.get('Accept')?.includes('text/html')) return;

  // Pages app — network only (bypass HTTP cache), fallback offline
  if (isAppUrl(url.pathname)) {
    event.respondWith(
      fetch(request, { cache: 'no-store' }).catch(() => caches.match('/offline/'))
    );
    return;
  }

  // Pages vitrine — network-first, fallback cache puis offline
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
});
