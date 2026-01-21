import json
from fastapi import APIRouter, HTTPException, Response
from api.database import get_connection
from api.models import Book, Entry, EntryWithNav, Navigation, AdjacentEntry

router = APIRouter(tags=["book"])

def add_cache_control(response: Response, max_age: int = 3600, s_maxage: int = 86400):
    """Add Cache-Control headers."""
    response.headers["Cache-Control"] = f"public, max-age={max_age}, s-maxage={s_maxage}"

@router.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: str, response: Response):
    """Get book metadata."""
    add_cache_control(response)  # Cache book metadata for 24h
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


@router.get("/books/{book_id}/entries", response_model=list[Entry])
async def list_entries(book_id: str, response: Response):
    """Get all entries with full content for reader."""
    add_cache_control(response)  # Cache list for 24h
    conn = get_connection()
    
    # Verify book exists
    book = conn.execute(
        "SELECT book_id FROM books WHERE book_id = ?", 
        (book_id,)
    ).fetchone()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    rows = conn.execute("""
        SELECT sort_order, slug, name, descriptor, content, metadata
        FROM entries
        WHERE book_id = ?
        ORDER BY sort_order
    """, (book_id,)).fetchall()
    
    return [
        Entry(
            order=r[0],
            slug=r[1],
            name=r[2],
            descriptor=r[3],
            content=r[4],
            metadata=json.loads(r[5]) if r[5] else {}
        )
        for r in rows
    ]


@router.get("/books/{book_id}/entries/{slug}", response_model=EntryWithNav, tags=["entry"])
async def get_entry(book_id: str, slug: str, response: Response):
    """Get a single entry with full content and navigation."""
    add_cache_control(response)  # Cache content for 24h
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


@router.get("/books/{book_id}/introduction")
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


@router.get("/books/{book_id}/appendix")
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


@router.get("/books/{book_id}/colophon")
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
