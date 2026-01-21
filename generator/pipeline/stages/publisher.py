import json
from pathlib import Path
from dataclasses import asdict
from ..config import OUTPUT_DIR
from ..models import Book
from .base import Stage

class Publisher(Stage):
    def execute(self, book: Book) -> Book:
        print(f"Publishing book: {book.book_id}")
        
        # Ensure directories
        book_dir = OUTPUT_DIR / book.book_id
        entries_dir = book_dir / "entries"
        entries_dir.mkdir(parents=True, exist_ok=True)
        
        # Save Entries
        for entry in book.entries:
            if entry.content:
                filepath = entries_dir / f"{entry.slug}.md"
                with open(filepath, "w") as f:
                    f.write(entry.content)
                    
        # Save Book JSON
        # Convert dataclass to dict, handle non-serializable types if any
        book_dict = asdict(book)
        
        # Sort entries by order
        book_dict["entries"].sort(key=lambda x: x["order"])
        
        json_path = book_dir / "book.json"
        with open(json_path, "w") as f:
            json.dump(book_dict, f, indent=2)
            
        print(f"Book saved to: {json_path}")
        
        # Generate EPUB
        print(f"Generating EPUB for {book.book_id}...")
        try:
            import subprocess
            import sys
            
            # Resolve path to generate_epub.py relative to this file
            # This file is in generator/pipeline/stages/publisher.py
            # generate_epub.py is in generator/generate_epub.py
            # So we go up 3 levels to generator/
            
            # Actually, config.py defines BASE_DIR as project root
            # Let's rely on finding it relative to project root
            from ..config import BASE_DIR
            script_path = BASE_DIR / "generator" / "generate_epub.py"
            
            if script_path.exists():
                subprocess.run([sys.executable, str(script_path), book.book_id], check=True)
            else:
                print(f"Warning: EPUB generator script not found at {script_path}")
                
        except Exception as e:
            print(f"EPUB generation failed: {e}")
            
        # Update Database
        print(f"Updating Turso database for {book.book_id}...")
        try:
            # Add project root to path to import db
            import sys
            from ..config import BASE_DIR
            if str(BASE_DIR) not in sys.path:
                sys.path.append(str(BASE_DIR))
                
            from db.load_db import get_connection, load_book as db_load_book
            
            conn = get_connection()
            db_load_book(conn, str(json_path), book.cover_path)
            conn.close()
            print(f"✓ Database updated for {book.book_id}")
            
        except Exception as e:
            print(f"Database update failed: {e}")
            
        return book
