---
name: generate-alexandria-book
description: End-to-end autonomous pipeline for generating, validating, and publishing new volumes for Alexandria Press (alexandria.press). Trigger whenever the user asks to generate a new book, pick the next book from the queue, or synthesize a volume on a new topic.
---

# Generate Alexandria Book — Autonomous 5-Stage Pipeline

This skill executes the drift-proof, deterministic 5-stage pipeline for creating new books for **Alexandria Press (`alexandria.press`)**. Never attempt to write a 12-chapter book in a single unvalidated pass without following these five stages.

---

## Stage 1: Topic Selection, Anchor Deduplication & Tier-2 Profile Routing

1. **Read the Core Rules**:
   - View `/Users/niraj/book-writer/alexandria_manifesto.md` and `/Users/niraj/book-writer/GENERATION_GUIDELINES.md`.
2. **Extract Used Anchors (Anti-Duplication)**:
   - Run:
     ```bash
     python3 scripts/publish_book.py --list-anchors
     ```
   - Every historical event, clinical case, or primary experiment already used as a chapter anchor in an existing book is **strictly off-limits** as a primary chapter anchor in the new volume.
3. **Select or Synthesize the Tier-2 Topic Profile**:
   - Classify the book's topic into one of the four profiles in `GENERATION_GUIDELINES.md`:
     - **Profile A**: Physical Systems, Infrastructure & Engineering
     - **Profile B**: Biological, Neural & Affective Control Loops
     - **Profile C**: Decision Theory, Economics & Enterprise Mechanics
     - **Profile D**: Intellectual Ruptures & Consensus Breaking
   - If the topic spans a new domain (e.g., *Epidemiology*, *Monetary Architecture*, *Sensory Ethology*), define its custom **Narrative Anchor** (what counts as a concrete scene) and **Forensic Engine** (when to use display equations vs. empirical ledgers) while preserving all **Seven Tier-1 Universal Laws**.

---

## Stage 2: Lock the 12-Chapter Dossier (`dossiers/<slug>.json`)

Before drafting a single sentence of book prose, write a structured JSON blueprint to `/Users/niraj/book-writer/dossiers/<slug>.json` containing:
- `slug` (hyphenated, e.g., `"geometries-of-contagion"`), `file` (underscored, e.g., `"geometries_of_contagion.md"`), `title`, `subtitle` (zero colons!), `category`, `profile`, `accent`, `bg`, `theme`.
- `chapters`: Array of 12 chapter objects, each specifying:
  1. `chapter`: `1` through `12`
  2. `title`: Plainspoken chapter title (zero colons)
  3. `subtitle`: Concrete chapter subtitle (zero colons)
  4. `opening_door`: Deterministically rotated across `"Door A (Scene)"`, `"Door B (Constraint/Paradox)"`, and `"Door C (Artifact/Measurement)"` so no more than 4 chapters open with a date/time phrase.
  5. `historical_anchor`: Exact named person(s), year/date, location, and verifiable primary source/experiment (verified not in `--list-anchors`).
  6. `formalism_mode`: Either `"equation"` (with the exact real governing equation written out) or `"ledger_or_list"` (explicitly forbidding display equations so the writer never invents "math cosplay").
  7. `exit_fact`: The concrete historical, physical, or clinical fact on which the chapter will end cleanly (zero moralizing sermons).

---

## Stage 3: Batched Chapter Drafting (~250-Word Introduction + 650–850 Words per Chapter)

To prevent LLM context-window compression (where chapters shrink to 300 words by Chapter 5):
- Spawn a dedicated author subagent (or 2 parallel subagents drafting Chapters 1–6 and Chapters 7–12) equipped with the locked `dossiers/<slug>.json` blueprint and `GENERATION_GUIDELINES.md`.
- **Introduction Rule (~250 Words, No Chapter Summaries)**: The `### Introduction` must be approximately **200–275 words** (~250 words). It should introduce the core topic and structural thesis only—**never** summarize or preview the individual chapters.
- Enforce the **650–850 word** target per chapter body (total book ~9,000–10,000 words).
- Formatting requirements:
  - Escape all literal currency dollar signs (`\$100`).
  - Never wrap bare numbers in `$...$` (write `50`, not `$50$`).
  - Use `\sum\nolimits` whenever a summation symbol appears inside a `\frac{...}{...}` numerator or denominator.

---

## Stage 4: Deterministic Quality Gate (`scripts/validate_book.py`)

Run the hard validator script against the completed manuscript:

```bash
python3 scripts/validate_book.py <slug_with_underscores>.md
```

- The validator checks:
  1. Exact 3-line headers (`### Chapter N` / `# Title` / `## Subtitle`) with zero colons.
  2. Chapter word counts (600–900 words per chapter).
  3. Concrete historical date/year anchors in every chapter.
  4. Opening-door rotation (fails if $>4$ chapters open with `"In/On/At [Date]"`).
  5. Clean exits & anti-hyperbole (fails on moralizing exit sermons or banned words).
  6. Math cosplay detection, raw LaTeX leak detection, and Node KaTeX compilation.
- **Self-Healing Loop**: If `validate_book.py` reports any `ERROR` or `WARN`, fix the exact offending chapter(s) and re-run `validate_book.py` until it exits with code `0` (`PASS`).

---

## Stage 5: Automated Cover Generation, Catalog Registration & Deployment

Once `validate_book.py` passes with zero errors:

1. **Publish locally (generates SVG cover, updates `js/books-data.js`, `index.html`, and `sitemap.xml`)**:
   ```bash
   python3 scripts/publish_book.py \
     --slug <slug> \
     --category "<Category>" \
     --accent "<#hex>" \
     --bg "<#hex>" \
     --theme "<network-wave|harmonic-rings|lattice>"
   ```
2. **Verify full library integrity**:
   ```bash
   python3 scripts/validate_book.py --all
   ```
3. **Commit, push, and deploy to production (`https://www.alexandria.press`)**:
   ```bash
   git add . && git commit -m "Publish new volume: <Title>" && git push origin main && npx vercel --prod --yes
   ```
