# Alexandria Press: Design Brief

## What This Is

Alexandria Press publishes AI-generated books. Not cheap knockoffs of human writing, but a new genre: collections that only AI can write. Complete sets — every element, every country, every myth — treated with equal depth and care. The machine doesn't tire at entry 74. It brings the same attention to ytterbium as to gold.

The tagline: **Books only AI can write.**

## The Mission

Earn respect through substance, not style. The AI-generated nature is stated plainly, not hidden, not apologized for. The work speaks for itself. If a reader finishes an entry and sits quietly for a moment, struck by what they learned, we've succeeded.

## The Voice (Content)

The content was written as a chronicler would write it:

- The subject is sovereign. The writer is invisible.
- No self in the voice. No commentary. No rhetoric.
- Facts arranged with care speak for themselves.
- No "isn't it remarkable" — the material is remarkable; we don't say so.
- Restrained. Clear. Confident. No flourishes.

The design must match this voice.

## The Aesthetic (Design)

**What it is:**
- A quiet, well-lit room full of books
- Invisible design — if you notice the design, something is wrong
- Restraint that conveys reverence
- Confidence without flash
- Old-school gravitas, modern execution

**What it is not:**
- A tech product
- A startup landing page
- Dark mode with neon accents
- Anything that says "AI" visually (no gradients, no glows, no circuit patterns)
- Anything clever or whimsical

**Typography:**
- Serif for content (classical, readable, dignified)
- Clean sans for UI elements (invisible, functional)
- No display fonts. No quirky choices. No personality in the letterforms.

**Color:**
- Light mode: Parchment. Warm cream, off-white, soft black. Think old paper under good light.
- Dark mode: Vault. Near-black, dark grey, warm white. Think a library at night.
- No brand colors. No accents. Monochromatic with warmth.
- The content provides the color (cover images, nothing else).

**Interaction:**
- Subtle. Transitions exist to smooth, not to impress.
- No hover effects that call attention to themselves.
- No animations that delay the reader.
- Keyboard navigation works (arrows for prev/next).

**Layout:**
- Generous whitespace. Air on the page.
- Content centered, never wider than comfortable reading width (~680px for text).
- Card grids are tight but not cramped.
- Mobile-first, but this is a reading experience — tablets and desktop matter.

## The Structure

Three levels:

1. **Library** — All books as covers on a shelf
2. **Book** — Cover → Card grid of entries → Individual pages (Introduction, Appendix, Colophon)
3. **Entry** — The content itself, with prev/next navigation

The card grid is the universal navigation pattern. For Periodic Tales, cards show symbol/name/number. For other collections, cards show whatever identifies that entry. Same component, different content.

## What Success Looks Like

A reader arrives at alexandria.press. They see a shelf of books. They click one. They see a cover, then a grid of entries. They start reading. An hour later, they've read twelve entries about elements they never thought about. They learned something. They felt something. They never once thought about the fact that it was AI-generated.

The design disappeared. The content remained.

## Technical Notes

- Vanilla HTML/CSS/JS. No framework needed.
- Markdown rendered client-side (marked.js or similar).
- API serves JSON; frontend renders.
- Static hosting works (Vercel, Netlify, etc.).
- Respect `prefers-color-scheme` for dark/light.

## Files Included

```
alexandria/
├── generator/     # Python scripts to generate books
├── db/            # Turso schema and loader
├── api/           # FastAPI backend
└── frontend/      # HTML/CSS/JS viewer (your canvas)
```

The frontend provided is functional but minimal. It establishes the structure and core aesthetic. Your job: refine it until it feels inevitable. Every padding value, every transition duration, every shade of grey — considered and correct.

## Final Word

This is not a project that needs "personality" or "delight" or "brand expression." It needs dignity. It needs to get out of the way. The books are the product. The reader's experience of the content is everything.

Make it beautiful by making it invisible.
