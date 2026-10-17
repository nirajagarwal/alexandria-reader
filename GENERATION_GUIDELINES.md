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

3. **Mandatory Concrete Grounding & Zero Direct Quotations (Paraphrase Only)**
   - Every single chapter must be anchored in a concrete historical event, physical experiment, clinical case, or primary empirical record with named people, years, institutions, and specific measurements.
   - **No Direct Quotations (`"..."`)**: Never place multi-word direct speech quotations attributed to historical actors or scientists in prose. Always paraphrase findings, arguments, and statements in crisp indirect speech so quote fabrication is impossible. Let empirical findings drive the chapter thesis rather than bending a study to fit a pre-written moral takeaway.

4. **High-Density Compression (550–720 Words per Chapter; ~250-Word Introductions)**
   - **Introductions**: Keep introductions around **250 words** (strictly 140–300 words). Introduce the core topic, structural problem, and thesis directly—**never** summarize or list the upcoming chapters.
   - **Chapters**: Keep every chapter tightly compressed between **550 and 720 words** (~600–650 words ideal; hard validator bounds: `520–760` words). Do not let the model drift toward 850-word bloat, and do not truncate mechanisms into 300-word sketches. Punchiness comes from compression: unpack *how* the mechanism worked with zero wasted clauses.

5. **Earned Formalisms & Isomorphic Parallels Only (Zero "Math Cosplay" or Decorative Metaphors)**
   - Include a display equation (`$$...$$`) **only** when a genuine, established mathematical, physical, chemical, or statistical law governs the mechanism (e.g., Kuramoto coupled oscillators, Shannon channel capacity, Fick's law of diffusion, Kelly criterion, Bethe-Weizsäcker pairing energy, Manning's open-channel flow).
   - **Never** invent conceptual pseudo-equations or fake proportionalities (e.g., $\text{Fragility} \propto \text{Inertia} \times \text{Orthodoxy}^2$ or $\Delta S_{\text{exit}} \to \infty$).
   - Include a cross-domain parallel only when the exact same mathematical equation governs both systems—never add decorative biological or physics metaphors.
   - When a chapter's mechanism is clinical, historical, or procedural rather than mathematical, present the exact experimental setup, mortality ledger, or structured bullet list instead of forcing a fake equation.
   - All genuine math must use valid LaTeX enclosed in `$$...$$` (block) or `$...$` (inline), with multi-character subscripts wrapped in curly braces (`_{...}`).

6. **Sentence Cadence: Smaller Average Length & Natural Variance (17–22 Words/Sentence)**
   - Prevent the model from drifting toward its default 33–36 word multi-clause encyclopedic mean or repetitive participial-phrase openers (*"Working alongside..., X did Y"*, *"Having discovered..., Z..."*).
   - Target a **crisp average sentence length of 17–22 words** (strictly $\le 24$ words/sentence) with natural variance: mix clean 10–14 word declarative sentences with 20–26 word mechanism explanations.
   - **Warning Against "Short Punchy Sentences"**: Do **not** write artificial LLM staccato fragments or dramatic one-liners (*"It failed."*, *"Then everything changed."*). Keep all short sentences factual and plainspoken.

7. **Anti-Novelistic Openings: Ban Unverified Micro-Details & Rotate Three Entry Doors**
   - **Forbid Novelistic Micro-Details**: Never invent or include weekdays (*"On a Sunday afternoon"*), clock times (unless part of an official telemetry log), weather adjectives (*"On a cold, rainy morning"*), or researcher ages (*"Forty-three-year-old..."*).
   - Across the 12 chapters of a book, deliberately rotate across three substantive opening doors:
     - **Door A — The Experiment / Case Open**: Start directly with the laboratory setup, clinical ward, or engineering system, anchored by year and institution.
     - **Door B — The Constraint / Paradox Open**: Start directly with a hard physical limit, material bottleneck, or counterintuitive number, then introduce the person or system that confronted it.
     - **Door C — The Artifact / Evidence Open**: Start with a physical remnant, clinical ledger, or unexplained measurement (e.g., an eight-arcminute error in Mars tables or a laboratory biopsy log).

8. **Clean Exits: No Moralizing Final Paragraphs**
   - Never end a chapter with a "high-school essay" summary paragraph (*"X showed that..."*, *"This demonstrated that..."*, *"His life proved that..."*).
   - End directly on the final factual outcome, physical resolution, or empirical consequence. Trust the reader to draw the conclusion.

9. **Epistemic Honesty, Anti-Conflation & Header Formatting**
   - **Preserve Source Hedges & Unconfirmed Mechanisms**: State verified telemetry and primary records plainly. Never upgrade an unconfirmed forensic hypothesis (such as a suspected surveying projection error when physical evidence was destroyed) into a proven judicial or federal conclusion, and never strip statistical or historical qualifiers into sweeping absolutes (*"never"*, *"every single"*, *"worse than random"*).
   - **Anti-Conflation & Internal Arithmetic Consistency**: Never conflate separate defects across multi-incident failures (such as the Tyler cursor-editing race condition versus the Yakima 8-bit counter overflow in Therac-25) or attribute a later laboratory measurement to an earlier field pioneer. Ensure all numerical ratios and unit comparisons across a chapter and book are dimensionally and arithmetically consistent.
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

11. **Mandatory Independent Fact-Check & Provenance Audit Pass**
    - Because error density in machine synthesis tracks narrative pressure, every volume must undergo an **independent fact-check pass** (either after each chapter or immediately after full-book generation) executed by a separate verification subagent before PDF compilation.
    - The independent Fact-Checker Agent extracts and audits six specific failure modes across all 12 chapters:
      1. **Direct Quote Purge**: Verify zero multi-word direct quotations (`"..."` $\ge 5$ words) exist anywhere in the text.
      2. **Empirical Direction & Sign Audit**: Verify against primary literature (`pubmed-database`, `literature-search-openalex`, `wiki-grounding`, web search) that every cited study or experiment reports the *actual direction and metric* found by the authors, never inverted to fit a moral trope.
      3. **Chronology & Attribution Audit**: Verify exact years, dates, ship/institution names, and chronological sequences (e.g., ensuring a gene or organization was not named anachronistically before its discovery or founding).
      4. **Multi-Incident & Pioneers Conflation Audit**: Verify that separate failures in the same system or later laboratory measurements versus earlier field experiments are cleanly distinguished.
      5. **Epistemic Hedge Audit**: Verify that unconfirmed mechanisms, out-of-court settlements, and statistical trends retain their source qualifiers rather than being stated as absolute or judicially proven facts.
      6. **Isomorphic Parallel & Internal Math Audit**: Verify that any cross-domain analogy obeys the *exact same mathematical equation* (deleting decorative metaphors) and that all ratios and numbers within and across chapters are arithmetically consistent.

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
*Applies to: `Singular Minds`, `Tales of Audacity`, `Ghosts in the Parchment`, `Flights and Perches`, `The Curious Physicist`*
- **Narrative Vector**: Establish the concrete institutional orthodoxy or intellectual puzzle, introduce the specific empirical anomaly or primary text that broke it, and walk through the exact sequence of trials, measurements, or arguments executed by the protagonist(s). For a single-thinker 12-facet volume (*Twelve Facets*), one facet may serve as a biographical profile while the remaining eleven unpack distinct experiments, concepts, and intellectual collisions.
- **Forensic Engine**:
  - When the breakthrough was mathematical, physical, or astronomical (Eratosthenes, Archimedes, Kepler, Grothendieck, Shannon, Noether), show the authentic geometric or mathematical derivation.
  - When the breakthrough was medical, biological, philological, or philosophical (James Lind's scurvy trial, Ignaz Semmelweis's Vienna maternity clinics, William James's stream of thought or pragmatist maxim, Lorenzo Valla's philological exposure of the Donation of Constantine), show the exact experimental protocol, schematic diagram, or primary textual comparison—**do not invent fake equations for non-mathematical discoveries**.

### Profile E: The Prospected Spaced-Dot Listicle (`mode: "listicle"`)
*Applies when narrative is not the right fit and the reader wants 12 dynamite, perpendicular highlights per chapter (e.g., `The Human Body`, where Chapter 1 is 12 dynamite facts about the Heart).*
- **Prospecting Engine (`topic-prospector` + Domain Knowledge)**:
  - Before writing each chapter, run a **Topic Prospector** pass on that chapter's subject to mine perpendicular, cross-disciplinary seeds—insights that violate expectations, reveal hidden mechanics, dissolve categories, and lean into concrete numbers, measurements, or named studies.
  - Combine the sharpest prospected seeds with domain essentials to select **12 distinct, high-voltage observations** for the chapter.
- **Typographic Structure (12 Paragraphs Separated by `❦`)**:
  - Do **not** use numbered lists (`1.`, `2.`) or bullet points for the 12 items.
  - Write **12 standalone paragraphs** per chapter (~45–55 words per paragraph; ~550–700 words total per chapter).
  - Separate each of the 12 paragraphs with a standalone centered **spaced middle dots (`· · ·`)** on its own line (`11` fleurons per chapter between the `12` paragraphs).
  - Every paragraph must open directly with the substance (never throat-clearing) and pack a concrete number, physical ratio, or surprising mechanism.

### Profile F: The Contextual Landscape (`mode: "landscape"`, from `knowra.com`)
*Applies when the goal is to learn a central topic in context with a view to its surrounding conceptual landscape.*
- **Neighborhood Mapping (Knowra Lenses & Relational Moves)**:
  - Given a central topic $X$, **Chapter 1** examines the **Anchor Concept ($X$)** itself (`what` it is, how it works at the core, and what makes it distinctive).
  - **Chapters 2–12** explore **eleven specific adjacent concepts** (never vague categories!) chosen across Knowra's lenses (`Building blocks` — what you need to understand first; `Mechanism` — finer sub-parts via `zoom-in`; `Origins` — where it came from; `People` — who shaped it; `Contrasts` — rival theories, opposites, or things it is confused with; `Neighbors` — sibling ideas at the same level via `go`; `Consequences` & `Cases` — what it changed and canonical instances; `Open questions` — unresolved boundaries).
- **Map-Primed Chapter Synthesis**:
  - In `dossiers/<slug>.json`, each chapter specifies its `lens`, `verb` (`anchor`, `zoom-in`, `zoom-out`, `go`, `contrast`), `what` (context-free definition), `why_here` (its exact connection to the central topic $X$), and 4–5 `background_nodes` (linked sub-concepts that prime the writing with concrete mechanisms, numbers, and names).
  - Each chapter (550–720 words) explains both the adjacent concept on its own terms and how it connects to, constrains, or contrasts with the book's central subject—building a 360-degree mental map of the landscape.

### Profile G: Additional Structural Forms in the Nine-Form Stockpile
Beyond `"facet"`, `"listicle"`, and `"landscape"`, the Alexandria stockpile includes six specialized structural forms (`mode` in `dossiers/<slug>.json`):
- **`"contrast"` (The Contrast / Twins Form)**:
  - *Structure*: Each chapter puts two confused, look-alike, or rival concepts side by side (either 12 pairs across a field, or 12 comparative axes between two rival systems).
  - *Chapter Construction*: (1) The shared problem or surface resemblance, (2) the exact physical, structural, or institutional fork where they diverge, and (3) a decisive real-world test or failure mode where confusing them is fatal.
- **`"anatomy"` (The Anatomy / Under-the-Hood Form)**:
  - *Structure*: Opens up **one complex everyday black box** (*Anatomy of a Jetliner*, *Anatomy of a City*, *Anatomy of a Hospital*, *Anatomy of a Smartphone*, *Anatomy of a Central Bank*) into 12 functional subsystems.
  - *Chapter Construction*: Zooms into one physical or institutional subsystem, the hard constraint it solves, its historical invention, and how it couples to the rest of the whole.
- **`"field-guide"` (The Field Guide / "How to Read..." Form)**:
  - *Structure*: Decodes visible clues hiding in plain sight in the everyday world (*How to Read a City Street*, *How to Read a Building*, *How to Read the Sky*, *How to Read a Financial Statement*).
  - *Chapter Construction*: Starts with an observable physical sign or artifact you pass in daily life, shows how to spot its diagnostic features, and unpacks the hidden engineering, geology, law, or economics that put it there.
- **`"scale"` (The Scale Ladder / Powers of Ten Form)**:
  - *Structure*: Climbs 12 orders of magnitude in size, time, energy, or population (*Being the Right Size*, *Twelve Scales of Time*, *From Village to Megacity*).
  - *Chapter Construction*: Each chapter represents one rung on the scale ladder, pinpointing the exact physical or organizational phase transition where the old governing mechanism breaks and a new law takes over.
- **`"inversion"` (The Counter-Intuition / Myth-Buster Form)**:
  - *Structure*: Examines 12 entrenched misconceptions, optical/cognitive illusions, or folk-science traps in a domain.
  - *Chapter Construction*: (1) States the universal everyday belief and why human intuition falls for it, (2) introduces the historical experiment or measurement that broke the illusion, and (3) unpacks the actual mechanism.
- **`"chain"` (The End-to-End Chain Form)**:
  - *Structure*: Follows one everyday object, signal, or resource across 12 sequential transformations (*From Sand to Thought*, *What Happens When You Click a Link*, *From Coffee Cherry to Morning Cup*).
  - *Chapter Construction*: Each chapter is one self-contained link in a 12-stage physical or informational pipeline—receiving the output of Chapter $N-1$, executing its transformation and solving its bottleneck, and handing off to Chapter $N+1$.

---

## Tier 3: The Two-Pass Creator Workflow & Composite Option Selection

Every book created on the platform follows a bounded two-pass loop where **topic exploration always evaluates the 9-Form Stockpile**:
1. **Topic Input $\rightarrow$ 3–4 Composite Options (`Topic Angle × Structural Form × 12-Chapter Construction`)**:
   - When the creator proposes a topic, do **not** offer four subtopic slices of the same default form.
   - Evaluate the topic across the **Nine-Form Stockpile** (`"facet"`, `"listicle"`, `"landscape"`, `"contrast"`, `"anatomy"`, `"field-guide"`, `"scale"`, `"inversion"`, `"chain"`) and present **3–4 distinct composite options**.
   - For each option, show:
     1. **Proposed Title & Subtitle**
     2. **Selected Form (`mode`) & Why It Fits This Angle**
     3. **The 12-Chapter Construction** (how the 12 chapters are sliced and how each individual chapter is built).
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

