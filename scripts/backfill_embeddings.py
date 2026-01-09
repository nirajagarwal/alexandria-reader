"""
Alexandria Press - Backfill Embeddings

Generates embeddings for all entries that don't have them.

Usage:
    python backfill_embeddings.py [--dry-run] [--batch-size 10]
    
Environment:
    TURSO_DATABASE_URL=libsql://your-db.turso.io
    TURSO_AUTH_TOKEN=your-token
    GEMINI_API_KEY=your-key
"""

import os
import argparse
import time
from pathlib import Path

from dotenv import load_dotenv
import libsql_experimental as libsql
from google import genai

# Load environment variables
load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMS = 768


# =============================================================================
# Database
# =============================================================================

def get_connection():
    """Create connection to Turso database."""
    return libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )


# =============================================================================
# Embeddings
# =============================================================================

def get_gemini_client():
    """Get Gemini client for embeddings."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_embedding(client, text: str) -> list[float] | None:
    """Generate embedding for text using Gemini."""
    try:
        # Truncate very long text to avoid token limits
        truncated = text[:8000] if len(text) > 8000 else text
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=truncated
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"  Embedding generation failed: {e}")
        return None


def create_embedding_text(name: str, descriptor: str | None, content: str | None) -> str:
    """Create text for embedding from entry fields."""
    parts = [name]
    if descriptor:
        parts.append(descriptor)
    if content:
        # Take first portion of content for embedding
        parts.append(content[:4000])
    return "\n\n".join(parts)


# =============================================================================
# Backfill Logic
# =============================================================================

def get_entries_without_embeddings(conn) -> list[dict]:
    """Get all entries that don't have embeddings."""
    rows = conn.execute("""
        SELECT entry_id, book_id, slug, name, descriptor, content
        FROM entries
        WHERE embedding IS NULL
        ORDER BY book_id, sort_order
    """).fetchall()
    
    return [
        {
            "entry_id": r[0],
            "book_id": r[1],
            "slug": r[2],
            "name": r[3],
            "descriptor": r[4],
            "content": r[5]
        }
        for r in rows
    ]


def update_embedding(conn, entry_id: int, embedding: list[float]):
    """Update an entry with its embedding."""
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
    conn.execute(
        "UPDATE entries SET embedding = vector(?) WHERE entry_id = ?",
        (embedding_str, entry_id)
    )


def backfill_embeddings(dry_run: bool = False, batch_size: int = 10):
    """Backfill embeddings for all entries without them."""
    conn = get_connection()
    client = get_gemini_client()
    
    entries = get_entries_without_embeddings(conn)
    total = len(entries)
    
    if total == 0:
        print("All entries already have embeddings.")
        return
    
    print(f"Found {total} entries without embeddings")
    
    if dry_run:
        print("\nDry run - entries that would be updated:")
        for entry in entries[:20]:  # Show first 20
            print(f"  [{entry['book_id']}] {entry['name']}")
        if total > 20:
            print(f"  ... and {total - 20} more")
        return
    
    print(f"\nProcessing in batches of {batch_size}...")
    
    success = 0
    failed = 0
    
    for i, entry in enumerate(entries):
        # Create text for embedding
        text = create_embedding_text(
            entry["name"],
            entry["descriptor"],
            entry["content"]
        )
        
        # Generate embedding
        embedding = generate_embedding(client, text)
        
        if embedding:
            update_embedding(conn, entry["entry_id"], embedding)
            success += 1
            print(f"[{i + 1}/{total}] ✓ {entry['name']}")
        else:
            failed += 1
            print(f"[{i + 1}/{total}] ✗ {entry['name']}")
        
        # Commit in batches
        if (i + 1) % batch_size == 0:
            conn.commit()
            print(f"  Committed batch ({i + 1} entries)")
            # Small delay to avoid rate limits
            time.sleep(0.5)
    
    # Final commit
    conn.commit()
    conn.close()
    
    print(f"\nComplete: {success} successful, {failed} failed")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Backfill embeddings for entries")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    parser.add_argument("--batch-size", type=int, default=10, help="Commit after this many entries (default: 10)")
    
    args = parser.parse_args()
    
    backfill_embeddings(dry_run=args.dry_run, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
