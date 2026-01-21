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
        return book
