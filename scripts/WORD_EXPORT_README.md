# Book to Word Exporter

This script converts book data from the `outputs` folder to Microsoft Word documents.

## Installation

First, install the required dependency:

```bash
pip install python-docx
```

## Usage

Run the script from the project root:

```bash
python scripts/export_to_word.py
```

Or make it executable and run directly:

```bash
chmod +x scripts/export_to_word.py
./scripts/export_to_word.py
```

## What It Does

The script will:

1. Scan the `outputs` directory for all `book.json` files
2. For each book:
   - Parse the book metadata (title, descriptor, introduction)
   - Process all entries with their content
   - Convert markdown formatting to Word formatting
   - Apply professional styling
3. Save Word documents to the `outputs_word` directory

## Output Format

Each Word document includes:

- **Book title** (centered, large font)
- **Book descriptor** (centered, italic)
- **Introduction** (if available)
- **Entries** with:
  - Entry titles (bold, larger font)
  - Entry descriptors (italic, gray)
  - Formatted content with headings, paragraphs, and blockquotes
  - Page breaks between entries

## Features

- Preserves markdown formatting (bold, italic, headings)
- Handles blockquotes with special styling
- Includes metadata for special collections (e.g., atomic numbers for Periodic Tales)
- Professional typography with Georgia font
- Proper spacing and indentation
- Clean, readable output

## Example

```bash
$ python scripts/export_to_word.py

Alexandria Press - Book to Word Exporter
==================================================
Outputs directory: /Users/niraj/alexandria-press/outputs
Word output directory: /Users/niraj/alexandria-press/outputs_word

Found 9 books to process

Processing: /Users/niraj/alexandria-press/outputs/body/book.json
  Found 30 entries
  Processing entry 1/30: The Skeletal System
  ...
✓ Saved: /Users/niraj/alexandria-press/outputs_word/body.docx
```

## Notes

- The script creates a new `outputs_word` directory if it doesn't exist
- Each book becomes a single Word document named after its book_id
- Existing Word files will be overwritten
- The script handles special characters and formatting gracefully
