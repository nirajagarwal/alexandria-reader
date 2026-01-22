from pathlib import Path
from PIL import Image
import google.genai as genai
from google.genai import types

from ..config import GEMINI_API_KEY, IMAGEN_MODEL, OUTPUT_DIR
from ..models import Book
from .base import Stage

class Designer(Stage):
    def execute(self, book: Book) -> Book:
        print(f"Designing cover for: {book.book_id}")
        
        # Check if cover already exists and we shouldn't overwrite?
        # For now, let's assume if we run the pipeline, we want to ensure the cover exists.
        # If it exists, we might want to skip to save cost/time unless forced.
        # But per user request "Are images not generated as a part of the run_pipeline.py?", implies expectation they are.
        
        output_dir = OUTPUT_DIR / book.book_id
        output_dir.mkdir(parents=True, exist_ok=True)
        cover_path = output_dir / "cover.png"
        
        # If cover exists, verify size? Or just skip?
        # Let's skip if it exists to be safe and cost-effective, but log it.
        # User can delete cover to regenerate.
        if cover_path.exists():
            print(f"  Cover already exists at {cover_path}")
            book.cover_path = f"/outputs/{book.book_id}/cover.png"
            return book

        if not GEMINI_API_KEY:
            print("  Warning: GEMINI_API_KEY not found, skipping cover generation")
            return book

        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            # Updated Prompt for Full Bleed
            prompt = f"""Abstract art representing '{book.title}: {book.descriptor}'.
Style: Modern, minimalist, abstract, high-quality texture.
Composition: Full bleed, edge-to-edge art. EXTEND TO ALL EDGES. No borders, no frames, no white margins, no book mockup.
Colors: Subtle gradient or texture.
IMPORTANT: The image must NOT contain any text, letters, numbers, or characters. Purely visual art."""
            
            print(f"  Generating image with {IMAGEN_MODEL}...")
            response = client.models.generate_content(
                model=IMAGEN_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(
                        aspect_ratio="3:4"
                    ),
                    safety_settings=[types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="BLOCK_ONLY_HIGH"
                    )]
                )
            )
            
            image = None
            for part in response.parts:
                if part.inline_data is not None:
                    import io
                    img_bytes = part.inline_data.data
                    image = Image.open(io.BytesIO(img_bytes))
                    break
            
            if image:
                # Save original temporarily
                # We can skip temp save if using Pillow directly, but keeping logic consistent
                # Actually, let's just resize the PIL image directly
                
                print("  Resizing to 400px width...")
                width_percent = (400 / float(image.size[0]))
                hsize = int((float(image.size[1]) * float(width_percent)))
                
                img_resized = image.resize((400, hsize), Image.Resampling.LANCZOS)
                img_resized.save(cover_path)
                
                print(f"  ✓ Cover generated and resized: {cover_path}")
                book.cover_path = f"/outputs/{book.book_id}/cover.png"
                
        except Exception as e:
            print(f"  ✗ Cover generation failed: {e}")
            
        return book
