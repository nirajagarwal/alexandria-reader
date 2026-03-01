import os
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-sonnet-4-5"

# Paths
BASE_DIR = Path(__file__).parent
PROMPT_FILE = BASE_DIR / "prompt.md"
ENTITIES_FILE = BASE_DIR / "entities.json"
OUTPUT_DIR = BASE_DIR / "entries"
FINAL_OUTPUT = BASE_DIR / "book.md"

# =============================================================================
# Clients
# =============================================================================

def get_anthropic_client():
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# =============================================================================
# Data Loading
# =============================================================================

def load_entities():
    if not ENTITIES_FILE.exists():
        raise FileNotFoundError(f"Entities file not found: {ENTITIES_FILE}")
    
    with open(ENTITIES_FILE, "r") as f:
        return json.load(f)

def load_prompt() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE}")
    
    with open(PROMPT_FILE, "r") as f:
        return f.read()

# =============================================================================
# Helpers
# =============================================================================

def get_entries_list(data):
    """Normalized way to get a list of entries from the loaded JSON data."""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("entries", [])
    return []

def get_slug(entry, index):
    """Get a filename-safe slug for an entry."""
    # 1. Use explicit slug if available
    if "slug" in entry and entry["slug"]:
        return entry["slug"]
    
    # 2. Slugify title if available
    if "title" in entry and entry["title"]:
        slug = entry["title"].lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        return slug

    # 3. Fallback to index
    return f"entry_{index:03d}"

# =============================================================================
# Content Generation
# =============================================================================

def generate_entry_content(
    client: anthropic.Anthropic, 
    system_prompt: str, 
    entry_data: dict
) -> str:
    """Generate content for a single entry using Anthropic."""
    
    # Generic prompt injection: pass the entire JSON object
    user_prompt = f"""
Please generate an entry based on the following data:

{json.dumps(entry_data, indent=2)}
"""

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
            {"role": "user", "content": user_prompt.strip()}
        ]
    )
    return message.content[0].text

def save_entry(slug: str, content: str):
    """Save a single entry to disk as markdown."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / f"{slug}.md"
    with open(filepath, "w") as f:
        f.write(content)

def generate_all_entries(max_workers: int = 5):
    """Generate content for all entries."""
    print("Starting generation...")
    
    client = get_anthropic_client()
    data = load_entities()
    system_prompt = load_prompt()
    
    entries = get_entries_list(data)
    entries_to_process = []
    
    # Pre-calculate slugs and check existence
    for i, item in enumerate(entries):
        slug = get_slug(item, i)
        item["_slug"] = slug # Store specifically for internal use
        
        output_path = OUTPUT_DIR / f"{slug}.md"
        
        if output_path.exists():
            print(f"Skipping existing: {item.get('title', slug)}")
            continue
            
        entries_to_process.append(item)
    
    if not entries_to_process:
        print("All entries already generated.")
        return

    print(f"Queueing {len(entries_to_process)} entries for generation...")
    
    completed = 0
    total = len(entries_to_process)
    
    def process_entity(entity):
        title = entity.get('title', entity['_slug'])
        try:
            print(f"Generating: {title}...")
            content = generate_entry_content(client, system_prompt, entity)
            save_entry(entity["_slug"], content)
            return title
        except Exception as e:
            print(f"✗ Failed {title}: {e}")
            return None
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_entity, item): item for item in entries_to_process}
        
        for future in as_completed(futures):
            result_title = future.result()
            if result_title:
                completed += 1
                print(f"[{completed}/{total}] ✓ Finished: {result_title}")

# =============================================================================
# Book Assembly
# =============================================================================

def assemble_book():
    """Assemble all generated entries into a single book.md file."""
    print("\nAssembling book.md...")
    
    if not OUTPUT_DIR.exists():
        print(f"No entries directory found at {OUTPUT_DIR}")
        return

    # Get all markdown files and sort them alphabetically
    md_files = sorted(list(OUTPUT_DIR.glob("*.md")))
    
    if not md_files:
        print("No markdown files found to assemble.")
        return

    print(f"Found {len(md_files)} files to assemble.")
    
    all_content = []
    all_content.append("# Generated Book\n\n")
    
    for filepath in md_files:
        with open(filepath, "r") as f:
            content = f.read()
            all_content.append(content)
            all_content.append("\n\n---\n\n") # Separator between entries
    
    with open(FINAL_OUTPUT, "w") as f:
        f.write("".join(all_content))
    
    print(f"Book assembled at: {FINAL_OUTPUT}")

# =============================================================================
# Main
# =============================================================================

def main():
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate any missing entries
    generate_all_entries()
    
    # 2. Assemble the final book
    assemble_book()
    
    print("Done.")

if __name__ == "__main__":
    main()
