import sys
from pathlib import Path
import json

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from db.load_db import get_connection, load_book

OUTPUTS_DIR = BASE_DIR / "outputs"

def update_db():
    print("="*60)
    print("Updating Turso Database from existing book.json files")
    print("="*60)

    # Get all collection directories
    collections = [d for d in OUTPUTS_DIR.iterdir() if d.is_dir()]
    collections.sort(key=lambda x: x.name)
    
    conn = get_connection()
    
    success_count = 0
    fail_count = 0

    for collection_dir in collections:
        collection_id = collection_dir.name
        book_json_path = collection_dir / "book.json"
        
        if not book_json_path.exists():
            print(f"Skipping {collection_id}: book.json not found")
            continue
            
        print(f"Processing {collection_id}...")
        
        try:
            # Check if cover exists, though load_book might handle None
            # The original publisher.py passed book.cover_path which comes from the Book object
            # We need to read the book.json to get the cover_path if possible, or infer it
            
            with open(book_json_path, 'r') as f:
                book_data = json.load(f)
                
            cover_path = book_data.get("cover_path")
            
            # call load_book
            load_book(conn, str(book_json_path), cover_path)
            print(f"✓ Updated {collection_id}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Failed to update {collection_id}: {e}")
            fail_count += 1
            
    conn.close()
    
    print("="*60)
    print(f"Update Complete")
    print(f"Success: {success_count}")
    print(f"Failed:  {fail_count}")
    print("="*60)

if __name__ == "__main__":
    update_db()
