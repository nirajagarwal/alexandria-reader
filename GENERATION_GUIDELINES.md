# Alexandria Press — Book Generation Guidelines & Prompt Architecture

This document defines the two-tier generation process for Alexandria Press (`alexandria.press`):
1. **Tier 1: The Universal Core Prompt** — Binding rules applied to every volume without exception.
2. **Tier 2: Topic-Specific Prompt Profiles** — Domain-adapted instructions that specify what constitutes the *Narrative Vector* and the *Forensic Deep-Dive* for a given subject.

---

## Tier 1: Universal Core Guidelines (Common to All Books)

Every book generation prompt must include and enforce these universal constraints:

1. **Authorial Humility & The Reporter's Register**
   - Write in clear, direct, plainspoken prose. Use everyday nouns and active verbs.
   - Never use purple prose, awe-inducing adjectives (*"profound"*, *"breathtaking"*, *"unprecedented"*, *"astonishing"*), or academic throat-clearing. Let the raw numbers, physical scales, and primary facts generate the wonder.

2. **Mandatory Concrete Grounding (Zero Abstract Essays)**
   - Every single chapter must be anchored in a concrete historical event, physical experiment, clinical case, or primary empirical record with named people, dates, places, and specific measurements.
   - Never write a chapter as a purely theoretical overview or textbook summary.

3. **Depth & Mechanism Completeness (650–900 Words per Chapter; ~250-Word Introductions)**
   - Volumes consist of **8 to 12 chapters**, plus a concise **Introduction (~200–275 words)**.
   - **Introductions**: Keep introductions around **250 words**. Introduce the core topic, structural problem, and thesis directly—**never** summarize or list the upcoming chapters.
   - **Chapters**: Every chapter must be **650 to 900 words** (5 to 8 rich paragraphs). Never compress chapters into 300-word summaries.
   - A story is not told until the reader can see *how* the mechanism actually worked step by step.

4. **Earned Formalisms Only (Zero "Math Cosplay")**
   - Include a display equation (`$$...$$`) **only** when a genuine, established mathematical, physical, chemical, or statistical law governs the mechanism (e.g., Kuramoto coupled oscillators, Shannon channel capacity, Fick's law of diffusion, Kelly criterion, Bethe-Weizsäcker pairing energy, Manning's open-channel flow).
   - **Never** invent conceptual pseudo-equations or fake proportionalities (e.g., $\text{Fragility} \propto \text{Inertia} \times \text{Orthodoxy}^2$ or $\Delta S_{\text{exit}} \to \infty$).
   - When a chapter's mechanism is clinical, historical, or procedural rather than mathematical, present the exact experimental setup, mortality ledger, or structured bullet list instead of forcing a fake equation.
   - All genuine math must use valid LaTeX enclosed in `$$...$$` (block) or `$...$` (inline), with multi-character subscripts wrapped in curly braces (`_{...}`).

5. **Antidote to Cadence Fatigue: Rotate Three Opening Doors**
   - Do **not** open every chapter with the same sentence formula (*"At [Time] on [Date], [Age]-year-old [Name]..."*).
   - Across the 8–12 chapters of a book, deliberately rotate across three distinct opening doors:
     - **Door A — The Scene Open**: Drop into a specific moment, place, and physical action where an anomaly or crisis unfolded.
     - **Door B — The Constraint / Paradox Open**: Start directly with a hard physical limit, material bottleneck, or counterintuitive number, then introduce the person or system that confronted it.
     - **Door C — The Artifact / Evidence Open**: Start with a physical remnant, clinical ledger, or unexplained measurement (e.g., the open lower gunports of the salvaged *Vasa*, an eight-arcminute error in Mars tables, or a laboratory biopsy log).

6. **Clean Exits: No Moralizing Final Paragraphs**
   - Never end a chapter with a "high-school essay" summary paragraph (*"X showed that..."*, *"This demonstrated that..."*, *"His life proved that..."*).
   - End directly on the final factual outcome, physical resolution, or empirical consequence. Trust the reader to draw the conclusion.

7. **Epistemic Honesty & Header Formatting**
   - Distinguish hard historical telemetry from company lore or hagiography (*"According to company lore..."*).
   - **Strict Three-Line Headers (Zero Colons)**:
     ```markdown
     ### Chapter [N]
     # [Plain, Direct Title Without Colons]
     ## [Concrete Subtitle Naming the Subject, Place, or Mechanism Without Colons]
     ```

---

## Tier 2: Topic-Specific Prompt Profiles

When generating or regenerating a book, select the profile that matches its domain and combine it with Tier 1:

### Profile A: Physical Systems, Infrastructure & Engineering Failures
*Applies to: `Latent Fragility`, `Architectures of the Grid`, `Elemental Asymmetries`, `Liminal Thresholds`*
- **Narrative Vector**: Focus on the physical machine, infrastructure node, industrial reactor, or experimental apparatus—the exact materials, pressures, voltages, dimensions, and the human operators or engineers on site.
- **Forensic Engine**: Unpack the governing physical or chemical law, the boundary condition that was violated, the exact differential or thermodynamic equation, and the quantitative post-mortem telemetry.
- **Cross-Domain Bridge**: Connect the physical mechanism to an isomorphic process in biology, acoustics, or network theory only when both systems obey the same mathematical law.

### Profile B: Biological, Neural & Affective Control Loops
*Applies to: `The Autonomous Engine`, `Affective Topologies`, `Radical Subtraction`*
- **Narrative Vector**: Every chapter **must** center on a specific landmark experiment, clinical patient, physiological ward, or historical practitioner (e.g., Wolfram Schultz's primate dopamine recordings, António Damasio's prefrontal patients, Colin Murray Parkes's bereavement studies, Ernest Starling's isolated heart preparation, John of the Cross in Toledo). Never write unanchored theory.
- **Forensic Engine**: Trace the exact anatomical pathway, receptor kinetics, autonomic shift, or computational neuroscience equation (e.g., temporal-difference reward prediction error, variational free energy, Hill cooperative binding, countercurrent multiplication).

### Profile C: Decision Theory, Economics & Enterprise Mechanics
*Applies to: `Non-Linear Engines`, `Architectures of Choice`*
- **Narrative Vector**: Every chapter **must** center on a concrete historical decision, financial blowup, military survival problem, or startup inflection point (e.g., Abraham Wald's WWII bomber armor analysis, Ed Thorp and Claude Shannon testing the Kelly criterion in Las Vegas, Andy Grove and Gordon Moore exiting DRAM at Intel in 1985, Ole Peters resolving the 1713 St. Petersburg paradox).
- **Forensic Engine**: Show the exact arithmetic—why ensemble averages diverge from time averages, how the payoff matrix or balance sheet worked, and where the absorbing barrier sat. Use real probability/financial equations where applicable; never invent symbolic jargon for simple business concepts.

### Profile D: Intellectual Ruptures & Consensus Breaking
*Applies to: `Singular Minds`, `Tales of Audacity`*
- **Narrative Vector**: Establish the concrete institutional orthodoxy and why it held power, introduce the specific empirical anomaly or intractable problem that defied it, and walk through the exact sequence of trials, measurements, or proofs executed by the protagonist.
- **Forensic Engine**:
  - When the breakthrough was mathematical, physical, or astronomical (Eratosthenes, Archimedes, Kepler, Grothendieck, Shannon, Noether), show the authentic geometric or mathematical derivation.
  - When the breakthrough was medical, biological, or geological (James Lind's scurvy trial, Ignaz Semmelweis's Vienna maternity clinics, Barry Marshall's *H. pylori* self-experimentation, Barbara McClintock's maize chromosomes, Katalin Karikó's modified mRNA), show the exact experimental protocol, clinical comparison groups, or biochemical mechanism—**do not invent fake equations for non-mathematical discoveries**.

---

## Pre-Publication Quality Audit Checklist

Before any volume is compiled into `js/books-data.js`:
1. **Word Count Check**: Does every chapter have between **600 and 950 words**?
2. **Concrete Anchor Check**: Does every chapter feature named people, dates, places, and concrete empirical events?
3. **Opening Door Variety**: Are the openings varied across Scene, Constraint/Paradox, and Artifact/Evidence doors?
4. **Clean Exit Check**: Are there zero *"X showed that..."* / *"This demonstrated that..."* moralizing tail paragraphs?
5. **Equation Audit**: Is every `$$...$$` block a real mathematical, physical, chemical, or statistical formula with valid KaTeX syntax?
6. **Zero-Colon Header Check**: Do all book titles, subtitles, and 3-line chapter headers contain zero colons?
