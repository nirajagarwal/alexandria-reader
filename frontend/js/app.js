/* =============================================================================
   Alexandria Press - Application Logic
   ============================================================================= */

// Configuration
const API_BASE = '';

// State
let currentBook = null;
let currentEntries = [];
let currentEntry = null;

/* -----------------------------------------------------------------------------
   API Calls
   ----------------------------------------------------------------------------- */

async function fetchAPI(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }
    return response.json();
}

/* -----------------------------------------------------------------------------
   Library View
   ----------------------------------------------------------------------------- */

async function loadLibrary() {
    const shelf = document.getElementById('bookShelf');
    if (!shelf) return;

    try {
        const books = await fetchAPI('/books');

        if (books.length === 0) {
            shelf.innerHTML = '<p class="empty-state">No books yet.</p>';
            return;
        }

        shelf.innerHTML = books.map(book => `
            <a href="book.html?id=${book.book_id}" class="book-card">
                <div class="book-card-cover">
                    ${book.cover_url
                ? `<img src="${book.cover_url}" alt="${book.title}">`
                : `<span class="book-card-cover-placeholder">${book.title.charAt(0)}</span>`
            }
                    <div class="book-card-overlay">
                        <div class="book-card-overlay-content">
                            <h2 class="book-card-title">${book.title}</h2>
                            <p class="book-card-descriptor">${book.descriptor || ''}</p>
                            <span class="book-card-button">Read</span>
                        </div>
                    </div>
                </div>
            </a>
        `).join('');
    } catch (error) {
        console.error('Failed to load library:', error);
        shelf.innerHTML = '<p class="error-state">Failed to load books.</p>';
    }
}

/* -----------------------------------------------------------------------------
   Book View
   ----------------------------------------------------------------------------- */

async function loadBook(bookId) {
    try {
        // Load book metadata
        currentBook = await fetchAPI(`/books/${bookId}`);
        document.title = `${currentBook.title} | Alexandria Press`;

        // Update Meta Tags
        const desc = currentBook.descriptor || `A generated book: ${currentBook.title}`;
        document.querySelector('meta[name="description"]').setAttribute('content', desc);
        document.querySelector('meta[property="og:title"]').setAttribute('content', `${currentBook.title} | Alexandria Press`);
        document.querySelector('meta[property="og:description"]').setAttribute('content', desc);
        if (currentBook.cover_url) {
            const fullCoverUrl = new URL(currentBook.cover_url, window.location.origin).href;
            document.querySelector('meta[property="og:image"]').setAttribute('content', fullCoverUrl);
        }

        // Load entries for navigation
        currentEntries = await fetchAPI(`/books/${bookId}/entries`);

        // Navigate directly to first entry if available
        if (currentEntries.length > 0) {
            loadEntry(bookId, currentEntries[0].slug);
        } else {
            console.error('No entries found for book:', bookId);
            window.location.href = '/';
        }

        // Setup navigation links (for Intro, Appendix, etc if visible)
        setupBookNav(bookId);

    } catch (error) {
        console.error('Failed to load book:', error);
        alert('Failed to load book');
        window.location.href = '/';
    }
}

// Grid view removed as per requirements

function setupBookNav(bookId) {
    document.getElementById('introLink').addEventListener('click', (e) => {
        e.preventDefault();
        loadContentPage(bookId, 'introduction', 'Introduction');
    });

    document.getElementById('appendixLink').addEventListener('click', (e) => {
        e.preventDefault();
        loadContentPage(bookId, 'appendix', 'Appendix: The Prompt');
    });

    document.getElementById('colophonLink').addEventListener('click', (e) => {
        e.preventDefault();
        loadContentPage(bookId, 'colophon', 'Colophon');
    });
}

/* -----------------------------------------------------------------------------
   Entry View
   ----------------------------------------------------------------------------- */

async function loadEntry(bookId, slug) {
    try {
        const data = await fetchAPI(`/books/${bookId}/entries/${slug}`);
        currentEntry = data.entry;

        showEntryView(data);
    } catch (error) {
        console.error('Failed to load entry:', error);
        alert('Failed to load entry');
    }
}

function showEntryView(data) {
    if (document.getElementById('bookView')) {
        document.getElementById('bookView').classList.add('hidden');
    }
    document.getElementById('contentPageView').classList.add('hidden');
    document.getElementById('entryView').classList.remove('hidden');

    const { entry, nav } = data;
    const totalEntries = currentEntries.length;

    // Update position
    document.getElementById('entryPosition').textContent = `${entry.order} of ${totalEntries}`;

    // Render content
    const contentEl = document.getElementById('entryContent');
    contentEl.innerHTML = marked.parse(entry.content || '');

    // Setup navigation
    setupEntryNav(nav);

    // Scroll to top
    window.scrollTo(0, 0);

    // Setup back button to go to library
    const backBtn = document.getElementById('backToGrid');
    backBtn.onclick = () => {
        window.location.href = '/';
    };

    document.getElementById('backToGridFooter').onclick = backBtn.onclick;
}

function setupEntryNav(nav) {
    const prevBtn = document.getElementById('prevEntry');
    const nextBtn = document.getElementById('nextEntry');
    const prevBtnFooter = document.getElementById('prevEntryFooter');
    const nextBtnFooter = document.getElementById('nextEntryFooter');

    // Previous
    if (nav.prev) {
        prevBtn.disabled = false;
        prevBtnFooter.disabled = false;
        prevBtn.onclick = () => loadEntry(currentBook.book_id, nav.prev.slug);
        prevBtnFooter.onclick = prevBtn.onclick;
        prevBtnFooter.textContent = `← ${nav.prev.name}`;
    } else {
        prevBtn.disabled = true;
        prevBtnFooter.disabled = true;
        prevBtnFooter.textContent = '← Previous';
    }

    // Next
    if (nav.next) {
        nextBtn.disabled = false;
        nextBtnFooter.disabled = false;
        nextBtn.onclick = () => loadEntry(currentBook.book_id, nav.next.slug);
        nextBtnFooter.onclick = nextBtn.onclick;
        nextBtnFooter.textContent = `${nav.next.name} →`;
    } else {
        nextBtn.disabled = true;
        nextBtnFooter.disabled = true;
        nextBtnFooter.textContent = 'Next →';
    }
}

/* -----------------------------------------------------------------------------
   Content Page View (Introduction, Appendix, Colophon)
   ----------------------------------------------------------------------------- */

async function loadContentPage(bookId, type, title) {
    try {
        const data = await fetchAPI(`/books/${bookId}/${type}`);
        showContentPage(title, data.content);
    } catch (error) {
        console.error(`Failed to load ${type}:`, error);
        alert(`Failed to load ${type}`);
    }
}

function showContentPage(title, content) {
    if (document.getElementById('bookView')) {
        document.getElementById('bookView').classList.add('hidden');
    }
    document.getElementById('entryView').classList.add('hidden');
    document.getElementById('contentPageView').classList.remove('hidden');

    document.getElementById('contentPageTitle').textContent = title;

    const contentEl = document.getElementById('contentPageContent');

    // Check if it looks like markdown (has headers, etc)
    if (content && (content.includes('#') || content.includes('**'))) {
        contentEl.innerHTML = marked.parse(content);
    } else {
        // Wrap plain text in paragraphs
        contentEl.innerHTML = content
            ? content.split('\n\n').map(p => `<p>${p}</p>`).join('')
            : '<p>No content available.</p>';
    }

    // Setup back button to go to library
    document.getElementById('backFromContentPage').onclick = () => {
        window.location.href = '/';
    };

    window.scrollTo(0, 0);
}

/* -----------------------------------------------------------------------------
   Keyboard Navigation
   ----------------------------------------------------------------------------- */

document.addEventListener('keydown', (e) => {
    const entryView = document.getElementById('entryView');
    if (!entryView || entryView.classList.contains('hidden')) return;

    if (e.key === 'ArrowLeft') {
        const prevBtn = document.getElementById('prevEntry');
        if (!prevBtn.disabled) prevBtn.click();
    } else if (e.key === 'ArrowRight') {
        const nextBtn = document.getElementById('nextEntry');
        if (!nextBtn.disabled) nextBtn.click();
    } else if (e.key === 'Escape') {
        document.getElementById('backToGrid').click();
    }
});
