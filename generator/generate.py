import os
import json
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

import anthropic
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Models
ANTHROPIC_MODEL = "claude-sonnet-4-5"
IMAGEN_MODEL = "gemini-3-pro-image-preview"

# Paths
BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
ENTITIES_DIR = BASE_DIR / "entities"
OUTPUT_DIR = BASE_DIR / "outputs"


# =============================================================================
# Clients
# =============================================================================

def get_anthropic_client():
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def get_gemini_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return genai.Client(api_key=GEMINI_API_KEY)


# =============================================================================
# Data Loading
# =============================================================================

def load_entities(collection_id: str) -> dict:
    filepath = ENTITIES_DIR / f"{collection_id}.json"
    if not filepath.exists():
        raise FileNotFoundError(f"Entities file not found: {filepath}")
    
    with open(filepath, "r") as f:
        return json.load(f)

def load_prompt(collection_id: str) -> str:
    filepath = PROMPTS_DIR / f"{collection_id}.md"
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt file not found: {filepath}")
    
    with open(filepath, "r") as f:
        return f.read()


# =============================================================================
# Content Generation
# =============================================================================

def generate_entry_content(
    client: anthropic.Anthropic, 
    system_prompt: str, 
    entry_name: str
) -> str:
    """Generate content for a singe entry using Anthropic."""
    
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text", 
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[
            {"role": "user", "content": entry_name}
        ]
    )
    return message.content[0].text


def extract_descriptor(content: str) -> str | None:
    """Extract descriptor from content (between ***)."""
    lines = content.strip().split("\n")
    # Check first few lines
    for line in lines[:5]:
        match = re.match(r"\*\*\*(.+?)\*\*\*", line.strip())
        if match:
            return match.group(1)
    return None


def generate_all_entries(
    collection_id: str, 
    resume_from: int = 0, 
    skip_existing: bool = False,
    max_workers: int = 5
):
    """Generate content for all entries in a collection."""
    print(f"Starting generation for collection: {collection_id}")
    
    client = get_anthropic_client()
    data = load_entities(collection_id)
    system_prompt = load_prompt(collection_id)
    
    entries_to_process = []
    
    # Filter entries
    for i, item in enumerate(data.get("entries", [])):
        if i < resume_from:
            continue
            
        # Check existing
        slug = item["slug"]
        output_path = OUTPUT_DIR / collection_id / "entries" / f"{slug}.md"
        
        if skip_existing and output_path.exists():
            print(f"Skipping existing: {item['name']}")
            continue
            
        entries_to_process.append(item)
    
    print(f"Queueing {len(entries_to_process)} entries for generation...")
    
    entries = []
    completed = 0
    
    def process_entity(entity):
        try:
            # We create a new client per thread if needed, or share one. 
            # Anthropic client is thread safe.
            content = generate_entry_content(client, system_prompt, entity["name"])
            
            # Save immediately
            entry_data = {**entity, "content": content}
            save_entry(collection_id, entry_data)
            
            return entry_data
        except Exception as e:
            # Simple retry logic could go here
            nonlocal completed
            completed += 1
            print(f"[{completed}/{len(entries_to_process)}] ✗ {entity['name']}: {e}")
            return None
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_entity, args): args for args in entries_to_process}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                entries.append(result)
                completed += 1
                print(f"[{completed}/{len(entries_to_process)}] ✓ {result['name']}")
    
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

Do not use headers. Write in paragraphs."""

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
    if style_prompt is None:
        style_prompt = """Modern look. Not too busy. IMPORTANT: No text, letters, numbers, or symbols anywhere on the image."""
    
    prompt = f"""Create a book cover image (3:4 aspect ratio, portrait orientation, edge to edge image, no borders).
The book is about {title} - {descriptor}. 
{style_prompt}"""
    
    # Handle Gemini Image models (e.g. gemini-2.5-flash-image)
    if "gemini" in IMAGEN_MODEL.lower():
        response = client.models.generate_content(
            model=IMAGEN_MODEL,
            contents=prompt
        )
        
        # Extract image bytes from response parts
        # Note: response structure can vary by SDK version, checking logic order
        parts = []
        if hasattr(response, 'parts'):
            parts = response.parts
        elif hasattr(response, 'candidates') and response.candidates:
            parts = response.candidates[0].content.parts
            
        for part in parts:
            if part.inline_data:
                return part.inline_data.data
        
        raise ValueError("No image found in Gemini response")

    # Handle Imagen models
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
