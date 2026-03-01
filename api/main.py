"""
Alexandria — API

FastAPI application serving the Alexandria digital library.
Books are defined in data/books.json; epub files are in outputs/{id}/book.epub;
cover images are in data/{id}/cover.png.

Usage:
    uvicorn api.main:app --reload

Environment (optional — only needed if Turso search is used):
    TURSO_DATABASE_URL=libsql://your-db.turso.io
    TURSO_AUTH_TOKEN=your-token
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
BOOKS_JSON = DATA_DIR / "books.json"


# =============================================================================
# Application
# =============================================================================

app = FastAPI(
    title="Alexandria API",
    description="API for the Alexandria digital library",
    version="2.0.0",
    docs_url=None,   # Hide docs in production
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# =============================================================================
# Helpers
# =============================================================================

def load_books() -> list[dict]:
    """Load books from data/books.json."""
    if not BOOKS_JSON.exists():
        return []
    with open(BOOKS_JSON) as f:
        return json.load(f)


# =============================================================================
# API Routes
# =============================================================================

@app.get("/api/books", include_in_schema=True)
async def list_books():
    """Return all books (without full chapter list to keep payload small)."""
    books = load_books()
    # Return lightweight version for library listing
    return JSONResponse([
        {
            "id": b["id"],
            "title": b["title"],
            "subtitle": b.get("subtitle", ""),
            "cover": b.get("cover"),
            "epub": b.get("epub"),
        }
        for b in books
    ], headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/books/{book_id}", include_in_schema=True)
async def get_book(book_id: str):
    """Return a single book's metadata and chapter list."""
    books = load_books()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(book, headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/search", include_in_schema=True)
async def search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    """Search books and chapters by title (client also does this, server is backup)."""
    books = load_books()
    query = q.lower()
    results = []

    for book in books:
        score = 0
        if query in book["title"].lower():
            score = 2
        elif query in book.get("subtitle", "").lower():
            score = 1.5

        if score > 0:
            results.append({
                "type": "book",
                "book_id": book["id"],
                "book_title": book["title"],
                "title": book["title"],
                "subtitle": book.get("subtitle", ""),
                "cover": book.get("cover"),
                "score": score,
            })

        for ch in book.get("chapters", []):
            if query in ch["title"].lower():
                results.append({
                    "type": "chapter",
                    "book_id": book["id"],
                    "book_title": book["title"],
                    "title": ch["title"],
                    "href": ch.get("href", ""),
                    "score": 1,
                })

    results.sort(key=lambda r: -r["score"])
    return JSONResponse(results[:limit], headers={"Cache-Control": "no-store"})


# =============================================================================
# Error Handling
# =============================================================================

@app.exception_handler(404)
async def custom_404_handler(request, _):
    path = request.url.path
    # Return JSON for API paths
    if path.startswith("/api/"):
        return JSONResponse({"error": "Not found", "path": path}, status_code=404)
    html_404 = BASE_DIR / "frontend" / "404.html"
    if html_404.exists():
        return FileResponse(html_404, status_code=404)
    return JSONResponse({"error": "Not found"}, status_code=404)


# =============================================================================
# Static Files
# =============================================================================

# Epub files and book covers
if (BASE_DIR / "outputs").exists():
    app.mount("/outputs", StaticFiles(directory=str(BASE_DIR / "outputs")), name="outputs")

# data/ folder (covers, books.json)
if DATA_DIR.exists():
    app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

# Frontend assets
if (BASE_DIR / "frontend" / "css").exists():
    app.mount("/css", StaticFiles(directory=str(BASE_DIR / "frontend" / "css")), name="css")

if (BASE_DIR / "frontend" / "js").exists():
    app.mount("/js", StaticFiles(directory=str(BASE_DIR / "frontend" / "js")), name="js")

if (BASE_DIR / "frontend" / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "frontend" / "assets")), name="assets")


# =============================================================================
# Frontend HTML Routes
# =============================================================================

@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(BASE_DIR / "frontend" / "index.html")

@app.get("/reader.html", include_in_schema=False)
async def serve_reader():
    return FileResponse(BASE_DIR / "frontend" / "reader.html")

@app.get("/robots.txt", include_in_schema=False)
async def serve_robots():
    return FileResponse(BASE_DIR / "frontend" / "robots.txt")

@app.get("/manifest.json", include_in_schema=False)
async def serve_manifest():
    return FileResponse(BASE_DIR / "frontend" / "manifest.json")

@app.get("/sw.js", include_in_schema=False)
async def serve_sw():
    return FileResponse(BASE_DIR / "frontend" / "sw.js")

@app.get("/sitemap.xml", include_in_schema=False)
async def serve_sitemap():
    sitemap = BASE_DIR / "sitemap.xml"
    if sitemap.exists():
        return FileResponse(sitemap)
    return JSONResponse({"error": "Not found"}, status_code=404)
