"""
Generate sitemap.xml for Alexandria Press.
This script queries the database for all available books and generates a standard sitemap.xml.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import libsql_experimental as libsql

# Add parent directory to path to allow imports if needed, though we only need simple connection here
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

# Load environment variables
load_dotenv(BASE_DIR / ".env")

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
BASE_URL = "https://alexandria.press"

def get_connection():
    if not TURSO_DATABASE_URL:
        print("Error: TURSO_DATABASE_URL not set in .env")
        sys.exit(1)
        
    return libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )

def generate_sitemap():
    print("Fetching books from database...")
    try:
        conn = get_connection()
        rows = conn.execute("SELECT book_id, created_at FROM books ORDER BY created_at DESC").fetchall()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
    
    print(f"Found {len(rows)} books.")
    
    # Header
    xml_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    
    # Home page
    current_date = datetime.now().strftime("%Y-%m-%d")
    xml_content.append(f"""  <url>
    <loc>{BASE_URL}/</loc>
    <lastmod>{current_date}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""")
    
    # Book pages
    for row in rows:
        book_id = row[0]
        # Parse created_at if possible, otherwise use current date or specific default
        # created_at is likely a string based on main.py model
        try:
            # Attempt to clean specific timestamp format if necessary or use as is if ISO
            # Assuming row[1] is a string like "2024-01-01T..."
            book_date = row[1].split('T')[0] if row[1] else current_date
        except:
            book_date = current_date
            
        xml_content.append(f"""  <url>
    <loc>{BASE_URL}/book.html?id={book_id}</loc>
    <lastmod>{book_date}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")
        
    # Footer
    xml_content.append('</urlset>')
    
    # Write to file
    output_path = BASE_DIR / "frontend" / "sitemap.xml"
    with open(output_path, "w") as f:
        f.write("\n".join(xml_content))
        
    print(f"Sitemap generated at: {output_path}")

if __name__ == "__main__":
    generate_sitemap()
