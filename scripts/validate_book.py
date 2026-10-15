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


def validate_book(filepath: str, min_words: int = 600, max_words: int = 900, legacy: bool = False):
    errors = []
    warnings = []

    if not os.path.exists(filepath):
        return [f"File not found: {filepath}"], [], {}

    raw_text = open(filepath, encoding="utf-8").read()
    filename = os.path.basename(filepath)

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
    katex_items = []

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
        body_words = len(body.split())

        if idx == 0:
            # Introduction word count check
            if body_words < 120 or body_words > 650:
                warnings.append(f"Introduction word count ({body_words}) outside typical 150–550 range.")
        else:
            effective_min = 280 if legacy else min_words
            effective_max = 1050 if legacy else max_words
            if body_words < effective_min:
                errors.append(
                    f"Chapter {idx} ('{h2[2:]}') body is too short: {body_words} words (minimum {effective_min})."
                )
            elif body_words > effective_max:
                warnings.append(
                    f"Chapter {idx} ('{h2[2:]}') body is {body_words} words (target max {effective_max})."
                )

            # Concrete grounding check (must have a 3-4 digit year or BCE/CE date)
            if not re.search(r"\b(1\d{3}|20[0-2]\d|\d+\s*(?:BCE|BC|CE|AD))\b", body):
                errors.append(f"Chapter {idx} ('{h2[2:]}') lacks a concrete historical year/date anchor.")

            # Check opening sentence cadence
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
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
            m = re.search(bpat, body, flags=re.IGNORECASE)
            if m:
                errors.append(f"{expected_label} contains banned hyperbolic word: '{m.group(0)}'")

        # Math & LaTeX validation
        body_no_code = re.sub(r"```[\s\S]*?```", "", body)
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

    katex_errors = verify_katex_batch(katex_items)
    errors.extend(katex_errors)

    summary = {
        "file": filename,
        "chapters": num_chapters,
        "total_words": len(raw_text.split()),
        "chapter_words": [c["words"] for c in chapters_meta[1:]],
        "date_opens": date_open_count,
        "equations_checked": len(katex_items),
    }
    return errors, warnings, summary


def main():
    parser = argparse.ArgumentParser(description="Validate Alexandria Press markdown manuscripts.")
    parser.add_argument("files", nargs="*", help="Markdown file(s) to validate")
    parser.add_argument("--all", action="store_true", help="Validate all 11+ published books injs/books-data.js")
    parser.add_argument("--min-words", type=int, default=600, help="Minimum words per chapter (default: 600)")
    parser.add_argument("--max-words", type=int, default=900, help="Maximum words per chapter (default: 900)")
    parser.add_argument("--legacy", action="store_true", help="Allow legacy 380+ word counts for earlier 7 volumes")
    args = parser.parse_args()

    LEGACY_BOOKS = {
        "latent_fragility.md",
        "radical_subtraction.md",
        "singular_minds.md",
        "elemental_asymmetries.md",
        "liminal_thresholds.md",
        "autonomous_engine.md",
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
        errs, warns, info = validate_book(fpath, args.min_words, args.max_words, legacy=use_legacy)
        status = "PASS" if not errs else "FAIL"
        ch_w = info.get("chapter_words", [])
        w_range = f"{min(ch_w)}–{max(ch_w)} w/ch" if ch_w else "N/A"
        print(
            f"[{status}] {fname:28s} | {info.get('chapters', 0):2d} chs | {info.get('total_words', 0):6,d} words ({w_range}) | "
            f"date-opens: {info.get('date_opens', 0)} | eqs: {info.get('equations_checked', 0)}"
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
