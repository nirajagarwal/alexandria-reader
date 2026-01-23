import os
import sqlite3
import libsql_experimental as libsql
from dotenv import load_dotenv

load_dotenv()

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

def main():
    print(f"Connecting to {TURSO_DATABASE_URL.split('://')[0]}://... (masked)")
    conn = libsql.connect(TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)
    cursor = conn.cursor()
    
    # Query for the book
    cursor.execute("SELECT book_id, title, descriptor, cover_url FROM books WHERE book_id = 'countries'")
    row = cursor.fetchone()
    
    if row:
        print(f"Book found: {row[0]}")
        print(f"Title: {row[1]}")
        print(f"Descriptor: {row[2]}")
        print(f"Cover URL: {row[3]}")
    else:
        print("Book 'prayers' not found.")

if __name__ == "__main__":
    main()
