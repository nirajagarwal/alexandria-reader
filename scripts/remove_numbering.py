
import json
import re
import sys
from pathlib import Path

def remove_numbering(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {path}")
        return

    print(f"Processing {path}...")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        entries = data.get('entries', [])
        modified_count = 0
        
        for entry in entries:
            content = entry.get('content', '')
            if content:
                # Regex to find bold numbering: **1. , **2. , etc.
                # Pattern: \*\* literal, \d+ digits, \. literal dot, \s whitespace
                new_content = re.sub(r'\*\*(\d+)\.\s', '**', content)
                
                if new_content != content:
                    entry['content'] = new_content
                    modified_count += 1
                    
        if modified_count > 0:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Successfully updated {modified_count} entries in {path.name}.")
        else:
            print(f"No changes needed for {path.name}.")
            
    except Exception as e:
        print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to the requested file if no argument provided
        target = "outputs/body/book.json"
    else:
        target = sys.argv[1]
        
    remove_numbering(target)
