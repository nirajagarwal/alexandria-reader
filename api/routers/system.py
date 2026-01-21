import os
from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])

@router.get("/debug")
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

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "env": "production" if not os.environ.get("VERCEL_DEV") else "dev"}
