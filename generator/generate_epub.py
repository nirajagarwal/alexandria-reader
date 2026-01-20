#!/usr/bin/env python3
"""
EPUB Generator for Alexandria Press
Converts book.json files to EPUB 3.0 format
"""

import json
import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime
import markdown
import uuid

def generate_epub(book_id: str):
    """Generate EPUB file from book.json"""
    
    # Paths
    base_dir = Path(__file__).parent.parent
    book_dir = base_dir / "outputs" / book_id
    json_path = book_dir / "book.json"
    cover_path = book_dir / "cover.png"
    epub_path = book_dir / "book.epub"
    
    # Load book data
    if not json_path.exists():
        print(f"Error: {json_path} not found")
        sys.exit(1)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        book = json.load(f)
    
    # Create EPUB structure
    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
        # 1. mimetype (must be first, uncompressed)
        epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        
        # 2. META-INF/container.xml
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        epub.writestr('META-INF/container.xml', container_xml)
        
        # 3. Cover image
        if cover_path.exists():
            with open(cover_path, 'rb') as f:
                epub.writestr('OEBPS/images/cover.png', f.read())
        
        # 4. Stylesheet
        css = generate_css()
        epub.writestr('OEBPS/styles.css', css)
        
        # 5. Cover page
        cover_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Cover</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body class="cover">
    <div class="cover-image">
        <img src="images/cover.png" alt="Cover"/>
    </div>
</body>
</html>'''
        epub.writestr('OEBPS/cover.xhtml', cover_html)
        
        # 6. Title page
        title_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{book['title']}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="title-page">
        <h1 class="book-title">{book['title']}</h1>
        <p class="book-descriptor">{book.get('descriptor', '')}</p>
        <p class="publisher">Alexandria Press</p>
    </div>
</body>
</html>'''
        epub.writestr('OEBPS/title.xhtml', title_html)
        
        # 7. Introduction (if exists)
        if book.get('introduction'):
            intro_html = generate_chapter_html(
                title="Introduction",
                content=book['introduction'],
                chapter_num=0
            )
            epub.writestr('OEBPS/introduction.xhtml', intro_html)
        
        # 8. Chapters (entries)
        entries = book.get('entries', [])
        for idx, entry in enumerate(entries, 1):
            chapter_html = generate_chapter_html(
                title=entry['name'],
                content=entry.get('content', ''),
                chapter_num=idx,
                section=entry.get('section')
            )
            epub.writestr(f'OEBPS/chapter-{idx:03d}.xhtml', chapter_html)
        
        # 9. Navigation Document (EPUB 3)
        nav_html = generate_nav(book, entries)
        epub.writestr('OEBPS/nav.xhtml', nav_html)
        
        # 10. NCX (EPUB 2 backwards compatibility)
        ncx = generate_ncx(book, entries)
        epub.writestr('OEBPS/toc.ncx', ncx)
        
        # 11. OPF Package Document
        opf = generate_opf(book, entries, has_cover=cover_path.exists())
        epub.writestr('OEBPS/content.opf', opf)
    
    print(f"✓ Generated: {epub_path}")
    print(f"  Entries: {len(entries)}")
    print(f"  Size: {epub_path.stat().st_size / 1024:.1f} KB")

def generate_css():
    """Generate EPUB stylesheet"""
    return '''
/* Alexandria Press EPUB Styles */

body {
    font-family: "Crimson Pro", "Crimson Text", Georgia, serif;
    line-height: 1.6;
    color: #2d1810;
    margin: 2em;
    text-align: justify;
    hyphens: auto;
}

h1, h2, h3 {
    font-family: "IBM Plex Sans", "Helvetica Neue", sans-serif;
    color: #2d1810;
    page-break-after: avoid;
    hyphens: none;
}

h1 {
    font-size: 2em;
    margin: 1.5em 0 0.5em 0;
    font-weight: 600;
    page-break-before: always;
}

h2 {
    font-size: 1.3em;
    margin: 1.2em 0 0.4em 0;
    font-weight: 500;
}

p {
    margin: 0;
    text-indent: 1.5em;
    orphans: 2;
    widows: 2;
}

p:first-of-type,
h1 + p,
h2 + p,
h3 + p {
    text-indent: 0;
}

/* Cover */
.cover {
    margin: 0;
    padding: 0;
    text-align: center;
}

.cover-image {
    width: 100%;
    height: 100%;
}

.cover-image img {
    width: 100%;
    height: auto;
}

/* Title Page */
.title-page {
    text-align: center;
    margin-top: 30%;
}

.book-title {
    font-size: 3em;
    font-weight: 700;
    margin-bottom: 0.3em;
}

.book-descriptor {
    font-size: 1.2em;
    font-style: italic;
    margin-bottom: 2em;
    text-indent: 0;
}

.publisher {
    font-size: 0.9em;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 3em;
    text-indent: 0;
}

/* Section Headers */
.section-label {
    font-family: "IBM Plex Sans", sans-serif;
    font-size: 0.9em;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #8b7355;
    margin-bottom: 0.5em;
    text-indent: 0;
}

/* Navigation */
nav ol {
    list-style-type: none;
    padding-left: 0;
}

nav li {
    margin: 0.5em 0;
}

nav a {
    color: #2d1810;
    text-decoration: none;
}
'''

def generate_chapter_html(title: str, content: str, chapter_num: int, section: str = None):
    """Generate XHTML for a chapter"""
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra', 'smarty'])
    html_content = md.convert(content)
    
    # EPUB/XHTML Fix: Standard HTML entities like &rsquo; are not valid in XML
    # We replace them with numeric entities or UTF-8 equivalents.
    replacements = {
        '&rsquo;': '&#8217;',
        '&lsquo;': '&#8216;',
        '&rdquo;': '&#8221;',
        '&ldquo;': '&#8220;',
        '&ndash;': '&#8211;',
        '&mdash;': '&#8212;',
        '&hellip;': '&#8230;',
        '&nbsp;': '&#160;',
        '&copy;': '&#169;',
        '&reg;': '&#174;',
    }
    for search, replace in replacements.items():
        html_content = html_content.replace(search, replace)
    
    # Remove the H1 from content if it duplicates the title
    if html_content.startswith(f'<h1>{title}</h1>'):
        html_content = html_content[len(f'<h1>{title}</h1>'):]
    
    section_html = f'<p class="section-label">{section}</p>' if section else ''
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    {section_html}
    <h1>{title}</h1>
    {html_content}
</body>
</html>'''

def generate_nav(book, entries):
    """Generate EPUB 3 Navigation Document"""
    
    # Build TOC
    toc_items = []
    
    # Introduction
    if book.get('introduction'):
        toc_items.append('<li><a href="introduction.xhtml">Introduction</a></li>')
    
    # Entries
    for idx, entry in enumerate(entries, 1):
        toc_items.append(f'<li><a href="chapter-{idx:03d}.xhtml">{entry["name"]}</a></li>')
    
    nav_content = '\n'.join(toc_items)
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Table of Contents</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>Contents</h1>
        <ol>
            {nav_content}
        </ol>
    </nav>
</body>
</html>'''

def generate_ncx(book, entries):
    """Generate NCX for EPUB 2 compatibility"""
    
    nav_points = []
    play_order = 1
    
    # Introduction
    if book.get('introduction'):
        nav_points.append(f'''
    <navPoint id="intro" playOrder="{play_order}">
        <navLabel><text>Introduction</text></navLabel>
        <content src="introduction.xhtml"/>
    </navPoint>''')
        play_order += 1
    
    # Entries
    for idx, entry in enumerate(entries, 1):
        nav_points.append(f'''
    <navPoint id="chapter-{idx}" playOrder="{play_order}">
        <navLabel><text>{entry["name"]}</text></navLabel>
        <content src="chapter-{idx:03d}.xhtml"/>
    </navPoint>''')
        play_order += 1
    
    nav_content = '\n'.join(nav_points)
    
    book_uid = str(uuid.uuid4())
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="{book_uid}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>{book['title']}</text>
    </docTitle>
    <navMap>
        {nav_content}
    </navMap>
</ncx>'''

def generate_opf(book, entries, has_cover=False):
    """Generate OPF Package Document"""
    
    # Manifest items
    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="css" href="styles.css" media-type="text/css"/>',
        '<item id="cover-page" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="title-page" href="title.xhtml" media-type="application/xhtml+xml"/>',
    ]
    
    if has_cover:
        manifest_items.append('<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>')
    
    if book.get('introduction'):
        manifest_items.append('<item id="intro" href="introduction.xhtml" media-type="application/xhtml+xml"/>')
    
    for idx in range(1, len(entries) + 1):
        manifest_items.append(f'<item id="chapter-{idx}" href="chapter-{idx:03d}.xhtml" media-type="application/xhtml+xml"/>')
    
    manifest_content = '\n        '.join(manifest_items)
    
    # Spine items
    spine_items = [
        '<itemref idref="cover-page"/>',
        '<itemref idref="title-page"/>',
    ]
    
    if book.get('introduction'):
        spine_items.append('<itemref idref="intro"/>')
    
    for idx in range(1, len(entries) + 1):
        spine_items.append(f'<itemref idref="chapter-{idx}"/>')
    
    spine_content = '\n        '.join(spine_items)
    
    book_uid = str(uuid.uuid4())
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="book-id">{book_uid}</dc:identifier>
        <dc:title>{book['title']}</dc:title>
        <dc:language>en</dc:language>
        <dc:creator>Alexandria Press (AI)</dc:creator>
        <dc:publisher>Alexandria Press</dc:publisher>
        <dc:date>{timestamp}</dc:date>
        <dc:description>{book.get('descriptor', '')}</dc:description>
        <meta property="dcterms:modified">{timestamp}</meta>
    </metadata>
    <manifest>
        {manifest_content}
    </manifest>
    <spine toc="ncx">
        {spine_content}
    </spine>
</package>'''

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python generate_epub.py <book_id>")
        sys.exit(1)
    
    generate_epub(sys.argv[1])
