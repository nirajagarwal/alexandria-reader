import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Global Gemini client (safe to cache)
gemini_client = None

EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMS = 768

def get_gemini_client():
    """Get Gemini client for embeddings."""
    global gemini_client
    if gemini_client is None and GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return gemini_client


def generate_embedding(text: str) -> list[float] | None:
    """Generate embedding for text using Gemini."""
    client = get_gemini_client()
    if not client:
        return None
    
    try:
        # Truncate very long text to avoid token limits
        truncated = text[:8000] if len(text) > 8000 else text
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=truncated
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return None
