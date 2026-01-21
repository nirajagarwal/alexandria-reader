/* =============================================================================
   Alexandria Press - UI Module
   ============================================================================= */

import { state } from './state.js';
import * as api from './api.js';

/* -----------------------------------------------------------------------------
   Library View
   ----------------------------------------------------------------------------- */

export function renderLibrary(books) {
    const shelf = document.getElementById('bookShelf');
    if (!shelf) return;

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
}

/* -----------------------------------------------------------------------------
   Search
   ----------------------------------------------------------------------------- */

let searchTimeout = null;

export function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    if (!searchInput || !searchResults) return;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        if (searchTimeout) clearTimeout(searchTimeout);

        if (!query) {
            searchResults.classList.add('hidden');
            return;
        }

        searchTimeout = setTimeout(() => performSearch(query), 300);
    });

    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });

    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim() && searchResults.children.length > 0) {
            searchResults.classList.remove('hidden');
        }
    });
}

async function performSearch(query) {
    const searchResults = document.getElementById('searchResults');

    searchResults.innerHTML = '<div class="search-loading">Searching...</div>';
    searchResults.classList.remove('hidden');

    try {
        const results = await api.search(query);
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
   Book Views
   ----------------------------------------------------------------------------- */

export function showEntryView(data, onNavigate) {
    if (document.getElementById('bookView')) {
        document.getElementById('bookView').classList.add('hidden');
    }
    document.getElementById('contentPageView').classList.add('hidden');
    document.getElementById('entryView').classList.remove('hidden');

    const { entry, nav } = data;
    const totalEntries = state.currentEntries.length;

    // Update Meta
    updateMetaTags(entry.name, entry.descriptor);

    // Update position
    const posEl = document.getElementById('entryPosition');
    if (posEl) posEl.textContent = `${entry.order} of ${totalEntries}`;

    // Render content
    const contentEl = document.getElementById('entryContent');
    // Using global marked
    contentEl.innerHTML = marked.parse(entry.content || '');

    // Setup navigation
    setupEntryNav(nav, onNavigate);

    window.scrollTo(0, 0);

    const backBtn = document.getElementById('backToGrid');
    if (backBtn) {
        backBtn.onclick = () => { window.location.href = '/'; };
    }
    const backBtnFooter = document.getElementById('backToGridFooter');
    if (backBtnFooter) backBtnFooter.onclick = backBtn.onclick;
}

export function showContentPage(title, content, type, onNavigate) {
    if (document.getElementById('bookView')) {
        document.getElementById('bookView').classList.add('hidden');
    }
    document.getElementById('entryView').classList.add('hidden');
    document.getElementById('contentPageView').classList.remove('hidden');

    const contentEl = document.getElementById('contentPageContent');
    const footer = document.getElementById('contentPageFooter');
    const pageView = document.getElementById('contentPageView');

    pageView.classList.remove('is-appendix');

    if (type === 'appendix') {
        pageView.classList.add('is-appendix');
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
        let htmlContent = '';
        if (type === 'introduction' && state.currentEntries.length > 0) {
            htmlContent += `
                <div class="page-header-container">
                    <h1 class="page-title">${title}</h1>
                    <button class="start-reading-btn header-btn" id="startReadingBtn">Read</button>
                </div>
            `;
        } else {
            htmlContent += `<h1 class="page-title">${title}</h1>`;
        }

        if (content && (content.includes('#') || content.includes('**'))) {
            htmlContent += marked.parse(content);
        } else {
            htmlContent += content
                ? content.split('\n\n').map(p => `<p>${p}</p>`).join('')
                : '<p>No content available.</p>';
        }
        contentEl.innerHTML = htmlContent;

        const startBtn = document.getElementById('startReadingBtn');
        if (startBtn && onNavigate) {
            startBtn.onclick = () => onNavigate(state.currentEntries[0].slug);
        }
    }

    if (type !== 'appendix') {
        footer.innerHTML = '';
        footer.classList.add('hidden');
    }

    if (document.getElementById('entryPosition')) {
        document.getElementById('entryPosition').textContent = '';
    }

    // Nav buttons
    const prevBtn = document.getElementById('prevEntry');
    if (prevBtn) prevBtn.disabled = true;

    const nextBtn = document.getElementById('nextEntry');
    if (nextBtn) {
        if (type === 'introduction' && state.currentEntries.length > 0) {
            nextBtn.disabled = false;
            if (onNavigate) {
                nextBtn.onclick = () => onNavigate(state.currentEntries[0].slug);
            }
        } else {
            nextBtn.disabled = true;
        }
    }

    window.scrollTo(0, 0);
}

function updateMetaTags(titlePart, descriptor) {
    const currentBook = state.currentBook;
    const pageTitle = `${titlePart} | ${currentBook.title} | Alexandria Press`;
    document.title = pageTitle;
    const url = window.location.href;
    const desc = descriptor || `${titlePart} from ${currentBook.title}`;

    const setMeta = (sel, val) => {
        const el = document.querySelector(sel);
        if (el) el.setAttribute('content', val);
    };

    setMeta('meta[property="og:title"]', pageTitle);
    setMeta('meta[property="og:url"]', url);
    setMeta('meta[name="twitter:title"]', pageTitle);
    setMeta('meta[name="twitter:url"]', url);
    setMeta('meta[name="description"]', desc);
    setMeta('meta[property="og:description"]', desc);
    setMeta('meta[name="twitter:description"]', desc);
}

function setupEntryNav(nav, onNavigate) {
    const prevBtn = document.getElementById('prevEntry');
    const nextBtn = document.getElementById('nextEntry');
    const prevBtnFooter = document.getElementById('prevEntryFooter');
    const nextBtnFooter = document.getElementById('nextEntryFooter');

    if (nav.prev) {
        prevBtn.disabled = false;
        prevBtnFooter.disabled = false;
        prevBtn.onclick = () => onNavigate(nav.prev.slug);
        prevBtnFooter.onclick = prevBtn.onclick;
        prevBtnFooter.textContent = '← Back';
    } else {
        prevBtn.disabled = true;
        prevBtnFooter.disabled = true;
        prevBtnFooter.textContent = '← Back';
    }

    if (nav.next) {
        nextBtn.disabled = false;
        nextBtnFooter.disabled = false;
        nextBtn.onclick = () => onNavigate(nav.next.slug);
        nextBtnFooter.onclick = nextBtn.onclick;
        nextBtnFooter.textContent = 'Next →';
    } else {
        nextBtn.disabled = true;
        nextBtnFooter.disabled = true;
        nextBtnFooter.textContent = 'Next →';
    }
}

/* -----------------------------------------------------------------------------
   Menu / Overlay
   ----------------------------------------------------------------------------- */

export function toggleMenu() {
    state.isMenuOpen = !state.isMenuOpen;
    const overlay = document.getElementById('contentsOverlay');
    if (state.isMenuOpen) {
        overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    } else {
        overlay.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

export function closeMenu() {
    state.isMenuOpen = false;
    const overlay = document.getElementById('contentsOverlay');
    if (overlay) overlay.classList.add('hidden');
    document.body.style.overflow = '';
}

export function populateMenu(onNavigate, onLoadPage) {
    const menuLinks = document.getElementById('contentsMenuLinks');
    if (!menuLinks) return;

    const currentBook = state.currentBook;
    const currentEntries = state.currentEntries;
    const currentEntry = state.currentEntry;

    let html = '';

    if (currentBook.introduction) {
        html += '<ul class="menu-list front-matter">';
        html += '<li><a href="#" data-type="introduction" class="is-intro">Introduction</a></li>';
        html += '</ul>';
        html += '<hr class="menu-divider">';
    }

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

    const pages = [
        { type: 'appendix', label: 'Prompt' },
        { type: 'colophon', label: 'Colophon' }
    ];

    html += '<ul class="menu-list secondary-pages">';
    pages.forEach(page => {
        html += `<li><a href="#" data-type="${page.type}">${page.label}</a></li>`;
    });
    html += '</ul>';

    menuLinks.innerHTML = html;

    menuLinks.querySelectorAll('a').forEach(link => {
        link.onclick = (e) => {
            e.preventDefault();
            const slug = link.dataset.slug;
            const type = link.dataset.type;

            if (slug) {
                onNavigate(slug);
            } else if (type) {
                let label = '';
                if (type === 'introduction') {
                    label = 'Introduction';
                } else {
                    const page = pages.find(p => p.type === type);
                    if (page) label = page.label;
                }
                if (label) onLoadPage(type, label);
            }
            closeMenu();
        };
    });
}

export function bindBookControls() {
    const trigger = document.getElementById('contentsTrigger');
    if (trigger) trigger.onclick = toggleMenu;

    const closeBtn = document.getElementById('contentsClose');
    if (closeBtn) closeBtn.onclick = closeMenu;

    const overlay = document.getElementById('contentsOverlay');
    if (overlay) overlay.onclick = (e) => {
        if (e.target === overlay) closeMenu();
    };

    const readBookIcon = document.getElementById('readBookIcon');
    if (readBookIcon) {
        readBookIcon.onclick = (e) => {
            e.preventDefault();
            const currentBook = state.currentBook;
            if (!currentBook) return;

            let href = '';
            const currentEntry = state.currentEntry;
            if (currentEntry) {
                const idx = state.currentEntries.findIndex(e => e.slug === currentEntry.slug);
                if (idx !== -1) {
                    const chapterNum = (idx + 1).toString().padStart(3, '0');
                    href = `&href=chapter-${chapterNum}.xhtml`;
                }
            }
            window.location.href = `/reader.html?bookId=${currentBook.book_id}${href}`;
        };
    }
}

export function updateSchema() {
    const currentBook = state.currentBook;
    if (!currentBook) return;

    const schema = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": currentBook.title,
        "description": currentBook.descriptor,
        "author": { "@type": "Organization", "name": "Alexandria Press" },
        "publisher": { "@type": "Organization", "name": "Alexandria Press" }
    };

    if (currentBook.cover_url) {
        schema.image = new URL(currentBook.cover_url, window.location.origin).href;
    }

    const currentEntry = state.currentEntry;
    if (currentEntry) {
        schema.mainEntity = {
            "@type": "Article",
            "headline": currentEntry.name,
            "description": currentEntry.descriptor,
            "author": { "@type": "Organization", "name": "Alexandria Press" }
        };
    }

    const schemaScript = document.getElementById('schemaData');
    if (schemaScript) {
        schemaScript.textContent = JSON.stringify(schema, null, 2);
    }
}
