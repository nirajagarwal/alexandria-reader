"""
Alexandria Press - Database Loader

Loads generated book.json into Turso database.

Usage:
    python load_db.py --book output/periodic-tales/book.json
    
Environment:
    TURSO_DATABASE_URL=libsql://your-db.turso.io
    TURSO_AUTH_TOKEN=your-token
"""

import os
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv
import libsql_experimental as libsql

# Load environment variables from .env
load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")


# =============================================================================
# Database Connection
# =============================================================================

def get_connection():
    """Create connection to Turso database."""
    return libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )


def init_schema(conn):
    """Initialize database schema."""
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, "r") as f:
        schema = f.read()
    
    # Remove comment lines first, then split by semicolon
    lines = [line for line in schema.split('\n') if not line.strip().startswith('--')]
    clean_schema = '\n'.join(lines)
    statements = [s.strip() for s in clean_schema.split(';') if s.strip()]
    
    for statement in statements:
        if statement:
            conn.execute(statement)
    
    conn.commit()
    print("Schema initialized.")


# =============================================================================
# Data Loading
# =============================================================================

def load_book(conn, book_path: str, cover_url: str = None):
    """Load a book.json file into the database."""
    with open(book_path, "r") as f:
        book = json.load(f)
    
    book_id = book.get("book_id") or book.get("collection_id")
    if not book_id:
        raise ValueError("Book JSON must contain 'book_id' or 'collection_id'")
    
    # Check if book already exists
    existing = conn.execute(
        "SELECT book_id FROM books WHERE book_id = ?",
        (book_id,)
    ).fetchone()
    
    if existing:
        print(f"Book '{book_id}' already exists. Updating...")
        delete_book(conn, book_id)
    
    # Normalize cover path/URL
    cover_val = cover_url or book.get("cover_url") or book.get("cover_path")
    if cover_val and os.path.isabs(cover_val):
        # If it's an absolute path within our project, make it relative /outputs/...
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if cover_val.startswith(project_root):
            rel_path = os.path.relpath(cover_val, project_root)
            # Ensure it uses forward slashes and starts with /
            cover_val = "/" + rel_path.replace(os.sep, "/")

    # Insert book
    conn.execute("""
        INSERT INTO books (
            book_id, title, descriptor, cover_url, model, 
            created_at, introduction, appendix_prompt, colophon, card_display
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        book_id,
        book["title"],
        book.get("descriptor"),
        cover_val,
        book.get("model"),
        book["created_at"],
        book.get("introduction"),
        book.get("appendix_prompt"),
        book.get("colophon"),
        json.dumps(book.get("card_display", {}))
    ))
    
    print(f"Inserted book: {book_id}")
    
    # Insert entries
    entries = book.get("entries", [])
    for entry in entries:
        # Extract metadata (everything except standard fields)
        standard_fields = {"order", "slug", "name", "descriptor", "content", "generated_at"}
        metadata = {k: v for k, v in entry.items() if k not in standard_fields}
        
        conn.execute("""
            INSERT INTO entries (
                book_id, sort_order, slug, name, descriptor, content, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            book_id,
            entry["order"],
            entry["slug"],
            entry["name"],
            entry.get("descriptor"),
            entry.get("content"),
            json.dumps(metadata) if metadata else None
        ))
    
    conn.commit()
    print(f"Inserted {len(entries)} entries.")


def delete_book(conn, book_id: str):
    """Delete a book and its entries."""
    conn.execute("DELETE FROM entries WHERE book_id = ?", (book_id,))
    conn.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
    conn.commit()


# =============================================================================
# Queries (for reference/testing)
# =============================================================================

def get_all_books(conn) -> list[dict]:
    """Get all books for library view."""
    rows = conn.execute("""
        SELECT book_id, title, descriptor, cover_url 
        FROM books
    """).fetchall()
    
    return [
        {"book_id": r[0], "title": r[1], "descriptor": r[2], "cover_url": r[3]}
        for r in rows
    ]


def get_book(conn, book_id: str) -> dict | None:
    """Get full book metadata."""
    row = conn.execute("""
        SELECT book_id, title, descriptor, cover_url, model, 
               created_at, introduction, appendix_prompt, colophon, card_display
        FROM books WHERE book_id = ?
    """, (book_id,)).fetchone()
    
    if not row:
        return None
    
    return {
        "book_id": row[0],
        "title": row[1],
        "descriptor": row[2],
        "cover_url": row[3],
        "model": row[4],
        "created_at": row[5],
        "introduction": row[6],
        "appendix_prompt": row[7],
        "colophon": row[8],
        "card_display": json.loads(row[9]) if row[9] else {}
    }


def get_entries_for_cards(conn, book_id: str) -> list[dict]:
    """Get entries without content for card grid."""
    rows = conn.execute("""
        SELECT sort_order, slug, name, descriptor, metadata
        FROM entries
        WHERE book_id = ?
        ORDER BY sort_order
    """, (book_id,)).fetchall()
    
    return [
        {
            "order": r[0],
            "slug": r[1],
            "name": r[2],
            "descriptor": r[3],
            "metadata": json.loads(r[4]) if r[4] else {}
        }
        for r in rows
    ]


def get_entry(conn, book_id: str, slug: str) -> dict | None:
    """Get a single entry with full content."""
    row = conn.execute("""
        SELECT sort_order, slug, name, descriptor, content, metadata
        FROM entries
        WHERE book_id = ? AND slug = ?
    """, (book_id, slug)).fetchone()
    
    if not row:
        return None
    
    return {
        "order": row[0],
        "slug": row[1],
        "name": row[2],
        "descriptor": row[3],
        "content": row[4],
        "metadata": json.loads(row[5]) if row[5] else {}
    }


def get_adjacent_entries(conn, book_id: str, current_order: int) -> dict:
    """Get previous and next entries for navigation."""
    prev_row = conn.execute("""
        SELECT slug, name FROM entries
        WHERE book_id = ? AND sort_order < ?
        ORDER BY sort_order DESC LIMIT 1
    """, (book_id, current_order)).fetchone()
    
    next_row = conn.execute("""
        SELECT slug, name FROM entries
        WHERE book_id = ? AND sort_order > ?
        ORDER BY sort_order ASC LIMIT 1
    """, (book_id, current_order)).fetchone()
    
    return {
        "prev": {"slug": prev_row[0], "name": prev_row[1]} if prev_row else None,
        "next": {"slug": next_row[0], "name": next_row[1]} if next_row else None
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Load books into Turso database")
    parser.add_argument("--book", required=True, help="Path to book.json")
    parser.add_argument("--cover-url", help="URL for cover image (overrides book.json)")
    parser.add_argument("--init-schema", action="store_true", help="Initialize schema first")
    
    args = parser.parse_args()
    
    conn = get_connection()
    
    if args.init_schema:
        init_schema(conn)
    
    load_book(conn, args.book, args.cover_url)
    
    # Verify
    books = get_all_books(conn)
    print(f"\nDatabase now contains {len(books)} book(s):")
    for b in books:
        print(f"  - {b['title']}")
    
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
