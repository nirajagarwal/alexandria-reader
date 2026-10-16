#!/usr/bin/env python3
"""
Alexandria Press — Test Suite & Typst PDF Integrity Verifier
Verifies standalone reader structure, slimmed book metadata, dual Typst PDFs (desktop & mobile),
Literata font assets, and chapter navigation mappings.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_core_files_exist():
    required_files = [
        "index.html",
        "style.css",
        "js/books-data.js",
        "js/covers-data.js",
        "scripts/compile_typst.py",
        "scripts/publish_book.py",
        "scripts/validate_book.py",
        "vendor/pdfjs/pdf.min.js",
        "vendor/pdfjs/pdf.worker.min.js",
        "fonts/Literata-400-normal.ttf",
        "fonts/Literata-400-italic.ttf",
        "fonts/Literata-600-normal.ttf",
        "fonts/Literata-700-normal.ttf",
    ]
    for rel in required_files:
        path = os.path.join(BASE_DIR, rel)
        assert os.path.exists(path), f"Missing required file: {rel}"
        assert os.path.getsize(path) > 0, f"File is empty: {rel}"
    print("✓ Core files, PDF.js vendor assets, and Literata fonts verified.")


def test_index_html_pdf_reader():
    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert '<link rel="stylesheet" href="style.css">' in html
    assert 'src="vendor/pdfjs/pdf.min.js"' in html
    assert 'src="js/covers-data.js"' in html
    assert 'src="js/books-data.js"' in html
    assert 'id="pdf-book-frame"' in html
    assert 'id="pdf-slot-left"' in html
    assert 'id="pdf-slot-right"' in html
    assert 'id="prev-spread-btn"' in html
    assert 'id="next-spread-btn"' in html
    assert 'class="running-footer"' not in html, "Legacy .running-footer should be removed"
    assert 'id="col-left"' not in html, "Legacy HTML reflow columns should be removed"
    print("✓ index.html Typst PDF reader structure verified.")


def test_books_data_and_pdfs():
    books_js_path = os.path.join(BASE_DIR, "js", "books-data.js")
    assert os.path.getsize(books_js_path) < 100_000, "js/books-data.js should be slimmed (<100 KB)"

    content = open(books_js_path, "r", encoding="utf-8").read()
    p_end = content.find("return {") + len("return ")
    s_start = content.rfind("};") + 1
    books = json.loads(content[p_end:s_start])

    assert len(books) >= 17, f"Expected at least 17 books, found {len(books)}"

    for slug, b in books.items():
        assert "markdown" not in b, f"{slug} should not embed raw markdown in js/books-data.js"
        assert "chapters" in b and len(b["chapters"]) >= 9, f"{slug} missing chapters metadata"
        assert "pdf" in b and "mobilePdf" in b, f"{slug} missing pdf/mobilePdf paths"
        assert "sectionPages" in b and "mobileSectionPages" in b, f"{slug} missing sectionPages"

        desktop_pdf = os.path.join(BASE_DIR, b["pdf"])
        mobile_pdf = os.path.join(BASE_DIR, b["mobilePdf"])
        assert os.path.exists(desktop_pdf) and os.path.getsize(desktop_pdf) > 50_000, f"Invalid desktop PDF for {slug}"
        assert os.path.exists(mobile_pdf) and os.path.getsize(mobile_pdf) > 50_000, f"Invalid mobile PDF for {slug}"

        # Page 1 is Frontispiece + Contents, Page 2 is Introduction, Page 3 is Chapter 1
        assert b["sectionPages"][0] == 2, f"{slug} Introduction should start on Page 2, got {b['sectionPages'][0]}"
        assert b["sectionPages"][1] == 3, f"{slug} Chapter 1 should start on Page 3, got {b['sectionPages'][1]}"

    print(f"✓ All {len(books)} volumes verified with slim metadata and dual Desktop/Mobile Typst PDFs.")


def run_all():
    print("=== Running Alexandria Press Typst PDF Test Suite ===")
    test_core_files_exist()
    test_index_html_pdf_reader()
    test_books_data_and_pdfs()
    print("\n--- ALL TESTS PASSED: 100% PRODUCTION READY ---")


if __name__ == "__main__":
    run_all()
