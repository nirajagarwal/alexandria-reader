/**
 * Alexandria Press - Markdown & Block Parser
 */

export function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

export function formatInline(str) {
    if (!str) return '';
    let s = escapeHtml(str);
    s = s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return s;
}

export function parseAlexandriaMarkdown(mdText) {
    const sections = mdText.split(/\n---\n/);
    const chapters = [];
    let bookTitle = "Alexandria Volume";
    let bookSubtitle = "";

    sections.forEach((sec, idx) => {
        sec = sec.trim();
        if (!sec) return;

        if (idx === 0 && sec.startsWith('# ')) {
            const firstLines = sec.split('\n');
            bookTitle = firstLines[0].replace(/^#\s+/, '').trim();
            if (firstLines.length > 1 && firstLines[1].startsWith('## ')) {
                bookSubtitle = firstLines[1].replace(/^##\s+/, '').trim();
            }
            return;
        }

        const lines = sec.split('\n');
        let label = "";
        let title = "";
        let subtitle = "";
        let bodyStartIndex = 0;

        for (let i = 0; i < lines.length; i++) {
            const l = lines[i].trim();
            if (l.startsWith('### ')) {
                label = l.replace(/^###\s+/, '').trim();
                if (i + 1 < lines.length && lines[i + 1].trim().startsWith('# ')) {
                    title = lines[i + 1].trim().replace(/^#\s+/, '').trim();
                }
                if (i + 2 < lines.length && lines[i + 2].trim().startsWith('## ')) {
                    subtitle = lines[i + 2].trim().replace(/^##\s+/, '').trim();
                }
                bodyStartIndex = i + 3;
                break;
            }
        }

        const rawBody = lines.slice(bodyStartIndex).join('\n').trim();
        chapters.push({
            label: label || (idx === 0 ? "Introduction" : `Chapter ${idx}`),
            title: title || "Untitled Chapter",
            subtitle: subtitle || "",
            body: rawBody
        });
    });

    return {
        title: bookTitle,
        subtitle: bookSubtitle,
        chapters: chapters
    };
}

export function parseChapterBlocks(rawBody) {
    const codeBlocks = [];
    let text = rawBody.replace(/```([a-zA-Z0-9]*)\n([\s\S]*?)```/g, (match, lang, code) => {
        const id = `__CODE_${codeBlocks.length}__`;
        codeBlocks.push(code.trim());
        return id;
    });

    // Ensure lists preceded or followed immediately by prose are isolated by double newlines
    const rawLines = text.split('\n');
    const separatedLines = [];
    let inList = false;
    for (let i = 0; i < rawLines.length; i++) {
        const line = rawLines[i];
        const trimmed = line.trim();
        const isListItem = /^(?:[\*\-]\s+|\d+\.\s+)/.test(trimmed);
        if (isListItem) {
            if (!inList && separatedLines.length > 0 && separatedLines[separatedLines.length - 1].trim() !== '') {
                separatedLines.push('');
            }
            inList = true;
        } else if (trimmed === '') {
            inList = false;
        } else {
            if (inList) {
                separatedLines.push('');
            }
            inList = false;
        }
        separatedLines.push(line);
    }
    text = separatedLines.join('\n');

    const paragraphs = text.split(/\n\s*\n/);
    const blocks = [];

    paragraphs.forEach(p => {
        p = p.trim();
        if (!p) return;

        if (p.startsWith('__CODE_')) {
            const idx = parseInt(p.replace(/[^0-9]/g, ''));
            const code = codeBlocks[idx] || "";
            blocks.push({
                type: 'code',
                text: code,
                html: `<div class="code-box"><code>${escapeHtml(code)}</code></div>`
            });
            return;
        }

        if (p.startsWith('* ') || p.startsWith('- ')) {
            const items = p.split('\n').filter(l => l.trim().startsWith('* ') || l.trim().startsWith('- '));
            let listHtml = '<ul>';
            items.forEach(it => {
                let content = it.replace(/^[*\-]\s+/, '').trim();
                content = formatInline(content);
                listHtml += `<li>${content}</li>`;
            });
            listHtml += '</ul>';
            blocks.push({
                type: 'list',
                itemCount: items.length,
                html: listHtml
            });
            return;
        }

        if (p.length < 90 && (p.includes(' = ') || p.includes(' ∝ ') || p.includes('∑') || p.includes('Π('))) {
            blocks.push({
                type: 'equation',
                text: p,
                html: `<div class="equation-box">${escapeHtml(p)}</div>`
            });
            return;
        }

        // Standard paragraph
        blocks.push({
            type: 'paragraph',
            text: p,
            html: `<p>${formatInline(p)}</p>`
        });
    });

    return blocks;
}
