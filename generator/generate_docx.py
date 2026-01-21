#!/usr/bin/env python3
"""
DOCX Generator for Alexandria Press
Converts book.json files to Word DOCX format for Kindle Create
"""

import json
import sys
import re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

def generate_docx(book_id: str):
    """Generate DOCX file from book.json"""
    
    # Paths
    base_dir = Path(__file__).parent.parent
    book_dir = base_dir / "outputs" / book_id
    json_path = book_dir / "book.json"
    docx_path = book_dir / "book.docx"
    
    # Load book data
    if not json_path.exists():
        print(f"Error: {json_path} not found")
        sys.exit(1)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        book = json.load(f)
    
    # Create Document
    doc = Document()
    
    # --- Styles Setup ---
    # We rely on default styles but could customize here
    # doc.styles['Normal'].font.name = 'Times New Roman'
    # doc.styles['Normal'].font.size = Pt(12)
    
    # --- Title Page ---
    doc.add_paragraph("\n\n\n\n")  # Spacing
    
    title = doc.add_paragraph(book['title'])
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.style = 'Title'
    
    if book.get('descriptor'):
        desc = doc.add_paragraph(book['descriptor'])
        desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
        desc.style = 'Subtitle'
        
    doc.add_paragraph("\n\n")
    pub = doc.add_paragraph("Alexandria Press")
    pub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_page_break()
    
    # --- Introduction ---
    if book.get('introduction'):
        doc.add_heading('Introduction', level=1)
        add_markdown_content(doc, book['introduction'])
        doc.add_page_break()
        
    # --- Entries (Chapters) ---
    entries = book.get('entries', [])
    for i, entry in enumerate(entries):
        # Kindle Create uses Heading 1 for Chapter detection
        doc.add_heading(entry['name'], level=1)
        
        content = entry.get('content', '')
        if content:
            add_markdown_content(doc, content)
            
        # Add page break after every chapter except the last one
        if i < len(entries) - 1:
            doc.add_page_break()
            
    # Save
    doc.save(docx_path)
    print(f"✓ Generated: {docx_path}")
    print(f"  Entries: {len(entries)}")
    print(f"  Size: {docx_path.stat().st_size / 1024:.1f} KB")

def add_markdown_content(doc, content: str):
    """
    Simple Markdown to Docx parser.
    Handles:
    - Paragraphs
    - **Bold**
    - *Italics*
    - Headers (#, ##, etc)
    """
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Headers
        if line.startswith('#'):
            level = len(line.split(' ')[0])
            text = line.lstrip('#').strip()
            # Map Markdown H1-H6 to Docx Heading 2-7 (since H1 is Chapter Title)
            # Actually, standard is usually H2 for sub-sections
            doc.add_heading(text, level=min(level + 1, 9))
            continue
            
        # Normal Paragraph
        p = doc.add_paragraph()
        
        # Simple Bold/Italic parsing
        # This is a naive regex parser, good enough for simple text
        # Splitting by tokens to handle mixed formatting
        
        # Regex for bold (**text**) and italic (*text*)
        # We process bold first, then chunks
        # A more robust way requires a proper tokenizer, but let's try a simple approach:
        # iterate chars or use split.
        
        # Let's just add text for now to ensure content is there.
        # Enhancing formatting is a "nice to have".
        
        format_and_add_run(p, line)

def format_and_add_run(paragraph, text):
    """
    Parses **bold** and *italic* and adds runs to paragraph.
    Ordering: Bold then Italic.
    """
    # Pattern to split by bold: **...**
    parts = re.split(r'(\*\*.*?\*\*)', text)
    
    for part in parts:
        is_bold = part.startswith('**') and part.endswith('**')
        clean_part = part[2:-2] if is_bold else part
        
        if not clean_part:
            continue
            
        # Now split by italic: *...*
        sub_parts = re.split(r'(\*.*?\*)', clean_part)
        
        for sub in sub_parts:
            is_italic = sub.startswith('*') and sub.endswith('*')
            final_text = sub[1:-1] if is_italic else sub
            
            if not final_text:
                continue
                
            run = paragraph.add_run(final_text)
            if is_bold:
                run.bold = True
            if is_italic:
                run.italic = True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_docx.py <book_id>")
        sys.exit(1)
    
    generate_docx(sys.argv[1])
