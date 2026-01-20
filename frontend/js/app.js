/* =============================================================================
   Alexandria Press - Application Logic
   ============================================================================= */

// Configuration
const API_BASE = '';

// State
let currentBook = null;
let currentEntries = [];
let currentEntry = null;
let isMenuOpen = false;

// Book data cache for the reader (caches full book with entry content)
const bookDataCache = {};

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

        // Setup search after loading library
        setupSearch();
    } catch (error) {
        console.error('Failed to load library:', error);
        shelf.innerHTML = `<p class="error-state">Failed to load books. ${error.message}</p>`;
    }
}

/* -----------------------------------------------------------------------------
   Search
   ----------------------------------------------------------------------------- */

let searchTimeout = null;

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    if (!searchInput || !searchResults) return;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        // Clear previous timeout
        if (searchTimeout) clearTimeout(searchTimeout);

        // Hide results if query is empty
        if (!query) {
            searchResults.classList.add('hidden');
            return;
        }

        // Debounce search
        searchTimeout = setTimeout(() => performSearch(query), 300);
    });

    // Hide results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });

    // Show results when focusing on input with existing query
    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim() && searchResults.children.length > 0) {
            searchResults.classList.remove('hidden');
        }
    });
}

async function performSearch(query) {
    const searchResults = document.getElementById('searchResults');

    // Show loading state
    searchResults.innerHTML = '<div class="search-loading">Searching...</div>';
    searchResults.classList.remove('hidden');

    try {
        const results = await fetchAPI(`/search?q=${encodeURIComponent(query)}&limit=8`);
        renderSearchResults(results);
    } catch (error) {
        console.error('Search failed:', error);
        searchResults.innerHTML = '<div class="search-empty">Search unavailable</div>';
    }
}

function renderSearchResults(results) {
    const searchResults = document.getElementById('searchResults');

    if (results.length === 0) {
        searchResults.innerHTML = '<div class="search-empty">No results found</div>';
        return;
    }

    searchResults.innerHTML = results.map(r => `
        <a href="book.html?id=${r.book_id}&slug=${r.slug}" class="search-result-item">
            <div class="search-result-name">${r.name}</div>
            <div class="search-result-book">${r.book_title}</div>
            ${r.descriptor ? `<div class="search-result-descriptor">${r.descriptor}</div>` : ''}
        </a>
    `).join('');
}

/* -----------------------------------------------------------------------------
   Book View
   ----------------------------------------------------------------------------- */

async function loadBook(bookId) {
    try {
        console.log('loadBook starting for:', bookId);
        // Load book metadata
        currentBook = await fetchAPI(`/books/${bookId}`);
        console.log('Metadata loaded:', currentBook);
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
        console.log('Fetching entries...');
        currentEntries = await fetchAPI(`/books/${bookId}/entries`);
        console.log('Entries loaded:', currentEntries.length);

        // Populate the contents menu
        populateMenu(bookId);

        // Navigate to entry from URL or first entry
        const params = new URLSearchParams(window.location.search);
        const slug = params.get('slug');

        if (slug) {
            loadEntry(bookId, slug, false); // false = don't push state again
        } else if (currentBook.introduction) {
            // content is already in currentBook, no need to fetch again
            showContentPage('Introduction', currentBook.introduction, bookId, 'introduction');
        } else if (currentEntries.length > 0) {
            loadEntry(bookId, currentEntries[0].slug, true);
        } else {
            console.error('No entries found for book:', bookId);
            window.location.href = '/';
        }

        // Setup navigation links (for Intro, Appendix, etc if visible)
        console.log('Setting up nav...');
        setupBookNav(bookId);

        // Update Schema
        console.log('Updating schema...');
        updateSchema();
        console.log('loadBook complete.');

    } catch (error) {
        console.error('Failed to load book:', error);
        console.error('Stack trace:', error.stack);
        alert('Failed to load book: ' + error.message);
        window.location.href = '/';
    }
}

// Grid view removed as per requirements

function setupBookNav(bookId) {
    // Menu trigger
    const trigger = document.getElementById('contentsTrigger');
    if (trigger) {
        trigger.onclick = toggleMenu;
    }

    // Menu close
    const closeBtn = document.getElementById('contentsClose');
    if (closeBtn) {
        closeBtn.onclick = closeMenu;
    }

    // Overlay click to close
    const overlay = document.getElementById('contentsOverlay');
    if (overlay) {
        overlay.onclick = (e) => {
            if (e.target === overlay) closeMenu();
        };
    }

    // Read Book Icon (Header)
    const readBookIcon = document.getElementById('readBookIcon');
    if (readBookIcon) {
        readBookIcon.onclick = (e) => {
            e.preventDefault();

            if (!currentBook) {
                console.warn('Book data missing');
                return;
            }

            let href = '';
            if (currentEntry) {
                const idx = currentEntries.findIndex(e => e.slug === currentEntry.slug);
                if (idx !== -1) {
                    // Match Chapter index in EPUB (1-based, padded)
                    // Note: display() expects path relative to OPF (manifest href)
                    const chapterNum = (idx + 1).toString().padStart(3, '0');
                    href = `href=chapter-${chapterNum}.xhtml`;
                }
            }

            window.location.href = `/reader.html?bookId=${currentBook.book_id}&${href}`;
        };
    }
}

function toggleMenu() {
    isMenuOpen = !isMenuOpen;
    const overlay = document.getElementById('contentsOverlay');
    if (isMenuOpen) {
        overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent scroll
    } else {
        overlay.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

function closeMenu() {
    isMenuOpen = false;
    document.getElementById('contentsOverlay').classList.add('hidden');
    document.body.style.overflow = '';
}

async function populateMenu(bookId) {
    const menuLinks = document.getElementById('contentsMenuLinks');
    if (!menuLinks) return;

    let html = '';

    // Introduction (if exists)
    if (currentBook.introduction) {
        // html += '<h3>Front Matter</h3>'; // Optional header
        html += '<ul class="menu-list front-matter">';
        html += '<li><a href="#" data-type="introduction" class="is-intro">Introduction</a></li>';
        html += '</ul>';
        html += '<hr class="menu-divider">';
    }

    // Entries Section
    html += '<h3 class="menu-section-title">Chapters</h3>';
    html += '<ul class="menu-list primary-entries">';
    html += currentEntries.map(entry => `
        <li>
            <a href="#" data-slug="${entry.slug}" class="${currentEntry && currentEntry.slug === entry.slug ? 'active' : ''}">
                <span class="menu-name">${entry.name}</span>
            </a>
        </li>
    `).join('');
    html += '</ul>';

    html += '<hr class="menu-divider">';

    // Standard pages (now at the bottom)
    const pages = [
        // 'About' / Introduction moved to top
        { id: 'appendixLink', type: 'appendix', label: 'Prompt' },
        { id: 'colophonLink', type: 'colophon', label: 'Colophon' }
    ];

    html += '<ul class="menu-list secondary-pages">';
    pages.forEach(page => {
        html += `<li><a href="#" data-type="${page.type}">${page.label}</a></li>`;
    });
    html += '</ul>';

    menuLinks.innerHTML = html;

    // Add click handlers for menu links
    menuLinks.querySelectorAll('a').forEach(link => {
        link.onclick = (e) => {
            e.preventDefault();
            const slug = link.dataset.slug;
            const type = link.dataset.type;

            if (slug) {
                loadEntry(bookId, slug);
            } else if (type) {
                let label = '';
                if (type === 'introduction') {
                    label = 'Introduction';
                } else {
                    const page = pages.find(p => p.type === type);
                    if (page) label = page.label;
                }

                if (label) {
                    loadContentPage(bookId, type, label);
                }
            }
            closeMenu();
        };
    });

    closeMenu();
}

/* -----------------------------------------------------------------------------
   Entry View
   ----------------------------------------------------------------------------- */

async function loadEntry(bookId, slug, pushState = true) {
    try {
        // Show entry view immediately to display skeleton
        const entryView = document.getElementById('entryView');
        if (entryView) entryView.classList.remove('hidden');
        document.getElementById('contentPageView').classList.add('hidden');

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
        }

        const data = await fetchAPI(`/books/${bookId}/entries/${slug}`);
        currentEntry = data.entry;

        if (pushState) {
            const newUrl = `${window.location.pathname}?id=${bookId}&slug=${slug}`;
            window.history.pushState({ bookId, slug }, '', newUrl);
        }

        updateSchema();
        showEntryView(data);
    } catch (error) {
        console.error('Failed to load entry:', error);
        alert('Failed to load entry');
    }
}

// Handle browser back/forward buttons
window.onpopstate = (event) => {
    if (event.state && event.state.bookId && event.state.slug) {
        loadEntry(event.state.bookId, event.state.slug, false);
    } else {
        // Fallback or home
        const params = new URLSearchParams(window.location.search);
        const bookId = params.get('id');
        const slug = params.get('slug');
        if (bookId && slug) {
            loadEntry(bookId, slug, false);
        }
    }
};

function showEntryView(data) {
    if (document.getElementById('bookView')) {
        document.getElementById('bookView').classList.add('hidden');
    }
    document.getElementById('contentPageView').classList.add('hidden');
    document.getElementById('entryView').classList.remove('hidden');

    const { entry, nav } = data;
    const totalEntries = currentEntries.length;

    // Update page title and meta tags to include entry name and book title
    const pageTitle = `${entry.name} | ${currentBook.title} | Alexandria Press`;
    document.title = pageTitle;
    document.querySelector('meta[property="og:title"]').setAttribute('content', pageTitle);

    // Update description meta tags with entry descriptor if available
    const entryDesc = entry.descriptor || `${entry.name} from ${currentBook.title}`;
    document.querySelector('meta[name="description"]').setAttribute('content', entryDesc);
    document.querySelector('meta[property="og:description"]').setAttribute('content', entryDesc);

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
        prevBtnFooter.textContent = '← Back';
    } else {
        prevBtn.disabled = true;
        prevBtnFooter.disabled = true;
        prevBtnFooter.textContent = '← Back';
    }

    // Next
    if (nav.next) {
        nextBtn.disabled = false;
        nextBtnFooter.disabled = false;
        nextBtn.onclick = () => loadEntry(currentBook.book_id, nav.next.slug);
        nextBtnFooter.onclick = nextBtn.onclick;
        nextBtnFooter.textContent = 'Next →';
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
        showContentPage(title, data.content, bookId, type);
    } catch (error) {
        console.error(`Failed to load ${type}:`, error);
        alert(`Failed to load ${type}`);
    }
}

function showContentPage(title, content, bookId, type) {
    if (document.getElementById('bookView')) {
        document.getElementById('bookView').classList.add('hidden');
    }
    document.getElementById('entryView').classList.add('hidden');
    document.getElementById('contentPageView').classList.remove('hidden');

    document.getElementById('contentPageView').classList.remove('hidden');

    // Title is now injected into contentEl (see below), so we don't set a header title

    const contentEl = document.getElementById('contentPageContent');
    const footer = document.getElementById('contentPageFooter');
    const pageView = document.getElementById('contentPageView');

    // Reset specific page classes
    pageView.classList.remove('is-appendix');

    // Handle content rendering based on page type
    if (type === 'appendix') {
        pageView.classList.add('is-appendix');

        // Truly raw rendering: No markdown, no paragraphs, just a pre block
        contentEl.innerHTML = '<pre class="appendix-code"><code id="rawAppendixCode"></code></pre>';
        document.getElementById('rawAppendixCode').textContent = content;

        footer.innerHTML = `<button class="start-reading-btn" id="copyAppendixBtn">Copy Prompt</button>`;
        footer.classList.remove('hidden');

        document.getElementById('copyAppendixBtn').onclick = (e) => {
            navigator.clipboard.writeText(content).then(() => {
                const btn = e.target;
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.background = 'var(--text-secondary)';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '';
                }, 2000);
            });
        };
    } else {
        // Standard rendering for About, Colophon, etc.
        let htmlContent = '';

        // Add Title right above content (User Request)
        htmlContent += `<h1 class="page-title">${title}</h1>`;

        if (content && (content.includes('#') || content.includes('**'))) {
            htmlContent += marked.parse(content);
        } else {
            // Wrap plain text in paragraphs
            htmlContent += content
                ? content.split('\n\n').map(p => `<p>${p}</p>`).join('')
                : '<p>No content available.</p>';
        }
        contentEl.innerHTML = htmlContent;
    }

    // About page logic
    if (type === 'introduction' && currentEntries.length > 0) {
        footer.innerHTML = `<button class="start-reading-btn" id="startReadingBtn">Start Reading</button>`;
        footer.classList.remove('hidden');
        document.getElementById('startReadingBtn').onclick = () => {
            loadEntry(bookId, currentEntries[0].slug);
        };
    } else {
        footer.innerHTML = '';
        footer.classList.add('hidden');
    }

    // Customize Global Header for Content Page
    if (document.getElementById('entryPosition')) {
        document.getElementById('entryPosition').textContent = '';
    }

    // Disable prev button (start of book)
    const prevBtn = document.getElementById('prevEntry');
    if (prevBtn) prevBtn.disabled = true;

    // Handle Next button logic
    const nextBtn = document.getElementById('nextEntry');
    if (nextBtn) {
        if (type === 'introduction' && currentEntries.length > 0) {
            nextBtn.disabled = false;
            nextBtn.onclick = () => {
                loadEntry(bookId, currentEntries[0].slug);
            };
        } else {
            nextBtn.disabled = true;
        }
    }

    // Ensure global back button goes to library
    const backBtn = document.getElementById('backToGrid');
    if (backBtn) {
        backBtn.onclick = () => {
            window.location.href = '/';
        };
    }

    window.scrollTo(0, 0);
}

/* -----------------------------------------------------------------------------
   SEO & Structured Data
   ----------------------------------------------------------------------------- */

function updateSchema() {
    if (!currentBook) return;

    const schema = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": currentBook.title,
        "description": currentBook.descriptor,
        "author": {
            "@type": "Organization",
            "name": "Alexandria Press"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Alexandria Press"
        }
    };

    if (currentBook.cover_url) {
        schema.image = new URL(currentBook.cover_url, window.location.origin).href;
    }

    if (currentEntry) {
        schema.mainEntity = {
            "@type": "Article",
            "headline": currentEntry.name,
            "description": currentEntry.descriptor,
            "author": {
                "@type": "Organization",
                "name": "Alexandria Press"
            }
        };
    }

    const schemaScript = document.getElementById('schemaData');
    if (schemaScript) {
        schemaScript.textContent = JSON.stringify(schema, null, 2);
    }
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
        if (isMenuOpen) {
            closeMenu();
        } else {
            document.getElementById('backToGrid').click();
        }
    }
});
