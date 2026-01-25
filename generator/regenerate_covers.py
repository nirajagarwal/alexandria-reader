import os
import sys
import argparse
from pathlib import Path

# Add project root to path to allow imports
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from generator.generate import load_entities, generate_cover_image, save_cover_image

def regenerate_covers(target_collection=None, fast_mode=False):
    """Regenerate covers for collections."""
    entities_dir = BASE_DIR / "entities"
    
    if target_collection:
        collections = [target_collection]
    else:
        # Find all collection JSON files
        collections = [f.stem for f in entities_dir.glob("*.json")]
    
    print(f"Found {len(collections)} collections to process: {', '.join(collections)}")
    
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
            
            # Generate new cover
            image_bytes = generate_cover_image(collection_id, title, descriptor)
            
            # Save overwrite
            filepath = save_cover_image(collection_id, image_bytes)
            print(f"  ✓ Saved to {filepath}")
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate book covers")
    parser.add_argument("--collection", help="Specific collection ID to regenerate")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    if not args.yes and not args.collection:
        confirm = input("This will overwrite all existing covers. Continue? [y/N] ")
        if confirm.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
            
    regenerate_covers(args.collection)
