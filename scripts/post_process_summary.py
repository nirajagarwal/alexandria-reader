
import os
import sys
import glob
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
    output_file = os.path.join(base_path, collection_name, "summary.md")

    if not os.path.exists(entries_path):
        print(f"Error: Collection '{collection_name}' not found at {entries_path}")
        return

    # Read all markdown files
    md_files = sorted(glob.glob(os.path.join(entries_path, "*.md")))
    if not md_files:
        print(f"No markdown files found in {entries_path}")
        return

    print(f"Found {len(md_files)} files in {collection_name}. Processing in parallel...")

    summaries = []
    # Process in parallel with 10 workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks matches the order of md_files?
        # executor.map returns results in order
        results = list(executor.map(process_entry, md_files))
    
    # Filter out None results
    valid_summaries = [r for r in results if r is not None]

    if not valid_summaries:
        print("No summaries generated.")
        return

    print(f"Generated {len(valid_summaries)} summaries. concatenating...")
    
    combined_content = "\n\n---\n\n".join(valid_summaries)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(combined_content)
        
    print(f"Summary written to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/post_process_summary.py <collection_name>")
        sys.exit(1)
    
    collection = sys.argv[1]
    # Allow user to specify model via env var or just modify script? 
    # User said "changed model to: gemini-3-flash-preview".
    # I'll hardcode it in process_entry as requested.
    generate_summary(collection)
