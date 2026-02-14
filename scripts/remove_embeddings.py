import os
import json

def remove_embeddings():
    outputs_dir = "/Users/niraj/alexandria-press/outputs"
    
    modified_count = 0
    
    for root, dirs, files in os.walk(outputs_dir):
        if "book.json" in files:
            file_path = os.path.join(root, "book.json")
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if 'entries' in data:
                    entries_modified = False
                    for entry in data['entries']:
                        if 'embedding' in entry:
                            del entry['embedding']
                            entries_modified = True
                    
                    if entries_modified:
                        with open(file_path, 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"Modified: {file_path}")
                        modified_count += 1
                    else:
                        print(f"Skipped (no embeddings found): {file_path}")
                else:
                     print(f"Skipped (no entries): {file_path}")

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    print(f"\nTotal files modified: {modified_count}")

if __name__ == "__main__":
    remove_embeddings()
