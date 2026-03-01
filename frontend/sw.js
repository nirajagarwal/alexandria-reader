const CACHE_NAME = 'alexandria-v3';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/book.html',
    '/css/style.css',
    '/js/app.js',

    '/assets/favicon.png',
    'https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&family=Lora:ital,wght@0,400..700;1,400..700&family=IBM+Plex+Sans:wght@400;600&display=swap',
    'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
    'https://cdn.jsdelivr.net/npm/page-flip@2.0.7/dist/js/page-flip.browser.min.js'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API calls: Network First, fallback to Cache
    if (url.pathname.startsWith('/books') || url.pathname.startsWith('/search')) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    // Clone the response to store in cache
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseToCache);
                    });
                    return response;
                })
                .catch(() => {
                    return caches.match(event.request);
                })
        );
        return;
    }

    // Static assets: Stale-While-Revalidate (or Cache First for simplicity/speed)
    // Using Cache First for standard assets, but revalidating if needed could be better.
    // Let's go with Cache First for known assets to ensure offline works reliably.
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request).then((response) => {
                // Dynamically cache other assets?
                // For now, let's strictly cache what we know or let it slip distinct from API.
                // Actually, caching fonts/CDNs that weren't in the initial list might be good.
                return response;
            });
        })
    );
});
