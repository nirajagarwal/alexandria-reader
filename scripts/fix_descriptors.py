import json
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
ENTITIES_DIR = BASE_DIR / "entities"
OUTPUTS_DIR = BASE_DIR / "outputs"

def fix_descriptors():
    # Iterate over all files in the entities directory
    for entity_file in ENTITIES_DIR.glob("*.json"):
        collection_id = entity_file.stem
        book_path = OUTPUTS_DIR / collection_id / "book.json"

        if not book_path.exists():
            print(f"Skipping {collection_id}: book.json not found")
            continue

        print(f"Processing {collection_id}...")

        # Load entity data
        with open(entity_file, "r") as f:
            try:
                entity_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error decoding {entity_file}")
                continue

        # Load book data
        with open(book_path, "r") as f:
            try:
                book_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error decoding {book_path}")
                continue

        # Create a mapping of slug to descriptor from entity data
        slug_to_descriptor = {
            entry["slug"]: entry.get("descriptor")
            for entry in entity_data.get("entries", [])
        }

        # Update entries in book data
        updated_count = 0
        for entry in book_data.get("entries", []):
            slug = entry.get("slug")
            if slug in slug_to_descriptor:
                # Update top-level descriptor
                entry["descriptor"] = slug_to_descriptor[slug]
                
                # Check if descriptor is in metadata and remove it if so (cleanup)
                if "metadata" in entry and "descriptor" in entry["metadata"]:
                    del entry["metadata"]["descriptor"]
                
                updated_count += 1

        # Save updated book data
        with open(book_path, "w") as f:
            json.dump(book_data, f, indent=2)

        print(f"Updated {updated_count} entries in {collection_id}")

if __name__ == "__main__":
    fix_descriptors()
