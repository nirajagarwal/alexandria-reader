
import os
import libsql_experimental as libsql
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
MAX_WIDTH = 400

load_dotenv(BASE_DIR / ".env")

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

def get_db_connection():
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        print("Error: TURSO_DATABASE_URL or TURSO_AUTH_TOKEN not set.")
        return None
    return libsql.connect(TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)

def process_book_covers():
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    
    # Get all books to verify paths
    rows = cursor.execute("SELECT book_id, title FROM books").fetchall()
    print(f"Found {len(rows)} books in database.")

    processed_count = 0
    updated_count = 0

    for row in rows:
        # row access might be by index or key depending on cursor type, usually tuple in standard python sqlite
        book_id = row[0]
        title = row[1]
        
        book_dir = OUTPUTS_DIR / book_id
        original_cover = book_dir / "cover.png"
        new_cover = book_dir / "cover_third.jpg"

        if not original_cover.exists():
            print(f"Skipping {title} ({book_id}): cover.png not found")
            continue

        try:
            with Image.open(original_cover) as img:
                # 1. Crop vertical middle third
                width, height = img.size
                
                # Calculate third stats
                third_height = height / 3
                top = third_height
                bottom = 2 * third_height
                
                # Crop box is (left, top, right, bottom)
                cropped_img = img.crop((0, top, width, bottom))
                
                # 2. Resize to max width 400px
                if cropped_img.width > MAX_WIDTH:
                    ratio = MAX_WIDTH / cropped_img.width
                    new_height = int(cropped_img.height * ratio)
                    resized_img = cropped_img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
                else:
                    resized_img = cropped_img

                # 3. Save as JPG
                # Convert to RGB if necessary (e.g. if PNG has alpha transparency)
                if resized_img.mode in ("RGBA", "P"):
                    resized_img = resized_img.convert("RGB")
                
                resized_img.save(new_cover, "JPEG", quality=85)
                processed_count += 1
                
                # 4. Update Database
                new_url = f"/outputs/{book_id}/cover_third.jpg"
                cursor.execute(
                    "UPDATE books SET cover_url = ? WHERE book_id = ?",
                    (new_url, book_id)
                )
                conn.commit()  # Commit after each update for safety in loop
                updated_count += 1
                print(f"Processed: {title}")

        except Exception as e:
            print(f"Error processing {book_id}: {e}")

    # Final commit not strictly needed if per-operation commit is used, but good for cleanup

    # Libsql connection doesn't strictly need close() in same way but good practice if available
    # conn.close() 
    
    print("\n------------------------------------------------")
    print(f"Processing Complete.")
    print(f"Images Processed: {processed_count}")
    print(f"Database Records Updated: {updated_count}")
    print("------------------------------------------------")

if __name__ == "__main__":
    process_book_covers()
