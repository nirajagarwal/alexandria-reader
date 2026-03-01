/* =============================================================================
   Alexandria Press - Main App Entry Point
   ============================================================================= */

import * as router from './modules/router.js';
import * as ui from './modules/ui.js';

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            })
            .catch(err => {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    router.init();

    // Determine initial route
    const params = new URLSearchParams(window.location.search);
    const bookId = params.get('id');

    if (bookId) {
        router.loadBook(bookId);
    } else {
        router.loadLibrary();
    }
});
