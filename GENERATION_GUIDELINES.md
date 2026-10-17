# Alexandria Press — Book Generation Guidelines

> [!IMPORTANT]
> **LOCKED SPECIFICATION (`prompt-lock.json`)**: These generation guidelines, [`alexandria_manifesto.md`](alexandria_manifesto.md), [`scripts/create_book_pipeline.py`](scripts/create_book_pipeline.py), and [`.agent/skills/generate-alexandria-book/SKILL.md`](.agent/skills/generate-alexandria-book/SKILL.md) are **LOCKED**. Whenever a future book generation or rewrite is requested, you MUST ask the user whether to proceed with the locked prompt and guidelines or whether they want to make changes to the prompt before modifying these files or overriding prompt instructions.

These guidelines translate the **Alexandria Manifesto** ([`alexandria_manifesto.md`](alexandria_manifesto.md)) into the **Two-Tier Generation Architecture**:
- **Tier 1**: Seven broad laws common to all books.
- **Tier 2**: Topic-specific prompt profiles that adapt the *Narrative Vector* and *Forensic Engine* to the specific subject without forcing a one-size-fits-all template.

---

## The First Principle: Authorial Humility & The Contrapuntal Cadence

> **"We are not writing to impress. The material we have itself is impressive. We need to get out of the way and let the material speak for itself."**

Every Alexandria chapter is built on **The Contrapuntal Cadence**—the interplay between two modes:
1. **The Narrative Vector**: The human stakes, historical anomaly, entrenched orthodoxy, or physical crisis where a problem surfaced.
2. **The Forensic Deep-Dive**: The step-by-step physical, mathematical, biological, philosophical, or institutional mechanism that explains *why* and *how* it works.

---

## Tier 1: Seven Universal Laws (Common to All Books)

1. **Direct, Clear Prose (Zero Pretension, Zero Condescension)**
   - Say things simply and directly. Complexity belongs in the underlying ideas, mechanisms, and cross-domain connections—never in decorative vocabulary or academic throat-clearing.
   - Do not talk down to the reader with breezy pop-science filler, and do not use hyperbolic adjectives (*"breathtaking"*, *"awe-inspiring"*, *"mind-boggling"*, *"staggering"*, *"paradigm-shifting"*, *"unprecedented"*, *"astonishing"*). Let the facts, scale, and logic carry the weight.

2. **Mandatory Concrete Grounding**
   - Never write an unanchored abstract overview. Anchor every chapter in real experiments, historical events, clinical cases, or primary texts with named individuals, years, places, and concrete evidence.
   - Use the historical or experimental case to expose the underlying mechanism or conceptual fault line—never as a superficial anecdote told for its own sake.

3. **Mechanism Completeness (550–800 Words per Chapter; ~250-Word Topic-Only Introductions)**
   - **Introductions (~200–270 Words)**: Frame the central intellectual tension or physical constraint of the book's topic directly. Never summarize, list, or preview the individual chapters.
   - **Chapters (550–800 Words)**: Unpack *how* the mechanism or argument works step by step across 5–7 paragraphs so a reader is never left asking *"but how?"*

4. **Earned Formalisms Only (Zero Math Cosplay)**
   - Choose each chapter's formalism organically based on the subject:
     - **Genuine Equations (`"equation"`)**: Include a `$$...$$` display equation *only* when an authentic mathematical, physical, chemical, or statistical law governs the phenomenon (e.g., non-ergodic time-average growth, Kelly criterion, Shannon capacity, Kuramoto synchronization). Never invent conceptual pseudo-equations ($\text{Fragility} \propto \text{Inertia}^2$).
     - **Protocols & Ledgers (`"ledger_or_list"`)**: When a mechanism is experimental, clinical, or comparative (such as James Lind's six scurvy treatment pairs), use a crisp 3–4 item structured list where it brings immediate clarity.
     - **Schematic Diagrams (`"diagram"`)**: Include a theme-aware SVG schematic (`FIG. N.1`) only where a 3-stage structural flow genuinely clarifies the system.
     - **Continuous Prose (`"prose"`)**: When the chapter's engine is philosophical, historical, contemplative, or conceptual, let continuous prose carry the entire argument.

5. **Three Opening Doors (Preventing Cadence Fatigue)**
   - Never start every chapter with the same mechanical formula (*"In [Year], in [City], [Name]..."*). Rotate naturally across three entry doors:
     - **Door A — The Scene / Collision Open**: Drop into a decisive historical moment, laboratory apparatus, or clinical encounter where an anomaly surfaced.
     - **Door B — The Constraint / Paradox Open**: Start directly with a hard physical bottleneck, mathematical paradox, or entrenched orthodoxy, then introduce the thinker or system that collided with it.
     - **Door C — The Artifact / Measurement Open**: Start with a physical remnant, primary text, clinical ledger, or unexplained discrepancy (such as an eight-arcminute error in Mars tables or the open gunports of a salvaged hull).

6. **Clean Exits (Withhold Concluding Sermons)**
   - Never end a chapter with a moralizing summary sentence (*"X showed that..."*, *"This demonstrated that..."*, *"Ultimately..."*, *"serves as a testament"*).
   - When the final empirical fact, mathematical resolution, or philosophical consequence lands, stop and let the reader close the circuit.

7. **Epistemic Honesty, Paraphrase Hygiene & Strict 3-Line Headers**
   - **Paraphrase Only**: Paraphrase primary arguments and historical statements in accurate indirect speech (no 5+ word direct quotes inside `"..."`).
   - **No Fabricated Micro-Details**: Do not invent novelistic weekdays, weather cold-opens, or hyphenated character ages (`"forty-three-year-old"`).
   - **Three-Line Header Standard (Zero Colons)**:
     ```markdown
     ### Chapter [N]
     # [Title Without Colons]
     ## [Subtitle Naming the Subject or Mechanism Without Colons]
     ```

---

## Tier 2: Topic-Specific Prompt Profiles

Rather than forcing every subject into a single template, each volume pairs **Tier 1** with a **Topic-Specific Prompt Profile** tailored to how that domain proves its truths:

### Profile A: Physical Systems, Infrastructure & Engineering Failures
*Examples: `Latent Fragility`, `Architectures of the Grid`, `Elemental Asymmetries`, `Liminal Thresholds`, `Planetary Triggers`, `Materials`, `Entropy`*
- **Narrative Vector**: Focus on the physical machine, infrastructure node, geological fault, or experimental apparatus—the exact materials, pressures, voltages, dimensions, and the engineers or physicists on site.
- **Forensic Engine**: Unpack the governing physical or chemical law, the boundary condition that was violated, the thermodynamic or differential equation, and the quantitative post-mortem telemetry.

### Profile B: Biological, Neural, Cognitive & Contemplative Systems
*Examples: `The Autonomous Engine`, `Radical Subtraction`, `Sensory Worlds`, `Consciousness`, `Attention`, `Self-Transcendence`, `Vaccines`*
- **Narrative Vector**: Center on the landmark clinical patient, physiological experiment, evolutionary adaptation, contemplative tradition, or philosophical thought experiment that exposed a hidden property of life or mind.
- **Forensic Engine**: Trace the anatomical circuit, cellular/immunological mechanism, receptor kinetics, computational neuroscience model, or phenomenological argument step by step.

### Profile C: Decision Theory, Economics & Institutional Mechanics
*Examples: `Non-Linear Engines`, `Architectures of Choice`, `Fictions of Order`, `Bonds of Enmity`, `Paper Panics`*
- **Narrative Vector**: Center on a high-stakes historical wager, financial blowup, legal invention, military survival problem, or corporate inflection point.
- **Forensic Engine**: Show the exact structural logic—why ensemble averages diverge from time averages, how the payoff convexity or balance-sheet plumbing worked, where the absorbing barrier sat, or how the institutional rule altered incentives.

### Profile D: Intellectual Ruptures, Forensics & Biography
*Examples: `Singular Minds`, `Tales of Audacity`, `Instruments of Precision`, `Ghosts in the Parchment`, `William James`, `Richard Feynman`, `Claude Shannon`, `Alan Turing`*
- **Narrative Vector**: Establish the entrenched consensus or intractable problem, introduce the specific anomaly or conceptual leap that broke it, and walk through the sequence of trials, instruments, or proofs executed by the protagonist.
- **Forensic Engine**: Use authentic geometric or mathematical derivations where the discovery was mathematical or physical, and use exact experimental protocols, philological forensics, or primary evidence tables where the breakthrough was biological, medical, or historical.
