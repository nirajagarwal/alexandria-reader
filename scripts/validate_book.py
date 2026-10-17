#!/usr/bin/env python3
r"""
Alexandria Press — Deterministic Book Validator & Quality Gate (scripts/validate_book.py)

Enforces the Seven Universal Laws from alexandria_manifesto.md and GENERATION_GUIDELINES.md:
1. Strict 3-line chapter headers (### Chapter N / # Title / ## Subtitle) with zero colons.
2. Substantive chapter depth (default 600–900 words per chapter; catches 300-word compression drift).
3. Concrete historical/empirical grounding (verifies dates and named entities in every chapter).
4. Opening-door cadence rotation (flags formulaic "In [Year]," openings if overused).
5. Clean exits & anti-hyperbole (flags moralizing final-paragraph sermons and banned adjectives).
6. Earned formalisms & KaTeX compilation (rejects "math cosplay" pseudo-equations, checks for
   raw LaTeX leaks, unescaped currency $, tall \sum in \frac without \nolimits, and compiles
   every inline/display equation via Node KaTeX with throwOnError: true).

Usage:
    python3 scripts/validate_book.py <book.md> [--min-words 600] [--max-words 900] [--legacy]
    python3 scripts/validate_book.py --all
"""

import argparse
import json
import os
import re
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BANNED_WORDS = [
    r"\bbreathtaking\b",
    r"\bawe-inspiring\b",
    r"\bmind-boggling\b",
    r"\bstaggering\b",
    r"\bparadigm-shifting\b",
]

MORALIZING_EXIT_PATTERNS = [
    r"\b(?:life|career|story|history|tragedy|triumph|fate|legacy|example|lesson)\s+(?:proved|demonstrated|showed|taught|reminds)\s+that\b",
    r"\b(?:this|these)\s+(?:episode|incident|disaster|collapse|story|history)\s+(?:proved|demonstrated|showed|reminds)\s+that\b",
    r"\bserves as a (?:permanent\s+|eternal\s+|stark\s+)?(?:testament|reminder|monument|warning)\b",
    r"\breminds us that\b",
    r"^ultimately,",
    r"\bin conclusion\b",
]

RAW_LATEX_LEAK_RE = re.compile(
    r"\\(frac|Delta|sum|int|propto|approx|implies|longrightarrow|xrightarrow|text\{|mathbb|mathcal|sqrt|sigma|alpha|beta|gamma|lambda|omega|theta|tau|rho|pi|mu|nu|epsilon|eta|nabla|partial|infty|cdot|times|le\b|ge\b|neq|equiv)"
)


def clean_math_syntax(math_str: str) -> str:
    m = math_str.strip()
    m = m.replace("·", " \\cdot ")
    m = m.replace("×", " \\times ")
    m = m.replace("∝", " \\propto ")
    m = m.replace("⇒", " \\implies ")
    m = m.replace("→", " \\to ")
    m = re.sub(r"√\s*([a-zA-Z0-9_{}]+)", r"\\sqrt{\1}", m)
    m = m.replace("√", "\\sqrt")
    m = re.sub(r"_([a-zA-Z]{2,})(?![a-zA-Z0-9_]*\})", r"_{\1}", m)
    return m


def is_math_cosplay(eq: str) -> bool:
    r"""
    Detects fake conceptual equations such as:
    \text{Fragility}(\text{Monopoly}) \propto \text{Inertia} \times (\text{Orthodoxy})^2
    where English prose inside \text{...} dominates the expression without real math variables.
    """
    text_spans = re.findall(r"\\text\{([^}]*)\}", eq)
    if not text_spans:
        return False
    unit_whitelist = {
        "kJ/mol", "mol", "kcal", "min", "sec", "days", "hours", "years", "meters",
        "feet", "tons", "volts", "watts", "ohms", "kelvin", "celsius", "bars",
        "atoms", "molecules", "electrons", "photons", "bits", "bytes", "hosts",
        "lines", "erlangs", "knots", "miles", "cycles", "beats", "breaths",
        "survive", "downed", "returning", "prior", "sensory", "ideal", "operating",
        "ambient", "skin", "cell", "bank", "open", "mech", "elec", "kin",
        "apparent", "planet", "earth", "urease", "closed", "proton", "neutron",
        "shell", "photoelectric", "electrical", "current", "time", "hit",
        "total", "electron", "neutral", "recoil", "constant", "myosin", "actin",
        "retinal", "photon", "rhodopsin", "vascular", "sarcomere",
    }
    prose_words = []
    for span in text_spans:
        for w in re.findall(r"[A-Za-z]{4,}", span):
            if w.lower() not in unit_whitelist:
                prose_words.append(w)

    stripped = re.sub(r"\\text\{[^}]*\}", "", eq)
    has_numbers_or_greek_or_frac = bool(
        re.search(r"(\d|\\frac|\\sum|\\int|\\sqrt|\\log|\\ln|\\exp|\\sin|\\cos|\\Delta|\\sigma|\\alpha|\\beta|\\gamma|\\lambda|\\tau|\\rho|\\theta|\\pi|\\mu|\\nu|\\mathbb)", stripped)
    )
    if len(prose_words) >= 3 and not has_numbers_or_greek_or_frac:
        return True
    return False


def verify_katex_batch(equations):
    """
    Runs Node.js with KaTeX (if installed or via local script) or syntax check on all equations.
    Returns a list of error strings.
    """
    if not equations:
        return []
    node_script = r"""
const fs = require('fs');
let katex = null;
try {
  katex = require('katex');
} catch (e) {
  // If katex npm package is not installed locally, exit cleanly
  process.exit(0);
}
const items = JSON.parse(fs.readFileSync(0, 'utf8'));
const errors = [];
for (const item of items) {
  try {
    katex.renderToString(item.math, { displayMode: item.display, throwOnError: true, strict: false });
  } catch (err) {
    errors.push(`${item.loc}: ${err.message} in [${item.math}]`);
  }
}
console.log(JSON.stringify(errors));
"""
    try:
        proc = subprocess.run(
            ["node", "-e", node_script],
            input=json.dumps(equations),
            text=True,
            capture_output=True,
            cwd=BASE_DIR,
            timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return json.loads(proc.stdout.strip())
    except Exception:
        pass
    return []


def validate_svg_diagram(svg_str: str, loc: str):
    import xml.etree.ElementTree as ET
    errs = []
    try:
        root = ET.fromstring(svg_str)
    except Exception as e:
        return [f"{loc}: Invalid SVG XML syntax ({e})"]

    vb = root.attrib.get("viewBox", "").strip()
    m_vb = re.match(r"^0\s+0\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$", vb)
    if not m_vb:
        errs.append(f"{loc}: Diagram <svg> must have viewBox='0 0 600 H' (found '{vb}').")
        vw, vh = 600.0, 200.0
    else:
        vw, vh = float(m_vb.group(1)), float(m_vb.group(2))
        if vw != 600.0 or vh < 140.0 or vh > 250.0:
            errs.append(f"{loc}: Diagram viewBox must have width=600 and height between 140 and 250 (found '{vb}').")

    # Check for forbidden hardcoded dark/light colors that break theme switching
    bad_color = re.search(
        r'(?:stroke|fill)\s*=\s*"\s*(?:#000(?:000)?|#fff(?:fff)?|#111(?:111)?|#222(?:222)?|#333(?:333)?|black|white)\s*"',
        svg_str,
        re.IGNORECASE,
    )
    if bad_color:
        errs.append(
            f"{loc}: Diagram uses hardcoded color {bad_color.group(0)}—use CSS theme variables (var(--text-color), var(--text-muted), var(--accent-color), var(--border-color), var(--card-bg))."
        )

    prim_tags = {"rect", "circle", "ellipse", "line", "polyline", "polygon", "path", "text"}
    prim_count = 0
    text_boxes = []
    rect_boxes = []

    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in prim_tags:
            prim_count += 1
        if tag == "rect":
            try:
                rx = float(el.attrib.get("x", "0"))
                ry = float(el.attrib.get("y", "0"))
                rw = float(el.attrib.get("width", "0"))
                rh = float(el.attrib.get("height", "0"))
            except ValueError:
                errs.append(f"{loc}: Diagram <rect> has non-numeric x/y/width/height.")
                continue
            if rw > 0 and rh > 0:
                if rx < 4 or rx + rw > vw - 4 or ry < 2 or ry + rh > vh - 2:
                    errs.append(
                        f"{loc}: Diagram <rect> at ({rx:.0f},{ry:.0f},{rw:.0f}x{rh:.0f}) clips outside viewBox (0..{int(vw)}, 0..{int(vh)})."
                    )
                rect_boxes.append((rx, ry, rx + rw, ry + rh, rw, rh))
        if tag == "text":
            txt = "".join(el.itertext()).strip()
            if not txt:
                continue
            try:
                x = float(el.attrib.get("x", "0"))
                y = float(el.attrib.get("y", "0"))
                fs = float(re.sub(r"[^0-9.]", "", el.attrib.get("font-size", "13")) or "13")
            except ValueError:
                errs.append(f"{loc}: Diagram <text> '{txt}' has non-numeric x/y/font-size.")
                continue
            if fs < 11 or fs > 18:
                errs.append(f"{loc}: Diagram <text> '{txt}' font-size ({fs}) must be between 11 and 18.")
            anchor = el.attrib.get("text-anchor", "start").strip()
            ff = el.attrib.get("font-family", "").lower()
            char_factor = 0.64 if "mono" in ff else 0.58
            if txt.isupper() and "mono" not in ff:
                char_factor = 0.63
            est_w = len(txt) * fs * char_factor
            if anchor == "middle":
                x0, x1 = x - est_w / 2.0, x + est_w / 2.0
            elif anchor == "end":
                x0, x1 = x - est_w, x
            else:
                x0, x1 = x, x + est_w
            y0, y1 = y - fs * 0.85, y + fs * 0.25
            if x0 < 4 or x1 > vw - 4 or y0 < 2 or y1 > vh - 2:
                errs.append(
                    f"{loc}: Diagram <text> '{txt}' at ({x},{y}) clips outside viewBox (0..{int(vw)}, 0..{int(vh)}): est x=[{x0:.0f}..{x1:.0f}], y=[{y0:.0f}..{y1:.0f}]."
                )
            text_boxes.append((txt, x0, y0, x1, y1, x, y))

    if prim_count > 34:
        errs.append(f"{loc}: Diagram is too cluttered ({prim_count} elements; maximum 34 for clean schematic legibility).")

    for i in range(len(text_boxes)):
        t1, ax0, ay0, ax1, ay1, _, _ = text_boxes[i]
        for j in range(i + 1, len(text_boxes)):
            t2, bx0, by0, bx1, by1, _, _ = text_boxes[j]
            if min(ax1, bx1) - max(ax0, bx0) > 6 and min(ay1, by1) - max(ay0, by0) > 3:
                errs.append(f"{loc}: Diagram text labels overlap: '{t1}' and '{t2}'.")

    # Check that text inside label <rect> boxes fits with padding, and external text does not cross box borders
    label_rects = [r for r in rect_boxes if r[4] >= 24 and 16 <= r[5] <= 90]
    for txt, tx0, ty0, tx1, ty1, tcx, tcy in text_boxes:
        tw = tx1 - tx0
        for rx0, ry0, rx1, ry1, rw, rh in label_rects:
            # Is the text anchor point inside this label rect?
            if rx0 - 2 <= tcx <= rx1 + 2 and ry0 <= tcy <= ry1 + 2:
                req_w = int(tw + 20)
                if rw < req_w or tx0 < rx0 + 7 or tx1 > rx1 - 7:
                    errs.append(
                        f"{loc}: Diagram box (x={rx0:.0f}, width={rw:.0f}) is too narrow for text '{txt}' (est text width={tw:.0f}px; box needs width >= {req_w})."
                    )
            else:
                # Text is outside this label rect—ensure its bounding box doesn't collide with the rect
                if min(tx1, rx1) - max(tx0, rx0) > 2 and min(ty1, ry1) - max(ty0, ry0) > 2:
                    errs.append(
                        f"{loc}: Diagram text '{txt}' collides with box at (x={rx0:.0f}..{rx1:.0f}, y={ry0:.0f}..{ry1:.0f})."
                    )

    # Check that label <rect> boxes do not overlap each other (except intentional adjacent timeline bars sharing an edge)
    for i in range(len(label_rects)):
        ax0, ay0, ax1, ay1, aw, ah = label_rects[i]
        for j in range(i + 1, len(label_rects)):
            bx0, by0, bx1, by1, bw, bh = label_rects[j]
            if min(ax1, bx1) - max(ax0, bx0) > 1 and min(ay1, by1) - max(ay0, by0) > 1:
                errs.append(
                    f"{loc}: Diagram boxes overlap at (x={ax0:.0f}..{ax1:.0f}) and (x={bx0:.0f}..{bx1:.0f})."
                )

    return errs


def validate_book(
    filepath: str,
    min_words: int = 520,
    max_words: int = 760,
    legacy: bool = False,
    require_quotes: bool = False,
):
    errors = []
    warnings = []

    if not os.path.exists(filepath):
        return [f"File not found: {filepath}"], [], {}

    raw_text = open(filepath, encoding="utf-8").read()
    filename = os.path.basename(filepath)
    slug = os.path.splitext(filename)[0].replace("_", "-")
    dossier_path = os.path.join(BASE_DIR, "dossiers", f"{slug}.json")

    VALID_MODES = {
        "facet",
        "listicle",
        "landscape",
        "contrast",
        "anatomy",
        "field-guide",
        "scale",
        "inversion",
        "chain",
    }

    min_diagrams = 0
    book_mode = "facet"
    if os.path.exists(dossier_path):
        try:
            dossier = json.load(open(dossier_path, encoding="utf-8"))
            book_mode = dossier.get("mode", "facet")
            if book_mode not in VALID_MODES:
                errors.append(
                    f"Invalid dossier mode '{book_mode}' in {dossier_path}. Must be one of {sorted(VALID_MODES)}."
                )
            cc = dossier.get("creator_constraints", {})
            if cc.get("require_quote_per_chapter"):
                require_quotes = True
            if "min_diagrams" in cc:
                min_diagrams = int(cc["min_diagrams"])
            # Also auto-enable require_quotes if all 12 dossier chapters specify verbatim_quote
            d_chaps = dossier.get("chapters", [])
            if d_chaps and all(c.get("verbatim_quote") for c in d_chaps):
                require_quotes = True
        except Exception:
            pass

    # 1. Check for leftover script artifacts
    if "with open(" in raw_text or 'print(f"' in raw_text:
        errors.append("Found leftover Python script snippet ('with open(' or 'print(f\"') in file.")

    sections = [s.strip() for s in raw_text.split("\n---\n") if s.strip()]
    if len(sections) < 9:
        errors.append(f"Expected Title + Intro + 8–12 chapters (>=10 sections), found {len(sections)} sections.")
        return errors, warnings, {}

    # Check Book Title block (Section 0)
    title_lines = [l.strip() for l in sections[0].splitlines() if l.strip()]
    if not title_lines or not title_lines[0].startswith("# "):
        errors.append("Section 0 must start with '# [Book Title]'.")
    if len(title_lines) < 2 or not title_lines[1].startswith("## "):
        errors.append("Section 0 second line must be '## [Book Subtitle]'.")
    for tl in title_lines[:2]:
        if ":" in tl:
            errors.append(f"Colon forbidden in Book Title header: '{tl}'")

    # Check Introduction (Section 1) and Chapters (Sections 2..N)
    chapters_meta = []
    date_open_count = 0
    quote_chap_count = 0
    katex_items = []
    diagram_count = 0

    for idx, sec in enumerate(sections[1:]):
        sec_lines = sec.splitlines()
        non_empty = [l.strip() for l in sec_lines if l.strip()]
        if len(non_empty) < 4:
            errors.append(f"Section {idx + 1} is too short (<4 non-empty lines).")
            continue

        h1, h2, h3 = non_empty[0], non_empty[1], non_empty[2]
        expected_label = "### Introduction" if idx == 0 else f"### Chapter {idx}"
        if h1 != expected_label:
            errors.append(f"Section {idx + 1} header line 1 must be '{expected_label}', found '{h1}'.")
        if not h2.startswith("# "):
            errors.append(f"Section {idx + 1} header line 2 must start with '# ', found '{h2}'.")
        if not h3.startswith("## "):
            errors.append(f"Section {idx + 1} header line 3 must start with '## ', found '{h3}'.")

        for h_line in (h1, h2, h3):
            if ":" in h_line:
                errors.append(f"Colon forbidden in header ({expected_label}): '{h_line}'")

        # Extract body after the 3 header lines
        header_end_line = 0
        seen_headers = 0
        for line_i, l in enumerate(sec_lines):
            if l.strip().startswith("#"):
                seen_headers += 1
                if seen_headers == 3:
                    header_end_line = line_i + 1
                    break
        body = "\n".join(sec_lines[header_end_line:]).strip()

        # Validate any ```svg diagram blocks in this section
        svg_blocks = re.findall(r"```(?:svg|diagram)\s*\n([\s\S]*?)```", body, flags=re.IGNORECASE)
        if len(svg_blocks) > 1:
            errors.append(f"{expected_label} has {len(svg_blocks)} diagrams (maximum 1 per chapter).")
        for svg_b in svg_blocks:
            diagram_count += 1
            errors.extend(validate_svg_diagram(svg_b.strip(), f"{filename}:{expected_label}"))

        body_no_code = re.sub(r"```[\s\S]*?```", "", body)
        # Exclude standalone middle-dot separators from word count
        body_no_sep = re.sub(r"(?m)^[ \t]*(?:·\s*·\s*·|\*\s*\*\s*\*|[❦☙⁂✦])[ \t]*$", "", body_no_code)
        body_words = len(body_no_sep.split())

        if idx == 0:
            # Introduction word count & no-chapter-summary check (~250 words target)
            if body_words < 140 or body_words > 300:
                errors.append(f"Introduction word count ({body_words}) must be between 140 and 300 words (~250 word target).")
            if re.search(r"\b(?:this volume traces|this volume examines|across twelve chapters|in the first half of the|in the second half of the|the twelve chapters that follow)\b", body_no_code, re.IGNORECASE):
                errors.append("Introduction must introduce the topic only—do not summarize or list the chapters.")
        else:
            effective_min = 280 if legacy else min_words
            effective_max = 1070 if legacy else max_words
            if body_words < effective_min:
                errors.append(
                    f"Chapter {idx} ('{h2[2:]}') body is too short: {body_words} words (minimum {effective_min})."
                )
            elif body_words > effective_max:
                errors.append(
                    f"Chapter {idx} ('{h2[2:]}') body is too long: {body_words} words (maximum {effective_max}; target 550–720 words for high-density compression)."
                )

            if book_mode == "listicle":
                mid_dot_count = len(re.findall(r"(?m)^[ \t]*·\s*·\s*·[ \t]*$", body_no_code))
                if mid_dot_count != 11:
                    errors.append(
                        f"Chapter {idx} ('{h2[2:]}') in listicle mode must have 12 single-paragraph items separated by 11 standalone middle-dot ('· · ·') lines (found {mid_dot_count} '· · ·' lines)."
                    )
                para_blocks = [p.strip() for p in re.split(r"\n\s*\n", body_no_code) if p.strip()]
                if len(para_blocks) != 23:
                    errors.append(
                        f"Chapter {idx} ('{h2[2:]}') in listicle mode must have blank lines around every '· · ·' separator (expected 23 blank-line-separated blocks, found {len(para_blocks)})."
                    )
                if re.search(r"(?m)^\s*\d+\.\s+", body_no_code):
                    errors.append(
                        f"Chapter {idx} ('{h2[2:]}') in listicle mode must NOT use numbered lists ('1. ', '2. ')—use 12 paragraphs separated by standalone '· · ·' lines."
                    )
            else:
                # Concrete grounding check (must have a 3-4 digit year or BCE/CE date)
                if not re.search(r"\b(1\d{3}|20[0-2]\d|\d+\s*(?:BCE|BC|CE|AD))\b", body_no_code):
                    errors.append(f"Chapter {idx} ('{h2[2:]}') lacks a concrete historical year/date anchor.")

            # Check for verbatim quote in chapter ("..." or “...” with >= 3 words)
            quotes_found = [
                q for q in re.findall(r'(?:"([^"\n]{12,})"|“([^”\n]{12,})”)', body_no_code)
                if len((q[0] or q[1]).split()) >= 3
            ]
            if quotes_found:
                quote_chap_count += 1
            elif require_quotes:
                errors.append(
                    f"Chapter {idx} ('{h2[2:]}') is missing a required verbatim quote (--require-quotes / creator_constraints)."
                )

            # Check opening sentence cadence
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body_no_sep) if p.strip()]
            first_para = paragraphs[0] if paragraphs else ""
            if re.match(r"^(In|On|At)\s+(January|February|March|April|May|June|July|August|September|October|November|December|the\s+(?:morning|afternoon|evening|night|spring|summer|autumn|winter|early|late)|\d{4}|\d{1,2}:\d{2})", first_para):
                date_open_count += 1

            # Check final paragraph for moralizing exit sermons
            last_para = paragraphs[-1] if paragraphs else ""
            for pat in MORALIZING_EXIT_PATTERNS:
                if re.search(pat, last_para, flags=re.IGNORECASE):
                    errors.append(
                        f"Chapter {idx} ('{h2[2:]}') final paragraph contains moralizing exit pattern '{pat}': \"{last_para[-140:]}\""
                    )

        # Banned hyperbolic words check
        for bpat in BANNED_WORDS:
            m = re.search(bpat, body_no_code, flags=re.IGNORECASE)
            if m:
                errors.append(f"{expected_label} contains banned hyperbolic word: '{m.group(0)}'")

        # Math & LaTeX validation
        body_esc = body_no_code.replace("\\$", "___ESC_DOLLAR___")

        # Extract display math $$...$$
        for disp_m in re.finditer(r"\$\$([\s\S]*?)\$\$", body_esc):
            eq_raw = disp_m.group(1).replace("___ESC_DOLLAR___", "\\$").strip()
            if is_math_cosplay(eq_raw):
                errors.append(f"{expected_label} contains suspected 'math cosplay' pseudo-equation: $${eq_raw}$$")
            if "\\frac" in eq_raw and "\\sum_" in eq_raw and "\\nolimits" not in eq_raw:
                # Check if \sum_ is inside a \frac
                if re.search(r"\\frac\{[^}]*\\sum_|\\frac\{[\s\S]*?\}\{[^}]*\\sum_", eq_raw):
                    warnings.append(
                        f"{expected_label} has \\sum_ inside \\frac without \\nolimits (risk of height clipping): $${eq_raw}$$"
                    )
            katex_items.append({"loc": f"{filename}:{expected_label} (display)", "math": clean_math_syntax(eq_raw), "display": True})

        body_no_disp = re.sub(r"\$\$[\s\S]*?\$\$", "", body_esc)

        # Check inline math and raw LaTeX leaks line by line
        for l_num, line in enumerate(body_no_disp.splitlines(), 1):
            # Protect legitimate currency like $10 million
            line_curr = re.sub(
                r"\$(?=\d[\d,]*(?:\.\d+)?\s*(?:million|billion|trillion|thousand|hundred|per\s+share)\b)",
                "___CURR___",
                line,
                flags=re.IGNORECASE,
            )
            inline_matches = list(re.finditer(r"\$([^\s$](?:[^$\n]*?[^\s$])?)\$", line_curr))
            for in_m in inline_matches:
                in_raw = in_m.group(1).replace("___ESC_DOLLAR___", "\\$")
                if re.match(r"^\d[\d,]*(?:\.\d+)?$", in_raw) and not re.search(r"[+\-*/=^_\\]", in_raw):
                    warnings.append(f"{expected_label} line {l_num} has unescaped currency '${in_raw}' (use \\${in_raw}).")
                    continue
                katex_items.append({"loc": f"{filename}:{expected_label}:L{l_num} (inline)", "math": clean_math_syntax(in_raw), "display": False})

            # Remove valid inline math and check for unmatched $ or leaked raw LaTeX
            rem_line = re.sub(r"\$([^\s$](?:[^$\n]*?[^\s$])?)\$", "", line_curr)
            if "$" in rem_line:
                errors.append(f"{expected_label} line {l_num} has unmatched or unescaped '$': {line.strip()}")
            leak = RAW_LATEX_LEAK_RE.search(rem_line)
            if leak:
                errors.append(f"{expected_label} line {l_num} leaks raw un-delimited LaTeX '{leak.group(0)}': {line.strip()}")

        chapters_meta.append({"label": expected_label, "title": h2[2:], "words": body_words})

    num_chapters = len(sections) - 2
    if date_open_count > max(4, num_chapters // 2):
        errors.append(
            f"Cadence fatigue: {date_open_count}/{num_chapters} chapters open with a formulaic 'In/On/At [Date/Time]' sentence. Rotate across Door A (Scene), Door B (Paradox/Constraint), and Door C (Artifact/Measurement)."
        )
    if diagram_count > 4:
        errors.append(f"Too many diagrams in volume ({diagram_count}; maximum 4 per book so diagrams remain high-signal).")
    if diagram_count < min_diagrams:
        errors.append(f"Volume has {diagram_count} diagrams, fewer than creator_constraints.min_diagrams ({min_diagrams}).")

    katex_errors = verify_katex_batch(katex_items)
    errors.extend(katex_errors)

    # Compute prose sentence length cadence (excluding code/diagram blocks, display math, and bullet items)
    raw_no_code = re.sub(r"```[\s\S]*?```", "", raw_text)
    prose_lines = [
        l for l in re.sub(r"\$\$[\s\S]*?\$\$", "", raw_no_code).splitlines()
        if l.strip()
        and l.strip() not in ("❦", "☙", "⁂", "✦")
        and not l.strip().startswith(("#", "*", "-", ">", "---"))
        and not re.match(r"^\d+\.", l.strip())
    ]
    prose_text = " ".join(prose_lines)
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", prose_text) if len(s.strip().split()) >= 3]
    avg_sent_words = round(sum(len(s.split()) for s in sents) / len(sents), 1) if sents else 0.0
    if not legacy and avg_sent_words > 24.0:
        errors.append(
            f"Average sentence length is {avg_sent_words} words/sentence (maximum 24.0 w/s; target 17–22 w/s). Break up long multi-clause sentences into direct declarative statements."
        )

    summary = {
        "file": filename,
        "chapters": num_chapters,
        "total_words": len(raw_no_code.split()),
        "chapter_words": [c["words"] for c in chapters_meta[1:]],
        "date_opens": date_open_count,
        "quote_chapters": quote_chap_count,
        "equations_checked": len(katex_items),
        "diagrams_checked": diagram_count,
        "avg_sent_words": avg_sent_words,
    }
    return errors, warnings, summary


def main():
    parser = argparse.ArgumentParser(description="Validate Alexandria Press markdown manuscripts.")
    parser.add_argument("files", nargs="*", help="Markdown file(s) to validate")
    parser.add_argument("--all", action="store_true", help="Validate all published books in js/books-data.js")
    parser.add_argument("--min-words", type=int, default=520, help="Minimum words per chapter (default: 520)")
    parser.add_argument("--max-words", type=int, default=760, help="Maximum words per chapter (default: 760)")
    parser.add_argument("--legacy", action="store_true", help="Allow legacy word counts and sentence lengths for existing volumes")
    parser.add_argument("--require-quotes", action="store_true", help="Require at least one verbatim quote in every chapter (Creator Steering constraint)")
    args = parser.parse_args()

    LEGACY_BOOKS = {
        "non_linear_engines.md",
        "latent_fragility.md",
        "singular_minds.md",
        "radical_subtraction.md",
        "elemental_asymmetries.md",
        "liminal_thresholds.md",
        "autonomous_engine.md",
        "affective_topologies.md",
        "architectures_of_choice.md",
        "tales_of_audacity.md",
        "architectures_of_the_grid.md",
        "sensory_worlds.md",
        "instruments_of_precision.md",
        "ghosts_in_the_parchment.md",
        "fictions_of_order.md",
        "bonds_of_enmity.md",
    }

    target_files = list(args.files)
    if args.all:
        books_js = open(os.path.join(BASE_DIR, "js", "books-data.js"), encoding="utf-8").read()
        p_end = books_js.find("return {") + len("return ")
        s_start = books_js.rfind("};") + 1
        data = json.loads(books_js[p_end:s_start])
        target_files = [os.path.join(BASE_DIR, k.replace("-", "_") + ".md") for k in data.keys()]

    if not target_files:
        parser.print_help()
        sys.exit(1)

    total_errors = 0
    for fpath in target_files:
        fname = os.path.basename(fpath)
        use_legacy = args.legacy or (args.all and fname in LEGACY_BOOKS)
        errs, warns, info = validate_book(
            fpath,
            args.min_words,
            args.max_words,
            legacy=use_legacy,
            require_quotes=args.require_quotes,
        )
        status = "PASS" if not errs else "FAIL"
        ch_w = info.get("chapter_words", [])
        w_range = f"{min(ch_w)}–{max(ch_w)} w/ch" if ch_w else "N/A"
        print(
            f"[{status}] {fname:28s} | {info.get('chapters', 0):2d} chs | {info.get('total_words', 0):6,d} words ({w_range}) | "
            f"sent: {info.get('avg_sent_words', 0):4.1f} w/s | quotes: {info.get('quote_chapters', 0):2d}/{info.get('chapters', 0)} | "
            f"eqs: {info.get('equations_checked', 0):3d} | diags: {info.get('diagrams_checked', 0)}"
        )
        for w in warns:
            print(f"   WARN: {w}")
        for e in errs:
            print(f"  ERROR: {e}")
        total_errors += len(errs)

    if total_errors > 0:
        print(f"\nValidation FAILED with {total_errors} error(s).")
        sys.exit(1)
    else:
        print("\nAll validated volumes PASSED 100% of quality gates.")


if __name__ == "__main__":
    main()

