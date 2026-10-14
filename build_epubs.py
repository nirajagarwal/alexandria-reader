#!/usr/bin/env python3
"""
Alexandria Press - Automated EPUB3 Builder
Compiles all Markdown volumes into valid EPUB3 packages with Literata styling.
"""

import os
import re
import html
import zipfile
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BOOKS_CONFIG = [
    {
        "md": "liminal_thresholds.md",
        "epub": "Liminal_Thresholds.epub",
        "title": "Liminal Thresholds",
        "subtitle": "Forensic Investigations of Phenomena That Defied Scientific Orthodoxy",
        "author": "Alexandria Press",
        "id": "alexandria-press-liminal-thresholds",
    },
    {
        "md": "non_linear_engines.md",
        "epub": "Non_Linear_Engines.epub",
        "title": "Non-Linear Engines",
        "subtitle": "Structural Mechanics of Asymmetric Enterprise Creation",
        "author": "Alexandria Press",
        "id": "alexandria-press-non-linear-engines",
    },
    {
        "md": "latent_fragility.md",
        "epub": "Latent_Fragility.epub",
        "title": "Latent Fragility",
        "subtitle": "Forensic Post-Mortems of Optimal Systems That Collapsed",
        "author": "Alexandria Press",
        "id": "alexandria-press-latent-fragility",
    },
    {
        "md": "singular_minds.md",
        "epub": "Singular_Minds.epub",
        "title": "Singular Minds",
        "subtitle": "Forensic Dissections of Anomalous Cognitive Architectures",
        "author": "Alexandria Press",
        "id": "alexandria-press-singular-minds",
    },
    {
        "md": "radical_subtraction.md",
        "epub": "Radical_Subtraction.epub",
        "title": "Radical Subtraction",
        "subtitle": "The Neuroscience and Information Theory of the Silent Contemplatives",
        "author": "Alexandria Press",
        "id": "alexandria-press-radical-subtraction",
    },
]

EPUB_CSS = """
@namespace "http://www.w3.org/1999/xhtml";

body {
    font-family: 'Literata', Charter, Georgia, serif;
    font-size: 1.05em;
    line-height: 1.58;
    color: #1a1a1a;
    background-color: #faf9f6;
    margin: 5% 8%;
    text-align: justify;
}

h1.book-title {
    font-size: 2.2em;
    font-weight: 700;
    line-height: 1.2;
    margin-top: 25%;
    margin-bottom: 0.2em;
    text-align: left;
}

h2.book-subtitle {
    font-size: 1.25em;
    font-weight: 400;
    font-style: italic;
    color: #555555;
    margin-bottom: 2em;
    text-align: left;
}

.c-label {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 0.8em;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #92400e;
    margin-bottom: 0.5em;
}

h1.c-title {
    font-size: 1.85em;
    font-weight: 700;
    line-height: 1.2;
    margin: 0 0 0.3em 0;
}

h2.c-subtitle {
    font-size: 1.1em;
    font-weight: 300;
    font-style: italic;
    color: #555555;
    margin: 0 0 1.5em 0;
    padding-bottom: 0.8em;
    border-bottom: 1px solid #e5e2da;
}

p {
    margin: 0 0 0.8em 0;
    text-indent: 0;
}

.equation-box {
    background-color: #f4f1ea;
    border-left: 3px solid #92400e;
    padding: 10px 16px;
    margin: 1.2em 0;
    font-family: "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.95em;
}

.code-box {
    background-color: #ece8df;
    padding: 12px;
    margin: 1em 0;
    font-family: "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.9em;
    overflow-x: auto;
}

nav#toc ol {
    list-style-type: none;
    padding-left: 0;
}

nav#toc li {
    margin: 0.8em 0;
}
"""

def parse_markdown_to_chapters(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = content.split("\n---\n")
    chapters = []

    for idx, sec in enumerate(sections):
        sec = sec.strip()
        if not sec:
            continue

        if idx == 0 and sec.startswith("# "):
            continue

        lines = sec.split("\n")
        label = ""
        title = ""
        subtitle = ""
        body_start = 0

        for i, l in enumerate(lines):
            l_str = l.strip()
            if l_str.startswith("### "):
                label = l_str.replace("### ", "").strip()
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("# "):
                    title = lines[i + 1].strip().replace("# ", "").strip()
                if i + 2 < len(lines) and lines[i + 2].strip().startswith("## "):
                    subtitle = lines[i + 2].strip().replace("## ", "").strip()
                body_start = i + 3
                break

        body_raw = "\n".join(lines[body_start:]).strip()
        chapters.append({
            "idx": idx,
            "label": label or (f"Chapter {idx}"),
            "title": title or "Untitled",
            "subtitle": subtitle or "",
            "body": body_raw
        })

    return chapters

def format_body_to_html(raw_body):
    paras = raw_body.split("\n\n")
    html_parts = []

    for p in paras:
        p = p.strip()
        if not p:
            continue

        if p.startswith("```"):
            code = p.strip("` \n")
            html_parts.append(f'<div class="code-box"><pre><code>{html.escape(code)}</code></pre></div>')
            continue

        if p.startswith("* ") or p.startswith("- "):
            items = [l.strip()[2:] for l in p.split("\n") if l.strip().startswith(("* ", "- "))]
            items_html = "".join(f"<li>{format_inline(it)}</li>" for it in items)
            html_parts.append(f"<ul>{items_html}</ul>")
            continue

        if len(p) < 90 and (" = " in p or " ∝ " in p or "∑" in p or "Π(" in p):
            html_parts.append(f'<div class="equation-box">{html.escape(p)}</div>')
            continue

        html_parts.append(f"<p>{format_inline(p)}</p>")

    return "\n".join(html_parts)

def format_inline(text):
    s = html.escape(text)
    s = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.*?)\*", r"<em>\1</em>", s)
    return s

def build_epub(book_config):
    md_path = os.path.join(BASE_DIR, book_config["md"])
    epub_path = os.path.join(BASE_DIR, book_config["epub"])

    chapters = parse_markdown_to_chapters(md_path)
    book_uuid = str(uuid.uuid4())

    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. mimetype (stored, uncompressed)
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # 2. META-INF/container.xml
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
        zf.writestr("META-INF/container.xml", container_xml)

        # 3. OEBPS/style.css
        zf.writestr("OEBPS/style.css", EPUB_CSS)

        # 4. OEBPS/title.xhtml
        title_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>{html.escape(book_config["title"])}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
  <div style="text-align:center; padding-top:20%;">
    <div class="c-label">{html.escape(book_config["author"])}</div>
    <h1 class="book-title">{html.escape(book_config["title"])}</h1>
    <h2 class="book-subtitle">{html.escape(book_config["subtitle"])}</h2>
  </div>
</body>
</html>"""
        zf.writestr("OEBPS/title.xhtml", title_xhtml)

        # 5. Chapters XHTML
        manifest_items = [
            '<item id="style" href="style.css" media-type="text/css"/>',
            '<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>',
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
        ]
        spine_items = [
            '<itemref idref="title"/>',
            '<itemref idref="nav"/>'
        ]
        nav_points = []

        for ch in chapters:
            ch_filename = f"chapter_{ch['idx']}.xhtml"
            ch_id = f"ch_{ch['idx']}"
            manifest_items.append(f'<item id="{ch_id}" href="{ch_filename}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="{ch_id}"/>')
            nav_points.append((ch_filename, ch["label"], ch["title"], ch["subtitle"]))

            ch_body_html = format_body_to_html(ch["body"])
            ch_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>{html.escape(ch["title"])}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
  <div class="c-label">{html.escape(ch["label"])}</div>
  <h1 class="c-title">{html.escape(ch["title"])}</h1>
  <h2 class="c-subtitle">{html.escape(ch["subtitle"])}</h2>
  {ch_body_html}
</body>
</html>"""
            zf.writestr(f"OEBPS/{ch_filename}", ch_xhtml)

        # 6. OEBPS/nav.xhtml
        nav_links = "\n".join([
            f'      <li><a href="{fn}"><strong>{html.escape(lbl)}</strong>: {html.escape(tit)}</a></li>'
            for fn, lbl, tit, sub in nav_points
        ])
        nav_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>Table of Contents</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
{nav_links}
    </ol>
  </nav>
</body>
</html>"""
        zf.writestr("OEBPS/nav.xhtml", nav_xhtml)

        # 7. OEBPS/content.opf
        now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest_str = "\n    ".join(manifest_items)
        spine_str = "\n    ".join(spine_items)
        opf_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{book_config["id"]}-{book_uuid[:8]}</dc:identifier>
    <dc:title>{html.escape(book_config["title"])}</dc:title>
    <dc:creator>{html.escape(book_config["author"])}</dc:creator>
    <dc:language>en</dc:language>
    <meta property="dcterms:modified">{now_iso}</meta>
  </metadata>
  <manifest>
    {manifest_str}
  </manifest>
  <spine>
    {spine_str}
  </spine>
</package>"""
        zf.writestr("OEBPS/content.opf", opf_xml)

    print(f"Compiled EPUB: {book_config['epub']} ({os.path.getsize(epub_path):,} bytes, {len(chapters)} chapters)")

def main():
    print("=== Alexandria Press EPUB3 Compiler ===")
    for b in BOOKS_CONFIG:
        build_epub(b)
    print("All volumes built successfully.")

if __name__ == "__main__":
    main()
