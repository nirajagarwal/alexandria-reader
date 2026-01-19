/* =============================================================================
   Alexandria Press - Book Reader Component
   Clean reimplementation based on working prototype
   ============================================================================= */

// Paper texture generator for realistic book appearance
class PaperTextureGenerator {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
    }

    generate(type, intensity, flocculation) {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;

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
        this.isMobile = window.innerWidth < 768;
    }

    // Convert markdown content to HTML paragraphs (simple approach)
    formatContent(markdown) {
        if (!markdown) return '';

        // Use marked.js if available
        if (typeof marked !== 'undefined') {
            // Remove title line if present (already shown as chapter title)
            let content = markdown.replace(/^# .+\n\n?/, '');
            return marked.parse(content);
        }

        // Simple fallback
        return markdown
            .replace(/^# .+\n\n?/, '')
            .replace(/## (.+)/g, '<div class="section-title">$1</div>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .split('\n\n')
            .filter(p => p.trim())
            .map(p => `<p>${p.trim()}</p>`)
            .join('\n');
    }

    // Paginate content using DOM-based height measurement
    // This properly splits paragraphs across pages for accurate reflow
    paginateEntry(entry, pageHeight) {
        const formatted = this.formatContent(entry.content);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = formatted;

        const elements = Array.from(tempDiv.children);
        if (elements.length === 0) return [];

        // Use provided height or calculate based on viewport
        const targetHeight = pageHeight || this.calculatePageContentHeight();

        // Create hidden measurement container matching page styling
        const measureContainer = document.createElement('div');
        measureContainer.className = 'body-text';
        measureContainer.style.cssText = `
            position: absolute;
            visibility: hidden;
            width: 380px;
            font-family: 'Crimson Pro', Georgia, serif;
            font-size: 1.1em;
            line-height: 1.7;
            text-align: justify;
            padding: 0;
            top: 0; left: 0;
        `;
        document.body.appendChild(measureContainer);

        const pages = [];
        let currentPageElements = [];

        // Helper to measure current page height
        const measureHeight = () => {
            measureContainer.innerHTML = '';
            currentPageElements.forEach(el => {
                measureContainer.appendChild(el.cloneNode(true));
            });
            return measureContainer.offsetHeight;
        };

        for (const el of elements) {
            // Try adding the whole element
            currentPageElements.push(el.cloneNode(true));

            if (measureHeight() <= targetHeight) {
                // Fits! Continue to next element
                continue;
            }

            // Doesn't fit - remove it and handle
            currentPageElements.pop();

            // Can we split this element? (Only split paragraph-like elements)
            if (el.nodeType === Node.ELEMENT_NODE &&
                ['P', 'DIV', 'LI', 'BLOCKQUOTE'].includes(el.tagName)) {

                // Split the paragraph across pages
                const [firstPart, secondPart] = this.splitElement(
                    el, currentPageElements, measureContainer, targetHeight
                );

                if (firstPart) {
                    currentPageElements.push(firstPart);
                }

                // Finalize current page
                if (currentPageElements.length > 0) {
                    pages.push(currentPageElements.map(e => e.outerHTML).join(''));
                    currentPageElements = [];
                }

                // Add remaining part to next page
                if (secondPart) {
                    currentPageElements.push(secondPart);
                }
            } else {
                // Can't split (heading, image, etc.) - finalize page and move element to next
                if (currentPageElements.length > 0) {
                    pages.push(currentPageElements.map(e => e.outerHTML).join(''));
                    currentPageElements = [];
                }
                currentPageElements.push(el.cloneNode(true));
            }
        }

        // Add remaining content
        if (currentPageElements.length > 0) {
            pages.push(currentPageElements.map(e => e.outerHTML).join(''));
        }

        document.body.removeChild(measureContainer);
        return pages;
    }

    // Split an element (paragraph) into two parts that fit the page
    splitElement(originalEl, currentPageElements, measureContainer, targetHeight) {
        const text = originalEl.textContent;
        const words = text.split(/\s+/);

        if (words.length <= 1) {
            // Can't split single word - return whole element for next page
            return [null, originalEl.cloneNode(true)];
        }

        // Create clone for first part
        const part1 = originalEl.cloneNode(false);

        // Binary search for optimal split point
        let low = 0;
        let high = words.length;
        let bestFit = 0;

        while (low < high) {
            const mid = Math.floor((low + high + 1) / 2);
            part1.textContent = words.slice(0, mid).join(' ');

            // Measure with this split
            measureContainer.innerHTML = '';
            currentPageElements.forEach(e => measureContainer.appendChild(e.cloneNode(true)));
            measureContainer.appendChild(part1);

            if (measureContainer.offsetHeight <= targetHeight) {
                bestFit = mid;
                low = mid;
            } else {
                high = mid - 1;
            }
        }

        if (bestFit === 0) {
            // Not even one word fits with current page content
            return [null, originalEl.cloneNode(true)];
        }

        if (bestFit >= words.length) {
            // Everything fits
            part1.textContent = text;
            return [part1, null];
        }

        // Create both parts
        part1.textContent = words.slice(0, bestFit).join(' ');
        const part2 = originalEl.cloneNode(false);
        part2.textContent = words.slice(bestFit).join(' ');

        return [part1, part2];
    }

    // Calculate available height for page content
    calculatePageContentHeight() {
        // Page has 60px padding top/bottom and ~80px for publisher/chapter headers
        const viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
        const pageHeight = Math.max(viewportHeight - 160, 400); // Subtract toolbar/margins
        const contentHeight = pageHeight - 120 - 80; // Subtract padding and headers
        return Math.max(200, contentHeight);
    }

    // Build all book pages from data
    buildBookPages() {
        if (!this.bookData) return [];

        const pages = [];

        // Front cover
        pages.push({
            type: 'cover',
            content: `
                <div class="cover">
                    <div class="cover-title">${this.bookData.title}</div>
                    <div class="cover-subtitle">${this.bookData.descriptor || ''}</div>
                    <div class="cover-publisher">Alexandria Press</div>
                </div>
            `
        });

        // Introduction (paginate if needed)
        if (this.bookData.introduction) {
            const introPages = this.paginateEntry({ content: `# Introduction\n\n${this.bookData.introduction}` });

            introPages.forEach((pageContent, index) => {
                pages.push({
                    title: index === 0 ? 'Introduction' : null,
                    content: pageContent,
                    pageNum: pages.length
                });
            });
        }

        // Each entry (chapter)
        if (this.bookData.entries && this.bookData.entries.length > 0) {
            console.log(`Processing ${this.bookData.entries.length} entries...`);
            this.bookData.entries.forEach((entry, i) => {
                // Skip entries without content
                if (!entry.content) {
                    console.warn(`Entry ${i} (${entry.name}) has no content, skipping`);
                    return;
                }

                const entryPages = this.paginateEntry(entry);

                if (entryPages.length === 0) {
                    console.warn(`Entry ${i} (${entry.name}) produced 0 pages`);
                    return;
                }

                entryPages.forEach((pageContent, pageIndex) => {
                    pages.push({
                        title: pageIndex === 0 ? entry.name : null,
                        section: pageIndex === 0 ? (entry.metadata?.section || entry.section) : null,
                        content: pageContent,
                        pageNum: pages.length
                    });
                });
            });
            console.log(`Total pages after entries: ${pages.length}`);
        }

        // Back cover
        pages.push({
            type: 'cover',
            content: `
                <div class="cover">
                    <div class="cover-publisher" style="margin-top: 0; margin-bottom: auto;">Alexandria Press</div>
                    <div style="text-align: center; opacity: 0.8; line-height: 1.6; font-size: 0.95em;">
                        <p>${this.bookData.descriptor || 'A generated collection'}</p>
                        <p style="margin-top: 20px; font-size: 0.85em;">Generated by artificial intelligence<br>in conversation with humanity's wisdom</p>
                    </div>
                </div>
            `
        });

        return pages;
    }

    // Create page DOM elements
    createPageElements(bookPages) {
        const container = document.getElementById('readerBook');
        if (!container) return;

        container.innerHTML = '';

        bookPages.forEach((pageData, index) => {
            const pageDiv = document.createElement('div');
            pageDiv.className = 'page';
            pageDiv.setAttribute('data-density', 'hard');

            // Add canvas for texture
            const canvas = document.createElement('canvas');
            canvas.className = 'paper-texture';
            pageDiv.appendChild(canvas);

            // Add content
            const contentDiv = document.createElement('div');
            contentDiv.className = 'page-content';

            if (pageData.type === 'cover') {
                contentDiv.innerHTML = pageData.content;
            } else {
                let html = '<div class="publisher">Alexandria Press</div>';
                if (pageData.title) {
                    html += `<div class="chapter-title">${pageData.title}</div>`;
                }
                if (pageData.section) {
                    html += `<div class="section-label">${pageData.section}</div>`;
                }
                html += `<div class="body-text">${pageData.content}</div>`;
                if (pageData.pageNum) {
                    const pageNumClass = index % 2 === 0 ? 'right' : 'left';
                    html += `<div class="page-number ${pageNumClass}">${pageData.pageNum}</div>`;
                }
                contentDiv.innerHTML = html;
            }

            pageDiv.appendChild(contentDiv);
            container.appendChild(pageDiv);
        });
    }

    // Initialize page flip library
    initPageFlip(width, height) {
        const bookContainer = document.getElementById('readerBook');
        if (!bookContainer) return;

        // Check if StPageFlip library loaded
        if (typeof St === 'undefined' || typeof St.PageFlip === 'undefined') {
            console.error('StPageFlip library not loaded');
            return;
        }

        this.pageFlip = new St.PageFlip(bookContainer, {
            width: this.isMobile ? width : width / 2,
            height: height,
            size: 'fixed',
            minWidth: 300,
            maxWidth: 600,
            minHeight: 400,
            maxHeight: 900,
            showCover: true,
            flippingTime: 1000,
            usePortrait: this.isMobile,
            startPage: 0,
            drawShadow: true,
            maxShadowOpacity: 0.5,
            mobileScrollSupport: false,
            swipeDistance: 30,
            clickEventForward: true,
            startZIndex: 100,
            disableFlipByClick: false
        });

        this.pageFlip.loadFromHTML(document.querySelectorAll('.page'));

        // Page flip events
        this.pageFlip.on('flip', () => {
            this.updatePageInfo();
            this.updateNavButtons();
        });
    }

    // Generate textures for visible pages using ResizeObserver
    initTextures() {
        const pages = document.querySelectorAll('.page');

        const observer = new ResizeObserver((entries) => {
            entries.forEach(entry => {
                const page = entry.target;
                const canvas = page.querySelector('.paper-texture');

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

    // Update page info display
    updatePageInfo() {
        if (!this.pageFlip) return;
        const current = this.pageFlip.getCurrentPageIndex() + 1;
        const total = this.pageFlip.getPageCount();

        const info = document.getElementById('readerPageInfo');
        if (info) info.textContent = `${current} / ${total}`;

        const progressBar = document.getElementById('readerProgressBar');
        if (progressBar) {
            const percent = ((current - 1) / Math.max(total - 1, 1)) * 100;
            progressBar.style.width = `${percent}%`;
        }
    }

    // Update navigation button states
    updateNavButtons() {
        if (!this.pageFlip) return;
        const prevBtn = document.getElementById('readerPrevBtn');
        const nextBtn = document.getElementById('readerNextBtn');

        if (prevBtn) prevBtn.disabled = this.pageFlip.getCurrentPageIndex() === 0;
        if (nextBtn) nextBtn.disabled = this.pageFlip.getCurrentPageIndex() >= this.pageFlip.getPageCount() - 1;
    }

    // Setup navigation button handlers
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

    // Add toolbar HTML
    addToolbar(totalPages) {
        const container = document.getElementById('bookReaderContent');
        if (!container) return;

        const toolbar = document.createElement('div');
        toolbar.className = 'reader-toolbar';
        toolbar.innerHTML = `
            <div class="reader-toolbar-progress">
                <div class="reader-progress-bar" id="readerProgressBar" style="width: 0%"></div>
            </div>
            <div class="reader-toolbar-controls">
                <button class="reader-tool-btn" id="readerPrevBtn" title="Previous Page">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
                </button>
                <span class="reader-page-info" id="readerPageInfo">1 / ${totalPages}</span>
                <button class="reader-tool-btn" id="readerNextBtn" title="Next Page">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
                </button>
            </div>
        `;
        container.appendChild(toolbar);
    }

    // Main initialization
    async init(bookData) {
        console.log('BookReader.init() called with:', bookData?.title);
        this.bookData = bookData;

        const container = document.getElementById('bookReaderContent');
        if (!container) {
            console.error('Container #bookReaderContent not found');
            return;
        }

        // Calculate dimensions
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
        this.isMobile = viewportWidth < 768;

        const availableHeight = Math.max(viewportHeight - 100, 400);
        const availableWidth = Math.min(viewportWidth - 40, this.isMobile ? 500 : 1000);

        // Set up container HTML
        container.innerHTML = `
            <div class="reader-book-wrapper">
                <div id="readerBook" style="height:${availableHeight}px; width:${availableWidth}px; margin:auto;"></div>
            </div>
        `;

        // Build pages
        console.log('Building book pages...');
        const bookPages = this.buildBookPages();
        console.log(`Built ${bookPages.length} pages`);

        if (bookPages.length === 0) {
            container.innerHTML = '<div style="color:white; text-align:center; padding:40px;">No content to display</div>';
            return;
        }

        // Create page elements
        this.createPageElements(bookPages);

        // Add toolbar
        this.addToolbar(bookPages.length);

        // Initialize PageFlip
        console.log('Initializing PageFlip...');
        this.initPageFlip(availableWidth, availableHeight);

        // Initialize textures
        this.initTextures();

        // Setup navigation
        this.setupNavigation();
        this.updatePageInfo();
        this.updateNavButtons();

        console.log('BookReader initialization complete');
    }
}

// Export for use
if (typeof window !== 'undefined') {
    window.BookReader = BookReader;
}
