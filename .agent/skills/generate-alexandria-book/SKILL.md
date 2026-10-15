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
- `slug` (hyphenated, e.g., `"geometries-of-contagion"`), `file` (underscored, e.g., `"geometries_of_contagion.md"`), `title`, `subtitle` (zero colons!), `category`, `profile`, `mode` (`"facet"` for Mode I modular essays on a theme, or `"arc"` for Mode II continuous 12-chapter narrative trajectory), `accent`, `bg`, `theme`.
- **Title Distinctness Rule**: Never reuse head nouns already used in existing Alexandria Press book titles (do NOT use *Architectures*, *Engines*, *Topologies*, *Thresholds*, *Asymmetries*, *Tales*, *Worlds*, *Instruments*, *Ghosts*, *Fictions*, or *Bonds* in new book titles).
- `chapters`: Array of 12 chapter objects, each specifying:
  1. `chapter`: `1` through `12`
  2. `title`: Plainspoken chapter title (zero colons)
  3. `subtitle`: Concrete chapter subtitle (zero colons)
  4. `opening_door`: Deterministically rotated across `"Door A (Scene)"`, `"Door B (Constraint/Paradox)"`, and `"Door C (Artifact/Measurement)"` so no more than 4 chapters open with a date/time phrase.
  5. `historical_anchor`: Exact named person(s), year/date, location, verifiable primary source/experiment (verified not in `--list-anchors`), and where available, a brief documented verbatim quote from the primary record.
  6. `formalism_mode`: Either `"equation"` (with the exact real governing equation written out) or `"ledger_or_list"` (using a clear Markdown bulleted/numbered list for clarity, explicitly forbidding fake "math cosplay").
  7. `exit_fact`: The concrete historical, physical, or clinical fact on which the chapter will end cleanly (zero moralizing sermons).

---

## Stage 3: Batched Chapter Drafting (~250-Word Introduction + 650–850 Words per Chapter)

To prevent LLM context-window compression (where chapters shrink to 300 words by Chapter 5), spawn a dedicated author subagent (or 2 parallel subagents) using the **Canonical Manifesto Prompt Template** below so the Alexandria Manifesto is baked directly into every generation call:

```markdown
Read `/Users/niraj/book-writer/alexandria_manifesto.md`, `/Users/niraj/book-writer/GENERATION_GUIDELINES.md`, and `/Users/niraj/book-writer/dossiers/<slug>.json`.
Write `/Users/niraj/book-writer/<filename>.md` and validate it with `python3 scripts/validate_book.py <filename>.md` until it passes with 0 errors and 0 warnings.

### Baked-In Alexandria Manifesto Laws (Non-Negotiable):
1. **Structural Modality (5-Minute Chapters / 1-Hour Book)**: Default to **Mode I (Modular Facets)**—12 self-contained 5-minute stories examining a single theme from 12 angles without requiring cross-chapter continuity ("shorts, not the long video")—unless `dossiers/<slug>.json` explicitly specifies **Mode II (Continuous Arc)**.
2. **Authorial Humility & Honest Machine Synthesis**: "Do not be fashioned according to the age"—we do not hide machine synthesis or imitate commercial literary padding. Use plainspoken syntax, everyday nouns, and active verbs. Zero purple prose or hyperbole ("breathtaking", "awe-inspiring", "mind-boggling", "staggering", "paradigm-shifting"). Keep structured bullet lists wherever they bring clarity.
3. **Concise Topic-Only Introduction (~250 Words)**: The `### Introduction` must be **200–275 words** (strictly $\le 300$ words). Introduce the core topic and structural thesis only—**NEVER summarize, list, or preview the individual chapters**.
4. **Mandatory Concrete Grounding & Verbatim Quotes**: Every chapter must anchor its mechanism in real historical events, physical experiments, clinical cases, or primary records with named people, dates, places, and exact measurements. Sprinkle 1–2 brief, documented **verbatim quotes** from historical actors or primary texts to humanize the story without inventing dialogue.
5. **Sentence Cadence & Length Variance (No Staccato Clichés)**: Avoid uniform 28–35 word sentences and repetitive participial-phrase openers ("Working alongside..., X did Y"). Aim for a smaller average sentence length (**~16–22 words**) with natural variance by splitting sprawling multi-clause sentences into clean declarative statements. **Warning**: Do NOT use cheesy LLM "short punchy sentences" (dramatic 2–4 word fragments like "It failed." or "Everything changed.").
6. **Mechanism Completeness (650–850 Words per Chapter)**: Unpack *how* the mechanism worked step by step across 5–8 paragraphs. Never compress a chapter into a 300-word sketch.
7. **Earned Formalisms Only (Zero Math Cosplay)**: Follow each chapter's `formalism_mode` in `dossiers/<slug>.json`. Include `$$...$$` display equations ONLY in chapters marked `"equation"` (where a real mathematical, physical, chemical, or statistical law exists). In chapters marked `"ledger_or_list"`, use a clean Markdown bulleted/numbered list—never invent fake pseudo-equations!
8. **Rotate the 3 Opening Doors**: Follow each chapter's `opening_door` (`A: Scene`, `B: Constraint/Paradox`, `C: Artifact/Measurement`). Ensure $\le 3$ chapters across the entire book begin their first sentence with `"In/On/At [Date]"`.
9. **Clean Exits (Zero Concluding Sermons)**: End every chapter directly on the concrete `exit_fact`. Never add a moralizing summary sentence ("X showed that...", "This demonstrated that...", "Ultimately...", "serves as a testament").
10. **Strict 3-Line Headers & LaTeX Hygiene**: Use `### Chapter N` / `# Title` / `## Subtitle` with zero colons. Escape literal currency dollar signs (`\$100`), never wrap bare numbers in `$50$`, and use `\sum\nolimits` inside `\frac{...}{...}`.
```

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
