"""
Extract Names from Entries

Processes book.json entries to:
1. Extract the name in parenthesis from the 'name' field (e.g., "Marie Curie")
2. Remove it from the 'name' field along with the parenthesis
3. Set it as the 'descriptor' field

Usage:
    python scripts/extract_names.py outputs/nobel-women/book.json
    python scripts/extract_names.py outputs/nobel-women/book.json --dry-run
"""

import json
import re
import argparse
from pathlib import Path


def extract_parenthetical_name(name: str) -> tuple[str, str | None]:
    """
    Extract the name inside parenthesis from the end of a string.
    
    Returns:
        tuple: (cleaned_name, extracted_name)
        
    Example:
        "1903 — Radioactivity (Marie Curie)" -> ("1903 — Radioactivity", "Marie Curie")
    """
    # Match text in parenthesis at the end, possibly with trailing whitespace
    pattern = r'\s*\(([^)]+)\)\s*$'
    match = re.search(pattern, name)
    
    if match:
        extracted_name = match.group(1).strip()
        cleaned_name = name[:match.start()].strip()
        return cleaned_name, extracted_name
    
    return name, None


def process_book(book_path: str, dry_run: bool = False) -> dict:
    """Process a book.json file, extracting names from entries."""
    
    path = Path(book_path)
    if not path.exists():
        raise FileNotFoundError(f"Book file not found: {book_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        book = json.load(f)
    
    entries = book.get('entries', [])
    changes = []
    
    for entry in entries:
        original_name = entry.get('name', '')
        cleaned_name, extracted = extract_parenthetical_name(original_name)
        
        if extracted:
            changes.append({
                'slug': entry.get('slug'),
                'original_name': original_name,
                'new_name': cleaned_name,
                'descriptor': extracted
            })
            
            if not dry_run:
                entry['name'] = cleaned_name
                entry['descriptor'] = extracted
                
                # Also update the content title if it matches the original name
                content = entry.get('content', '')
                if content.startswith(f'# {original_name}'):
                    entry['content'] = content.replace(
                        f'# {original_name}',
                        f'# {cleaned_name}',
                        1  # Only replace first occurrence
                    )
    
    if not dry_run and changes:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(book, f, indent=2, ensure_ascii=False)
    
    return {
        'total_entries': len(entries),
        'modified': len(changes),
        'changes': changes
    }


def main():
    parser = argparse.ArgumentParser(
        description='Extract names from parenthesis in book.json entries'
    )
    parser.add_argument('book_path', help='Path to book.json file')
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Preview changes without modifying the file'
    )
    
    args = parser.parse_args()
    
    try:
        result = process_book(args.book_path, args.dry_run)
        
        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Processed: {args.book_path}")
        print(f"Total entries: {result['total_entries']}")
        print(f"Entries modified: {result['modified']}")
        
        if result['changes']:
            print("\nChanges:")
            for change in result['changes']:
                print(f"\n  {change['slug']}:")
                print(f"    Before: {change['original_name']}")
                print(f"    After:  {change['new_name']}")
                print(f"    Descriptor: {change['descriptor']}")
        
        if args.dry_run and result['changes']:
            print(f"\n[DRY RUN] Run without --dry-run to apply {result['modified']} changes.")
        elif result['changes']:
            print(f"\n✓ Applied {result['modified']} changes.")
        else:
            print("\nNo changes needed.")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
