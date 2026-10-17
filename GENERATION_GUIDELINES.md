# Alexandria Press — Book Generation Guidelines & Prompt Architecture

This document defines the minimal, high-trust editorial architecture for Alexandria Press (`alexandria.press`).

---

## Core Editorial Principle: Minimal Pointers, High Intellectual Trust

Over-constraining a frontier model with rigid formatting schedules, forced sentence-length caps, or instructions to "write simply for any reader" causes **mean reversion**: the model spends its attention budget on checklist compliance and retreats to the safest, most overused 101-level anecdotes in its pretraining distribution.

Conversely, feeding a model a dense checklist of sub-nodes to cram into 600 words causes **academic compression**: joyless, Latinate deepspeak where terms are defined rather than ideas explored.

To preserve the intellectual electricity of our best volumes (*Singular Minds*, *Architectures of Choice*, *Sensory Worlds*, *Fictions of Order*), prompts must stay **minimal, high-trust, and thesis-driven**:

1. **Thesis-Driven Chapters (Never Safe Anecdotes)**
   - Every chapter must be built around a **sharp, non-obvious thesis, paradox, or structural insight**.
   - Historical episodes, clinical patients, experiments, and contemplative texts are **servants of the argument**, not the point of the chapter.
   - Avoid overused pop-science chestnuts (or if a classic problem is unavoidable, bypass the 101-level textbook summary and expose the deeper mathematical, structural, or philosophical fault line underneath).

2. **High Intellectual Voltage, Zero Pretension**
   - Write for an intellectually ambitious adult reader. Never talk down to the reader in a breezy explainer tone ("Imagine your brain inside a dark box..."), and never use pretentious academic throat-clearing ("perceptual disengagement and motor quiescence" when you mean "falling asleep").
   - Use precise technical, mathematical, or philosophical concepts whenever they do real explanatory work, and unpack them with crystalline clarity.

3. **Organic Formalisms (No Pre-Assigned Schedules)**
   - **Never** force a fixed schedule of equations, diagrams, or bullet lists across chapters.
   - Include a display equation (`$$...$$`) **only** when a genuine mathematical, physical, or information-theoretic law is the sharpest way to state the argument.
   - Include a schematic SVG diagram (` ```svg `) or a structured bullet list **only** when a topology, comparison, or multi-part distinction is clearer structured than in continuous prose. When pure essay prose is stronger, use pure prose.

4. **The 12-Chapter Container (~550–750 Words per Chapter)**
   - Every volume consists of a concise **Introduction (~200–280 words)** that frames the core conceptual tension of the book (without listing or previewing chapters), followed by **12 self-contained chapters** (~550–750 words each; validator window `500–800` words).
   - Book titles must never start with the prefix `"Twelve "` (use `# Virtues`, `# Vaccines`, `# Emotions`, `# Plants`, `# Materials`).

5. **Mechanical & Factual Hygiene (Enforced by `scripts/validate_book.py`)**
   - Keep formatting rules out of the creative way while enforcing clean production hygiene:
     - **3-Line Headers (No Colons)**: `### Chapter N` / `# Title` / `## Subtitle`.
     - **Concrete Grounding**: Anchor every chapter in real experiments, thinkers, or primary records (verified via 1 Google Search per chapter in Stage 2).
     - **Paraphrase Only (No 5+ Word Direct Quotes)**: Paraphrase all statements in indirect speech so fabricated quotes are impossible.
     - **Clean Exits**: End each chapter when the argument lands—never tack on a moralizing summary sentence (*"This proved that..."*, *"Ultimately..."*, *"serves as a testament"*).
     - **LaTeX & SVG Hygiene**: Escape literal currency dollar signs (`\$100`), use valid KaTeX syntax, and keep any SVG diagram inside `viewBox="0 0 600 H"` ($140 \le H \le 250$) using CSS theme variables.

---

## Structural Modes

1. **12-Facet Essays & Mechanisms (`mode: "facet"` / `format: "mechanisms"`)**
   - Examines a rich phenomenon from 12 distinct structural, scientific, philosophical, or historical angles. Each chapter is a self-contained essay driven by a sharp thesis and concrete empirical or historical evidence.

2. **12-Facet Biographies (`mode: "facet"` / `format: "biography"`)**
   - Uses the subject's name as the main book title (`# Claude Shannon`, `# Richard Feynman`, `# Alan Turing`). Chapter 1 examines the thinker's formative cognitive style; Chapters 2–12 each unpack a decisive theorem, machine, experiment, or intellectual collision.

3. **Conceptual Landscapes (`mode: "landscape"` / `format: "landscape"`)**
   - Chapter 1 examines the anchor concept itself; Chapters 2–12 explore 11 neighboring concepts that constrain, contrast with, or illuminate the anchor. Focus on the *structural relationship* between the neighbor and the core topic—never reduce a chapter to a glossary definition of background nodes.

4. **12×12 Prospected Highlights (`mode: "listicle"` / `format: "highlights"`)**
   - Each of the 12 chapters examines one subsystem through 12 standalone paragraphs separated by 11 centered middle-dot lines (`· · ·`), where each paragraph delivers a counterintuitive, quantitative insight.
