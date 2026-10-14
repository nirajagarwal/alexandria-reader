/**
 * Alexandria Press - Paging, Pretext Layout & Dynamic Measurement Engine
 */

import { escapeHtml, formatInline, parseChapterBlocks } from './parser.js';

// Global canvas reference for measurement
let measureCanvas = null;

/**
 * Splits paragraph text into lines fitting colWidth using Pretext with segments or Canvas fallback
 */
export function getParagraphLines(text, colWidth, pretextModule = null) {
    const fontSpec = "18px 'Literata', Charter, Georgia, serif";
    const lineH = 28.5;

    // 1. Pretext with segments
    if (pretextModule && pretextModule.prepareWithSegments && pretextModule.layoutWithLines) {
        try {
            const prep = pretextModule.prepareWithSegments(text, fontSpec);
            const res = pretextModule.layoutWithLines(prep, colWidth, lineH);
            if (res && res.lines && res.lines.length > 0) {
                return res.lines.map(l => l.text.trim()).filter(Boolean);
            }
        } catch (e) {
            console.info("Pretext line layout note:", e.message);
        }
    }

    // 2. Browser Canvas 2D measurement
    if (typeof document !== 'undefined') {
        try {
            if (!measureCanvas) {
                measureCanvas = document.createElement('canvas');
            }
            const ctx = measureCanvas.getContext('2d');
            if (ctx) {
                ctx.font = fontSpec;
                const words = text.split(/\s+/).filter(Boolean);
                const lines = [];
                let currentLine = "";

                for (let i = 0; i < words.length; i++) {
                    const testLine = currentLine ? (currentLine + " " + words[i]) : words[i];
                    const w = ctx.measureText(testLine).width;
                    if (w > colWidth && currentLine) {
                        lines.push(currentLine);
                        currentLine = words[i];
                    } else {
                        currentLine = testLine;
                    }
                }
                if (currentLine) lines.push(currentLine);
                if (lines.length > 0) return lines;
            }
        } catch (e) {}
    }

    // 3. Fallback character-width approximation (~8.2px per character)
    const charsPerLine = Math.max(40, Math.floor(colWidth / 8.2));
    const words = text.split(/\s+/).filter(Boolean);
    const lines = [];
    let currentLine = "";
    for (let i = 0; i < words.length; i++) {
        const testLine = currentLine ? (currentLine + " " + words[i]) : words[i];
        if (testLine.length > charsPerLine && currentLine) {
            lines.push(currentLine);
            currentLine = words[i];
        } else {
            currentLine = testLine;
        }
    }
    if (currentLine) lines.push(currentLine);
    return lines;
}

/**
 * Renders paragraph HTML, applying classes for split continuation
 */
export function renderParagraphHtml(text, isContinuation = false, isContinued = false) {
    const classes = [];
    if (isContinuation) classes.push('para-split-continuation');
    if (isContinued) classes.push('para-split-continued');
    const classAttr = classes.length > 0 ? ` class="${classes.join(' ')}"` : "";
    return `<p${classAttr}>${formatInline(text)}</p>`;
}

/**
 * Measure non-paragraph block heights (code, equation, list)
 */
export function measureBlockHeight(block, colWidth) {
    if (block.type === 'equation') {
        return 44 + 24; // padding + font + margins
    }
    if (block.type === 'code') {
        const lines = block.text.split('\n').length;
        return (lines * 20) + 36;
    }
    if (block.type === 'list') {
        return (block.itemCount * 26) + 24;
    }
    return 60;
}

/**
 * Measures actual rendered header box height dynamically in the DOM
 */
export function measureHeaderBox(chapter, colWidth) {
    if (typeof document === 'undefined') return 180;

    let probe = document.getElementById("header-measure-probe");
    if (!probe) {
        probe = document.createElement("div");
        probe.id = "header-measure-probe";
        probe.style.cssText = "position:absolute; visibility:hidden; pointer-events:none; z-index:-1000; top:0; left:0;";
        document.body.appendChild(probe);
    }
    probe.style.width = colWidth + "px";
    probe.innerHTML = `
        <div class="chapter-header-box" style="margin-top:0;">
            <div class="c-label">${escapeHtml(chapter.label)}</div>
            <h1 class="c-title">${escapeHtml(chapter.title)}</h1>
            <div class="c-subtitle">${escapeHtml(chapter.subtitle)}</div>
        </div>
    `;
    const rect = probe.getBoundingClientRect();
    return Math.max(120, Math.ceil(rect.height) + 8);
}

/**
 * Builds Spreads for the Current Chapter with within-paragraph breaking
 */
export function paginateChapter(chapter, pretextModule = null) {
    const stage = typeof document !== 'undefined' ? document.getElementById("spread-container") : null;
    const colLeftEl = typeof document !== 'undefined' ? document.getElementById("col-left") : null;
    const totalWidth = (stage && stage.clientWidth > 400) ? stage.clientWidth : Math.max(600, (typeof window !== 'undefined' ? window.innerWidth - 160 : 1200));
    const totalHeight = (colLeftEl && colLeftEl.clientHeight > 200) ? colLeftEl.clientHeight : ((stage && stage.clientHeight > 200) ? stage.clientHeight : Math.max(500, (typeof window !== 'undefined' ? window.innerHeight - 120 : 700)));
    const isTwoCol = typeof window !== 'undefined' ? window.innerWidth >= 900 : true;
    const colWidth = (colLeftEl && colLeftEl.clientWidth > 200) ? colLeftEl.clientWidth : (isTwoCol ? Math.max(260, (totalWidth - 52) / 2) : totalWidth);
    
    // Safety buffer (8px) so bottom line never clips against container border
    const columnHeightBudget = totalHeight - 8;
    const lineH = 28.5;
    const paraMargin = 10;

    const blocks = parseChapterBlocks(chapter.body);

    // Dynamically measured header box for Column 1 on Spread 0
    const headerBoxHtml = `
        <div class="chapter-header-box">
            <div class="c-label">${escapeHtml(chapter.label)}</div>
            <h1 class="c-title">${escapeHtml(chapter.title)}</h1>
            <div class="c-subtitle">${escapeHtml(chapter.subtitle)}</div>
        </div>
    `;
    const headerBoxHeight = measureHeaderBox(chapter, colWidth);

    const spreads = [];
    let currentLeftItems = [];
    let currentRightItems = [];
    let leftUsedHeight = 0;
    let rightUsedHeight = 0;
    let spreadIdx = 0;

    let blockIdx = 0;
    let activeParaLines = null;
    let activeIsContinuation = false;

    while (blockIdx < blocks.length || activeParaLines !== null) {
        const leftBudget = (spreadIdx === 0) ? (columnHeightBudget - headerBoxHeight) : columnHeightBudget;
        const rightBudget = isTwoCol ? columnHeightBudget : 0;

        const targetIsLeft = (rightUsedHeight === 0 && currentRightItems.length === 0 && leftUsedHeight < leftBudget);
        const targetBudget = targetIsLeft ? leftBudget : rightBudget;
        const targetUsed = targetIsLeft ? leftUsedHeight : rightUsedHeight;
        const targetItems = targetIsLeft ? currentLeftItems : currentRightItems;
        const remBudget = targetBudget - targetUsed;

        // Single column mode: if left column full, advance spread immediately
        if (!isTwoCol && leftUsedHeight >= leftBudget) {
            spreads.push({
                isFirstSpread: spreadIdx === 0,
                colLeftHtml: (spreadIdx === 0 ? headerBoxHtml : "") + currentLeftItems.join(""),
                colRightHtml: ""
            });
            spreadIdx++;
            currentLeftItems = [];
            currentRightItems = [];
            leftUsedHeight = 0;
            rightUsedHeight = 0;
            continue;
        }

        // Non-paragraph atomic blocks (code, equation, list)
        if (activeParaLines === null) {
            const block = blocks[blockIdx];
            if (block.type !== "paragraph") {
                const blockH = measureBlockHeight(block, colWidth);
                if (blockH <= remBudget || targetItems.length === 0) {
                    targetItems.push(block.html);
                    if (targetIsLeft) leftUsedHeight += blockH;
                    else rightUsedHeight += blockH;
                    blockIdx++;
                    continue;
                } else {
                    if (targetIsLeft) {
                        leftUsedHeight = leftBudget;
                        if (!isTwoCol) {
                            spreads.push({
                                isFirstSpread: spreadIdx === 0,
                                colLeftHtml: (spreadIdx === 0 ? headerBoxHtml : "") + currentLeftItems.join(""),
                                colRightHtml: ""
                            });
                            spreadIdx++;
                            currentLeftItems = [];
                            currentRightItems = [];
                            leftUsedHeight = 0;
                            rightUsedHeight = 0;
                        }
                    } else {
                        spreads.push({
                            isFirstSpread: spreadIdx === 0,
                            colLeftHtml: (spreadIdx === 0 ? headerBoxHtml : "") + currentLeftItems.join(""),
                            colRightHtml: currentRightItems.join("")
                        });
                        spreadIdx++;
                        currentLeftItems = [];
                        currentRightItems = [];
                        leftUsedHeight = 0;
                        rightUsedHeight = 0;
                    }
                    continue;
                }
            }
        }

        // Paragraph blocks: break lines
        let pLines;
        let isCont;
        if (activeParaLines !== null) {
            pLines = activeParaLines;
            isCont = activeIsContinuation;
        } else {
            const block = blocks[blockIdx];
            pLines = getParagraphLines(block.text, colWidth, pretextModule);
            isCont = false;
        }

        const totalParaH = (pLines.length * lineH) + paraMargin;

        // Case 1: Paragraph fits completely in remaining column budget
        if (totalParaH <= remBudget || (targetItems.length === 0 && remBudget < lineH * 2)) {
            targetItems.push(renderParagraphHtml(pLines.join(" "), isCont, false));
            if (targetIsLeft) leftUsedHeight += totalParaH;
            else rightUsedHeight += totalParaH;

            if (activeParaLines !== null) {
                activeParaLines = null;
                activeIsContinuation = false;
                blockIdx++;
            } else {
                blockIdx++;
            }
            continue;
        }

        // Case 2: Paragraph does NOT fit completely. Break within paragraph!
        // 6px safety clearance guarantees zero 50% line cutoff
        const linesFit = Math.floor((remBudget - 6) / lineH);

        if (linesFit >= 1 && (pLines.length > linesFit)) {
            const firstSlice = pLines.slice(0, linesFit);
            const remSlice = pLines.slice(linesFit);

            targetItems.push(renderParagraphHtml(firstSlice.join(" "), isCont, true));
            if (targetIsLeft) leftUsedHeight += (linesFit * lineH);
            else rightUsedHeight += (linesFit * lineH);

            activeParaLines = remSlice;
            activeIsContinuation = true;

            if (targetIsLeft) {
                leftUsedHeight = leftBudget;
                if (!isTwoCol) {
                    spreads.push({
                        isFirstSpread: spreadIdx === 0,
                        colLeftHtml: (spreadIdx === 0 ? headerBoxHtml : "") + currentLeftItems.join(""),
                        colRightHtml: ""
                    });
                    spreadIdx++;
                    currentLeftItems = [];
                    currentRightItems = [];
                    leftUsedHeight = 0;
                    rightUsedHeight = 0;
                }
            } else {
                spreads.push({
                    isFirstSpread: spreadIdx === 0,
                    colLeftHtml: (spreadIdx === 0 ? headerBoxHtml : "") + currentLeftItems.join(""),
                    colRightHtml: currentRightItems.join("")
                });
                spreadIdx++;
                currentLeftItems = [];
                currentRightItems = [];
                leftUsedHeight = 0;
                rightUsedHeight = 0;
            }
        } else {
            if (targetItems.length === 0) {
                targetItems.push(renderParagraphHtml(pLines.join(" "), isCont, false));
                if (targetIsLeft) leftUsedHeight += totalParaH;
                else rightUsedHeight += totalParaH;
                if (activeParaLines !== null) {
                    activeParaLines = null;
                    activeIsContinuation = false;
                    blockIdx++;
                } else {
                    blockIdx++;
                }
            } else {
                if (targetIsLeft) {
                    leftUsedHeight = leftBudget;
                    if (!isTwoCol) {
                        spreads.push({
                            isFirstSpread: spreadIdx === 0,
                            colLeftHtml: (spreadIdx === 0 ? headerBoxHtml : "") + currentLeftItems.join(""),
                            colRightHtml: ""
                        });
                        spreadIdx++;
                        currentLeftItems = [];
                        currentRightItems = [];
                        leftUsedHeight = 0;
                        rightUsedHeight = 0;
                    }
                } else {
                    spreads.push({
                        isFirstSpread: spreadIdx === 0,
                        colLeftHtml: (spreadIdx === 0 ? headerBoxHtml : "") + currentLeftItems.join(""),
                        colRightHtml: currentRightItems.join("")
                    });
                    spreadIdx++;
                    currentLeftItems = [];
                    currentRightItems = [];
                    leftUsedHeight = 0;
                    rightUsedHeight = 0;
                }
            }
        }
    }

    // Push any remaining spread
    if (currentLeftItems.length > 0 || currentRightItems.length > 0 || spreads.length === 0) {
        spreads.push({
            isFirstSpread: spreadIdx === 0,
            colLeftHtml: (spreadIdx === 0 ? headerBoxHtml : "") + currentLeftItems.join(""),
            colRightHtml: currentRightItems.join("")
        });
    }

    return spreads;
}
