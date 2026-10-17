#!/usr/bin/env python3
"""
Alexandria Press — Autonomous Book Publisher & Library Sync (scripts/publish_book.py)

Automates Stage 5 of the Alexandria Press generation pipeline using `catalog.json`
as the single source of truth:
1. Runs deterministic validation (`validate_book`) on `books/<slug>.md`.
2. Generates a 1600x2400 mathematical vector SVG cover (`assets/covers/<slug>.svg`) and
   a 1:1 high-contrast thumbnail (`assets/covers/thumbs/<slug>.svg`).
3. Compiles Desktop, Compact, and Mobile Typst PDF editions (`assets/pdfs/<slug>*.pdf`).
4. Updates `catalog.json` and deterministically regenerates:
   - `js/books-data.js`
   - `<!-- BEGIN:JSON_LD -->` and `<!-- BEGIN:CATALOG_GRID -->` in `index.html`
   - `sitemap.xml`

Usage:
    python3 scripts/publish_book.py --list-anchors
    python3 scripts/publish_book.py --sync-all [--recompile]
    python3 scripts/publish_book.py --slug the-cell --category "Molecular Biology" --accent "#10b981" --bg "#061e16"
    python3 scripts/publish_book.py --batch 3
"""

import argparse
import colorsys
import datetime
import hashlib
import html
import json
import math
import os
import re
import subprocess
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from lib import (  # noqa: E402
    COVERS_DIR,
    DOSSIERS_DIR,
    INDEX_HTML_PATH,
    LEGACY_SLUGS,
    OG_DIR,
    PDFS_DIR,
    READ_HTML_DIR,
    SITEMAP_PATH,
    THUMBS_DIR,
    extract_book_metadata,
    infer_book_format,
    load_backlog,
    load_catalog,
    normalize_slug,
    resolve_book_md,
    save_backlog,
    save_catalog,
    slugify_text,
    write_books_js_from_catalog,
)
from validate_book import validate_book  # noqa: E402


def list_existing_anchors():
    catalog = load_catalog()
    print("=== EXISTING ALEXANDRIA PRESS LIBRARY ANCHORS (DO NOT DUPLICATE) ===")
    for slug, meta in catalog.items():
        print(f"\n[{slug}] {meta['title']} — {meta['subtitle']} ({meta.get('category', '')})")
        chapters = meta.get("chapters")
        if not chapters:
            _, md_file = resolve_book_md(slug)
            if os.path.exists(md_file):
                _, _, chapters = extract_book_metadata(open(md_file, encoding="utf-8").read())
        for idx, ch in enumerate((chapters or [])[1:], 1):
            print(f"  Ch {idx:2d}: {ch['title']} — {ch['subtitle']}")


def generate_emblem_svg(theme: str, accent: str, slug: str = ""):
    cx, cy = 800, 1400
    seed = int(hashlib.sha256((slug or theme).encode("utf-8")).hexdigest()[:8], 16)

    if theme == "foveal-aperture" or slug == "attention":
        elems = []
        for r in (380, 330, 280, 230, 180):
            op = 0.16 + (400 - r) / 700
            dash = ' stroke-dasharray="6,10"' if r > 250 else ""
            elems.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{accent}" stroke-width="1.5"{dash} fill="none" opacity="{op:.2f}"/>'
            )
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
        elems.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" stroke="{accent}" stroke-width="2.6" fill="{accent}" fill-opacity="0.08" opacity="0.92"/>'
        )
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="44" stroke="{accent}" stroke-width="1.8" fill="none" opacity="0.85"/>')
        for a_deg in (0, 90, 180, 270):
            rad = math.radians(a_deg)
            x_in, y_in = cx + 52 * math.cos(rad), cy + 52 * math.sin(rad)
            x_out, y_out = cx + 118 * math.cos(rad), cy + 118 * math.sin(rad)
            elems.append(
                f'<line x1="{x_in:.1f}" y1="{y_in:.1f}" x2="{x_out:.1f}" y2="{y_out:.1f}" stroke="{accent}" stroke-width="2.0" opacity="0.85"/>'
            )
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="11" fill="{accent}"/>')
        return f'<g class="emblem-foveal-aperture">{"".join(elems)}</g>'

    if theme == "open-horizon" or slug == "self-transcendence":
        elems = []
        for ring_idx, r in enumerate((76, 122, 172, 226, 284, 346)):
            dash_len = max(4, 38 - ring_idx * 6)
            gap_len = 4 + ring_idx * 9
            op = max(0.20, 0.88 - ring_idx * 0.11)
            sw = max(1.2, 2.4 - ring_idx * 0.2)
            rot = ring_idx * 15
            elems.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{accent}" stroke-width="{sw:.1f}" stroke-dasharray="{dash_len},{gap_len}" transform="rotate({rot} {cx} {cy})" fill="none" opacity="{op:.2f}"/>'
            )
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
        elems.append(
            f'<circle cx="{cx}" cy="{cy}" r="28" stroke="{accent}" stroke-width="1.8" fill="{accent}" fill-opacity="0.10" opacity="0.90"/>'
        )
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="{accent}"/>')
        return f'<g class="emblem-open-horizon">{"".join(elems)}</g>'

    # Slug-parameterized mathematical rose / spirograph / polyhedral family so no two covers ever repeat
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
        elems.append(
            f'<circle cx="{cx}" cy="{cy}" r="{ring}" stroke="{accent}" stroke-width="1.2" stroke-dasharray="6,8" fill="none" opacity="0.35"/>'
        )
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


def sync_thumbs_from_covers():
    """Rebuild `assets/covers/thumbs/*.svg` emblem-only square thumbnails for Home cards."""
    os.makedirs(THUMBS_DIR, exist_ok=True)
    for fname in sorted(os.listdir(COVERS_DIR)):
        if not fname.endswith(".svg"):
            continue
        slug = fname[:-4]
        svg_text = open(os.path.join(COVERS_DIR, fname), encoding="utf-8").read().strip()
        thumb_svg = build_thumb_svg_from_cover(svg_text, slug)
        open(os.path.join(THUMBS_DIR, fname), "w", encoding="utf-8").write(thumb_svg)


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
    """Split PDF cover subtitle into 1, 2, or 3 balanced lines in the bottom zone (y_center=1985)."""
    text = subtitle.strip()
    words = text.split()
    if len(text) <= 28 or len(words) <= 3:
        return 54, 1985, html.escape(text)

    if len(text) <= 54:
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
    """Update title and subtitle blocks in an existing `assets/covers/<slug>.svg` while preserving its bespoke emblem."""
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


def _render_markdown_section_to_semantic_html(sec_md: str) -> str:
    """Convert a chapter or introduction markdown section body into clean semantic HTML for crawlers and static view."""
    lines = sec_md.splitlines()
    body_start = 0
    h_cnt = 0
    for i, l in enumerate(lines):
        if l.strip().startswith("#"):
            h_cnt += 1
            if h_cnt == 3:
                body_start = i + 1
                break
    body = "\n".join(lines[body_start:]).strip()

    blocks = []

    def _save_blk(h_str: str) -> str:
        idx = len(blocks)
        blocks.append(h_str)
        return f"\n\n@@HTML_BLK_{idx}@@\n\n"

    def _repl_svg(m):
        svg_raw = m.group(1).strip()
        cap_m = re.search(r'data-caption="([^"]+)"', svg_raw)
        cap_html = f'<figcaption>{html.escape(cap_m.group(1))}</figcaption>' if cap_m else ""
        return _save_blk(f'<figure class="chapter-diagram">{svg_raw}{cap_html}</figure>')

    body = re.sub(r"```(?:svg|diagram)\s*\n([\s\S]*?)```", _repl_svg, body, flags=re.IGNORECASE)

    def _repl_math(m):
        eq_txt = html.escape(m.group(1).strip())
        return _save_blk(f'<div class="math-block"><code>$${eq_txt}$$</code></div>')

    body = re.sub(r"\$\$([\s\S]*?)\$\$", _repl_math, body)

    def _inline_fmt(txt: str) -> str:
        txt = txt.replace("\\$", "$")
        t = html.escape(txt)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
        return t

    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    out_html = []
    for p in paras:
        m_b = re.match(r"^@@HTML_BLK_(\d+)@@$", p)
        if m_b:
            out_html.append(blocks[int(m_b.group(1))])
            continue
        p_lines = [l.strip() for l in p.splitlines() if l.strip()]
        if not p_lines:
            continue
        if len(p_lines) == 1 and p_lines[0] in ("· · ·", "···", "• • •", "❦"):
            out_html.append('<div class="section-sep">· · ·</div>')
            continue
        if all(l.startswith(">") for l in p_lines):
            q = " ".join(re.sub(r"^>\s*", "", l) for l in p_lines)
            out_html.append(f"<blockquote>{_inline_fmt(q)}</blockquote>")
            continue
        if all(re.match(r"^[*\-]\s+", l) for l in p_lines):
            items = [f"<li>{_inline_fmt(re.sub(r'^[*-]\\s+', '', l))}</li>" for l in p_lines]
            out_html.append("<ul>\n  " + "\n  ".join(items) + "\n</ul>")
            continue
        if all(re.match(r"^\d+\.\s+", l) for l in p_lines):
            items = [f"<li>{_inline_fmt(re.sub(r'^\\d+\\.\\s+', '', l))}</li>" for l in p_lines]
            out_html.append("<ol>\n  " + "\n  ".join(items) + "\n</ol>")
            continue
        out_html.append(f"<p>{_inline_fmt(' '.join(p_lines))}</p>")

    return "\n      ".join(out_html)


def sync_crawlable_read_pages(catalog: dict) -> None:
    """
    Generate static crawlable HTML pages for every volume (`read/<slug>/index.html`)
    and every section/chapter (`read/<slug>/<ch-slug>.html`) with full semantic HTML,
    OpenGraph preview tags, JSON-LD structured data, and automatic reader handoff.
    """
    os.makedirs(READ_HTML_DIR, exist_ok=True)
    shared_css = (
        ":root{--bg:#faf8f5;--ink:#1c1b18;--muted:#605a52;--border:#dcd5ca;--card:#f3efe6;--accent:#92400e}"
        "body{margin:0;padding:0;background:var(--bg);color:var(--ink);font-family:'Literata',Georgia,serif;line-height:1.68;-webkit-font-smoothing:antialiased}"
        ".wrap{max-width:720px;margin:0 auto;padding:32px 22px 80px}"
        ".topbar{display:flex;justify-content:space-between;align-items:center;padding-bottom:16px;margin-bottom:28px;border-bottom:1px solid var(--border);font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px}"
        ".brand{font-weight:700;letter-spacing:.12em;color:var(--ink);text-decoration:none}"
        ".cta{background:var(--ink);color:var(--bg);padding:7px 14px;border-radius:6px;text-decoration:none;font-weight:600;font-size:12px;letter-spacing:.04em}"
        ".eyebrow{font-family:monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin-bottom:6px}"
        "h1{font-size:2rem;line-height:1.18;margin:0 0 6px}"
        "h2.sub{font-size:1.12rem;font-weight:400;font-style:italic;color:var(--muted);margin:0 0 24px}"
        ".prov-box{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin:22px 0;font-size:.92rem}"
        ".prov-label{font-family:monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:4px}"
        "p{margin:0 0 1.1em;text-align:justify}"
        "ul,ol{margin:0 0 1.1em;padding-left:1.4em}"
        "li{margin-bottom:.85em}"
        ".section-sep{text-align:center;color:var(--accent);font-weight:700;letter-spacing:.4em;margin:1.2em 0}"
        "figure.chapter-diagram{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px;margin:1.4em 0;text-align:center}"
        "figure.chapter-diagram svg{max-width:100%;height:auto}"
        "figcaption{font-family:monospace;font-size:11px;color:var(--muted);margin-top:8px}"
        ".math-block{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:12px;margin:1.2em 0;text-align:center;overflow-x:auto}"
        ".toc-list{list-style:none;padding:0;margin:24px 0}"
        ".toc-list li{border-bottom:1px solid var(--border);padding:12px 0;margin:0}"
        ".toc-list a{text-decoration:none;color:var(--ink);display:block}"
        ".toc-list .t-title{font-weight:600;font-size:1.05rem}"
        ".toc-list .t-sub{font-style:italic;color:var(--muted);font-size:.92rem;margin-top:2px}"
        ".toc-list .t-anchor{font-size:.84rem;color:var(--muted);margin-top:4px}"
        ".nav-row{display:flex;justify-content:space-between;gap:12px;margin-top:36px;padding-top:18px;border-top:1px solid var(--border);font-family:-apple-system,sans-serif;font-size:13px}"
        ".nav-row a{color:var(--ink);text-decoration:none;font-weight:600}"
    )

    for slug, entry in catalog.items():
        book_dir = os.path.join(READ_HTML_DIR, slug)
        os.makedirs(book_dir, exist_ok=True)
        _, md_path = resolve_book_md(slug)
        raw_md = open(md_path, encoding="utf-8").read()
        secs = [s.strip() for s in raw_md.split("\n---\n") if s.strip()][1:]
        chapters = entry.get("chapters", [])
        b_title = entry["title"]
        b_sub = entry["subtitle"]
        b_cat = entry.get("category", "Systems & Science")
        og_img_url = f"https://alexandria.press/assets/og/{slug}.png"
        og_img_alt = f"{b_title} — {b_sub} (Alexandria Press)"

        # 1. Generate each section/chapter page: read/<slug>/<ch_slug>.html
        for idx, ch in enumerate(chapters):
            ch_slug = ch.get("slug") or ("introduction" if idx == 0 else slugify_text(ch["title"]))
            ch["slug"] = ch_slug
            ch_title = ch["title"]
            ch_sub = ch.get("subtitle", "")
            ch_label = ch.get("label", "Introduction" if idx == 0 else f"Chapter {idx}")
            ch_anchor = ch.get("anchor", "")
            ch_exit = ch.get("exitFact", "")
            sec_md = secs[idx] if idx < len(secs) else ""
            body_html = _render_markdown_section_to_semantic_html(sec_md)

            page_url = f"https://alexandria.press/read/{slug}/{ch_slug}.html"
            reader_target = f"../../index.html#read={slug}" if idx == 0 else f"../../index.html#read={slug}&ch={idx}"
            meta_desc = f"{ch_sub} — {ch_anchor}"[:240].strip(" —")

            ld_chapter = {
                "@context": "https://schema.org",
                "@type": "Chapter",
                "name": ch_title,
                "headline": ch_sub,
                "position": idx,
                "url": page_url,
                "image": og_img_url,
                "isPartOf": {
                    "@type": "Book",
                    "name": b_title,
                    "url": f"https://alexandria.press/read/{slug}/",
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "Alexandria Press",
                    "url": "https://alexandria.press",
                },
            }

            prov_html = ""
            if idx > 0 and (ch_anchor or ch_exit):
                prov_html = (
                    f'<aside class="prov-box">'
                    f'<div class="prov-label">Primary Anchor &amp; Verified Finding</div>'
                    f'<div><strong>Historical / Experimental Grounding:</strong> {html.escape(ch_anchor)}</div>'
                    + (f'<div style="margin-top:6px"><strong>Empirical Payoff:</strong> {html.escape(ch_exit)}</div>' if ch_exit else "")
                    + "</aside>"
                )

            prev_link = (
                f'<a href="{chapters[idx - 1]["slug"]}.html">&larr; {html.escape(chapters[idx - 1]["title"])}</a>'
                if idx > 0
                else f'<a href="index.html">&larr; {html.escape(b_title)} Contents</a>'
            )
            next_link = (
                f'<a href="{chapters[idx + 1]["slug"]}.html">{html.escape(chapters[idx + 1]["title"])} &rarr;</a>'
                if idx + 1 < len(chapters)
                else '<a href="../../index.html">All Volumes &rarr;</a>'
            )

            ch_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(ch_title)} — {html.escape(b_title)} | Alexandria Press</title>
  <meta name="description" content="{html.escape(meta_desc)}">
  <meta name="author" content="Alexandria Press">
  <link rel="canonical" href="{page_url}">
  <link rel="icon" type="image/svg+xml" href="../../favicon.svg?v=3">
  <link rel="apple-touch-icon" href="../../favicon.svg?v=3">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Alexandria Press">
  <meta property="og:locale" content="en_US">
  <meta property="og:title" content="{html.escape(ch_title)} — {html.escape(b_title)}">
  <meta property="og:description" content="{html.escape(meta_desc)}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:image" content="{og_img_url}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{html.escape(og_img_alt)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@alexandriapress">
  <meta name="twitter:title" content="{html.escape(ch_title)} — {html.escape(b_title)}">
  <meta name="twitter:description" content="{html.escape(meta_desc)}">
  <meta name="twitter:image" content="{og_img_url}">
  <meta name="twitter:image:alt" content="{html.escape(og_img_alt)}">
  <script type="application/ld+json">{json.dumps(ld_chapter, ensure_ascii=False)}</script>
  <script>
  (function(){{
    var ua = navigator.userAgent || '';
    var isBot = /bot|crawl|spider|slurp|bingpreview|facebookexternalhit|twitterbot|slackbot|discordbot|linkedinbot|whatsapp|telegram|applebot|gptbot|claudebot|perplexity|bytespider/i.test(ua);
    if (!isBot && window.location.search.indexOf('static=1') === -1 && !navigator.webdriver) {{
      window.location.replace('{reader_target}');
    }}
  }})();
  </script>
  <style>{shared_css}</style>
</head>
<body>
  <div class="wrap">
    <nav class="topbar">
      <a class="brand" href="../../index.html">ALEXANDRIA.PRESS</a>
      <a class="cta" href="{reader_target}">Open in 2-Page Spread Reader &rarr;</a>
    </nav>
    <article>
      <div class="eyebrow">{html.escape(b_title)} &middot; {html.escape(ch_label)}</div>
      <h1>{html.escape(ch_title)}</h1>
      <h2 class="sub">{html.escape(ch_sub)}</h2>
      {body_html}
      {prov_html}
    </article>
    <nav class="nav-row">
      <span>{prev_link}</span>
      <span><a href="index.html">Volume Contents</a></span>
      <span>{next_link}</span>
    </nav>
  </div>
</body>
</html>
"""
            open(os.path.join(book_dir, f"{ch_slug}.html"), "w", encoding="utf-8").write(ch_html)

        # 2. Generate volume index page: read/<slug>/index.html
        book_url = f"https://alexandria.press/read/{slug}/"
        intro_html = _render_markdown_section_to_semantic_html(secs[0]) if secs else ""
        has_part_ch = [
            {
                "@type": "Chapter",
                "position": i,
                "name": c["title"],
                "headline": c.get("subtitle", ""),
                "url": f"https://alexandria.press/read/{slug}/{c['slug']}.html",
            }
            for i, c in enumerate(chapters)
        ]
        ld_book = {
            "@context": "https://schema.org",
            "@type": "Book",
            "name": b_title,
            "headline": b_sub,
            "genre": b_cat,
            "url": book_url,
            "image": og_img_url,
            "publisher": {
                "@type": "Organization",
                "name": "Alexandria Press",
                "url": "https://alexandria.press",
            },
            "hasPart": has_part_ch,
        }
        toc_items_html = []
        for i, c in enumerate(chapters):
            lbl = "Introduction" if i == 0 else f"{i}. {html.escape(c['title'])}"
            anch = f'<div class="t-anchor">{html.escape(c.get("anchor", ""))}</div>' if i > 0 and c.get("anchor") else ""
            toc_items_html.append(
                f'<li><a href="{c["slug"]}.html">'
                f'<div class="t-title">{lbl}</div>'
                f'<div class="t-sub">{html.escape(c.get("subtitle", ""))}</div>'
                f"{anch}</a></li>"
            )
        vol_desc = f"{b_sub} — Twelve-chapter illustrated monograph published by Alexandria Press."
        vol_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(b_title)} — {html.escape(b_sub)} | Alexandria Press</title>
  <meta name="description" content="{html.escape(vol_desc)}">
  <meta name="author" content="Alexandria Press">
  <link rel="canonical" href="{book_url}">
  <link rel="icon" type="image/svg+xml" href="../../favicon.svg?v=3">
  <link rel="apple-touch-icon" href="../../favicon.svg?v=3">
  <meta property="og:type" content="book">
  <meta property="og:site_name" content="Alexandria Press">
  <meta property="og:locale" content="en_US">
  <meta property="og:title" content="{html.escape(b_title)} — {html.escape(b_sub)}">
  <meta property="og:description" content="{html.escape(vol_desc)}">
  <meta property="og:url" content="{book_url}">
  <meta property="og:image" content="{og_img_url}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{html.escape(og_img_alt)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@alexandriapress">
  <meta name="twitter:title" content="{html.escape(b_title)} — {html.escape(b_sub)}">
  <meta name="twitter:description" content="{html.escape(vol_desc)}">
  <meta name="twitter:image" content="{og_img_url}">
  <meta name="twitter:image:alt" content="{html.escape(og_img_alt)}">
  <script type="application/ld+json">{json.dumps(ld_book, ensure_ascii=False)}</script>
  <script>
  (function(){{
    var ua = navigator.userAgent || '';
    var isBot = /bot|crawl|spider|slurp|bingpreview|facebookexternalhit|twitterbot|slackbot|discordbot|linkedinbot|whatsapp|telegram|applebot|gptbot|claudebot|perplexity|bytespider/i.test(ua);
    if (!isBot && window.location.search.indexOf('static=1') === -1 && !navigator.webdriver) {{
      var h = (window.location.hash || '').replace(/^#/, '');
      var extra = h ? ('&' + h) : '';
      window.location.replace('../../index.html#read={slug}' + extra);
    }}
  }})();
  </script>
  <style>{shared_css}</style>
</head>
<body>
  <div class="wrap">
    <nav class="topbar">
      <a class="brand" href="../../index.html">ALEXANDRIA.PRESS</a>
      <a class="cta" href="../../index.html#read={slug}">Open Interactive 2-Page Spread Reader &rarr;</a>
    </nav>
    <header>
      <div class="eyebrow">{html.escape(b_cat)}</div>
      <h1>{html.escape(b_title)}</h1>
      <h2 class="sub">{html.escape(b_sub)}</h2>
    </header>
    <section>
      {intro_html}
    </section>
    <section>
      <div class="eyebrow" style="margin-top:28px">Contents &amp; Provenance Ledger (12 Chapters)</div>
      <ul class="toc-list">
        {"".join(toc_items_html)}
      </ul>
    </section>
  </div>
</body>
</html>
"""
        open(os.path.join(book_dir, "index.html"), "w", encoding="utf-8").write(vol_html)


def _escape_typst_str(s: str) -> str:
    return (
        (s or "")
        .replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("$", "\\$")
        .replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("<", "\\<")
        .replace(">", "\\>")
        .replace("@", "\\@")
    )


def generate_book_og_png(slug: str, entry: dict, force: bool = False) -> str:
    """Render a 1200x630 PNG OpenGraph social card (`assets/og/<slug>.png`) via Typst."""
    os.makedirs(OG_DIR, exist_ok=True)
    out_png = os.path.join(OG_DIR, f"{slug}.png")
    thumb_file = os.path.join(THUMBS_DIR, f"{slug}.svg")
    if not os.path.exists(thumb_file):
        sync_thumbs_from_covers()
    if (
        not force
        and os.path.exists(out_png)
        and os.path.getsize(out_png) > 10_000
        and os.path.getmtime(out_png) >= os.path.getmtime(thumb_file)
    ):
        return out_png

    font_dir = os.path.join(BASE_DIR, "fonts")
    cat_esc = _escape_typst_str(entry.get("category", "Systems & Science").upper())
    title_esc = _escape_typst_str(entry["title"])
    sub_esc = _escape_typst_str(entry["subtitle"])
    title_pt = "24pt" if len(entry["title"]) > 22 else "28pt"

    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "thumb.svg"), "w", encoding="utf-8").write(
            open(thumb_file, encoding="utf-8").read()
        )
        typ_path = os.path.join(td, "card.typ")
        typ_code = f"""#set page(width: 600pt, height: 315pt, margin: 0pt, fill: rgb("#faf8f5"))
#set text(font: "Literata", fill: rgb("#1c1917"), lang: "en")

#place(top + left, dx: 12pt, dy: 12pt)[
  #rect(width: 576pt, height: 291pt, radius: 12pt, stroke: 1pt + rgb("#e4ded2"), fill: rgb("#faf8f5"))
]

#place(top + left, dx: 30pt, dy: 30pt)[
  #box(width: 255pt, height: 255pt, radius: 10pt, clip: true, stroke: 1pt + rgb("#dcd5ca"))[
    #image("thumb.svg", width: 255pt, height: 255pt)
  ]
]

#place(top + left, dx: 310pt, dy: 34pt)[
  #block(width: 254pt, height: 247pt)[
    #text(font: "IBM Plex Mono", size: 8.5pt, tracking: 1.6pt, weight: "medium", fill: rgb("#9a6b2f"))[{cat_esc}]
    #v(1fr)
    #set par(leading: 0.35em)
    #text(font: "Literata", size: {title_pt}, weight: "bold", fill: rgb("#1c1917"))[{title_esc}]
    #v(10pt)
    #set par(leading: 0.48em)
    #text(font: "Literata", size: 14pt, style: "italic", fill: rgb("#4a453e"))[{sub_esc}]
    #v(1fr)
    #line(length: 100%, stroke: 0.75pt + rgb("#e4ded2"))
    #v(10pt)
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      [#text(font: "IBM Plex Mono", size: 8pt, tracking: 1.4pt, weight: "medium", fill: rgb("#1c1917"))[ALEXANDRIA.PRESS]],
      [#text(font: "IBM Plex Mono", size: 7.5pt, tracking: 1.1pt, fill: rgb("#78716c"))[12 CHAPTERS]]
    )
  ]
]
"""
        open(typ_path, "w", encoding="utf-8").write(typ_code)
        subprocess.run(
            ["typst", "compile", "--font-path", font_dir, "--ppi", "144", typ_path, out_png],
            check=True,
        )
    return out_png


def generate_app_og_png(catalog: dict, force: bool = False) -> str:
    """Render the 1200x630 PNG OpenGraph social card (`og-image.png`) for the Alexandria Press app."""
    out_png = os.path.join(BASE_DIR, "og-image.png")
    fav_path = os.path.join(BASE_DIR, "favicon.svg")
    if not force and os.path.exists(out_png) and os.path.getsize(out_png) > 10_000:
        return out_png

    font_dir = os.path.join(BASE_DIR, "fonts")
    preferred = [
        "non-linear-engines",
        "latent-fragility",
        "singular-minds",
        "elemental-asymmetries",
        "architectures-of-choice",
        "instruments-of-precision",
        "planetary-triggers",
        "entropy",
    ]
    sample_slugs = [s for s in preferred if os.path.exists(os.path.join(THUMBS_DIR, f"{s}.svg"))]
    if len(sample_slugs) < 8:
        for s in catalog:
            if s not in sample_slugs and os.path.exists(os.path.join(THUMBS_DIR, f"{s}.svg")):
                sample_slugs.append(s)
            if len(sample_slugs) == 8:
                break

    with tempfile.TemporaryDirectory() as td:
        for i, s in enumerate(sample_slugs):
            open(os.path.join(td, f"t{i}.svg"), "w", encoding="utf-8").write(
                open(os.path.join(THUMBS_DIR, f"{s}.svg"), encoding="utf-8").read()
            )
        open(os.path.join(td, "fav.svg"), "w", encoding="utf-8").write(
            open(fav_path, encoding="utf-8").read()
        )
        tiles_code = ",\n      ".join(
            [
                f'box(width: 56pt, height: 56pt, radius: 6pt, clip: true, stroke: 0.75pt + rgb("#dcd5ca"))[#image("t{i}.svg", width: 56pt, height: 56pt)]'
                for i in range(len(sample_slugs))
            ]
        )
        app_typ = os.path.join(td, "app.typ")
        app_code = f"""#set page(width: 600pt, height: 315pt, margin: 0pt, fill: rgb("#faf8f5"))
#set text(font: "Literata", fill: rgb("#1c1917"), lang: "en")

#place(top + left, dx: 12pt, dy: 12pt)[
  #rect(width: 576pt, height: 291pt, radius: 12pt, stroke: 1pt + rgb("#e4ded2"), fill: rgb("#faf8f5"))
]

#place(top + left, dx: 36pt, dy: 34pt)[
  #block(width: 528pt, height: 247pt)[
    #grid(
      columns: (auto, 1fr),
      column-gutter: 12pt,
      align: horizon,
      [#image("fav.svg", width: 32pt, height: 32pt)],
      [#text(font: "IBM Plex Mono", size: 9.5pt, tracking: 2.0pt, weight: "medium", fill: rgb("#1c1917"))[ALEXANDRIA.PRESS]]
    )
    #v(1fr)
    #set par(leading: 0.42em)
    #text(font: "Literata", size: 28pt, weight: "bold", fill: rgb("#1c1917"))[Deep Learning for Humans.\\ Distilled by Frontier AI.]
    #v(1fr)
    #line(length: 100%, stroke: 0.75pt + rgb("#e4ded2"))
    #v(12pt)
    #grid(
      columns: (1fr,) * {len(sample_slugs)},
      column-gutter: 10pt,
      align: center,
      {tiles_code}
    )
  ]
]
"""
        open(app_typ, "w", encoding="utf-8").write(app_code)
        subprocess.run(
            ["typst", "compile", "--font-path", font_dir, "--ppi", "144", app_typ, out_png],
            check=True,
        )
    return out_png


def sync_all_og_images(catalog: dict, force: bool = False) -> None:
    """Ensure `og-image.png` and all `assets/og/<slug>.png` (1200x630 PNG) exist."""
    generate_app_og_png(catalog, force=force)
    for slug, entry in catalog.items():
        generate_book_og_png(slug, entry, force=force)


def sync_index_and_sitemap_from_catalog(catalog: dict) -> None:
    """
    Deterministically regenerate the `<!-- BEGIN:JSON_LD -->` and `<!-- BEGIN:CATALOG_GRID -->`
    sections of `index.html`, 1200x630 PNG OG images, static crawlable `read/<slug>/` HTML pages, and `sitemap.xml`.
    """
    sync_all_og_images(catalog)
    sync_crawlable_read_pages(catalog)
    index_html = open(INDEX_HTML_PATH, encoding="utf-8").read()

    # 1. Regenerate JSON-LD block
    has_part = []
    for slug, entry in catalog.items():
        has_part.append(
            {
                "@type": "Book",
                "name": entry["title"],
                "headline": entry["subtitle"],
                "url": f"https://alexandria.press/read/{slug}/",
                "image": f"https://alexandria.press/assets/og/{slug}.png",
            }
        )
    ld_obj = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Alexandria Press",
        "url": "https://alexandria.press",
        "description": "Deep Learning for Humans. Distilled by Frontier AI.",
        "publisher": {
            "@type": "Organization",
            "name": "Alexandria Press",
            "url": "https://alexandria.press",
            "logo": "https://alexandria.press/favicon.svg",
        },
        "hasPart": has_part,
    }
    ld_json_str = "\n".join("    " + line for line in json.dumps(ld_obj, indent=2, ensure_ascii=False).splitlines())
    ld_block = (
        "<!-- BEGIN:JSON_LD -->\n"
        '    <script type="application/ld+json">\n'
        f"{ld_json_str}\n"
        "    </script>\n"
        "    <!-- END:JSON_LD -->"
    )
    index_html = re.sub(
        r"<!-- BEGIN:JSON_LD -->[\s\S]*?<!-- END:JSON_LD -->",
        lambda _: ld_block,
        index_html,
        count=1,
    )

    # 2. Regenerate Catalog Grid block with crawlable hrefs and data-format attributes
    cards_html = []
    for slug, entry in catalog.items():
        esc_title = html.escape(entry["title"])
        esc_sub = html.escape(entry["subtitle"])
        esc_cat = html.escape(entry.get("category", "Systems & Science"))
        fmt = entry.get("format") or infer_book_format(slug, entry.get("mode", "facet"))
        cards_html.append(
            f'                <a class="book-card" href="read/{slug}/index.html" data-key="{slug}" data-format="{fmt}" data-title="{esc_title}" data-subtitle="{esc_sub}" data-category="{esc_cat}" onclick="if(!event.metaKey &amp;&amp; !event.ctrlKey &amp;&amp; !event.shiftKey &amp;&amp; event.button === 0){{event.preventDefault(); openBookFromCatalog(\'{slug}\');}}" title="{esc_title} — {esc_sub}">\n'
            f'                    <div class="book-cover-frame">\n'
            f'                        <img src="assets/covers/thumbs/{slug}.svg" alt="{esc_title}" loading="eager">\n'
            f'                    </div>\n'
            f'                    <div class="book-card-info">\n'
            f'                        <div class="book-card-title">{esc_title}</div>\n'
            f'                        <div class="book-card-subtitle">{esc_sub}</div>\n'
            f'                    </div>\n'
            f"                </a>"
        )
    grid_block = (
        "<!-- BEGIN:CATALOG_GRID -->\n"
        + "\n".join(cards_html)
        + "\n                <!-- END:CATALOG_GRID -->"
    )
    index_html = re.sub(
        r"<!-- BEGIN:CATALOG_GRID -->[\s\S]*?<!-- END:CATALOG_GRID -->",
        lambda _: grid_block,
        index_html,
        count=1,
    )

    open(INDEX_HTML_PATH, "w", encoding="utf-8").write(index_html)

    # 3. Regenerate sitemap.xml (root + all 34 books + all 442 section/chapter pages)
    today = datetime.date.today().isoformat()
    smap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "  <url>",
        "    <loc>https://alexandria.press/</loc>",
        f"    <lastmod>{today}</lastmod>",
        "    <changefreq>daily</changefreq>",
        "    <priority>1.0</priority>",
        "  </url>",
    ]
    for slug, entry in catalog.items():
        smap_lines.extend(
            [
                "  <url>",
                f"    <loc>https://alexandria.press/read/{slug}/</loc>",
                f"    <lastmod>{today}</lastmod>",
                "    <changefreq>weekly</changefreq>",
                "    <priority>0.9</priority>",
                "  </url>",
            ]
        )
        for ch in entry.get("chapters", []):
            ch_slug = ch.get("slug") or slugify_text(ch["title"])
            smap_lines.extend(
                [
                    "  <url>",
                    f"    <loc>https://alexandria.press/read/{slug}/{ch_slug}.html</loc>",
                    f"    <lastmod>{today}</lastmod>",
                    "    <changefreq>monthly</changefreq>",
                    "    <priority>0.8</priority>",
                    "  </url>",
                ]
            )
    smap_lines.append("</urlset>\n")
    open(SITEMAP_PATH, "w", encoding="utf-8").write("\n".join(smap_lines))


def publish_single_volume(
    catalog: dict,
    slug: str,
    category: str = None,
    accent: str = None,
    bg: str = None,
    theme: str = "lattice",
    regenerate_cover: bool = False,
    force_recompile: bool = True,
) -> dict:
    """Validate, generate cover + thumb, compile 3 Typst PDFs, and update catalog entry for `slug`."""
    from compile_typst import compile_book_to_pdf

    slug, md_path = resolve_book_md(slug)
    existing = catalog.get(slug, {})

    dossier_meta = {}
    dossier_path = os.path.join(DOSSIERS_DIR, f"{slug}.json")
    if os.path.exists(dossier_path):
        try:
            dossier_meta = json.load(open(dossier_path, encoding="utf-8"))
        except Exception:
            pass

    use_legacy = slug in LEGACY_SLUGS
    errs, warns, info = validate_book(md_path, legacy=use_legacy)
    if errs:
        print(f"[ABORT] {md_path} failed quality gates ({len(errs)} error(s)):")
        for e in errs:
            print("  ERROR:", e)
        sys.exit(1)

    for w in warns:
        print("  WARN:", w)

    md_text = open(md_path, encoding="utf-8").read()
    title, subtitle, chapters = extract_book_metadata(md_text, dossier_meta)

    eff_cat = category or existing.get("category") or dossier_meta.get("category") or "Systems & Science"
    eff_accent = accent or existing.get("accent") or dossier_meta.get("accent") or "#d97706"
    eff_bg = bg or existing.get("bg") or dossier_meta.get("bg") or "#1c1917"
    eff_mode = dossier_meta.get("mode") or existing.get("mode") or "facet"
    eff_format = infer_book_format(slug, eff_mode)
    eff_profile = existing.get("profile") or dossier_meta.get("profile") or "A"

    cover_file = os.path.join(COVERS_DIR, f"{slug}.svg")
    if not os.path.exists(cover_file) or regenerate_cover:
        generate_cover_svg(slug, title, subtitle, eff_cat, eff_accent, eff_bg, theme)
        print(f"[COVER] Generated vector cover: assets/covers/{slug}.svg")
    else:
        refresh_existing_pdf_cover_typography(slug, title, subtitle)

    pdf_path = os.path.join(PDFS_DIR, f"{slug}.pdf")
    comp_path = os.path.join(PDFS_DIR, f"{slug}-compact.pdf")
    mob_path = os.path.join(PDFS_DIR, f"{slug}-mobile.pdf")
    needs_compile = (
        force_recompile
        or not os.path.exists(pdf_path)
        or not os.path.exists(comp_path)
        or not os.path.exists(mob_path)
        or os.path.getmtime(md_path) > os.path.getmtime(pdf_path)
        or (os.path.exists(cover_file) and os.path.getmtime(cover_file) > os.path.getmtime(pdf_path))
        or not existing.get("sectionPages")
        or not existing.get("compactSectionPages")
        or not existing.get("mobileSectionPages")
    )

    if needs_compile:
        pdf_path, sec_pages, comp_path, comp_pages, mob_path, mob_pages = compile_book_to_pdf(
            md_path, category=eff_cat, accent_hex=eff_accent
        )
    else:
        sec_pages = existing["sectionPages"]
        comp_pages = existing["compactSectionPages"]
        mob_pages = existing["mobileSectionPages"]

    catalog[slug] = {
        "slug": slug,
        "file": f"books/{slug}.md",
        "title": title,
        "subtitle": subtitle,
        "category": eff_cat,
        "mode": eff_mode,
        "format": eff_format,
        "profile": eff_profile,
        "accent": eff_accent,
        "bg": eff_bg,
        "pdf": f"assets/pdfs/{slug}.pdf",
        "compactPdf": f"assets/pdfs/{slug}-compact.pdf",
        "mobilePdf": f"assets/pdfs/{slug}-mobile.pdf",
        "sectionPages": sec_pages,
        "compactSectionPages": comp_pages,
        "mobileSectionPages": mob_pages,
        "chapters": chapters,
    }
    return info


def main():
    parser = argparse.ArgumentParser(description="Publish or sync Alexandria Press books.")
    parser.add_argument("--list-anchors", action="store_true", help="List all existing books and chapters")
    parser.add_argument("--sync-all", action="store_true", help="Validate and sync all catalog books into js/books-data.js and index.html")
    parser.add_argument("--batch", type=int, help="Publish all books in batch N of backlog.json")
    parser.add_argument("--slug", help="Hyphenated book slug (e.g. the-cell)")
    parser.add_argument("--category", default=None, help="Book category label")
    parser.add_argument("--accent", default=None, help="Hex accent color for cover")
    parser.add_argument("--bg", default=None, help="Hex background color for cover")
    parser.add_argument("--theme", default="lattice", help="Cover geometric emblem")
    parser.add_argument("--regenerate-cover", action="store_true", help="Force regenerate SVG cover")
    parser.add_argument("--recompile", action="store_true", help="Force recompile all PDFs during --sync-all")
    args = parser.parse_args()

    if args.list_anchors:
        list_existing_anchors()
        return

    catalog = load_catalog()

    if args.sync_all:
        for slug in list(catalog.keys()):
            publish_single_volume(
                catalog,
                slug=slug,
                regenerate_cover=args.regenerate_cover,
                force_recompile=args.recompile,
            )
            pdf_path = os.path.join(PDFS_DIR, f"{slug}.pdf")
            comp_path = os.path.join(PDFS_DIR, f"{slug}-compact.pdf")
            mob_path = os.path.join(PDFS_DIR, f"{slug}-mobile.pdf")
            print(
                f"[SYNCED] {slug:26s} -> {len(catalog[slug]['chapters'])} sections | "
                f"Desktop: {os.path.getsize(pdf_path)//1024} KB | "
                f"Compact: {os.path.getsize(comp_path)//1024} KB | "
                f"Mobile: {os.path.getsize(mob_path)//1024} KB"
            )
        save_catalog(catalog)
        write_books_js_from_catalog(catalog)
        sync_thumbs_from_covers()
        sync_index_and_sitemap_from_catalog(catalog)
        print(f"Successfully synced all {len(catalog)} volumes into catalog.json, js/books-data.js, read/*, index.html, and sitemap.xml.")
        return

    if args.batch is not None:
        backlog = load_backlog()
        batch_books = [b for b in backlog.get("books", []) if b.get("batch") == args.batch]
        if not batch_books:
            print(f"[ERROR] No books found for batch {args.batch} in backlog.json.")
            sys.exit(1)
        for b in batch_books:
            b_slug = b["slug"]
            info = publish_single_volume(
                catalog,
                slug=b_slug,
                category=b.get("category"),
                accent=b.get("accent"),
                bg=b.get("bg"),
                regenerate_cover=args.regenerate_cover,
                force_recompile=True,
            )
            b["status"] = "published"
            entry = catalog[b_slug]
            print(
                f"[PUBLISHED] '{entry['title']}: {entry['subtitle']}' ({b_slug}) | "
                f"{info['chapters']} chapters | {info['total_words']:,} words"
            )
        save_backlog(backlog)
        save_catalog(catalog)
        write_books_js_from_catalog(catalog)
        sync_thumbs_from_covers()
        sync_index_and_sitemap_from_catalog(catalog)
        return

    if not args.slug:
        parser.print_help()
        sys.exit(1)

    slug = normalize_slug(args.slug)
    info = publish_single_volume(
        catalog,
        slug=slug,
        category=args.category,
        accent=args.accent,
        bg=args.bg,
        theme=args.theme,
        regenerate_cover=args.regenerate_cover,
        force_recompile=True,
    )
    save_catalog(catalog)
    write_books_js_from_catalog(catalog)
    sync_thumbs_from_covers()
    sync_index_and_sitemap_from_catalog(catalog)
    entry = catalog[slug]
    print(
        f"[PUBLISHED] '{entry['title']}: {entry['subtitle']}' ({slug}) | "
        f"{info['chapters']} chapters | {info['total_words']:,} words"
    )


if __name__ == "__main__":
    main()

