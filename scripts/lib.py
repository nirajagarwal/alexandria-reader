#!/usr/bin/env python3
"""
Alexandria Press — Shared Pipeline Utilities & Path Constants (scripts/lib.py)

Provides canonical directory paths, slug-to-manuscript resolution (`books/<slug>.md`),
and `catalog.json` / `backlog.json` helpers shared by `validate_book.py`,
`compile_typst.py`, and `publish_book.py`.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR = os.path.join(BASE_DIR, "books")
DOSSIERS_DIR = os.path.join(BASE_DIR, "dossiers")
COVERS_DIR = os.path.join(BASE_DIR, "assets", "covers")
THUMBS_DIR = os.path.join(COVERS_DIR, "thumbs")
PDFS_DIR = os.path.join(BASE_DIR, "assets", "pdfs")

CATALOG_PATH = os.path.join(BASE_DIR, "catalog.json")
BACKLOG_PATH = os.path.join(BASE_DIR, "backlog.json")
BOOKS_JS_PATH = os.path.join(BASE_DIR, "js", "books-data.js")
INDEX_HTML_PATH = os.path.join(BASE_DIR, "index.html")
SITEMAP_PATH = os.path.join(BASE_DIR, "sitemap.xml")

LEGACY_SLUGS = {
    "non-linear-engines",
    "latent-fragility",
    "singular-minds",
    "radical-subtraction",
    "elemental-asymmetries",
    "liminal-thresholds",
    "autonomous-engine",
    "affective-topologies",
    "architectures-of-choice",
    "tales-of-audacity",
    "architectures-of-the-grid",
    "sensory-worlds",
    "instruments-of-precision",
    "ghosts-in-the-parchment",
    "fictions-of-order",
    "bonds-of-enmity",
}


def normalize_slug(slug_or_path: str) -> str:
    """Convert any slug, filename, or path into a canonical hyphenated slug."""
    base = os.path.basename(slug_or_path.strip())
    if base.endswith(".md") or base.endswith(".json"):
        base = os.path.splitext(base)[0]
    return base.lower().replace("_", "-")


def resolve_book_md(slug_or_path: str) -> tuple[str, str]:
    """
    Resolve a book slug (`the-cell`), legacy filename (`the_cell.md`), or path (`books/the-cell.md`)
    to `(slug, absolute_md_path)`.
    """
    slug = normalize_slug(slug_or_path)
    canonical_path = os.path.join(BOOKS_DIR, f"{slug}.md")
    if os.path.exists(canonical_path):
        return slug, canonical_path

    # Check if the caller passed an explicit path that exists
    if os.path.exists(slug_or_path):
        return slug, os.path.abspath(slug_or_path)

    rel_candidate = os.path.join(BASE_DIR, slug_or_path)
    if os.path.exists(rel_candidate):
        return slug, os.path.abspath(rel_candidate)

    # Default to canonical books/<slug>.md path
    return slug, canonical_path


def load_catalog() -> dict:
    """Load the canonical book catalog from `catalog.json` as an ordered `{slug: entry}` dict."""
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and isinstance(raw.get("books"), list):
            return {item["slug"]: item for item in raw["books"] if "slug" in item}
        return raw
    return {}


def save_catalog(catalog: dict) -> None:
    """Save the canonical book catalog to `catalog.json` in `{version, updated_at, books: [...]}` format."""
    import datetime

    books_list = list(catalog.values()) if isinstance(catalog, dict) else list(catalog)
    payload = {
        "version": 1,
        "updated_at": datetime.date.today().isoformat(),
        "books": books_list,
    }
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_backlog() -> dict:
    """Load `backlog.json` if present."""
    if os.path.exists(BACKLOG_PATH):
        with open(BACKLOG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_backlog(backlog: dict) -> None:
    """Save `backlog.json`."""
    with open(BACKLOG_PATH, "w", encoding="utf-8") as f:
        json.dump(backlog, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_books_js_from_catalog(catalog: dict) -> None:
    """Regenerate `js/books-data.js` UMD bundle deterministically from `catalog.json`."""
    js_payload = {}
    for slug, entry in catalog.items():
        js_payload[slug] = {
            "title": entry["title"],
            "subtitle": entry["subtitle"],
            "category": entry.get("category", "Systems & Science"),
            "pdf": entry.get("pdf", f"assets/pdfs/{slug}.pdf"),
            "compactPdf": entry.get("compactPdf", f"assets/pdfs/{slug}-compact.pdf"),
            "mobilePdf": entry.get("mobilePdf", f"assets/pdfs/{slug}-mobile.pdf"),
            "sectionPages": entry.get("sectionPages", []),
            "compactSectionPages": entry.get("compactSectionPages", []),
            "mobileSectionPages": entry.get("mobileSectionPages", []),
            "chapters": entry.get("chapters", []),
        }

    js_content = (
        "// Alexandria Press — Universal Book Metadata Bundle (Generated from catalog.json)\n"
        "(function (root, factory) {\n"
        "  if (typeof module === 'object' && module.exports) {\n"
        "    module.exports = factory();\n"
        "  } else {\n"
        "    root.EMBEDDED_BOOKS = factory();\n"
        "  }\n"
        "}(typeof self !== 'undefined' ? self : this, function () {\n"
        "  return " + json.dumps(js_payload, indent=2, ensure_ascii=False) + ";\n"
        "}));\n"
    )
    with open(BOOKS_JS_PATH, "w", encoding="utf-8") as f:
        f.write(js_content)


def extract_book_metadata(md_text: str) -> tuple[str, str, list[dict]]:
    """Extract `(title, subtitle, chapters)` from an Alexandria Press markdown manuscript."""
    secs = [s.strip() for s in md_text.split("\n---\n") if s.strip()]
    first_lines = [l.strip() for l in secs[0].splitlines() if l.strip()] if secs else []
    title = first_lines[0].lstrip("#").strip() if first_lines else "Untitled Volume"
    subtitle = first_lines[1].lstrip("#").strip() if len(first_lines) > 1 else ""
    chapters = []
    for idx, sec in enumerate(secs[1:]):
        headers = []
        for l in sec.splitlines():
            if l.strip().startswith("#"):
                headers.append(l.strip().lstrip("#").strip())
                if len(headers) == 3:
                    break
        while len(headers) < 3:
            headers.append("")
        chapters.append(
            {
                "label": headers[0] or ("Introduction" if idx == 0 else f"Chapter {idx}"),
                "title": headers[1] or "Untitled",
                "subtitle": headers[2] or "",
            }
        )
    return title, subtitle, chapters
