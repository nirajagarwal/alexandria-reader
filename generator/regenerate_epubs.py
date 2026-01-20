import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from generator.generate_epub import generate_epub

def regenerate_all_epubs():
    """Regenerate EPUBs for all collections."""
    entities_dir = BASE_DIR / "entities"
    
    # Find all collection JSON ids
    collections = [f.stem for f in entities_dir.glob("*.json")]
    
    print(f"Found {len(collections)} collections.")
    
    for collection_id in collections:
        print(f"\nProcessing: {collection_id}")
        try:
            generate_epub(collection_id)
        except Exception as e:
            print(f"  ✗ Failed: {e}")

if __name__ == "__main__":
    regenerate_all_epubs()
