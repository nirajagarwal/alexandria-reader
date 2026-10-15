# Equation Subscripts and Presentation Status Report
*Alexandria Press · Forensic Audit and Resolution*

---

### 1. Status of the Previous Request (Home Page & Presentation)
The previous analysis and layout fixes were completed and committed locally (`commit 3646c63` and `commit 207c016`):
- **1-Line Clean Brand Title**: Simplified the home header brand to `ALEXANDRIA.PRESS` on one horizontal line.
- **Minimalist Action Icons**: Replaced the text "Theme" and "?" with 16px vector icons (crescent moon and info circle).
- **Pure 2:3 Cover Grid**: Excised all `.book-meta` text panels below the covers on the home catalog.
- **Aspect-Ratio Lock**: Fixed the grid container with `aspect-ratio: 2 / 3` and `align-items: start`, eliminating the vertical squishing.
- **Manifesto Scope**: Removed *Alexandria Manifesto* from the published book catalog.

---

### 2. Root Cause of Subscript Formatting Failure
In standard LaTeX and KaTeX syntax, the underscore operator `_` binds strictly to the immediate next single token unless enclosed within curly braces `{...}`:
- **What was written**: `$$q_conv = h_conv · A · (T_surface - T_ambient)$$`
- **How KaTeX parsed it**:
  - `q_c` became subscript $q_c$, while `onv` was treated as normal inline text $\implies$ $q_c onv$.
  - `T_s` became subscript $T_s$, while `urface` was treated as normal text $\implies$ $T_s urface$.
  - `T_a` became subscript $T_a$, while `mbient` was treated as normal text $\implies$ $T_a mbient$.

---

### 3. Resolution Applied
1. **Source Markdown Audit & Batch Bracing**:
   - Scanned all 11 volumes across the library and wrapped all multi-character subscripts in curly braces:
     `$$q_{conv} = h_{conv} \cdot A \cdot (T_{surface} - T_{ambient})$$`
   - Updated variables across physics, thermodynamics, and physiology (e.g., `v_{wall}`, `c_{sound}`, `T_{hot}`, `T_{cold}`, `\Delta P_{hydraulic}`, `\Delta V_{EDV}`).
2. **Defensive Preprocessor in Reader Engine (`index.html`)**:
   - Added automatic regex normalizers to both block math (`$$...$$`) and inline math (`$...$`) inside `index.html`.
   - Any unbraced multi-character subscript matching `_([a-zA-Z]{2,})` is automatically enclosed into `_{$1}` prior to KaTeX execution, preventing unbraced notation from ever splitting characters again.
3. **Repository Sync**:
   - Cleaned stray generator script fragments from `autonomous_engine.md` and `elemental_asymmetries.md`.
   - Synchronized all updated markdowns into `EMBEDDED_BOOKS`.
