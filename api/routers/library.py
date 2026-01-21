from fastapi import APIRouter
from api.database import get_connection
from api.models import BookSummary

router = APIRouter(tags=["library"])

@router.get("/books", response_model=list[BookSummary])
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
