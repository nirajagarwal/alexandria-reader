import os
import json
import sys
from pathlib import Path

# Add project root to path so we can import modules
base_dir = Path(__file__).parent.resolve()
sys.path.append(str(base_dir))

from generator.generate import (
    generate_all_entries, 
    generate_cover_image, 
    save_cover_image, 
    assemble_book, 
    get_anthropic_client,
    load_entities,
    OUTPUT_DIR,
    ENTITIES_DIR
)
from db.load_db import get_connection, load_book

def regenerate_all():
    """
    Regenerates missing entries and covers for all collections,
    assembles book.json if missing, and updates the Turso database.
    """
    anthropic_client = get_anthropic_client()
    db_conn = get_connection()
    
    # Get all collection IDs from entities directory
    collection_files = sorted(list(ENTITIES_DIR.glob("*.json")))
    collection_ids = [f.stem for f in collection_files]
    
    print(f"Found {len(collection_ids)} collections: {', '.join(collection_ids)}")
    
    for coll_id in collection_ids:
        print(f"\n" + "="*80)
        print(f"Processing Collection: {coll_id}")
        print("="*80)
        
        # 1. Generate missing entries
        print(f"Checking entries for {coll_id}...")
        generate_all_entries(coll_id, skip_existing=True)
        
        # 2. Generate missing cover
        coll_output_dir = OUTPUT_DIR / coll_id
        cover_path = coll_output_dir / "cover.png"
        
        if not cover_path.exists():
            print(f"Cover missing for {coll_id}. Generating...")
            try:
                coll_data = load_entities(coll_id)
                cover_bytes = generate_cover_image(
                    coll_id,
                    coll_data["title"],
                    coll_data["descriptor"]
                )
                save_cover_image(coll_id, cover_bytes)
                print(f"✓ Cover generated: {cover_path}")
            except Exception as e:
                print(f"✗ Cover generation failed: {e}")
        else:
            print(f"✓ Cover already exists: {cover_path}")
            
        # 3. Assemble book.json if missing
        book_json_path = coll_output_dir / "book.json"
        if not book_json_path.exists():
            print(f"book.json missing for {coll_id}. Assembling...")
            assemble_book(coll_id)
            print(f"✓ book.json assembled: {book_json_path}")
        else:
            print(f"✓ book.json exists, respecting manual edits: {book_json_path}")
            
        # 4. Update Turso DB
        print(f"Updating Turso database for {coll_id}...")
        try:
            load_book(db_conn, str(book_json_path))
            print(f"✓ Database updated for {coll_id}")
        except Exception as e:
            print(f"✗ Database update failed for {coll_id}: {e}")
            
    db_conn.close()
    print("\n" + "="*80)
    print("Regenerate All Completed.")
    print("="*80)

if __name__ == "__main__":
    regenerate_all()
