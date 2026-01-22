
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from api.database import get_connection

def main():
    print("Starting cover URL fix...")
    
    # 1. Connect to DB
    try:
        conn = get_connection()
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return

    # 2. Get all books
    try:
        books = conn.execute("SELECT book_id, title FROM books").fetchall()
        print(f"Found {len(books)} books in database.")
    except Exception as e:
        print(f"Failed to fetch books: {e}")
        return

    updated_count = 0
    
    # 3. Check and update keys
    for book in books:
        book_id = book[0]
        title = book[1]
        
        # Check if cover exists
        cover_path = PROJECT_ROOT / "outputs" / book_id / "cover.png"
        
        if cover_path.exists():
            # Correct URL format (relative to domain root)
            cover_url = f"/outputs/{book_id}/cover.png"
            
            print(f"Updating '{title}' ({book_id})...")
            try:
                conn.execute(
                    "UPDATE books SET cover_url = ? WHERE book_id = ?",
                    (cover_url, book_id)
                )
                updated_count += 1
            except Exception as e:
                print(f"  Error updating {book_id}: {e}")
        else:
            print(f"Warning: Cover not found for '{title}' at {cover_path}")

    # Commit changes
    try:
        conn.commit()
        print(f"\nSuccessfully updated {updated_count} books.")
    except Exception as e:
        print(f"Failed to commit changes: {e}")

if __name__ == "__main__":
    main()
