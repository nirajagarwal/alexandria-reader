---
name: generate-alexandria-book
description: End-to-end autonomous pipeline for generating, validating, and publishing new volumes for Alexandria Press (alexandria.press). Trigger whenever the user asks to generate a new book, pick the next book from the queue, or synthesize a volume on a new topic.
---

# Generate Alexandria Book — Universal 12-Facet & Two-Pass Creator Pipeline

This skill executes the drift-proof pipeline for creating volumes for **Alexandria Press (`alexandria.press`)**—**"Deep Learning for Humans"** designed to train the reader's mental network through compressed, concrete mechanisms rather than comprehensive textbooks or vocational curricula.

Every Alexandria volume uses the **Universal 12-Facet Container** (a ~250-word topic-only Introduction + twelve 5-minute chapters of 550–720 words each) and follows the **Two-Pass Creator Loop**:
1. **Topic Input $\rightarrow$ 3–4 Forks on the Road**
2. **Fork Selection $\rightarrow$ `v1` Synthesis & Validation**
3. **Creator Steering Prompt ("Director's Cut") $\rightarrow$ `v2` Regeneration & Publication**

---

## Stage 1: Topic Analysis, Fork Proposals & Anchor Deduplication

1. **Read the Core Rules**:
   - View `/Users/niraj/book-writer/alexandria_manifesto.md` and `/Users/niraj/book-writer/GENERATION_GUIDELINES.md`.
2. **Extract Used Anchors (Anti-Duplication)**:
   - Run:
     ```bash
     python3 scripts/publish_book.py --list-anchors
     ```
   - Every historical event, clinical case, or primary experiment already used as a chapter anchor in an existing book is **strictly off-limits** as a primary chapter anchor in the new volume.
3. **Select the Structural Form (`mode`) & Present 3–4 Forks on the Road**:
   - Alexandria supports **three structural forms** inside the 12-chapter container:
     1. **`"facet"` (Narrative-Mechanism Facet)**: Each chapter pairs a concrete historical event/experiment with its underlying physical, biological, or institutional mechanism.
     2. **`"listicle"` (Prospected 12-Gem Fleuron Listicle)**: When narrative is not the right fit and the reader wants the high-voltage highlights (e.g., *The Human Body*, where Chapter 1 is 12 dynamite facts about the Heart). Each chapter combines [`topic-prospector`](file:///Users/niraj/.gemini/config/plugins/topic-prospector/skills/topic-prospector/SKILL.md) perpendicular seeds with domain knowledge to deliver **12 self-contained paragraphs** (~45–55 words each) separated by **11 standalone centered fleuron (`❦`) lines** (never numbered lists!).
     3. **`"landscape"` (Knowra Contextual Landscape)**: Inspired by `knowra.com` ([`/Users/niraj/knowra-browser/lib/prompts.ts`](file:///Users/niraj/knowra-browser/lib/prompts.ts)). Given a central topic $X$, Chapter 1 examines the anchor concept itself, and Chapters 2–12 explore **11 adjacent concepts** across Knowra's lenses (`Building blocks`, `Mechanism`, `Origins`, `Contrasts`, `Neighbors`, `Consequences`, `Cases`, `Open questions`) and moves (`zoom-in`, `zoom-out`, `go`, `contrast`), primed by linked `background_nodes` so the reader learns the topic in context with its surrounding landscape.

---

## Stage 2: Lock the 12-Chapter Dossier (`dossiers/<slug>.json`)

Before drafting a single sentence of book prose, write a structured JSON blueprint to `/Users/niraj/book-writer/dossiers/<slug>.json` containing:
- `slug` (hyphenated), `file` (underscored), `title`, `subtitle` (zero colons!), `category`, `profile`, `mode` (`"facet"`, `"listicle"`, or `"landscape"`), `accent`, `bg`, `theme`.
- `creator_constraints` (optional object): Encodes any explicit creator rules so `scripts/validate_book.py` enforces them deterministically:
  - `"require_quote_per_chapter": true` — requires at least one documented verbatim quote (`"..."`) in every chapter (Chapters 1–12).
  - `"min_diagrams": 2` — requires at least $N$ schematic SVG diagrams (`2–4`) across the volume.
- **Title Distinctness Rule**: Avoid overused head nouns already saturated in the catalog (*Architectures*, *Engines*, *Topologies*, *Thresholds*, *Asymmetries*, *Tales*, *Worlds*, *Instruments*, *Ghosts*, *Fictions*, *Bonds*) unless deliberately pairing with a creator's chosen title.
- `chapters`: Array of 12 chapter objects:
  - **For `"facet"` mode**: `chapter`, `title`, `subtitle`, `opening_door`, `historical_anchor`, `verbatim_quote`, `formalism_mode` (`"equation"`, `"diagram"`, or `"ledger_or_list"`), `exit_fact`.
  - **For `"listicle"` mode**: `chapter`, `title`, `subtitle`, `prospected_seeds` (array of 12 sharp, perpendicular, number-anchored seeds combining `topic-prospector` cross-disciplinary insights with core domain knowledge, which will become the 12 `❦`-separated paragraphs of that chapter).
  - **For `"landscape"` mode**: `chapter`, `title`, `subtitle`, `lens` (Knowra lens: `anchor`, `building-blocks`, `mechanism`, `origins`, `contrasts`, `neighbors`, `consequences`, `cases`, `open-questions`), `verb` (`anchor`, `zoom-in`, `zoom-out`, `go`, `contrast`), `what` (context-free definition), `why_here` (specific connection to the central topic), `background_nodes` (array of 4–5 linked sub-concepts with `label`, `what`, `whyHere`), and `formalism_mode`.

---

## Stage 3: Synthesize Manuscript (`v1` or Steered `v2`)

To prevent both context-window truncation and verbose drift toward the LLM's preferred mean, spawn a dedicated author subagent using the **Canonical Manifesto Prompt Template** below so the Alexandria Manifesto is baked directly into every generation call:

```markdown
Read `/Users/niraj/book-writer/alexandria_manifesto.md`, `/Users/niraj/book-writer/GENERATION_GUIDELINES.md`, and `/Users/niraj/book-writer/dossiers/<slug>.json`.
Write `/Users/niraj/book-writer/<filename>.md` and validate it with `python3 scripts/validate_book.py <filename>.md` until it passes with 0 errors and 0 warnings.

### Baked-In Alexandria Manifesto Laws (Non-Negotiable):
1. **Universal 12-Facet Container ("Deep Learning for Humans")**: We are not writing a comprehensive textbook or vocational curriculum; 12 facets is enough. Write 12 self-contained 5-minute facets examining the subject from 12 angles ("shorts, not the long video").
2. **Authorial Humility & Honest Machine Synthesis**: "Do not be fashioned according to the age"—we do not hide machine synthesis or imitate commercial literary padding. Use plainspoken syntax, everyday nouns, and active verbs. Zero purple prose or hyperbole ("breathtaking", "awe-inspiring", "mind-boggling", "staggering", "paradigm-shifting"). Keep structured bullet lists wherever they bring clarity.
3. **Concise Topic-Only Introduction (~250 Words)**: The `### Introduction` must be **200–275 words** (strictly `140–300` words). Introduce the core topic and structural thesis only—**NEVER summarize, list, or preview the individual chapters**.
4. **Mandatory Concrete Grounding & Verbatim Quotes**: Every chapter must anchor its mechanism in real historical events, physical experiments, clinical cases, or primary records with named people, dates, places, and exact measurements. Include documented **verbatim quotes** from historical actors or primary texts (and if `require_quote_per_chapter` is true, include at least one verbatim quote in all 12 chapters).
5. **Sentence Cadence & Length Variance (17–22 Words/Sentence)**: Prevent drift toward the LLM's 33-word multi-clause mean and avoid repetitive participial-phrase openers ("Working alongside..., X did Y"). Keep the average sentence length at **17–22 words** ($\le 24.0$ w/s) by writing direct declarative sentences. **Warning**: Do NOT use cheesy LLM "short punchy sentences" (dramatic 2–4 word fragments like "It failed." or "Everything changed.").
6. **High-Density Compression (550–720 Words per Chapter)**: Our punchiness comes from compression. Unpack *how* the mechanism worked step by step across 5–6 crisp paragraphs (**550–720 words per chapter**, ~600–650 words ideal; hard gate `520–760`). Do not pad chapters to 850 words.
7. **Earned Formalisms Only (Zero Math Cosplay)**: Follow each chapter's `formalism_mode` in `dossiers/<slug>.json`. Include `$$...$$` display equations ONLY in chapters marked `"equation"` (where a real mathematical, physical, chemical, or statistical law exists). In chapters marked `"ledger_or_list"`, use a clean Markdown bulleted/numbered list—never invent fake pseudo-equations!
8. **Rotate the 3 Opening Doors**: Follow each chapter's `opening_door` (`A: Scene`, `B: Constraint/Paradox`, `C: Artifact/Measurement`). Ensure $\le 3$ chapters across the entire book begin their first sentence with `"In/On/At [Date]"`.
9. **Clean Exits (Zero Concluding Sermons)**: End every chapter directly on the concrete `exit_fact`. Never add a moralizing summary sentence ("X showed that...", "This demonstrated that...", "Ultimately...", "serves as a testament").
10. **Strict 3-Line Headers & LaTeX Hygiene**: Use `### Chapter N` / `# Title` / `## Subtitle` with zero colons. Escape literal currency dollar signs (`\$100`), never wrap bare numbers in `$50$`, and use `\sum\nolimits` inside `\frac{...}{...}`.
11. **Earned Schematic Diagrams (` ```svg ` — 2 to 4 Per Book Max)**: In chapters marked `"diagram"`, include a clean ` ```svg ` block with `viewBox="0 0 600 H"` ($140 \le H \le 250$), `data-caption="FIG. N.1 — ..."`, CSS theme variables (`var(--text-color)`, `var(--text-muted)`, `var(--accent-color)`, `var(--border-color)`, `var(--card-bg)`), $\le 34$ SVG primitives, and `<rect>` box widths at least `24px` wider than their enclosed `<text>`.
```

---

## Stage 4: Deterministic Quality Gate (`scripts/validate_book.py`)

Run the hard validator script against the completed manuscript:

```bash
python3 scripts/validate_book.py <slug_with_underscores>.md
```

- The validator checks:
  1. Exact 3-line headers (`### Chapter N` / `# Title` / `## Subtitle`) with zero colons.
  2. Introduction length (`140–300` words, zero chapter previews), chapter word counts (`520–760` words), and sentence cadence ($\le 24.0$ words/sentence).
  3. Concrete historical date/year anchors in every chapter, plus verbatim quote presence in every chapter when `--require-quotes` or `creator_constraints.require_quote_per_chapter` is enabled.
  4. Opening-door rotation (fails if $>4$ chapters open with `"In/On/At [Date]"`).
  5. Clean exits & anti-hyperbole (fails on moralizing exit sermons or banned words).
  6. Math cosplay detection, raw LaTeX leak detection, and Node KaTeX compilation.
  7. Schematic SVG diagram validation ($\le 1$ per chapter, $\le 4$ per book, valid XML, `viewBox="0 0 600 H"`, theme CSS variables, `<rect>` text containment, and zero text/box collisions).
- **Self-Healing Loop**: If `validate_book.py` reports any `ERROR` or `WARN`, fix the exact offending chapter(s) and re-run `validate_book.py` until it exits with code `0` (`PASS`).

---

## Stage 5: Creator Steering Pass ("Director's Cut") & Publication (`v2` & Done)

1. **Creator Steering Prompt (`v1` $\rightarrow$ `v2`)**:
   - After `v1` is synthesized, if the creator provides steering input (e.g., *"I want to see at least one quote per chapter"*, *"Swap Chapter 8 for his Brazil expedition"*, *"Change the title to Twelve Facets"*):
     1. Update `dossiers/<slug>.json` (including `creator_constraints` such as `"require_quote_per_chapter": true`).
     2. Regenerate the affected chapters (or full manuscript `v2`) and run `python3 scripts/validate_book.py <filename>.md --require-quotes`.
     3. Once `v2` passes with 0 errors, lock the book and call it done.
2. **Publish & Deploy (`scripts/publish_book.py`)**:
   ```bash
   python3 scripts/publish_book.py \
     --slug <slug> \
     --category "<Category>" \
     --accent "<#hex>" \
     --bg "<#hex>" \
     --theme "<network-wave|harmonic-rings|lattice>"
   python3 scripts/validate_book.py --all
   git add . && git commit -m "Publish volume: <Title>" && git push origin main && npx vercel --prod --yes
   ```

