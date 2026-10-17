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


def extract_book_metadata(md_text: str):
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


def list_existing_anchors():
    _, data, _ = load_books_data()
    print("=== EXISTING ALEXANDRIA PRESS LIBRARY ANCHORS (DO NOT DUPLICATE) ===")
    for slug, meta in data.items():
        print(f"\n[{slug}] {meta['title']} — {meta['subtitle']} ({meta['category']})")
        chapters = meta.get("chapters")
        if not chapters:
            md_file = os.path.join(BASE_DIR, slug.replace("-", "_") + ".md")
            if os.path.exists(md_file):
                _, _, chapters = extract_book_metadata(open(md_file, encoding="utf-8").read())
        for idx, ch in enumerate((chapters or [])[1:], 1):
            print(f"  Ch {idx:2d}: {ch['title']} — {ch['subtitle']}")


def generate_emblem_svg(theme: str, accent: str, slug: str = ""):
    import hashlib
    cx, cy = 800, 1400
    seed = int(hashlib.sha256((slug or theme).encode("utf-8")).hexdigest()[:8], 16)

    if theme == "foveal-aperture" or slug == "attention":
        # Bespoke Foveal Aperture & Thalamic Searchlight geometry for Attention
        elems = []
        # Outer peripheral retinal rings (fading outward)
        for r in (380, 330, 280, 230, 180):
            op = 0.16 + (400 - r) / 700
            dash = ' stroke-dasharray="6,10"' if r > 250 else ""
            elems.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{accent}" stroke-width="1.5"{dash} fill="none" opacity="{op:.2f}"/>'
            )
        # 24 iris aperture blades tangent to an inner 92px foveal circle
        blades = 24
        r_inner = 92
        r_outer = 340
        for i in range(blades):
            a1 = (i * 2 * math.pi) / blades
            a2 = a1 + 0.68
            x1 = cx + r_inner * math.cos(a1)
            y1 = cy + r_inner * math.sin(a1)
            x2 = cx + r_outer * math.cos(a2)
            y2 = cy + r_outer * math.sin(a2)
            op = 0.28 + 0.35 * ((i % 3) / 2)
            elems.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{accent}" stroke-width="1.6" opacity="{op:.2f}"/>'
            )
            if i % 2 == 0:
                elems.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="4.2" fill="{accent}" opacity="0.65"/>')
        # Crisp foveal aperture ring + crosshairs + central fixation target
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" stroke="{accent}" stroke-width="2.6" fill="{accent}" fill-opacity="0.08" opacity="0.92"/>')
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="44" stroke="{accent}" stroke-width="1.8" fill="none" opacity="0.85"/>')
        for a_deg in (0, 90, 180, 270):
            rad = math.radians(a_deg)
            x_in, y_in = cx + 52 * math.cos(rad), cy + 52 * math.sin(rad)
            x_out, y_out = cx + 118 * math.cos(rad), cy + 118 * math.sin(rad)
            elems.append(f'<line x1="{x_in:.1f}" y1="{y_in:.1f}" x2="{x_out:.1f}" y2="{y_out:.1f}" stroke="{accent}" stroke-width="2.0" opacity="0.85"/>')
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="11" fill="{accent}"/>')
        return f'<g class="emblem-foveal-aperture">{"".join(elems)}</g>'

    if theme == "open-horizon" or slug == "self-transcendence":
        # Bespoke Dissolving Boundary / Open Horizon geometry for Self-Transcendence
        elems = []
        # Inner crisp dodecagonal self-boundary that progressively opens into wider broken arcs
        for ring_idx, r in enumerate((76, 122, 172, 226, 284, 346)):
            dash_len = max(4, 38 - ring_idx * 6)
            gap_len = 4 + ring_idx * 9
            op = max(0.20, 0.88 - ring_idx * 0.11)
            sw = max(1.2, 2.4 - ring_idx * 0.2)
            rot = ring_idx * 15
            elems.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{accent}" stroke-width="{sw:.1f}" stroke-dasharray="{dash_len},{gap_len}" transform="rotate({rot} {cx} {cy})" fill="none" opacity="{op:.2f}"/>'
            )
        # 12 ascending parabolic/hyperbolic horizon rays opening upward and outward from the center
        rays = 12
        for i in range(rays):
            ang = (i * 2 * math.pi) / rays
            x1 = cx + 76 * math.cos(ang)
            y1 = cy + 76 * math.sin(ang)
            x2 = cx + 375 * math.cos(ang)
            y2 = cy + 375 * math.sin(ang)
            ctrl_ang = ang + 0.24 * (1 if i % 2 == 0 else -1)
            cx_ctrl = cx + 225 * math.cos(ctrl_ang)
            cy_ctrl = cy + 225 * math.sin(ctrl_ang)
            elems.append(
                f'<path d="M {x1:.1f} {y1:.1f} Q {cx_ctrl:.1f} {cy_ctrl:.1f} {x2:.1f} {y2:.1f}" stroke="{accent}" stroke-width="1.5" fill="none" opacity="0.48"/>'
            )
            elems.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="4.5" fill="{accent}" opacity="0.72"/>')
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="28" stroke="{accent}" stroke-width="1.8" fill="{accent}" fill-opacity="0.10" opacity="0.90"/>')
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="{accent}"/>')
        return f'<g class="emblem-open-horizon">{"".join(elems)}</g>'

    # Slug-parameterized unique mathematical rose / spirograph / polyhedral family so no two covers ever repeat
    elems = []
    petals = 5 + (seed % 9)  # 5..13
    loops = 140
    pts = []
    r_base = 150 + (seed % 50)
    r_amp = 160 + ((seed >> 4) % 45)
    phase = ((seed >> 8) % 360) * math.pi / 180.0
    for step in range(loops + 1):
        t = (step * 2 * math.pi) / loops
        r = r_base + r_amp * math.cos(petals * t + phase) * math.sin(2 * t)
        px = cx + r * math.cos(t)
        py = cy + r * math.sin(t)
        pts.append(f"{px:.1f},{py:.1f}")
    elems.append(f'<polyline points="{" ".join(pts)}" stroke="{accent}" stroke-width="1.8" fill="none" opacity="0.72"/>')
    for ring in (110, 240, 365):
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="{ring}" stroke="{accent}" stroke-width="1.2" stroke-dasharray="6,8" fill="none" opacity="0.35"/>')
    elems.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="{accent}"/>')
    return f'<g class="emblem-{slug or "custom"}">{"".join(elems)}</g>'


def _blend_hex(c1: str, c2: str, t: float) -> str:
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(round(r1 * (1 - t) + r2 * t))
    g = int(round(g1 * (1 - t) + g2 * t))
    b = int(round(b1 * (1 - t) + b2 * t))
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _mute_pastel_hex(hex_str: str, target_l: float, max_s: float) -> str:
    import colorsys
    c = hex_str.lstrip("#")
    r, g, b = int(c[0:2], 16) / 255.0, int(c[2:4], 16) / 255.0, int(c[4:6], 16) / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    s_new = min(max_s, s * 0.42)
    r2, g2, b2 = colorsys.hls_to_rgb(h, target_l, s_new)
    return f"#{int(round(r2*255)):02x}{int(round(g2*255)):02x}{int(round(b2*255)):02x}"


def _derive_cover_stops(bg: str, accent: str):
    """Derive muted mineral/bookcloth pastel background stops."""
    top_pastel = _blend_hex(_mute_pastel_hex(accent, 0.83, 0.32), "#e3ded4", 0.24)
    mid_pastel = _blend_hex(_mute_pastel_hex(accent, 0.79, 0.34), "#dbd5c8", 0.26)
    edge_pastel = _blend_hex(_mute_pastel_hex(accent, 0.75, 0.36), "#d2cbbd", 0.28)
    return top_pastel, mid_pastel, edge_pastel


THUMBS_DIR = os.path.join(COVERS_DIR, "thumbs")


def build_thumb_svg_from_cover(cover_svg: str, slug: str) -> str:
    """Extract the pastel background and geometric emblem (without cover text) into a high-contrast 1:1 square thumbnail SVG."""
    defs_m = re.search(r"<defs>[\s\S]*?</defs>", cover_svg)
    emblem_m = re.search(r'<g class="emblem-[^"]*"[\s\S]*?</g>', cover_svg)
    defs_block = defs_m.group(0) if defs_m else ""
    emblem_block = emblem_m.group(0) if emblem_m else ""

    # 1. Darken all hex stroke/fill colors in the emblem toward deep ink (#0b0f17) for strong contrast on pastel tiles
    emblem_block = re.sub(
        r'(stroke|fill)="#([0-9a-fA-F]{6})"',
        lambda m: f'{m.group(1)}="{_blend_hex("#" + m.group(2), "#0b0f17", 0.58)}"',
        emblem_block,
    )

    # 2. Scale up stroke-widths (~3.2x, floor 4.8) so geometric & equation curves remain crisp at 68x68px
    emblem_block = re.sub(
        r'stroke-width="([0-9.]+)"',
        lambda m: f'stroke-width="{max(4.8, float(m.group(1)) * 3.2):.1f}"',
        emblem_block,
    )

    # 3. Boost opacity on stroked primitives and text so secondary curves don't wash out against the background
    def _boost_tag_opacity(tag_m):
        tag = tag_m.group(0)
        if 'stroke="' in tag or tag.startswith("<text"):
            tag = re.sub(
                r'(?<!fill-)opacity="([0-9.]+)"',
                lambda m: f'opacity="{min(1.0, 0.72 + float(m.group(1)) * 0.28):.2f}"',
                tag,
            )
        return tag

    emblem_block = re.sub(r"<[a-zA-Z]+[^>]*>", _boost_tag_opacity, emblem_block)

    # 4. Slightly enlarge small vertex dots (r <= 8) so nodes read clearly at thumbnail scale
    emblem_block = re.sub(
        r'\br="([0-9.]+)"',
        lambda m: f'r="{float(m.group(1)) * 1.45:.1f}"' if float(m.group(1)) <= 8.0 else m.group(0),
        emblem_block,
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="310 700 980 980" width="100%" height="100%">\n'
        f"  {defs_block}\n"
        f'  <rect x="310" y="700" width="980" height="980" fill="url(#bg-{slug})"/>\n'
        f'  <rect x="310" y="700" width="980" height="980" fill="url(#halo-{slug})"/>\n'
        f"  {emblem_block}\n"
        f"</svg>"
    )


def sync_covers_data():
    """Rebuild assets/covers/thumbs/*.svg and js/covers-data.js (emblem-only square thumbnails for Home cards)."""
    os.makedirs(THUMBS_DIR, exist_ok=True)
    covers_js_path = os.path.join(BASE_DIR, "js", "covers-data.js")
    covers = {}
    for fname in sorted(os.listdir(COVERS_DIR)):
        if not fname.endswith(".svg"):
            continue
        slug = fname[:-4]
        svg_text = open(os.path.join(COVERS_DIR, fname), encoding="utf-8").read().strip()
        thumb_svg = build_thumb_svg_from_cover(svg_text, slug)
        open(os.path.join(THUMBS_DIR, fname), "w", encoding="utf-8").write(thumb_svg)
        covers[slug] = thumb_svg
    js_out = (
        "// Alexandria Press - Inlined Vector SVG Thumbnails (Home Catalog Cards)\n"
        "(function(root) {\n"
        "  const covers = " + json.dumps(covers, indent=2, ensure_ascii=False) + ";\n"
        '  if (typeof window !== "undefined") window.EMBEDDED_COVER_SVGS = covers;\n'
        '  if (typeof module !== "undefined" && module.exports) module.exports = covers;\n'
        '})(typeof globalThis !== "undefined" ? globalThis : this);\n'
    )
    open(covers_js_path, "w", encoding="utf-8").write(js_out)


def _wrap_title_svg(title: str):
    """Wrap PDF cover titles >20 chars into 2 balanced lines with clean PDF-cover proportions."""
    text = title.strip()
    words = text.split()
    if len(text) <= 20 or len(words) <= 1:
        return 88, 380, html.escape(text)
    best_idx = 1
    best_max = 9999
    for i in range(1, len(words)):
        l1 = " ".join(words[:i])
        l2 = " ".join(words[i:])
        m = max(len(l1), len(l2))
        if m < best_max:
            best_max = m
            best_idx = i
    line1 = html.escape(" ".join(words[:best_idx]))
    line2 = html.escape(" ".join(words[best_idx:]))
    dy = 116
    inner = f'<tspan x="800" dy="0">{line1}</tspan><tspan x="800" dy="{dy}">{line2}</tspan>'
    return 88, 332, inner


def _wrap_subtitle_svg(subtitle: str):
    """Split PDF cover subtitle into 1, 2, or 3 balanced lines in the bottom zone (y_center=1985) without horizontal distortion."""
    text = subtitle.strip()
    words = text.split()
    if len(text) <= 28 or len(words) <= 3:
        return 54, 1985, html.escape(text)

    if len(text) <= 54:
        # 2 balanced lines
        best_idx = 1
        best_max = 9999
        for i in range(1, len(words)):
            l1 = " ".join(words[:i])
            l2 = " ".join(words[i:])
            m = max(len(l1), len(l2))
            if m < best_max:
                best_max = m
                best_idx = i
        line1 = html.escape(" ".join(words[:best_idx]))
        line2 = html.escape(" ".join(words[best_idx:]))
        sub_font_size = 54
        dy = 82
        y_start = 1985 - dy // 2
        inner = f'<tspan x="800" dy="0">{line1}</tspan><tspan x="800" dy="{dy}">{line2}</tspan>'
        return sub_font_size, y_start, inner

    # 3 balanced lines for subtitles > 54 chars
    best_pair = (1, 2)
    best_max = 9999
    n = len(words)
    for i in range(1, n - 1):
        for j in range(i + 1, n):
            l1 = " ".join(words[:i])
            l2 = " ".join(words[i:j])
            l3 = " ".join(words[j:])
            m = max(len(l1), len(l2), len(l3))
            if m < best_max:
                best_max = m
                best_pair = (i, j)
    i, j = best_pair
    line1 = html.escape(" ".join(words[:i]))
    line2 = html.escape(" ".join(words[i:j]))
    line3 = html.escape(" ".join(words[j:]))
    sub_font_size = 50 if best_max <= 30 else 47
    dy = 76 if sub_font_size == 50 else 72
    y_start = 1985 - dy
    inner = (
        f'<tspan x="800" dy="0">{line1}</tspan>'
        f'<tspan x="800" dy="{dy}">{line2}</tspan>'
        f'<tspan x="800" dy="{dy}">{line3}</tspan>'
    )
    return sub_font_size, y_start, inner


def refresh_existing_pdf_cover_typography(slug: str, title: str, subtitle: str):
    """Update title and subtitle blocks in an existing assets/covers/<slug>.svg for optimal PDF cover proportions while preserving its bespoke emblem."""
    cover_path = os.path.join(COVERS_DIR, f"{slug}.svg")
    if not os.path.exists(cover_path):
        return False
    svg = open(cover_path, encoding="utf-8").read()
    text_blocks = list(re.finditer(r'<g text-anchor="middle"[^>]*>\s*<text[^>]*fill="([^"]+)"[^>]*>[\s\S]*?</text>\s*</g>', svg))
    if len(text_blocks) < 2:
        return False
    title_color = text_blocks[0].group(1)
    subtitle_color = text_blocks[-1].group(1)
    title_font_size, title_y, title_inner = _wrap_title_svg(title)
    sub_font_size, sub_y, sub_inner = _wrap_subtitle_svg(subtitle)
    new_title_g = (
        f'<g text-anchor="middle">\n'
        f'    <text x="800" y="{title_y}" font-family="\'Literata\', Georgia, serif" font-size="{title_font_size}" font-weight="700" letter-spacing="-0.01em" fill="{title_color}">{title_inner}</text>\n'
        f"  </g>"
    )
    new_sub_g = (
        f'<g text-anchor="middle">\n'
        f'    <text x="800" y="{sub_y}" font-family="\'Literata\', Georgia, serif" font-size="{sub_font_size}" font-weight="400" letter-spacing="0.01em" fill="{subtitle_color}">{sub_inner}</text>\n'
        f"  </g>"
    )
    # Replace last block first so indices stay valid
    s2, e2 = text_blocks[-1].span()
    svg = svg[:s2] + new_sub_g + svg[e2:]
    s1, e1 = text_blocks[0].span()
    svg = svg[:s1] + new_title_g + svg[e1:]
    open(cover_path, "w", encoding="utf-8").write(svg)
    return True


def generate_cover_svg(slug: str, title: str, subtitle: str, category: str, accent: str, bg: str, theme: str):
    os.makedirs(COVERS_DIR, exist_ok=True)
    title_color = _blend_hex(_blend_hex("#1e222a", bg, 0.78), accent, 0.12)
    subtitle_color = _blend_hex(title_color, "#4a4842", 0.35)
    emblem_color = _blend_hex(title_color, accent, 0.35)
    emblem = generate_emblem_svg(theme, emblem_color, slug=slug)
    emblem = re.sub(r'^<g class="([^"]+)">', r'<g class="\1" transform="translate(0, -210)">', emblem)
    title_font_size, title_y, title_inner = _wrap_title_svg(title)
    sub_font_size, sub_y, sub_inner = _wrap_subtitle_svg(subtitle)
    top_stop, mid_stop, edge_stop = _derive_cover_stops(bg, accent)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 2400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg-{slug}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{top_stop}"/>
      <stop offset="60%" stop-color="{mid_stop}"/>
      <stop offset="100%" stop-color="{edge_stop}"/>
    </linearGradient>
    <radialGradient id="halo-{slug}" cx="50%" cy="50%" r="75%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.06"/>
      <stop offset="55%" stop-color="{accent}" stop-opacity="0.03"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0.00"/>
    </radialGradient>
  </defs>

  <rect width="1600" height="2400" fill="url(#bg-{slug})"/>
  <rect width="1600" height="2400" fill="url(#halo-{slug})"/>

  <g text-anchor="middle">
    <text x="800" y="{title_y}" font-family="'Literata', Georgia, serif" font-size="{title_font_size}" font-weight="700" letter-spacing="-0.01em" fill="{title_color}">{title_inner}</text>
  </g>

  {emblem}

  <g text-anchor="middle">
    <text x="800" y="{sub_y}" font-family="'Literata', Georgia, serif" font-size="{sub_font_size}" font-weight="400" letter-spacing="0.01em" fill="{subtitle_color}">{sub_inner}</text>
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
                        <img src="assets/covers/thumbs/{slug}.svg" alt="{esc_title}" loading="eager">
                    </div>
                    <div class="book-card-info">
                        <div class="book-card-title">{esc_title}</div>
                        <div class="book-card-subtitle">{esc_sub}</div>
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
    parser.add_argument("--theme", default="lattice", help="Cover geometric emblem")
    parser.add_argument("--regenerate-cover", action="store_true", help="Force regenerate SVG cover")
    parser.add_argument("--recompile", action="store_true", help="Force recompile all PDFs during --sync-all")
    args = parser.parse_args()

    if args.list_anchors:
        list_existing_anchors()
        return

    prefix, data, suffix = load_books_data()

    if args.sync_all:
        from compile_typst import compile_book_to_pdf
        for slug, meta in data.items():
            md_file = os.path.join(BASE_DIR, slug.replace("-", "_") + ".md")
            errs, _, _ = validate_book(md_file, legacy=True)
            if errs:
                print(f"[FAIL] {md_file} failed validation:")
                for e in errs:
                    print("  ", e)
                sys.exit(1)
            md_text = open(md_file, encoding="utf-8").read()
            title, subtitle, chapters = extract_book_metadata(md_text)
            refresh_existing_pdf_cover_typography(slug, title, subtitle)
            update_index_and_sitemap(slug, title, subtitle, meta.get("category", "Systems & Science"))
            pdf_path = os.path.join(BASE_DIR, "assets", "pdfs", f"{slug}.pdf")
            comp_path = os.path.join(BASE_DIR, "assets", "pdfs", f"{slug}-compact.pdf")
            mob_path = os.path.join(BASE_DIR, "assets", "pdfs", f"{slug}-mobile.pdf")
            cover_path = os.path.join(COVERS_DIR, f"{slug}.svg")
            needs_compile = (
                args.recompile
                or not os.path.exists(pdf_path)
                or not os.path.exists(comp_path)
                or not os.path.exists(mob_path)
                or os.path.getmtime(md_file) > os.path.getmtime(pdf_path)
                or (os.path.exists(cover_path) and os.path.getmtime(cover_path) > os.path.getmtime(pdf_path))
                or not meta.get("sectionPages")
                or not meta.get("compactSectionPages")
                or not meta.get("mobileSectionPages")
            )
            if needs_compile:
                pdf_path, sec_pages, comp_path, comp_pages, mob_path, mob_pages = compile_book_to_pdf(
                    md_file, category=meta.get("category", "NON-FICTION")
                )
            else:
                sec_pages = meta["sectionPages"]
                comp_pages = meta["compactSectionPages"]
                mob_pages = meta["mobileSectionPages"]

            meta.pop("markdown", None)
            meta["title"] = title
            meta["subtitle"] = subtitle
            meta["pdf"] = f"assets/pdfs/{slug}.pdf"
            meta["compactPdf"] = f"assets/pdfs/{slug}-compact.pdf"
            meta["mobilePdf"] = f"assets/pdfs/{slug}-mobile.pdf"
            meta["sectionPages"] = sec_pages
            meta["compactSectionPages"] = comp_pages
            meta["mobileSectionPages"] = mob_pages
            meta["chapters"] = chapters
            print(f"[SYNCED] {slug:26s} -> {len(chapters)} sections | Desktop: {os.path.getsize(pdf_path)//1024} KB | Compact: {os.path.getsize(comp_path)//1024} KB | Mobile: {os.path.getsize(mob_path)//1024} KB")
        save_books_data(prefix, data, suffix)
        sync_covers_data()
        print("Successfully synced all volumes and Typst PDFs into js/books-data.js and js/covers-data.js.")
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
    title, subtitle, chapters = extract_book_metadata(md_text)

    cover_file = os.path.join(COVERS_DIR, f"{slug}.svg")
    if not os.path.exists(cover_file) or args.regenerate_cover:
        generate_cover_svg(slug, title, subtitle, args.category, args.accent, args.bg, args.theme)
        print(f"[COVER] Generated vector cover: assets/covers/{slug}.svg")
    else:
        refresh_existing_pdf_cover_typography(slug, title, subtitle)

    from compile_typst import compile_book_to_pdf
    pdf_path, sec_pages, comp_path, comp_pages, mob_path, mob_pages = compile_book_to_pdf(md_path, category=args.category, accent_hex=args.accent)
    print(f"[TYPST] Compiled PDFs: {slug}.pdf ({os.path.getsize(pdf_path)//1024} KB), {slug}-compact.pdf ({os.path.getsize(comp_path)//1024} KB), {slug}-mobile.pdf ({os.path.getsize(mob_path)//1024} KB)")

    data[slug] = {
        "title": title,
        "subtitle": subtitle,
        "category": args.category,
        "pdf": f"assets/pdfs/{slug}.pdf",
        "compactPdf": f"assets/pdfs/{slug}-compact.pdf",
        "mobilePdf": f"assets/pdfs/{slug}-mobile.pdf",
        "sectionPages": sec_pages,
        "compactSectionPages": comp_pages,
        "mobileSectionPages": mob_pages,
        "chapters": chapters,
    }
    save_books_data(prefix, data, suffix)
    sync_covers_data()
    update_index_and_sitemap(slug, title, subtitle, args.category)
    print(
        f"[PUBLISHED] '{title}: {subtitle}' ({slug}) | {info['chapters']} chapters | {info['total_words']:,} words"
    )


if __name__ == "__main__":
    main()

