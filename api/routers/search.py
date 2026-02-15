from fastapi import APIRouter, HTTPException, Query
from api.database import get_connection
from api.models import SearchResult
from api.services.embedding import generate_embedding

router = APIRouter(tags=["search"])

@router.get("/search", response_model=list[SearchResult])
async def search_entries(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results")
):
    """Semantic search across all book entries."""
    conn = get_connection()
    
    # Try vector search first
    query_embedding = generate_embedding(q)
    
    if query_embedding:
        try:
            vector_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
            # Use vector_top_k for efficient similarity search
            rows = conn.execute("""
                SELECT 
                    e.book_id,
                    b.title as book_title,
                    e.slug,
                    e.name,
                    e.descriptor,
                    vector_distance_cos(e.embedding, vector(?)) as distance
                FROM entries e
                JOIN books b ON e.book_id = b.book_id
                WHERE e.embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT ?
            """, (vector_str, limit)).fetchall()
            
            return [
                SearchResult(
                    book_id=r[0],
                    book_title=r[1],
                    slug=r[2],
                    name=r[3],
                    descriptor=r[4],
                    score=round(1 - (r[5] or 0), 4)
                )
                for r in rows
            ]
        except Exception as e:
            print(f"Vector search failed: {e}")
            # Fall through to text search
            pass
    
    # Fallback: Text Search
    print("Falling back to text search")
    rows = conn.execute("""
        SELECT 
            e.book_id,
            b.title as book_title,
            e.slug,
            e.name,
            e.descriptor
        FROM entries e
        JOIN books b ON e.book_id = b.book_id
        WHERE e.name LIKE ? OR e.descriptor LIKE ?
        LIMIT ?
    """, (f"%{q}%", f"%{q}%", limit)).fetchall()
    
    return [
        SearchResult(
            book_id=r[0],
            book_title=r[1],
            slug=r[2],
            name=r[3],
            descriptor=r[4],
            score=0.5
        )
        for r in rows
    ]

