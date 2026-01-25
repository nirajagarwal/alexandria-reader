import os
import libsql_experimental as libsql
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

def main():
    if not TURSO_DATABASE_URL:
        print("Error: TURSO_DATABASE_URL not found in environment.")
        return

    conn = libsql.connect(TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)
    cursor = conn.cursor()
    console = Console()

    # 1. Total Counts
    cursor.execute("SELECT COUNT(*) FROM books")
    book_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entries")
    entry_count = cursor.fetchone()[0]

    print(f"\nDatabase Stats for {TURSO_DATABASE_URL.split('://')[0]}...")
    print(f"Total Books: {book_count}")
    print(f"Total Entries: {entry_count}\n")

    # 2. Per-Book Stats
    table = Table(title="Collection Statistics")
    table.add_column("Book ID", style="cyan")
    table.add_column("Title", style="magenta")
    table.add_column("Entries", justify="right")
    table.add_column("Key", style="dim")

    # Join books and entries to count entries per book
    query = """
    SELECT 
        b.book_id, 
        b.title, 
        COUNT(e.book_id) as entry_count 
    FROM books b
    LEFT JOIN entries e ON b.book_id = e.book_id
    GROUP BY b.book_id
    ORDER BY entry_count DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        table.add_row(row[0], row[1], str(row[2]), row[0])

    console.print(table)

if __name__ == "__main__":
    main()
