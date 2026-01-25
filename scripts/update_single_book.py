import sys
from pathlib import Path
import json
import argparse

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from db.load_db import get_connection, load_book

OUTPUTS_DIR = BASE_DIR / "outputs"

def update_single_book(collection_id):
    print(f"\nUpdating Turso Database for: {collection_id}")
    
    collection_dir = OUTPUTS_DIR / collection_id
    book_json_path = collection_dir / "book.json"
    
    if not book_json_path.exists():
        print(f"Error: {book_json_path} not found")
        return

    conn = get_connection()
    
    try:
        with open(book_json_path, 'r') as f:
            book_data = json.load(f)
            
        cover_path = book_data.get("cover_path")
        
        # Fix missing cover_path if cover.png exists
        if not cover_path:
            potential_cover = collection_dir / "cover.png"
            if potential_cover.exists():
                print(f"  Found orphaned cover for {collection_id}, updating book.json...")
                cover_path = f"/outputs/{collection_id}/cover.png"
                book_data["cover_path"] = cover_path
                
                with open(book_json_path, "w") as f:
                    json.dump(book_data, f, indent=2)
        
        # call load_book
        load_book(conn, str(book_json_path), cover_path)
        print(f"✓ Updated {collection_id}")
        
    except Exception as e:
        print(f"✗ Failed to update {collection_id}: {e}")
        
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("collection__id")
    args = parser.parse_args()
    
    update_single_book(args.collection__id)
