"""
Pass 2: Copy Editing
Polishes entries for grammar, flow, consistency, and clarity.
Removes hedging, tightens prose, fixes mechanical issues.

Usage:
  python pass2_copy_edit.py outputs/decision-making/book.json

Requires:
  AI_GATEWAY_API_KEY env var
  pip install openai

Output:
  outputs/decision-making/book.json
  outputs/decision-making/copy_edit_log.json (shows changes made)
"""

import os
import argparse
import json
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# --- Config ---
EDITING_MODEL = "anthropic/claude-sonnet-4.5"
RATE_LIMIT_DELAY = 1.0  # seconds between API calls

client = OpenAI(
    api_key=os.getenv("AI_GATEWAY_API_KEY"),
    base_url="https://ai-gateway.vercel.sh/v1",
)


def load_book(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def copy_edit_entry(entry: dict, book_title: str, book_descriptor: str) -> dict:
    """
    Copy edit a single entry. Returns edited content and change summary.
    """
    original_content = entry.get("content", "")
    entry_name = entry.get("name", "Unknown")

    prompt = f"""You are a copy editor for "{book_title}: {book_descriptor}" published at alexandria.press.

Your job is to polish this entry for publication. Make it publication-ready.

**What to fix:**

1. **Grammar & mechanics** — Fix any grammatical errors, punctuation issues, or mechanical problems.

2. **Hedging & filler** — Remove unnecessary hedging ("perhaps", "it seems that", "in some ways", "sort of"). Remove filler phrases that add no meaning.

3. **Flow & clarity** — Improve sentence flow. Break up overly long sentences. Connect ideas smoothly. Make sure each paragraph has a clear point.

4. **Em dash overuse** — Minimize em dashes (—). Most can be replaced with periods (split into two sentences), commas, semicolons, or parentheses. Keep em dashes only for genuine interruptions or strong emphasis.

5. **Consistency** — Ensure consistent voice, tone, and style throughout the entry.

6. **Tightness** — Cut redundancy. Every sentence should earn its place.

7. **Engagement** — Keep the reader moving forward. Remove anything that would make them skip ahead.

**What NOT to change:**

- Do NOT alter the substance or core meaning
- Do NOT add new information or examples not present in the original
- Do NOT change the entry structure significantly
- Keep the voice natural and readable, not overly formal

**Entry name:** {entry_name}

**Original content:**
{original_content}

**Instructions:**
Return ONLY the edited content as plain text. Do not add commentary, do not use markdown formatting for the content itself, do not add "Here is the edited version:" or similar preambles. Just return the clean edited text."""

    try:
        response = client.chat.completions.create(
            model=EDITING_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,  # Slight creativity for natural phrasing
        )
        edited_content = response.choices[0].message.content.strip()
        
        # Remove any markdown wrapping or preambles that might have slipped through
        if edited_content.startswith("```"):
            lines = edited_content.split("\n")
            # Skip first and last lines if they're markdown fences
            if lines[0].startswith("```") and lines[-1].startswith("```"):
                edited_content = "\n".join(lines[1:-1]).strip()
        
        # Detect if Claude added a preamble
        preamble_markers = [
            "here is the edited",
            "here's the edited",
            "edited version:",
            "edited content:",
        ]
        first_line_lower = edited_content.split("\n")[0].lower()
        if any(marker in first_line_lower for marker in preamble_markers):
            edited_content = "\n".join(edited_content.split("\n")[1:]).strip()

        # Calculate rough change metrics
        original_words = len(original_content.split())
        edited_words = len(edited_content.split())
        word_diff = edited_words - original_words

        return {
            "success": True,
            "edited_content": edited_content,
            "change_summary": {
                "original_words": original_words,
                "edited_words": edited_words,
                "word_diff": word_diff,
                "word_diff_pct": round(
                    (word_diff / original_words * 100) if original_words > 0 else 0, 1
                ),
            },
        }

    except Exception as e:
        return {
            "success": False,
            "edited_content": original_content,  # Fallback to original
            "error": str(e),
            "change_summary": {
                "original_words": len(original_content.split()),
                "edited_words": len(original_content.split()),
                "word_diff": 0,
                "word_diff_pct": 0,
            },
        }


def run_pass2(book_path: str, limit: int = None, max_workers: int = 10):
    """Run copy editing pass on all entries in book."""
    print(f"Loading book from: {book_path}")
    book = load_book(book_path)

    title = book.get("title", "Unknown Book")
    descriptor = book.get("descriptor", "")
    entries = book.get("entries", [])

    if limit:
        print(f"Limiting to first {limit} entries.")
        entries = entries[:limit]

    print(f"\nBook: {title}")
    print(f"Entries to edit: {len(entries)}")
    print(f"Starting copy editing pass (workers: {max_workers})...\n")

    # Process each entry in parallel
    edited_entries_map = {} # Map original index to edited entry
    edit_log = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a future for each entry, preserving original index
        future_to_index = {
            executor.submit(copy_edit_entry, entry, title, descriptor): i 
            for i, entry in enumerate(entries)
        }

        # Process as they complete
        for future in tqdm(as_completed(future_to_index), total=len(entries), unit="entry"):
            i = future_to_index[future]
            entry = entries[i]
            entry_name = entry.get("name", f"Entry {i+1}")
            
            try:
                result = future.result()
                
                # Create edited entry
                edited_entry = entry.copy()
                edited_entry["content"] = result["edited_content"]
                edited_entries_map[i] = edited_entry

                # Log the edit
                log_entry = {
                    "entry_name": entry_name,
                    "entry_index": i,
                    "success": result["success"],
                    "change_summary": result["change_summary"],
                }
                if not result["success"]:
                    log_entry["error"] = result.get("error", "Unknown error")
                
                edit_log.append(log_entry)

            except Exception as e:
                print(f"Error processing {entry_name}: {e}")
                # Fallback to original content on error
                edited_entries_map[i] = entry
                edit_log.append({
                    "entry_name": entry_name,
                    "entry_index": i,
                    "success": False,
                    "error": str(e),
                    "change_summary": {"word_diff": 0, "original_words": 0, "edited_words": 0}
                })

    # Reconstruct edited entries list in original order
    edited_entries = [edited_entries_map[i] for i in range(len(entries))]


    # --- Create edited book ---
    edited_book = book.copy()
    edited_book["entries"] = edited_entries
    edited_book["_metadata"] = edited_book.get("_metadata", {})
    edited_book["_metadata"]["pass2_copy_edited"] = True

    # --- Calculate stats ---
    total_word_diff = sum(e["change_summary"]["word_diff"] for e in edit_log)
    successful_edits = sum(1 for e in edit_log if e["success"])
    failed_edits = len(edit_log) - successful_edits

    # --- Save outputs ---
    output_dir = Path(book_path).parent
    edited_book_path = output_dir / "book_edited.json"
    log_path = output_dir / "copy_edit_log.json"

    with open(edited_book_path, "w", encoding="utf-8") as f:
        json.dump(edited_book, f, indent=2, ensure_ascii=False)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": {
                    "total_entries": len(entries),
                    "successful_edits": successful_edits,
                    "failed_edits": failed_edits,
                    "total_word_diff": total_word_diff,
                },
                "entries": edit_log,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    # --- Print Summary ---
    print(f"\n{'=' * 60}")
    print(f"COPY EDITING COMPLETE: {title}")
    print(f"{'=' * 60}")
    print(f"Entries edited: {successful_edits}/{len(entries)}")
    if failed_edits > 0:
        print(f"Failed edits: {failed_edits}")
    print(f"Total word change: {total_word_diff:+d} words")
    print()
    print(f"Edited book saved to: {edited_book_path}")
    print(f"Edit log saved to: {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pass 2: Copy Editing")
    parser.add_argument("book_path", help="Path to book.json")
    parser.add_argument("--limit", type=int, help="Limit number of entries to process")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers")

    args = parser.parse_args()

    run_pass2(args.book_path, limit=args.limit, max_workers=args.workers)