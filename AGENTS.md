# Alexandria Press — Locked Prompts & Generation Guidelines Rule

## 1. Locked Prompt & Guideline Files (`prompt-lock.json`)
The following four files define the canonical **Alexandria Manifesto**, **Two-Tier Generation Architecture (`Tier 1: Universal Laws` + `Tier 2: Topic-Specific Profiles A–D`)**, and **Form-Specific Prompt Branching (`facet` / `biography` / `landscape` / `listicle`)**:
- `/Users/niraj/book-writer/alexandria_manifesto.md`
- `/Users/niraj/book-writer/GENERATION_GUIDELINES.md`
- `/Users/niraj/book-writer/scripts/create_book_pipeline.py`
- `/Users/niraj/book-writer/.agent/skills/generate-alexandria-book/SKILL.md`

Their SHA-256 checksums are locked in `/Users/niraj/book-writer/prompt-lock.json` and verified automatically by `python3 scripts/create_book_pipeline.py --verify-lock` and `python3 tests/test_reader.py`.

## 2. Mandatory Rule for Future Book Generation & Rewrite Requests
Whenever the user asks to generate a new book, pick a book from the backlog, or rewrite an existing book:
1. **Do NOT silently modify the prompt or guidelines**: Never edit `alexandria_manifesto.md`, `GENERATION_GUIDELINES.md`, `scripts/create_book_pipeline.py`, or `.agent/skills/generate-alexandria-book/SKILL.md`—and never pass ad-hoc prompt overrides to subagents or batch jobs that deviate from the locked specification—without explicit user permission.
2. **Always ask about prompt changes before generating**: Before launching book generation, present the proposed book configuration (`Title`, `Subtitle`, `Mode: facet | biography | landscape | listicle`, `Profile: A | B | C | D`, and `12-Chapter Arc`) and **explicitly ask the user**:
   - Whether to generate using the **locked prompt and guidelines as-is**, OR
   - Whether they want to make any **changes to the prompt or guidelines** for this request.
3. **Updating the Lock (Only After Explicit User Approval)**: If and only if the user explicitly approves changes to the prompt or guidelines, apply the requested edits and run `python3 scripts/create_book_pipeline.py --update-lock` to update `/Users/niraj/book-writer/prompt-lock.json`.
