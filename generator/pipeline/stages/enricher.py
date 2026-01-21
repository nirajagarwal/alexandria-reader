import google.genai as genai
from ..config import GEMINI_API_KEY, EMBEDDING_MODEL
from ..models import Book
from .base import Stage

class Enricher(Stage):
    def __init__(self, context):
        super().__init__(context)
        if GEMINI_API_KEY:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        else:
            self.client = None
            print("Warning: GEMINI_API_KEY not found. Embeddings will be skipped.")

    def execute(self, book: Book) -> Book:
        if not self.client:
            return book
            
        print(f"Generating embeddings for {len(book.entries)} entries...")
        
        for i, entry in enumerate(book.entries):
            # Skip if embedding exists or content is missing
            if entry.embedding or not entry.content:
                continue
                
            text = self._create_embedding_text(entry.name, entry.descriptor, entry.content)
            
            try:
                embedding = self._generate_embedding(text)
                if embedding:
                    entry.embedding = embedding
                    print(f"  [{i + 1}/{len(book.entries)}] Embedding ✓ {entry.name}")
            except Exception as e:
                print(f"  [{i + 1}/{len(book.entries)}] Embedding ✗ {entry.name}: {e}")
                
        return book

    def _generate_embedding(self, text: str):
        # Truncate very long text to avoid token limits
        truncated = text[:8000] if len(text) > 8000 else text
        result = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=truncated
        )
        return result.embeddings[0].values

    def _create_embedding_text(self, name: str, descriptor: str | None, content: str | None) -> str:
        parts = [name]
        if descriptor:
            parts.append(descriptor)
        if content:
            parts.append(content[:4000])
        return "\n\n".join(parts)
