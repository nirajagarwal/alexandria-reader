"""
Alexandria Press - Migrate Database for Embeddings

Adds embedding column to entries table.

Usage:
    python migrate_embeddings.py
    
Environment:
    TURSO_DATABASE_URL=libsql://your-db.turso.io
    TURSO_AUTH_TOKEN=your-token
"""

import os
from dotenv import load_dotenv
import libsql_experimental as libsql

load_dotenv()

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")


def get_connection():
    """Create connection to Turso database."""
    return libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )


def migrate():
    """Add embedding column and vector index to entries table."""
    conn = get_connection()
    
    # Check if column exists
    cols = conn.execute("PRAGMA table_info(entries)").fetchall()
    col_names = [c[1] for c in cols]
    
    if "embedding" in col_names:
        print("Embedding column already exists")
    else:
        print("Adding embedding column...")
        conn.execute("ALTER TABLE entries ADD COLUMN embedding F32_BLOB(768)")
        conn.commit()
        print("✓ Embedding column added")
    
    # Try to create vector index (may fail if not supported in current env)
    try:
        print("Creating vector index...")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_embedding ON entries(libsql_vector_idx(embedding))")
        conn.commit()
        print("✓ Vector index created")
    except Exception as e:
        print(f"⚠ Vector index creation failed (may not be supported in this environment): {e}")
    
    conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    migrate()
