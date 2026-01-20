import os
import sys
import argparse
from pathlib import Path

# Add project root to path to allow imports
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from generator.generate import load_entities, generate_cover_image, save_cover_image

def regenerate_all_covers():
    """Regenerate covers for all collections in entities directory."""
    entities_dir = BASE_DIR / "entities"
    
    # Find all collection JSON files
    collections = [f.stem for f in entities_dir.glob("*.json")]
    
    print(f"Found {len(collections)} collections: {', '.join(collections)}")
    
    for collection_id in collections:
        print(f"\nProcessing: {collection_id}")
        try:
            # Load metadata
            data = load_entities(collection_id)
            title = data.get("title")
            descriptor = data.get("descriptor")
            
            if not title or not descriptor:
                print(f"  Skipping {collection_id}: Missing title/descriptor")
                continue
                
            print(f"  Generating cover for '{title}'...")
            
            # Generate new cover (uses updated prompt in generate.py)
            image_bytes = generate_cover_image(collection_id, title, descriptor)
            
            # Save overwrite
            filepath = save_cover_image(collection_id, image_bytes)
            print(f"  ✓ Saved to {filepath}")
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")

if __name__ == "__main__":
    confirm = input("This will overwrite all existing covers. Continue? [y/N] ")
    if confirm.lower() == 'y':
        regenerate_all_covers()
    else:
        print("Aborted.")
