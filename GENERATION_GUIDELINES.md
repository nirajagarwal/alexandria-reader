# Alexandria Press — Book Generation Guidelines & Prompt Architecture

This document defines the two-tier generation process for Alexandria Press (`alexandria.press`):
1. **Tier 1: The Universal Core Prompt** — Binding rules applied to every volume without exception.
2. **Tier 2: Topic-Specific Prompt Profiles** — Domain-adapted instructions that specify what constitutes the *Narrative Vector* and the *Forensic Deep-Dive* for a given subject.

---

### Tier 1: Universal Core Guidelines (Common to All Books)

Every book generation prompt must include and enforce these universal constraints:

1. **The Universal 12-Facet Volume ("Deep Learning for Humans")**
   - Alexandria does not publish comprehensive textbooks or vocational curricula to teach a narrow skill. We publish **"Deep Learning for Humans"**—high-signal, non-exhaustive training volumes that wire the reader's internal neural network through compressed structural examples.
   - Because we do not need to be comprehensive, **12 facets is always enough**. Every volume consists of **12 self-contained chapters** (~550–720 words each, ~5 minutes per chapter, ~1 hour for the book) plus a concise **Introduction (~250 words)**.
   - **Elastic 12-Facet Container & Ordinary Human Worlds**: All book concepts—whether examining a single extraordinary thinker (*Flights and Perches*), twelve physical instruments (*Instruments of Precision*), or **ordinary subjects of everyday human interest** (*Twelve Countries*, *Twelve Plants*, *Twelve Animals*, *Twelve Foods*, *Twelve Laws*)—are shaped into 12 modular facets ("shorts, not the long video"). Avoid defaulting to "LLM-ish" esoteric topics or two-word abstract titles; take familiar things in the real world and reveal the hidden physical, biological, geographical, or institutional mechanics underneath them. Zero cross-chapter narrative continuity is required; any facet can be read standalone.

2. **Authorial Humility & Honest Machine Synthesis ("Do Not Be Fashioned According to the Age")**
   - Write in clear, direct, plainspoken prose. We are not trying to imitate commercial literary non-fiction or hide machine synthesis.
   - Never use purple prose, awe-inducing adjectives (*"profound"*, *"breathtaking"*, *"unprecedented"*, *"astonishing"*), or academic throat-clearing.
   - **Functional Bullet Lists**: Use structured bulleted or numbered lists freely whenever they bring clarity to a mechanism, protocol, or ledger.

3. **Mandatory Concrete Grounding & Verbatim Historical Quotes**
   - Every single chapter must be anchored in a concrete historical event, physical experiment, clinical case, or primary empirical record with named people, dates, places, and specific measurements.
   - **Verbatim Quotes**: Sprinkle 1–2 short, authentic, documented verbatim quotes from primary sources (words actually written or spoken by the historical figures) into chapters to humanize the record without inventing fictional dialogue. When a creator or dossier sets `require_quote_per_chapter: true` (or `--require-quotes`), every single chapter (1–12) must contain at least one documented verbatim quote.

4. **High-Density Compression (550–720 Words per Chapter; ~250-Word Introductions)**
   - **Introductions**: Keep introductions around **250 words** (strictly 140–300 words). Introduce the core topic, structural problem, and thesis directly—**never** summarize or list the upcoming chapters.
   - **Chapters**: Keep every chapter tightly compressed between **550 and 720 words** (~600–650 words ideal; hard validator bounds: `520–760` words). Do not let the model drift toward 850-word bloat, and do not truncate mechanisms into 300-word sketches. Punchiness comes from compression: unpack *how* the mechanism worked with zero wasted clauses.

5. **Earned Formalisms Only (Zero "Math Cosplay")**
   - Include a display equation (`$$...$$`) **only** when a genuine, established mathematical, physical, chemical, or statistical law governs the mechanism (e.g., Kuramoto coupled oscillators, Shannon channel capacity, Fick's law of diffusion, Kelly criterion, Bethe-Weizsäcker pairing energy, Manning's open-channel flow).
   - **Never** invent conceptual pseudo-equations or fake proportionalities (e.g., $\text{Fragility} \propto \text{Inertia} \times \text{Orthodoxy}^2$ or $\Delta S_{\text{exit}} \to \infty$).
   - When a chapter's mechanism is clinical, historical, or procedural rather than mathematical, present the exact experimental setup, mortality ledger, or structured bullet list instead of forcing a fake equation.
   - All genuine math must use valid LaTeX enclosed in `$$...$$` (block) or `$...$` (inline), with multi-character subscripts wrapped in curly braces (`_{...}`).

6. **Sentence Cadence: Smaller Average Length & Natural Variance (17–22 Words/Sentence)**
   - Prevent the model from drifting toward its default 33–36 word multi-clause encyclopedic mean or repetitive participial-phrase openers (*"Working alongside..., X did Y"*, *"Having discovered..., Z..."*).
   - Target a **crisp average sentence length of 17–22 words** (strictly $\le 24$ words/sentence) with natural variance: mix clean 10–14 word declarative sentences with 20–26 word mechanism explanations.
   - **Warning Against "Short Punchy Sentences"**: Do **not** write artificial LLM staccato fragments or dramatic one-liners (*"It failed."*, *"Then everything changed."*). Keep all short sentences factual and plainspoken.

7. **Antidote to Opening Fatigue: Rotate Three Opening Doors**
   - Do **not** open every chapter with the same sentence formula (*"At [Time] on [Date], [Age]-year-old [Name]..."*).
   - Across the 12 chapters of a book, deliberately rotate across three distinct opening doors:
     - **Door A — The Scene Open**: Drop into a specific moment, place, and physical action where an anomaly or crisis unfolded.
     - **Door B — The Constraint / Paradox Open**: Start directly with a hard physical limit, material bottleneck, or counterintuitive number, then introduce the person or system that confronted it.
     - **Door C — The Artifact / Evidence Open**: Start with a physical remnant, clinical ledger, or unexplained measurement (e.g., the open lower gunports of the salvaged *Vasa*, an eight-arcminute error in Mars tables, or a laboratory biopsy log).

8. **Clean Exits: No Moralizing Final Paragraphs**
   - Never end a chapter with a "high-school essay" summary paragraph (*"X showed that..."*, *"This demonstrated that..."*, *"His life proved that..."*).
   - End directly on the final factual outcome, physical resolution, or empirical consequence. Trust the reader to draw the conclusion.

9. **Epistemic Honesty & Header Formatting**
   - Distinguish hard historical telemetry from company lore or hagiography (*"According to company lore..."*).
   - **Strict Three-Line Headers (Zero Colons)**:
     ```markdown
     ### Chapter [N]
     # [Plain, Direct Title Without Colons]
     ## [Concrete Subtitle Naming the Subject, Place, or Mechanism Without Colons]
     ```

10. **Earned Schematic Diagrams (` ```svg `)**
    - **Restraint First (2–4 Per Book, Max 1 Per Chapter)**: Only include a diagram when a spatial topology, optical/mechanical apparatus, feedback loop, or timeline is genuinely clearer drawn than described in prose. Never include decorative or generic box-and-arrow filler.
    - **Theme-Aware Inline SVG**: Use fenced ` ```svg ` blocks with `viewBox="0 0 600 H"` ($140 \le H \le 250$) and `data-caption="FIG. X.1 — ..."`. Use CSS variables (`var(--text-color)`, `var(--text-muted)`, `var(--accent-color)`, `var(--border-color)`, `var(--card-bg)`) rather than hardcoded black/white colors so diagrams adapt seamlessly to Light, Dark, and Sepia themes.
    - **Complexity & Collision Cap**: Keep diagrams sparse ($\le 34$ SVG primitives), use `font-size` between `11` and `18`, ensure every `<rect>` box is at least `20px` wider than its enclosed `<text>`, and verify zero text/box collisions via `scripts/validate_book.py`.

---

## Tier 2: Topic-Specific Prompt Profiles

When generating or regenerating a book, select the profile that matches its domain and combine it with Tier 1:

### Profile A: Physical Systems, Infrastructure & Engineering Failures
*Applies to: `Latent Fragility`, `Architectures of the Grid`, `Elemental Asymmetries`, `Liminal Thresholds`, `Instruments of Precision`*
- **Narrative Vector**: Focus on the physical machine, infrastructure node, industrial reactor, or experimental apparatus—the exact materials, pressures, voltages, dimensions, and the human operators or engineers on site.
- **Forensic Engine**: Unpack the governing physical or chemical law, the boundary condition that was violated, the exact differential or thermodynamic equation, and the quantitative post-mortem telemetry.
- **Cross-Domain Bridge**: Connect the physical mechanism to an isomorphic process in biology, acoustics, or network theory only when both systems obey the same mathematical law.

### Profile B: Biological, Neural & Affective Control Loops
*Applies to: `The Autonomous Engine`, `Affective Topologies`, `Radical Subtraction`, `Sensory Worlds`*
- **Narrative Vector**: Every chapter **must** center on a specific landmark experiment, clinical patient, physiological ward, or historical practitioner (e.g., Wolfram Schultz's primate dopamine recordings, António Damasio's prefrontal patients, Colin Murray Parkes's bereavement studies, Ernest Starling's isolated heart preparation, John of the Cross in Toledo). Never write unanchored theory.
- **Forensic Engine**: Trace the exact anatomical pathway, receptor kinetics, autonomic shift, or computational neuroscience equation (e.g., temporal-difference reward prediction error, variational free energy, Hill cooperative binding, countercurrent multiplication).

### Profile C: Decision Theory, Economics & Enterprise Mechanics
*Applies to: `Non-Linear Engines`, `Architectures of Choice`, `Fictions of Order`, `Bonds of Enmity`*
- **Narrative Vector**: Every chapter **must** center on a concrete historical decision, financial blowup, legal/institutional invention, rivalry, or startup inflection point (e.g., Abraham Wald's WWII bomber armor analysis, Ed Thorp and Claude Shannon testing the Kelly criterion in Las Vegas, Andy Grove and Gordon Moore exiting DRAM at Intel in 1985, Ole Peters resolving the 1713 St. Petersburg paradox).
- **Forensic Engine**: Show the exact arithmetic—why ensemble averages diverge from time averages, how the payoff matrix or balance sheet worked, and where the absorbing barrier sat. Use real probability/financial equations where applicable; never invent symbolic jargon for simple business or legal concepts.

### Profile D: Intellectual Ruptures, Forensic Scholarship & Prismatic Minds
*Applies to: `Singular Minds`, `Tales of Audacity`, `Ghosts in the Parchment`, `Twelve Facets`*
- **Narrative Vector**: Establish the concrete institutional orthodoxy or intellectual puzzle, introduce the specific empirical anomaly or primary text that broke it, and walk through the exact sequence of trials, measurements, or arguments executed by the protagonist(s). For a single-thinker 12-facet volume (*Twelve Facets*), one facet may serve as a biographical profile while the remaining eleven unpack distinct experiments, concepts, and intellectual collisions.
- **Forensic Engine**:
  - When the breakthrough was mathematical, physical, or astronomical (Eratosthenes, Archimedes, Kepler, Grothendieck, Shannon, Noether), show the authentic geometric or mathematical derivation.
  - When the breakthrough was medical, biological, philological, or philosophical (James Lind's scurvy trial, Ignaz Semmelweis's Vienna maternity clinics, William James's stream of thought or pragmatist maxim, Lorenzo Valla's philological exposure of the Donation of Constantine), show the exact experimental protocol, schematic diagram, or primary textual comparison—**do not invent fake equations for non-mathematical discoveries**.

---

## Tier 3: The Two-Pass Creator Workflow & Steering Constraints

Every book created on the platform follows a bounded two-pass loop:
1. **Topic Input $\rightarrow$ 3–4 Forks on the Road**: Analyze the creator's raw topic and present 3–4 distinct 12-facet angles.
2. **First-Pass Generation (`v1`)**: Lock `dossiers/<slug>.json`, generate `v1`, and pass `scripts/validate_book.py`.
3. **Creator Steering Prompt $\rightarrow$ Regenerate `v2` & Done**: Accept the creator's post-`v1` steering prompt (e.g., *"I want at least one quote per chapter"*, *"Swap Chapter 8"*, *"Add a diagram to Chapter 2"*), encode the constraint into `dossiers/<slug>.json` (under `creator_constraints`) and `scripts/validate_book.py` (e.g., `--require-quotes`), regenerate `v2`, validate, publish, and call it done.

---

## Pre-Publication Quality Audit Checklist (`scripts/validate_book.py`)

Before any volume is compiled into `js/books-data.js`:
1. **Compression Check**: Is the Introduction `140–300` words (~250 target) with zero chapter summaries, and is every chapter `520–760` words (`550–720` target)?
2. **Sentence Cadence Check**: Is the average sentence length $\le 24.0$ words/sentence (`17–22` w/s target)?
3. **Concrete Anchor & Quote Check**: Does every chapter feature named people, dates, places, and concrete empirical events (plus $\ge 1$ verbatim quote per chapter when `--require-quotes` or `creator_constraints.require_quote_per_chapter` is active)?
4. **Opening Door Variety**: Are openings rotated across Scene, Constraint/Paradox, and Artifact/Evidence doors ($\le 4$ date-phrase opens)?
5. **Clean Exit Check**: Are there zero *"X showed that..."* / *"This demonstrated that..."* moralizing tail paragraphs?
6. **Equation & Diagram Audit**: Is every `$$...$$` block a real KaTeX-compilable formula, and does every ` ```svg ` diagram pass text-in-box containment and collision checks?
7. **Zero-Colon Header Check**: Do all book titles, subtitles, and 3-line chapter headers contain zero colons?

