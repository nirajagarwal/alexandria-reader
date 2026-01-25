/* =============================================================================
   Alexandria Press - Router Module
   ============================================================================= */

import { state } from './state.js';
import * as api from './api.js';
import * as ui from './ui.js';

/* -----------------------------------------------------------------------------
   Route Handlers
   ----------------------------------------------------------------------------- */

export async function loadLibrary() {
    try {
        const books = await api.getLibrary();
        ui.renderLibrary(books);
        ui.setupSearch();
    } catch (error) {
        console.error('Failed to load library:', error);
        const shelf = document.getElementById('bookShelf');
        if (shelf) shelf.innerHTML = `<p class="error-state">Failed to load books. ${error.message}</p>`;
    }
}

export async function loadBook(bookId) {
    try {
        console.log('Router: Loading book', bookId);
        state.currentBook = await api.getBook(bookId);

        // Set basic metadata
        const currentBook = state.currentBook;
        document.title = `${currentBook.title} | Alexandria Press`;
        updateBookMeta(currentBook);

        console.log('Router: Fetching entries');
        state.currentEntries = await api.getEntries(bookId);

        // Setup UI
        ui.populateMenu(navigate, (type, label) => loadContentPage(bookId, type, label));
        ui.bindBookControls();

        // Routing logic
        const params = new URLSearchParams(window.location.search);
        const slug = params.get('slug') || params.get('amp;slug');

        if (slug) {
            navigate(slug, false);
        } else if (state.currentBook.introduction) {
            loadContentPage(bookId, 'introduction', 'Introduction');
        } else if (state.currentEntries.length > 0) {
            navigate(state.currentEntries[0].slug, true);
        } else {
            console.error('No content found for book:', bookId);
            window.location.href = '/';
        }

    } catch (error) {
        console.error('Failed to load book:', error);
        alert('Failed to load book: ' + error.message);
        window.location.href = '/';
    }
}

export async function loadContentPage(bookId, type, title) {
    try {
        const data = await api.getBookContent(bookId, type);
        ui.showContentPage(title, data.content, type, navigate);
    } catch (error) {
        console.error(`Failed to load ${type}:`, error);
        alert(`Failed to load ${type}`);
    }
}

export async function navigate(slug, pushState = true) {
    const bookId = state.currentBook.book_id;

    try {
        // Show skeleton while loading
        const contentEl = document.getElementById('entryContent');
        if (contentEl) {
            contentEl.innerHTML = `
                <div class="skeleton-loading-view">
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-text" style="width: 90%;"></div>
                    <div class="skeleton skeleton-text" style="width: 95%;"></div>
                    <div class="skeleton skeleton-text" style="width: 85%;"></div>
                    <br>
                    <div class="skeleton skeleton-text" style="width: 92%;"></div>
                    <div class="skeleton skeleton-text" style="width: 88%;"></div>
                    <div class="skeleton skeleton-text" style="width: 94%;"></div>
                </div>
            `;
            document.getElementById('bookView')?.classList.add('hidden');
            document.getElementById('contentPageView')?.classList.add('hidden');
            document.getElementById('entryView')?.classList.remove('hidden');
        }

        const data = await api.getEntry(bookId, slug);
        state.currentEntry = data.entry;

        if (pushState) {
            const newUrl = `${window.location.pathname}?id=${bookId}&slug=${slug}`;
            window.history.pushState({ bookId, slug }, '', newUrl);
        }

        ui.updateSchema();
        ui.showEntryView(data, navigate);

    } catch (error) {
        console.error('Failed to load entry:', error);
        alert('Failed to load entry');
    }
}

/* -----------------------------------------------------------------------------
   Helpers
   ----------------------------------------------------------------------------- */

function updateBookMeta(book) {
    const desc = book.descriptor || `A generated book: ${book.title}`;
    const title = `${book.title} | Alexandria Press`;
    const url = window.location.href;

    const setMeta = (sel, val) => {
        const el = document.querySelector(sel);
        if (el) el.setAttribute('content', val);
    };

    setMeta('meta[name="description"]', desc);
    setMeta('meta[property="og:title"]', title);
    setMeta('meta[property="og:description"]', desc);
    setMeta('meta[property="og:url"]', url);
    setMeta('meta[name="twitter:title"]', title);
    setMeta('meta[name="twitter:description"]', desc);
    setMeta('meta[name="twitter:url"]', url);

    if (book.cover_url) {
        const fullCoverUrl = new URL(book.cover_url, window.location.origin).href;
        setMeta('meta[property="og:image"]', fullCoverUrl);
        setMeta('meta[name="twitter:image"]', fullCoverUrl);
    }
}

/* -----------------------------------------------------------------------------
   Initialization
   ----------------------------------------------------------------------------- */

export function init() {
    window.onpopstate = (event) => {
        if (event.state && event.state.bookId && event.state.slug) {
            navigate(event.state.slug, false);
        } else {
            // Fallback for popstate without state obj (e.g. reload or external nav)
            const params = new URLSearchParams(window.location.search);
            const bookId = params.get('id');
            const slug = params.get('slug') || params.get('amp;slug');
            if (bookId && slug && state.currentBook) {
                navigate(slug, false);
            }
        }
    };
}
