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

        // Populate the contents menu
        populateMenu(bookId);

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
        { id: 'introLink', type: 'introduction', label: 'About' },
        { id: 'appendixLink', type: 'appendix', label: 'Prompt' },
        { id: 'colophonLink', type: 'colophon', label: 'Colophon' }
    ];

    html += '<ul class="menu-list secondary-pages">';
    pages.forEach(page => {
        html += `<li><a href="#" data-type="${page.type}">${page.label}</a></li>`;
    });
    html += '</ul>';

    menuLinks.innerHTML = html;

    // Add click handlers
    menuLinks.querySelectorAll('a').forEach(link => {
        link.onclick = (e) => {
            e.preventDefault();
            const slug = link.dataset.slug;
            const type = link.dataset.type;

            if (slug) {
                loadEntry(bookId, slug);
            } else if (type) {
                const label = pages.find(p => p.type === type).label;
                loadContentPage(bookId, type, label);
            }
            closeMenu();
        };
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
        prevBtnFooter.textContent = 'Previous';
    } else {
        prevBtn.disabled = true;
        prevBtnFooter.disabled = true;
        prevBtnFooter.textContent = 'Previous';
    }

    // Next
    if (nav.next) {
        nextBtn.disabled = false;
        nextBtnFooter.disabled = false;
        nextBtn.onclick = () => loadEntry(currentBook.book_id, nav.next.slug);
        nextBtnFooter.onclick = nextBtn.onclick;
        nextBtnFooter.textContent = 'Next';
    } else {
        nextBtn.disabled = true;
        nextBtnFooter.disabled = true;
        nextBtnFooter.textContent = 'Next';
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

    document.getElementById('contentPageTitle').textContent = title;

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
        if (content && (content.includes('#') || content.includes('**'))) {
            contentEl.innerHTML = marked.parse(content);
        } else {
            // Wrap plain text in paragraphs
            contentEl.innerHTML = content
                ? content.split('\n\n').map(p => `<p>${p}</p>`).join('')
                : '<p>No content available.</p>';
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
        if (isMenuOpen) {
            closeMenu();
        } else {
            document.getElementById('backToGrid').click();
        }
    }
});
