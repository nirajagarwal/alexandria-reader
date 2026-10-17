#!/usr/bin/env python3
"""
Alexandria Press — Shared Pipeline Utilities & Path Constants (scripts/lib.py)

Provides canonical directory paths, slug-to-manuscript resolution (`books/<slug>.md`),
and `catalog.json` / `backlog.json` helpers shared by `validate_book.py`,
`compile_typst.py`, and `publish_book.py`.
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR = os.path.join(BASE_DIR, "books")
DOSSIERS_DIR = os.path.join(BASE_DIR, "dossiers")
COVERS_DIR = os.path.join(BASE_DIR, "assets", "covers")
THUMBS_DIR = os.path.join(COVERS_DIR, "thumbs")
OG_DIR = os.path.join(BASE_DIR, "assets", "og")
PDFS_DIR = os.path.join(BASE_DIR, "assets", "pdfs")
READ_HTML_DIR = os.path.join(BASE_DIR, "read")

CATALOG_PATH = os.path.join(BASE_DIR, "catalog.json")
BACKLOG_PATH = os.path.join(BASE_DIR, "backlog.json")
BOOKS_JS_PATH = os.path.join(BASE_DIR, "js", "books-data.js")
INDEX_HTML_PATH = os.path.join(BASE_DIR, "index.html")
SITEMAP_PATH = os.path.join(BASE_DIR, "sitemap.xml")

LEGACY_SLUGS = {
    "non-linear-engines",
    "latent-fragility",
    "singular-minds",
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

BIOGRAPHY_SLUGS = {
    "flights-and-perches",
    "curious-physicist",
    "claude-shannon",
    "alan-turing",
}


def slugify_text(text: str) -> str:
    """Convert a heading or title string into a clean URL slug."""
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "section"


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

    if os.path.exists(slug_or_path):
        return slug, os.path.abspath(slug_or_path)

    rel_candidate = os.path.join(BASE_DIR, slug_or_path)
    if os.path.exists(rel_candidate):
        return slug, os.path.abspath(rel_candidate)

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


def infer_book_format(slug: str, mode: str) -> str:
    """Return canonical catalog filter format (`mechanisms` | `landscape` | `highlights` | `biography`)."""
    if slug in BIOGRAPHY_SLUGS:
        return "biography"
    if mode == "landscape":
        return "landscape"
    if mode == "listicle":
        return "highlights"
    return "mechanisms"


def write_books_js_from_catalog(catalog: dict) -> None:
    """Regenerate `js/books-data.js` UMD bundle deterministically from `catalog.json`."""
    js_payload = {}
    for slug, entry in catalog.items():
        mode = entry.get("mode", "facet")
        fmt = entry.get("format") or infer_book_format(slug, mode)
        js_payload[slug] = {
            "title": entry["title"],
            "subtitle": entry["subtitle"],
            "category": entry.get("category", "Systems & Science"),
            "mode": mode,
            "format": fmt,
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


def extract_book_metadata(md_text: str, dossier: dict | None = None) -> tuple[str, str, list[dict]]:
    """Extract `(title, subtitle, chapters)` with provenance metadata from manuscript + dossier."""
    secs = [s.strip() for s in md_text.split("\n---\n") if s.strip()]
    first_lines = [l.strip() for l in secs[0].splitlines() if l.strip()] if secs else []
    title = first_lines[0].lstrip("#").strip() if first_lines else "Untitled Volume"
    subtitle = first_lines[1].lstrip("#").strip() if len(first_lines) > 1 else ""
    dossier_chapters = (dossier or {}).get("chapters", []) if isinstance(dossier, dict) else []
    book_mode = (dossier or {}).get("mode", "facet") if isinstance(dossier, dict) else "facet"

    chapters = []
    for idx, sec in enumerate(secs[1:]):
        lines = sec.splitlines()
        headers = []
        body_start = 0
        for line_i, l in enumerate(lines):
            if l.strip().startswith("#"):
                headers.append(l.strip().lstrip("#").strip())
                if len(headers) == 3:
                    body_start = line_i + 1
                    break
        while len(headers) < 3:
            headers.append("")

        label_str = headers[0] or ("Introduction" if idx == 0 else f"Chapter {idx}")
        title_str = headers[1] or "Untitled"
        sub_str = headers[2] or ""
        body_raw = "\n".join(lines[body_start:]).strip()

        if idx == 0:
            ch_slug = "introduction"
            clean_b = re.sub(r"\s+", " ", body_raw).strip()
            sents = re.split(r"(?<=[.!?])\s+", clean_b)
            anchor = " ".join(sents[:2]).strip() if sents else ""
            exit_fact = sents[-1].strip() if len(sents) > 2 else ""
            formalism_mode = "introduction"
        else:
            ch_slug = slugify_text(title_str)
            d_ch = dossier_chapters[idx - 1] if (idx - 1) < len(dossier_chapters) else {}
            if "```svg" in body_raw.lower() or "```diagram" in body_raw.lower():
                formalism_mode = "diagram"
            elif "$$" in body_raw:
                formalism_mode = "equation"
            elif book_mode == "listicle" or "· · ·" in body_raw or "❦" in body_raw:
                formalism_mode = "highlights"
            else:
                formalism_mode = d_ch.get("formalism_mode") or "ledger_or_list"

            clean_b = re.sub(r"```(?:svg|diagram)[\s\S]*?```", "", body_raw, flags=re.IGNORECASE)
            clean_b = re.sub(r"\$\$[\s\S]*?\$\$", "", clean_b)
            paras = [
                pr.strip()
                for pr in re.split(r"\n\s*\n", clean_b)
                if pr.strip() and not pr.strip().startswith(("· · ·", "❦", "- ", "* ", "1. "))
            ]
            anchor = d_ch.get("historical_anchor", "").strip()
            if not anchor and paras:
                first_p = re.sub(r"\s+", " ", paras[0])
                sents = re.split(r"(?<=[.!?])\s+", first_p)
                anchor = " ".join(sents[:2]).strip()

            exit_fact = d_ch.get("exit_fact", "").strip()
            if not exit_fact and paras:
                last_p = re.sub(r"\s+", " ", paras[-1])
                sents = re.split(r"(?<=[.!?])\s+", last_p)
                exit_fact = sents[-1].strip() if sents else last_p

        chapters.append(
            {
                "label": label_str,
                "title": title_str,
                "subtitle": sub_str,
                "slug": ch_slug,
                "formalismMode": formalism_mode,
                "anchor": anchor,
                "exitFact": exit_fact,
            }
        )
    return title, subtitle, chapters
