#!/usr/bin/env python3
"""
Alexandria Press — Autonomous Book Publisher & Library Sync (scripts/publish_book.py)

Automates Stage 5 of the Alexandria Press generation pipeline:
1. Runs deterministic validation (`validate_book`) on the manuscript.
2. Generates a 1600x2400 mathematical vector SVG cover (`assets/covers/<slug>.svg`) if needed.
3. Registers or updates the book inside `js/books-data.js`.
4. Injects or updates the catalog card and JSON-LD entry inside `index.html`.
5. Updates `sitemap.xml`.
6. Can also dump all existing chapter anchors (`--list-anchors`) to prevent cross-book duplication.

Usage:
    python3 scripts/publish_book.py --list-anchors
    python3 scripts/publish_book.py --sync-all
    python3 scripts/publish_book.py --slug geometries-of-contagion --category "Epidemiology & Networks" --accent "#10b981" --bg "#061e16" --theme "network-wave"
"""

import argparse
import datetime
import html
import json
import math
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
from validate_book import validate_book  # noqa: E402

BOOKS_JS_PATH = os.path.join(BASE_DIR, "js", "books-data.js")
INDEX_HTML_PATH = os.path.join(BASE_DIR, "index.html")
SITEMAP_PATH = os.path.join(BASE_DIR, "sitemap.xml")
COVERS_DIR = os.path.join(BASE_DIR, "assets", "covers")


def load_books_data():
    text = open(BOOKS_JS_PATH, encoding="utf-8").read()
    p_end = text.find("return {") + len("return ")
    s_start = text.rfind("};") + 1
    data = json.loads(text[p_end:s_start])
    return text[:p_end], data, text[s_start:]


def save_books_data(prefix, data, suffix):
    new_js = prefix + json.dumps(data, indent=2, ensure_ascii=False) + suffix
    open(BOOKS_JS_PATH, "w", encoding="utf-8").write(new_js)


def extract_title_subtitle(md_text: str):
    lines = [l.strip() for l in md_text.splitlines() if l.strip()]
    title = lines[0].lstrip("#").strip() if lines else "Untitled Volume"
    subtitle = lines[1].lstrip("#").strip() if len(lines) > 1 else ""
    return title, subtitle


def list_existing_anchors():
    _, data, _ = load_books_data()
    print("=== EXISTING ALEXANDRIA PRESS LIBRARY ANCHORS (DO NOT DUPLICATE) ===")
    for slug, meta in data.items():
        print(f"\n[{slug}] {meta['title']} — {meta['subtitle']} ({meta['category']})")
        secs = [s.strip() for s in meta["markdown"].split("\n---\n") if s.strip()]
        for idx, sec in enumerate(secs[2:], 1):
            lines = [l.strip() for l in sec.splitlines() if l.strip()]
            if len(lines) >= 3:
                ch_title = lines[1].lstrip("#").strip()
                ch_sub = lines[2].lstrip("#").strip()
                print(f"  Ch {idx:2d}: {ch_title} — {ch_sub}")


def generate_emblem_svg(theme: str, accent: str):
    cx, cy = 800, 1400
    if theme == "network-wave":
        elems = []
        for r in range(70, 420, 55):
            op = max(0.18, 0.78 - (r / 450) * 0.55)
            elems.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{accent}" stroke-width="1.5" stroke-dasharray="10,8" fill="none" opacity="{op:.2f}"/>'
            )
        num_spokes = 16
        for i in range(num_spokes):
            ang = (i * 2 * math.pi) / num_spokes
            ox = cx + 380 * math.cos(ang)
            oy = cy + 380 * math.sin(ang)
            elems.append(
                f'<line x1="{cx}" y1="{cy}" x2="{ox:.1f}" y2="{oy:.1f}" stroke="{accent}" stroke-width="1.2" opacity="0.35"/>'
            )
            for r_node in (125, 235, 345):
                nx = cx + r_node * math.cos(ang)
                ny = cy + r_node * math.sin(ang)
                elems.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="5.5" fill="{accent}" opacity="0.88"/>')
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="42" fill="{accent}" opacity="0.16"/>')
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="11" fill="{accent}"/>')
        return f'<g class="emblem-network">{"".join(elems)}</g>'

    elif theme == "harmonic-rings":
        elems = []
        for step in range(18):
            r = 80 + step * 18
            rot = step * 10
            op = 0.16 + step * 0.038
            elems.append(
                f'<ellipse cx="{cx}" cy="{cy}" rx="{r * 1.45:.1f}" ry="{r * 0.68:.1f}" transform="rotate({rot} {cx} {cy})" stroke="{accent}" stroke-width="1.4" fill="none" opacity="{min(0.85, op):.2f}"/>'
            )
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="{accent}"/>')
        return f'<g class="emblem-harmonic">{"".join(elems)}</g>'

    else:
        # Default geometric phase-lattice
        elems = []
        for ring in range(1, 7):
            r = ring * 62
            pts = []
            sides = 8
            for s in range(sides):
                a = (s * 2 * math.pi) / sides + (ring * 0.12)
                px = cx + r * math.cos(a)
                py = cy + r * math.sin(a)
                pts.append(f"{px:.1f},{py:.1f}")
                elems.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.8" fill="{accent}" opacity="0.85"/>')
            op = max(0.22, 0.78 - ring * 0.08)
            elems.append(
                f'<polygon points="{" ".join(pts)}" stroke="{accent}" stroke-width="1.5" fill="none" opacity="{op:.2f}"/>'
            )
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="36" fill="{accent}" opacity="0.18"/>')
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="{accent}"/>')
        return f'<g class="emblem-lattice">{"".join(elems)}</g>'


def _blend_hex(c1: str, c2: str, t: float) -> str:
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(round(r1 * (1 - t) + r2 * t))
    g = int(round(g1 * (1 - t) + g2 * t))
    b = int(round(b1 * (1 - t) + b2 * t))
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _derive_cover_stops(bg: str, accent: str):
    """Ensure cover background and edges stay rich and visible on mobile screens without black crush."""
    top_stop = _blend_hex(_blend_hex("#242a33", bg, 0.65), accent, 0.22)
    mid_stop = _blend_hex(top_stop, "#1b2028", 0.18)
    edge_stop = _blend_hex(top_stop, "#181c24", 0.26)
    return top_stop, mid_stop, edge_stop


def sync_covers_data():
    """Rebuild js/covers-data.js from assets/covers/*.svg so inline cover SVGs stay in sync."""
    covers_js_path = os.path.join(BASE_DIR, "js", "covers-data.js")
    covers = {}
    for fname in sorted(os.listdir(COVERS_DIR)):
        if not fname.endswith(".svg"):
            continue
        slug = fname[:-4]
        if slug == "alexandria-manifesto":
            continue
        svg_text = open(os.path.join(COVERS_DIR, fname), encoding="utf-8").read().strip()
        covers[slug] = svg_text
    if "the-autonomous-engine" in covers and "autonomous-engine" not in covers:
        covers["autonomous-engine"] = covers["the-autonomous-engine"]
    js_out = (
        "// Alexandria Press - Inlined Vector SVG Covers\n"
        "(function(root) {\n"
        "  const covers = " + json.dumps(covers, indent=2, ensure_ascii=False) + ";\n"
        '  if (covers["the-autonomous-engine"] && !covers["autonomous-engine"]) {\n'
        '    covers["autonomous-engine"] = covers["the-autonomous-engine"];\n'
        "  }\n"
        '  if (typeof window !== "undefined") window.EMBEDDED_COVER_SVGS = covers;\n'
        '  if (typeof module !== "undefined" && module.exports) module.exports = covers;\n'
        '})(typeof globalThis !== "undefined" ? globalThis : this);\n'
    )
    open(covers_js_path, "w", encoding="utf-8").write(js_out)


def _wrap_subtitle_svg(subtitle: str):
    """Split subtitle into 1 or 2 balanced lines and return (font_size, inner_svg)."""
    words = subtitle.strip().split()
    if len(subtitle) <= 28 or len(words) <= 3:
        return 62, html.escape(subtitle.strip())
    best_idx = 1
    best_diff = 9999
    for i in range(1, len(words)):
        l1 = " ".join(words[:i])
        l2 = " ".join(words[i:])
        diff = abs(len(l1) - len(l2))
        if diff < best_diff:
            best_diff = diff
            best_idx = i
    line1 = html.escape(" ".join(words[:best_idx]))
    line2 = html.escape(" ".join(words[best_idx:]))
    max_chars = max(len(" ".join(words[:best_idx])), len(" ".join(words[best_idx:])))
    sub_font_size = 62 if max_chars <= 34 else 54
    dy = 78 if sub_font_size == 62 else 68
    inner = f'<tspan x="800" dy="0">{line1}</tspan><tspan x="800" dy="{dy}">{line2}</tspan>'
    return sub_font_size, inner


def generate_cover_svg(slug: str, title: str, subtitle: str, category: str, accent: str, bg: str, theme: str):
    os.makedirs(COVERS_DIR, exist_ok=True)
    emblem = generate_emblem_svg(theme, accent)
    title_font_size = 104 if len(title) <= 22 else (88 if len(title) <= 28 else 74)
    esc_cat = html.escape(category.upper())
    esc_title = html.escape(title)
    sub_font_size, sub_inner = _wrap_subtitle_svg(subtitle)
    top_stop, mid_stop, edge_stop = _derive_cover_stops(bg, accent)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 2400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg-{slug}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{top_stop}"/>
      <stop offset="60%" stop-color="{mid_stop}"/>
      <stop offset="100%" stop-color="{edge_stop}"/>
    </linearGradient>
    <radialGradient id="halo-{slug}" cx="50%" cy="58%" r="75%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.26"/>
      <stop offset="55%" stop-color="{accent}" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0.08"/>
    </radialGradient>
  </defs>

  <rect width="1600" height="2400" fill="url(#bg-{slug})"/>
  <rect width="1600" height="2400" fill="url(#halo-{slug})"/>

  <g text-anchor="middle" font-family="'Inter', -apple-system, sans-serif">
    <text x="800" y="270" font-size="44" font-weight="700" letter-spacing="9" fill="{accent}" opacity="0.95">{esc_cat}</text>
  </g>

  <g text-anchor="middle">
    <text x="800" y="490" font-family="'Literata', Georgia, serif" font-size="{title_font_size}" font-weight="700" letter-spacing="-0.01em" fill="#faf9f6">
      {esc_title}
    </text>
    <text x="800" y="610" font-family="'Literata', Georgia, serif" font-size="{sub_font_size}" font-weight="400" font-style="italic" fill="#cbd5e1">
      {sub_inner}
    </text>
  </g>

  {emblem}

  <g text-anchor="middle" font-family="'Inter', -apple-system, sans-serif">
    <text x="800" y="2220" font-size="34" font-weight="700" letter-spacing="10" fill="#a8a29e" opacity="0.85">ALEXANDRIA.PRESS</text>
  </g>
</svg>
"""
    cover_path = os.path.join(COVERS_DIR, f"{slug}.svg")
    open(cover_path, "w", encoding="utf-8").write(svg)
    return cover_path


def update_index_and_sitemap(slug: str, title: str, subtitle: str, category: str):
    index_html = open(INDEX_HTML_PATH, encoding="utf-8").read()
    esc_title = html.escape(title)
    esc_sub = html.escape(subtitle)
    esc_cat = html.escape(category)

    # 1. Check if book card already in index.html
    card_pattern = re.compile(
        rf'<article class="book-card"\s+data-key="{re.escape(slug)}"[\s\S]*?</article>'
    )
    new_card = f"""<article class="book-card" data-key="{slug}" data-title="{esc_title}" data-subtitle="{esc_sub}" data-category="{esc_cat}" onclick="openBookFromCatalog('{slug}')" title="{esc_title} — {esc_sub}">
                    <div class="book-cover-frame">
                        <img src="assets/covers/{slug}.svg" alt="{esc_title} Cover" loading="eager">
                    </div>
                </article>"""

    if card_pattern.search(index_html):
        index_html = card_pattern.sub(new_card, index_html)
    else:
        grid_close = '            </div>\n        </div>\n    </div>\n\n    <main id="main-stage">'
        if grid_close in index_html:
            index_html = index_html.replace(grid_close, f"                {new_card}\n{grid_close}", 1)

    # 2. Check JSON-LD in index.html
    if f'"?book={slug}"' not in index_html:
        ld_entry = f""",
        {{
          "@type": "Book",
          "name": {json.dumps(title)},
          "headline": {json.dumps(subtitle)},
          "url": "https://alexandria.press/?book={slug}",
          "image": "https://alexandria.press/assets/covers/{slug}.svg"
        }}
      ]"""
        index_html = re.sub(r"\n\s*\]\s*\n\s*\}\s*\n\s*</script>", ld_entry + "\n    }\n    </script>", index_html, count=1)

    open(INDEX_HTML_PATH, "w", encoding="utf-8").write(index_html)

    # 3. Update sitemap.xml
    if os.path.exists(SITEMAP_PATH):
        smap = open(SITEMAP_PATH, encoding="utf-8").read()
        loc_url = f"https://alexandria.press/?book={slug}"
        if loc_url not in smap:
            today = datetime.date.today().isoformat()
            entry = f"""  <url>
    <loc>{loc_url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>"""
            smap = smap.replace("</urlset>", entry)
            open(SITEMAP_PATH, "w", encoding="utf-8").write(smap)


def main():
    parser = argparse.ArgumentParser(description="Publish or sync Alexandria Press books.")
    parser.add_argument("--list-anchors", action="store_true", help="List all existing books and chapters")
    parser.add_argument("--sync-all", action="store_true", help="Validate and sync all existing books into js/books-data.js")
    parser.add_argument("--slug", help="Hyphenated book slug (e.g. geometries-of-contagion)")
    parser.add_argument("--category", default="Systems & Science", help="Book category label")
    parser.add_argument("--accent", default="#10b981", help="Hex accent color for cover")
    parser.add_argument("--bg", default="#0b1d18", help="Hex background color for cover")
    parser.add_argument("--theme", default="lattice", choices=["network-wave", "harmonic-rings", "lattice"], help="Cover geometric emblem")
    parser.add_argument("--regenerate-cover", action="store_true", help="Force regenerate SVG cover")
    args = parser.parse_args()

    if args.list_anchors:
        list_existing_anchors()
        return

    prefix, data, suffix = load_books_data()

    if args.sync_all:
        for slug, meta in data.items():
            md_file = os.path.join(BASE_DIR, slug.replace("-", "_") + ".md")
            errs, _, _ = validate_book(md_file, legacy=True)
            if errs:
                print(f"[FAIL] {md_file} failed validation:")
                for e in errs:
                    print("  ", e)
                sys.exit(1)
            md_text = open(md_file, encoding="utf-8").read()
            title, subtitle = extract_title_subtitle(md_text)
            meta["title"] = title
            meta["subtitle"] = subtitle
            meta["markdown"] = md_text
            print(f"[SYNCED] {slug:26s} -> {len(md_text):6,d} chars")
        save_books_data(prefix, data, suffix)
        sync_covers_data()
        print("Successfully synced all volumes into js/books-data.js and js/covers-data.js.")
        return

    if not args.slug:
        parser.print_help()
        sys.exit(1)

    slug = args.slug.strip().lower().replace("_", "-")
    md_filename = slug.replace("-", "_") + ".md"
    md_path = os.path.join(BASE_DIR, md_filename)

    errs, warns, info = validate_book(md_path)
    if errs:
        print(f"[ABORT] {md_filename} failed quality gates ({len(errs)} error(s)):")
        for e in errs:
            print("  ERROR:", e)
        sys.exit(1)

    for w in warns:
        print("  WARN:", w)

    md_text = open(md_path, encoding="utf-8").read()
    title, subtitle = extract_title_subtitle(md_text)

    cover_file = os.path.join(COVERS_DIR, f"{slug}.svg")
    if not os.path.exists(cover_file) or args.regenerate_cover:
        generate_cover_svg(slug, title, subtitle, args.category, args.accent, args.bg, args.theme)
        print(f"[COVER] Generated vector cover: assets/covers/{slug}.svg")

    data[slug] = {
        "title": title,
        "subtitle": subtitle,
        "category": args.category,
        "markdown": md_text,
    }
    save_books_data(prefix, data, suffix)
    sync_covers_data()
    update_index_and_sitemap(slug, title, subtitle, args.category)
    print(
        f"[PUBLISHED] '{title}: {subtitle}' ({slug}) | {info['chapters']} chapters | {info['total_words']:,} words"
    )


if __name__ == "__main__":
    main()
