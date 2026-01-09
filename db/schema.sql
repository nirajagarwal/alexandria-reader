-- Alexandria Press Database Schema
-- Turso (SQLite)

-- =============================================================================
-- Books
-- =============================================================================

CREATE TABLE IF NOT EXISTS books (
    book_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    descriptor TEXT,
    cover_url TEXT,
    model TEXT,
    created_at TEXT NOT NULL,
    introduction TEXT,
    appendix_prompt TEXT,
    colophon TEXT,
    card_display TEXT  -- JSON: {"primary": "symbol", "secondary": "name", ...}
);

-- =============================================================================
-- Entries
-- =============================================================================

CREATE TABLE IF NOT EXISTS entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    descriptor TEXT,
    content TEXT,
    metadata TEXT,  -- JSON: element-specific fields (symbol, atomic_number, etc.)
    embedding F32_BLOB(768),  -- Vector embedding for semantic search (768 dims for text-embedding-004)
    
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    UNIQUE(book_id, slug)
);

-- Index for fast card grid queries
CREATE INDEX IF NOT EXISTS idx_entries_book_order ON entries(book_id, sort_order);

-- Vector index for semantic search
CREATE INDEX IF NOT EXISTS idx_entries_embedding ON entries(libsql_vector_idx(embedding));

-- =============================================================================
-- Example Queries
-- =============================================================================

-- Library view: all books
-- SELECT book_id, title, descriptor, cover_url FROM books;

-- Book metadata
-- SELECT * FROM books WHERE book_id = 'periodic-tales';

-- Card grid: entries without content
-- SELECT sort_order, slug, name, descriptor, metadata 
-- FROM entries 
-- WHERE book_id = 'periodic-tales' 
-- ORDER BY sort_order;

-- Single entry
-- SELECT * FROM entries WHERE book_id = 'periodic-tales' AND slug = 'hydrogen';

-- Navigation: previous/next
-- SELECT slug, name FROM entries 
-- WHERE book_id = 'periodic-tales' AND sort_order IN (25, 27) 
-- ORDER BY sort_order;
