"""
Alexandria Press - Book Generator

Generates complete book content from a prompt template and entity list.
Stores results in MongoDB or Turso.

Usage:
    python generate.py --collection periodic-tales
"""

import os
import json
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path
from io import BytesIO

import anthropic
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

ANTHROPIC_MODEL = "claude-sonnet-4-5"
IMAGEN_MODEL = "imagen-4.0-generate-001"

BASE_DIR = Path(__file__).parent.parent  # Project root
PROMPTS_DIR = BASE_DIR / "prompts"
ENTITIES_DIR = BASE_DIR / "entities"
OUTPUT_DIR = BASE_DIR / "outputs"


# =============================================================================
# Clients
# =============================================================================

def get_anthropic_client():
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


# Embedding configuration
EMBEDDING_MODEL = "text-embedding-004"


def generate_embedding(text: str) -> list[float] | None:
    """Generate embedding for text using Gemini."""
    client = get_gemini_client()
    try:
        # Truncate very long text to avoid token limits
        truncated = text[:8000] if len(text) > 8000 else text
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=truncated
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"  Embedding generation failed: {e}")
        return None


def create_embedding_text(name: str, descriptor: str | None, content: str | None) -> str:
    """Create text for embedding from entry fields."""
    parts = [name]
    if descriptor:
        parts.append(descriptor)
    if content:
        parts.append(content[:4000])
    return "\n\n".join(parts)


# =============================================================================
# Content Generation
# =============================================================================

def load_prompt(collection_id: str) -> str:
    """Load the system prompt for a collection."""
    prompt_path = PROMPTS_DIR / f"{collection_id}.md"
    with open(prompt_path, "r") as f:
        return f.read()


def load_entities(collection_id: str) -> dict:
    """Load the entity list and metadata for a collection."""
    entities_path = ENTITIES_DIR / f"{collection_id}.json"
    with open(entities_path, "r") as f:
        return json.load(f)


def extract_descriptor(content: str) -> str | None:
    """Extract the descriptor from the first few lines of generated content."""
    lines = content.strip().split("\n")
    # Look for ***Descriptor*** pattern in first 5 lines
    for line in lines[:5]:
        match = re.match(r"\*\*\*(.+?)\*\*\*", line.strip())
        if match:
            return match.group(1)
    return None


def generate_entry(client: anthropic.Anthropic, system_prompt: str, entity_name: str) -> str:
    """Generate a single entry using the Anthropic API."""
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": entity_name}
        ]
    )
    return message.content[0].text


def generate_all_entries(collection_id: str, resume_from: int = 0, skip_existing: bool = False, max_workers: int = 10) -> list[dict]:
    """Generate entries for all entities in a collection using parallel execution."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    client = get_anthropic_client()
    system_prompt = load_prompt(collection_id)
    collection_data = load_entities(collection_id)
    
    # Filter entities to process
    entities_to_process = []
    total = len(collection_data["entries"])
    
    for i, entity in enumerate(collection_data["entries"]):
        if i < resume_from:
            continue
        
        if skip_existing:
            output_path = OUTPUT_DIR / collection_id / "entries" / f"{entity['slug']}.md"
            if output_path.exists():
                print(f"[{i + 1}/{total}] Skipping (exists): {entity['name']}")
                continue
        
        entities_to_process.append((i, entity))
    
    print(f"\nProcessing {len(entities_to_process)} entries with {max_workers} workers...\n")
    
    entries = []
    completed = 0
    lock = threading.Lock()
    
    def process_entity(args):
        nonlocal completed
        i, entity = args
        
        try:
            content = generate_entry(client, system_prompt, entity["name"])
            descriptor = extract_descriptor(content)
            
            entry = {
                "order": entity["order"],
                "slug": entity["slug"],
                "name": entity["name"],
                "descriptor": descriptor,
                "content": content,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Include any additional entity metadata
            for key in entity:
                if key not in entry:
                    entry[key] = entity[key]
            
            # Save immediately (thread-safe due to unique filenames)
            save_entry(collection_id, entry)
            
            with lock:
                completed += 1
                print(f"[{completed}/{len(entities_to_process)}] ✓ {entity['name']}")
            
            return entry
            
        except Exception as e:
            with lock:
                completed += 1
                print(f"[{completed}/{len(entities_to_process)}] ✗ {entity['name']}: {e}")
            return None
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_entity, args): args for args in entities_to_process}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                entries.append(result)
    
    print(f"\nCompleted: {len(entries)} successful, {len(entities_to_process) - len(entries)} failed")
    return entries


def save_entry(collection_id: str, entry: dict):
    """Save a single entry to disk as markdown."""
    output_path = OUTPUT_DIR / collection_id / "entries"
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / f"{entry['slug']}.md"
    with open(filepath, "w") as f:
        f.write(entry["content"])


# =============================================================================
# Book Components
# =============================================================================

def generate_introduction(client: anthropic.Anthropic, collection_data: dict) -> str:
    """Generate the introduction for a book."""
    prompt = f"""Write a brief introduction for a book titled "{collection_data['title']}".

The book's descriptor is: "{collection_data['descriptor']}"

This is an AI-generated collection published on alexandria.press. The introduction should:
- Be 150-250 words
- Explain what the reader will find
- Not apologize for being AI-generated, but acknowledge it matter-of-factly
- Match the voice: restrained, clear, confident, no flourishes
- End with an invitation to begin

Do not use headers. Do NOT add a title. Write in paragraphs."""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def generate_colophon(collection_data: dict, model_used: str) -> str:
    """Generate the colophon for a book."""
    now = datetime.now(timezone.utc).strftime("%B %d, %Y")
    
    return f"""This collection was generated on {now}.

Model: {model_used}
Entries: {len(collection_data['entries'])}

Published at alexandria.press

All content generated by artificial intelligence. No human author.
SynthID watermarks embedded in cover image."""


# =============================================================================
# Cover Image Generation
# =============================================================================

def generate_cover_image(
    collection_id: str,
    title: str,
    descriptor: str,
    style_prompt: str | None = None
) -> bytes:
    """Generate a cover image using Imagen 3."""
    client = get_gemini_client()
    
    # Default style for alexandria.press covers
    # Default style for alexandria.press covers
    if style_prompt is None:
        style_prompt = """Modern abstract style. High quality. Full bleed, edge to edge.
IMPORTANT: Do NOT include any text, letters, numbers, symbols, borders, or frames. Pure artwork only."""
    
    prompt = f"""Create an abstract artistic interpretation of the concept: "{title} - {descriptor}".
{style_prompt}"""
    
    response = client.models.generate_images(
        model=IMAGEN_MODEL,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="3:4",  # Book cover ratio
            output_mime_type="image/png"
        )
    )
    
    return response.generated_images[0].image.image_bytes


def save_cover_image(collection_id: str, image_bytes: bytes) -> Path:
    """Save cover image to disk."""
    output_path = OUTPUT_DIR / collection_id
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / "cover.png"
    
    # Resize before saving
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            # Resize logic: 400px width, aspect ratio preserved
            base_width = 400
            w_percent = (base_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            
            # Use Resampling.LANCZOS for quality
            img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
            img.save(filepath, format="PNG", optimize=True)
            
    except Exception as e:
        print(f"    Resizing failed ({e}), saving original...")
        with open(filepath, "wb") as f:
            f.write(image_bytes)
    
    return filepath


# =============================================================================
# Book Assembly
# =============================================================================

def assemble_book(collection_id: str) -> dict:
    """Assemble all components into a complete book structure."""
    client = get_anthropic_client()
    collection_data = load_entities(collection_id)
    system_prompt = load_prompt(collection_id)
    
    # Load generated entries
    entries_dir = OUTPUT_DIR / collection_id / "entries"
    entries = []
    
    for entity in collection_data["entries"]:
        filepath = entries_dir / f"{entity['slug']}.md"
        if filepath.exists():
            with open(filepath, "r") as f:
                content = f.read()
            
            entry = {
                **entity,
                "content": content,
                "descriptor": extract_descriptor(content)
            }
            entries.append(entry)
    
    # Generate embeddings for entries
    print(f"Generating embeddings for {len(entries)} entries...")
    for i, entry in enumerate(entries):
        text = create_embedding_text(
            entry["name"],
            entry.get("descriptor"),
            entry.get("content")
        )
        embedding = generate_embedding(text)
        if embedding:
            entry["embedding"] = embedding
            print(f"  [{i + 1}/{len(entries)}] ✓ {entry['name']}")
        else:
            print(f"  [{i + 1}/{len(entries)}] ✗ {entry['name']}")
    
    # Generate other components
    print("Generating introduction...")
    introduction = generate_introduction(client, collection_data)
    
    print("Generating colophon...")
    colophon = generate_colophon(collection_data, ANTHROPIC_MODEL)
    
    print("Generating cover image...")
    try:
        cover_bytes = generate_cover_image(
            collection_id,
            collection_data["title"],
            collection_data["descriptor"]
        )
        cover_path = save_cover_image(collection_id, cover_bytes)
        cover_generated = True
    except Exception as e:
        print(f"    Cover generation failed: {e}")
        cover_path = None
        cover_generated = False
    
    # Assemble book
    book = {
        "book_id": collection_id,
        "title": collection_data["title"],
        "descriptor": collection_data["descriptor"],
        "cover_path": str(cover_path) if cover_path else None,
        "model": ANTHROPIC_MODEL,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "introduction": introduction,
        "entries": entries,
        "appendix_prompt": system_prompt,
        "colophon": colophon,
        "card_display": collection_data.get("card_display", {})
    }
    
    # Save complete book JSON
    book_path = OUTPUT_DIR / collection_id / "book.json"
    with open(book_path, "w") as f:
        json.dump(book, f, indent=2)
    
    print(f"Book assembled: {book_path}")
    return book


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate alexandria.press books")
    parser.add_argument("--collection", required=True, help="Collection ID (e.g., periodic-tales)")
    parser.add_argument("--resume-from", type=int, default=0, help="Resume from entry index")
    parser.add_argument("--skip-existing", action="store_true", help="Skip entries that already have output files")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers (default: 10)")
    parser.add_argument("--entries-only", action="store_true", help="Generate entries only, skip assembly")
    parser.add_argument("--assemble-only", action="store_true", help="Assemble existing entries into book")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.assemble_only:
        book = assemble_book(args.collection)
    else:
        print(f"Generating entries for: {args.collection}")
        entries = generate_all_entries(
            args.collection, 
            resume_from=args.resume_from,
            skip_existing=args.skip_existing,
            max_workers=args.workers
        )
        print(f"Generated {len(entries)} entries")
        
        if not args.entries_only:
            print("\nAssembling book...")
            book = assemble_book(args.collection)
    
    print("Done.")


if __name__ == "__main__":
    main()
