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
        this.tocItems = []; // Track chapter/section pages for TOC
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

    // Generate HTML for the entire book flow
    buildMasterFlowHTML() {
        if (!this.bookData) return '';

        let html = '';

        // Introduction
        if (this.bookData.introduction) {
            html += `<div class="chapter-title">Introduction</div>`;
            html += `<div class="body-content">${this.formatContent(this.bookData.introduction)}</div>`;
        }

        // Each entry (chapter)
        if (this.bookData.entries && this.bookData.entries.length > 0) {
            this.bookData.entries.forEach((entry) => {
                if (!entry.content) return;

                html += `<div class="chapter-title">${entry.name}</div>`;
                if (entry.metadata?.section || entry.section) {
                    html += `<div class="section-label">${entry.metadata?.section || entry.section}</div>`;
                }
                html += `<div class="body-content">${this.formatContent(entry.content)}</div>`;
            });
        }

        return html;
    }

    // Deprecated: No longer used with the column flow approach
    calculateLinesPerPage() {
        return 0;
    }

    // Create page elements using Paged.js for high-quality fragmentation
    async createPageElements(dims) {
        const container = document.getElementById('readerBook');
        const sourceContainer = document.getElementById('pagedSource');
        if (!container || !sourceContainer) return 0;

        // 1. Prepare Content for Paged.js
        sourceContainer.innerHTML = this.buildMasterFlowHTML();

        // 2. Configure Paged.js with EXACT dimensions
        const pageWidth = dims.pageWidth;
        const pageHeight = dims.pageHeight;

        // Add Paged.js styles to the document dynamically for fragmentation
        let style = document.getElementById('paged-js-styles');
        if (!style) {
            style = document.createElement('style');
            style.id = 'paged-js-styles';
            document.head.appendChild(style);
        }

        // Ensure margins match the CSS .page padding EXACTLY so content fits
        // CSS .page is padding: 60px 50px;
        // We add extra bottom margin to ensure text doesn't hit the page number
        style.innerHTML = `
            @page {
                size: ${pageWidth}px ${pageHeight}px;
                margin-top: 60px;
                margin-bottom: 100px; 
                margin-left: 50px;
                margin-right: 50px;
            }
            .pagedjs_pages {
                width: ${pageWidth}px;
                height: ${pageHeight}px;
            }
            .pagedjs_page {
                width: ${pageWidth}px;
                height: ${pageHeight}px;
            }
            .chapter-title {
                break-before: page !important;
                page-break-before: always !important;
            }
        `;

        // 3. Run Paged.js Fragmentation
        console.log('Starting Paged.js fragmentation...');
        const paged = new Paged.Previewer();
        const pagedContainer = document.createElement('div');
        pagedContainer.style.visibility = 'hidden';
        pagedContainer.style.position = 'absolute';
        pagedContainer.style.zIndex = '-1000';
        document.body.appendChild(pagedContainer);

        // Prepend the @page styles to the content so Paged.js definitely sees them
        // We set side margins to 60px to match what we will add as padding in the viewer
        const dynamicStyles = `
            <style>
                @page {
                    size: ${pageWidth}px ${pageHeight}px;
                    margin-top: 80px; 
                    margin-bottom: 80px;
                    margin-left: 60px;
                    margin-right: 60px;
                }
                .chapter-title {
                    break-before: page !important;
                    page-break-before: always !important;
                }
            </style>
        `;

        // Pass reader.css explicitly + inject dynamic styles into the content flow
        await paged.preview(dynamicStyles + sourceContainer.innerHTML, ['css/reader.css'], pagedContainer);
        console.log('Paged.js fragmentation complete');

        // 4. Extract Fragmented Pages
        const pagedPages = pagedContainer.querySelectorAll('.pagedjs_page');
        const numContentPages = pagedPages.length;
        console.log(`Extracted ${numContentPages} content pages`);

        // 5. Build Physical Pages for PageFlip
        container.innerHTML = '';
        this.tocItems = [];

        // Front Cover
        this.addPhysicalPage(container, 'cover', `
            <div class="cover">
                <div class="cover-title">${this.bookData.title}</div>
                <div class="cover-subtitle">${this.bookData.descriptor || ''}</div>
                <div class="cover-publisher">Alexandria Press</div>
            </div>
        `, 0);

        // Content Pages
        pagedPages.forEach((pagedPage, i) => {
            const contentHTML = pagedPage.querySelector('.pagedjs_page_content').innerHTML;

            // Check for chapter titles to update TOC
            const chapterTitle = pagedPage.querySelector('.chapter-title');
            if (chapterTitle) {
                this.tocItems.push({
                    title: chapterTitle.textContent.trim(),
                    pageIndex: i + 1 // +1 for cover
                });
            }

            const pageHTML = `
                <div class="body-text">${contentHTML}</div>
                <div class="page-number ${i % 2 === 0 ? 'left' : 'right'}">${i + 1}</div>
            `;
            this.addPhysicalPage(container, 'content', pageHTML, i + 1);
        });

        // Back Cover
        this.addPhysicalPage(container, 'cover', `
            <div class="cover">
                <div class="cover-publisher" style="margin-top: 0; margin-bottom: auto;">Alexandria Press</div>
                <div style="text-align: center; opacity: 0.8; line-height: 1.6; font-size: 0.95em;">
                    <p>${this.bookData.descriptor || 'A generated collection'}</p>
                    <p style="margin-top: 20px; font-size: 0.85em;">Generated by artificial intelligence<br>in conversation with humanity's wisdom</p>
                </div>
            </div>
        `, numContentPages + 1);

        // Cleanup
        document.body.removeChild(pagedContainer);
        sourceContainer.innerHTML = '';

        return numContentPages + 2;
    }

    addPhysicalPage(container, type, html, index) {
        const pageDiv = document.createElement('div');
        pageDiv.className = 'page';
        pageDiv.setAttribute('data-density', 'hard');

        // Add canvas for texture
        const canvas = document.createElement('canvas');
        canvas.className = 'paper-texture';
        pageDiv.appendChild(canvas);

        const contentDiv = document.createElement('div');
        contentDiv.className = 'page-content';
        contentDiv.innerHTML = html;

        pageDiv.appendChild(contentDiv);
        container.appendChild(pageDiv);
    }

    // Initialize page flip library
    initPageFlip(pageWidth, pageHeight) {
        const bookContainer = document.getElementById('readerBook');
        if (!bookContainer) return;

        // Check if StPageFlip library loaded
        if (typeof St === 'undefined' || typeof St.PageFlip === 'undefined') {
            console.error('StPageFlip library not loaded');
            return;
        }

        const flipConfig = {
            width: pageWidth,  // Use calculated page width directly
            height: pageHeight,
            size: 'fixed',
            minWidth: 300,
            maxWidth: 3000,
            minHeight: 400,
            maxHeight: 3000,
            showCover: true,
            flippingTime: 1000,
            usePortrait: this.isMobile, // Single page on mobile, Spread on desktop
            startPage: 0,
            drawShadow: true,
            maxShadowOpacity: 0.5,
            mobileScrollSupport: false,
            swipeDistance: 30,
            clickEventForward: true,
            startZIndex: 100,
            disableFlipByClick: false
        };

        console.log('Initializing PageFlip with config:', flipConfig);

        this.pageFlip = new St.PageFlip(bookContainer, flipConfig);

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
        const toolbar = document.createElement('div');
        toolbar.className = 'reader-toolbar';
        // Force top positioning to override any cached CSS issues
        toolbar.style.top = '0';
        toolbar.style.bottom = 'auto';
        toolbar.style.position = 'fixed';
        toolbar.innerHTML = `
            <div class="reader-toolbar-controls">
                <button class="reader-tool-btn reader-menu-btn" id="readerMenuBtn" title="Table of Contents">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="3" y1="6" x2="21" y2="6"/>
                        <line x1="3" y1="12" x2="21" y2="12"/>
                        <line x1="3" y1="18" x2="21" y2="18"/>
                    </svg>
                </button>
                <div class="reader-pagination">
                    <button class="reader-tool-btn" id="readerPrevBtn" title="Previous Page">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
                    </button>
                    <span class="reader-page-info" id="readerPageInfo">1 / ${totalPages}</span>
                    <button class="reader-tool-btn" id="readerNextBtn" title="Next Page">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
                    </button>
                </div>
                <button class="reader-tool-btn reader-close-btn-toolbar" onclick="window.close(); window.location.href='/'" title="Close Reader">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
        `;
        document.body.appendChild(toolbar);

        // Add TOC Menu to body as well
        this.addTocMenu(document.body);
    }

    // Add Table of Contents Menu
    addTocMenu(container) {
        const tocMenu = document.createElement('div');
        tocMenu.className = 'toc-menu';
        tocMenu.id = 'readerTocMenu';

        let tocHtml = `<div class="toc-header">Contents</div><div class="toc-content">`;

        for (const item of this.tocItems) {
            tocHtml += `
                <button class="toc-item" data-page="${item.pageIndex}">
                    ${item.title}
                    <span class="toc-item-page">${item.pageIndex + 1}</span>
                </button>
            `;
        }

        tocHtml += `</div>`;
        tocMenu.innerHTML = tocHtml;
        container.appendChild(tocMenu);

        // Setup TOC event listeners
        this.setupTocMenu();
    }

    // Setup TOC Menu interactions
    setupTocMenu() {
        const menuBtn = document.getElementById('readerMenuBtn');
        const tocMenu = document.getElementById('readerTocMenu');

        if (!menuBtn || !tocMenu) return;

        // Toggle menu on button click
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            tocMenu.classList.toggle('open');
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!tocMenu.contains(e.target) && e.target !== menuBtn) {
                tocMenu.classList.remove('open');
            }
        });

        // Navigate to chapter on item click
        tocMenu.querySelectorAll('.toc-item').forEach(item => {
            item.addEventListener('click', () => {
                const pageIndex = parseInt(item.dataset.page, 10);
                if (this.pageFlip && !isNaN(pageIndex)) {
                    this.pageFlip.turnToPage(pageIndex);
                    tocMenu.classList.remove('open');
                }
            });
        });
    }

    // Calculate optimal book dimensions to fit in viewport
    calculateDimensions(viewportW, viewportH) {
        const toolbarHeight = 60;
        const paddingV = 40; // Vertical padding for top/bottom
        const paddingH = 60; // Horizontal padding for left/right safety

        const availableH = viewportH - toolbarHeight - paddingV;
        const availableW = viewportW - paddingH;

        if (this.isMobile) {
            return {
                pageWidth: availableW,
                pageHeight: availableH,
                spreadWidth: availableW,
                height: availableH
            };
        }

        // DESKTOP:
        // Prioritize utilizing the full width while maintaining a reasonable aspect ratio.
        // We want 2 pages side-by-side.

        let spreadWidth = availableW;
        let pHeight = availableH;

        // Calculate max width per page based on height (don't get too square/wide)
        // A minimum aspect ratio of 1.2 (Height/Width) prevents it from looking like a landscape monitor 
        const minAspectRatio = 1.2;
        const maxPageWidth = pHeight / minAspectRatio;

        // If the spread requires pages wider than maxPageWidth, constrain the width
        if (spreadWidth / 2 > maxPageWidth) {
            spreadWidth = maxPageWidth * 2;
        }

        // Calculate height based on this width, ensuring it fits
        // But actually we prefer filling height first usually.
        // Let's stick to: Height = Available Height (maximize vertical space)
        // Width = Spread Width / 2 (maximize horizontal space up to limit)

        let pWidth = spreadWidth / 2;

        // Round to integer
        pWidth = Math.floor(pWidth);
        pHeight = Math.floor(pHeight);
        spreadWidth = pWidth * 2;

        return {
            pageWidth: pWidth,
            pageHeight: pHeight,
            spreadWidth: spreadWidth,
            height: pHeight
        };
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
        const viewportHeight = window.innerHeight;
        this.isMobile = viewportWidth < 768;

        const dims = this.calculateDimensions(viewportWidth, viewportHeight);

        console.log('STRICT Layout Calc:', {
            viewport: { w: viewportWidth, h: viewportHeight },
            dims: dims
        });

        // Set explicit dimensions on the wrapper
        // The wrapper centers the book in the flex container #bookReaderContent
        container.innerHTML = `
            <div class="reader-book-wrapper" style="width: ${dims.spreadWidth}px; height: ${dims.height}px;">
                <div id="readerBook" style="width: 100%; height: 100%;"></div>
            </div>
        `;

        // Build pages
        console.log('Building book pages...');
        // Pass the calculated strict dimensions
        const totalPhysicalPages = await this.createPageElements(dims);
        console.log(`Built ${totalPhysicalPages} pages`);

        if (totalPhysicalPages === 0) {
            container.innerHTML = '<div style="color:white; text-align:center; padding:40px;">No content to display</div>';
            return;
        }

        // Add toolbar
        this.addToolbar(totalPhysicalPages);

        // Initialize PageFlip
        console.log('Initializing PageFlip...');
        this.initPageFlip(dims.pageWidth, dims.height);

        // Initialize textures
        this.initTextures();

        // Setup navigation
        this.setupNavigation();
        this.updatePageInfo();
        this.updateNavButtons();

        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                console.log('Window resized, reloading reader...');
                window.location.reload();
            }, 500);
        });

        console.log('BookReader initialization complete');
    }
}

// Export for use
if (typeof window !== 'undefined') {
    window.BookReader = BookReader;
}
