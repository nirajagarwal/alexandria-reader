const CACHE_NAME = 'alexandria-v4';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/reader.html',
    '/css/style.css',
    '/css/reader.css',
    '/js/app.js',
    '/js/texture.js',
    '/assets/favicon.png',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) =>
            Promise.all(
                cacheNames
                    .filter((n) => n !== CACHE_NAME)
                    .map((n) => caches.delete(n))
            )
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API and epub files: network first
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/outputs/')) {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
        return;
    }

    // Static assets: cache first
    event.respondWith(
        caches.match(event.request).then(
            (cached) => cached || fetch(event.request)
        )
    );
});
