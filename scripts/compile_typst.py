#!/usr/bin/env python3
"""
Alexandria Press — Deterministic Typst PDF Compiler (scripts/compile_typst.py)

Compiles Alexandria Press markdown manuscripts (.md) into print- and screen-ready
Typst PDFs (assets/pdfs/<slug>.pdf) and returns exact chapter starting page numbers
via `typst query`.

Usage:
    python3 scripts/compile_typst.py flights_and_perches.md
    python3 scripts/compile_typst.py --all
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_OUT_DIR = os.path.join(BASE_DIR, "assets", "pdfs")


def load_books_metadata():
    books_js_path = os.path.join(BASE_DIR, "js", "books-data.js")
    if not os.path.exists(books_js_path):
        return {}
    books_js = open(books_js_path, encoding="utf-8").read()
    p_end = books_js.find("return {") + len("return ")
    s_start = books_js.rfind("};") + 1
    return json.loads(books_js[p_end:s_start])


def clean_latex_for_mitex(latex_str: str) -> str:
    s = latex_str.strip()
    # Replace unicode symbols with standard LaTeX commands
    s = s.replace("·", r" \cdot ")
    s = s.replace("×", r" \times ")
    s = s.replace("∝", r" \propto ")
    s = s.replace("⇒", r" \implies ")
    s = s.replace("→", r" \to ")
    s = s.replace("−", "-")
    s = re.sub(r"√\s*([a-zA-Z0-9_{}]+)", r"\\sqrt{\1}", s)
    s = s.replace("√", r"\sqrt")
    # mitex handles standard \sum, so strip \nolimits if followed by _
    s = s.replace(r"\nolimits", "")
    # Replace \xrightarrow{...} with \stackrel{...}{\longrightarrow} for mitex compatibility
    s = re.sub(r"\\xrightarrow\{([^}]*)\}", r"\\stackrel{\1}{\\longrightarrow}", s)
    s = re.sub(r"\\xleftarrow\{([^}]*)\}", r"\\stackrel{\1}{\\longleftarrow}", s)
    return s


def auto_fit_svg_boxes(svg_str: str) -> str:
    """
    Expands <rect> label boxes in schematic SVG diagrams so enclosed <text>
    always has >= 28px horizontal padding, and trims connecting <line> endpoints.
    """
    try:
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        root = ET.fromstring(svg_str)
    except Exception:
        return svg_str

    rects = []
    texts = []
    lines = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "rect":
            try:
                rx = float(el.attrib.get("x", "0"))
                ry = float(el.attrib.get("y", "0"))
                rw = float(el.attrib.get("width", "0"))
                rh = float(el.attrib.get("height", "0"))
                if rw >= 24 and 16 <= rh <= 95:
                    rects.append({"el": el, "x": rx, "y": ry, "w": rw, "h": rh})
            except ValueError:
                pass
        elif tag == "text":
            txt = "".join(el.itertext()).strip()
            if not txt:
                continue
            try:
                tx = float(el.attrib.get("x", "0"))
                ty = float(el.attrib.get("y", "0"))
                fs = float(re.sub(r"[^0-9.]", "", el.attrib.get("font-size", "12")) or "12")
                ff = el.attrib.get("font-family", "").lower()
                cf = 0.65 if "mono" in ff else (0.64 if txt.isupper() else 0.58)
                tw = len(txt) * fs * cf
                texts.append({"x": tx, "y": ty, "w": tw, "txt": txt})
            except ValueError:
                pass
        elif tag == "line":
            try:
                lines.append(
                    {
                        "el": el,
                        "x1": float(el.attrib.get("x1", "0")),
                        "y1": float(el.attrib.get("y1", "0")),
                        "x2": float(el.attrib.get("x2", "0")),
                        "y2": float(el.attrib.get("y2", "0")),
                    }
                )
            except ValueError:
                pass

    for r in rects:
        rx0, ry0, rx1, ry1 = r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]
        inside_w = 0.0
        for t in texts:
            if rx0 - 2 <= t["x"] <= rx1 + 2 and ry0 <= t["y"] <= ry1 + 2:
                inside_w = max(inside_w, t["w"])
        req_w = inside_w + 28.0
        if req_w > r["w"]:
            cx = rx0 + r["w"] / 2.0
            max_w = r["w"] + 80.0
            for o in rects:
                if o is r:
                    continue
                if min(ry1, o["y"] + o["h"]) - max(ry0, o["y"]) > 0:
                    ocx = o["x"] + o["w"] / 2.0
                    dist = abs(cx - ocx) - o["w"] / 2.0 - 10.0
                    if dist * 2.0 < max_w:
                        max_w = dist * 2.0
            new_w = round(min(req_w, max(r["w"], max_w)), 1)
            if new_w > r["w"]:
                new_x = round(max(4.0, min(600.0 - 4.0 - new_w, cx - new_w / 2.0)), 1)
                new_rx1 = new_x + new_w
                for ln in lines:
                    if abs(ln["y1"] - ln["y2"]) < 2.0 and ry0 <= ln["y1"] <= ry1:
                        if abs(ln["x1"] - rx1) <= 8.0 and ln["x2"] > ln["x1"]:
                            ln["el"].set("x1", str(round(new_rx1 + 2.0, 1)))
                        elif abs(ln["x2"] - rx0) <= 8.0 and ln["x2"] > ln["x1"]:
                            ln["el"].set("x2", str(round(new_x - 2.0, 1)))
                r["el"].set("x", str(new_x))
                r["el"].set("width", str(new_w))
                r["x"], r["w"] = new_x, new_w

    return ET.tostring(root, encoding="unicode")


def prepare_svg_for_typst(svg_raw: str, accent_hex: str = "#a37c40") -> tuple[str, str]:
    """
    Extracts data-caption, resolves CSS variables to concrete print/reader colors,
    and ensures <rect> boxes are wide enough for their enclosed <text> labels.
    """
    caption = ""
    m_cap = re.search(r'data-caption\s*=\s*"([^"]*)"', svg_raw)
    if m_cap:
        caption = m_cap.group(1).strip()

    svg_clean = svg_raw
    replacements = {
        "var(--text-color)": "#1c1b18",
        "var(--text-muted)": "#605a52",
        "var(--accent-color)": accent_hex,
        "var(--border-color)": "#d4cdc3",
        "var(--card-bg)": "#f3efe6",
        "var(--bg-color)": "#faf8f5",
        "var(--font-sans)": "Inter, Helvetica Neue, Arial, sans-serif",
        "var(--font-mono)": "IBM Plex Mono, Courier New, monospace",
        "var(--font-serif)": "Literata, Georgia, serif",
    }
    for k, v in replacements.items():
        svg_clean = svg_clean.replace(k, v)

    # Ensure root <svg> has xmlns
    if "xmlns=" not in svg_clean:
        svg_clean = svg_clean.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)

    svg_clean = auto_fit_svg_boxes(svg_clean)
    return svg_clean, caption


def escape_typst_text(s: str) -> str:
    """Escapes special Typst markup characters in plain text spans."""
    s = s.replace("\\$", "$")
    # Glue em-dashes to preceding character with word-joiner so em-dashes never start a new line
    s = re.sub(r"(\S)—", "\\1\u2060—", s)
    out = []
    for ch in s:
        if ch in ("\\", "#", "*", "_", "`", "$", "@", "<", ">", "~", "^"):
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def convert_inline_markdown_to_typst(text: str) -> str:
    """
    Converts inline markdown (**bold**, *italic*, `code`, and $inline math$)
    into valid Typst markup.
    """
    # Protect escaped dollar signs first
    text = text.replace("\\$", "\x00ESCDOLLAR\x00")
    # Protect legitimate currency like $10 million
    text = re.sub(
        r"\$(?=\d[\d,]*(?:\.\d+)?\s*(?:million|billion|trillion|thousand|hundred|per\s+share)\b)",
        "\x00ESCDOLLAR\x00",
        text,
        flags=re.IGNORECASE,
    )

    tokens = []

    def save_token(typst_expr: str) -> str:
        idx = len(tokens)
        tokens.append(typst_expr)
        return f"\x01TOK{idx}\x01"

    # 1. Inline code `...`
    def repl_code(m):
        code_txt = m.group(1).replace('"', '\\"')
        return save_token(f'#raw("{code_txt}")')

    text = re.sub(r"`([^`\n]+)`", repl_code, text)

    # 2. Inline math $...$
    def repl_math(m):
        raw_m = m.group(1).replace("\x00ESCDOLLAR\x00", r"\$")
        cleaned = clean_latex_for_mitex(raw_m).replace("\\", "\\\\").replace('"', '\\"')
        return save_token(f'#mi("{cleaned}")')

    text = re.sub(r"\$([^\s$](?:[^$\n]*?[^\s$])?)\$", repl_math, text)

    # 3. Bold+Italic ***...***
    def repl_bold_italic(m):
        return save_token(f"#strong[#emph[{escape_typst_with_tokens(m.group(1))}]]")

    def escape_typst_with_tokens(s: str) -> str:
        parts = re.split(r"(\x01TOK\d+\x01)", s)
        res = []
        for p in parts:
            if re.match(r"^\x01TOK\d+\x01$", p):
                res.append(p)
            else:
                res.append(escape_typst_text(p))
        return "".join(res)

    text = re.sub(r"\*\*\*([^\*\n]+)\*\*\*", repl_bold_italic, text)

    # 4. Bold **...**
    def repl_bold(m):
        return save_token(f"#strong[{escape_typst_with_tokens(m.group(1))}]")

    text = re.sub(r"\*\*([^\*\n]+)\*\*", repl_bold, text)

    # 5. Italic *...*
    def repl_italic(m):
        return save_token(f"#emph[{escape_typst_with_tokens(m.group(1))}]")

    text = re.sub(r"\*([^\*\n]+)\*", repl_italic, text)

    # Restore escaped dollars as plain $ before escaping Typst characters
    text = text.replace("\x00ESCDOLLAR\x00", "$")

    out = escape_typst_with_tokens(text)
    # Expand all tokens (including nested tokens inside bold/italic)
    for _ in range(4):
        if "\x01TOK" not in out:
            break
        out = re.sub(r"\x01TOK(\d+)\x01", lambda m: tokens[int(m.group(1))], out)
    return out


def convert_body_to_typst(body: str, temp_dir: str, sec_idx: int, accent_hex: str) -> str:
    """Converts a chapter/introduction markdown body into Typst blocks."""
    blocks = []

    def save_block(b_str: str) -> str:
        idx = len(blocks)
        blocks.append(b_str)
        return f"\n\n@@BLOCK_{idx}@@\n\n"

    # 1. Fenced SVG diagrams
    def repl_svg(m):
        svg_raw = m.group(1).strip()
        svg_clean, caption = prepare_svg_for_typst(svg_raw, accent_hex)
        svg_filename = f"diag_{sec_idx}_{len(blocks)}.svg"
        svg_path = os.path.join(temp_dir, svg_filename)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_clean)
        cap_typst = ""
        if caption:
            cap_escaped = convert_inline_markdown_to_typst(caption)
            cap_typst = f'\n  #v(4pt)\n  #align(center)[#text(font: "IBM Plex Mono", size: 6.8pt, tracking: 0.4pt, fill: rgb("#605a52"))[{cap_escaped}]]'
        return save_block(
            f'#v(5pt)\n#block(breakable: false, width: 100%, inset: (x: 8pt, y: 8pt), radius: 3pt, stroke: 0.5pt + rgb("#dcd5ca"), fill: rgb("#f6f2ea"))[\n  #align(center)[#image("{svg_filename}", width: 98%)]{cap_typst}\n]\n#v(5pt)'
        )

    body = re.sub(r"```(?:svg|diagram)\s*\n([\s\S]*?)```", repl_svg, body, flags=re.IGNORECASE)

    # 2. Display math $$...$$ (centered and vertically spaced, no quote box)
    def repl_disp_math(m):
        eq_raw = m.group(1).strip()
        cleaned = clean_latex_for_mitex(eq_raw).replace("\\", "\\\\").replace('"', '\\"')
        return save_block(
            f'#v(6pt)\n#block(breakable: false, width: 100%, inset: (y: 4pt))[\n  #align(center)[#mitex("{cleaned}")]\n]\n#v(6pt)'
        )

    body = re.sub(r"\$\$([\s\S]*?)\$\$", repl_disp_math, body)

    # Split remaining body into paragraphs / list groups
    raw_paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    out_typ = []

    for para in raw_paras:
        m_blk = re.match(r"^@@BLOCK_(\d+)@@$", para)
        if m_blk:
            out_typ.append(blocks[int(m_blk.group(1))])
            continue

        lines = [l.strip() for l in para.splitlines() if l.strip()]
        if not lines:
            continue

        # Check if blockquote
        if all(l.startswith(">") for l in lines):
            q_text = " ".join(re.sub(r"^>\s*", "", l) for l in lines)
            q_typ = convert_inline_markdown_to_typst(q_text)
            out_typ.append(
                f'#block(inset: (left: 12pt, y: 4pt), stroke: (left: 1.5pt + rgb("{accent_hex}")))[\n  #text(style: "italic", fill: rgb("#3d3934"))[{q_typ}]\n]'
            )
            continue

        # Check if bullet list or numbered list
        if all(re.match(r"^([*\-]|\d+\.)\s+", l) for l in lines):
            list_items = []
            for l in lines:
                m_ul = re.match(r"^[*\-]\s+(.*)", l)
                m_ol = re.match(r"^\d+\.\s+(.*)", l)
                if m_ul:
                    list_items.append(f"- {convert_inline_markdown_to_typst(m_ul.group(1))}")
                elif m_ol:
                    list_items.append(f"+ {convert_inline_markdown_to_typst(m_ol.group(1))}")
            out_typ.append("#block(inset: (left: 4pt, y: 1pt))[\n" + "\n".join(list_items) + "\n]")
            continue

        # Otherwise normal paragraph (possibly mixed with trailing list lines)
        para_lines = []
        list_lines = []
        for l in lines:
            if re.match(r"^([*\-]|\d+\.)\s+", l):
                list_lines.append(l)
            else:
                if list_lines:
                    para_lines.append("\n".join(list_lines))
                    list_lines = []
                para_lines.append(l)
        if list_lines:
            para_text = " ".join(para_lines)
            if para_text:
                out_typ.append(convert_inline_markdown_to_typst(para_text))
            items = []
            for l in list_lines:
                m_ul = re.match(r"^[*\-]\s+(.*)", l)
                m_ol = re.match(r"^\d+\.\s+(.*)", l)
                if m_ul:
                    items.append(f"- {convert_inline_markdown_to_typst(m_ul.group(1))}")
                elif m_ol:
                    items.append(f"+ {convert_inline_markdown_to_typst(m_ol.group(1))}")
            out_typ.append("\n".join(items))
        else:
            joined = " ".join(lines)
            out_typ.append(convert_inline_markdown_to_typst(joined))

    return "\n\n".join(out_typ)


def parse_book_markdown(md_text: str):
    sections = [s.strip() for s in md_text.split("\n---\n") if s.strip()]
    title_lines = [l.strip() for l in sections[0].splitlines() if l.strip()]
    book_title = title_lines[0].lstrip("#").strip() if title_lines else "Untitled"
    book_subtitle = title_lines[1].lstrip("#").strip() if len(title_lines) > 1 else ""

    parsed_sections = []
    for idx, sec in enumerate(sections[1:]):
        sec_lines = sec.splitlines()
        headers = []
        header_end_line = 0
        for line_i, l in enumerate(sec_lines):
            if l.strip().startswith("#"):
                headers.append(l.strip().lstrip("#").strip())
                if len(headers) == 3:
                    header_end_line = line_i + 1
                    break
        while len(headers) < 3:
            headers.append("")
        body = "\n".join(sec_lines[header_end_line:]).strip()
        parsed_sections.append(
            {
                "index": idx,
                "label": headers[0],
                "title": headers[1],
                "subtitle": headers[2],
                "body": body,
            }
        )
    return book_title, book_subtitle, parsed_sections


def build_typ_source(
    book_title: str,
    book_subtitle: str,
    category: str,
    accent_hex: str,
    sections: list,
    temp_dir: str,
    preset: dict,
) -> str:
    page_w = preset.get("width", "6.4in")
    page_h = preset.get("height", "7.5in")
    f_size = preset["font_size"]
    leading = preset["leading"]
    spacing = preset["spacing"]
    m_v = preset["margin_v"]
    m_h = preset["margin_h"]
    title_sz = preset["ch_title_size"]
    is_mobile = preset.get("is_mobile", False)
    is_compact = preset.get("is_compact", False)
    diag_w = "92%" if not (is_mobile or is_compact) else ("95%" if is_compact else "98%")

    footer_block = (
        "  footer-descent: 12pt,\n"
        "  footer: context {\n"
        "    let p = here().page()\n"
        "    if p > 1 {\n"
        '      set text(font: "IBM Plex Mono", size: 7.5pt, fill: muted-color)\n'
        + (
            "      align(center)[#p]\n"
            if is_mobile
            else (
                "      if calc.odd(p) {\n"
                "        align(left)[#h(18pt)#p]\n"
                "      } else {\n"
                "        align(right)[#p#h(18pt)]\n"
                "      }\n"
            )
        )
        + "    }\n"
        "  }"
    )

    typ_lines = [
        '#import "@preview/mitex:0.2.6": mitex-convert, mitex-scope',
        "#let my-scope = mitex-scope + (diff: sym.partial)",
        '#let fix-mt(s) = s.replace("planck.reduce", "planck").replace("angle.l", "chevron.l").replace("angle.r", "chevron.r").replace("plus.circle", "plus.o").replace("minus.circle", "minus.o").replace("times.circle", "times.o").replace("dot.circle", "dot.o")',
        '#let mitex(it) = math.equation(block: true, eval("$" + fix-mt(mitex-convert(it)) + "$", scope: my-scope))',
        '#let mi(it) = math.equation(block: false, eval("$" + fix-mt(mitex-convert(it)) + "$", scope: my-scope))',
        "",
        "#let book-title = " + json.dumps(book_title),
        "#let book-subtitle = " + json.dumps(book_subtitle),
        "#let book-category = " + json.dumps(category.upper()),
        f'#let accent-color = rgb("{accent_hex}")',
        '#let ink-color = rgb("#1c1b18")',
        '#let sub-color = rgb("#4a453e")',
        '#let muted-color = rgb("#655f57")',
        '#let rule-color = rgb("#dcd5ca")',
        '#let current-chapter = state("current-chapter", "")',
        "",
        "#set page(",
        f"  width: {page_w},",
        f"  height: {page_h},",
        '  fill: rgb("#faf8f5"),',
        f"  margin: (top: {m_v}, bottom: {m_v}, left: {m_h}, right: {m_h}),",
        "  header: context {",
        "    let p = here().page()",
        "    if p > 1 {",
        '      set text(font: "IBM Plex Mono", size: 6.5pt, tracking: 0.8pt, fill: muted-color)',
        "      if calc.odd(p) {",
        "        align(left)[#upper(book-title)]",
        "      } else {",
        "        align(right)[#upper(current-chapter.get())]",
        "      }",
        "    }",
        "  },",
        footer_block,
        ")",
        "",
        f'#set text(font: "Literata", size: {f_size}, fill: ink-color, lang: "en")',
        f"#set par(justify: true, leading: {leading}, spacing: {spacing})",
        "",
        "// PAGE 1: TITLE & CONTENTS FRONTISPIECE",
        "#v(0.02in)",
        '#text(font: "IBM Plex Mono", size: 7.2pt, tracking: 1.8pt, fill: accent-color, weight: "medium")[#book-category]',
        "#v(4pt)",
        f'#text(font: "Literata", size: {"17.0pt" if (is_mobile or is_compact) else "19.5pt"}, weight: "bold", fill: ink-color)[#book-title]',
        "#v(2pt)",
        f'#text(font: "Literata", size: {"10.2pt" if (is_mobile or is_compact) else "11.2pt"}, fill: sub-color)[#book-subtitle]',
        "#v(5pt)",
        "#line(length: 100%, stroke: 0.6pt + accent-color)",
        "#v(5pt)",
        '#text(font: "IBM Plex Mono", size: 6.8pt, tracking: 1.5pt, fill: muted-color)[CONTENTS]',
        "#v(3pt)",
    ]

    toc_entries = []
    toc_title_sz = "7.7pt" if is_compact else ("7.9pt" if is_mobile else "8.5pt")
    toc_sub_sz = "6.7pt" if is_compact else ("6.9pt" if is_mobile else "7.5pt")
    toc_spacing = "2.6pt" if is_compact else ("3.2pt" if is_mobile else "4.2pt")
    for sec in sections:
        idx = sec["index"]
        lbl = "Introduction" if idx == 0 else f"{idx}. {sec['title']}"
        lbl_esc = escape_typst_text(lbl)
        sub_esc = escape_typst_text(sec["subtitle"])
        toc_entries.append(
            f'#block(spacing: {toc_spacing})[\n'
            f'  #context {{\n'
            f'    let target = label("sec-{idx}")\n'
            f'    let pg = locate(target).page()\n'
            f'    set par(leading: 0.34em)\n'
            f'    grid(\n'
            f'      columns: (1fr, auto),\n'
            f'      gutter: 6pt,\n'
            f'      [#text(size: {toc_title_sz}, weight: "semibold")[#link(target)[{lbl_esc}]] #h(3pt) #text(size: {toc_sub_sz}, fill: muted-color)[{sub_esc}]],\n'
            f'      [#text(font: "IBM Plex Mono", size: 7.5pt, fill: muted-color)[#link(target)[#pg]]]\n'
            f'    )\n'
            f'  }}\n'
            f']'
        )
    typ_lines.extend(toc_entries)
    typ_lines.append("#v(1fr)")
    typ_lines.append('#align(left)[#text(font: "IBM Plex Mono", size: 6.5pt, tracking: 1.4pt, fill: muted-color)[ALEXANDRIA PRESS · ALEXANDRIA.PRESS]]')

    for sec in sections:
        idx = sec["index"]
        label_txt = escape_typst_text(sec["label"].upper())
        title_txt = escape_typst_text(sec["title"])
        subtitle_txt = escape_typst_text(sec["subtitle"])
        body_typ = convert_body_to_typst(sec["body"], temp_dir, idx, accent_hex).replace('width: 98%', f'width: {diag_w}')

        typ_lines.append("")
        typ_lines.append(f'#current-chapter.update({json.dumps(sec["title"])})')
        typ_lines.append("#pagebreak()")
        typ_lines.append(f'#context [#metadata((sec: {idx}, title: {json.dumps(sec["title"])}, page: here().page())) <sec-mark>]')
        typ_lines.append(f'#metadata({idx}) <sec-{idx}>')
        typ_lines.append("#v(0.02in)")
        typ_lines.append(f'#text(font: "IBM Plex Mono", size: 7.2pt, tracking: 1.6pt, fill: accent-color, weight: "medium")[{label_txt}]')
        typ_lines.append("#v(2pt)")
        typ_lines.append(f'#text(font: "Literata", size: {title_sz}, weight: "bold", fill: ink-color)[{title_txt}]')
        typ_lines.append("#v(1pt)")
        typ_lines.append(f'#text(font: "Literata", size: 10.6pt, fill: sub-color)[{subtitle_txt}]')
        typ_lines.append("#v(4pt)")
        typ_lines.append("#line(length: 2.2in, stroke: 0.5pt + rule-color)")
        typ_lines.append("#v(5pt)")
        # Ensure Introductions on Page 2 always fit on a single page so Chapter 1 always starts on Page 3
        if not is_mobile and idx == 0 and len(sec["body"].split()) > 180:
            w_cnt = len(sec["body"].split())
            if is_compact:
                intro_sz = "9.2pt" if w_cnt > 330 else ("9.8pt" if w_cnt > 260 else "10.3pt")
                intro_lead = "0.48em" if w_cnt > 330 else "0.52em"
                intro_spac = "0.68em" if w_cnt > 330 else "0.74em"
            else:
                intro_sz = "9.8pt" if w_cnt > 330 else ("10.3pt" if w_cnt > 270 else "10.8pt")
                intro_lead = "0.52em" if w_cnt > 330 else "0.55em"
                intro_spac = "0.76em" if w_cnt > 330 else "0.82em"
            typ_lines.append(f'#block[#set text(size: {intro_sz}); #set par(leading: {intro_lead}, spacing: {intro_spac});\n{body_typ}\n]')
        else:
            typ_lines.append(body_typ)

    typ_lines.append('#context [#metadata((sec: -1, title: "END", page: here().page())) <sec-mark>]')
    return "\n".join(typ_lines)


FONT_DIR = os.path.join(BASE_DIR, "fonts")

# Desktop Widescreen Preset: 5.8in x 7.5in per page -> 11.6in x 7.5in two-page spread (2P aspect = 1.55)
DESKTOP_PRESET = {
    "width": "5.8in",
    "height": "7.5in",
    "font_size": "11.6pt",
    "leading": "0.59em",
    "spacing": "0.90em",
    "margin_v": "0.42in",
    "margin_h": "0.42in",
    "ch_title_size": "16.0pt",
    "is_mobile": False,
    "is_compact": False,
}

# Compact / Medium-Width 2-Page Preset: 5.5in x 6.8in per page (12.2pt font)
COMPACT_PRESET = {
    "width": "5.5in",
    "height": "6.8in",
    "font_size": "12.2pt",
    "leading": "0.56em",
    "spacing": "0.84em",
    "margin_v": "0.36in",
    "margin_h": "0.36in",
    "ch_title_size": "15.8pt",
    "is_mobile": False,
    "is_compact": True,
}

# Mobile Tall-Screen Preset: 4.2in x 7.5in per page (Literata +2px body size)
MOBILE_PRESET = {
    "width": "4.2in",
    "height": "7.5in",
    "font_size": "11.8pt",
    "leading": "0.58em",
    "spacing": "0.90em",
    "margin_v": "0.38in",
    "margin_h": "0.32in",
    "ch_title_size": "15.2pt",
    "is_mobile": True,
    "is_compact": False,
}


def _compile_single_preset(book_title, book_subtitle, category, accent_hex, sections, temp_dir, preset, typ_name, out_path, slug):
    typ_path = os.path.join(temp_dir, typ_name)
    typ_src = build_typ_source(book_title, book_subtitle, category, accent_hex, sections, temp_dir, preset)
    with open(typ_path, "w", encoding="utf-8") as f:
        f.write(typ_src)

    q_proc = subprocess.run(
        ["typst", "query", "--font-path", FONT_DIR, typ_path, "<sec-mark>"],
        capture_output=True,
        text=True,
    )
    if q_proc.returncode != 0:
        raise RuntimeError(f"Typst query failed for {slug} ({typ_name}):\n{q_proc.stderr}")
    marks = json.loads(q_proc.stdout)
    sec_pages = [m["value"]["page"] for m in marks[:-1]]

    proc = subprocess.run(
        ["typst", "compile", "--font-path", FONT_DIR, typ_path, out_path],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Typst compile failed for {slug} ({typ_name}):\n{proc.stderr}")
    return sec_pages


def compile_book_to_pdf(md_path: str, category: str = "NON-FICTION", accent_hex: str = "#a37c40"):
    raw_md = open(md_path, encoding="utf-8").read()
    book_title, book_subtitle, sections = parse_book_markdown(raw_md)
    slug = os.path.splitext(os.path.basename(md_path))[0].replace("_", "-")

    os.makedirs(PDF_OUT_DIR, exist_ok=True)
    out_pdf_path = os.path.join(PDF_OUT_DIR, f"{slug}.pdf")
    out_compact_pdf_path = os.path.join(PDF_OUT_DIR, f"{slug}-compact.pdf")
    out_mobile_pdf_path = os.path.join(PDF_OUT_DIR, f"{slug}-mobile.pdf")

    with tempfile.TemporaryDirectory() as temp_dir:
        sec_pages = _compile_single_preset(
            book_title, book_subtitle, category, accent_hex, sections, temp_dir,
            DESKTOP_PRESET, "book.typ", out_pdf_path, slug
        )
        compact_sec_pages = _compile_single_preset(
            book_title, book_subtitle, category, accent_hex, sections, temp_dir,
            COMPACT_PRESET, "book_compact.typ", out_compact_pdf_path, slug
        )
        mobile_sec_pages = _compile_single_preset(
            book_title, book_subtitle, category, accent_hex, sections, temp_dir,
            MOBILE_PRESET, "book_mobile.typ", out_mobile_pdf_path, slug
        )

    return out_pdf_path, sec_pages, out_compact_pdf_path, compact_sec_pages, out_mobile_pdf_path, mobile_sec_pages


def main():
    parser = argparse.ArgumentParser(description="Compile Alexandria Press markdown manuscripts to Typst PDFs.")
    parser.add_argument("files", nargs="*", help="Markdown file(s) to compile")
    parser.add_argument("--all", action="store_true", help="Compile all books in js/books-data.js")
    args = parser.parse_args()

    books_meta = load_books_metadata()
    target_files = list(args.files)
    if args.all:
        target_files = [os.path.join(BASE_DIR, slug.replace("-", "_") + ".md") for slug in books_meta.keys()]

    if not target_files:
        parser.print_help()
        sys.exit(1)

    for fpath in target_files:
        slug = os.path.splitext(os.path.basename(fpath))[0].replace("_", "-")
        meta = books_meta.get(slug, {})
        cat = meta.get("category", "NON-FICTION")
        pdf_path, sec_pages, comp_path, comp_pages, mob_path, mob_pages = compile_book_to_pdf(fpath, category=cat)
        size_kb = os.path.getsize(pdf_path) / 1024.0
        comp_kb = os.path.getsize(comp_path) / 1024.0
        mob_kb = os.path.getsize(mob_path) / 1024.0
        print(f"[OK] {slug:28s} -> desktop ({size_kb:5.1f} KB) | compact ({comp_kb:5.1f} KB) | mobile ({mob_kb:5.1f} KB)")


if __name__ == "__main__":
    main()

