"""
Alexandria Press - API

FastAPI application serving book content from Turso.

Usage:
    uvicorn main:app --reload
    
Environment:
    TURSO_DATABASE_URL=libsql://your-db.turso.io
    TURSO_AUTH_TOKEN=your-token
"""

import os
import json
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import libsql_experimental as libsql

# Load environment variables
load_dotenv()

# Get project root (main.py is in api/)
BASE_DIR = Path(__file__).parent.parent


# =============================================================================
# Configuration
# =============================================================================

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

# Global connection
db = None


# =============================================================================
# Models
# =============================================================================

class BookSummary(BaseModel):
    book_id: str
    title: str
    descriptor: str | None
    cover_url: str | None


class Book(BaseModel):
    book_id: str
    title: str
    descriptor: str | None
    cover_url: str | None
    model: str | None
    created_at: str
    introduction: str | None
    appendix_prompt: str | None
    colophon: str | None
    card_display: dict


class EntryCard(BaseModel):
    order: int
    slug: str
    name: str
    descriptor: str | None
    metadata: dict


class Entry(BaseModel):
    order: int
    slug: str
    name: str
    descriptor: str | None
    content: str | None
    metadata: dict


class AdjacentEntry(BaseModel):
    slug: str
    name: str


class Navigation(BaseModel):
    prev: AdjacentEntry | None
    next: AdjacentEntry | None


class EntryWithNav(BaseModel):
    entry: Entry
    nav: Navigation


# =============================================================================
# Database
# =============================================================================

def get_connection():
    """Get database connection."""
    global db
    if db is None:
        db = libsql.connect(
            database=TURSO_DATABASE_URL,
            auth_token=TURSO_AUTH_TOKEN
        )
    return db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    get_connection()
    yield
    if db:
        db.close()


# =============================================================================
# Application
# =============================================================================

app = FastAPI(
    title="Alexandria Press API",
    description="API for serving AI-generated book collections",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(404)
async def custom_404_handler(request, __):
    # Retrieve the path that caused the 404
    path = request.url.path
    # Check if we should serve the HTML 404
    html_404 = BASE_DIR / "frontend" / "404.html"
    if html_404.exists():
        return FileResponse(html_404, status_code=404)
    return {"error": "Not Found", "detail": f"Path '{path}' not found in API"}



@app.get("/debug", tags=["system"])
async def debug_request(request: Request):
    """Debug endpoint to inspect request scope."""
    return {
        "url": str(request.url),
        "base_url": str(request.base_url),
        "path": request.url.path,
        "root_path": request.scope.get("root_path"),
        "headers": dict(request.headers),
        "env_vercel": os.environ.get("VERCEL", "false"),
    }



@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "env": "production" if not os.environ.get("VERCEL_DEV") else "dev"}


# =============================================================================
# Routes: Library
# =============================================================================


@app.get("/books", response_model=list[BookSummary], tags=["library"])
async def list_books():
    """Get all books for library view."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT book_id, title, descriptor, cover_url 
        FROM books
        ORDER BY created_at DESC
    """).fetchall()
    
    return [
        BookSummary(
            book_id=r[0],
            title=r[1],
            descriptor=r[2],
            cover_url=r[3]
        )
        for r in rows
    ]


# =============================================================================
# Routes: Book
# =============================================================================

@app.get("/books/{book_id}", response_model=Book, tags=["book"])
async def get_book(book_id: str):
    """Get book metadata."""
    conn = get_connection()
    row = conn.execute("""
        SELECT book_id, title, descriptor, cover_url, model, 
               created_at, introduction, appendix_prompt, colophon, card_display
        FROM books WHERE book_id = ?
    """, (book_id,)).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return Book(
        book_id=row[0],
        title=row[1],
        descriptor=row[2],
        cover_url=row[3],
        model=row[4],
        created_at=row[5],
        introduction=row[6],
        appendix_prompt=row[7],
        colophon=row[8],
        card_display=json.loads(row[9]) if row[9] else {}
    )


@app.get("/books/{book_id}/entries", response_model=list[EntryCard], tags=["book"])
async def list_entries(book_id: str):
    """Get all entries for card grid (without content)."""
    conn = get_connection()
    
    # Verify book exists
    book = conn.execute(
        "SELECT book_id FROM books WHERE book_id = ?", 
        (book_id,)
    ).fetchone()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    rows = conn.execute("""
        SELECT sort_order, slug, name, descriptor, metadata
        FROM entries
        WHERE book_id = ?
        ORDER BY sort_order
    """, (book_id,)).fetchall()
    
    return [
        EntryCard(
            order=r[0],
            slug=r[1],
            name=r[2],
            descriptor=r[3],
            metadata=json.loads(r[4]) if r[4] else {}
        )
        for r in rows
    ]


# =============================================================================
# Routes: Entry
# =============================================================================

@app.get("/books/{book_id}/entries/{slug}", response_model=EntryWithNav, tags=["entry"])
async def get_entry(book_id: str, slug: str):
    """Get a single entry with full content and navigation."""
    conn = get_connection()
    
    # Get entry
    row = conn.execute("""
        SELECT sort_order, slug, name, descriptor, content, metadata
        FROM entries
        WHERE book_id = ? AND slug = ?
    """, (book_id, slug)).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry = Entry(
        order=row[0],
        slug=row[1],
        name=row[2],
        descriptor=row[3],
        content=row[4],
        metadata=json.loads(row[5]) if row[5] else {}
    )
    
    # Get navigation
    current_order = row[0]
    
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
    
    nav = Navigation(
        prev=AdjacentEntry(slug=prev_row[0], name=prev_row[1]) if prev_row else None,
        next=AdjacentEntry(slug=next_row[0], name=next_row[1]) if next_row else None
    )
    
    return EntryWithNav(entry=entry, nav=nav)


# =============================================================================
# Routes: Book Content Pages
# =============================================================================

@app.get("/books/{book_id}/introduction", tags=["book"])
async def get_introduction(book_id: str):
    """Get book introduction."""
    conn = get_connection()
    row = conn.execute(
        "SELECT introduction FROM books WHERE book_id = ?",
        (book_id,)
    ).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"content": row[0]}


@app.get("/books/{book_id}/appendix", tags=["book"])
async def get_appendix(book_id: str):
    """Get book appendix (the prompt)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT appendix_prompt FROM books WHERE book_id = ?",
        (book_id,)
    ).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"content": row[0]}


@app.get("/books/{book_id}/colophon", tags=["book"])
async def get_colophon(book_id: str):
    """Get book colophon."""
    conn = get_connection()
    row = conn.execute(
        "SELECT colophon FROM books WHERE book_id = ?",
        (book_id,)
    ).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"content": row[0]}


from fastapi.responses import FileResponse

# =============================================================================
# Static Files & Frontend
# =============================================================================

# Serve generated assets
if (BASE_DIR / "outputs").exists():
    app.mount("/outputs", StaticFiles(directory=str(BASE_DIR / "outputs")), name="outputs")

# Serve CSS and JS subdirectories
if (BASE_DIR / "frontend" / "css").exists():
    app.mount("/css", StaticFiles(directory=str(BASE_DIR / "frontend" / "css")), name="css")

if (BASE_DIR / "frontend" / "js").exists():
    app.mount("/js", StaticFiles(directory=str(BASE_DIR / "frontend" / "js")), name="js")

if (BASE_DIR / "frontend" / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "frontend" / "assets")), name="assets")

# Explicit routes for frontend HTML files
@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(BASE_DIR / "frontend" / "index.html")

@app.get("/book.html", include_in_schema=False)
async def serve_book():
    return FileResponse(BASE_DIR / "frontend" / "book.html")

@app.get("/robots.txt", include_in_schema=False)
async def serve_robots():
    return FileResponse(BASE_DIR / "frontend" / "robots.txt")

@app.get("/manifest.json", include_in_schema=False)
async def serve_manifest():
    return FileResponse(BASE_DIR / "frontend" / "manifest.json")


@app.get("/sitemap.xml", include_in_schema=False)
async def serve_sitemap():
    return FileResponse(BASE_DIR / "frontend" / "sitemap.xml")


