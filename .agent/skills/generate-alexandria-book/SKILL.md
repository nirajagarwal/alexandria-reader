---
name: generate-alexandria-book
description: End-to-end autonomous pipeline for generating, validating, and publishing new volumes for Alexandria Press (alexandria.press). Trigger whenever the user asks to generate a new book, pick the next book from the queue, or synthesize a volume on a new topic.
---

# Generate Alexandria Book — Locked Manifesto & Two-Tier Profile Pipeline

> [!IMPORTANT]
> **LOCKED PROMPTS & GUIDELINES (`prompt-lock.json`)**: [`alexandria_manifesto.md`](file:///Users/niraj/book-writer/alexandria_manifesto.md), [`GENERATION_GUIDELINES.md`](file:///Users/niraj/book-writer/GENERATION_GUIDELINES.md), [`scripts/create_book_pipeline.py`](file:///Users/niraj/book-writer/scripts/create_book_pipeline.py), and this [`SKILL.md`](file:///Users/niraj/book-writer/.agent/skills/generate-alexandria-book/SKILL.md) are **LOCKED**.
> - **NEVER** modify `alexandria_manifesto.md`, `GENERATION_GUIDELINES.md`, `scripts/create_book_pipeline.py`, or this `SKILL.md`—and never inject ad-hoc prompt overrides—without first asking the user and receiving explicit permission.
> - **MANDATORY PRE-GENERATION QUESTION**: On **every** future book generation or book rewrite request, you MUST ask the user whether to proceed with the locked prompt and guidelines as-is (`Alexandria Manifesto + Two-Tier Profile Architecture + Form-Specific Branching`) or whether they want to make any changes to the prompt/guidelines for this volume.

---

## Stage 0: Mandatory Prompt-Lock & User Confirmation Gate

Whenever the user asks to generate a new volume or rewrite an existing volume:
1. **Verify the Prompt Lock**:
   ```bash
   python3 scripts/create_book_pipeline.py --verify-lock
   ```
2. **Present the Book Blueprint & Ask About Prompt Changes**:
   - Present the proposed **Title** (never starting with `"Twelve "`), **Subtitle** (zero colons), **Format (`mode`: `facet` / `biography` / `landscape` / `listicle`)**, **Tier 2 Profile (`A` / `B` / `C` / `D`)**, and **12-Chapter Arc**.
   - **Explicitly ask the user** (via `ask_question` or direct confirmation):
     - *"The Alexandria Press prompts and guidelines are locked (`Tier 1 Universal Laws` + `Tier 2 Profile A–D` + `Form-Specific Branching`). Should we generate this volume using the locked prompt as-is, or would you like to make any changes to the prompt/guidelines?"*
   - Only if the user explicitly requests a prompt/guideline modification should you edit the prompt files and run `python3 scripts/create_book_pipeline.py --update-lock`.

---

## Stage 1: Topic Analysis, Four Volume Formats & Two-Tier Profiles

1. **Read the Locked Core Rules**:
   - View `/Users/niraj/book-writer/alexandria_manifesto.md` and `/Users/niraj/book-writer/GENERATION_GUIDELINES.md`.
2. **Extract Used Anchors (Anti-Duplication)**:
   ```bash
   python3 scripts/publish_book.py --list-anchors
   ```
   Every historical event, clinical case, or primary experiment already used as a chapter anchor in an existing book is strictly off-limits as a primary chapter anchor in a new volume.
3. **Select the Structural Form (`mode`)**:
   - **`"facet"` / `"mechanisms"` (12-Facet Mechanisms)**: Each chapter pairs a concrete historical scene, experiment, clinical case, or primary text (*The Narrative Vector*) with its underlying physical, biological, philosophical, or institutional mechanism (*The Forensic Deep-Dive*).
   - **`"biography"` (12-Facet Biography)**: Book title MUST be the person's name (`# Claude Shannon`, `# Alan Turing`). Chapter 1 unpacks their formative intellectual crucible; Chapters 2–12 unpack 11 distinct theorems, machines, experiments, or conceptual breakthroughs.
   - **`"landscape"` (Contextual Landscape)**: Chapter 1 defines the core anchor concept (`lens: "anchor"`, `verb: "anchor"`); Chapters 2–12 explore 11 neighboring concepts across building blocks, mechanisms, origins, contrasts, cases, consequences, and open questions, bridging via `what`, `why_here`, and 3 `background_nodes` in clear plain English (zero academic deepspeak).
   - **`"listicle"` (12×12 Prospected Highlights)**: Examines 12 subsystems or facets of an everyday subject through **12 standalone paragraphs** (`48–56` words each) separated by **11 standalone centered spaced-dot (`· · ·`) lines** per chapter (144 highlights total). Written in crisp, objective third-person authority with zero second-person (`"When you..."`, `"Your..."`) filler, zero display equations, and zero SVG diagrams.
4. **Select the Tier 2 Topic-Specific Profile (`profile`)**:
   - **Profile A (`Physical, Chemical & Engineering Systems`)**: Pair the concrete historical failure, invention, or physical anomaly with the exact governing thermodynamic, mechanical, or chemical mechanism.
   - **Profile B (`Biological, Ecological, Cognitive & Medical Systems`)**: Pair the clinical anomaly, evolutionary puzzle, or classic experiment with the biological, neural, physiological, or philosophical mechanism.
   - **Profile C (`Strategy, Economics, Law, History & Human Behavior`)**: Pair the historical crisis, institutional invention, or strategic turning point with the game-theoretic, economic, or structural incentive mechanism.
   - **Profile D (`Scientific Discovery, Biography, Philology & Contemplative Philosophy`)**: Pair the investigator, thinker, or primary text with the exact deductive method, apparatus, or philosophical argument that broke entrenched consensus.

---

## Stage 2: Lock the 12-Chapter Dossier (`dossiers/<slug>.json`)

Write a structured JSON blueprint to `/Users/niraj/book-writer/dossiers/<slug>.json` containing:
- `slug` (hyphenated), `file` (`"books/<slug>.md"`), `title` (never starting with `"Twelve "`), `subtitle` (zero colons), `category`, `profile` (`"A"`, `"B"`, `"C"`, or `"D"`), `mode` (`"facet"`, `"mechanisms"`, `"biography"`, `"landscape"`, or `"listicle"`), `accent`, `bg`, `theme`.
- `creator_constraints`:
  ```json
  {
    "min_diagrams": 0,
    "quotes_allowed": false
  }
  ```
- `chapters`: Array of 12 chapter objects:
  - **For `"facet"`, `"mechanisms"`, and `"biography"`**: `chapter`, `title`, `subtitle`, `opening_door` (`"A: Experiment/Case"`, `"B: Constraint/Paradox"`, or `"C: Artifact/Measurement"`), `historical_anchor`, `formalism_mode` (`"prose"`, `"equation"`, `"ledger_or_list"`, or `"diagram"`), `exit_fact`.
  - **For `"landscape"`**: Same fields plus `lens`, `verb`, `what`, `why_here`, and `background_nodes` (3 items with `label`, `what`, `whyHere`).
  - **For `"listicle"`**: `chapter`, `title`, `subtitle`, `historical_anchor`, `formalism_mode` (`"listicle"`), `prospected_seeds` (array of 12 concrete, number-anchored seeds), `exit_fact`.

---

## Stage 3: Synthesize Manuscript (`books/<slug>.md`)

Use either `python3 scripts/create_book_pipeline.py` (Gemini 4 Argon Batch API) or spawn a dedicated author subagent with the locked **Canonical Alexandria Manifesto Prompt**:

```markdown
Read `/Users/niraj/book-writer/alexandria_manifesto.md`, `/Users/niraj/book-writer/GENERATION_GUIDELINES.md`, and `/Users/niraj/book-writer/dossiers/<slug>.json`.
Write `/Users/niraj/book-writer/books/<slug>.md` and validate it with `python3 scripts/validate_book.py books/<slug>.md` until it passes with 0 errors and 0 warnings.

### Locked Alexandria Manifesto & Two-Tier Profile Laws:
1. **Authorial Humility & High Intellectual Trust**: "We are not writing to impress. The material we have itself is impressive. We need to get out of the way and let the material speak for itself." Write for a curious, intelligent adult reader. Never use pretentious academic/neuroimaging deepspeak, and never talk down with condescending pop-science baby-talk.
2. **The Contrapuntal Cadence (Essay Modes: `facet`, `biography`, `landscape`)**: Weave the **Narrative Vector** (the historical crisis, clinical anomaly, experiment, or thinker) with the **Forensic Deep-Dive** (the step-by-step physical, biological, philosophical, or institutional mechanism). Allow natural multi-clause analytical sentences (`22–28` words/sentence average, strictly `<= 28.5` w/s). Never chop prose into robotic staccato telegraph sentences.
3. **12×12 Prospected Highlights (`listicle` Mode Only)**: Write 12 chapters where each chapter consists of **12 standalone paragraphs** (`48–56` words each, `560–690` words per chapter, `16–22` w/s) separated by **11 standalone centered `· · ·` lines**. Use crisp, objective third-person empirical authority—never second-person conversational filler (`"When you..."`, `"Your..."`).
4. **Concise Topic-Only Introduction (~200–270 Words)**: Frame the core intellectual tension or physical constraint of the subject directly. Never summarize, list, or preview the 12 chapters.
5. **Organic Formalisms (Zero Math Cosplay)**: Follow each chapter's `formalism_mode` (`"prose"`, `"equation"`, `"ledger_or_list"`, or `"diagram"`). Include `$$...$$` display equations ONLY where a genuine mathematical, physical, chemical, or statistical law exists. Never invent conceptual pseudo-equations.
6. **Zero Direct Quotations & Zero Novelistic Micro-Details**: Paraphrase all statements in crisp indirect speech (zero 5+ word strings inside `"..."`). Never include weekdays (`"On a Tuesday morning"`), weather cold-opens, or hyphenated/spelled-out character ages (`"forty-three-year-old"`).
7. **Clean Exits & Hygiene**: End every chapter directly on the concrete `exit_fact` with zero moralizing summary sentences (`"proved that"`, `"demonstrated that"`, `"Ultimately"`). Use `### Chapter N` / `# Title` / `## Subtitle` with zero colons, escape literal currency dollar signs (`\$100`), and never wrap bare numbers in `$50$`.
```

---

## Stage 4: Deterministic Quality Gate & Publication

1. **Validate Manuscript**:
   ```bash
   python3 scripts/validate_book.py books/<slug>.md
   ```
2. **Publish Volume (`scripts/publish_book.py`)**:
   ```bash
   python3 scripts/publish_book.py \
     --slug <slug> \
     --category "<Category>" \
     --accent "<#hex>" \
     --bg "<#hex>" \
     --theme "<theme>"
   ```
3. **Verify Entire Repository & Lock Integrity**:
   ```bash
   python3 scripts/validate_book.py --all
   python3 tests/test_reader.py
   ```
