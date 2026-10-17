#!/usr/bin/env python3
"""
Alexandria Press — Test Suite & Typst PDF Integrity Verifier (tests/test_reader.py)

Verifies:
1. Repository layout hygiene (no root book `.md` files, retired `js/covers-data.js` removed).
2. Core application files (`index.html`, `style.css`, `catalog.json`, `backlog.json`, `js/app.js`,
   `js/books-data.js`, `scripts/lib.py`, `scripts/validate_book.py`, `scripts/compile_typst.py`,
   `scripts/publish_book.py`, PDF.js vendor assets, and Literata fonts).
3. `index.html` marker blocks (`<!-- BEGIN:JSON_LD -->`, `<!-- BEGIN:CATALOG_GRID -->`), external
   `js/app.js` integration, and 1:1 parity with `catalog.json`.
4. All 34+ volumes across `catalog.json`, `books/<slug>.md`, `dossiers/<slug>.json`,
   `assets/covers/<slug>.svg`, `assets/covers/thumbs/<slug>.svg`, and all 3 Typst PDF editions
   (Desktop, Compact, and Mobile).
"""

import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
from create_book_pipeline import verify_prompt_lock  # noqa: E402
from lib import load_catalog  # noqa: E402

ALLOWED_ROOT_MDS = {
    "alexandria_manifesto.md",
    "GENERATION_GUIDELINES.md",
    "BACKLOG.md",
    "README.md",
    "AGENTS.md",
}


def test_repo_layout_and_core_files():
    required_files = [
        "index.html",
        "style.css",
        "catalog.json",
        "backlog.json",
        "prompt-lock.json",
        "AGENTS.md",
        "js/app.js",
        "js/books-data.js",
        "scripts/lib.py",
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

    verify_prompt_lock()

    # Verify redundant js/covers-data.js and dossiers/topic_queue.json are removed
    assert not os.path.exists(os.path.join(BASE_DIR, "js", "covers-data.js")), (
        "Redundant js/covers-data.js should be removed"
    )
    assert not os.path.exists(os.path.join(BASE_DIR, "dossiers", "topic_queue.json")), (
        "Obsolete dossiers/topic_queue.json should be removed"
    )

    # Verify no book manuscripts remain in the repository root
    root_mds = [f for f in os.listdir(BASE_DIR) if f.endswith(".md")]
    stray_mds = [f for f in root_mds if f not in ALLOWED_ROOT_MDS]
    assert not stray_mds, f"Found stray book markdown files in repo root (must live in books/): {stray_mds}"
    print("✓ Repo layout hygiene, core scripts, prompt-lock.json, PDF.js vendor assets, and Literata fonts verified.")


def test_index_html_and_markers():
    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html_text = f.read()

    assert 'href="style.css' in html_text
    assert 'src="vendor/pdfjs/pdf.min.js"' in html_text
    assert 'src="js/books-data.js' in html_text
    assert 'src="js/app.js' in html_text
    assert "covers-data.js" not in html_text, "index.html must not reference retired js/covers-data.js"
    assert "<!-- BEGIN:JSON_LD -->" in html_text and "<!-- END:JSON_LD -->" in html_text
    assert "<!-- BEGIN:CATALOG_GRID -->" in html_text and "<!-- END:CATALOG_GRID -->" in html_text
    assert 'id="pdf-book-frame"' in html_text
    assert 'id="pdf-slot-left"' in html_text
    assert 'id="pdf-slot-right"' in html_text
    assert 'id="edge-zone-prev"' in html_text
    assert 'id="edge-zone-next"' in html_text
    assert 'id="prev-spread-btn"' in html_text
    assert 'id="next-spread-btn"' in html_text
    assert 'id="sources-modal"' in html_text
    assert 'class="home-tagline"' in html_text
    assert 'Deep Learning for Humans. Distilled by Frontier AI.' in html_text
    assert 'id="catalog-filters"' not in html_text, "Filter pills bar should be removed"
    assert 'id="library-modal"' not in html_text, "Redundant #library-modal should be removed"
    assert 'class="running-footer"' not in html_text, "Legacy .running-footer should be removed"
    assert 'id="col-left"' not in html_text, "Legacy HTML reflow columns should be removed"

    catalog = load_catalog()
    card_keys = re.findall(r'class="book-card"[^>]*data-key="([^"]+)"', html_text)
    assert card_keys == list(catalog.keys()), (
        f"Catalog cards in index.html ({len(card_keys)}) do not match catalog.json order ({len(catalog)})"
    )
    print(f"✓ index.html structure, external js/app.js, and {len(card_keys)} catalog cards verified.")


def test_catalog_dossiers_and_pdfs():
    catalog = load_catalog()
    books_js_path = os.path.join(BASE_DIR, "js", "books-data.js")
    assert os.path.getsize(books_js_path) < 500_000, "js/books-data.js should remain slim (<500 KB with provenance)"

    content = open(books_js_path, "r", encoding="utf-8").read()
    p_end = content.find("return {") + len("return ")
    s_start = content.rfind("};") + 1
    books = json.loads(content[p_end:s_start])

    assert len(catalog) >= 34, f"Expected at least 34 books in catalog.json, found {len(catalog)}"
    assert list(books.keys()) == list(catalog.keys()), "js/books-data.js keys must match catalog.json keys"

    for slug, entry in catalog.items():
        b = books[slug]
        assert not b.get("title", "").lower().startswith("twelve "), (
            f"{slug} title must not start with 'Twelve ': {b.get('title')}"
        )
        assert not slug.startswith("twelve-"), (
            f"Book slug must not start with 'twelve-': {slug}"
        )
        assert "markdown" not in b, f"{slug} should not embed raw markdown in js/books-data.js"
        assert b.get("format") in ("mechanisms", "landscape", "highlights", "biography"), (
            f"{slug} missing valid format in js/books-data.js: {b.get('format')}"
        )
        assert len(b.get("chapters", [])) == 13, (
            f"{slug} must have 13 sections (Introduction + 12 Chapters), found {len(b.get('chapters', []))}"
        )

        # Verify static crawlable book & chapter HTML pages exist
        book_read_index = os.path.join(BASE_DIR, "read", slug, "index.html")
        assert os.path.exists(book_read_index), f"Missing crawlable book index: read/{slug}/index.html"
        for ch_idx, ch in enumerate(b["chapters"]):
            ch_slug = ch.get("slug")
            assert ch_slug, f"Missing chapter slug for {slug} ch_idx={ch_idx}"
            ch_html_path = os.path.join(BASE_DIR, "read", slug, f"{ch_slug}.html")
            assert os.path.exists(ch_html_path), f"Missing crawlable chapter page: read/{slug}/{ch_slug}.html"
            if ch_idx >= 1:
                assert ch.get("anchor"), f"Missing provenance anchor for {slug} ch {ch_idx}"
                assert ch.get("exitFact"), f"Missing provenance exitFact for {slug} ch {ch_idx}"

        # Verify manuscript, dossier, cover SVG, thumbnail SVG, and 1200x630 OG PNG exist
        md_path = os.path.join(BASE_DIR, "books", f"{slug}.md")
        dossier_path = os.path.join(BASE_DIR, "dossiers", f"{slug}.json")
        cover_path = os.path.join(BASE_DIR, "assets", "covers", f"{slug}.svg")
        thumb_path = os.path.join(BASE_DIR, "assets", "covers", "thumbs", f"{slug}.svg")
        og_png_path = os.path.join(BASE_DIR, "assets", "og", f"{slug}.png")
        assert os.path.exists(md_path), f"Missing manuscript: books/{slug}.md"
        assert os.path.exists(dossier_path), f"Missing dossier: dossiers/{slug}.json"
        assert os.path.exists(cover_path), f"Missing cover SVG: assets/covers/{slug}.svg"
        assert os.path.exists(thumb_path), f"Missing thumbnail SVG: assets/covers/thumbs/{slug}.svg"
        assert os.path.exists(og_png_path) and os.path.getsize(og_png_path) > 10_000, f"Missing OG PNG: assets/og/{slug}.png"

        # Verify dossier JSON parses cleanly
        dossier_data = json.load(open(dossier_path, encoding="utf-8"))
        assert dossier_data.get("slug") == slug, f"Dossier slug mismatch in dossiers/{slug}.json"

        # Verify all 3 Typst PDF editions (Desktop, Compact, Mobile)
        for pdf_key in ("pdf", "compactPdf", "mobilePdf"):
            assert pdf_key in b, f"{slug} missing {pdf_key}"
            pdf_file = os.path.join(BASE_DIR, b[pdf_key])
            assert os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 50_000, (
                f"Invalid or missing {pdf_key} for {slug}: {b[pdf_key]}"
            )

        # Physical Page 1 is Book Cover, Physical Page 2 is TOC Frontispiece, Physical Page 3 is Introduction
        for sec_key in ("sectionPages", "compactSectionPages", "mobileSectionPages"):
            assert sec_key in b and len(b[sec_key]) == 13, f"{slug} invalid {sec_key}"
            assert b[sec_key][0] == 3, f"{slug} {sec_key}[0] (Introduction) should start on Page 3, got {b[sec_key][0]}"
            assert all(b[sec_key][i] < b[sec_key][i + 1] for i in range(len(b[sec_key]) - 1)), (
                f"{slug} {sec_key} must be strictly increasing: {b[sec_key]}"
            )

    print(
        f"✓ All {len(catalog)} volumes verified across catalog.json, books/*.md, dossiers/*.json, read/<slug>/*.html, covers, thumbs, and 3-edition Typst PDFs."
    )


def run_all():
    print("=== Running Alexandria Press Typst PDF & Architecture Test Suite ===")
    test_repo_layout_and_core_files()
    test_index_html_and_markers()
    test_catalog_dossiers_and_pdfs()
    print("\n--- ALL TESTS PASSED: 100% PRODUCTION READY ---")


if __name__ == "__main__":
    run_all()
