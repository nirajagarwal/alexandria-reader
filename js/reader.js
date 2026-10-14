/**
 * Alexandria Press - Interactive Digital Reader Controller
 */

import { EMBEDDED_BOOKS } from './books.js';
import { escapeHtml, parseAlexandriaMarkdown } from './parser.js';
import { paginateChapter } from './layout.js';

// Pretext and Justif Modules
let pretextModule = null;
let justifModule = null;
let hyphenateEnUS = null;
let activeJustifController = null;

try {
    pretextModule = await import('../vendor/pretext/layout.js');
} catch (e) {
    console.info('Pretext module fallback:', e.message);
}

try {
    justifModule = await import('../vendor/justif/index.js');
    const hyp = await import('../vendor/justif/hyphenate/en-us.js');
    hyphenateEnUS = hyp.hyphenateEnUS;
} catch (e) {
    console.info('Justif module fallback:', e.message);
}

// Reader State
let currentBookKey = 'non-linear-engines';
let currentChapterIndex = 0;
let currentSpreadIndex = 0;
let chapterSpreads = [];
let parsedBook = null;

const themes = ['light', 'dark', 'sepia'];
let currentThemeIndex = 0;

export function loadBook(key) {
    currentBookKey = key;
    const bookData = EMBEDDED_BOOKS[key];
    if (!bookData) return;
    parsedBook = parseAlexandriaMarkdown(bookData.markdown);
    currentChapterIndex = 0;
    currentSpreadIndex = 0;
    rebuildAndRenderSpread();
    renderTocList();
    renderLibraryList();
    closeModals();
}

export function rebuildAndRenderSpread() {
    if (!parsedBook || !parsedBook.chapters.length) return;
    const ch = parsedBook.chapters[currentChapterIndex];

    // Paginate chapter into 2-column spreads
    chapterSpreads = paginateChapter(ch, pretextModule);
    if (currentSpreadIndex >= chapterSpreads.length) {
        currentSpreadIndex = Math.max(0, chapterSpreads.length - 1);
    }
    if (currentSpreadIndex < 0) currentSpreadIndex = 0;

    renderActiveSpread();
    updateTelescopeWidgets(ch);
}

export function renderActiveSpread() {
    const ch = parsedBook.chapters[currentChapterIndex];
    const spread = chapterSpreads[currentSpreadIndex] || { colLeftHtml: "", colRightHtml: "" };

    // Update Running Header & Footer
    const headerCenter = document.getElementById('header-center-box');
    if (headerCenter) {
        if (currentSpreadIndex === 0) {
            headerCenter.innerHTML = `<span class="folio-title" style="font-size:12.5px; opacity:0.65;">${escapeHtml(parsedBook.title)}</span>`;
        } else {
            headerCenter.innerHTML = `
                <span class="folio-chap-tag" id="header-chap-label">${escapeHtml(ch.label)}</span>
                <span class="folio-sep">·</span>
                <span class="folio-title" id="header-chap-title">${escapeHtml(ch.title)}</span>
                <span class="folio-sep">—</span>
                <span class="folio-subtitle" id="header-chap-subtitle">${escapeHtml(ch.subtitle)}</span>
            `;
        }
    }

    const footerBook = document.getElementById('footer-book-name');
    if (footerBook) footerBook.innerText = parsedBook.title;

    const footerCounter = document.getElementById('footer-page-counter');
    if (footerCounter) footerCounter.innerText = `Spread ${currentSpreadIndex + 1} of ${chapterSpreads.length}`;

    // Populate columns
    const colLeft = document.getElementById('col-left');
    const colRight = document.getElementById('col-right');

    if (colLeft) colLeft.innerHTML = spread.colLeftHtml || '';
    if (colRight) colRight.innerHTML = spread.colRightHtml || '';

    // Apply Justif TeX justification pass ONLY to intact paragraphs (not split continuation pieces)
    if (justifModule && justifModule.justify) {
        try {
            if (activeJustifController && activeJustifController.unjustify) {
                activeJustifController.unjustify();
            }
            const paras = Array.from(document.querySelectorAll('.spread-col p:not(.para-split-continued):not(.para-split-continuation)'));
            if (paras.length > 0) {
                activeJustifController = justifModule.justify(paras, {
                    hyphenate: hyphenateEnUS || undefined,
                    observeResize: false
                });
            }
        } catch (e) {
            console.warn('Justif enhancement notice:', e);
        }
    }
}

// Advance Page / Turn Spread (Left/Right arrow keys)
export function advancePage(direction) {
    if (direction > 0) {
        // Next spread
        if (currentSpreadIndex < chapterSpreads.length - 1) {
            currentSpreadIndex++;
            renderActiveSpread();
        } else if (currentChapterIndex < parsedBook.chapters.length - 1) {
            // Advance to next chapter
            currentChapterIndex++;
            currentSpreadIndex = 0;
            rebuildAndRenderSpread();
        }
    } else {
        // Previous spread
        if (currentSpreadIndex > 0) {
            currentSpreadIndex--;
            renderActiveSpread();
        } else if (currentChapterIndex > 0) {
            // Retreat to previous chapter (last spread)
            currentChapterIndex--;
            const prevCh = parsedBook.chapters[currentChapterIndex];
            const prevSpreads = paginateChapter(prevCh, pretextModule);
            currentSpreadIndex = Math.max(0, prevSpreads.length - 1);
            rebuildAndRenderSpread();
        }
    }
}

export function nextChapter() {
    if (parsedBook && currentChapterIndex < parsedBook.chapters.length - 1) {
        currentChapterIndex++;
        currentSpreadIndex = 0;
        rebuildAndRenderSpread();
    }
}

export function prevChapter() {
    if (currentChapterIndex > 0) {
        currentChapterIndex--;
        currentSpreadIndex = 0;
        rebuildAndRenderSpread();
    }
}

export function renderTocList() {
    const list = document.getElementById('toc-container');
    if (!list) return;
    list.innerHTML = "";
    const titleEl = document.getElementById('toc-book-title');
    if (titleEl) titleEl.innerText = parsedBook.title;

    parsedBook.chapters.forEach((ch, idx) => {
        const li = document.createElement('li');
        li.className = `toc-item ${idx === currentChapterIndex ? 'active' : ''}`;
        li.onclick = () => {
            currentChapterIndex = idx;
            currentSpreadIndex = 0;
            rebuildAndRenderSpread();
            closeModals();
        };
        li.innerHTML = `
            <div class="t-label">${escapeHtml(ch.label)}</div>
            <div class="t-title">${escapeHtml(ch.title)}</div>
            <div class="t-sub">${escapeHtml(ch.subtitle)}</div>
        `;
        list.appendChild(li);
    });
}

export function renderLibraryList() {
    const container = document.getElementById('library-list');
    if (!container) return;
    container.innerHTML = "";

    Object.keys(EMBEDDED_BOOKS).forEach(k => {
        const b = EMBEDDED_BOOKS[k];
        const div = document.createElement('div');
        div.className = `library-item ${k === currentBookKey ? 'active' : ''}`;
        div.onclick = () => loadBook(k);
        div.innerHTML = `
            <div class="b-cat">${b.category}</div>
            <div class="b-title">${b.title}</div>
            <div class="b-sub">${b.subtitle}</div>
        `;
        container.appendChild(div);
    });
}

export function updateTelescopeWidgets(chapter) {
    const area = document.getElementById('drawer-widget-area');
    if (!area) return;
    let widgetsHtml = "";

    if (chapter.title.includes("Star Graph")) {
        widgetsHtml = `
            <div class="interactive-widget">
                <div class="widget-title">Star Graph Topology Reduction</div>
                <p style="font-size:0.85em; color:var(--text-muted); margin-bottom:10px;">
                    Adjust the number of connected cities (N) to compare quadratic point-to-point routes against linear star routes.
                </p>
                <input type="range" min="5" max="100" value="25" class="widget-slider" id="city-slider" oninput="window.updateFedexMath(this.value)">
                <div class="widget-metric"><span>Cities (N):</span> <strong id="val-n">25</strong></div>
                <div class="widget-metric"><span>Point-to-Point [N(N-1)/2]:</span> <strong id="val-p2p" style="color:#ef4444;">300 routes</strong></div>
                <div class="widget-metric"><span>Star Graph [N]:</span> <strong id="val-star" style="color:#10b981;">25 routes</strong></div>
                <div class="widget-metric"><span>Route Reduction:</span> <strong id="val-pct">91.7%</strong></div>
            </div>
        `;
    } else if (chapter.title.includes("Infinite Shelf")) {
        widgetsHtml = `
            <div class="interactive-widget">
                <div class="widget-title">Negative Cash Conversion Cycle</div>
                <p style="font-size:0.85em; color:var(--text-muted); margin-bottom:10px;">
                    CCC = DSO + DIO - DPO. Negative days create free operational float.
                </p>
                <div class="widget-metric"><span>Days Sales (DSO):</span> <strong>1 day</strong></div>
                <div class="widget-metric"><span>Inventory Transit (DIO):</span> <strong>2 days</strong></div>
                <div class="widget-metric"><span>Days Payable (DPO):</span> <strong>60 days</strong></div>
                <div class="widget-metric"><span>Net Cash Cycle:</span> <strong style="color:#10b981;">-57 days (Free Float)</strong></div>
            </div>
        `;
    } else if (chapter.title.includes("Percolation Threshold")) {
        widgetsHtml = `
            <div class="interactive-widget">
                <div class="widget-title">Spatial Nearest-Neighbor ETA</div>
                <p style="font-size:0.85em; color:var(--text-muted); margin-bottom:10px;">
                    Expected distance E[r] = 1 / (2 * √Density). Non-linear drop as density crosses critical threshold.
                </p>
                <div class="widget-metric"><span>Sub-Critical (D = 0.4):</span> <strong style="color:#ef4444;">ETA ~ 18 min</strong></div>
                <div class="widget-metric"><span>Critical Threshold (D = 2.0):</span> <strong>ETA ~ 6 min</strong></div>
                <div class="widget-metric"><span>Super-Critical (D = 8.0):</span> <strong style="color:#10b981;">ETA ~ 2.8 min</strong></div>
            </div>
        `;
    } else {
        widgetsHtml = `
            <div class="interactive-widget">
                <div class="widget-title">${escapeHtml(chapter.title)}</div>
                <p style="font-size:0.88em; color:var(--text-muted);">${escapeHtml(chapter.subtitle)}</p>
            </div>
        `;
    }

    area.innerHTML = widgetsHtml;
}

export function updateFedexMath(n) {
    n = parseInt(n);
    const p2p = (n * (n - 1)) / 2;
    const star = n;
    const pct = (((p2p - star) / p2p) * 100).toFixed(1);

    const elN = document.getElementById('val-n');
    const elP2p = document.getElementById('val-p2p');
    const elStar = document.getElementById('val-star');
    const elPct = document.getElementById('val-pct');

    if (elN) elN.innerText = n;
    if (elP2p) elP2p.innerText = `${p2p} routes`;
    if (elStar) elStar.innerText = `${star} routes`;
    if (elPct) elPct.innerText = `${pct}%`;
}

export function toggleTelescope() {
    const drawer = document.getElementById('telescope-drawer');
    if (drawer) drawer.classList.toggle('open');
}

export function openTocModal() {
    const modal = document.getElementById('toc-modal');
    if (modal) modal.classList.add('open');
}

export function openLibraryModal() {
    const modal = document.getElementById('library-modal');
    if (modal) modal.classList.add('open');
}

export function openHelpModal() {
    const modal = document.getElementById('help-modal');
    if (modal) modal.classList.add('open');
}

export function closeModals(e) {
    if (!e || e.target.classList.contains('modal-overlay') || e.target.tagName === 'BUTTON') {
        document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
    }
}

export function cycleTheme() {
    currentThemeIndex = (currentThemeIndex + 1) % themes.length;
    const t = themes[currentThemeIndex];
    document.documentElement.setAttribute('data-theme', t);
}

export function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(evt) {
        const content = evt.target.result;
        const bookKey = 'custom-' + Date.now();
        EMBEDDED_BOOKS[bookKey] = {
            title: file.name.replace(/\.[^/.]+$/, ""),
            subtitle: "Custom Uploaded Markdown",
            category: "Local",
            markdown: content
        };
        loadBook(bookKey);
    };
    reader.readAsText(file);
}

// Bind Global Window Handlers for inline HTML onclick attributes
if (typeof window !== 'undefined') {
    window.advancePage = advancePage;
    window.nextChapter = nextChapter;
    window.prevChapter = prevChapter;
    window.loadBook = loadBook;
    window.openTocModal = openTocModal;
    window.openLibraryModal = openLibraryModal;
    window.openHelpModal = openHelpModal;
    window.closeModals = closeModals;
    window.toggleTelescope = toggleTelescope;
    window.cycleTheme = cycleTheme;
    window.updateFedexMath = updateFedexMath;
    window.handleFileUpload = handleFileUpload;

    // Window Resize Event
    window.addEventListener('resize', () => {
        rebuildAndRenderSpread();
    });

    // Keyboard Navigation Handlers
    window.addEventListener('keydown', (e) => {
        if (e.target && e.target.tagName === 'INPUT') return;

        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
            const drawer = document.getElementById('telescope-drawer');
            if (drawer) drawer.classList.remove('open');
        } else if (e.key === 'ArrowRight' || (e.key === ' ' && !e.shiftKey)) {
            e.preventDefault();
            advancePage(1);
        } else if (e.key === 'ArrowLeft' || (e.key === ' ' && e.shiftKey)) {
            e.preventDefault();
            advancePage(-1);
        } else if (e.key === 'n') {
            nextChapter();
        } else if (e.key === 'p') {
            prevChapter();
        } else if (e.key === 't') {
            openTocModal();
        } else if (e.key === 'l') {
            openLibraryModal();
        } else if (e.key === 'e') {
            toggleTelescope();
        } else if (e.key === 'd') {
            cycleTheme();
        } else if (e.key === '?') {
            openHelpModal();
        }
    });

    // Initialize once Web Fonts and DOM are ready
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(() => {
            rebuildAndRenderSpread();
        });
    }

    // Initial load
    loadBook('non-linear-engines');
}
