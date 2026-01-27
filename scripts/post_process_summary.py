
import os
import sys
import glob
import json
import concurrent.futures
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

CLIENT = None

def get_client():
    global CLIENT
    if CLIENT is None:
        CLIENT = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    return CLIENT

def process_entry(file_path):
    try:
        client = get_client()
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Prompt for super-condensed version
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=f"Create a distilled version of the following entry, preserving the essence and insights. Output as a collection of short paragraphs in narrative style with minimal use of lists and styling. Output as Markdown.\n\n{content}",
            config=types.GenerateContentConfig(
                response_mime_type='text/plain'
            )
        )
        return response.text
    except Exception as e:
        print(f"Error processing {os.path.basename(file_path)}: {e}")
        return None

def generate_summary(collection_name):
    # validate collection path
    base_path = "outputs"
    entries_path = os.path.join(base_path, collection_name, "entries")
    book_json_path = os.path.join(base_path, collection_name, "book.json")
    output_file = os.path.join(base_path, collection_name, "summary.md")

    if not os.path.exists(entries_path):
        print(f"Error: Collection '{collection_name}' not found at {entries_path}")
        return

    if not os.path.exists(book_json_path):
        print(f"Error: book.json not found at {book_json_path}")
        return

    # Load book.json
    try:
        with open(book_json_path, "r", encoding="utf-8") as f:
            book_data = json.load(f)
    except Exception as e:
        print(f"Error reading {book_json_path}: {e}")
        return

    book_entries = book_data.get("entries", [])
    if not book_entries:
        print("No entries found in book.json")
        return

    # Map slug to file path and preserve order locally
    # We want to process only existing files that match the book.json entries
    ordered_files = []
    entry_metadata_map = {} # Map file_path -> entry_data

    for entry in book_entries:
        slug = entry.get("slug")
        if not slug:
            continue
        
        file_path = os.path.join(entries_path, f"{slug}.md")
        if os.path.exists(file_path):
            ordered_files.append(file_path)
            entry_metadata_map[file_path] = entry
        else:
            print(f"Warning: File not found for slug '{slug}' at {file_path}")

    if not ordered_files:
        print(f"No matching markdown files found in {entries_path}")
        return

    print(f"Found {len(ordered_files)} files in {collection_name}. Processing in parallel...")

    # Process in parallel with 10 workers
    summaries_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_entry, fp): fp for fp in ordered_files}
        
        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                if result:
                    summaries_map[file_path] = result
            except Exception as e:
                print(f"Exception for {file_path}: {e}")

    # Assemble content in correct order
    final_parts = []
    
    # Add Book Title and Header
    book_title = book_data.get("title", collection_name)
    book_descriptor = book_data.get("descriptor", "")
    
    header = f"# {book_title}\n"
    if book_descriptor:
        header += f"*{book_descriptor}*\n"
    final_parts.append(header)

    generated_count = 0
    for file_path in ordered_files:
        summary_text = summaries_map.get(file_path)
        if not summary_text:
            continue
            
        entry_data = entry_metadata_map.get(file_path)
        name = entry_data.get("name", "Unknown")
        descriptor = entry_data.get("descriptor", "")
        
        entry_section = f"## {name}\n"
        if descriptor:
            entry_section += f"*{descriptor}*\n\n"
        else:
            entry_section += "\n"
            
        entry_section += summary_text
        final_parts.append(entry_section)
        generated_count += 1

    if generated_count == 0:
        print("No summaries generated.")
        return

    print(f"Generated {generated_count} summaries. Concatenating...")
    
    combined_content = "\n\n---\n\n".join(final_parts)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(combined_content)
        
    print(f"Summary written to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/post_process_summary.py <collection_name>")
        sys.exit(1)
    
    collection = sys.argv[1]
    generate_summary(collection)
