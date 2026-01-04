import os
from dotenv import load_dotenv
import libsql_experimental as libsql

load_dotenv()

url = os.environ.get("TURSO_DATABASE_URL")
token = os.environ.get("TURSO_AUTH_TOKEN")

print(f"Connecting to {url}...")
conn = libsql.connect(database=url, auth_token=token)

row = conn.execute("SELECT book_id, cover_url FROM books WHERE book_id = 'mental-models'").fetchone()
if row:
    print(f"Book found: {row[0]}")
    print(f"Cover URL: {row[1]}")
else:
    print("Book not found")
