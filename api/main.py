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
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import routers
from api.routers import library, books, search, system

# Load environment variables
load_dotenv()

# Get project root (main.py is in api/)
BASE_DIR = Path(__file__).parent.parent


# =============================================================================
# Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for FastAPI application."""
    # Nothing to initialize - connections are per-request
    yield
    # Nothing to cleanup - connections are auto-closed


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

# Include Routers
app.include_router(library.router)
app.include_router(books.router)
app.include_router(search.router)
app.include_router(system.router)


# =============================================================================
# Error Handling
# =============================================================================

@app.exception_handler(404)
async def custom_404_handler(request, __):
    # Retrieve the path that caused the 404
    path = request.url.path
    # Check if we should serve the HTML 404
    html_404 = BASE_DIR / "frontend" / "404.html"
    if html_404.exists():
        return FileResponse(html_404, status_code=404)
    return {"error": "Not Found", "detail": f"Path '{path}' not found in API"}


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

@app.get("/reader.html", include_in_schema=False)
async def serve_reader():
    return FileResponse(BASE_DIR / "frontend" / "reader.html")

@app.get("/sw.js", include_in_schema=False)
async def serve_sw():
    return FileResponse(BASE_DIR / "frontend" / "sw.js")

@app.get("/sitemap.xml", include_in_schema=False)
async def serve_sitemap():
    return FileResponse(BASE_DIR / "sitemap.xml")
