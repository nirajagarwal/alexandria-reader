/**
 * Alexandria Press — Digital Reader & Catalog Application
 * Renders Typst-compiled PDF editions (Desktop, Compact, Mobile), manages
 * provenance ledgers, deep-link routing, and catalog filtering.
 */
(function () {
    'use strict';

    const EMBEDDED_BOOKS = window.EMBEDDED_BOOKS || {};

    let currentBookKey = 'non-linear-engines';
    let currentChapterIndex = 0;
    let activeBook = null;

    const themes = ['light', 'dark', 'sepia'];
    let currentThemeIndex = 0;

    const STORAGE_THEME_KEY = 'alexandria_theme';
    const STORAGE_PROGRESS_KEY = 'alexandria_reading_progress';

    // Restore saved theme immediately on load
    try {
        const savedTheme = localStorage.getItem(STORAGE_THEME_KEY);
        if (savedTheme && themes.includes(savedTheme)) {
            currentThemeIndex = themes.indexOf(savedTheme);
            document.documentElement.setAttribute('data-theme', savedTheme);
        }
    } catch (e) {}

    if (window.pdfjsLib) {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'vendor/pdfjs/pdf.worker.min.js';
    }

    const PDF_BUILD_VERSION = '20261017c';
    const COVER_PAGE = 1;       // Physical Page 1 is the Full-Bleed Book Cover
    const TOC_PAGE = 2;         // Physical Page 2 is the Title & Contents Frontispiece
    const READER_FIRST_PAGE = 2; // Default opening spread starts at Page 2 (Contents + Intro)
    const EDITION_SPECS = {
        desktop: { widthIn: 5.8, heightIn: 7.5, aspect: 5.8 / 7.5, fontPt: 11.6 },
        compact: { widthIn: 5.5, heightIn: 6.8, aspect: 5.5 / 6.8, fontPt: 12.2 },
        mobile:  { widthIn: 4.2, heightIn: 7.5, aspect: 4.2 / 7.5, fontPt: 11.8 }
    };

    let activePdfDoc = null;
    let activePdfEdition = 'desktop'; // 'desktop' | 'compact' | 'mobile'
    const pdfDocCache = {};
    let pdfPageNum = READER_FIRST_PAGE;
    let activeRenderTasks = { left: null, right: null };
    let renderToken = 0;

    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function getSavedBookPage(bookKey) {
        try {
            const raw = localStorage.getItem(STORAGE_PROGRESS_KEY);
            if (!raw) return null;
            const map = JSON.parse(raw);
            const entry = map && map[bookKey];
            if (entry && typeof entry.page === 'number' && entry.page >= COVER_PAGE) {
                return entry.page;
            }
        } catch (e) {}
        return null;
    }

    function saveBookPageProgress(bookKey, pageNum) {
        if (!bookKey || typeof pageNum !== 'number') return;
        try {
            const raw = localStorage.getItem(STORAGE_PROGRESS_KEY);
            const map = raw ? JSON.parse(raw) : {};
            map[bookKey] = {
                page: pageNum,
                chapter: currentChapterIndex,
                updatedAt: Date.now()
            };
            localStorage.setItem(STORAGE_PROGRESS_KEY, JSON.stringify(map));
        } catch (e) {}
    }

    function setMetaAttr(id, attr, val) {
        const el = document.getElementById(id);
        if (el) el.setAttribute(attr, val);
    }

    function updatePageMetaForCatalog() {
        const title = 'Alexandria Press — Deep Learning for Humans. Distilled by Frontier AI.';
        const cardTitle = 'Alexandria Press';
        const desc = 'Deep Learning for Humans. Distilled by Frontier AI.';
        const url = 'https://alexandria.press/';
        const img = 'https://alexandria.press/og-image.png';
        document.title = title;
        setMetaAttr('meta-canonical', 'href', url);
        setMetaAttr('meta-og-type', 'content', 'website');
        setMetaAttr('meta-og-url', 'content', url);
        setMetaAttr('meta-og-title', 'content', cardTitle);
        setMetaAttr('meta-og-desc', 'content', desc);
        setMetaAttr('meta-og-image', 'content', img);
        setMetaAttr('meta-og-image-alt', 'content', title);
        setMetaAttr('meta-tw-title', 'content', cardTitle);
        setMetaAttr('meta-tw-desc', 'content', desc);
        setMetaAttr('meta-tw-image', 'content', img);
        setMetaAttr('meta-tw-image-alt', 'content', title);
    }

    function updatePageMetaForBook(bookKey) {
        const b = EMBEDDED_BOOKS[bookKey];
        if (!b) return;
        const title = `${b.title} — ${b.subtitle} | Alexandria Press`;
        const cardTitle = `${b.title} — ${b.subtitle}`;
        const desc = `${b.subtitle} — Twelve-chapter illustrated monograph published by Alexandria Press.`;
        const url = `https://alexandria.press/read/${bookKey}/`;
        const img = `https://alexandria.press/assets/og/${bookKey}.png`;
        document.title = title;
        setMetaAttr('meta-canonical', 'href', url);
        setMetaAttr('meta-og-type', 'content', 'book');
        setMetaAttr('meta-og-url', 'content', url);
        setMetaAttr('meta-og-title', 'content', cardTitle);
        setMetaAttr('meta-og-desc', 'content', desc);
        setMetaAttr('meta-og-image', 'content', img);
        setMetaAttr('meta-og-image-alt', 'content', cardTitle);
        setMetaAttr('meta-tw-title', 'content', cardTitle);
        setMetaAttr('meta-tw-desc', 'content', desc);
        setMetaAttr('meta-tw-image', 'content', img);
        setMetaAttr('meta-tw-image-alt', 'content', cardTitle);
    }

    function syncReaderUrlHash() {
        const homeView = document.getElementById('home-view');
        if (homeView && homeView.classList.contains('active')) return;
        if (!currentBookKey) return;
        updatePageMetaForBook(currentBookKey);
        const pageSuffix = (pdfPageNum !== READER_FIRST_PAGE) ? `&page=${pdfPageNum}` : '';
        const desiredHash = `#read=${currentBookKey}${pageSuffix}`;
        if (window.location.hash !== desiredHash) {
            try {
                window.history.replaceState(null, '', desiredHash);
            } catch (e) {}
        }
    }

    function getStageViewport() {
        const stageEl = document.getElementById('spread-container') || document.getElementById('main-stage');
        const stageW = (stageEl && stageEl.clientWidth > 100) ? stageEl.clientWidth : Infinity;
        const stageH = (stageEl && stageEl.clientHeight > 100) ? stageEl.clientHeight : Infinity;
        const vvW = (window.visualViewport && window.visualViewport.width > 100) ? window.visualViewport.width : Infinity;
        const vvH = (window.visualViewport && window.visualViewport.height > 100) ? window.visualViewport.height : Infinity;
        const winW = window.innerWidth || document.documentElement.clientWidth || 360;
        const winH = window.innerHeight || document.documentElement.clientHeight || 640;
        const vpW = Math.min(winW, vvW, stageW);
        const vpH = Math.min(winH, vvH, stageH);
        const isMob = vpW < 600;
        return {
            availW: Math.max(200, Math.floor(vpW - (isMob ? 10 : 12))),
            availH: Math.max(200, Math.floor(vpH - (isMob ? 16 : 12)))
        };
    }

    function computeResponsiveLayout() {
        const { availW, availH } = getStageViewport();
        const windowAspect = availW / availH;

        if (availW >= 800 && windowAspect >= 1.05) {
            const ed = (windowAspect >= 1.48 && availH >= 700) ? 'desktop' : 'compact';
            const aspect = EDITION_SPECS[ed].aspect;
            const pageH = Math.floor(Math.min(availH, availW / (2 * aspect)));
            const pageW = Math.floor(pageH * aspect);
            return { edition: ed, twoPage: true, pageW, pageH };
        }

        if (availW >= 540) {
            const ed = (availH >= 720) ? 'desktop' : 'compact';
            const aspect = EDITION_SPECS[ed].aspect;
            const pageH = Math.floor(Math.min(availH, availW / aspect));
            const pageW = Math.floor(pageH * aspect);
            return { edition: ed, twoPage: false, pageW, pageH };
        }

        const pageH = Math.floor(Math.min(availH, availW / EDITION_SPECS.mobile.aspect));
        const pageW = Math.floor(pageH * EDITION_SPECS.mobile.aspect);
        return { edition: 'mobile', twoPage: false, pageW, pageH };
    }

    function isTwoPageEffective() {
        return computeResponsiveLayout().twoPage;
    }

    function getSectionPages(forEdition) {
        const bookData = EMBEDDED_BOOKS[currentBookKey];
        const ed = forEdition || activePdfEdition || computeResponsiveLayout().edition;
        if (bookData) {
            if (ed === 'mobile' && Array.isArray(bookData.mobileSectionPages) && bookData.mobileSectionPages.length) {
                return bookData.mobileSectionPages;
            }
            if (ed === 'compact' && Array.isArray(bookData.compactSectionPages) && bookData.compactSectionPages.length) {
                return bookData.compactSectionPages;
            }
            if (Array.isArray(bookData.sectionPages) && bookData.sectionPages.length) {
                return bookData.sectionPages;
            }
        }
        return [3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26];
    }

    function syncChapterFromPdfPage() {
        if (!activeBook || !activeBook.chapters || !activeBook.chapters.length) return;
        if (pdfPageNum <= COVER_PAGE) {
            currentChapterIndex = 0;
            return;
        }
        const sectionPages = getSectionPages(activePdfEdition);
        const twoPage = isTwoPageEffective();
        const leftP = twoPage
            ? (Math.floor((Math.max(TOC_PAGE, pdfPageNum) - TOC_PAGE) / 2) * 2 + TOC_PAGE)
            : pdfPageNum;
        const maxVisiblePage = twoPage ? (leftP + 1) : leftP;

        let chapIdx = 0;
        for (let i = 0; i < sectionPages.length; i++) {
            if (sectionPages[i] <= maxVisiblePage) {
                chapIdx = i;
            }
        }
        currentChapterIndex = Math.min(chapIdx, activeBook.chapters.length - 1);
    }

    async function ensurePdfEditionLoaded(key, edition) {
        const bookData = EMBEDDED_BOOKS[key];
        if (!bookData || !window.pdfjsLib) return null;
        let pdfUrl = bookData.pdf;
        if (edition === 'mobile' && bookData.mobilePdf) {
            pdfUrl = bookData.mobilePdf;
        } else if (edition === 'compact' && bookData.compactPdf) {
            pdfUrl = bookData.compactPdf;
        }
        if (!pdfUrl) return null;

        const versionedUrl = `${pdfUrl}?v=${PDF_BUILD_VERSION}`;
        const cacheKey = `${key}:${edition}:${PDF_BUILD_VERSION}`;
        if (!pdfDocCache[cacheKey]) {
            pdfDocCache[cacheKey] = await window.pdfjsLib.getDocument(versionedUrl).promise;
        }
        return pdfDocCache[cacheKey];
    }

    async function loadBook(key, initialPage = null, initialChapter = null) {
        currentBookKey = key;
        const bookData = EMBEDDED_BOOKS[key];
        if (!bookData) return;
        activeBook = {
            title: bookData.title,
            subtitle: bookData.subtitle,
            category: bookData.category,
            mode: bookData.mode || 'facet',
            format: bookData.format || 'mechanisms',
            chapters: Array.isArray(bookData.chapters) ? bookData.chapters : []
        };
        const dlBtn = document.getElementById('download-pdf-btn');
        if (dlBtn && bookData.pdf) {
            dlBtn.href = bookData.pdf;
            dlBtn.setAttribute('download', `${key}.pdf`);
        }
        currentChapterIndex = 0;
        activePdfEdition = computeResponsiveLayout().edition;

        if (typeof initialChapter === 'number' && initialChapter >= 0) {
            const secPages = getSectionPages(activePdfEdition);
            pdfPageNum = secPages[initialChapter] || READER_FIRST_PAGE;
        } else if (typeof initialPage === 'number' && initialPage >= COVER_PAGE) {
            pdfPageNum = initialPage;
        } else {
            pdfPageNum = READER_FIRST_PAGE;
        }

        if (bookData.pdf && window.pdfjsLib) {
            try {
                activePdfDoc = await ensurePdfEditionLoaded(key, activePdfEdition);
            } catch (err) {
                console.error('Failed to load Typst PDF:', err);
                activePdfDoc = null;
            }
        } else {
            activePdfDoc = null;
        }

        rebuildAndRenderSpread();
        renderTocList();
        renderSourcesList();
        closeModals();
    }

    async function rebuildAndRenderSpread() {
        if (!activeBook) return;

        const layout = computeResponsiveLayout();
        const desiredEdition = layout.edition;
        const bookData = EMBEDDED_BOOKS[currentBookKey];
        if (bookData && bookData.pdf && window.pdfjsLib && desiredEdition !== activePdfEdition) {
            const wasCoverPage = (pdfPageNum === COVER_PAGE);
            const wasTocPage = (pdfPageNum === TOC_PAGE);
            const oldSecPages = getSectionPages(activePdfEdition);
            const savedChap = currentChapterIndex;
            const oldChapStart = oldSecPages[savedChap] || 3;
            const pageOffset = Math.max(0, pdfPageNum - oldChapStart);

            activePdfEdition = desiredEdition;
            try {
                activePdfDoc = await ensurePdfEditionLoaded(currentBookKey, activePdfEdition);
                if (wasCoverPage) {
                    pdfPageNum = COVER_PAGE;
                } else if (wasTocPage) {
                    pdfPageNum = TOC_PAGE;
                } else {
                    const newSecPages = getSectionPages(activePdfEdition);
                    const newStart = newSecPages[savedChap] || 3;
                    const nextStart = newSecPages[savedChap + 1] || (activePdfDoc.numPages + 1);
                    pdfPageNum = Math.min(nextStart - 1, newStart + pageOffset);
                }
            } catch (e) {
                console.warn('Failed to switch PDF edition:', e);
            }
        }

        if (activePdfDoc) {
            syncChapterFromPdfPage();
            renderPdfSpread(layout);
        }
    }

    async function renderSinglePdfPage(pageNumber, canvasEl, linksEl, slotEl, maxPageW, maxPageH, slotKey, myToken) {
        if (!activePdfDoc || !canvasEl || !slotEl) return;
        if (linksEl) linksEl.innerHTML = '';

        if (activeRenderTasks[slotKey]) {
            try { activeRenderTasks[slotKey].cancel(); } catch (e) {}
            activeRenderTasks[slotKey] = null;
        }

        try {
            const page = await activePdfDoc.getPage(pageNumber);
            if (myToken !== renderToken) return;

            const unscaledVp = page.getViewport({ scale: 1 });
            const dpr = Math.min(window.devicePixelRatio || 1, 3);
            const cssScale = Math.min(maxPageW / unscaledVp.width, maxPageH / unscaledVp.height);
            const exactCssW = Math.round(unscaledVp.width * cssScale);
            const exactCssH = Math.round(unscaledVp.height * cssScale);
            const alignedScale = exactCssW / unscaledVp.width;
            const hiDpiViewport = page.getViewport({ scale: alignedScale * dpr });

            // Render to an offscreen canvas first to eliminate any page-turn flicker
            const offCanvas = document.createElement('canvas');
            offCanvas.width = Math.round(hiDpiViewport.width);
            offCanvas.height = Math.round(hiDpiViewport.height);
            const offCtx = offCanvas.getContext('2d');

            const task = page.render({ canvasContext: offCtx, viewport: hiDpiViewport });
            activeRenderTasks[slotKey] = task;
            await task.promise;
            if (myToken !== renderToken) return;

            canvasEl.width = offCanvas.width;
            canvasEl.height = offCanvas.height;
            const cssWStr = (canvasEl.width / dpr) + 'px';
            const cssHStr = (canvasEl.height / dpr) + 'px';
            canvasEl.style.width = cssWStr;
            canvasEl.style.height = cssHStr;
            slotEl.style.width = cssWStr;
            slotEl.style.height = cssHStr;

            const ctx = canvasEl.getContext('2d');
            ctx.drawImage(offCanvas, 0, 0);

            const bookFrame = document.getElementById('pdf-book-frame');
            if (bookFrame) {
                bookFrame.style.setProperty('--pt', alignedScale.toFixed(4) + 'px');
                bookFrame.setAttribute('data-edition', activePdfEdition);
            }

            // Render interactive TOC link hotspots on the TOC Frontispiece page (Page 2)
            if (linksEl && pageNumber === TOC_PAGE) {
                const annots = await page.getAnnotations();
                if (myToken !== renderToken) return;
                const linkAnnots = annots
                    .filter(a => a.subtype === 'Link' && Array.isArray(a.rect))
                    .sort((a, b) => b.rect[1] - a.rect[1]);
                const cssVp = page.getViewport({ scale: alignedScale });
                const sectionPages = getSectionPages(activePdfEdition);

                const padX = 7.5 * alignedScale;
                const padY = 2.8 * alignedScale;

                linkAnnots.forEach((annot, idx) => {
                    const rect = cssVp.convertToViewportRectangle(annot.rect);
                    const left = Math.min(rect[0], rect[2]) - padX;
                    const top = Math.min(rect[1], rect[3]) - padY;
                    const width = Math.abs(rect[2] - rect[0]) + padX * 2;
                    const height = Math.abs(rect[3] - rect[1]) + padY * 2;

                    const targetPage = sectionPages[idx] || (idx === 0 ? 3 : (idx * 2 + 2));
                    const chObj = activeBook.chapters[idx];
                    const a = document.createElement('a');
                    a.className = 'pdf-link-hotspot';
                    a.href = '#';
                    a.title = chObj ? `${chObj.label}: ${chObj.title}` : `Jump to Section ${idx}`;
                    a.style.left = `${left.toFixed(1)}px`;
                    a.style.top = `${top.toFixed(1)}px`;
                    a.style.width = `${width.toFixed(1)}px`;
                    a.style.height = `${height.toFixed(1)}px`;
                    a.onclick = (ev) => {
                        ev.preventDefault();
                        pdfPageNum = targetPage;
                        rebuildAndRenderSpread();
                    };
                    linksEl.appendChild(a);
                });
            }
        } catch (err) {
            if (err && err.name !== 'RenderingCancelledException') {
                console.warn('PDF page render notice:', err);
            }
        }
    }

    function prewarmAdjacentPages(leftPage, rightPage, totalPages) {
        if (!activePdfDoc) return;
        const maxDisplayed = rightPage || leftPage;
        const toWarm = [];
        if (maxDisplayed + 1 <= totalPages) toWarm.push(maxDisplayed + 1);
        if (maxDisplayed + 2 <= totalPages) toWarm.push(maxDisplayed + 2);
        toWarm.forEach(p => {
            activePdfDoc.getPage(p).catch(() => {});
        });
    }

    function renderPdfSpread(layoutOverride) {
        if (!activePdfDoc) return;
        const myToken = ++renderToken;

        const layout = layoutOverride || computeResponsiveLayout();
        const twoPage = layout.twoPage;
        const pageW = Math.max(142, layout.pageW);
        const pageH = Math.max(220, layout.pageH);

        const bookFrame = document.getElementById('pdf-book-frame');
        const slotLeft = document.getElementById('pdf-slot-left');
        const slotRight = document.getElementById('pdf-slot-right');
        const canvasLeft = document.getElementById('pdf-canvas-left');
        const canvasRight = document.getElementById('pdf-canvas-right');
        const linksLeft = document.getElementById('pdf-links-left');
        const linksRight = document.getElementById('pdf-links-right');

        const totalPages = activePdfDoc.numPages;

        let leftPage = pdfPageNum;
        let rightPage = null;

        if (pdfPageNum <= COVER_PAGE) {
            // Physical Page 1 is the Full-Bleed Book Cover (always displayed as a centered single page)
            leftPage = COVER_PAGE;
            rightPage = null;
            pdfPageNum = COVER_PAGE;
        } else if (twoPage) {
            const spreadIdx = Math.floor((Math.max(TOC_PAGE, Math.min(totalPages, pdfPageNum)) - TOC_PAGE) / 2);
            leftPage = spreadIdx * 2 + TOC_PAGE;
            rightPage = (leftPage + 1 <= totalPages) ? (leftPage + 1) : null;
            pdfPageNum = leftPage;
        } else {
            leftPage = Math.max(COVER_PAGE, Math.min(totalPages, pdfPageNum));
            rightPage = null;
            pdfPageNum = leftPage;
        }

        syncChapterFromPdfPage();
        saveBookPageProgress(currentBookKey, pdfPageNum);
        syncReaderUrlHash();

        const prevBtn = document.getElementById('prev-spread-btn');
        const nextBtn = document.getElementById('next-spread-btn');
        const edgePrev = document.getElementById('edge-zone-prev');
        const edgeNext = document.getElementById('edge-zone-next');

        const atCover = (leftPage <= COVER_PAGE);
        const atEnd = (twoPage && leftPage >= TOC_PAGE)
            ? ((rightPage || leftPage) >= totalPages)
            : (leftPage >= totalPages);

        if (prevBtn) {
            prevBtn.classList.remove('is-disabled');
            prevBtn.title = atCover
                ? 'Return to Home Catalog (←)'
                : ((leftPage === TOC_PAGE) ? 'View Book Cover (←)' : 'Previous Page (←)');
        }
        if (edgePrev) {
            edgePrev.classList.remove('is-disabled');
        }
        if (nextBtn) {
            nextBtn.classList.remove('is-disabled');
            nextBtn.title = atEnd ? 'Return to Home Catalog (→)' : 'Next Page (→)';
        }
        if (edgeNext) {
            edgeNext.classList.remove('is-disabled');
        }

        const showBoth = twoPage && rightPage !== null && leftPage >= TOC_PAGE;

        if (bookFrame) {
            bookFrame.className = showBoth ? 'pdf-book-frame two-page' : 'pdf-book-frame single-page';
            bookFrame.classList.toggle('is-page-one', leftPage <= TOC_PAGE && !showBoth);
        }

        if (slotLeft) slotLeft.style.display = 'block';
        renderSinglePdfPage(leftPage, canvasLeft, linksLeft, slotLeft, pageW, pageH, 'left', myToken);

        if (showBoth && slotRight) {
            slotRight.style.display = 'block';
            renderSinglePdfPage(rightPage, canvasRight, linksRight, slotRight, pageW, pageH, 'right', myToken);
        } else if (slotRight) {
            slotRight.style.display = 'none';
        }

        prewarmAdjacentPages(leftPage, rightPage, totalPages);
        renderTocList();
        renderSourcesList();
    }

    function advancePage(direction) {
        if (!activePdfDoc) return;
        const twoPage = isTwoPageEffective();
        const total = activePdfDoc.numPages;

        if (direction < 0) {
            if (pdfPageNum <= COVER_PAGE) {
                saveBookPageProgress(currentBookKey, READER_FIRST_PAGE);
                showHomeView();
                return;
            }
            if (pdfPageNum <= TOC_PAGE) {
                pdfPageNum = COVER_PAGE;
            } else {
                const step = twoPage ? 2 : 1;
                pdfPageNum = Math.max(TOC_PAGE, pdfPageNum - step);
            }
            rebuildAndRenderSpread();
        } else if (direction > 0) {
            if (pdfPageNum === COVER_PAGE) {
                pdfPageNum = TOC_PAGE;
                rebuildAndRenderSpread();
                return;
            }
            const step = twoPage ? 2 : 1;
            const nextP = pdfPageNum + step;
            if (nextP <= total) {
                pdfPageNum = nextP;
                rebuildAndRenderSpread();
            } else {
                saveBookPageProgress(currentBookKey, READER_FIRST_PAGE);
                showHomeView();
            }
        }
    }

    function jumpToChapterIndex(idx) {
        if (!activeBook || idx < 0 || idx >= activeBook.chapters.length) return;
        currentChapterIndex = idx;
        const sectionPages = getSectionPages(activePdfEdition);
        pdfPageNum = sectionPages[idx] || (idx === 0 ? 3 : (idx * 2 + 2));
        rebuildAndRenderSpread();
    }

    function nextChapter() {
        if (!activeBook) return;
        if (currentChapterIndex < activeBook.chapters.length - 1) {
            jumpToChapterIndex(currentChapterIndex + 1);
        } else {
            saveBookPageProgress(currentBookKey, READER_FIRST_PAGE);
            showHomeView();
        }
    }

    function prevChapter() {
        if (currentChapterIndex > 0) {
            jumpToChapterIndex(currentChapterIndex - 1);
        } else if (pdfPageNum > TOC_PAGE) {
            pdfPageNum = TOC_PAGE;
            rebuildAndRenderSpread();
        } else if (pdfPageNum === TOC_PAGE) {
            pdfPageNum = COVER_PAGE;
            rebuildAndRenderSpread();
        } else {
            saveBookPageProgress(currentBookKey, READER_FIRST_PAGE);
            showHomeView();
        }
    }

    function renderTocList() {
        const list = document.getElementById('toc-container');
        if (!list || !activeBook) return;
        list.innerHTML = '';
        const titleEl = document.getElementById('toc-book-title');
        if (titleEl) titleEl.innerText = activeBook.title;

        activeBook.chapters.forEach((ch, idx) => {
            const li = document.createElement('li');
            li.className = `toc-item ${idx === currentChapterIndex ? 'active' : ''}`;
            li.onclick = () => {
                jumpToChapterIndex(idx);
                closeModals();
            };
            li.innerHTML = `
                <div class="toc-item-main">
                    <div class="t-label">${escapeHtml(ch.label)}</div>
                    <div class="t-title">${escapeHtml(ch.title)}</div>
                    <div class="t-sub">${escapeHtml(ch.subtitle)}</div>
                </div>
            `;
            list.appendChild(li);
        });
    }

    function formatFormalismBadge(mode) {
        if (mode === 'equation') return 'Governing Equation';
        if (mode === 'diagram') return 'Schematic Diagram';
        if (mode === 'highlights') return '12 Prospected Highlights';
        if (mode === 'introduction') return 'Volume Thesis';
        return 'Empirical Ledger';
    }

    function renderSourcesList() {
        const container = document.getElementById('sources-container');
        if (!container || !activeBook) return;
        container.innerHTML = '';
        const titleEl = document.getElementById('sources-book-title');
        if (titleEl) titleEl.innerText = `${activeBook.title} — Provenance`;

        activeBook.chapters.forEach((ch, idx) => {
            if (idx === 0) return; // Start directly with Chapter 1
            const div = document.createElement('div');
            div.className = `source-item ${idx === currentChapterIndex ? 'active' : ''}`;
            div.onclick = () => {
                jumpToChapterIndex(idx);
                closeModals();
            };
            const fBadge = formatFormalismBadge(ch.formalismMode);
            const anchorHtml = ch.anchor
                ? `<div class="source-item-field"><strong>Primary Anchor:</strong>${escapeHtml(ch.anchor)}</div>`
                : '';
            const exitHtml = ch.exitFact
                ? `<div class="source-item-field"><strong>Verified Finding:</strong>${escapeHtml(ch.exitFact)}</div>`
                : '';

            div.innerHTML = `
                <div class="source-item-meta">${escapeHtml(ch.label)} &middot; ${escapeHtml(fBadge)}</div>
                <div class="source-item-title">${escapeHtml(ch.title)}</div>
                <div class="source-item-sub">${escapeHtml(ch.subtitle)}</div>
                ${anchorHtml}
                ${exitHtml}
            `;
            container.appendChild(div);
        });
    }

    function openTocModal() {
        const modal = document.getElementById('toc-modal');
        if (modal) modal.classList.add('open');
    }

    function openSourcesModal() {
        renderSourcesList();
        const modal = document.getElementById('sources-modal');
        if (modal) {
            modal.classList.add('open');
            const container = document.getElementById('sources-container');
            if (container) container.scrollTop = 0;
        }
    }

    function openHelpModal() {
        const modal = document.getElementById('help-modal');
        if (modal) modal.classList.add('open');
    }

    function closeModals(e) {
        if (!e || e.target.classList.contains('modal-overlay') || (e.target.closest && e.target.closest('.btn-icon'))) {
            document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
        }
    }

    function cycleTheme() {
        currentThemeIndex = (currentThemeIndex + 1) % themes.length;
        const t = themes[currentThemeIndex];
        document.documentElement.setAttribute('data-theme', t);
        try {
            localStorage.setItem(STORAGE_THEME_KEY, t);
        } catch (e) {}
    }

    // Catalog Home View Logic
    let activeFormatFilter = 'all';
    let searchQuery = '';
    let selectedCatalogIndex = 0;

    function getVisibleBookCards() {
        const grid = document.getElementById('catalog-grid');
        if (!grid) return [];
        return Array.from(grid.querySelectorAll('.book-card')).filter(c => c.style.display !== 'none');
    }

    function setSelectedCatalogCard(idx, scrollIntoView = true) {
        const visible = getVisibleBookCards();
        const grid = document.getElementById('catalog-grid');
        if (grid) {
            grid.querySelectorAll('.book-card.is-selected').forEach(c => c.classList.remove('is-selected'));
        }
        if (!visible.length) {
            selectedCatalogIndex = -1;
            return;
        }
        selectedCatalogIndex = Math.max(0, Math.min(visible.length - 1, idx));
        const card = visible[selectedCatalogIndex];
        if (card) {
            card.classList.add('is-selected');
            if (scrollIntoView) {
                card.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            }
        }
    }

    function navigateCatalogGrid(key) {
        const visible = getVisibleBookCards();
        if (!visible.length) return;
        if (selectedCatalogIndex < 0 || selectedCatalogIndex >= visible.length) {
            setSelectedCatalogCard(0);
            return;
        }
        const firstTop = visible[0].getBoundingClientRect().top;
        const cols = Math.max(1, visible.filter(c => Math.abs(c.getBoundingClientRect().top - firstTop) < 12).length);
        let nextIdx = selectedCatalogIndex;
        if (key === 'ArrowRight') {
            nextIdx = Math.min(visible.length - 1, selectedCatalogIndex + 1);
        } else if (key === 'ArrowLeft') {
            nextIdx = Math.max(0, selectedCatalogIndex - 1);
        } else if (key === 'ArrowDown') {
            nextIdx = Math.min(visible.length - 1, selectedCatalogIndex + cols);
        } else if (key === 'ArrowUp') {
            nextIdx = Math.max(0, selectedCatalogIndex - cols);
        }
        setSelectedCatalogCard(nextIdx, true);
    }

    function showHomeView() {
        const homeView = document.getElementById('home-view');
        if (homeView) {
            homeView.classList.add('active');
            updatePageMetaForCatalog();
            renderCatalogGrid();
            const visible = getVisibleBookCards();
            const matchIdx = visible.findIndex(c => c.getAttribute('data-key') === currentBookKey);
            setSelectedCatalogCard(matchIdx >= 0 ? matchIdx : Math.max(0, selectedCatalogIndex), false);
            if (window.location.hash !== '#catalog') {
                window.location.hash = 'catalog';
            }
        }
    }

    function hideHomeView() {
        const homeView = document.getElementById('home-view');
        if (homeView) {
            homeView.classList.remove('active');
        }
    }

    function openBookFromCatalog(bookKey) {
        const visible = getVisibleBookCards();
        const matchIdx = visible.findIndex(c => c.getAttribute('data-key') === bookKey);
        if (matchIdx >= 0) selectedCatalogIndex = matchIdx;
        hideHomeView();
        const savedPage = getSavedBookPage(bookKey);
        const startPage = (savedPage && savedPage >= COVER_PAGE) ? savedPage : READER_FIRST_PAGE;
        loadBook(bookKey, startPage);
        window.location.hash = 'read=' + bookKey + (startPage !== READER_FIRST_PAGE ? '&page=' + startPage : '');
    }

    function filterCatalog(format, btnElement) {
        activeFormatFilter = format || 'all';
        document.querySelectorAll('#catalog-filters .filter-pill').forEach(p => p.classList.remove('active'));
        if (btnElement) btnElement.classList.add('active');
        renderCatalogGrid();
    }

    function handleCatalogSearch(query) {
        searchQuery = (query || '').toLowerCase().trim();
        renderCatalogGrid();
    }

    function renderCatalogGrid() {
        const grid = document.getElementById('catalog-grid');
        if (!grid) return;

        const cards = grid.querySelectorAll('.book-card');
        let visibleCount = 0;

        cards.forEach(card => {
            const key = card.getAttribute('data-key');
            const b = (typeof EMBEDDED_BOOKS !== 'undefined' && EMBEDDED_BOOKS[key]) ? EMBEDDED_BOOKS[key] : null;
            const cardFormat = card.getAttribute('data-format') || (b && b.format) || 'mechanisms';

            const matchFormat = (activeFormatFilter === 'all') || (cardFormat === activeFormatFilter) || (card.getAttribute('data-category') === activeFormatFilter);
            let matchSearch = true;

            if (searchQuery) {
                const title = (card.getAttribute('data-title') || '').toLowerCase();
                const subtitle = (card.getAttribute('data-subtitle') || '').toLowerCase();
                const cat = (card.getAttribute('data-category') || '').toLowerCase();
                const chapText = (b && Array.isArray(b.chapters))
                    ? b.chapters.map(c => `${c.title} ${c.subtitle} ${c.anchor || ''} ${c.exitFact || ''}`).join(' ').toLowerCase()
                    : '';
                matchSearch = title.includes(searchQuery) || subtitle.includes(searchQuery) || cat.includes(searchQuery) || chapText.includes(searchQuery);
            }

            if (matchFormat && matchSearch) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        if (visibleCount > 0) {
            setSelectedCatalogCard(Math.max(0, Math.min(visibleCount - 1, selectedCatalogIndex)), false);
        } else {
            setSelectedCatalogCard(-1, false);
        }

        let emptyNotice = document.getElementById('catalog-empty-notice');
        if (visibleCount === 0) {
            if (!emptyNotice) {
                emptyNotice = document.createElement('div');
                emptyNotice.id = 'catalog-empty-notice';
                emptyNotice.style.cssText = 'grid-column: 1 / -1; padding: 48px; text-align: center; color: var(--text-muted); font-family: var(--font-serif); font-size: 1.1rem;';
                grid.appendChild(emptyNotice);
            }
            emptyNotice.textContent = `No volumes found matching "${searchQuery}".`;
            emptyNotice.style.display = '';
        } else if (emptyNotice) {
            emptyNotice.style.display = 'none';
        }
    }

    function resolveChapterIndexParam(bookKey, chParam) {
        if (!chParam || !EMBEDDED_BOOKS[bookKey]) return null;
        const chs = EMBEDDED_BOOKS[bookKey].chapters || [];
        const asNum = parseInt(chParam, 10);
        if (!isNaN(asNum) && asNum >= 0 && asNum < chs.length) {
            return asNum;
        }
        const norm = chParam.toLowerCase().trim();
        const foundIdx = chs.findIndex(c => (c.slug && c.slug.toLowerCase() === norm));
        return foundIdx >= 0 ? foundIdx : null;
    }

    // URL Hash and Query Parameter routing check
    const LEGACY_BOOK_SLUGS = {
        'sleep': 'human-functions',
        'twelve-virtues': 'virtues',
        'twelve-plants': 'plants',
        'twelve-materials': 'materials',
        'twelve-emotions': 'emotions',
        'twelve-vaccines': 'vaccines'
    };
    function handleHashRoute() {
        const hash = window.location.hash;
        const searchParams = new URLSearchParams(window.location.search);
        let queryBook = searchParams.get('book');
        if (LEGACY_BOOK_SLUGS[queryBook]) queryBook = LEGACY_BOOK_SLUGS[queryBook];

        if (hash.startsWith('#read=')) {
            const params = new URLSearchParams(hash.slice(1));
            let bookKey = params.get('read');
            if (LEGACY_BOOK_SLUGS[bookKey]) bookKey = LEGACY_BOOK_SLUGS[bookKey];
            const pageParam = parseInt(params.get('page') || '0', 10);
            const chParam = params.get('ch');
            if (EMBEDDED_BOOKS[bookKey]) {
                hideHomeView();
                const chIdx = resolveChapterIndexParam(bookKey, chParam);
                const savedPage = getSavedBookPage(bookKey);
                const targetPage = pageParam > 0 ? pageParam : (savedPage || READER_FIRST_PAGE);
                if (currentBookKey !== bookKey || !activeBook) {
                    loadBook(bookKey, targetPage, chIdx);
                } else if (chIdx !== null) {
                    jumpToChapterIndex(chIdx);
                } else if (pageParam > 0 && pdfPageNum !== pageParam) {
                    pdfPageNum = pageParam;
                    rebuildAndRenderSpread();
                }
            } else {
                showHomeView();
            }
        } else if (queryBook && EMBEDDED_BOOKS[queryBook] && hash !== '#catalog' && hash !== '#home') {
            const pageParam = parseInt(searchParams.get('page') || '0', 10);
            const chParam = searchParams.get('ch');
            const chIdx = resolveChapterIndexParam(queryBook, chParam);
            hideHomeView();
            loadBook(queryBook, pageParam > 0 ? pageParam : READER_FIRST_PAGE, chIdx);
        } else if (hash === '#home' || hash === '#catalog' || !hash) {
            const homeView = document.getElementById('home-view');
            if (!homeView || !homeView.classList.contains('active')) {
                showHomeView();
            } else {
                renderCatalogGrid();
            }
        }
    }

    // Event Listeners
    let resizeTimer = null;
    function scheduleSpreadResize() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            rebuildAndRenderSpread();
        }, 60);
    }
    window.addEventListener('resize', scheduleSpreadResize);
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', scheduleSpreadResize);
    }

    // Touch swipe left/right to turn pages on mobile/tablet
    let touchStartX = 0;
    let touchStartY = 0;
    window.addEventListener('touchstart', (e) => {
        if (e.touches && e.touches.length === 1) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }
    }, { passive: true });

    window.addEventListener('touchend', (e) => {
        const homeView = document.getElementById('home-view');
        if (homeView && homeView.classList.contains('active')) return;
        if (document.querySelector('.modal-overlay.open')) return;
        if (e.changedTouches && e.changedTouches.length === 1) {
            const dx = e.changedTouches[0].clientX - touchStartX;
            const dy = e.changedTouches[0].clientY - touchStartY;
            if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.6) {
                advancePage(dx < 0 ? 1 : -1);
            }
        }
    }, { passive: true });

    // Book Creator Studio State & Logic
    const PIPELINE_PRESETS = {
        'human-functions': {
            slug: 'human-functions',
            title: 'Human Functions',
            subtitle: 'Sleeping, Breathing, Walking, Running, and Eight Other Daily Acts in Twelve Highlights Each',
            category: 'Physiology & Biomechanics',
            mode: 'listicle',
            format: 'highlights',
            profile: 'B'
        },
        'twelve-foods': {
            slug: 'twelve-foods',
            title: 'Twelve Foods',
            subtitle: 'The Physics, Chemistry, and History of the Kitchen',
            category: 'Chemistry & Culture',
            mode: 'facet',
            format: 'mechanisms',
            profile: 'B'
        },
        'leonardo-da-vinci': {
            slug: 'leonardo-da-vinci',
            title: 'Leonardo da Vinci',
            subtitle: 'The Anatomist Engineer of Renaissance Florence and Milan',
            category: 'Biography & Engineering',
            mode: 'facet',
            format: 'biography',
            profile: 'D'
        },
        'the-night-sky': {
            slug: 'the-night-sky',
            title: 'The Night Sky',
            subtitle: 'Twelve Celestial Objects and Phenomena in Twelve Highlights Each',
            category: 'Astrophysics & Astronomy',
            mode: 'listicle',
            format: 'highlights',
            profile: 'A'
        },
        'evolution': {
            slug: 'evolution',
            title: 'Evolution',
            subtitle: 'Natural Selection and Eleven Neighbors That Shape Adaptation, Drift, and Form',
            category: 'Evolutionary Biology',
            mode: 'landscape',
            format: 'landscape',
            profile: 'B'
        },
        'twelve-colors': {
            slug: 'twelve-colors',
            title: 'Twelve Colors',
            subtitle: 'How Rare Pigments, Quantum Transitions, and Synthetic Dyes Painted the World',
            category: 'Optics & Chemistry',
            mode: 'facet',
            format: 'mechanisms',
            profile: 'A'
        }
    };

    let creatorState = {
        step: 1,
        slug: 'human-functions',
        title: 'Human Functions',
        subtitle: 'Sleeping, Breathing, Walking, Running, and Eight Other Daily Acts in Twelve Highlights Each',
        category: 'Physiology & Biomechanics',
        mode: 'listicle',
        format: 'highlights',
        profile: 'B',
        email: 'niraj@alexandria.press',
        activeJobId: null,
        pollTimer: null
    };

    function syncCreatorInputsFromState() {
        const titleEl = document.getElementById('creator-title');
        const subEl = document.getElementById('creator-subtitle');
        const catEl = document.getElementById('creator-category');
        const profEl = document.getElementById('creator-profile');
        const emailEl = document.getElementById('creator-email');
        if (titleEl) titleEl.value = creatorState.title;
        if (subEl) subEl.value = creatorState.subtitle;
        if (catEl) catEl.value = creatorState.category;
        if (profEl) profEl.value = creatorState.profile;
        if (emailEl && !emailEl.value) emailEl.value = creatorState.email;

        document.querySelectorAll('#creator-format-grid .creator-format-card').forEach(card => {
            card.classList.toggle('active', card.getAttribute('data-format') === creatorState.format);
        });
        document.querySelectorAll('#creator-pipeline-chips .creator-chip').forEach(chip => {
            const onClickAttr = chip.getAttribute('onclick') || '';
            chip.classList.toggle('active', onClickAttr.includes(`'${creatorState.slug}'`));
        });
    }

    function openCreatorModal() {
        const modal = document.getElementById('creator-modal');
        if (modal) {
            modal.classList.add('open');
            syncCreatorInputsFromState();
            fetchLatestCreatorJobReceipt();
        }
    }

    function setCreatorStep(stepNum) {
        creatorState.step = stepNum;
        const titleEl = document.getElementById('creator-title');
        const subEl = document.getElementById('creator-subtitle');
        const catEl = document.getElementById('creator-category');
        const profEl = document.getElementById('creator-profile');
        if (titleEl && titleEl.value.trim()) {
            creatorState.title = titleEl.value.trim().replace(/:/g, '');
        }
        if (subEl && subEl.value.trim()) {
            creatorState.subtitle = subEl.value.trim().replace(/:/g, '');
        }
        if (catEl && catEl.value.trim()) {
            creatorState.category = catEl.value.trim();
        }
        if (profEl && profEl.value) {
            creatorState.profile = profEl.value;
        }
        document.querySelectorAll('#creator-stepper .creator-step-pill').forEach(p => {
            p.classList.toggle('active', parseInt(p.getAttribute('data-step'), 10) === stepNum);
        });
        [1, 2, 3].forEach(n => {
            const pane = document.getElementById(`creator-step-${n}`);
            if (pane) pane.classList.toggle('active', n === stepNum);
        });
    }

    function selectPipelineTopic(slug) {
        const preset = PIPELINE_PRESETS[slug];
        if (!preset) return;
        creatorState.slug = preset.slug;
        creatorState.title = preset.title;
        creatorState.subtitle = preset.subtitle;
        creatorState.category = preset.category;
        creatorState.mode = preset.mode;
        creatorState.format = preset.format;
        creatorState.profile = preset.profile;
        syncCreatorInputsFromState();
    }

    function handleCreatorTitleInput(val) {
        const clean = (val || '').trim().replace(/:/g, '');
        creatorState.title = clean;
        const slugKey = clean.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        creatorState.slug = slugKey || 'custom-volume';
        if (PIPELINE_PRESETS[slugKey]) {
            selectPipelineTopic(slugKey);
        } else if (clean) {
            const subEl = document.getElementById('creator-subtitle');
            if (subEl && (!subEl.value || Object.values(PIPELINE_PRESETS).some(p => p.subtitle === subEl.value))) {
                creatorState.subtitle = creatorState.format === 'landscape'
                    ? `The Core Concept and Eleven Neighbors That Shape ${clean}`
                    : (creatorState.format === 'highlights'
                        ? `Twelve Subsystems of ${clean} in Twelve Highlights Each`
                        : `Twelve Mechanisms and Turning Points of ${clean}`);
                subEl.value = creatorState.subtitle;
            }
        }
    }

    function selectCreatorFormat(format, mode, btnEl) {
        creatorState.format = format;
        creatorState.mode = mode;
        document.querySelectorAll('#creator-format-grid .creator-format-card').forEach(c => c.classList.remove('active'));
        if (btnEl) btnEl.classList.add('active');
    }

    function renderCreatorTelemetry(job) {
        if (!job) return;
        const u = job.usage || {};
        const c = job.cost || {};
        const inEl = document.getElementById('cm-input-tokens');
        const outEl = document.getElementById('cm-output-tokens');
        const srchEl = document.getElementById('cm-searches');
        const costEl = document.getElementById('cm-cost-usd');
        const savEl = document.getElementById('creator-savings-line');
        const badgeEl = document.getElementById('creator-status-badge');
        const progWrap = document.getElementById('creator-progress-wrap');
        const progFill = document.getElementById('creator-progress-fill');
        const stageTxt = document.getElementById('creator-stage-text');
        const logBox = document.getElementById('creator-log-box');
        const delivCard = document.getElementById('creator-delivery-card');
        const launchBtn = document.getElementById('creator-launch-btn');

        if (inEl) inEl.textContent = (u.total_input_tokens || 0).toLocaleString();
        if (outEl) {
            const vis = u.total_visible_output_tokens || 0;
            const thk = u.total_thinking_tokens || 0;
            outEl.textContent = `${(vis + thk).toLocaleString()} (${thk.toLocaleString()} think)`;
        }
        if (srchEl) {
            srchEl.textContent = `${u.google_searches_used || 0} / ${u.google_searches_max || 12} (1/ch)`;
        }
        if (costEl) {
            costEl.textContent = `$${(c.intro_batch_token_cost_usd || 0).toFixed(4)}`;
        }
        if (savEl) {
            savEl.textContent = `50% Batch API savings: -$${(c.intro_batch_savings_usd || 0).toFixed(4)} vs. on-demand ($${(c.intro_ondemand_equivalent_usd || 0).toFixed(4)}) · Standard tier eq: $${(c.standard_batch_token_cost_usd || 0).toFixed(4)}`;
        }
        if (badgeEl) {
            badgeEl.textContent = (job.status || 'RUNNING').toUpperCase();
        }
        if (progWrap) progWrap.style.display = 'block';
        if (progFill) progFill.style.width = `${job.progress_pct || 5}%`;
        if (stageTxt) {
            stageTxt.textContent = `${job.stage_label || 'Running...'} (${job.elapsed_seconds || 0}s)`;
        }
        if (logBox && Array.isArray(job.logs)) {
            logBox.innerHTML = job.logs.slice(-14).map(l => `<div>${escapeHtml(l)}</div>`).join('');
            logBox.scrollTop = logBox.scrollHeight;
        }
        if (job.status === 'completed' && job.delivery && delivCard) {
            delivCard.style.display = 'block';
            const d = job.delivery;
            const valSummary = (job.validation && job.validation.summary) || {};
            delivCard.innerHTML = `
                <div style="font-family:var(--font-mono);font-size:0.68rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--accent-color);font-weight:600;margin-bottom:4px;">
                    Volume Published &amp; Link Dispatched
                </div>
                <div><strong>Email Sent To:</strong> ${escapeHtml(d.recipient_email || '')}</div>
                <div><strong>Validation Gate:</strong> PASS (${valSummary.chapters || 12} chs &middot; ${(valSummary.total_words || 0).toLocaleString()} words &middot; ${valSummary.avg_sent_words || 0} w/s &middot; ${u.google_searches_used || 12}/12 Google Searches)</div>
                <div style="margin-top:8px;display:flex;gap:10px;align-items:center;">
                    <a href="#read=${escapeHtml(job.slug)}" onclick="closeModals(); selectBook('${escapeHtml(job.slug)}'); return false;" class="creator-primary-btn" style="text-decoration:none;display:inline-block;">Open "${escapeHtml(job.title)}" in Spread Reader &rarr;</a>
                    <a href="assets/pdfs/${escapeHtml(job.slug)}.pdf" target="_blank" rel="noopener" class="creator-secondary-btn" style="text-decoration:none;display:inline-block;">Download PDF</a>
                </div>
            `;
            if (launchBtn) {
                launchBtn.disabled = false;
                launchBtn.textContent = 'Commission Another Volume \u2192';
            }
        }
    }

    async function fetchLatestCreatorJobReceipt() {
        try {
            let res = await fetch('/api/creator/status?job_id=latest', { cache: 'no-store' });
            if (!res.ok) {
                res = await fetch('dossiers/jobs/latest.json?t=' + Date.now(), { cache: 'no-store' });
            }
            if (res.ok) {
                const data = await res.json();
                if (data && data.job_id) {
                    renderCreatorTelemetry(data);
                    if (data.status === 'running' || data.status === 'initializing') {
                        startCreatorPolling(data.job_id);
                    }
                }
            }
        } catch (e) {}
    }

    function startCreatorPolling(jobId) {
        if (creatorState.pollTimer) clearInterval(creatorState.pollTimer);
        creatorState.activeJobId = jobId;
        creatorState.pollTimer = setInterval(async () => {
            try {
                let res = await fetch(`/api/creator/status?job_id=${encodeURIComponent(jobId)}`, { cache: 'no-store' });
                if (!res.ok) {
                    res = await fetch('dossiers/jobs/latest.json?t=' + Date.now(), { cache: 'no-store' });
                }
                if (res.ok) {
                    const job = await res.json();
                    renderCreatorTelemetry(job);
                    if (job.status === 'completed' || job.status === 'failed') {
                        clearInterval(creatorState.pollTimer);
                        creatorState.pollTimer = null;
                    }
                }
            } catch (e) {}
        }, 2500);
    }

    async function submitCreatorJob() {
        const titleEl = document.getElementById('creator-title');
        const subEl = document.getElementById('creator-subtitle');
        const catEl = document.getElementById('creator-category');
        const profEl = document.getElementById('creator-profile');
        const emailEl = document.getElementById('creator-email');
        const launchBtn = document.getElementById('creator-launch-btn');

        if (titleEl && titleEl.value.trim()) creatorState.title = titleEl.value.trim().replace(/:/g, '');
        if (subEl && subEl.value.trim()) creatorState.subtitle = subEl.value.trim().replace(/:/g, '');
        if (catEl && catEl.value.trim()) creatorState.category = catEl.value.trim();
        if (profEl && profEl.value) creatorState.profile = profEl.value;
        if (emailEl && emailEl.value.trim()) creatorState.email = emailEl.value.trim();

        if (!creatorState.title || !creatorState.email) return;

        if (launchBtn) {
            launchBtn.disabled = true;
            launchBtn.textContent = 'Submitting Gemini 4 Argon Batch...';
        }

        try {
            const resp = await fetch('/api/creator/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    slug: creatorState.slug,
                    title: creatorState.title,
                    subtitle: creatorState.subtitle,
                    category: creatorState.category,
                    mode: creatorState.mode,
                    format: creatorState.format,
                    profile: creatorState.profile,
                    email: creatorState.email
                })
            });
            if (resp.ok) {
                const initData = await resp.json();
                startCreatorPolling(initData.job_id || 'latest');
            }
        } catch (e) {
            if (launchBtn) {
                launchBtn.disabled = false;
                launchBtn.textContent = 'Commission Volume via Batch API \u2192';
            }
        }
    }

    window.addEventListener('keydown', (e) => {
        if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA')) {
            if (e.key === 'Escape') {
                if (e.target.id === 'catalog-search') {
                    e.target.value = '';
                    handleCatalogSearch('');
                }
                e.target.blur();
            }
            return;
        }
        if (e.metaKey || e.ctrlKey || e.altKey) return;

        const homeView = document.getElementById('home-view');
        const isHomeActive = homeView && homeView.classList.contains('active');
        const isModalOpen = !!document.querySelector('.modal-overlay.open');

        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
        } else if (e.key === 'd') {
            cycleTheme();
        } else if (e.key === '?') {
            openHelpModal();
        } else if (e.key === 'c' || e.key === 'C') {
            if (isHomeActive && !isModalOpen) {
                e.preventDefault();
                openCreatorModal();
            }
        } else if (e.key === 'h' || e.key === 'H') {
            e.preventDefault();
            document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
            showHomeView();
        } else if (isHomeActive && !isModalOpen) {
            if (e.key === '/') {
                const searchInput = document.getElementById('catalog-search');
                if (searchInput) {
                    e.preventDefault();
                    searchInput.focus();
                    searchInput.select();
                }
            } else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft' || e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                navigateCatalogGrid(e.key);
            } else if (e.key === 'Enter') {
                const visible = getVisibleBookCards();
                const targetCard = (selectedCatalogIndex >= 0 && visible[selectedCatalogIndex])
                    ? visible[selectedCatalogIndex]
                    : visible[0];
                if (targetCard) {
                    e.preventDefault();
                    const bookKey = targetCard.getAttribute('data-key');
                    if (bookKey) openBookFromCatalog(bookKey);
                }
            }
        } else if (!isHomeActive) {
            if (e.key === 'ArrowRight' || (e.key === ' ' && !e.shiftKey)) {
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
            } else if (e.key === 's' || e.key === 'l') {
                openSourcesModal();
            }
        }
    });

    window.addEventListener('DOMContentLoaded', () => {
        handleHashRoute();
    });

    window.addEventListener('hashchange', () => {
        handleHashRoute();
    });

    // Export modal & navigation handlers to window for inline HTML attributes
    window.advancePage = advancePage;
    window.nextChapter = nextChapter;
    window.prevChapter = prevChapter;
    window.openTocModal = openTocModal;
    window.openSourcesModal = openSourcesModal;
    window.openLibraryModal = openSourcesModal;
    window.openHelpModal = openHelpModal;
    window.openCreatorModal = openCreatorModal;
    window.setCreatorStep = setCreatorStep;
    window.selectPipelineTopic = selectPipelineTopic;
    window.handleCreatorTitleInput = handleCreatorTitleInput;
    window.selectCreatorFormat = selectCreatorFormat;
    window.submitCreatorJob = submitCreatorJob;
    window.closeModals = closeModals;
    window.cycleTheme = cycleTheme;
    window.loadBook = loadBook;
    window.showHomeView = showHomeView;
    window.hideHomeView = hideHomeView;
    window.openBookFromCatalog = openBookFromCatalog;
    window.filterCatalog = filterCatalog;
    window.handleCatalogSearch = handleCatalogSearch;
    window.copyChapterLink = copyChapterLink;
})();
