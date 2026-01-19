/* =============================================================================
   Alexandria Press - Book Reader Component
   ============================================================================= */

// Paper texture generator for realistic book appearance
class PaperTextureGenerator {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
    }

    generate(type, intensity, flocculation) {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;

        const { width, height } = this.canvas;
        const imageData = this.ctx.createImageData(width, height);
        const data = imageData.data;

        const paperColors = {
            cream: { r: 244, g: 241, b: 232 },
            smooth: { r: 252, g: 252, b: 250 }
        };

        const baseColor = paperColors[type] || paperColors.cream;
        const scaledIntensity = intensity * 5;

        const heightMap = new Float32Array(width * height);

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const index = y * width + x;
                const noise1 = this.noise(x * 0.02, y * 0.02);
                const noise2 = this.noise(x * 0.08, y * 0.08) * 0.5;
                const noise3 = this.noise(x * 0.3, y * 0.3) * 0.25;
                const grain = (Math.random() - 0.5) * 0.1;
                const intensityFactor = Math.sqrt(scaledIntensity);
                heightMap[index] = (noise1 + noise2 + noise3 + grain) * intensityFactor;
            }
        }

        const lightAngle = Math.PI / 4;
        const lightX = Math.cos(lightAngle);
        const lightY = Math.sin(lightAngle);
        const heightScale = (10 + scaledIntensity * 40);

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const index = (y * width + x) * 4;
                const heightIndex = y * width + x;

                const heightL = x > 0 ? heightMap[heightIndex - 1] : heightMap[heightIndex];
                const heightR = x < width - 1 ? heightMap[heightIndex + 1] : heightMap[heightIndex];
                const heightU = y > 0 ? heightMap[heightIndex - width] : heightMap[heightIndex];
                const heightD = y < height - 1 ? heightMap[heightIndex + width] : heightMap[heightIndex];

                const dx = (heightR - heightL) * heightScale;
                const dy = (heightD - heightU) * heightScale;

                const normalLength = Math.sqrt(dx * dx + dy * dy + 1);
                const nx = -dx / normalLength;
                const ny = -dy / normalLength;
                const nz = 1 / normalLength;

                const lighting = Math.max(0, nx * lightX + ny * lightY + nz * 0.7);
                const shade = (lighting - 0.5) * (8 + scaledIntensity * 15);
                const colorVar = (Math.random() - 0.5) * 2;

                data[index] = Math.min(255, Math.max(0, baseColor.r + shade + colorVar));
                data[index + 1] = Math.min(255, Math.max(0, baseColor.g + shade + colorVar));
                data[index + 2] = Math.min(255, Math.max(0, baseColor.b + shade + colorVar));
                data[index + 3] = 255;
            }
        }

        this.addPaperCharacteristics(data, width, height, type, scaledIntensity);

        if (flocculation > 0) {
            for (let y = 0; y < height; y++) {
                for (let x = 0; x < width; x++) {
                    const index = (y * width + x) * 4;
                    const flocNoise1 = this.noise(x * 0.008, y * 0.008) * 12;
                    const flocNoise2 = this.noise(x * 0.02, y * 0.02) * 6;
                    const flocNoise3 = this.noise(x * 0.05, y * 0.05) * 3;
                    const flocScale = Math.pow(flocculation, 0.8);
                    const flocEffect = (flocNoise1 + flocNoise2 + flocNoise3) * flocScale;

                    data[index] = Math.min(255, Math.max(0, data[index] + flocEffect));
                    data[index + 1] = Math.min(255, Math.max(0, data[index + 1] + flocEffect));
                    data[index + 2] = Math.min(255, Math.max(0, data[index + 2] + flocEffect));
                }
            }
        }

        this.ctx.putImageData(imageData, 0, 0);
    }

    addPaperCharacteristics(data, width, height, type, intensity) {
        if (type === 'cream') {
            for (let i = 0; i < 100; i++) {
                const x = Math.random() * width;
                const y = Math.random() * height;
                const radius = Math.random() * 12 + 5;
                const variation = (Math.random() - 0.5) * 15 * intensity;
                this.addCircularVariation(data, width, height, x, y, radius, variation, 0.7);
            }
        } else if (type === 'smooth') {
            for (let y = 0; y < height; y += 2) {
                for (let x = 0; x < width; x += 2) {
                    const index = (y * width + x) * 4;
                    const microGrain = (Math.random() - 0.5) * 2 * intensity;
                    if (index < data.length) {
                        data[index] = Math.min(255, Math.max(0, data[index] + microGrain));
                        data[index + 1] = Math.min(255, Math.max(0, data[index + 1] + microGrain));
                        data[index + 2] = Math.min(255, Math.max(0, data[index + 2] + microGrain));
                    }
                }
            }
        }
    }

    addCircularVariation(data, width, height, cx, cy, radius, variation, intensity) {
        const minX = Math.max(0, Math.floor(cx - radius));
        const maxX = Math.min(width, Math.ceil(cx + radius));
        const minY = Math.max(0, Math.floor(cy - radius));
        const maxY = Math.min(height, Math.ceil(cy + radius));

        for (let y = minY; y < maxY; y++) {
            for (let x = minX; x < maxX; x++) {
                const dist = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);
                if (dist < radius) {
                    const index = (y * width + x) * 4;
                    const factor = (1 - dist / radius) * variation * intensity;
                    data[index] = Math.max(0, Math.min(255, data[index] + factor));
                    data[index + 1] = Math.max(0, Math.min(255, data[index + 1] + factor));
                    data[index + 2] = Math.max(0, Math.min(255, data[index + 2] + factor));
                }
            }
        }
    }

    noise(x, y) {
        if (!this.permutation) {
            this.initPerlin();
        }

        const X = Math.floor(x) & 255;
        const Y = Math.floor(y) & 255;
        x -= Math.floor(x);
        y -= Math.floor(y);
        const u = this.fade(x);
        const v = this.fade(y);
        const A = this.permutation[X] + Y;
        const AA = this.permutation[A];
        const AB = this.permutation[A + 1];
        const B = this.permutation[X + 1] + Y;
        const BA = this.permutation[B];
        const BB = this.permutation[B + 1];

        return this.lerp(v,
            this.lerp(u, this.grad(this.permutation[AA], x, y),
                this.grad(this.permutation[BA], x - 1, y)),
            this.lerp(u, this.grad(this.permutation[AB], x, y - 1),
                this.grad(this.permutation[BB], x - 1, y - 1))
        );
    }

    initPerlin() {
        const p = [];
        for (let i = 0; i < 256; i++) p[i] = i;
        for (let i = 255; i > 0; i--) {
            const n = Math.floor(Math.random() * (i + 1));
            [p[i], p[n]] = [p[n], p[i]];
        }
        this.permutation = new Array(512);
        for (let i = 0; i < 512; i++) {
            this.permutation[i] = p[i & 255];
        }
    }

    fade(t) { return t * t * t * (t * (t * 6 - 15) + 10); }
    lerp(t, a, b) { return a + t * (b - a); }
    grad(hash, x, y) {
        const h = hash & 15;
        const u = h < 8 ? x : y;
        const v = h < 4 ? y : h === 12 || h === 14 ? x : 0;
        return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
    }
}

/* -----------------------------------------------------------------------------
   Book Reader Class
   ----------------------------------------------------------------------------- */

class BookReader {
    constructor() {
        this.pageFlip = null;
        this.bookData = null;
        this.settings = {
            paperType: 'cream',
            inkDensity: 0.75,
            textureIntensity: 0.015,
            flocculation: 0.50
        };
        this.pagesWithTexture = new Set();
    }

    // Convert markdown content to HTML using marked.js (same as main app)
    formatContent(markdown) {
        // Remove the title line (already displayed separately as chapter title)
        let content = markdown.replace(/^# .+\n\n?/, '');

        // Use marked.js for proper markdown to HTML conversion
        if (typeof marked !== 'undefined') {
            return marked.parse(content);
        }

        // Fallback if marked is not available
        return content.split('\n\n').map(p => `<p>${p.trim()}</p>`).join('\n');
    }

    // Paginate content based on available height (dynamic pagination)
    paginateEntry(entry, pageHeight = null) {
        const formatted = this.formatContent(entry.content);

        // Get page height from actual container or use reasonable default
        const targetHeight = pageHeight || this.getPageContentHeight() || 500;

        // Create hidden measurement container matching page styles
        const measureContainer = document.createElement('div');
        measureContainer.className = 'reader-body-text';
        measureContainer.style.cssText = `
            position: absolute;
            visibility: hidden;
            width: 100%;
            max-width: 450px;
            font-family: 'Crimson Pro', Georgia, serif;
            font-size: 1.1em;
            line-height: 1.7;
            padding: 0;
        `;
        document.body.appendChild(measureContainer);

        // Parse HTML to get individual elements
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = formatted;
        const elements = Array.from(tempDiv.children);

        const pages = [];
        let currentPageElements = [];

        for (const el of elements) {
            // Add element to measurement container
            const clone = el.cloneNode(true);
            currentPageElements.push(clone);

            // Rebuild measurement container with current page elements
            measureContainer.innerHTML = '';
            currentPageElements.forEach(e => measureContainer.appendChild(e.cloneNode(true)));

            // Check if we've exceeded the target height (use 95% threshold for tighter packing)
            if (measureContainer.scrollHeight > targetHeight * 0.95 && currentPageElements.length > 1) {
                // Remove last element (it caused overflow)
                currentPageElements.pop();

                // Save current page without the overflowing element
                const pageHtml = currentPageElements.map(e => e.outerHTML).join('\n');
                pages.push(pageHtml);

                // Start new page with the overflowing element
                currentPageElements = [clone];
            }
        }

        // Add remaining content as final page
        if (currentPageElements.length > 0) {
            const pageHtml = currentPageElements.map(e => e.outerHTML).join('\n');
            pages.push(pageHtml);
        }

        // Cleanup
        document.body.removeChild(measureContainer);

        return pages;
    }

    // Get available height for page content (excluding chrome like headers/page numbers)
    getPageContentHeight() {
        // Calculate based on viewport and expected container layout to ensure we fit
        const viewportHeight = window.innerHeight;

        // Vertical space consumers:
        // Header: Book title + close button (~58px)
        // Nav: Bottom navigation (~60px)
        // Padding: Modal padding (~0), Container padding (~32px)
        // Page Chrome: Publisher (top) + Chapter (top) + Page Number (bottom) + margins

        // We need to be careful. The Reader Page has padding: 60px 50px;
        // The content consumes the space INSIDE that padding.

        const headerHeight = 60;
        const navHeight = 60;
        const verticalPadding = 20; // safe buffer

        // Total height available for the page DIV (including its padding)
        const availablePageHeight = viewportHeight - headerHeight - navHeight - verticalPadding;

        // Now subtract internal page padding (60px top + 60px bottom = 120px)
        // And internal chrome (Publisher ~20px, Chapter ~40px, PageNum ~20px + margins)
        // Let's approximate internal chrome + margins to ~100px
        const internalPadding = 120;
        const internalChrome = 100;

        const contentHeight = availablePageHeight - internalPadding - internalChrome;

        return Math.max(200, contentHeight);
    }

    // Build book pages from JSON data
    buildBookPages(targetPageHeight = null) {
        if (!this.bookData) return [];

        const pages = [];
        // If targetPageHeight provides the full PAGE height (including padding), 
        // we need to subtract the internal padding/chrome to get the CONTENT area height.
        // reader-page padding: 60px top + 60px bottom = 120px
        // chrome: ~100px
        const contentHeight = targetPageHeight ? targetPageHeight - 120 - 100 : null;

        // Front cover
        pages.push({
            type: 'cover',
            content: `
                <div class="reader-cover">
                    <div class="reader-cover-title">${this.bookData.title}</div>
                    <div class="reader-cover-subtitle">${this.bookData.descriptor || ''}</div>
                    <div class="reader-cover-publisher">Alexandria Press</div>
                </div>
            `
        });

        // Introduction (paginate if needed)
        if (this.bookData.introduction) {
            const introPages = this.paginateEntry({ content: `# Introduction\n\n${this.bookData.introduction}` }, contentHeight);

            introPages.forEach((pageContent, index) => {
                pages.push({
                    title: index === 0 ? 'Introduction' : null,
                    content: pageContent,
                    pageNum: pages.length
                });
            });
        }

        // Each entry
        if (this.bookData.entries && this.bookData.entries.length > 0) {
            this.bookData.entries.forEach((entry) => {
                const entryPages = this.paginateEntry(entry, contentHeight);

                entryPages.forEach((pageContent, pageIndex) => {
                    pages.push({
                        title: pageIndex === 0 ? entry.name : null,
                        section: pageIndex === 0 ? entry.section : null,
                        content: pageContent,
                        pageNum: pages.length
                    });
                });
            });
        } else {
            console.warn('No entries found in bookData');
        }

        // Back cover
        pages.push({
            type: 'cover',
            content: `
                <div class="reader-cover">
                    <div class="reader-cover-publisher" style="margin-top: 0; margin-bottom: auto;">Alexandria Press</div>
                    <div style="text-align: center; opacity: 0.8; line-height: 1.6; font-size: 0.95em;">
                        <p>${this.bookData.descriptor || 'A generated collection'}</p>
                        <p style="margin-top: 20px; font-size: 0.85em;">Generated by artificial intelligence<br>in conversation with humanity's wisdom</p>
                    </div>
                </div>
            `
        });

        return pages;
    }

    // Initialize the book reader with data
    async init(bookData) {
        this.bookData = bookData;
        this.pagesWithTexture = new Set();

        // Update modal title
        const titleEl = document.getElementById('readerBookTitle');
        if (titleEl) {
            titleEl.textContent = bookData.title;
        }

        // Get container
        const container = document.getElementById('bookReaderContent');
        if (!container) {
            console.error('Book reader container not found');
            return;
        }

        // Dynamic sizing based on viewport
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        // Available area for the book
        // Head (60) + Nav (60) = 120 buffer vertically
        // Add 20px safety buffer
        const availableHeight = viewportHeight - 140;

        // Width: leave some space for side margins if possible
        const availableWidth = Math.min(viewportWidth - 40, 1000);

        // Single page view on mobile/portrait
        const isMobile = viewportWidth < 768;

        // Build pages with the CALCULATED available height
        const bookPages = this.buildBookPages(availableHeight);
        console.log(`Building book with ${bookPages.length} pages`);

        // Create book element
        container.innerHTML = `
            <div class="reader-book-wrapper">
                <div id="readerBook"></div>
            </div>
            <div class="reader-navigation">
                <button class="reader-nav-button" id="readerPrevBtn">← Previous</button>
                <span class="reader-page-info" id="readerPageInfo">Page 1 of ${bookPages.length}</span>
                <button class="reader-nav-button" id="readerNextBtn">Next →</button>
            </div>
        `;

        const bookEl = document.getElementById('readerBook');

        // Create page elements
        bookPages.forEach((pageData, index) => {
            const pageDiv = document.createElement('div');
            pageDiv.className = 'reader-page';
            pageDiv.setAttribute('data-density', 'hard');

            // Add canvas for texture
            const canvas = document.createElement('canvas');
            canvas.className = 'reader-paper-texture';
            pageDiv.appendChild(canvas);

            // Add content
            const contentDiv = document.createElement('div');
            contentDiv.className = 'reader-page-content';

            if (pageData.type === 'cover') {
                contentDiv.innerHTML = pageData.content;
            } else {
                let html = '<div class="reader-publisher">Alexandria Press</div>';
                if (pageData.title) {
                    html += `<div class="reader-chapter-title">${pageData.title}</div>`;
                }
                html += `<div class="reader-body-text">${pageData.content}</div>`;
                if (pageData.pageNum) {
                    const pageNumClass = index % 2 === 0 ? 'right' : 'left';
                    html += `<div class="reader-page-number ${pageNumClass}">${pageData.pageNum}</div>`;
                }
                contentDiv.innerHTML = html;
            }

            pageDiv.appendChild(contentDiv);
            bookEl.appendChild(pageDiv);
        });

        // Wait for DOM to update
        await new Promise(resolve => setTimeout(resolve, 100));

        // Initialize PageFlip
        if (typeof St !== 'undefined' && typeof St.PageFlip !== 'undefined') {
            this.pageFlip = new St.PageFlip(bookEl, {
                width: isMobile ? availableWidth : availableWidth / 2, // Width of a SINGLE page
                height: availableHeight,
                size: 'fixed', // Use fixed to respect our calculated dimensions exactly
                // minWidth: 200,
                // maxWidth: 1000,
                // minHeight: 300,
                // maxHeight: 1200,
                showCover: true,
                flippingTime: 800,
                usePortrait: isMobile,
                startPage: 0,
                drawShadow: true,
                maxShadowOpacity: 0.4,
                mobileScrollSupport: false,
                swipeDistance: 30,
                clickEventForward: true,
                startZIndex: 100,
                disableFlipByClick: false
            });

            this.pageFlip.loadFromHTML(document.querySelectorAll('.reader-page'));

            // Event listeners for page flip
            this.pageFlip.on('flip', () => {
                this.updatePageInfo();
                this.updateNavButtons();
            });

            // Generate textures for visible pages
            this.generateInitialTextures();

            this.updatePageInfo();
            this.updateNavButtons();
            this.setupNavigation();

            // Setup debounced resize handler for repagination
            this.setupResizeHandler();
        } else {
            console.error('StPageFlip library not loaded');
            container.innerHTML = '<p style="padding: 40px; text-align: center;">Error loading page flip library.</p>';
        }
    }

    // Setup resize handler with debouncing
    setupResizeHandler() {
        let resizeTimeout;
        let lastHeight = window.innerHeight;

        window.addEventListener('resize', () => {
            // Only repaginate if height changed significantly (more than 50px)
            const heightDiff = Math.abs(window.innerHeight - lastHeight);
            if (heightDiff < 50) return;

            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                lastHeight = window.innerHeight;
                this.repaginate();
            }, 500); // 500ms debounce
        });
    }

    // Repaginate the book (called on resize)
    async repaginate() {
        if (!this.bookData) return;

        // Store current page position
        const currentPage = this.pageFlip ? this.pageFlip.getCurrentPageIndex() : 0;
        const totalPages = this.pageFlip ? this.pageFlip.getPageCount() : 1;
        const progress = currentPage / Math.max(totalPages - 1, 1);

        // Clear textures to regenerate
        this.pagesWithTexture = new Set();

        // Rebuild the book
        await this.init(this.bookData);

        // Try to restore approximate position
        if (this.pageFlip) {
            const newTotalPages = this.pageFlip.getPageCount();
            const targetPage = Math.floor(progress * (newTotalPages - 1));
            this.pageFlip.flip(targetPage);
        }
    }

    generateInitialTextures() {
        const pages = document.querySelectorAll('.reader-page');

        const observer = new ResizeObserver((entries) => {
            entries.forEach(entry => {
                const page = entry.target;
                const canvas = page.querySelector('.reader-paper-texture');

                if (canvas && entry.contentRect.width > 0 && entry.contentRect.height > 0) {
                    const pageIndex = Array.from(pages).indexOf(page);

                    if (!this.pagesWithTexture.has(pageIndex)) {
                        const generator = new PaperTextureGenerator(canvas);
                        generator.generate(
                            this.settings.paperType,
                            this.settings.textureIntensity,
                            this.settings.flocculation
                        );
                        this.pagesWithTexture.add(pageIndex);
                    }
                }
            });
        });

        pages.forEach(page => observer.observe(page));
    }

    updatePageInfo() {
        if (!this.pageFlip) return;
        const current = this.pageFlip.getCurrentPageIndex();
        const total = this.pageFlip.getPageCount();
        const pageInfo = document.getElementById('readerPageInfo');
        if (pageInfo) {
            pageInfo.textContent = `Page ${current + 1} of ${total}`;
        }
    }

    updateNavButtons() {
        if (!this.pageFlip) return;
        const prevBtn = document.getElementById('readerPrevBtn');
        const nextBtn = document.getElementById('readerNextBtn');

        if (prevBtn) prevBtn.disabled = this.pageFlip.getCurrentPageIndex() === 0;
        if (nextBtn) nextBtn.disabled = this.pageFlip.getCurrentPageIndex() >= this.pageFlip.getPageCount() - 1;
    }

    setupNavigation() {
        const prevBtn = document.getElementById('readerPrevBtn');
        const nextBtn = document.getElementById('readerNextBtn');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.pageFlip?.flipPrev());
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.pageFlip?.flipNext());
        }
    }

    open() {
        const modal = document.getElementById('bookReaderModal');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }

    close() {
        const modal = document.getElementById('bookReaderModal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
        }

        // Cleanup
        if (this.pageFlip) {
            this.pageFlip.destroy();
            this.pageFlip = null;
        }
        this.pagesWithTexture = new Set();
    }
}

// Global instance
const bookReader = new BookReader();

// Setup modal close handlers
document.addEventListener('DOMContentLoaded', () => {
    // Close button
    const closeBtn = document.getElementById('closeBookReader');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => bookReader.close());
    }

    // Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById('bookReaderModal');
            if (modal && !modal.classList.contains('hidden')) {
                bookReader.close();
            }
        }
    });

    // Click outside modal
    const modal = document.getElementById('bookReaderModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                bookReader.close();
            }
        });
    }
});
