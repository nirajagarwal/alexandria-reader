/* =============================================================================
   Alexandria Press - API Module
   ============================================================================= */

const API_BASE = '';

/**
 * Generic API fetcher
 * @param {string} endpoint 
 * @returns {Promise<any>}
 */
async function fetchAPI(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }
    return response.json();
}

/* -----------------------------------------------------------------------------
   Endpoints
   ----------------------------------------------------------------------------- */

export async function getLibrary() {
    return fetchAPI('/books');
}

export async function getBook(bookId) {
    return fetchAPI(`/books/${bookId}`);
}

export async function getEntries(bookId) {
    return fetchAPI(`/books/${bookId}/entries`);
}

export async function getEntry(bookId, slug) {
    return fetchAPI(`/books/${bookId}/entries/${slug}`);
}

export async function getBookContent(bookId, type) {
    return fetchAPI(`/books/${bookId}/${type}`);
}

export async function search(query) {
    return fetchAPI(`/search?q=${encodeURIComponent(query)}&limit=8`);
}
