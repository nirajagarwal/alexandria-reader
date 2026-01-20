#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

def generate_all():
    base_dir = Path(__file__).parent.parent
    outputs_dir = base_dir / "outputs"
    generator_script = base_dir / "generator" / "generate_epub.py"
    
    # Get all subdirectories in outputs/
    book_dirs = [d for d in outputs_dir.iterdir() if d.is_dir() and d.name != "body"]
    
    print(f"Found {len(book_dirs)} potential books...")
    
    for book_dir in book_dirs:
        book_id = book_dir.name
        json_path = book_dir / "book.json"
        
        if json_path.exists():
            print(f"\n--- Generating EPUB for {book_id} ---")
            try:
                # Run the generation script using the virtual environment
                # We assume the venv is at .venv in the project root
                venv_python = base_dir / ".venv" / "bin" / "python3"
                if not venv_python.exists():
                    venv_python = "python3" # Fallback
                
                cmd = [str(venv_python), str(generator_script), book_id]
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"Error generating {book_id}: {e}")
        else:
            print(f"Skipping {book_id} (no book.json found)")

if __name__ == "__main__":
    generate_all()
