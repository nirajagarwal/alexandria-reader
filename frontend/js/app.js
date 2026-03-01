/* =============================================================================
   Alexandria - Main App (Library Home)
   ============================================================================= */

const BOOKS_MANIFEST = '/data/books.json';

let allBooks = [];

// ─── Search ───────────────────────────────────────────────────────────────────

let searchTimeout = null;

function setupSearch() {
    const input = document.getElementById('searchInput');
    const results = document.getElementById('searchResults');
    if (!input || !results) return;

    input.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const q = e.target.value.trim();
        if (!q) { results.classList.add('hidden'); return; }
        searchTimeout = setTimeout(() => runSearch(q), 200);
    });

    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !results.contains(e.target)) {
            results.classList.add('hidden');
        }
    });

    input.addEventListener('focus', () => {
        if (input.value.trim() && !results.classList.contains('hidden')) {
            results.classList.remove('hidden');
        }
    });
}

function runSearch(query) {
    const results = document.getElementById('searchResults');
    const q = query.toLowerCase();

    const matches = [];

    for (const book of allBooks) {
        const titleMatch = book.title.toLowerCase().includes(q) || (book.subtitle || '').toLowerCase().includes(q);
        if (titleMatch) {
            matches.push({ type: 'book', book, score: 2 });
        }
        for (const ch of (book.chapters || [])) {
            if (ch.title.toLowerCase().includes(q)) {
                matches.push({ type: 'chapter', book, chapter: ch, score: 1 });
            }
        }
    }

    // Sort: books first, then chapters; dedupe books
    const seen = new Set();
    const sorted = [];
    for (const m of matches) {
        if (m.type === 'book' && !seen.has(m.book.id)) {
            seen.add(m.book.id);
            sorted.push(m);
        }
    }
    for (const m of matches) {
        if (m.type === 'chapter') sorted.push(m);
    }

    renderSearchResults(sorted.slice(0, 10), results);
}

function renderSearchResults(matches, container) {
    if (matches.length === 0) {
        container.innerHTML = '<div class="search-empty">No results found</div>';
        container.classList.remove('hidden');
        return;
    }

    container.innerHTML = matches.map(m => {
        if (m.type === 'book') {
            return `
                <a href="/reader.html?id=${m.book.id}" class="search-result-item">
                    <div class="search-result-name">${m.book.title}</div>
                    <div class="search-result-book">Book</div>
                    ${m.book.subtitle ? `<div class="search-result-descriptor">${m.book.subtitle}</div>` : ''}
                </a>`;
        } else {
            return `
                <a href="/reader.html?id=${m.book.id}&chapter=${encodeURIComponent(m.chapter.href)}" class="search-result-item">
                    <div class="search-result-name">${m.chapter.title}</div>
                    <div class="search-result-book">${m.book.title}</div>
                </a>`;
        }
    }).join('');
    container.classList.remove('hidden');
}

// ─── Library Render ───────────────────────────────────────────────────────────

function getLastReadBook() {
    try {
        return localStorage.getItem('alexandria_last_book');
    } catch { return null; }
}

function renderLibrary(books) {
    const shelf = document.getElementById('bookShelf');
    if (!shelf) return;

    const lastBookId = getLastReadBook();

    // Put last-read book first if it exists
    let ordered = [...books];
    if (lastBookId) {
        const idx = ordered.findIndex(b => b.id === lastBookId);
        if (idx > 0) {
            const [last] = ordered.splice(idx, 1);
            ordered.unshift(last);
        }
    }

    shelf.innerHTML = ordered.map((book, i) => {
        const isContinue = book.id === lastBookId && i === 0;
        return `
        <a href="/reader.html?id=${book.id}" class="book-card" aria-label="${book.title}">
            <div class="book-card-cover">
                ${book.cover
                ? `<img src="${book.cover}" alt="${book.title}" loading="lazy">`
                : `<span class="book-card-cover-placeholder">${book.title.charAt(0)}</span>`}
                <div class="book-card-overlay">
                    <div class="book-card-overlay-content">
                        <h2 class="book-card-title">${book.title}</h2>
                        ${book.subtitle ? `<p class="book-card-descriptor">${book.subtitle}</p>` : ''}
                        <span class="book-card-button">${isContinue ? 'Continue' : 'Read'}</span>
                    </div>
                </div>
            </div>
        </a>`;
    }).join('');
}

// ─── Init ─────────────────────────────────────────────────────────────────────

async function init() {
    try {
        const res = await fetch(BOOKS_MANIFEST);
        allBooks = await res.json();
        renderLibrary(allBooks);
        setupSearch();
    } catch (err) {
        const shelf = document.getElementById('bookShelf');
        if (shelf) shelf.innerHTML = '<p class="error-state">Could not load library. Please try again.</p>';
        console.error('Failed to load books:', err);
    }
}

document.addEventListener('DOMContentLoaded', init);
